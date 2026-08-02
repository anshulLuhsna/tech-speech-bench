#!/usr/bin/env python3
"""Validate the private 31-clip Kokoro pronunciation gate."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW = (
    REPO_ROOT / "data/synthetic/kokoro-v1/pronunciation-review.tsv"
)
DEFAULT_MANIFEST = (
    REPO_ROOT
    / "data/synthetic/kokoro-v1/private/pronunciation-gate/manifest.tsv"
)
EXPECTED_VOICE = "af_heart"
EXPECTED_SAMPLE_RATE = 24_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
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

    review_rows = read_tsv(args.review)
    manifest_rows = read_tsv(args.manifest)
    if len(review_rows) != 31:
        raise ValueError(f"expected 31 review rows, found {len(review_rows)}")
    if len(manifest_rows) != 31:
        raise ValueError(f"expected 31 manifest rows, found {len(manifest_rows)}")

    review_by_id = {row["gate_id"]: row for row in review_rows}
    manifest_by_id = {row["utterance_id"]: row for row in manifest_rows}
    if len(review_by_id) != 31 or len(manifest_by_id) != 31:
        raise ValueError("duplicate gate or manifest ids")
    if set(review_by_id) != set(manifest_by_id):
        raise ValueError("review and manifest gate ids do not match")

    total_duration = 0.0
    errors: list[str] = []
    for gate_id, review in review_by_id.items():
        row = manifest_by_id[gate_id]
        clip_id = row["clip_id"]
        audio_path = REPO_ROOT / row["relative_audio_path"]

        if review["review_status"] != "approved":
            errors.append(f"{gate_id}: text review is not approved")
        if row["target_terms"] != review["term"]:
            errors.append(f"{gate_id}: target term mismatch")
        if row["transcript"] != review["canonical_sentence"]:
            errors.append(f"{gate_id}: canonical transcript mismatch")
        if row["synthesis_text"] != review["tts_sentence"]:
            errors.append(f"{gate_id}: TTS sentence mismatch")
        if row["voice_id"] != EXPECTED_VOICE:
            errors.append(f"{gate_id}: unexpected voice {row['voice_id']!r}")
        if not audio_path.exists():
            errors.append(f"{gate_id}: missing WAV {audio_path}")
            continue
        if sha256(audio_path) != row["sha256"]:
            errors.append(f"{gate_id}: checksum mismatch")

        info = sf.info(audio_path)
        audio, sample_rate = sf.read(audio_path, dtype="float32")
        peak = float(np.max(np.abs(audio)))
        clipped_samples = int(np.count_nonzero(np.abs(audio) >= 0.999969))
        if sample_rate != EXPECTED_SAMPLE_RATE:
            errors.append(f"{gate_id}: unexpected sample rate {sample_rate}")
        if info.channels != 1 or info.subtype != "PCM_16":
            errors.append(
                f"{gate_id}: expected mono PCM16, got "
                f"{info.channels}ch {info.subtype}"
            )
        if info.frames <= 0 or not 1.5 <= info.duration <= 10.0:
            errors.append(f"{gate_id}: suspicious duration {info.duration:.3f}s")
        if not np.isfinite(audio).all():
            errors.append(f"{gate_id}: non-finite samples")
        if clipped_samples:
            errors.append(f"{gate_id}: {clipped_samples} clipped samples")
        if peak <= 0.001:
            errors.append(f"{gate_id}: near-silent audio peak={peak:.6f}")

        total_duration += info.duration
        print(
            f"{clip_id}\t{info.duration:.3f}s\t"
            f"peak={peak:.6f}\t{review['term']}"
        )

    if errors:
        raise ValueError("audio gate failed:\n" + "\n".join(errors))
    print(
        f"validated 31 masters: {total_duration:.3f}s total, "
        "24 kHz mono PCM16, checksums intact, no clipping"
    )


if __name__ == "__main__":
    main()
