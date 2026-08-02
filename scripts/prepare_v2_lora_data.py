#!/usr/bin/env python3
"""Build leakage-safe v2 LoRA train and dev metadata.

Training uses train-vocabulary clips from s01-s04. Development uses only
train-vocabulary clips from unseen speaker s05. Speaker s06 and every heldout
term clip remain outside training and development metadata.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "data/v2/manifest.tsv"
DEFAULT_REFERENCES = REPO_ROOT / "data/v2/references.tsv"
DEFAULT_TERMS = REPO_ROOT / "data/v2/domain_terms.tsv"
DEFAULT_OUT_DIR = REPO_ROOT / "data/v2/lora"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare v2 LoRA metadata.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--references", type=Path, default=DEFAULT_REFERENCES)
    parser.add_argument("--terms", type=Path, default=DEFAULT_TERMS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def terms_for_text(text: str, term_rows: list[dict[str, str]]) -> list[str]:
    return [row["term"] for row in term_rows if row["term"] in text]


def build_records(
    manifest_rows: list[dict[str, str]],
    references: dict[str, str],
    term_rows: list[dict[str, str]],
    partition: str,
) -> list[dict[str, object]]:
    records = []
    for row in manifest_rows:
        if row["speaker_partition"] != partition or row["split"] != "train":
            continue
        reference = references[row["clip_id"]]
        records.append(
            {
                "audio": str(Path("data/v2") / row["audio_path"]),
                "text": reference,
                "clip_id": row["clip_id"],
                "speaker_id": row["speaker_id"],
                "speaker_partition": row["speaker_partition"],
                "split": row["split"],
                "terms": terms_for_text(reference, term_rows),
            }
        )
    return records


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    manifest_rows = read_tsv(args.manifest)
    references = {
        row["clip_id"]: row["reference_text"]
        for row in read_tsv(args.references)
    }
    term_rows = read_tsv(args.terms)

    train_records = build_records(
        manifest_rows, references, term_rows, "train_speaker"
    )
    dev_records = build_records(
        manifest_rows, references, term_rows, "dev_speaker"
    )
    test_speaker_rows = [
        row for row in manifest_rows if row["speaker_partition"] == "test_speaker"
    ]

    if len(train_records) != 64:
        raise ValueError(f"expected 64 train records, found {len(train_records)}")
    if len(dev_records) != 16:
        raise ValueError(f"expected 16 dev records, found {len(dev_records)}")
    if len(test_speaker_rows) != 40:
        raise ValueError(
            f"expected 40 untouched test-speaker rows, found {len(test_speaker_rows)}"
        )

    print("train: 64 clips from s01-s04, train vocabulary only")
    print("dev: 16 clips from unseen speaker s05, train vocabulary only")
    print("test speaker: all 40 s06 clips remain untouched")
    print("heldout_real and heldout_fake: absent from train/dev metadata")

    if not args.write:
        print("dry run only. pass --write to create LoRA metadata")
        return

    write_jsonl(args.out_dir / "train.jsonl", train_records)
    write_jsonl(args.out_dir / "dev.jsonl", dev_records)
    print(f"wrote {args.out_dir / 'train.jsonl'}")
    print(f"wrote {args.out_dir / 'dev.jsonl'}")


if __name__ == "__main__":
    main()
