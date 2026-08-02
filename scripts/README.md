# Scripts

Planned scripts:

- `transcribe_faster_whisper.py`: run a local faster-whisper baseline
- `score_transcripts.py`: compute WER, CER, domain term error rate, and exact-match metrics
- `prepare_v1_small_train.py`: inspect v1-small train audio/transcript mapping and optionally write derived train metadata
- `check_v1_small_audio.py`: metadata gate for v1-small audio before ASR or fine-tuning
- `prepare_v1_small_eval.py`: write v1-small manifest/references/terms for ASR and scoring
- `train_whisper_lora.py`: train a PEFT LoRA adapter on the v1-small train split
- `transcribe_whisper_lora.py`: transcribe with the same Transformers Whisper path, either base-only or with a trained LoRA adapter
- `compare_transcript_runs.py`: compare ASR transcript runs by split
- `build_v2_friend_recording_scripts.py`: build participant-facing v2 recording PDFs from TSV scripts
- `prepare_v2_friend_data.py`: validate friend recordings and write anonymous v2 audio/metadata
- `check_v2_audio.py`: enforce the 240-clip v2 metadata and split gate
- `prepare_v2_lora_data.py`: freeze leakage-safe v2 LoRA train/dev metadata
- `compare_v2_slices.py`: compare runs by speaker partition and term split
- `bootstrap_paired_runs.py`: estimate paired clip-level uncertainty for WER and exact-term-rate differences between two frozen runs
- `generate_cartesia_tts.py`: validate and generate leakage-safe synthetic training audio with Cartesia
- `prepare_kokoro_v1.py`: validate the 31-term Kokoro pronunciation review and freeze gate prompts after approval
- `prepare_kokoro_training_prompts.py`: validate two new sentences per approved train term and freeze the 62 synthesis prompts
- `generate_kokoro_pilot.py`: generate a pinned, train-vocabulary-only Kokoro pronunciation pilot
- `check_kokoro_pronunciation_gate.py`: verify the 31 private gate masters, checksums, format, duration, and clipping
- `build_kokoro_pronunciation_review.py`: build six ordered review montages and their 31-row listening index
- `check_kokoro_training_corpus.py`: verify all 248 training WAVs, frozen prompt mappings, voice coverage, checksums, format, duration, pace, and clipping
- `prepare_kokoro_asr_sanity.py`: derive private ASR manifest and references for gross synthetic-audio failure detection
- `check_kokoro_asr_sanity.py`: reject empty, truncated, hallucinated, or repetitive ASR sanity outputs without judging term accuracy
- `prepare_kokoro_lora_data.py`: build synthetic-only and exactly 50/50 human-plus-synthetic LoRA metadata with a shared 160-update budget
- `generate_parler_pilot.py`: preserve the reproducible Parler-TTS pilot that failed pronunciation review; do not scale
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

Run the matching base model without an adapter for a controlled comparison:

```bash
uv run --group train python scripts/transcribe_whisper_lora.py \
  --base-model-only \
  --out-dir results/baselines/whisper-base-en-transformers
```

Compare v1-small transcript runs:

```bash
uv run python scripts/compare_transcript_runs.py \
  --run baseline=results/baselines/faster-whisper-base-en-v1-small/transcripts.tsv \
  --run lora=results/finetunes/whisper-base-en-lora-v1-small/eval/transcripts.tsv \
  --out-dir results/comparisons/v1-small-baseline-vs-lora
```

Prepare and validate the private multi-speaker v2 collection:

```bash
uv run python scripts/prepare_v2_friend_data.py
uv run python scripts/prepare_v2_friend_data.py --write
uv run python scripts/check_v2_audio.py
uv run python scripts/prepare_v2_lora_data.py
uv run python scripts/prepare_v2_lora_data.py --write
```

Raw friend audio and identity mappings stay local and ignored by Git. The
canonical manifest exposes only `s01` through `s06` and derived audio paths.

Validate the Kokoro pronunciation pilot without writing audio:

