#!/usr/bin/env python3
"""Flag structural failures in Kokoro ASR-sanity transcripts."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCES = (
    REPO_ROOT
    / "data/synthetic/kokoro-v1/private/training/asr-sanity-inputs/references.tsv"
)
DEFAULT_TRANSCRIPTS = (
    REPO_ROOT
    / "data/synthetic/kokoro-v1/private/training/asr-sanity/transcripts.tsv"
)
DEFAULT_REPORT = (
    REPO_ROOT
    / "data/synthetic/kokoro-v1/private/training/asr-sanity-summary.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--references", type=Path, default=DEFAULT_REFERENCES)
    parser.add_argument("--transcripts", type=Path, default=DEFAULT_TRANSCRIPTS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def repeated_run(tokens: list[str]) -> int:
    longest = 0
    current = 0
    previous = None
    for token in tokens:
        current = current + 1 if token == previous else 1
        longest = max(longest, current)
        previous = token
    return longest


def main() -> None:
    args = parse_args()
    references = {
        row["clip_id"]: row["reference_text"] for row in read_tsv(args.references)
    }
    hypotheses = {row["clip_id"]: row["text"] for row in read_tsv(args.transcripts)}
    if len(references) != 248 or set(references) != set(hypotheses):
        raise ValueError("ASR sanity references and hypotheses must cover 248 clips")

    flagged = []
    for clip_id, reference in references.items():
        hypothesis = hypotheses[clip_id].strip()
        ref_tokens = words(reference)
        hyp_tokens = words(hypothesis)
        ratio = len(hyp_tokens) / max(1, len(ref_tokens))
        reasons = []
        if not hypothesis:
            reasons.append("empty")
        if ratio < 0.5:
            reasons.append("possible_truncation")
        if ratio > 1.75:
            reasons.append("possible_hallucination")
        if repeated_run(hyp_tokens) >= 4:
            reasons.append("repeated_token_run")
        if reasons:
            flagged.append(
                {
                    "clip_id": clip_id,
                    "reasons": reasons,
                    "word_count_ratio": round(ratio, 3),
                    "reference": reference,
                    "hypothesis": hypothesis,
                }
            )

    report = {
        "clips": len(references),
        "nonempty": sum(bool(text.strip()) for text in hypotheses.values()),
        "structurally_flagged": len(flagged),
        "flagged": flagged,
        "interpretation": (
            "This gate detects gross audio failures only. Technical-term errors by "
            "base Whisper are expected and do not reject synthetic training audio."
        ),
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if flagged:
        raise ValueError(f"ASR sanity flagged {len(flagged)} clips")


if __name__ == "__main__":
    main()
