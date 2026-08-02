# TechSpeechBench

Technical speech benchmark for software engineering and AI engineering dictation.

## Thesis

Generic speech-to-text systems often understand ordinary English but fail on the words that matter in technical work: package names, acronyms, commands, eval names, repo terms, and code-like phrases.

TechSpeechBench is a focused benchmark and tooling project for measuring that failure mode and improving it.

## Current Scope

V0 focuses on one speaker and 100 short utterances covering:

- AI eval terms: `RAGAS`, `faithfulness`, `context precision`
- LLM infra: `vLLM`, `Triton`, `LoRA`, `QLoRA`
- agent systems: `LangGraph`, tool calls, memory stores, traces
- vector/data terms: `pgvector`, `Postgres`, `HNSW`, hybrid search
- software engineering terms: `pytest`, `Dockerfile`, `FastAPI`, `Pydantic`, GitHub Actions, Docker Compose, Kubernetes, Redis, Celery, WebSocket, Prometheus, OpenTelemetry

The current v2 benchmark expands this to 240 real-human clips from six
speakers with train, held-out real, and pronounceable held-out fake term sets.
The first open-source synthetic-data experiment trains Whisper LoRA adapters
on Kokoro speech and evaluates them only on this frozen human benchmark. Read
`docs/kokoro-synthetic-training-v1.md` for the protocol and result.

The follow-up compositional experiment trains on disjoint generated technical
names and improves real-human WER on both held-out real terms and held-out
coined names. Read `docs/kokoro-compositional-augmentation-v2.md` for the
result, uncertainty, and test-aware limitation.

## Repository Layout

```text
data/
  v0/
    audio/raw/          # original m4a clips
    manifest.tsv        # clip metadata
    references.tsv      # reference transcripts
docs/
  dataset-card.md
  recording-protocol.md
  evaluation-plan.md
results/
  baselines/            # STT baseline outputs and metrics
scripts/                # evaluation and transcription scripts
src/techspeechbench/    # package code when needed
```

## V0 Dataset

The initial dataset contains 100 `.m4a` clips recorded from iPhone Voice Memos.

Splits:

- `tsb_v0_001` to `tsb_v0_080`: dev
- `tsb_v0_081` to `tsb_v0_090`: dev stress
- `tsb_v0_091` to `tsb_v0_100`: held-out eval

Do not tune vocabulary rules, correction prompts, or model choices against the held-out clips until after the first baseline report.

## First Milestone

Create a baseline failure report comparing:

1. a generic dictation system, if output can be captured
2. a local Whisper/faster-whisper baseline
3. one commercial STT API, if credits are available

Metrics:

- WER
- CER
- domain term error rate
- acronym exact match
- command phrase exact match
- manual edits per 100 words
- latency

Run the first local baseline:

```bash
uv run python scripts/transcribe_faster_whisper.py --model base.en
```

First baseline report:

```text
results/baselines/faster-whisper-base-en/README.md
```

Generate candidate v1 utterances:

```text
docs/utterance-generation-prompt.md
```

## License

License is intentionally undecided until the dataset release policy is finalized. Do not publish audio publicly until consent and licensing are explicit.
