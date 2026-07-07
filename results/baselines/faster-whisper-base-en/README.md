# faster-whisper `base.en` Baseline

## Run

```bash
uv run python scripts/transcribe_faster_whisper.py --model base.en
uv run python scripts/score_transcripts.py \
  --transcripts results/baselines/faster-whisper-base-en/transcripts.tsv \
  --out-dir results/baselines/faster-whisper-base-en
```

## Setup

- System: `faster-whisper`
- Model: `base.en`
- Device: CPU
- Compute type: `int8`
- Clips: 100
- Dataset: `data/v0`

## Metrics

```text
WER: 16.78%
CER: 4.49%
Domain term exact match rate: 42.42%
Domain term error rate: 57.58%
Command exact match rate: 0.00%
Domain term mentions: 132
Domain term exact hits: 56
```

## Top Missed Terms

```text
pgvector: 13
RAGAS: 10
LangGraph: 8
vLLM: 6
pytest: 4
OpenTelemetry: 4
LoRA: 3
Dockerfile: 3
FastAPI: 3
WebSocket: 3
Pydantic: 3
```

## Representative Failures

### `tsb_v0_001`

Reference:

```text
Run the RAGAS faithfulness eval on the LangGraph branch and compare it with the pgvector baseline.
```

Hypothesis:

```text
Run the raga's faithfulness evale on the Langrav branch and compare it with the PG Vector Baseline.
```

Missed terms: `RAGAS`, `LangGraph`, `pgvector`

### `tsb_v0_012`

Reference:

```text
Fine-tune a LoRA adapter and compare it with the QLoRA checkpoint.
```

Hypothesis:

```text
Fine-tune a lower adapter and compare it with the Q lower checkpoint.
```

Missed terms: `LoRA`, `QLoRA`

### `tsb_v0_031`

Reference:

```text
Store the embeddings in pgvector with an HNSW index.
```

Hypothesis:

```text
Store the embeddings in PC vector with an HNSW index.
```

Missed term: `pgvector`

### `tsb_v0_041`

Reference:

```text
Run pytest dash k test memory retriever and show the failing assertion.
```

Hypothesis:

```text
run pi test dash k test memory retrieval and show the failing assertion
```

Missed term: `pytest`

## Takeaway

The baseline validates the benchmark thesis: general WER is usable, but the exact technical terms that carry meaning are frequently wrong. The next experiment should not be fine-tuning yet. It should test a vocabulary-aware correction layer against this same baseline.

