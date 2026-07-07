# Scripts

Planned scripts:

- `transcribe_faster_whisper.py`: run a local faster-whisper baseline
- `score_transcripts.py`: compute WER, CER, domain term error rate, and exact-match metrics
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
