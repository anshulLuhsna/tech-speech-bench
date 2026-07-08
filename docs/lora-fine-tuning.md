# Whisper LoRA Fine-Tuning

This is the first actual adaptation path for TechSpeechBench.

The goal is narrow:

```text
Does a small Whisper LoRA adapter improve technical-term transcription on heldout clips?
```

Do not train on `heldout_real` or `heldout_fake`. Those splits are the point of the benchmark.

## What We Fine-Tune

- Base model: `openai/whisper-base.en`
- Adapter method: LoRA through PEFT
- Train source: `data/v1-small/train/metadata.jsonl`
- Train clips: `tsb_v1_001` through `tsb_v1_040`
- Evaluation source: `data/v1-small/prepared/manifest.tsv`
- Evaluation clips: all 120 v1-small clips

The current default script keeps 8 of the 40 train clips as an internal dev split. That dev split is only for watching training behavior. The real result is the external benchmark score on all 120 clips, split by `train`, `heldout_real`, and `heldout_fake`.

## Install Training Dependencies

```bash
uv sync --group train
```

## Inspect The Plan

Read the script first:

```bash
sed -n '1,280p' scripts/train_whisper_lora.py
```

Dry-run the split:

```bash
uv run --group train python scripts/train_whisper_lora.py --dry-run
```

## Train

CPU will be slow. A GPU machine is preferred.

```bash
uv run --group train python scripts/train_whisper_lora.py
```

Default output:

```text
results/finetunes/whisper-base-en-lora-v1-small/
```

## Transcribe With The Adapter

```bash
uv run --group train python scripts/transcribe_whisper_lora.py \
  --adapter-dir results/finetunes/whisper-base-en-lora-v1-small \
  --out-dir results/finetunes/whisper-base-en-lora-v1-small/eval
```

## Score

```bash
uv run python scripts/score_transcripts.py \
  --references data/v1-small/prepared/references.tsv \
  --manifest data/v1-small/prepared/manifest.tsv \
  --terms data/v1-small/prepared/domain_terms.txt \
  --transcripts results/finetunes/whisper-base-en-lora-v1-small/eval/transcripts.tsv \
  --out-dir results/finetunes/whisper-base-en-lora-v1-small/eval
```

Compare against:

```text
results/baselines/faster-whisper-base-en-v1-small/metrics.json
```

## How To Read The Result

Good signal:

- lower WER on `heldout_real`
- higher domain-term exact match on `heldout_real`
- no collapse on `heldout_fake`
- train split improves without becoming the only place that improves

Weak signal:

- train split improves a lot, heldout does not move
- fake terms get worse
- generic WER improves but domain-term exact match does not

That means the adapter mostly memorized the small train set.

## Why LoRA First

LoRA is the right first fine-tuning path because it is cheap, inspectable, and reversible. With only 40 short training clips, full fine-tuning can easily overfit while looking impressive on the train split.

If LoRA shows real heldout movement, the next move is more data from more speakers, not a larger model immediately.
