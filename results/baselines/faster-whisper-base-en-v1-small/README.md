# faster-whisper `base.en` Baseline On V1 Small

## Run

```bash
uv run python scripts/prepare_v1_small_eval.py --write

uv run python scripts/transcribe_faster_whisper.py \
  --manifest data/v1-small/prepared/manifest.tsv \
  --data-root . \
  --out-dir results/baselines/faster-whisper-base-en-v1-small \
  --model base.en

uv run python scripts/score_transcripts.py \
  --references data/v1-small/prepared/references.tsv \
  --manifest data/v1-small/prepared/manifest.tsv \
  --terms data/v1-small/prepared/domain_terms.txt \
  --transcripts results/baselines/faster-whisper-base-en-v1-small/transcripts.tsv \
  --out-dir results/baselines/faster-whisper-base-en-v1-small
```

## Setup

- System: `faster-whisper`
- Model: `base.en`
- Device: CPU
- Compute type: `int8`
- Clips: 120
- Dataset: `data/v1-small`
- Splits: 40 train, 40 held-out real, 40 held-out fake

## Overall Metrics

```text
WER: 19.91%
CER: 4.21%
Domain term exact match rate: 26.56%
Domain term error rate: 73.44%
Command exact match rate: 66.67%
Domain term mentions: 241
Domain term exact hits: 64
```

## Split Metrics

```text
train:
  clips: 40
  avg WER: 13.51%
  avg CER: 3.46%
  term exact: 34 / 84 = 40.48%

heldout_real:
  clips: 40
  avg WER: 14.60%
  avg CER: 3.45%
  term exact: 22 / 77 = 28.57%

heldout_fake:
  clips: 40
  avg WER: 34.11%
  avg CER: 5.86%
  term exact: 8 / 80 = 10.00%
```

## Representative Failures

### `tsb_v1_074`

Reference:

```text
Redis Stack serves the lookup path, and ClickHouse stores the aggregated retrieval events.
```

Hypothesis:

```text
Ready stack serves the lookup path and click how stores the aggregated retrieval events.
```

Missed terms: `ClickHouse`, `Redis`, `Redis Stack`

### `tsb_v1_101`

Reference:

```text
ModelStack should preload the small checkpoint before FastServeX accepts traffic.
```

Hypothesis:

```text
Model stack should preload the small checkpoint before faster wrecks except stuff it.
```

Missed terms: `FastServeX`, `ModelStack`

### `tsb_v1_119`

Reference:

```text
Set EmbedForge to read-only during the QueryForge regression test.
```

Hypothesis:

```text
Set embed force to read only during the query force regression test.
```

Missed terms: `EmbedForge`, `QueryForge`

## Takeaway

The v1-small baseline is doing what the benchmark was designed to expose.

Generic WER looks usable on train and held-out real, but exact technical term preservation is weak. The held-out fake split is much harder, which suggests the benchmark is testing code-like word structure rather than only memorized known tool names.

The next experiment can be a small fine-tuning smoke test on `train` only, followed by evaluation on all three splits.
