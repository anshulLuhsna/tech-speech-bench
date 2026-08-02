#!/usr/bin/env python3
"""Build one-epoch human plus real-term and compositional synthetic metadata."""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HUMAN_TRAIN = REPO_ROOT / "data/v2/lora/train.jsonl"
DEFAULT_HUMAN_DEV = REPO_ROOT / "data/v2/lora/dev.jsonl"
DEFAULT_REAL_SYNTH = REPO_ROOT / "data/synthetic/kokoro-v1/private/training/manifest.tsv"
DEFAULT_COMPOSITIONAL_SYNTH = (
    REPO_ROOT / "data/synthetic/kokoro-compositional-v1/private/manifest.tsv"
)
DEFAULT_TERMS = REPO_ROOT / "data/v2/domain_terms.tsv"
DEFAULT_OUT_DIR = REPO_ROOT / "data/synthetic/kokoro-additive-v2/lora"
HUMAN_REPEATS = 20
EFFECTIVE_BATCH_SIZE = 8
SEED = 41


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--human-train", type=Path, default=DEFAULT_HUMAN_TRAIN)
    parser.add_argument("--human-dev", type=Path, default=DEFAULT_HUMAN_DEV)
    parser.add_argument("--real-synthetic", type=Path, default=DEFAULT_REAL_SYNTH)
    parser.add_argument(
        "--compositional-synthetic", type=Path, default=DEFAULT_COMPOSITIONAL_SYNTH
    )
    parser.add_argument("--terms", type=Path, default=DEFAULT_TERMS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def synthetic_records(
    rows: list[dict[str, str]], source_kind: str
) -> list[dict[str, Any]]:
    return [
        {
            "audio": row["relative_audio_path"],
            "text": row["transcript"],
            "clip_id": row["clip_id"],
            "source_clip_id": row["clip_id"],
            "source_kind": source_kind,
            "speaker_id": row["voice_id"],
            "speaker_partition": "synthetic_train",
            "split": "train",
            "terms": row["target_terms"].split(";"),
        }
        for row in rows
    ]


def repeated_human_records(
    rows: list[dict[str, Any]], repeats: int, seed: int
) -> list[dict[str, Any]]:
    repeated = []
    for cycle in range(repeats):
        shuffled = list(rows)
        random.Random(seed + cycle).shuffle(shuffled)
        for row in shuffled:
            repeated.append(
                {
                    **row,
                    "clip_id": f"humanadd_{cycle + 1:02d}_{row['clip_id']}",
                    "source_clip_id": row["clip_id"],
                    "source_kind": "human",
                }
            )
    return repeated


def main() -> None:
    args = parse_args()
    human_train = read_jsonl(args.human_train)
    human_dev = read_jsonl(args.human_dev)
    real_rows = read_tsv(args.real_synthetic)
    compositional_rows = read_tsv(args.compositional_synthetic)
    benchmark_terms = {row["term"] for row in read_tsv(args.terms)}

    if len(human_train) != 64 or len(human_dev) != 16:
        raise ValueError("expected 64 human train and 16 human dev records")
    if len(real_rows) != 248:
        raise ValueError(f"expected 248 real-term synthetic clips, found {len(real_rows)}")
    if len(compositional_rows) != 384:
        raise ValueError(
            f"expected 384 compositional synthetic clips, found {len(compositional_rows)}"
        )

    compositional_terms = {
        term
        for row in compositional_rows
        for term in row["target_terms"].split(";")
    }
    overlap = compositional_terms & benchmark_terms
    if overlap:
        raise ValueError(f"compositional term leakage: {sorted(overlap)}")

    human = repeated_human_records(human_train, HUMAN_REPEATS, args.seed)
    real = synthetic_records(real_rows, "kokoro_real_term")
    compositional = synthetic_records(
        compositional_rows, "kokoro_compositional_unseen_term"
    )
    training = human + real + compositional
    if len(training) % EFFECTIVE_BATCH_SIZE:
        raise ValueError("training records must divide the effective batch size")
    if len({row["clip_id"] for row in training}) != len(training):
        raise ValueError("training clip ids are not unique")

    plan = {
        "seed": args.seed,
        "human_source_records": len(human_train),
        "human_repeats_per_source": HUMAN_REPEATS,
        "human_training_records": len(human),
        "real_term_synthetic_records": len(real),
        "compositional_synthetic_records": len(compositional),
        "compositional_unique_terms": len(compositional_terms),
        "compositional_benchmark_term_overlap": len(overlap),
        "total_training_records": len(training),
        "effective_batch_size": EFFECTIVE_BATCH_SIZE,
        "optimizer_updates_for_one_epoch": len(training) // EFFECTIVE_BATCH_SIZE,
        "design": (
            "one full pass over every synthetic clip plus twenty exposures to each "
            "human source; compositional full terms are disjoint from the benchmark"
        ),
    }
    print(json.dumps(plan, indent=2))
    if not args.write:
        print("dry run only; pass --write to create LoRA metadata")
        return

    write_jsonl(args.out_dir / "train.jsonl", training)
    write_jsonl(args.out_dir / "dev.jsonl", human_dev)
    (args.out_dir / "experiment-plan.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote additive v2 metadata under {args.out_dir}")


if __name__ == "__main__":
    main()
