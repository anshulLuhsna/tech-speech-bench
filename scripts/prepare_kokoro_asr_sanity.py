#!/usr/bin/env python3
"""Build private ASR-sanity inputs from the Kokoro training manifest."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = (
    REPO_ROOT / "data/synthetic/kokoro-v1/private/training/manifest.tsv"
)
DEFAULT_OUT_DIR = (
    REPO_ROOT / "data/synthetic/kokoro-v1/private/training/asr-sanity-inputs"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


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
    source_rows = read_tsv(args.source)
    if len(source_rows) != 248:
        raise ValueError(f"expected 248 source rows, found {len(source_rows)}")

    manifest_rows = [
        {
            "clip_id": row["clip_id"],
            "audio_path": row["relative_audio_path"],
            "duration_seconds": row["duration_seconds"],
            "split": "train",
            "category": "kokoro_synthetic",
        }
        for row in source_rows
    ]
    reference_rows = [
        {"clip_id": row["clip_id"], "reference_text": row["transcript"]}
        for row in source_rows
    ]
    write_tsv(args.out_dir / "manifest.tsv", manifest_rows)
    write_tsv(args.out_dir / "references.tsv", reference_rows)
    print(f"wrote ASR sanity inputs for {len(source_rows)} clips")


if __name__ == "__main__":
    main()
