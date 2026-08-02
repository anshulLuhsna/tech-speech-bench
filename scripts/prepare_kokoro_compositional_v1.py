#!/usr/bin/env python3
"""Create disjoint CamelCase prompts for compositional ASR training."""

from __future__ import annotations

import argparse
import csv
import random
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK_TERMS = REPO_ROOT / "data/v2/domain_terms.tsv"
DEFAULT_OUT = REPO_ROOT / "data/synthetic/kokoro-compositional-v1/prompts.tsv"
SEED = 29
TERM_COUNT = 96

PREFIXES = (
    "Agent", "Audio", "Batch", "Build", "Cache", "Cloud", "Code", "Config",
    "Context", "Data", "Deploy", "Drift", "Eval", "Feature", "Graph", "Index",
    "Kernel", "Lattice", "Log", "Memory", "Metric", "Model", "Prompt", "Query",
    "Queue", "Relay", "Route", "Schema", "Shard", "Signal", "Stream", "Tensor",
    "Token", "Tool", "Trace", "Vector", "Voice",
)

SUFFIXES = (
    "Anchor", "Beacon", "Bridge", "Core", "Cove", "Crate", "Crest", "Dock",
    "Flow", "Forge", "Grid", "Guard", "Harbor", "Hawk", "Hub", "Kite",
    "Latch", "Lens", "Loom", "Mason", "Mesh", "Mint", "Nest", "Nook",
    "Path", "Pillar", "Pilot", "River", "Runner", "Sage", "Sparrow", "Spire",
    "Stack", "Stone", "Store", "Trail", "Vault", "Watch", "Warden", "Weaver",
)

TEMPLATES = (
    "{term} rebuilt the index after the schema changed.",
    "The worker sent the failed batch back to {term}.",
    "{term} flagged the regression during the canary rollout.",
    "We moved the retry policy into {term} yesterday.",
    "The dashboard reads its latency estimate from {term}.",
    "{term} rejected the payload before it reached production.",
    "The deployment called {term} after the health check failed.",
    "{term} stored the trace alongside the model response.",
    "The queue drained normally once {term} recovered.",
    "{term} compared the new output with the saved baseline.",
    "The service loads {term} before opening the event stream.",
    "{term} raised an alert when the cache became stale.",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-terms", type=Path, default=DEFAULT_BENCHMARK_TERMS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--count", type=int, default=TERM_COUNT)
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def read_benchmark_terms(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["term"] for row in csv.DictReader(handle, delimiter="\t")}


def split_camel_case(term: str) -> str:
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", term)


def build_rows(benchmark_terms: set[str], count: int, seed: int) -> list[dict[str, str]]:
    candidates = [
        prefix + suffix
        for prefix in PREFIXES
        for suffix in SUFFIXES
        if prefix + suffix not in benchmark_terms
    ]
    random.Random(seed).shuffle(candidates)
    if count > len(candidates):
        raise ValueError(f"requested {count} terms from {len(candidates)} candidates")

    rows = []
    for index, term in enumerate(candidates[:count], start=1):
        sentence = TEMPLATES[(index - 1) % len(TEMPLATES)].format(term=term)
        rows.append(
            {
                "utterance_id": f"kcv1_{index:03d}",
                "source_clip_id": "synthetic_kokoro_compositional_v1",
                "target_terms": term,
                "transcript": sentence,
                "synthesis_text": sentence.replace(term, split_camel_case(term)),
            }
        )
    return rows


def main() -> None:
    args = parse_args()
    benchmark_terms = read_benchmark_terms(args.benchmark_terms)
    rows = build_rows(benchmark_terms, args.count, args.seed)
    generated_terms = {row["target_terms"] for row in rows}
    overlap = generated_terms & benchmark_terms
    if overlap:
        raise ValueError(f"generated terms overlap benchmark: {sorted(overlap)}")

    print(f"prepared {len(rows)} prompts")
    print(f"benchmark overlap: {len(overlap)}")
    print("sample terms: " + ", ".join(sorted(generated_terms)[:12]))
    if not args.write:
        print("dry run only; pass --write to create the prompt sheet")
        return

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
