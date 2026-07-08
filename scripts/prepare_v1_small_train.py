#!/usr/bin/env python3
"""Prepare TechSpeechBench v1-small train metadata.

Default mode is read-only. It prints the train audio/transcript mapping so you
can inspect it before writing any derived files.

Examples:
  uv run python scripts/prepare_v1_small_train.py
  uv run python scripts/prepare_v1_small_train.py --write
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


DEFAULT_MANIFEST = Path("data/v1-small/manifest.tsv")
DEFAULT_AUDIO_DIR = Path("data/v1-small/tsb_v1-small-train")
DEFAULT_OUT_DIR = Path("data/v1-small/train")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect or write v1-small train metadata from the manifest and audio files."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--audio-dir", type=Path, default=DEFAULT_AUDIO_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write references.tsv and metadata.jsonl. Without this, the script only prints a preview.",
    )
    return parser.parse_args()


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def build_rows(manifest: list[dict[str, str]], audio_dir: Path) -> list[dict[str, str]]:
    train_rows = [row for row in manifest if row["split"] == "train"]
    rows = []
    for row in train_rows:
        clip_id = row["id"]
        audio_path = audio_dir / f"{clip_id}.m4a"
        rows.append(
            {
                "id": clip_id,
                "audio_path": str(audio_path),
                "exists": "yes" if audio_path.exists() else "no",
                "terms": row["terms"],
                "text": row["utterance"],
            }
        )
    return rows


def print_preview(rows: list[dict[str, str]]) -> None:
    print(f"train rows: {len(rows)}")
    print(f"audio present: {sum(row['exists'] == 'yes' for row in rows)}")
    print(f"audio missing: {sum(row['exists'] == 'no' for row in rows)}")
    print()
    for row in rows:
        print(f"{row['id']}  exists={row['exists']}  {row['audio_path']}")
        print(f"  terms: {row['terms']}")
        print(f"  text:  {row['text']}")
        print()


def write_outputs(rows: list[dict[str, str]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    references_path = out_dir / "references.tsv"
    with references_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["clip_id", "audio_path", "reference_text", "terms"],
            delimiter="\t",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "clip_id": row["id"],
                    "audio_path": row["audio_path"],
                    "reference_text": row["text"],
                    "terms": row["terms"],
                }
            )

    metadata_path = out_dir / "metadata.jsonl"
    with metadata_path.open("w", encoding="utf-8") as f:
        for row in rows:
            record = {
                "audio": row["audio_path"],
                "text": row["text"],
                "clip_id": row["id"],
                "terms": row["terms"].split(";"),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"wrote {references_path}")
    print(f"wrote {metadata_path}")


def main() -> None:
    args = parse_args()
    manifest = read_manifest(args.manifest)
    rows = build_rows(manifest, args.audio_dir)
    missing = [row for row in rows if row["exists"] == "no"]

    print_preview(rows)

    if missing:
        raise SystemExit("missing audio files; fix file names before writing metadata")

    if args.write:
        write_outputs(rows, args.out_dir)
    else:
        print("dry run only. pass --write to create derived train metadata.")


if __name__ == "__main__":
    main()
