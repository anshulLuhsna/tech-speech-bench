#!/usr/bin/env python3
"""Check v1-small audio metadata before ASR or fine-tuning.

This is a metadata gate, not an ASR script. It does not transcribe audio.

Examples:
  uv run python scripts/check_v1_small_audio.py
  uv run python scripts/check_v1_small_audio.py --write
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path


DEFAULT_MANIFEST = Path("data/v1-small/manifest.tsv")
DEFAULT_TRAIN_DIR = Path("data/v1-small/tsb_v1-small-train")
DEFAULT_FULL_DIR = Path("data/v1-small/tsb_v1-small-full")
DEFAULT_OUT = Path("data/v1-small/audio-metadata.tsv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check v1-small audio metadata.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--train-dir", type=Path, default=DEFAULT_TRAIN_DIR)
    parser.add_argument("--full-dir", type=Path, default=DEFAULT_FULL_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--expected-sample-rate", default="48000")
    parser.add_argument("--expected-channels", default="2")
    parser.add_argument("--expected-codec", default="aac")
    parser.add_argument("--min-duration", type=float, default=2.0)
    parser.add_argument("--max-duration", type=float, default=20.0)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write metadata TSV. Without this, only prints the check report.",
    )
    return parser.parse_args()


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def expected_audio_path(clip_id: str, train_dir: Path, full_dir: Path) -> Path:
    number = int(clip_id.rsplit("_", 1)[1])
    if number <= 40:
        return train_dir / f"{clip_id}.m4a"
    return full_dir / f"{clip_id}.m4a"


def ffprobe(path: Path) -> dict[str, str]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=codec_name,sample_rate,channels,channel_layout,duration",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout)
    streams = payload.get("streams", [])
    if not streams:
        raise ValueError("no audio stream found")
    stream = streams[0]
    return {key: str(stream.get(key, "")) for key in stream}


def build_report(args: argparse.Namespace) -> list[dict[str, str]]:
    rows = []
    for manifest_row in read_manifest(args.manifest):
        clip_id = manifest_row["id"]
        audio_path = expected_audio_path(clip_id, args.train_dir, args.full_dir)
        row = {
            "clip_id": clip_id,
            "split": manifest_row["split"],
            "category": manifest_row["category"],
            "audio_path": str(audio_path),
            "exists": "yes" if audio_path.exists() else "no",
            "codec_name": "",
            "sample_rate": "",
            "channels": "",
            "channel_layout": "",
            "duration": "",
            "status": "ok",
            "issues": "",
        }

        issues = []
        if not audio_path.exists():
            issues.append("missing_file")
            row["status"] = "fail"
            row["issues"] = ";".join(issues)
            rows.append(row)
            continue

        try:
            meta = ffprobe(audio_path)
            row.update(meta)
        except Exception as exc:  # noqa: BLE001 - report and continue through all files.
            issues.append(f"ffprobe_error:{exc}")
            row["status"] = "fail"
            row["issues"] = ";".join(issues)
            rows.append(row)
            continue

        duration = float(row["duration"] or 0)
        if row["codec_name"] != args.expected_codec:
            issues.append(f"codec:{row['codec_name']}")
        if row["sample_rate"] != args.expected_sample_rate:
            issues.append(f"sample_rate:{row['sample_rate']}")
        if row["channels"] != args.expected_channels:
            issues.append(f"channels:{row['channels']}")
        if duration < args.min_duration:
            issues.append(f"duration_too_short:{duration:.3f}")
        if duration > args.max_duration:
            issues.append(f"duration_too_long:{duration:.3f}")

        if issues:
            row["status"] = "fail"
            row["issues"] = ";".join(issues)
        rows.append(row)
    return rows


def print_summary(rows: list[dict[str, str]]) -> None:
    durations = [float(row["duration"]) for row in rows if row["duration"]]
    failures = [row for row in rows if row["status"] != "ok"]
    split_counts: dict[str, int] = {}
    for row in rows:
        split_counts[row["split"]] = split_counts.get(row["split"], 0) + 1

    print(f"rows: {len(rows)}")
    print(f"audio present: {sum(row['exists'] == 'yes' for row in rows)}")
    print(f"failures: {len(failures)}")
    print(f"splits: {split_counts}")
    if durations:
        print(f"duration_seconds_min: {min(durations):.3f}")
        print(f"duration_seconds_max: {max(durations):.3f}")
    print()

    if failures:
        print("failures:")
        for row in failures:
            print(f"- {row['clip_id']}: {row['issues']}")
    else:
        print("metadata gate passed.")


def write_tsv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {path}")


def main() -> None:
    args = parse_args()
    rows = build_report(args)
    print_summary(rows)
    if args.write:
        write_tsv(rows, args.out)


if __name__ == "__main__":
    main()
