#!/usr/bin/env python3
"""Paired bootstrap uncertainty for two ASR runs on benchmark slices."""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

from score_transcripts import edit_distance, normalize_for_error_rate, read_terms


DEFAULT_REFERENCES = Path("data/v2/references.tsv")
DEFAULT_MANIFEST = Path("data/v2/manifest.tsv")
DEFAULT_TERMS = Path("data/v2/domain_terms.txt")
PARTITIONS = ("train_speaker", "dev_speaker", "test_speaker")
SPLITS = ("train", "heldout_real", "heldout_fake")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--references", type=Path, default=DEFAULT_REFERENCES)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--terms", type=Path, default=DEFAULT_TERMS)
    parser.add_argument("--run-a", type=Path, required=True)
    parser.add_argument("--run-b", type=Path, required=True)
    parser.add_argument("--label-a", required=True)
    parser.add_argument("--label-b", required=True)
    parser.add_argument("--iterations", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument(
        "--exclude-clip-id",
        action="append",
        default=[],
        help="Exclude this clip from every slice. Can be passed multiple times.",
    )
    parser.add_argument("--out-dir", type=Path, required=True)
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def clip_stats(
    clip_ids: list[str],
    references: dict[str, str],
    run_a: dict[str, str],
    run_b: dict[str, str],
    terms: list[str],
) -> list[dict[str, int]]:
    rows = []
    for clip_id in clip_ids:
        reference = references[clip_id]
        ref_words = normalize_for_error_rate(reference)
        hyp_a = normalize_for_error_rate(run_a[clip_id])
        hyp_b = normalize_for_error_rate(run_b[clip_id])
        clip_terms = [term for term in terms if term in reference]
        rows.append(
            {
                "words": len(ref_words),
                "edits_a": edit_distance(ref_words, hyp_a),
                "edits_b": edit_distance(ref_words, hyp_b),
                "mentions": len(clip_terms),
                "hits_a": sum(term in run_a[clip_id] for term in clip_terms),
                "hits_b": sum(term in run_b[clip_id] for term in clip_terms),
            }
        )
    return rows


def aggregate(rows: list[dict[str, int]]) -> dict[str, float]:
    words = sum(row["words"] for row in rows)
    mentions = sum(row["mentions"] for row in rows)
    return {
        "wer_a": sum(row["edits_a"] for row in rows) / max(1, words),
        "wer_b": sum(row["edits_b"] for row in rows) / max(1, words),
        "term_rate_a": sum(row["hits_a"] for row in rows) / max(1, mentions),
        "term_rate_b": sum(row["hits_b"] for row in rows) / max(1, mentions),
    }


def bootstrap(
    rows: list[dict[str, int]], iterations: int, rng: random.Random
) -> dict[str, object]:
    observed = aggregate(rows)
    wer_differences = []
    term_differences = []
    for _ in range(iterations):
        sample = [rows[rng.randrange(len(rows))] for _ in rows]
        metrics = aggregate(sample)
        wer_differences.append(metrics["wer_b"] - metrics["wer_a"])
        term_differences.append(
            metrics["term_rate_b"] - metrics["term_rate_a"]
        )
    return {
        "clips": len(rows),
        **observed,
        "wer_difference_b_minus_a": observed["wer_b"] - observed["wer_a"],
        "wer_difference_95_percentile_interval": [
            percentile(wer_differences, 0.025),
            percentile(wer_differences, 0.975),
        ],
        "bootstrap_fraction_b_lower_wer": sum(
            difference < 0 for difference in wer_differences
        )
        / iterations,
        "term_rate_difference_b_minus_a": (
            observed["term_rate_b"] - observed["term_rate_a"]
        ),
        "term_rate_difference_95_percentile_interval": [
            percentile(term_differences, 0.025),
            percentile(term_differences, 0.975),
        ],
        "bootstrap_fraction_b_higher_term_rate": sum(
            difference > 0 for difference in term_differences
        )
        / iterations,
    }


def write_markdown(
    path: Path,
    results: dict[str, dict[str, object]],
    label_a: str,
    label_b: str,
    excluded_clip_ids: list[str],
) -> None:
    lines = [
        "# Paired Bootstrap Comparison",
        "",
        f"Differences are `{label_b} - {label_a}`. Negative WER and positive term-rate differences favor `{label_b}`.",
    ]
    if excluded_clip_ids:
        lines.append(
            "Excluded clips: "
            + ", ".join(f"`{clip_id}`" for clip_id in excluded_clip_ids)
        )
    lines.extend(
        [
            "",
            "| slice | clips | WER diff | 95% interval | term-rate diff | 95% interval |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for slice_name, metrics in results.items():
        wer_interval = metrics["wer_difference_95_percentile_interval"]
        term_interval = metrics["term_rate_difference_95_percentile_interval"]
        lines.append(
            f"| {slice_name} | {metrics['clips']} | "
            f"{metrics['wer_difference_b_minus_a']:.4f} | "
            f"[{wer_interval[0]:.4f}, {wer_interval[1]:.4f}] | "
            f"{metrics['term_rate_difference_b_minus_a']:.4f} | "
            f"[{term_interval[0]:.4f}, {term_interval[1]:.4f}] |"
        )
    lines.extend(
        [
            "",
            "Intervals are clip-level paired percentile-bootstrap intervals, not proof of population-level significance. Small 12-clip slices are especially uncertain.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    references = {
        row["clip_id"]: row["reference_text"] for row in read_tsv(args.references)
    }
    manifest = {row["clip_id"]: row for row in read_tsv(args.manifest)}
    run_a = {row["clip_id"]: row["text"] for row in read_tsv(args.run_a)}
    run_b = {row["clip_id"]: row["text"] for row in read_tsv(args.run_b)}
    terms = read_terms(args.terms)
    expected_ids = set(references)
    if set(run_a) != expected_ids or set(run_b) != expected_ids:
        raise ValueError("both runs must exactly cover the frozen references")
    excluded = set(args.exclude_clip_id)
    unknown_exclusions = excluded - expected_ids
    if unknown_exclusions:
        raise ValueError(f"unknown excluded clip ids: {sorted(unknown_exclusions)}")
    references = {
        clip_id: reference
        for clip_id, reference in references.items()
        if clip_id not in excluded
    }

    slices = {
        "overall": list(references),
        **{
            split: [
                clip_id
                for clip_id in references
                if manifest[clip_id]["split"] == split
            ]
            for split in SPLITS
        },
        **{
            f"{partition}/{split}": [
                clip_id
                for clip_id in references
                if manifest[clip_id]["speaker_partition"] == partition
                and manifest[clip_id]["split"] == split
            ]
            for partition in PARTITIONS
            for split in SPLITS
        },
    }
    rng = random.Random(args.seed)
    results = {
        slice_name: bootstrap(
            clip_stats(clip_ids, references, run_a, run_b, terms),
            args.iterations,
            rng,
        )
        for slice_name, clip_ids in slices.items()
    }
    payload = {
        "label_a": args.label_a,
        "label_b": args.label_b,
        "iterations": args.iterations,
        "seed": args.seed,
        "excluded_clip_ids": sorted(excluded),
        "slices": results,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "bootstrap.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    write_markdown(
        args.out_dir / "BOOTSTRAP.md",
        results,
        args.label_a,
        args.label_b,
        sorted(excluded),
    )
    print(f"wrote paired bootstrap results under {args.out_dir}")


if __name__ == "__main__":
    main()
