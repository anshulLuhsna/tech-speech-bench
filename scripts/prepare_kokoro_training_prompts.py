#!/usr/bin/env python3
"""Validate Kokoro v1 training sentences and freeze synthesis prompts."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SENTENCES = (
    REPO_ROOT / "data/synthetic/kokoro-v1/training-sentences.tsv"
)
DEFAULT_REVIEW = (
    REPO_ROOT / "data/synthetic/kokoro-v1/pronunciation-review.tsv"
)
DEFAULT_TERMS = REPO_ROOT / "data/v2/domain_terms.tsv"
DEFAULT_REFERENCES = REPO_ROOT / "data/v2/references.tsv"
DEFAULT_OUTPUT = (
    REPO_ROOT / "data/synthetic/kokoro-v1/training-prompts.tsv"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sentences", type=Path, default=DEFAULT_SENTENCES)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--terms", type=Path, default=DEFAULT_TERMS)
    parser.add_argument("--references", type=Path, default=DEFAULT_REFERENCES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def validate_and_build(
    sentence_rows: list[dict[str, str]],
    review_rows: list[dict[str, str]],
    term_rows: list[dict[str, str]],
    benchmark_references: set[str],
) -> list[dict[str, str]]:
    required = {"utterance_id", "term", "variant", "canonical_sentence"}
    if not sentence_rows:
        raise ValueError("training sentence sheet is empty")
    missing = required - set(sentence_rows[0])
    if missing:
        raise ValueError(f"training sentence columns missing: {sorted(missing)}")

    train_terms = [row["term"] for row in term_rows if row["split"] == "train"]
    heldout_terms = [row["term"] for row in term_rows if row["split"] != "train"]
    review_by_term = {row["term"]: row for row in review_rows}
    if set(review_by_term) != set(train_terms):
        raise ValueError("pronunciation review does not exactly cover train terms")
    unapproved = [
        term
        for term in train_terms
        if review_by_term[term]["review_status"] != "approved"
    ]
    if unapproved:
        raise ValueError(f"pronunciation review remains unapproved: {unapproved}")

    expected_ids = [
        f"ksv1_{index:03d}{variant}"
        for index in range(1, len(train_terms) + 1)
        for variant in ("a", "b")
    ]
    actual_ids = [row["utterance_id"] for row in sentence_rows]
    if actual_ids != expected_ids:
        raise ValueError("utterance ids must be ordered ksv1_001a through ksv1_031b")

    counts = Counter(row["term"] for row in sentence_rows)
    expected_counts = Counter({term: 2 for term in train_terms})
    if counts != expected_counts:
        raise ValueError(f"each train term needs two sentences; got {counts}")

    canonical_sentences = [row["canonical_sentence"] for row in sentence_rows]
    if len(set(canonical_sentences)) != len(canonical_sentences):
        raise ValueError("canonical training sentences must be unique")

    gate_sentences = {row["canonical_sentence"] for row in review_rows}
    prompts: list[dict[str, str]] = []
    for row in sentence_rows:
        utterance_id = row["utterance_id"]
        term = row["term"]
        variant = row["variant"]
        canonical = row["canonical_sentence"]

        if variant not in {"a", "b"}:
            raise ValueError(f"{utterance_id}: variant must be a or b")
        if canonical.count(term) != 1:
            raise ValueError(
                f"{utterance_id}: canonical sentence must contain target once"
            )
        other_terms = [
            candidate
            for candidate in train_terms
            if candidate != term and candidate in canonical
        ]
        if other_terms:
            raise ValueError(
                f"{utterance_id}: contains other train terms: {other_terms}"
            )
        leaked = [candidate for candidate in heldout_terms if candidate in canonical]
        if leaked:
            raise ValueError(f"{utterance_id}: held-out term leakage: {leaked}")
        if canonical in benchmark_references or canonical in gate_sentences:
            raise ValueError(f"{utterance_id}: reuses an existing sentence")

        spoken_form = review_by_term[term]["tts_spoken_form"]
        synthesis = canonical.replace(term, spoken_form, 1)
        if not 6 <= len(canonical.split()) <= 16:
            raise ValueError(f"{utterance_id}: sentence length outside 6-16 words")
        prompts.append(
            {
                "utterance_id": utterance_id,
                "source_clip_id": "synthetic_kokoro_v1",
                "target_terms": term,
                "transcript": canonical,
                "synthesis_text": synthesis,
            }
        )
    return prompts


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    sentence_rows = read_tsv(args.sentences)
    review_rows = read_tsv(args.review)
    term_rows = read_tsv(args.terms)
    benchmark_references = {
        row["reference_text"] for row in read_tsv(args.references)
    }
    prompts = validate_and_build(
        sentence_rows,
        review_rows,
        term_rows,
        benchmark_references,
    )
    print("validated 62 new sentences: 2 per train term")
    print("held-out vocabulary: absent")
    print("benchmark and pronunciation-gate sentence reuse: absent")
    if not args.write:
        print("dry run only; pass --write to freeze training prompts")
        return
    write_tsv(args.output, prompts)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
