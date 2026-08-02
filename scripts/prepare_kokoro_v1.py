#!/usr/bin/env python3
"""Validate Kokoro v1 pronunciation review and freeze gate prompts."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW = (
    REPO_ROOT / "data/synthetic/kokoro-v1/pronunciation-review.tsv"
)
DEFAULT_TERMS = REPO_ROOT / "data/v2/domain_terms.tsv"
DEFAULT_OUTPUT = (
    REPO_ROOT / "data/synthetic/kokoro-v1/pronunciation-gate-prompts.tsv"
)
REQUIRED_COLUMNS = {
    "gate_id",
    "term",
    "canonical_sentence",
    "tts_spoken_form",
    "tts_sentence",
    "expected_to_sound_like",
    "review_status",
    "review_note",
}
ALLOWED_STATUSES = {"pending", "approved", "revise"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--terms", type=Path, default=DEFAULT_TERMS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def validate_review(
    review_rows: list[dict[str, str]], term_rows: list[dict[str, str]]
) -> Counter[str]:
    if not review_rows:
        raise ValueError("pronunciation review is empty")
    missing_columns = REQUIRED_COLUMNS - set(review_rows[0])
    if missing_columns:
        raise ValueError(f"review columns missing: {sorted(missing_columns)}")

    train_terms = [row["term"] for row in term_rows if row["split"] == "train"]
    heldout_terms = [row["term"] for row in term_rows if row["split"] != "train"]
    reviewed_terms = [row["term"] for row in review_rows]
    if reviewed_terms != train_terms:
        missing = sorted(set(train_terms) - set(reviewed_terms))
        extra = sorted(set(reviewed_terms) - set(train_terms))
        raise ValueError(
            "review terms must exactly match train terms in frozen order; "
            f"missing={missing}, extra={extra}"
        )

    expected_ids = [f"kpg{index:03d}" for index in range(1, len(train_terms) + 1)]
    actual_ids = [row["gate_id"] for row in review_rows]
    if actual_ids != expected_ids:
        raise ValueError("gate ids must be contiguous kpg001 through kpg031")

    statuses: Counter[str] = Counter()
    all_terms = [row["term"] for row in term_rows]
    for row in review_rows:
        gate_id = row["gate_id"]
        term = row["term"]
        canonical = row["canonical_sentence"]
        spoken_form = row["tts_spoken_form"]
        synthesis = row["tts_sentence"]
        status = row["review_status"]

        if status not in ALLOWED_STATUSES:
            raise ValueError(f"{gate_id}: invalid review_status {status!r}")
        statuses[status] += 1
        if term not in canonical:
            raise ValueError(f"{gate_id}: term absent from canonical sentence")
        if spoken_form not in synthesis:
            raise ValueError(f"{gate_id}: spoken form absent from TTS sentence")

        other_terms = [
            candidate
            for candidate in all_terms
            if candidate != term and candidate in canonical
        ]
        if other_terms:
            raise ValueError(
                f"{gate_id}: gate sentence contains other domain terms: "
                f"{other_terms}"
            )
        leaked = [candidate for candidate in heldout_terms if candidate in synthesis]
        if leaked:
            raise ValueError(
                f"{gate_id}: held-out terms leaked into TTS sentence: {leaked}"
            )

    return statuses


def write_prompts(path: Path, review_rows: list[dict[str, str]]) -> None:
    fieldnames = (
        "utterance_id",
        "source_clip_id",
        "target_terms",
        "transcript",
        "synthesis_text",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in review_rows:
            writer.writerow(
                {
                    "utterance_id": row["gate_id"],
                    "source_clip_id": "synthetic_pronunciation_gate",
                    "target_terms": row["term"],
                    "transcript": row["canonical_sentence"],
                    "synthesis_text": row["tts_sentence"],
                }
            )


def main() -> None:
    args = parse_args()
    review_rows = read_tsv(args.review)
    term_rows = read_tsv(args.terms)
    statuses = validate_review(review_rows, term_rows)

    print(f"validated {len(review_rows)} train-term pronunciation rows")
    print(
        "review status: "
        f"approved={statuses['approved']}, "
        f"pending={statuses['pending']}, revise={statuses['revise']}"
    )

    if not args.write:
        if statuses["approved"] != len(review_rows):
            print("generation remains blocked until all 31 rows are approved")
        else:
            print("review complete; pass --write to freeze gate prompts")
        return

    if statuses["approved"] != len(review_rows):
        raise ValueError(
            "refusing to write gate prompts: every review row must be approved"
        )
    write_prompts(args.output, review_rows)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
