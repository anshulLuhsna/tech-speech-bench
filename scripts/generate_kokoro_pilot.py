#!/usr/bin/env python3
"""Generate Kokoro speech from frozen prompts and pinned local weights."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


MODEL_ID = "hexgrad/Kokoro-82M"
MODEL_REVISION = "f3ff3571791e39611d31c381e3a41a3af07b4987"
DEFAULT_SNAPSHOT = (
    Path.home()
    / ".cache"
    / "huggingface"
    / "hub"
    / "models--hexgrad--Kokoro-82M"
    / "snapshots"
    / MODEL_REVISION
)
DEFAULT_PROMPTS = Path("data/synthetic/kokoro-pilot/prompts.tsv")
DEFAULT_TERMS = Path("data/v2/domain_terms.tsv")
DEFAULT_PRIVATE_DIR = Path("data/synthetic/kokoro-pilot/private")
SAMPLE_RATE = 24_000


@dataclass(frozen=True)
class Voice:
    voice_id: str
    language_code: str
    description: str


VOICES = (
    Voice("af_heart", "a", "American English, feminine"),
    Voice("am_michael", "a", "American English, masculine"),
    Voice("bf_emma", "b", "British English, feminine"),
    Voice("bm_george", "b", "British English, masculine"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompts", type=Path, default=DEFAULT_PROMPTS)
    parser.add_argument("--terms", type=Path, default=DEFAULT_TERMS)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--private-dir", type=Path, default=DEFAULT_PRIVATE_DIR)
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "mps"),
        default="auto",
        help="Inference device. Auto prefers MPS on Apple Silicon.",
    )
    parser.add_argument(
        "--utterance-id",
        action="append",
        default=[],
        help="Generate only this utterance id. Can be passed multiple times.",
    )
    parser.add_argument(
        "--voice-id",
        action="append",
        default=[],
        help="Generate only this voice id. Can be passed multiple times.",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Generate audio. Without this flag, only validate and print the plan.",
    )
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty TSV: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(
    prompts: list[dict[str, str]], term_rows: list[dict[str, str]]
) -> None:
    required = {
        "utterance_id",
        "source_clip_id",
        "target_terms",
        "transcript",
        "synthesis_text",
    }
    if not prompts:
        raise ValueError("prompt sheet is empty")
    missing = required - set(prompts[0])
    if missing:
        raise ValueError(f"prompt columns missing: {sorted(missing)}")

    term_splits = {row["term"]: row["split"] for row in term_rows}
    seen_ids: set[str] = set()
    for row in prompts:
        utterance_id = row["utterance_id"]
        if utterance_id in seen_ids:
            raise ValueError(f"duplicate utterance_id: {utterance_id}")
        seen_ids.add(utterance_id)

        targets = [term.strip() for term in row["target_terms"].split(";")]
        if not all(targets):
            raise ValueError(f"{utterance_id}: empty target term")
        for term in targets:
            if term not in row["transcript"]:
                raise ValueError(
                    f"{utterance_id}: target absent from transcript: {term}"
                )
            split = term_splits.get(term)
            if split != "train":
                raise ValueError(
                    f"{utterance_id}: synthetic pilot may only use train terms; "
                    f"{term!r} has split {split!r}"
                )


def choose_device(requested: str, torch: object) -> str:
    if requested == "auto":
        return "mps" if torch.backends.mps.is_available() else "cpu"
    if requested == "mps" and not torch.backends.mps.is_available():
        raise RuntimeError("MPS requested but unavailable")
    return requested


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def package_version(name: str) -> str:
    return importlib.metadata.version(name)


def main() -> None:
    args = parse_args()
    prompts = read_tsv(args.prompts)
    term_rows = read_tsv(args.terms)
    validate_inputs(prompts, term_rows)

    prompt_ids = {prompt["utterance_id"] for prompt in prompts}
    requested_ids = set(args.utterance_id)
    unknown_ids = requested_ids - prompt_ids
    if unknown_ids:
        raise ValueError(f"unknown utterance ids: {sorted(unknown_ids)}")
    selected_prompts = [
        prompt
        for prompt in prompts
        if not requested_ids or prompt["utterance_id"] in requested_ids
    ]

    voice_ids = {voice.voice_id for voice in VOICES}
    requested_voices = set(args.voice_id)
    unknown_voices = requested_voices - voice_ids
    if unknown_voices:
        raise ValueError(f"unknown voice ids: {sorted(unknown_voices)}")
    selected_voices = [
        voice
        for voice in VOICES
        if not requested_voices or voice.voice_id in requested_voices
    ]

    expected = len(selected_prompts) * len(selected_voices)
    print(f"validated {len(prompts)} prompts x {len(VOICES)} voices")
    print(f"planned clips: {expected}")
    if not args.write:
        print("dry run only; pass --write to generate audio")
        return

    required_files = (
        args.snapshot / "config.json",
        args.snapshot / "kokoro-v1_0.pth",
        *(
            args.snapshot / "voices" / f"{voice.voice_id}.pt"
            for voice in selected_voices
        ),
    )
    missing_files = [str(path) for path in required_files if not path.exists()]
    if missing_files:
        raise FileNotFoundError(
            "pinned Kokoro snapshot is incomplete:\n" + "\n".join(missing_files)
        )

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

    import numpy as np
    import soundfile as sf
    import torch
    from kokoro import KModel, KPipeline

    torch.manual_seed(0)
    np.random.seed(0)
    device = choose_device(args.device, torch)
    print(f"loading {MODEL_ID}@{MODEL_REVISION} on {device}")

    model = KModel(
        repo_id=MODEL_ID,
        config=str(args.snapshot / "config.json"),
        model=str(args.snapshot / "kokoro-v1_0.pth"),
        disable_complex=device == "mps",
    ).to(device).eval()
    pipelines = {
        language_code: KPipeline(
            lang_code=language_code,
            repo_id=MODEL_ID,
            model=model,
        )
        for language_code in sorted(
            {voice.language_code for voice in selected_voices}
        )
    }

    audio_dir = args.private_dir / "audio" / "wav"
    manifest_path = args.private_dir / "manifest.tsv"
    run_path = args.private_dir / "generation-run.json"
    audio_dir.mkdir(parents=True, exist_ok=True)
    if not args.overwrite:
        selected_ids = {
            f"kokoro_{prompt['utterance_id']}_{voice.voice_id}"
            for prompt in selected_prompts
            for voice in selected_voices
        }
        existing = sorted(
            path for path in audio_dir.glob("*.wav") if path.stem in selected_ids
        )
        if existing:
            raise FileExistsError(
                f"{len(existing)} WAV files already exist; pass --overwrite "
                "to regenerate them"
            )

    selected_clip_ids = {
        f"kokoro_{prompt['utterance_id']}_{voice.voice_id}"
        for prompt in selected_prompts
        for voice in selected_voices
    }
    manifest: list[dict[str, object]] = []
    if manifest_path.exists() and len(selected_clip_ids) < len(prompts) * len(VOICES):
        manifest = [
            row
            for row in read_tsv(manifest_path)
            if row["clip_id"] not in selected_clip_ids
        ]

    for prompt in selected_prompts:
        for voice in selected_voices:
            clip_id = f"kokoro_{prompt['utterance_id']}_{voice.voice_id}"
            output_path = audio_dir / f"{clip_id}.wav"
            pipeline = pipelines[voice.language_code]
            voice_path = args.snapshot / "voices" / f"{voice.voice_id}.pt"
            results = list(
                pipeline(
                    prompt["synthesis_text"],
                    voice=str(voice_path),
                    speed=1.0,
                )
            )
            if not results or any(result.audio is None for result in results):
                raise RuntimeError(f"Kokoro returned no audio for {clip_id}")

            chunks = [
                result.audio.detach().cpu().numpy().astype(np.float32)
                for result in results
            ]
            audio = np.concatenate(chunks)
            sf.write(output_path, audio, SAMPLE_RATE, subtype="PCM_16")
            info = sf.info(output_path)
            if info.channels != 1 or info.samplerate != SAMPLE_RATE:
                raise ValueError(f"unexpected audio metadata for {output_path}")

            manifest.append(
                {
                    "clip_id": clip_id,
                    "utterance_id": prompt["utterance_id"],
                    "source_clip_id": prompt["source_clip_id"],
                    "target_terms": prompt["target_terms"],
                    "transcript": prompt["transcript"],
                    "synthesis_text": prompt["synthesis_text"],
                    "voice_id": voice.voice_id,
                    "voice_description": voice.description,
                    "language_code": voice.language_code,
                    "speed": "1.0",
                    "sample_rate": info.samplerate,
                    "channels": info.channels,
                    "frames": info.frames,
                    "duration_seconds": f"{info.duration:.3f}",
                    "sha256": sha256(output_path),
                    "relative_audio_path": output_path.as_posix(),
                    "graphemes": " ".join(result.graphemes for result in results),
                    "phonemes": " ".join(result.phonemes for result in results),
                }
            )
            print(f"generated {clip_id} ({info.duration:.2f}s)")

    utterance_order = {
        prompt["utterance_id"]: index for index, prompt in enumerate(prompts)
    }
    voice_order = {voice.voice_id: index for index, voice in enumerate(VOICES)}
    manifest.sort(
        key=lambda row: (
            utterance_order[str(row["utterance_id"])],
            voice_order[str(row["voice_id"])],
        )
    )
    write_tsv(manifest_path, manifest)
    run = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "snapshot": str(args.snapshot),
        "device": device,
        "sample_rate": SAMPLE_RATE,
        "clip_count": len(manifest),
        "prompt_count": len(prompts),
        "generated_utterance_ids": sorted(
            prompt["utterance_id"] for prompt in selected_prompts
        ),
        "generated_voice_ids": sorted(
            voice.voice_id for voice in selected_voices
        ),
        "voices": [voice.__dict__ for voice in VOICES],
        "packages": {
            "en-core-web-sm": package_version("en-core-web-sm"),
            "kokoro": package_version("kokoro"),
            "misaki": package_version("misaki"),
            "soundfile": package_version("soundfile"),
            "spacy": package_version("spacy"),
            "torch": package_version("torch"),
        },
    }
    run_path.write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {manifest_path}")
    print(f"wrote {run_path}")


if __name__ == "__main__":
    main()
