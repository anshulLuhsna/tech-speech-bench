#!/usr/bin/env python3
"""Transcribe TechSpeechBench clips with Whisper, optionally using LoRA."""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path


DEFAULT_MANIFEST = Path("data/v1-small/prepared/manifest.tsv")
DEFAULT_ADAPTER_DIR = Path("results/finetunes/whisper-base-en-lora-v1-small")
DEFAULT_OUT_DIR = Path("results/finetunes/whisper-base-en-lora-v1-small/eval")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe with Whisper, optionally using a LoRA adapter."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("."),
        help="Resolve relative manifest audio paths against this directory.",
    )
    parser.add_argument("--adapter-dir", type=Path, default=DEFAULT_ADAPTER_DIR)
    parser.add_argument(
        "--base-model-only",
        action="store_true",
        help="Skip adapter loading to produce a controlled base-model baseline.",
    )
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--base-model", default="openai/whisper-base.en")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--language", default="english")
    parser.add_argument("--task", default="transcribe")
    parser.add_argument("--num-beams", type=int, default=5)
    parser.add_argument("--max-new-tokens", type=int, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--clip-id",
        action="append",
        help="Only transcribe this clip id. Can be passed multiple times.",
    )
    return parser.parse_args()


def read_manifest(
    path: Path,
    limit: int | None,
    clip_ids: list[str] | None,
) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if clip_ids:
        wanted = set(clip_ids)
        rows = [row for row in rows if row["clip_id"] in wanted]
    return rows[:limit] if limit else rows


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()

    import librosa
    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = read_manifest(args.manifest, args.limit, args.clip_id)

    processor = WhisperProcessor.from_pretrained(
        args.base_model,
        language=args.language,
        task=args.task,
    )
    model = WhisperForConditionalGeneration.from_pretrained(args.base_model)
    if not args.base_model_only:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, args.adapter_dir)
    model.eval()
    model.to(args.device)

    forced_decoder_ids = processor.get_decoder_prompt_ids(
        language=args.language,
        task=args.task,
    )

    transcript_rows: list[dict[str, object]] = []
    jsonl_path = out_dir / "transcripts.jsonl"
    started = time.time()

    with jsonl_path.open("w", encoding="utf-8") as jsonl:
        for index, row in enumerate(rows, start=1):
            clip_started = time.time()
            audio_path = args.data_root / row["audio_path"]
            audio, _ = librosa.load(audio_path, sr=16000, mono=True)
            inputs = processor.feature_extractor(
                audio,
                sampling_rate=16000,
                return_tensors="pt",
            )
            input_features = inputs.input_features.to(args.device)
            with torch.no_grad():
                generation_kwargs = {
                    "forced_decoder_ids": forced_decoder_ids,
                    "num_beams": args.num_beams,
                }
                if args.max_new_tokens is not None:
                    generation_kwargs["max_new_tokens"] = args.max_new_tokens
                predicted_ids = model.generate(input_features, **generation_kwargs)
            text = processor.batch_decode(
                predicted_ids,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0].strip()
            elapsed = time.time() - clip_started

            payload = {
                "clip_id": row["clip_id"],
                "audio_path": row["audio_path"],
                "split": row["split"],
                "category": row["category"],
                "base_model": args.base_model,
                "adapter_dir": None if args.base_model_only else str(args.adapter_dir),
                "device": args.device,
                "duration_seconds": float(row["duration_seconds"]),
                "transcription_seconds": elapsed,
                "text": text,
            }
            jsonl.write(json.dumps(payload, ensure_ascii=False) + "\n")
            transcript_rows.append(
                {
                    "clip_id": row["clip_id"],
                    "split": row["split"],
                    "category": row["category"],
                    "duration_seconds": row["duration_seconds"],
                    "transcription_seconds": f"{elapsed:.3f}",
                    "text": text,
                }
            )
            print(f"[{index:03d}/{len(rows):03d}] {row['clip_id']}: {text}")

    write_tsv(out_dir / "transcripts.tsv", transcript_rows)
    metadata = {
        "system": (
            "transformers-whisper-base"
            if args.base_model_only
            else "transformers-whisper-lora"
        ),
        "base_model": args.base_model,
        "adapter_dir": None if args.base_model_only else str(args.adapter_dir),
        "device": args.device,
        "language": args.language,
        "task": args.task,
        "num_beams": args.num_beams,
        "manifest": str(args.manifest),
        "data_root": str(args.data_root),
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
