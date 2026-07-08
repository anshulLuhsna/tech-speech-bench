#!/usr/bin/env python3
"""Prepare v1-small files for baseline ASR and scoring.

Default mode is read-only. Use --write after inspecting the summary.

Outputs:
  data/v1-small/prepared/manifest.tsv
  data/v1-small/prepared/references.tsv
  data/v1-small/prepared/domain_terms.txt
"""

from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path


DEFAULT_SOURCE_MANIFEST = Path("data/v1-small/manifest.tsv")
DEFAULT_TRAIN_DIR = Path("data/v1-small/tsb_v1-small-train")
DEFAULT_FULL_DIR = Path("data/v1-small/tsb_v1-small-full")
DEFAULT_OUT_DIR = Path("data/v1-small/prepared")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare v1-small ASR/scoring files.")
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--train-dir", type=Path, default=DEFAULT_TRAIN_DIR)
    parser.add_argument("--full-dir", type=Path, default=DEFAULT_FULL_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def audio_path_for(clip_id: str, train_dir: Path, full_dir: Path) -> Path:
    number = int(clip_id.rsplit("_", 1)[1])
    if number <= 40:
        return train_dir / f"{clip_id}.m4a"
    return full_dir / f"{clip_id}.m4a"


def duration_seconds(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def build_outputs(
    source_rows: list[dict[str, str]], train_dir: Path, full_dir: Path
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[str]]:
    manifest_rows = []
    reference_rows = []
    terms = set()

    for row in source_rows:
        clip_id = row["id"]
        path = audio_path_for(clip_id, train_dir, full_dir)
        if not path.exists():
            raise FileNotFoundError(path)

        rel_path = path.as_posix()
        for term in row["terms"].split(";"):
            clean = term.strip()
            if clean:
                terms.add(clean)

        manifest_rows.append(
            {
                "clip_id": clip_id,
                "speaker_id": "anshul",
                "split": row["split"],
                "condition": "quiet",
                "category": row["category"],
                "audio_path": rel_path,
                "duration_seconds": f"{duration_seconds(path):.3f}",
                "size_bytes": str(path.stat().st_size),
                "transcript_status": "expected_reference_from_manifest",
            }
        )
        reference_rows.append(
            {
                "clip_id": clip_id,
                "reference_text": row["utterance"],
            }
        )

    return manifest_rows, reference_rows, sorted(terms, key=str.casefold)


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    source_rows = read_rows(args.source_manifest)
    manifest_rows, reference_rows, terms = build_outputs(
        source_rows, args.train_dir, args.full_dir
    )

    split_counts: dict[str, int] = {}
    for row in manifest_rows:
        split_counts[row["split"]] = split_counts.get(row["split"], 0) + 1

    print(f"rows: {len(manifest_rows)}")
    print(f"splits: {split_counts}")
    print(f"terms: {len(terms)}")
    print(f"out_dir: {args.out_dir}")

    if not args.write:
        print("dry run only. pass --write to create prepared v1-small files.")
        return

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(args.out_dir / "manifest.tsv", manifest_rows)
    write_tsv(args.out_dir / "references.tsv", reference_rows)
    (args.out_dir / "domain_terms.txt").write_text(
        "\n".join(terms) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {args.out_dir / 'manifest.tsv'}")
    print(f"wrote {args.out_dir / 'references.tsv'}")
    print(f"wrote {args.out_dir / 'domain_terms.txt'}")


if __name__ == "__main__":
    main()
