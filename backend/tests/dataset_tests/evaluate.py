"""
Evaluation script for the anonymization pipeline.
==================================================
Compares predictions from a dataset run (JSON files in ``results/``) against
manual ground-truth annotations (JSON files in ``dataset/ground_truth/``) and
reports precision, recall and F1 — globally, per category and per language.

Matching strategy
-----------------
Set-based per document:
    - each entity is normalised to ``(value_normalized, category)``
    - normalisation: NFKC unicode, lower-cased, whitespace collapsed,
      surrounding punctuation stripped
    - a prediction is a TP if the same ``(value, category)`` exists in the GT
    - duplicates within a document are deduplicated before matching

A predicted entity that matches a GT value but with the WRONG category is
counted as both an FP (wrong category prediction) and an FN (correct category
not produced) — strict mode. Use ``--lenient-category`` to score it as TP if
the value matches regardless of category.

Usage
-----
    cd backend/
    python -m tests.dataset_tests.evaluate                    # latest run
    python -m tests.dataset_tests.evaluate --run 20260422T074801Z
    python -m tests.dataset_tests.evaluate --lenient-category
"""

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from rich.console import Console
from rich.table import Table
from rich import box

# Allow running as a module from backend/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

RESULTS_DIR = Path(__file__).parent / "results"
GT_DIR = Path(__file__).parent.parent.parent.parent / "dataset" / "ground_truth"

console = Console()

CATEGORIES = [
    "persone_fisiche",
    "persone_giuridiche",
    "dati_contatto",
    "identificativi",
    "dati_finanziari",
    "dati_temporali",
]


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

_WS_RE = re.compile(r"\s+")
_TRIM_PUNCT = " \t\n\r.,;:!?\"'`«»“”‘’()[]{}<>"


def _norm(value: str) -> str:
    v = unicodedata.normalize("NFKC", value).strip(_TRIM_PUNCT).lower()
    return _WS_RE.sub(" ", v)


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def _load_run(run_id: str | None) -> tuple[str, list[Path]]:
    """Return (run_id, list of per-document result files) for the chosen run."""
    summaries = sorted(RESULTS_DIR.glob("*_SUMMARY.json"))
    if not summaries:
        console.print(f"[red]No SUMMARY files in {RESULTS_DIR}[/red]")
        sys.exit(1)

    if run_id is None:
        run_id = summaries[-1].name.replace("_SUMMARY.json", "")

    docs = sorted(p for p in RESULTS_DIR.glob(f"{run_id}_*.json")
                  if not p.name.endswith("_SUMMARY.json"))
    if not docs:
        console.print(f"[red]No per-document files for run {run_id}[/red]")
        sys.exit(1)
    return run_id, docs


def _load_gt(doc_name: str) -> list[dict] | None:
    gt_path = GT_DIR / (Path(doc_name).stem + ".json")
    if not gt_path.exists():
        return None
    return json.loads(gt_path.read_text(encoding="utf-8"))["entities"]


def _detect_lang(doc_name: str) -> str:
    stem = Path(doc_name).stem
    for lang in ("IT", "EN", "FR", "DECH", "DE"):
        if stem.endswith("_" + lang):
            return "DE" if lang == "DECH" else lang
    return "??"


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def _to_set(entities: Iterable[dict]) -> set[tuple[str, str]]:
    return {(_norm(e["value"]), e["category"]) for e in entities}


def _by_value(entities: Iterable[dict]) -> dict[str, set[str]]:
    """Map normalized value → set of categories (used for lenient matching)."""
    out: dict[str, set[str]] = defaultdict(set)
    for e in entities:
        out[_norm(e["value"])].add(e["category"])
    return out


def _evaluate_doc(
    pred_entities: list[dict],
    gt_entities: list[dict],
    lenient_category: bool,
) -> dict:
    """Return per-category {tp, fp, fn} for a single document."""
    counts = {c: {"tp": 0, "fp": 0, "fn": 0} for c in CATEGORIES}

    pred_set = _to_set(pred_entities)
    gt_set = _to_set(gt_entities)

    if lenient_category:
        gt_values = _by_value(gt_entities)
        pred_values = _by_value(pred_entities)
        # TP per prediction: value exists in GT (any category).
        # FP per prediction: value not in GT.
        seen_preds: set[str] = set()
        for value, cats in pred_values.items():
            for cat in cats:
                if value in gt_values:
                    counts[cat]["tp"] += 1
                    seen_preds.add(value)
                else:
                    counts[cat]["fp"] += 1
        # FN per GT: value not in any prediction.
        for value, cats in gt_values.items():
            if value not in pred_values:
                for cat in cats:
                    counts[cat]["fn"] += 1
    else:
        for v, c in pred_set:
            if (v, c) in gt_set:
                counts[c]["tp"] += 1
            else:
                counts[c]["fp"] += 1
        for v, c in gt_set:
            if (v, c) not in pred_set:
                counts[c]["fn"] += 1

    return counts


# ---------------------------------------------------------------------------
# Aggregation & reporting
# ---------------------------------------------------------------------------

