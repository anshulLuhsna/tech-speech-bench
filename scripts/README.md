# Scripts

Planned scripts:

- `transcribe_faster_whisper.py`: run a local faster-whisper baseline
- `score_transcripts.py`: compute WER, CER, domain term error rate, and exact-match metrics
- `prepare_v1_small_train.py`: inspect v1-small train audio/transcript mapping and optionally write derived train metadata
- `check_v1_small_audio.py`: metadata gate for v1-small audio before ASR or fine-tuning
- `prepare_v1_small_eval.py`: write v1-small manifest/references/terms for ASR and scoring
- `train_whisper_lora.py`: train a PEFT LoRA adapter on the v1-small train split
- `transcribe_whisper_lora.py`: transcribe the benchmark with a trained Whisper LoRA adapter
- `compare_transcript_runs.py`: compare ASR transcript runs by split
- `build_term_list.py`: extract domain terms from references

First baseline:

```bash
uv run python scripts/transcribe_faster_whisper.py --model base.en
```

Score the baseline:

```bash
uv run python scripts/score_transcripts.py \
  --transcripts results/baselines/faster-whisper-base-en/transcripts.tsv \
  --out-dir results/baselines/faster-whisper-base-en
```

Inspect v1-small train recordings:

```bash
uv run python scripts/prepare_v1_small_train.py
```

Check v1-small audio metadata:

```bash
uv run python scripts/check_v1_small_audio.py
```

Prepare v1-small ASR/scoring files:

```bash
uv run python scripts/prepare_v1_small_eval.py
uv run python scripts/prepare_v1_small_eval.py --write
```

Write v1-small train metadata after inspection:

```bash
uv run python scripts/prepare_v1_small_train.py --write
```

Inspect the Whisper LoRA training plan:

```bash
uv run --group train python scripts/train_whisper_lora.py --dry-run
```

Transcribe with a trained LoRA adapter:

```bash
uv run --group train python scripts/transcribe_whisper_lora.py
```

Compare v1-small transcript runs:

```bash
uv run python scripts/compare_transcript_runs.py \
  --run baseline=results/baselines/faster-whisper-base-en-v1-small/transcripts.tsv \
  --run lora=results/finetunes/whisper-base-en-lora-v1-small/eval/transcripts.tsv \
  --out-dir results/comparisons/v1-small-baseline-vs-lora
```
