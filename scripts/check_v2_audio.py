#!/usr/bin/env python3
"""Validate prepared TechSpeechBench v2 audio and benchmark mappings."""

from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
V2_DIR = REPO_ROOT / "data/v2"
EXPECTED_SPEAKERS = {f"s{index:02d}" for index in range(1, 7)}
EXPECTED_SPLITS = {"train": 96, "heldout_real": 72, "heldout_fake": 72}
EXPECTED_PARTITIONS = {"train_speaker": 160, "dev_speaker": 40, "test_speaker": 40}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def probe_audio(path: Path) -> dict[str, object]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=codec_name,sample_rate,channels",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    payload = json.loads(completed.stdout)
    stream = payload["streams"][0]
    return {
        "codec": stream["codec_name"],
        "sample_rate": int(stream["sample_rate"]),
        "channels": int(stream["channels"]),
        "duration": float(payload["format"]["duration"]),
    }


def fail_if(condition: bool, message: str, failures: list[str]) -> None:
    if condition:
        failures.append(message)


def main() -> None:
    manifest = read_tsv(V2_DIR / "manifest.tsv")
    references = read_tsv(V2_DIR / "references.tsv")
    terms = read_tsv(V2_DIR / "domain_terms.tsv")
    failures: list[str] = []

    manifest_ids = [row["clip_id"] for row in manifest]
    reference_ids = [row["clip_id"] for row in references]
    fail_if(len(manifest) != 240, f"manifest has {len(manifest)} rows, expected 240", failures)
    fail_if(len(set(manifest_ids)) != 240, "manifest clip IDs are not unique", failures)
    fail_if(set(manifest_ids) != set(reference_ids), "manifest/reference IDs differ", failures)

    speaker_counts = Counter(row["speaker_id"] for row in manifest)
    split_counts = Counter(row["split"] for row in manifest)
    partition_counts = Counter(row["speaker_partition"] for row in manifest)
    fail_if(set(speaker_counts) != EXPECTED_SPEAKERS, f"unexpected speakers: {speaker_counts}", failures)
    for speaker_id in EXPECTED_SPEAKERS:
        fail_if(speaker_counts[speaker_id] != 40, f"{speaker_id} has {speaker_counts[speaker_id]} clips", failures)
    fail_if(dict(split_counts) != EXPECTED_SPLITS, f"unexpected split counts: {split_counts}", failures)
    fail_if(
        dict(partition_counts) != EXPECTED_PARTITIONS,
        f"unexpected speaker partitions: {partition_counts}",
        failures,
    )

    reference_by_id = {row["clip_id"]: row["reference_text"] for row in references}
    text_splits: dict[str, set[str]] = defaultdict(set)
    for row in manifest:
        text_splits[reference_by_id[row["clip_id"]]].add(row["split"])
    leaked_text = {text: splits for text, splits in text_splits.items() if len(splits) > 1}
    fail_if(bool(leaked_text), f"exact transcript leakage across splits: {leaked_text}", failures)

    references_by_split: dict[str, list[str]] = defaultdict(list)
    for row in manifest:
        references_by_split[row["split"]].append(reference_by_id[row["clip_id"]])
    for term_row in terms:
        actual_splits = {
            split
            for split, texts in references_by_split.items()
            if any(term_row["term"] in text for text in texts)
        }
        fail_if(
            actual_splits != {term_row["split"]},
            f"term leakage or missing term: {term_row['term']} -> {sorted(actual_splits)}",
            failures,
        )

    codec_counts: Counter[str] = Counter()
    for index, row in enumerate(manifest, start=1):
        audio_path = V2_DIR / row["audio_path"]
        fail_if(not audio_path.exists(), f"missing audio: {row['clip_id']}", failures)
        if not audio_path.exists():
            continue
        fail_if("friend-data" in row["audio_path"], f"private path leaked: {row['clip_id']}", failures)
        metadata = probe_audio(audio_path)
        codec_counts[str(metadata["codec"])] += 1
        fail_if(metadata["codec"] != "pcm_s16le", f"{row['clip_id']} codec={metadata['codec']}", failures)
        fail_if(metadata["sample_rate"] != 16000, f"{row['clip_id']} sample_rate={metadata['sample_rate']}", failures)
        fail_if(metadata["channels"] != 1, f"{row['clip_id']} channels={metadata['channels']}", failures)
        fail_if(not 1.0 <= float(metadata["duration"]) <= 30.0, f"{row['clip_id']} duration={metadata['duration']}", failures)
        if index % 40 == 0:
            print(f"checked {index}/240 clips")

    if failures:
        print("v2 audio gate failed:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("v2 audio gate passed")
    print(f"speakers: {dict(sorted(speaker_counts.items()))}")
    print(f"splits: {dict(split_counts)}")
    print(f"speaker partitions: {dict(partition_counts)}")
    print(f"prepared codecs: {dict(codec_counts)}")
    print("all clips: 16 kHz, mono, PCM s16le, 1-30 seconds")
    print("private source paths: absent from canonical manifest")


if __name__ == "__main__":
    main()
