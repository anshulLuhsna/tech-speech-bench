#!/usr/bin/env python3
"""Compare ASR runs across v2 speaker-partition and term-split slices."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from compare_transcript_runs import parse_run_spec, read_terms, score_run


DEFAULT_REFERENCES = Path("data/v2/references.tsv")
DEFAULT_MANIFEST = Path("data/v2/manifest.tsv")
DEFAULT_TERMS = Path("data/v2/domain_terms.txt")
PARTITIONS = ("train_speaker", "dev_speaker", "test_speaker")
SPLITS = ("train", "heldout_real", "heldout_fake")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare v2 runs by benchmark slice.")
    parser.add_argument("--references", type=Path, default=DEFAULT_REFERENCES)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--terms", type=Path, default=DEFAULT_TERMS)
    parser.add_argument("--run", action="append", required=True, metavar="LABEL=TSV")
    parser.add_argument("--out-dir", type=Path, required=True)
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_markdown(path: Path, comparison: dict[str, object]) -> None:
    lines = [
        "# V2 Slice Comparison",
        "",
        "| speaker partition | term split | clips | run | WER | CER | term exact | term rate |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for partition in PARTITIONS:
        for split in SPLITS:
            slice_name = f"{partition}/{split}"
            for label, slices in comparison.items():
                metrics = slices[slice_name]
                lines.append(
                    f"| {partition} | {split} | {metrics['clips']} | {label} | "
                    f"{metrics['wer']:.4f} | {metrics['cer']:.4f} | "
                    f"{metrics['domain_term_exact_hits']} / {metrics['domain_term_mentions']} | "
                    f"{metrics['domain_term_exact_match_rate']:.4f} |"
                )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    references = {
        row["clip_id"]: row["reference_text"]
        for row in read_tsv(args.references)
    }
    manifest = {row["clip_id"]: row for row in read_tsv(args.manifest)}
    terms = read_terms(args.terms)

    comparison: dict[str, dict[str, object]] = {}
    for run_spec in args.run:
        label, transcripts_path = parse_run_spec(run_spec)
        comparison[label] = {}
        for partition in PARTITIONS:
            for split in SPLITS:
                selected_refs = {
                    clip_id: reference
                    for clip_id, reference in references.items()
                    if manifest[clip_id]["speaker_partition"] == partition
                    and manifest[clip_id]["split"] == split
                }
                slice_name = f"{partition}/{split}"
                comparison[label][slice_name] = score_run(
                    transcripts_path,
                    selected_refs,
                    manifest,
                    terms,
                )["overall"]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "comparison.json").write_text(
        json.dumps(comparison, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_markdown(args.out_dir / "README.md", comparison)
    print(json.dumps(comparison, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
