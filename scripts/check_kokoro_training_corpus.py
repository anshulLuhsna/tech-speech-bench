#!/usr/bin/env python3
"""Validate a private Kokoro training corpus against its frozen prompts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROMPTS = REPO_ROOT / "data/synthetic/kokoro-v1/training-prompts.tsv"
DEFAULT_MANIFEST = (
    REPO_ROOT / "data/synthetic/kokoro-v1/private/training/manifest.tsv"
)
DEFAULT_REPORT = (
    REPO_ROOT / "data/synthetic/kokoro-v1/private/training/qa-summary.json"
)
EXPECTED_VOICES = ("af_heart", "am_michael", "bf_emma", "bm_george")
EXPECTED_SAMPLE_RATE = 24_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompts", type=Path, default=DEFAULT_PROMPTS)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--write-report", action="store_true")
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    args = parse_args()

    import numpy as np
    import soundfile as sf

    prompt_rows = read_tsv(args.prompts)
    manifest_rows = read_tsv(args.manifest)
    if not prompt_rows:
        raise ValueError("prompt sheet is empty")
    expected_manifest_rows = len(prompt_rows) * len(EXPECTED_VOICES)
    if len(manifest_rows) != expected_manifest_rows:
        raise ValueError(
            f"expected {expected_manifest_rows} manifest rows, "
            f"found {len(manifest_rows)}"
        )

    prompt_by_id = {row["utterance_id"]: row for row in prompt_rows}
    expected_clip_ids = {
        f"kokoro_{utterance_id}_{voice_id}"
        for utterance_id in prompt_by_id
        for voice_id in EXPECTED_VOICES
    }
    actual_clip_ids = {row["clip_id"] for row in manifest_rows}
    if len(actual_clip_ids) != len(manifest_rows):
        raise ValueError("manifest contains duplicate clip ids")
    if actual_clip_ids != expected_clip_ids:
        missing = sorted(expected_clip_ids - actual_clip_ids)
        extra = sorted(actual_clip_ids - expected_clip_ids)
        raise ValueError(f"clip coverage mismatch; missing={missing}, extra={extra}")

    errors: list[str] = []
    warnings: list[str] = []
    voice_counts: Counter[str] = Counter()
    voice_durations: defaultdict[str, float] = defaultdict(float)
    total_duration = 0.0
    for row in manifest_rows:
        clip_id = row["clip_id"]
        prompt = prompt_by_id.get(row["utterance_id"])
        if prompt is None:
            errors.append(f"{clip_id}: unknown utterance id")
            continue
        for field in ("target_terms", "transcript", "synthesis_text"):
            if row[field] != prompt[field]:
                errors.append(f"{clip_id}: {field} differs from frozen prompt")

        voice_id = row["voice_id"]
        if voice_id not in EXPECTED_VOICES:
            errors.append(f"{clip_id}: unexpected voice {voice_id!r}")
        voice_counts[voice_id] += 1

        audio_path = REPO_ROOT / row["relative_audio_path"]
        if not audio_path.exists():
            errors.append(f"{clip_id}: missing WAV {audio_path}")
            continue
        if sha256(audio_path) != row["sha256"]:
            errors.append(f"{clip_id}: checksum mismatch")

        info = sf.info(audio_path)
        audio, sample_rate = sf.read(audio_path, dtype="float32")
        peak = float(np.max(np.abs(audio)))
        clipped = int(np.count_nonzero(np.abs(audio) >= 0.999969))
        if sample_rate != EXPECTED_SAMPLE_RATE:
            errors.append(f"{clip_id}: sample rate is {sample_rate}")
        if info.channels != 1 or info.subtype != "PCM_16":
            errors.append(
                f"{clip_id}: expected mono PCM16, got {info.channels}ch {info.subtype}"
            )
        if info.frames <= 0 or not 1.5 <= info.duration <= 12.0:
            errors.append(f"{clip_id}: suspicious duration {info.duration:.3f}s")
        if not np.isfinite(audio).all():
            errors.append(f"{clip_id}: non-finite samples")
        if clipped:
            errors.append(f"{clip_id}: {clipped} clipped samples")
        if peak <= 0.001:
            errors.append(f"{clip_id}: near-silent audio peak={peak:.6f}")

        words_per_second = len(row["synthesis_text"].split()) / info.duration
        if words_per_second > 4.0:
            warnings.append(
                f"{clip_id}: fast delivery estimate {words_per_second:.2f} words/s"
            )
        if words_per_second < 1.0:
            warnings.append(
                f"{clip_id}: slow delivery estimate {words_per_second:.2f} words/s"
            )
        total_duration += info.duration
        voice_durations[voice_id] += info.duration

    expected_voice_counts = Counter(
        {voice: len(prompt_rows) for voice in EXPECTED_VOICES}
    )
    if voice_counts != expected_voice_counts:
        errors.append(f"voice coverage mismatch: {dict(voice_counts)}")
    if errors:
        raise ValueError("training corpus failed:\n" + "\n".join(errors))

    summary = {
        "clips": len(manifest_rows),
        "prompts": len(prompt_rows),
        "voices": dict(voice_counts),
        "sample_rate": EXPECTED_SAMPLE_RATE,
        "channels": 1,
        "subtype": "PCM_16",
        "duration_seconds": round(total_duration, 3),
        "duration_by_voice_seconds": {
            voice: round(voice_durations[voice], 3) for voice in EXPECTED_VOICES
        },
        "warnings": warnings,
    }
    print(json.dumps(summary, indent=2))
    if args.write_report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.report}")


if __name__ == "__main__":
    main()