```bash
~/.venvs/techspeechbench-tts/bin/python \
  scripts/generate_kokoro_pilot.py
```

Generate the 16 private pilot clips:

```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 \
~/.venvs/techspeechbench-tts/bin/python \
  scripts/generate_kokoro_pilot.py --write
```

Validate the Kokoro v1 pronunciation review:

```bash
uv run python scripts/prepare_kokoro_v1.py
```

After all 31 rows are approved, freeze the pronunciation-gate prompt sheet:

```bash
uv run python scripts/prepare_kokoro_v1.py --write
```

Generate the 31-clip, single-voice gate only after that approval:

```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 \
~/.venvs/techspeechbench-tts/bin/python \
  scripts/generate_kokoro_pilot.py \
  --prompts data/synthetic/kokoro-v1/pronunciation-gate-prompts.tsv \
  --private-dir data/synthetic/kokoro-v1/private/pronunciation-gate \
  --voice-id af_heart \
  --write
```

Validate every generated gate master:

```bash
~/.venvs/techspeechbench-tts/bin/python \
  scripts/check_kokoro_pronunciation_gate.py
```

Build the six ordered pronunciation-review montages:

```bash
uv run python scripts/build_kokoro_pronunciation_review.py
```

Build a targeted replacement montage after pronunciation corrections:

```bash
uv run python scripts/build_kokoro_pronunciation_review.py \
  --gate-id kpg008 \
  --gate-id kpg010 \
  --gate-id kpg011 \
  --gate-id kpg024
```

Freeze the 62 leakage-safe Kokoro training prompts after the pronunciation
gate closes:

```bash
uv run python scripts/prepare_kokoro_training_prompts.py
uv run python scripts/prepare_kokoro_training_prompts.py --write
```

Generate and validate all 248 clips after the listening gate passes:

```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 \
~/.venvs/techspeechbench-tts/bin/python \
  scripts/generate_kokoro_pilot.py \
  --prompts data/synthetic/kokoro-v1/training-prompts.tsv \
  --private-dir data/synthetic/kokoro-v1/private/training \
  --write

~/.venvs/techspeechbench-tts/bin/python \
  scripts/check_kokoro_training_corpus.py --write-report

uv run python scripts/prepare_kokoro_lora_data.py
uv run python scripts/prepare_kokoro_lora_data.py --write
```

Train both matched 160-update adapters:

```bash
uv run --group train python scripts/train_whisper_lora.py \
  --train-metadata data/synthetic/kokoro-v1/lora/synthetic-only.jsonl \
  --dev-metadata data/synthetic/kokoro-v1/lora/human-dev.jsonl \
  --output-dir results/finetunes/whisper-base-en-lora-kokoro-v1-synthetic-only \
  --max-steps 160

uv run --group train python scripts/train_whisper_lora.py \
  --train-metadata data/synthetic/kokoro-v1/lora/balanced.jsonl \
  --dev-metadata data/synthetic/kokoro-v1/lora/human-dev.jsonl \
  --output-dir results/finetunes/whisper-base-en-lora-kokoro-v1-balanced \
  --max-steps 160
```

Transcribe the frozen real-human benchmark with each adapter, using
`--data-root data/v2`, then compare the resulting transcript TSVs with
`compare_transcript_runs.py`, `compare_v2_slices.py`, and
`bootstrap_paired_runs.py`. The exact commands and results are recorded in
`docs/kokoro-synthetic-training-v1.md` and
`results/comparisons/kokoro-v1-controlled/`.

Validate the Parler-TTS pronunciation pilot without writing audio:

```bash
~/.venvs/techspeechbench-parler/bin/python \
  scripts/generate_parler_pilot.py
```

Reproduce the rejected 16-clip Parler-TTS pilot only when investigating its
failure. These outputs are not approved training data:

```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 \
~/.venvs/techspeechbench-parler/bin/python \
  scripts/generate_parler_pilot.py --write
```
