#!/usr/bin/env python3
"""Prepare anonymous TechSpeechBench v2 audio and metadata.

Raw friend recordings remain untouched under data/friend-data. This script
sorts each speaker's clips by recording order, maps them to the frozen script,
and writes anonymous 16 kHz mono WAV derivatives plus benchmark metadata.

Default mode validates and previews only. Pass --write to create outputs.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = REPO_ROOT / "data/friend-data"
DEFAULT_SCRIPT_DIR = REPO_ROOT / "data/v2/recording-scripts"
DEFAULT_V2_DIR = REPO_ROOT / "data/v2"
SPEAKER_RE = re.compile(r"_(s\d{2})$")
WHATSAPP_RE = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2}) at "
    r"(?P<time>\d{1,2}\.\d{2}\.\d{2} [AP]M)"
)
VOICE_MEMO_RE = re.compile(r"New Recording (?P<number>\d+)")
EXPECTED_CLIPS_PER_SPEAKER = 40


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate or prepare anonymous TechSpeechBench v2 data."
    )
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--script-dir", type=Path, default=DEFAULT_SCRIPT_DIR)
    parser.add_argument("--v2-dir", type=Path, default=DEFAULT_V2_DIR)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write converted audio, manifests, references, and private source map.",
    )
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty TSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(rows[0]),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def clip_split(position: int) -> str:
    if 1 <= position <= 8 or 21 <= position <= 28:
        return "train"
    if 9 <= position <= 14 or 29 <= position <= 34:
        return "heldout_real"
    if 15 <= position <= 20 or 35 <= position <= 40:
        return "heldout_fake"
    raise ValueError(f"unsupported clip position: {position}")


def speaker_partition(speaker_id: str) -> str:
    if speaker_id in {"s01", "s02", "s03", "s04"}:
        return "train_speaker"
    if speaker_id == "s05":
        return "dev_speaker"
    if speaker_id == "s06":
        return "test_speaker"
    raise ValueError(f"unsupported speaker ID: {speaker_id}")


def recording_sort_key(path: Path) -> tuple[int, object]:
    whatsapp_match = WHATSAPP_RE.search(path.name)
    if whatsapp_match:
        timestamp = dt.datetime.strptime(
            f"{whatsapp_match.group('date')} {whatsapp_match.group('time')}",
            "%Y-%m-%d %I.%M.%S %p",
        )
        return 0, timestamp

    voice_memo_match = VOICE_MEMO_RE.search(path.name)
    if voice_memo_match:
        return 1, int(voice_memo_match.group("number"))

    return 2, (path.stat().st_mtime_ns, path.name)


def discover_speaker_audio(source_dir: Path) -> dict[str, list[Path]]:
    speakers: dict[str, list[Path]] = {}
    for folder in sorted(path for path in source_dir.iterdir() if path.is_dir()):
        match = SPEAKER_RE.search(folder.name)
        if not match:
            raise ValueError(f"speaker folder must end in _sNN: {folder}")
        speaker_id = match.group(1)
        if speaker_id in speakers:
            raise ValueError(f"duplicate folder for {speaker_id}")
        files = sorted(
            (path for path in folder.iterdir() if path.is_file() and not path.name.startswith(".")),
            key=recording_sort_key,
        )
        if len(files) != EXPECTED_CLIPS_PER_SPEAKER:
            raise ValueError(
                f"{speaker_id} must contain {EXPECTED_CLIPS_PER_SPEAKER} audio files, "
                f"found {len(files)}"
            )
        speakers[speaker_id] = files
    return speakers


def read_recording_scripts(script_dir: Path) -> dict[str, list[dict[str, str]]]:
    scripts = {}
    for path in sorted(script_dir.glob("s*.tsv")):
        speaker_id = path.stem
        rows = read_tsv(path)
        expected_ids = [
            f"{speaker_id}_{position:03d}"
            for position in range(1, EXPECTED_CLIPS_PER_SPEAKER + 1)
        ]
        if [row["clip_id"] for row in rows] != expected_ids:
            raise ValueError(f"{path} does not contain 40 sequential clip IDs")
        scripts[speaker_id] = rows
    return scripts


def validate_script_design(scripts: dict[str, list[dict[str, str]]], term_path: Path) -> None:
    shared_sets = {
        tuple(row["utterance"] for row in rows[:20])
        for rows in scripts.values()
    }
    if len(shared_sets) != 1:
        raise ValueError("shared positions 001-020 differ between speakers")

    unique_utterances = [
        row["utterance"]
        for rows in scripts.values()
        for row in rows[20:]
    ]
    duplicates = [
        utterance
        for utterance, count in Counter(unique_utterances).items()
        if count > 1
    ]
    if duplicates:
        raise ValueError(f"duplicate unique utterances: {duplicates}")

    term_rows = read_tsv(term_path)
    utterances_by_split: dict[str, list[str]] = defaultdict(list)
    for rows in scripts.values():
        for position, row in enumerate(rows, start=1):
            utterances_by_split[clip_split(position)].append(row["utterance"])

    problems = []
    for term_row in term_rows:
        term = term_row["term"]
        declared_split = term_row["split"]
        actual_splits = {
            split
            for split, utterances in utterances_by_split.items()
            if any(term in utterance for utterance in utterances)
        }
        if actual_splits != {declared_split}:
            problems.append(
                f"{term}: declared={declared_split}, found={sorted(actual_splits)}"
            )
    if problems:
        raise ValueError("term split validation failed:\n" + "\n".join(problems))


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
        "format=format_name,duration",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    payload = json.loads(completed.stdout)
    if len(payload.get("streams", [])) != 1:
        raise ValueError(f"expected one audio stream: {path}")
    stream = payload["streams"][0]
    return {
        "codec": stream["codec_name"],
        "sample_rate": int(stream["sample_rate"]),
        "channels": int(stream["channels"]),
        "format": payload["format"]["format_name"],
        "duration": float(payload["format"]["duration"]),
    }


def convert_audio(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-map",
        "0:a:0",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(destination),
    ]
    subprocess.run(command, check=True)


def source_condition(metadata: dict[str, object]) -> str:
    if metadata["codec"] == "opus":
        return "whatsapp_opus"
    if metadata["codec"] == "aac":
        return "voice_memo_aac_mp4"
    return f"source_{metadata['codec']}"


def main() -> None:
    args = parse_args()
    speakers = discover_speaker_audio(args.source_dir)
    scripts = read_recording_scripts(args.script_dir)
    if set(speakers) != set(scripts):
        raise ValueError(
            f"speaker/audio mismatch: audio={sorted(speakers)}, scripts={sorted(scripts)}"
        )

    term_path = args.v2_dir / "domain_terms.tsv"
    validate_script_design(scripts, term_path)

    manifest_rows: list[dict[str, object]] = []
    reference_rows: list[dict[str, object]] = []
    metadata_rows: list[dict[str, object]] = []
    private_map_rows: list[dict[str, object]] = []

    for speaker_id in sorted(speakers):
        print(f"{speaker_id}: mapping {len(speakers[speaker_id])} clips")
        for position, (source_path, script_row) in enumerate(
            zip(speakers[speaker_id], scripts[speaker_id], strict=True), start=1
        ):
            clip_id = script_row["clip_id"]
            relative_audio_path = Path("audio/converted") / speaker_id / f"{clip_id}.wav"
            destination = args.v2_dir / relative_audio_path
            source_metadata = probe_audio(source_path)

            if not 1.0 <= float(source_metadata["duration"]) <= 30.0:
                raise ValueError(
                    f"{clip_id} duration outside 1-30 seconds: {source_metadata['duration']}"
                )

            if args.write:
                convert_audio(source_path, destination)
                normalized_metadata = probe_audio(destination)
            else:
                normalized_metadata = {
                    "codec": "pcm_s16le",
                    "sample_rate": 16000,
                    "channels": 1,
                    "duration": source_metadata["duration"],
                }

            split = clip_split(position)
            manifest_rows.append(
                {
                    "clip_id": clip_id,
                    "speaker_id": speaker_id,
                    "speaker_partition": speaker_partition(speaker_id),
                    "split": split,
                    "condition": source_condition(source_metadata),
                    "category": "mixed_technical_dictation",
                    "audio_path": str(relative_audio_path),
                    "duration_seconds": f"{float(normalized_metadata['duration']):.6f}",
                    "size_bytes": destination.stat().st_size if args.write else "",
                    "transcript_status": "expected_reference_from_frozen_script",
                }
            )
            reference_rows.append(
                {
                    "clip_id": clip_id,
                    "reference_text": script_row["utterance"],
                }
            )
            metadata_rows.append(
                {
                    "clip_id": clip_id,
                    "speaker_id": speaker_id,
                    "source_codec": source_metadata["codec"],
                    "source_format": source_metadata["format"],
                    "source_sample_rate": source_metadata["sample_rate"],
                    "source_channels": source_metadata["channels"],
                    "source_duration_seconds": f"{float(source_metadata['duration']):.6f}",
                    "normalized_codec": normalized_metadata["codec"],
                    "normalized_sample_rate": normalized_metadata["sample_rate"],
                    "normalized_channels": normalized_metadata["channels"],
                    "normalized_duration_seconds": f"{float(normalized_metadata['duration']):.6f}",
                }
            )
            private_map_rows.append(
                {
                    "clip_id": clip_id,
                    "source_path": str(source_path.relative_to(REPO_ROOT)),
                }
            )

    split_counts = Counter(row["split"] for row in manifest_rows)
    print(f"clips: {len(manifest_rows)}")
    print(f"split counts: {dict(split_counts)}")
    print("source audio remains untouched")

    if not args.write:
        print("dry run only. pass --write to create prepared v2 data")
        return

    write_tsv(args.v2_dir / "manifest.tsv", manifest_rows)
    write_tsv(args.v2_dir / "references.tsv", reference_rows)
    write_tsv(args.v2_dir / "audio-metadata.tsv", metadata_rows)
    write_tsv(args.v2_dir / "private/source-map.tsv", private_map_rows)

    term_rows = read_tsv(term_path)
    (args.v2_dir / "domain_terms.txt").write_text(
        "\n".join(row["term"] for row in term_rows) + "\n",
        encoding="utf-8",
    )
    print(f"wrote prepared data under {args.v2_dir}")


if __name__ == "__main__":
    main()
