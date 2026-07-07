#!/usr/bin/env python3
"""Score baseline transcripts against TechSpeechBench references."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score TechSpeechBench transcripts.")
    parser.add_argument("--references", default="data/v0/references.tsv")
    parser.add_argument("--transcripts", required=True)
    parser.add_argument("--manifest", default="data/v0/manifest.tsv")
    parser.add_argument("--terms", default="data/v0/domain_terms.txt")
    parser.add_argument("--out-dir", required=True)
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


def normalize_for_error_rate(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"`", "", text)
    text = re.sub(r"[^a-z0-9.#+-]+", " ", text)
    return text.split()


def normalize_chars(text: str) -> str:
    return " ".join(normalize_for_error_rate(text))


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


def contains_case_sensitive(text: str, term: str) -> bool:
    return term in text


def command_hits(reference: str, hypothesis: str) -> tuple[int, int]:
    commands = ["pytest -k", "requirements.txt", ".env", "Dockerfile"]
    total = sum(1 for command in commands if command in reference)
    hits = sum(1 for command in commands if command in reference and command in hypothesis)
    return hits, total


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    refs = {row["clip_id"]: row["reference_text"] for row in read_tsv(Path(args.references))}
    hyps = {row["clip_id"]: row["text"] for row in read_tsv(Path(args.transcripts))}
    manifest = {row["clip_id"]: row for row in read_tsv(Path(args.manifest))}
    terms = read_terms(Path(args.terms))

    total_word_edits = 0
    total_words = 0
    total_char_edits = 0
    total_chars = 0
    total_term_mentions = 0
    total_term_hits = 0
    total_command_mentions = 0
    total_command_hits = 0
    per_clip_rows: list[dict[str, object]] = []
    missed_terms = Counter()

    for clip_id, reference in refs.items():
        hypothesis = hyps.get(clip_id, "")
        ref_words = normalize_for_error_rate(reference)
        hyp_words = normalize_for_error_rate(hypothesis)
        word_edits = edit_distance(ref_words, hyp_words)
        char_ref = normalize_chars(reference)
        char_hyp = normalize_chars(hypothesis)
        char_edits = edit_distance(char_ref, char_hyp)

        clip_terms = [term for term in terms if contains_case_sensitive(reference, term)]
        term_hits = [term for term in clip_terms if contains_case_sensitive(hypothesis, term)]
        term_misses = sorted(set(clip_terms) - set(term_hits))
        missed_terms.update(term_misses)

        command_hit_count, command_total = command_hits(reference, hypothesis)

        total_word_edits += word_edits
        total_words += len(ref_words)
        total_char_edits += char_edits
        total_chars += len(char_ref)
        total_term_mentions += len(clip_terms)
        total_term_hits += len(term_hits)
        total_command_mentions += command_total
        total_command_hits += command_hit_count

        per_clip_rows.append(
            {
                "clip_id": clip_id,
                "split": manifest.get(clip_id, {}).get("split", ""),
                "category": manifest.get(clip_id, {}).get("category", ""),
                "wer": f"{word_edits / max(1, len(ref_words)):.4f}",
                "cer": f"{char_edits / max(1, len(char_ref)):.4f}",
                "domain_terms_total": len(clip_terms),
                "domain_terms_exact": len(term_hits),
                "domain_terms_missed": ";".join(term_misses),
                "reference": reference,
                "hypothesis": hypothesis,
            }
        )

    metrics = {
        "clips": len(refs),
        "wer": total_word_edits / max(1, total_words),
        "cer": total_char_edits / max(1, total_chars),
        "domain_term_exact_match_rate": total_term_hits / max(1, total_term_mentions),
        "domain_term_error_rate": 1 - (total_term_hits / max(1, total_term_mentions)),
        "domain_term_mentions": total_term_mentions,
        "domain_term_exact_hits": total_term_hits,
        "command_exact_match_rate": total_command_hits / max(1, total_command_mentions),
        "command_mentions": total_command_mentions,
        "command_exact_hits": total_command_hits,
        "top_missed_terms": missed_terms.most_common(20),
    }

    (out_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    with (out_dir / "per_clip_errors.tsv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(per_clip_rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(per_clip_rows)

    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

