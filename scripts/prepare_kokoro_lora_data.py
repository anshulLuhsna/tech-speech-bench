#!/usr/bin/env python3
"""Build matched synthetic-only and balanced Kokoro v1 LoRA metadata."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SYNTHETIC_MANIFEST = (
    REPO_ROOT / "data/synthetic/kokoro-v1/private/training/manifest.tsv"
)
DEFAULT_HUMAN_TRAIN = REPO_ROOT / "data/v2/lora/train.jsonl"
DEFAULT_HUMAN_DEV = REPO_ROOT / "data/v2/lora/dev.jsonl"
DEFAULT_TERMS = REPO_ROOT / "data/v2/domain_terms.tsv"
DEFAULT_OUT_DIR = REPO_ROOT / "data/synthetic/kokoro-v1/lora"
SEED = 13


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--synthetic-manifest", type=Path, default=DEFAULT_SYNTHETIC_MANIFEST
    )
    parser.add_argument("--human-train", type=Path, default=DEFAULT_HUMAN_TRAIN)
    parser.add_argument("--human-dev", type=Path, default=DEFAULT_HUMAN_DEV)
    parser.add_argument("--terms", type=Path, default=DEFAULT_TERMS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def synthetic_records(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "audio": row["relative_audio_path"],
            "text": row["transcript"],
            "clip_id": row["clip_id"],
            "source_clip_id": row["clip_id"],
            "source_kind": "kokoro_synthetic",
            "speaker_id": row["voice_id"],
            "speaker_partition": "synthetic_train",
            "split": "train",
            "terms": row["target_terms"].split(";"),
        }
        for row in rows
    ]


def balanced_human_records(
    human_rows: list[dict[str, Any]], count: int, seed: int
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    cycle = 0
    while len(selected) < count:
        shuffled = list(human_rows)
        random.Random(seed + cycle).shuffle(shuffled)
        selected.extend(shuffled)
        cycle += 1
    selected = selected[:count]
    return [
        {
            **row,
            "clip_id": f"humanmix_{index:03d}_{row['clip_id']}",
            "source_clip_id": row["clip_id"],
            "source_kind": "human",
        }
        for index, row in enumerate(selected, start=1)
    ]


def main() -> None:
    args = parse_args()
    synthetic_manifest = read_tsv(args.synthetic_manifest)
    human_train = read_jsonl(args.human_train)
    human_dev = read_jsonl(args.human_dev)
    term_rows = read_tsv(args.terms)
    train_terms = {row["term"] for row in term_rows if row["split"] == "train"}
    heldout_terms = {row["term"] for row in term_rows if row["split"] != "train"}

    if len(synthetic_manifest) != 248:
        raise ValueError(
            f"expected 248 synthetic clips, found {len(synthetic_manifest)}"
        )
    if len(human_train) != 64 or len(human_dev) != 16:
        raise ValueError(
            f"expected 64 human train and 16 dev, got {len(human_train)} and {len(human_dev)}"
        )
    for row in synthetic_manifest:
        terms = set(row["target_terms"].split(";"))
        if not terms <= train_terms or terms & heldout_terms:
            raise ValueError(f"{row['clip_id']}: non-train term in synthetic data")
        if not (REPO_ROOT / row["relative_audio_path"]).exists():
            raise FileNotFoundError(row["relative_audio_path"])

    train_source_ids = {row["clip_id"] for row in human_train}
    dev_ids = {row["clip_id"] for row in human_dev}
    if train_source_ids & dev_ids:
        raise ValueError("human train and dev clip ids overlap")

    synthetic_only = synthetic_records(synthetic_manifest)
    balanced_human = balanced_human_records(
        human_train, len(synthetic_only), args.seed
    )
    balanced: list[dict[str, Any]] = []
    for synthetic, human in zip(synthetic_only, balanced_human, strict=True):
        balanced.extend((synthetic, human))

    if len({row["clip_id"] for row in synthetic_only}) != 248:
        raise ValueError("synthetic-only clip ids are not unique")
    if len({row["clip_id"] for row in balanced}) != 496:
        raise ValueError("balanced clip ids are not unique")

    plan = {
        "seed": args.seed,
        "optimizer_update_budget": 160,
        "effective_batch_size": 8,
        "human_only_reference_records": 64,
        "synthetic_only_records": len(synthetic_only),
        "balanced_records": len(balanced),
        "balanced_human_records": len(balanced_human),
        "balanced_synthetic_records": len(synthetic_only),
        "human_dev_records": len(human_dev),
        "human_train_sha256": sha256(args.human_train),
        "human_dev_sha256": sha256(args.human_dev),
        "synthetic_manifest_sha256": sha256(args.synthetic_manifest),
        "selection_rule": (
            "all 248 synthetic clips plus 248 deterministic human draws; "
            "human rows are shuffled in complete seed-offset cycles"
        ),
    }
    print(json.dumps(plan, indent=2))
    if not args.write:
        print("dry run only; pass --write to create LoRA metadata")
        return

    write_jsonl(args.out_dir / "synthetic-only.jsonl", synthetic_only)
    write_jsonl(args.out_dir / "balanced.jsonl", balanced)
    write_jsonl(args.out_dir / "human-dev.jsonl", human_dev)
    (args.out_dir / "experiment-plan.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote matched LoRA metadata under {args.out_dir}")


if __name__ == "__main__":
    main()
