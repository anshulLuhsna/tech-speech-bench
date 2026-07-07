#!/usr/bin/env python3
"""Run a faster-whisper baseline over a TechSpeechBench manifest."""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

from faster_whisper import WhisperModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe TechSpeechBench clips with faster-whisper."
    )
    parser.add_argument("--manifest", default="data/v0/manifest.tsv")
    parser.add_argument("--data-root", default="data/v0")
    parser.add_argument("--out-dir", default="results/baselines/faster-whisper-base-en")
    parser.add_argument("--model", default="base.en")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--language", default="en")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def read_manifest(path: Path, limit: int | None) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    return rows[:limit] if limit else rows


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifest)
    data_root = Path(args.data_root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = read_manifest(manifest_path, args.limit)

    model = WhisperModel(
        args.model,
        device=args.device,
        compute_type=args.compute_type,
    )

    transcript_rows: list[dict[str, object]] = []
    jsonl_path = out_dir / "transcripts.jsonl"
    started = time.time()

    with jsonl_path.open("w", encoding="utf-8") as jsonl:
        for index, row in enumerate(rows, start=1):
            clip_id = row["clip_id"]
            audio_path = data_root / row["audio_path"]
            clip_started = time.time()
            segments, info = model.transcribe(
                str(audio_path),
                language=args.language,
                beam_size=args.beam_size,
                vad_filter=False,
            )
            segment_payload = [
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "avg_logprob": segment.avg_logprob,
                    "no_speech_prob": segment.no_speech_prob,
                }
                for segment in segments
            ]
            text = " ".join(segment["text"].strip() for segment in segment_payload).strip()
            elapsed = time.time() - clip_started

            payload = {
                "clip_id": clip_id,
                "audio_path": row["audio_path"],
                "split": row["split"],
                "category": row["category"],
                "model": args.model,
                "device": args.device,
                "compute_type": args.compute_type,
                "language": args.language,
                "duration_seconds": float(row["duration_seconds"]),
                "transcription_seconds": elapsed,
                "detected_language": info.language,
                "language_probability": info.language_probability,
                "text": text,
                "segments": segment_payload,
            }
            jsonl.write(json.dumps(payload, ensure_ascii=False) + "\n")

            transcript_rows.append(
                {
                    "clip_id": clip_id,
                    "split": row["split"],
                    "category": row["category"],
                    "duration_seconds": row["duration_seconds"],
                    "transcription_seconds": f"{elapsed:.3f}",
                    "text": text,
                }
            )
            print(f"[{index:03d}/{len(rows):03d}] {clip_id}: {text}")

    write_tsv(out_dir / "transcripts.tsv", transcript_rows)
    metadata = {
        "system": "faster-whisper",
        "model": args.model,
        "device": args.device,
        "compute_type": args.compute_type,
        "language": args.language,
        "beam_size": args.beam_size,
        "manifest": str(manifest_path),
        "data_root": str(data_root),
        "clips": len(rows),
        "total_seconds": round(time.time() - started, 3),
        "outputs": ["transcripts.jsonl", "transcripts.tsv"],
    }
    (out_dir / "run.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

