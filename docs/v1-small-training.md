# V1 Small Training Notes

Current state:

- Train audio exists for `tsb_v1_001` through `tsb_v1_040`.
- Remaining audio exists for `tsb_v1_041` through `tsb_v1_120`.
- Audio folder: `data/v1-small/tsb_v1-small-train/`
- Remaining audio folder: `data/v1-small/tsb_v1-small-full/`
- Transcript source: `data/v1-small/manifest.tsv`
- The files have been renamed from the Voice Memos export names to stable IDs.

Do not jump straight to training before checking the mapping. If one audio file is shifted by one ID, the model trains on wrong labels and every result becomes suspect.

## Inspect The Train Mapping

Read the script first:

```bash
sed -n '1,220p' scripts/prepare_v1_small_train.py
```

Preview the audio/transcript mapping:

```bash
uv run python scripts/prepare_v1_small_train.py
```

This is read-only. It prints every train row, the expected audio path, terms, and transcript.

## Run The Metadata Gate

Read the script first:

```bash
sed -n '1,240p' scripts/check_v1_small_audio.py
```

Check all 120 audio files:

```bash
uv run python scripts/check_v1_small_audio.py
```

This is read-only. It checks that expected audio files exist and verifies codec, sample rate, channels, and duration.

After it looks right:

```bash
uv run python scripts/check_v1_small_audio.py --write
```

This writes:

```text
data/v1-small/audio-metadata.tsv
```

## Write Train Metadata

After the preview looks right:

```bash
uv run python scripts/prepare_v1_small_train.py --write
```

This creates:

```text
data/v1-small/train/references.tsv
data/v1-small/train/metadata.jsonl
```

These are derived metadata files for later fine-tuning experiments.

## Prepare ASR And Scoring Files

The v0 ASR script expects a manifest with `clip_id`, `audio_path`, and `duration_seconds`.
The source v1 manifest has different columns, so prepare v1-compatible files first.

Read the script:

```bash
sed -n '1,240p' scripts/prepare_v1_small_eval.py
```

Preview:

```bash
uv run python scripts/prepare_v1_small_eval.py
```

Write:

```bash
uv run python scripts/prepare_v1_small_eval.py --write
```

This creates:

```text
data/v1-small/prepared/manifest.tsv
data/v1-small/prepared/references.tsv
data/v1-small/prepared/domain_terms.txt
```

Use those files for the v1-small ASR baseline and scoring.

## Can We Train Now?

Almost, but first do the mapping check above.

Minimum next steps:

1. Preview the train mapping.
2. Run the metadata gate.
3. Write v1-small ASR/scoring files.
4. Listen to 3-5 random clips and confirm they match the shown transcript.
5. Run baseline ASR on all 120.
6. Score baseline by train, heldout real, and heldout fake.
7. Decide the first fine-tuning target.

The first fine-tuning target should probably be Whisper LoRA or another lightweight ASR adaptation path. Do not train on `heldout_real` or `heldout_fake`. Those splits exist to check whether adaptation generalizes beyond memorized terms.

## Important Caveat

Forty short clips is enough for a smoke test, not a serious claim.

The first training run should answer a narrow question:

```text
can the training pipeline overfit or improve on the small train split without breaking the evaluation setup?
```

It should not be framed as proof that the model has learned technical speech in general.