def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def _print_table(title: str, rows: list[tuple[str, int, int, int]]) -> None:
    table = Table(title=title, box=box.ROUNDED, show_lines=False)
    table.add_column("Group", style="bold", min_width=22)
    table.add_column("TP", justify="right")
    table.add_column("FP", justify="right")
    table.add_column("FN", justify="right")
    table.add_column("Precision", justify="right")
    table.add_column("Recall", justify="right")
    table.add_column("F1", justify="right", style="bold")

    for name, tp, fp, fn in rows:
        p, r, f = _prf(tp, fp, fn)
        table.add_row(
            name, str(tp), str(fp), str(fn),
            f"{p:.3f}", f"{r:.3f}", f"{f:.3f}",
        )
    console.print(table)


def _aggregate(per_doc: dict[str, dict]) -> dict:
    """Combine per-document/per-category counts into convenient totals."""
    by_cat = {c: {"tp": 0, "fp": 0, "fn": 0} for c in CATEGORIES}
    by_lang: dict[str, dict[str, int]] = defaultdict(
        lambda: {"tp": 0, "fp": 0, "fn": 0}
    )
    by_doc: dict[str, dict[str, int]] = {}
    total = {"tp": 0, "fp": 0, "fn": 0}

    for doc, info in per_doc.items():
        lang = info["lang"]
        d_tot = {"tp": 0, "fp": 0, "fn": 0}
        for c, cnt in info["counts"].items():
            for k in ("tp", "fp", "fn"):
                by_cat[c][k] += cnt[k]
                by_lang[lang][k] += cnt[k]
                d_tot[k] += cnt[k]
                total[k] += cnt[k]
        by_doc[doc] = d_tot

    return {
        "by_cat": by_cat,
        "by_lang": dict(by_lang),
        "by_doc": by_doc,
        "total": total,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate anonymization run vs ground truth")
    parser.add_argument("--run", help="Run timestamp (default: most recent)")
    parser.add_argument(
        "--lenient-category",
        action="store_true",
        help="Match on value alone, ignoring category mismatches",
    )
    parser.add_argument(
        "--json",
        metavar="OUT",
        help="Also write the full report as JSON to OUT",
    )
    args = parser.parse_args()

    run_id, doc_files = _load_run(args.run)
    console.print(f"[bold green]Run:[/bold green] {run_id}")
    console.print(f"[bold]Mode:[/bold] {'lenient-category' if args.lenient_category else 'strict'}")
    console.rule()

    per_doc: dict[str, dict] = {}
    skipped: list[str] = []

    for doc_file in doc_files:
        record = json.loads(doc_file.read_text(encoding="utf-8"))
        doc_name = record["document"]

        gt = _load_gt(doc_name)
        if gt is None:
            skipped.append(doc_name)
            continue
        if record.get("status") != "success" or not record.get("extraction"):
            skipped.append(doc_name)
            continue

        pred = record["extraction"]["entities"]
        counts = _evaluate_doc(pred, gt, args.lenient_category)
        per_doc[doc_name] = {
            "lang": _detect_lang(doc_name),
            "counts": counts,
            "n_pred": len(pred),
            "n_gt": len(gt),
        }

    if not per_doc:
        console.print("[red]No documents could be evaluated (no GT match).[/red]")
        if skipped:
            console.print(f"[dim]Skipped: {', '.join(skipped)}[/dim]")
        sys.exit(1)

    agg = _aggregate(per_doc)

    # --- Per-document table ---
    rows = sorted(
        [
            (doc, c["tp"], c["fp"], c["fn"])
            for doc, c in agg["by_doc"].items()
        ]
    )
    _print_table("Per-document", rows)

    # --- Per-language table ---
    rows = [
        (lang, c["tp"], c["fp"], c["fn"])
        for lang, c in sorted(agg["by_lang"].items())
    ]
    _print_table("Per-language", rows)

    # --- Per-category table ---
    rows = [
        (cat, c["tp"], c["fp"], c["fn"])
        for cat, c in agg["by_cat"].items()
    ]
    _print_table("Per-category", rows)

    # --- Global totals ---
    t = agg["total"]
    _print_table("GLOBAL", [("All", t["tp"], t["fp"], t["fn"])])

    if skipped:
        console.print(f"\n[dim]Skipped (no GT or run error): {', '.join(skipped)}[/dim]")

    # --- Optional JSON dump ---
    if args.json:
        report = {
            "run_id": run_id,
            "lenient_category": args.lenient_category,
            "skipped": skipped,
            "per_document": {
                doc: {
                    "lang": info["lang"],
                    "n_pred": info["n_pred"],
                    "n_gt": info["n_gt"],
                    "counts": info["counts"],
                }
                for doc, info in per_doc.items()
            },
            "by_category": agg["by_cat"],
            "by_language": agg["by_lang"],
            "total": agg["total"],
        }
        Path(args.json).write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        console.print(f"\n[dim]Report written to {args.json}[/dim]")


if __name__ == "__main__":
    main()
