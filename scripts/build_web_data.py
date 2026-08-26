#!/usr/bin/env python3
"""Build the browser-ready ELISER dataset from the repository CSV.

Run from anywhere after placing this file at ``scripts/build_web_data.py`` in
the ELISER-StrainDesignDB repository::

    python scripts/build_web_data.py

The source CSV remains authoritative. The generated JSON is an optimized,
structured representation for the static GitHub Pages explorer.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
REPOSITORY_ROOT = SCRIPT_PATH.parent.parent
DEFAULT_INPUT = REPOSITORY_ROOT / "files" / "Output" / "ELISER_DB_v3.csv"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "docs" / "data" / "eliser.json"
KNOWN_DIRECTIONS = {"Positive", "Negative", "Other"}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert ELISER_DB_v3.csv into browser-ready JSON."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Source semicolon-delimited CSV (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Generated JSON destination (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Write indented JSON for debugging (larger file).",
    )
    return parser.parse_args()


def clean(value: Any) -> str:
    return str(value or "").strip()


def split_organisms(value: str) -> list[str]:
    """Split the repository's comma-separated host labels, preserving order."""
    organisms: list[str] = []
    seen: set[str] = set()
    for item in value.split(","):
        label = clean(item)
        if label and label.casefold() not in seen:
            organisms.append(label)
            seen.add(label.casefold())
    return organisms or ([value] if value else [])


def split_products(value: str) -> list[str]:
    """Return the full product label plus comma-delimited product components."""
    full_label = clean(value)
    if not full_label:
        return []
    products: list[str] = []
    seen: set[str] = set()
    for item in [full_label, *full_label.split(",")]:
        label = clean(item)
        if label and label.casefold() not in seen:
            products.append(label)
            seen.add(label.casefold())
    return products


def normalize_directions(value: Any) -> list[str]:
    """Turn combined values such as ``Negative,Positive`` into a stable list."""
    raw_values = [clean(item) for item in clean(value).split(",")]
    directions: list[str] = []
    for raw in raw_values:
        if not raw:
            continue
        direction = raw if raw in KNOWN_DIRECTIONS else "Other"
        if direction not in directions:
            directions.append(direction)
    return directions or ["Other"]


def parse_genes(raw_value: str, row_number: int) -> list[dict[str, Any]]:
    """Safely parse the Python-dict strings stored in the source CSV."""
    if not raw_value:
        return []
    try:
        parsed = ast.literal_eval(raw_value)
    except (SyntaxError, ValueError) as error:
        raise ValueError(f"Invalid Genes_and_modifications at CSV row {row_number}") from error
    if not isinstance(parsed, dict):
        raise ValueError(
            f"Genes_and_modifications must be a dictionary at CSV row {row_number}"
        )
    return [
        {"name": clean(gene), "directions": normalize_directions(direction)}
        for gene, direction in parsed.items()
        if clean(gene)
    ]


def ranked_labels(counter: Counter[str], limit: int = 300) -> list[str]:
    """Frequent labels first, with deterministic alphabetical tie-breaking."""
    return [
        label
        for label, _ in sorted(
            counter.items(), key=lambda item: (-item[1], item[0].casefold())
        )[:limit]
    ]


def build_database(input_path: Path) -> dict[str, Any]:
    required_fields = {
        "PMID",
        "Title",
        "Year",
        "Organism",
        "Product",
        "Genes_and_modifications",
    }
    records: list[dict[str, Any]] = []
    organism_counts: Counter[str] = Counter()
    product_counts: Counter[str] = Counter()
    gene_counts: Counter[str] = Counter()
    years: list[int] = []

    with input_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";")
        actual_fields = set(reader.fieldnames or [])
        missing_fields = required_fields - actual_fields
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"Source CSV is missing required columns: {missing}")

        for row_number, row in enumerate(reader, start=2):
            try:
                year = int(clean(row["Year"]))
            except ValueError as error:
                raise ValueError(f"Invalid year at CSV row {row_number}") from error

            organism = clean(row["Organism"])
            organisms = split_organisms(organism)
            product = clean(row["Product"])
            products = split_products(product)
            genes = parse_genes(clean(row["Genes_and_modifications"]), row_number)

            records.append(
                {
                    "pmid": clean(row["PMID"]),
                    "title": clean(row["Title"]),
                    "year": year,
                    "organism": organism,
                    "organisms": organisms,
                    "product": product,
                    "products": products,
                    "genes": genes,
                }
            )
            years.append(year)
            organism_counts.update(organisms)
            if product:
                product_counts[product] += 1
            gene_counts.update(gene["name"] for gene in genes)

    if not records:
        raise ValueError("Source CSV contains no data records")

    meta = {
        "recordCount": len(records),
        "organismCount": len(organism_counts),
        "productCount": len(product_counts),
        "geneCount": len(gene_counts),
        "minYear": min(years),
        "maxYear": max(years),
        "organismSuggestions": ranked_labels(organism_counts),
        "productSuggestions": ranked_labels(product_counts),
        "geneSuggestions": ranked_labels(gene_counts),
        "sourceFile": input_path.name,
    }
    return {"meta": meta, "records": records}


def write_database(database: dict[str, Any], output_path: Path, pretty: bool) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if pretty:
        serialized = json.dumps(database, ensure_ascii=False, indent=2)
    else:
        serialized = json.dumps(database, ensure_ascii=False, separators=(",", ":"))
    output_path.write_text(serialized + "\n", encoding="utf-8")


def main() -> None:
    arguments = parse_arguments()
    input_path = arguments.input.resolve()
    output_path = arguments.output.resolve()
    if not input_path.is_file():
        raise SystemExit(f"Source CSV not found: {input_path}")
    database = build_database(input_path)
    write_database(database, output_path, arguments.pretty)
    meta = database["meta"]
    print(
        "Built {records:,} records ({organisms:,} organism labels, "
        "{products:,} product labels, {genes:,} gene targets) -> {output}".format(
            records=meta["recordCount"],
            organisms=meta["organismCount"],
            products=meta["productCount"],
            genes=meta["geneCount"],
            output=output_path,
        )
    )


if __name__ == "__main__":
    main()
