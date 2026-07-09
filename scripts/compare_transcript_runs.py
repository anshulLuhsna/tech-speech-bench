#!/usr/bin/env python3
"""Compare multiple transcript runs by TechSpeechBench split."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


DEFAULT_REFERENCES = Path("data/v1-small/prepared/references.tsv")
DEFAULT_MANIFEST = Path("data/v1-small/prepared/manifest.tsv")
DEFAULT_TERMS = Path("data/v1-small/prepared/domain_terms.txt")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare ASR runs by split.")
    parser.add_argument("--references", type=Path, default=DEFAULT_REFERENCES)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--terms", type=Path, default=DEFAULT_TERMS)
    parser.add_argument(
        "--run",
        action="append",
        required=True,
        metavar="LABEL=TRANSCRIPTS_TSV",
        help="Run label and transcripts TSV path. Can be passed multiple times.",
    )
    parser.add_argument("--out-dir", type=Path, required=True)
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def read_terms(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def parse_run_spec(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise ValueError(f"run must use LABEL=PATH form: {spec}")
    label, path = spec.split("=", 1)
    if not label:
        raise ValueError(f"run label is empty: {spec}")
    return label, Path(path)


def normalize_words(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"`", "", text)
    text = re.sub(r"[^a-z0-9.#+-]+", " ", text)
    return text.split()


def normalize_chars(text: str) -> str:
    return " ".join(normalize_words(text))


def edit_distance(a: list[str] | str, b: list[str] | str) -> int:
    previous = list(range(len(b) + 1))
    for i, item_a in enumerate(a, start=1):
        current = [i]
        for j, item_b in enumerate(b, start=1):
            cost = 0 if item_a == item_b else 1
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + cost,
                )
            )
        previous = current
    return previous[-1]


def command_hits(reference: str, hypothesis: str) -> tuple[int, int]:
    commands = ["pytest -k", "requirements.txt", ".env", "Dockerfile"]
    total = sum(1 for command in commands if command in reference)
    hits = sum(1 for command in commands if command in reference and command in hypothesis)
    return hits, total


def empty_bucket() -> dict[str, object]:
    return {
        "clips": 0,
        "word_edits": 0,
        "words": 0,
        "char_edits": 0,
        "chars": 0,
        "term_hits": 0,
        "term_total": 0,
        "command_hits": 0,
        "command_total": 0,
        "missed_terms": Counter(),
        "worst_clips": [],
    }


def finalize_bucket(bucket: dict[str, object]) -> dict[str, object]:
    word_edits = int(bucket["word_edits"])
    words = int(bucket["words"])
    char_edits = int(bucket["char_edits"])
    chars = int(bucket["chars"])
    term_hits = int(bucket["term_hits"])
    term_total = int(bucket["term_total"])
    command_hit_count = int(bucket["command_hits"])
    command_total = int(bucket["command_total"])
    missed_terms = bucket["missed_terms"]
    assert isinstance(missed_terms, Counter)
    worst_clips = bucket["worst_clips"]
    assert isinstance(worst_clips, list)
    return {
        "clips": bucket["clips"],
        "wer": word_edits / max(1, words),
        "cer": char_edits / max(1, chars),
        "domain_term_exact_hits": term_hits,
        "domain_term_mentions": term_total,
        "domain_term_exact_match_rate": term_hits / max(1, term_total),
        "command_exact_hits": command_hit_count,
        "command_mentions": command_total,
        "command_exact_match_rate": command_hit_count / max(1, command_total),
        "top_missed_terms": missed_terms.most_common(10),
        "worst_clips": sorted(worst_clips, key=lambda row: row["wer"], reverse=True)[:5],
    }


def score_run(
    transcripts_path: Path,
    refs: dict[str, str],
    manifest: dict[str, dict[str, str]],
    terms: list[str],
) -> dict[str, object]:
    hyps = {row["clip_id"]: row["text"] for row in read_tsv(transcripts_path)}
    buckets = {"overall": empty_bucket()}
    for clip_id, reference in refs.items():
        split = manifest[clip_id]["split"]
        buckets.setdefault(split, empty_bucket())
        hypothesis = hyps.get(clip_id, "")

        ref_words = normalize_words(reference)
        hyp_words = normalize_words(hypothesis)
        word_edits = edit_distance(ref_words, hyp_words)
        char_ref = normalize_chars(reference)
        char_hyp = normalize_chars(hypothesis)
        char_edits = edit_distance(char_ref, char_hyp)

        clip_terms = [term for term in terms if term in reference]
        term_hits = [term for term in clip_terms if term in hypothesis]
        term_misses = sorted(set(clip_terms) - set(term_hits))
        command_hit_count, command_total = command_hits(reference, hypothesis)

        for bucket in (buckets["overall"], buckets[split]):
            bucket["clips"] = int(bucket["clips"]) + 1
            bucket["word_edits"] = int(bucket["word_edits"]) + word_edits
            bucket["words"] = int(bucket["words"]) + len(ref_words)
            bucket["char_edits"] = int(bucket["char_edits"]) + char_edits
            bucket["chars"] = int(bucket["chars"]) + len(char_ref)
            bucket["term_hits"] = int(bucket["term_hits"]) + len(term_hits)
            bucket["term_total"] = int(bucket["term_total"]) + len(clip_terms)
            bucket["command_hits"] = int(bucket["command_hits"]) + command_hit_count
            bucket["command_total"] = int(bucket["command_total"]) + command_total
            missed_terms = bucket["missed_terms"]
            assert isinstance(missed_terms, Counter)
            missed_terms.update(term_misses)
            worst_clips = bucket["worst_clips"]
            assert isinstance(worst_clips, list)
            worst_clips.append(
                {
                    "clip_id": clip_id,
                    "split": split,
                    "wer": word_edits / max(1, len(ref_words)),
                    "missed_terms": term_misses,
                    "reference": reference,
                    "hypothesis": hypothesis,
                }
            )

    split_order = ["overall", "train", "heldout_real", "heldout_fake"]
    return {
        split: finalize_bucket(buckets[split])
        for split in split_order
        if split in buckets
    }


def format_rate(value: float) -> str:
    return f"{value:.4f}"


def format_text_for_markdown(text: str, max_chars: int = 180) -> str:
    text = text.replace("\ufffd", "[replacement-char]")
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def write_markdown(path: Path, comparison: dict[str, object]) -> None:
    labels = list(comparison.keys())
    splits = ["overall", "train", "heldout_real", "heldout_fake"]
    lines = ["# Transcript Run Comparison", ""]
    lines.append("| split | run | wer | cer | term exact | term rate | command exact |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: |")
    for split in splits:
        for label in labels:
            run = comparison[label]
            assert isinstance(run, dict)
            if split not in run:
                continue
            metrics = run[split]
            assert isinstance(metrics, dict)
            term_exact = (
                f"{metrics['domain_term_exact_hits']} / "
                f"{metrics['domain_term_mentions']}"
            )
            command_exact = (
                f"{metrics['command_exact_hits']} / {metrics['command_mentions']}"
            )
            lines.append(
                "| "
                + " | ".join(
                    [
                        split,
                        label,
                        format_rate(float(metrics["wer"])),
                        format_rate(float(metrics["cer"])),
                        term_exact,
                        format_rate(float(metrics["domain_term_exact_match_rate"])),
                        command_exact,
                    ]
                )
                + " |"
            )
    lines.append("")
    lines.append("## Worst Clips")
    lines.append("")
    for label in labels:
        run = comparison[label]
        assert isinstance(run, dict)
        lines.append(f"### {label}")
        lines.append("")
        overall = run["overall"]
        assert isinstance(overall, dict)
        for item in overall["worst_clips"]:
            lines.append(
                f"- `{item['clip_id']}` ({item['split']}), "
                f"wer={item['wer']:.4f}, missed={';'.join(item['missed_terms'])}"
            )
            lines.append(f"  - ref: {format_text_for_markdown(item['reference'])}")
            lines.append(f"  - hyp: {format_text_for_markdown(item['hypothesis'])}")
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    refs = {
        row["clip_id"]: row["reference_text"]
        for row in read_tsv(args.references)
    }
    manifest = {row["clip_id"]: row for row in read_tsv(args.manifest)}
    terms = read_terms(args.terms)

    comparison = {}
    for spec in args.run:
        label, path = parse_run_spec(spec)
        comparison[label] = score_run(path, refs, manifest, terms)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "comparison.json").write_text(
        json.dumps(comparison, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_markdown(args.out_dir / "README.md", comparison)
    print(json.dumps(comparison, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
