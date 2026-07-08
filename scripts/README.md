# Scripts

Planned scripts:

- `transcribe_faster_whisper.py`: run a local faster-whisper baseline
- `score_transcripts.py`: compute WER, CER, domain term error rate, and exact-match metrics
- `prepare_v1_small_train.py`: inspect v1-small train audio/transcript mapping and optionally write derived train metadata
- `check_v1_small_audio.py`: metadata gate for v1-small audio before ASR or fine-tuning
- `prepare_v1_small_eval.py`: write v1-small manifest/references/terms for ASR and scoring
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
