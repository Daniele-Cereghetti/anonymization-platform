"""
NER-Only Test Runner
====================
Runs ONLY the Presidio/spaCy NER pipeline (no LLM) on every document in dataset/
and prints a table of detected entities.

Useful to evaluate what the rule-based + spaCy layer can detect on its own,
before the LLM merging step.

Usage:
    cd backend/
    python -m tests.dataset_tests.runner_ner_only

Options (env vars):
    ANON_VERBOSE=0   suppress per-document entity tables (only show summary)
"""

import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich import box

# Allow running as a module from backend/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.domain.entities import EntityCategory
from app.services.identification_service import _run_presidio, _get_analyzer

DATASET_DIR = Path(__file__).parent.parent.parent.parent / "dataset"

console = Console()

_CAT_STYLE: dict[str, str] = {
    "persone_fisiche":    "bold cyan",
    "persone_giuridiche": "bold blue",
    "dati_contatto":      "bold green",
    "identificativi":     "bold yellow",
    "dati_finanziari":    "bold magenta",
    "dati_temporali":     "bold white",
}


def _print_entities(doc_name: str, entities: list, elapsed_ms: int) -> None:
    table = Table(
        title=f"[bold]NER-only — {doc_name}[/bold]  "
              f"([dim]{len(entities)} entità rilevate, {elapsed_ms} ms[/dim])",
        box=box.ROUNDED,
        show_lines=True,
        highlight=True,
    )
    table.add_column("#",        style="dim", width=4, justify="right")
    table.add_column("Value",    style="bold", max_width=40)
    table.add_column("Category", max_width=22)
    table.add_column("Type",     max_width=22)
    table.add_column("Score",    max_width=8, justify="right")

    for i, entity in enumerate(entities, 1):
        cat_style = _CAT_STYLE.get(entity.category.value, "")
        score_str = f"{entity.confidence:.2f}" if entity.confidence is not None else "—"
        table.add_row(
            str(i),
            entity.value,
            f"[{cat_style}]{entity.category.value}[/{cat_style}]",
            entity.entity_type,
            score_str,
        )

    console.print(table)


def main() -> None:
    import os
    import time

    verbose = os.getenv("ANON_VERBOSE", "1") != "0"

    # Check Presidio/spaCy availability
    analyzer = _get_analyzer()
    if analyzer is None:
        console.print(
            "[bold red]ERROR:[/bold red] Presidio/spaCy non disponibile.\n"
            "Installa con:\n"
            "  pip install presidio-analyzer spacy\n"
            "  python -m spacy download en_core_web_sm"
        )
        sys.exit(1)

    console.print("[bold green]Presidio/spaCy OK[/bold green] — modalità NER-only (nessun LLM)")
    console.print(f"Dataset: {DATASET_DIR}\n")

    documents = sorted(DATASET_DIR.glob("*.md"))
    if not documents:
        console.print(f"[red]Nessun file .md trovato in {DATASET_DIR}[/red]")
        sys.exit(1)

    console.print(f"Documenti da testare: [bold]{len(documents)}[/bold]")
    console.rule()

    all_categories = [c.value for c in EntityCategory]
    total_entities = 0
    category_counts: dict[str, int] = {c.value: 0 for c in EntityCategory}

    for i, doc_path in enumerate(documents, 1):
        console.print(
            f"\n[bold white][{i}/{len(documents)}][/bold white] "
            f"[bold]{doc_path.name}[/bold]",
            highlight=False,
        )

        content = doc_path.read_text(encoding="utf-8")

        t0 = time.monotonic()
        entities = _run_presidio(content, all_categories)
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        total_entities += len(entities)
        for e in entities:
            category_counts[e.category.value] += 1

        if verbose:
            if entities:
                _print_entities(doc_path.name, entities, elapsed_ms)
            else:
                console.print(
                    f"  [dim]Nessuna entità rilevata ({elapsed_ms} ms)[/dim]"
                )

    console.rule()

    summary_table = Table(
        title="[bold]Riepilogo NER-only[/bold]",
        box=box.ROUNDED,
        show_header=False,
    )
    summary_table.add_column("Key",   style="bold", min_width=30)
    summary_table.add_column("Value", style="cyan")
    summary_table.add_row("Pipeline",             "Presidio + spaCy en_core_web_sm")
    summary_table.add_row("Documenti analizzati",  str(len(documents)))
    summary_table.add_row("Totale entità rilevate", str(total_entities))
    for cat, count in category_counts.items():
        if count:
            style = _CAT_STYLE.get(cat, "")
            summary_table.add_row(
                f"  [{style}]{cat}[/{style}]",
                f"[{style}]{count}[/{style}]",
            )
    console.print(summary_table)


if __name__ == "__main__":
    main()
