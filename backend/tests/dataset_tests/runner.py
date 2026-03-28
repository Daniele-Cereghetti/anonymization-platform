"""
Dataset Test Runner
===================
Runs extraction + anonymization on every document in dataset/ and saves
a timestamped JSON record for each test plus a run-level SUMMARY.json.

After each document the runner prints two intermediate tables:
  1. Entity table  — entities found, with category, type, source, semantic role
  2. Mapping table — original value → anonymized replacement

Usage:
    cd backend/
    python -m tests.dataset_tests.runner
    python -m tests.dataset_tests.runner --group 01   # only docs starting with "01"

Options (env vars):
    ANON_VERBOSE=0   suppress intermediate tables (only show summary)

Results are written to:
    tests/dataset_tests/results/<timestamp>_<document>.json
    tests/dataset_tests/results/<timestamp>_SUMMARY.json
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich import box

# Allow running as a module from backend/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.domain.document import AnonymizationResult, ExtractionResult
from app.domain.entities import EntityCategory
from app.infrastructure.llm.ollama_client import OllamaClient, OllamaError
from app.services.anonymization_service import AnonymizationService
from app.services.extraction_service import ExtractionService

DATASET_DIR = Path(__file__).parent.parent.parent.parent / "dataset"
RESULTS_DIR = Path(__file__).parent / "results"
VERBOSE = os.getenv("ANON_VERBOSE", "1") != "0"

console = Console()


# ---------------------------------------------------------------------------
# Category colour map for the entity table
# ---------------------------------------------------------------------------

_CAT_STYLE: dict[str, str] = {
    "persone_fisiche":    "bold cyan",
    "persone_giuridiche": "bold blue",
    "dati_contatto":      "bold green",
    "identificativi":     "bold yellow",
    "dati_finanziari":    "bold magenta",
    "dati_temporali":     "bold white",
}

_SOURCE_STYLE: dict[str, str] = {
    "ner":    "dim yellow",
    "llm":    "dim cyan",
    "merged": "dim green",
}


# ---------------------------------------------------------------------------
# Rich table printers
# ---------------------------------------------------------------------------

def _print_entity_table(doc_name: str, ext: ExtractionResult) -> None:
    table = Table(
        title=f"[bold]Entities — {doc_name}[/bold]  "
              f"([dim]{len(ext.entities)} found, "
              f"{ext.processing_time_ms} ms[/dim])",
        box=box.ROUNDED,
        show_lines=True,
        highlight=True,
    )
    table.add_column("#",             style="dim", width=4, justify="right")
    table.add_column("Value",         style="bold", max_width=40)
    table.add_column("Category",      max_width=22)
    table.add_column("Type",          max_width=22)
    table.add_column("Source",        max_width=8, justify="center")
    table.add_column("Semantic role", max_width=24)

    for i, entity in enumerate(ext.entities, 1):
        cat_style = _CAT_STYLE.get(entity.category.value, "")
        src_style = _SOURCE_STYLE.get(entity.source or "", "dim")
        table.add_row(
            str(i),
            entity.value,
            f"[{cat_style}]{entity.category.value}[/{cat_style}]",
            entity.entity_type,
            f"[{src_style}]{entity.source or '—'}[/{src_style}]",
            f"[italic]{entity.semantic_role or '—'}[/italic]",
        )

    console.print(table)


def _print_mapping_table(doc_name: str, anon: AnonymizationResult) -> None:
    table = Table(
        title=f"[bold]Mapping table — {doc_name}[/bold]  "
              f"([dim]{len(anon.mappings)} substitutions, "
              f"{anon.processing_time_ms} ms[/dim])",
        box=box.ROUNDED,
        show_lines=True,
        highlight=True,
    )
    table.add_column("#",            style="dim", width=4, justify="right")
    table.add_column("Original",     style="bold red",   max_width=40)
    table.add_column("→ Replacement",style="bold green", max_width=30)
    table.add_column("Category",     max_width=22)
    table.add_column("Type",         max_width=22)

    for i, mapping in enumerate(anon.mappings, 1):
        cat_style = _CAT_STYLE.get(mapping.category.value, "")
        table.add_row(
            str(i),
            mapping.original,
            mapping.replacement,
            f"[{cat_style}]{mapping.category.value}[/{cat_style}]",
            mapping.entity_type,
        )

    console.print(table)


# ---------------------------------------------------------------------------
# Core test logic
# ---------------------------------------------------------------------------

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

    # Stage 1 — Extraction (Modulo Identificazione + Modulo Ruoli Semantici)
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

    if VERBOSE:
        _print_entity_table(doc_path.name, ext)

    # Stage 2 — Anonymization
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

    if VERBOSE:
        _print_mapping_table(doc_path.name, anon)

    record["status"] = "success"
    return record


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Dataset test runner")
    parser.add_argument(
        "--group", "-g",
        metavar="PREFIX",
        help="Run only documents whose filename starts with PREFIX (e.g. '01')",
    )
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    client = OllamaClient()
    if not client.is_available():
        console.print(f"[bold red]ERROR:[/bold red] Ollama not reachable at {client.base_url}")
        console.print("Start the container with:  [bold]docker start ollama[/bold]")
        sys.exit(1)

    models = client.available_models()
    console.print(f"[bold green]Ollama OK[/bold green] — model: [cyan]{client.model}[/cyan]")
    console.print(f"Available models: {', '.join(models)}")
    console.print(f"Dataset: {DATASET_DIR}\n")

    extraction_svc = ExtractionService(client)
    anonymization_svc = AnonymizationService()

    all_docs = sorted(DATASET_DIR.glob("*.md"))
    documents = (
        [d for d in all_docs if d.name.startswith(args.group)]
        if args.group
        else all_docs
    )
    if not documents:
        msg = (
            f"[red]No .md files starting with '{args.group}' found in {DATASET_DIR}[/red]"
            if args.group
            else f"[red]No .md files found in {DATASET_DIR}[/red]"
        )
        console.print(msg)
        sys.exit(1)

    if args.group:
        console.print(f"Group filter: [bold cyan]{args.group}[/bold cyan]")
    console.print(f"Documents to test: [bold]{len(documents)}[/bold]")
    console.rule()

    run_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    all_records: list = []

    for i, doc_path in enumerate(documents, 1):
        console.print(
            f"\n[bold white][{i}/{len(documents)}][/bold white] "
            f"[bold]{doc_path.name}[/bold]",
            highlight=False,
        )
        record = _run_single(doc_path, extraction_svc, anonymization_svc)
        all_records.append(record)

        if record["status"] == "error":
            console.print(f"  [bold red]ERROR:[/bold red] {record['error']}")

        # Save individual result immediately
        stem = doc_path.stem
        out_path = RESULTS_DIR / f"{run_ts}_{stem}.json"
        out_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # --- Final summary table ---
    success_records = [r for r in all_records if r["status"] == "success"]
    total_entities = sum(r["extraction"]["entities_count"] for r in success_records)

    category_counts: dict = {c.value: 0 for c in EntityCategory}
    for r in success_records:
        for e in r["extraction"]["entities"]:
            cat = e.get("category", "")
            if cat in category_counts:
                category_counts[cat] += 1

    console.rule()

    summary_table = Table(
        title="[bold]Run Summary[/bold]",
        box=box.ROUNDED,
        show_header=False,
    )
    summary_table.add_column("Key",   style="bold", min_width=30)
    summary_table.add_column("Value", style="cyan")
    summary_table.add_row("Model",      client.model)
    summary_table.add_row("Documents",  f"{len(success_records)}/{len(documents)} succeeded")
    summary_table.add_row("Total entities found", str(total_entities))
    for cat, count in category_counts.items():
        if count:
            style = _CAT_STYLE.get(cat, "")
            summary_table.add_row(
                f"  [{style}]{cat}[/{style}]",
                f"[{style}]{count}[/{style}]",
            )
    console.print(summary_table)

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
                if r["extraction"] else 0,
                "extraction_time_ms": r["extraction"]["processing_time_ms"]
                if r["extraction"] else 0,
                "error": r.get("error"),
            }
            for r in all_records
        ],
    }

    summary_path = RESULTS_DIR / f"{run_ts}_SUMMARY.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    console.print(f"\nResults saved to: [dim]{RESULTS_DIR}[/dim]")
    console.print(f"Summary:          [dim]{summary_path.name}[/dim]")


if __name__ == "__main__":
    main()
