#!/usr/bin/env python3
"""Build six ordered listening montages for the Kokoro pronunciation gate."""

from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW = (
    REPO_ROOT / "data/synthetic/kokoro-v1/pronunciation-review.tsv"
)
DEFAULT_MANIFEST = (
    REPO_ROOT
    / "data/synthetic/kokoro-v1/private/pronunciation-gate/manifest.tsv"
)
DEFAULT_OUT_DIR = (
    REPO_ROOT / "data/synthetic/kokoro-v1/private/pronunciation-gate/review"
)
GROUPS = (
    ("kpg001", "kpg002", "kpg003", "kpg004", "kpg005", "kpg006"),
    ("kpg007", "kpg008", "kpg009", "kpg010", "kpg011"),
    ("kpg012", "kpg013", "kpg014", "kpg015", "kpg016"),
    ("kpg017", "kpg018", "kpg019", "kpg020", "kpg021"),
    ("kpg022", "kpg023", "kpg024", "kpg025", "kpg026"),
    ("kpg027", "kpg028", "kpg029", "kpg030", "kpg031"),
)
SILENCE_SECONDS = 0.75
SAMPLE_RATE = 24_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument(
        "--gate-id",
        action="append",
        default=[],
        help="Build one replacement montage from these gate ids, in order.",
    )
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def build_montage(inputs: list[Path], output: Path) -> None:
    command = ["ffmpeg", "-v", "error", "-y"]
    for input_path in inputs:
        command.extend(["-i", str(input_path)])
    silence_index = len(inputs)
    command.extend(
        [
            "-f",
            "lavfi",
            "-t",
            str(SILENCE_SECONDS),
            "-i",
            f"anullsrc=r={SAMPLE_RATE}:cl=mono",
        ]
    )
    filter_parts: list[str] = []
    for index in range(len(inputs)):
        filter_parts.append(f"[{index}:a]")
        if index < len(inputs) - 1:
            filter_parts.append(f"[{silence_index}:a]")
    filter_graph = "".join(filter_parts) + (
        f"concat=n={len(filter_parts)}:v=0:a=1[out]"
    )
    command.extend(
        [
            "-filter_complex",
            filter_graph,
            "-map",
            "[out]",
            "-c:a",
            "pcm_s16le",
            str(output),
        ]
    )
    subprocess.run(command, check=True)


def main() -> None:
    args = parse_args()
    review_rows = read_tsv(args.review)
    manifest_rows = read_tsv(args.manifest)
    review_by_id = {row["gate_id"]: row for row in review_rows}
    manifest_by_id = {row["utterance_id"]: row for row in manifest_rows}

    expected_ids = {gate_id for group in GROUPS for gate_id in group}
    if len(expected_ids) != 31:
        raise ValueError("montage groups must contain 31 unique gate ids")
    if set(review_by_id) != expected_ids or set(manifest_by_id) != expected_ids:
        raise ValueError("review, manifest, and montage ids do not match")

    if args.gate_id:
        if len(args.gate_id) != len(set(args.gate_id)):
            raise ValueError("replacement gate ids must be unique")
        unknown_ids = set(args.gate_id) - expected_ids
        if unknown_ids:
            raise ValueError(f"unknown replacement gate ids: {sorted(unknown_ids)}")
        groups = (tuple(args.gate_id),)
        filename_prefix = "replacement"
        index_filename = "replacement-review-index.tsv"
    else:
        groups = GROUPS
        filename_prefix = "montage"
        index_filename = "review-index.tsv"

    args.out_dir.mkdir(parents=True, exist_ok=True)
    index_rows: list[dict[str, object]] = []
    for group_number, group in enumerate(groups, start=1):
        filename = (
            f"{filename_prefix}-{group_number:02d}-"
            f"{group[0]}-{group[-1]}.wav"
        )
        output = args.out_dir / filename
        inputs = [
            REPO_ROOT / manifest_by_id[gate_id]["relative_audio_path"]
            for gate_id in group
        ]
        missing = [str(path) for path in inputs if not path.exists()]
        if missing:
            raise FileNotFoundError("missing montage inputs:\n" + "\n".join(missing))
        build_montage(inputs, output)

        for position, gate_id in enumerate(group, start=1):
            review = review_by_id[gate_id]
            index_rows.append(
                {
                    "montage": filename,
                    "position": position,
                    "gate_id": gate_id,
                    "term": review["term"],
                    "expected_to_sound_like": review[
                        "expected_to_sound_like"
                    ],
                    "audio_review_status": "pending",
                    "review_note": "",
                }
            )
        print(f"wrote {output}")

    index_path = args.out_dir / index_filename
    with index_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(index_rows[0]), delimiter="\t"
        )
        writer.writeheader()
        writer.writerows(index_rows)
    print(f"wrote {index_path}")


if __name__ == "__main__":
    main()
