# Evaluation Plan

## Baseline Systems

Initial baselines:

1. current dictation tool, if output can be captured
2. local Whisper or faster-whisper
3. commercial STT API, if available

Later systems:

- contextual vocabulary / word boosting
- LLM post-correction using a technical term list
- fine-tuned STT adapter

## Metrics

### WER

Word error rate. Useful as a general signal, but can hide important technical failures.

### CER

Character error rate. Useful for package names and acronyms.

### Domain Term Error Rate

```text
missed_or_wrong_domain_terms / total_domain_terms
```

This is the primary metric for TechSpeechBench.

### Acronym Exact Match

Measures whether terms like `RAGAS`, `QLoRA`, `vLLM`, and `HNSW` are preserved exactly.

### Command Phrase Exact Match

Measures whether command-like speech such as `pytest -k` or `requirements.txt` is preserved correctly.

### Correction Burden

```text
manual_edits_after_model / transcript_words
```

This approximates how much work the user must do after dictation.

## First Report

The first useful report should include:

- table of metrics by system
- top recurring failure terms
- examples where WER looks acceptable but the technical term is wrong
- held-out split results separated from dev results

Run the local scorer:

```bash
uv run python scripts/score_transcripts.py \
  --transcripts results/baselines/faster-whisper-base-en/transcripts.tsv \
  --out-dir results/baselines/faster-whisper-base-en
```
