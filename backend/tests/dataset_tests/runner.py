"""
Dataset Test Runner
===================
Runs extraction + anonymization on every document in dataset/ and saves
a timestamped JSON record for each test plus a run-level SUMMARY.json.

Usage:
    cd backend/
    python -m tests.dataset_tests.runner

Results are written to:
    tests/dataset_tests/results/<timestamp>_<document>.json
    tests/dataset_tests/results/<timestamp>_SUMMARY.json
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Allow running as a module from backend/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.domain.entities import EntityCategory
from app.infrastructure.llm.ollama_client import OllamaClient, OllamaError
from app.services.anonymization_service import AnonymizationService
from app.services.extraction_service import ExtractionService

DATASET_DIR = Path(__file__).parent.parent.parent.parent / "dataset"
RESULTS_DIR = Path(__file__).parent / "results"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run_single(
    doc_path: Path,
    extraction_svc: ExtractionService,
    anonymization_svc: AnonymizationService,
) -> dict:
    content = doc_path.read_text(encoding="utf-8")
    document_id = str(uuid.uuid4())

    record: dict = {
        "run_id": str(uuid.uuid4()),
        "timestamp": _now_iso(),
        "document": doc_path.name,
        "document_id": document_id,
        "model": extraction_svc.client.model,
        "char_count": len(content),
        "status": "pending",
        "extraction": None,
        "anonymization": None,
        "error": None,
    }

    # --- Extraction ---
    try:
        ext = extraction_svc.extract(content=content, document_id=document_id)
    except OllamaError as e:
        record["status"] = "error"
        record["error"] = str(e)
        return record

    record["extraction"] = {
        "entities_count": len(ext.entities),
        "processing_time_ms": ext.processing_time_ms,
        "categories_requested": ext.categories_requested,
        "entities": [e.model_dump() for e in ext.entities],
    }

    # --- Anonymization ---
    anon = anonymization_svc.anonymize(
        content=content,
        entities=ext.entities,
        document_id=document_id,
    )
    record["anonymization"] = {
        "mappings_count": len(anon.mappings),
        "processing_time_ms": anon.processing_time_ms,
        "mappings": [m.model_dump() for m in anon.mappings],
        "anonymized_preview": anon.anonymized_content[:600],
    }

    record["status"] = "success"
    return record


def _print_record(record: dict, index: int, total: int) -> None:
    prefix = f"[{index}/{total}] {record['document']}"
    if record["status"] == "success":
        n = record["extraction"]["entities_count"]
        ms = record["extraction"]["processing_time_ms"]
        print(f"  OK  {prefix} — {n} entities in {ms} ms")
    else:
        print(f"  ERR {prefix} — {record['error']}")


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    client = OllamaClient()
    if not client.is_available():
        print("ERROR: Ollama not reachable at", client.base_url)
        print("Start the container with:  docker start ollama")
        sys.exit(1)

    models = client.available_models()
    print(f"Ollama OK — model: {client.model}")
    print(f"Available models: {', '.join(models)}")
    print(f"Dataset: {DATASET_DIR}\n")

    extraction_svc = ExtractionService(client)
    anonymization_svc = AnonymizationService()

    documents = sorted(DATASET_DIR.glob("*.md"))
    if not documents:
        print(f"No .md files found in {DATASET_DIR}")
        sys.exit(1)

    print(f"Documents to test: {len(documents)}")
    print("-" * 50)

    run_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    all_records: list = []

    for i, doc_path in enumerate(documents, 1):
        print(f"Testing {doc_path.name}...", flush=True)
        record = _run_single(doc_path, extraction_svc, anonymization_svc)
        all_records.append(record)
        _print_record(record, i, len(documents))

        # Save individual result immediately
        stem = doc_path.stem
        out_path = RESULTS_DIR / f"{run_ts}_{stem}.json"
        out_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # --- Summary ---
    success_records = [r for r in all_records if r["status"] == "success"]
    total_entities = sum(r["extraction"]["entities_count"] for r in success_records)

    # Entities breakdown by category across all documents
    category_counts: dict = {c.value: 0 for c in EntityCategory}
    for r in success_records:
        for e in r["extraction"]["entities"]:
            cat = e.get("category", "")
            if cat in category_counts:
                category_counts[cat] += 1

    summary = {
        "run_timestamp": run_ts,
        "model": client.model,
        "total_documents": len(documents),
        "success": len(success_records),
        "errors": len(all_records) - len(success_records),
        "total_entities_found": total_entities,
        "entities_by_category": category_counts,
        "documents": [
            {
                "document": r["document"],
                "status": r["status"],
                "entities_count": r["extraction"]["entities_count"]
                if r["extraction"]
                else 0,
                "extraction_time_ms": r["extraction"]["processing_time_ms"]
                if r["extraction"]
                else 0,
                "error": r.get("error"),
            }
            for r in all_records
        ],
    }

    summary_path = RESULTS_DIR / f"{run_ts}_SUMMARY.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("-" * 50)
    print(f"Run complete: {summary['success']}/{summary['total_documents']} succeeded")
    print(f"Total entities found: {total_entities}")
    print("Entities by category:")
    for cat, count in category_counts.items():
        if count:
            print(f"  {cat}: {count}")
    print(f"\nResults saved to: {RESULTS_DIR}")
    print(f"Summary: {summary_path.name}")


if __name__ == "__main__":
    main()
