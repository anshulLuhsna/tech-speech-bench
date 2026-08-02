# V2 Multi-Speaker Baseline

## Dataset

- 6 anonymous speakers, 40 clips each, 240 clips total
- source capture: 200 WhatsApp Opus/OGG clips and 40 AAC/MP4 clips
- model input: derived 16 kHz mono PCM WAV; source audio remains untouched and private
- term split: 96 train, 72 heldout real, 72 heldout fake
- speaker partition frozen before LoRA training:
  - `s01-s04`: train speakers
  - `s05`: dev speaker
  - `s06`: untouched test speaker
- exact transcript leakage across term splits: none
- target-term leakage across term splits: none
- ASR-assisted label alignment flags: 0

This benchmark tests two different things:

1. unseen technical terms on speakers represented in training
2. generalization to an entirely unseen speaker

Do not collapse those into one claim.

## Operational Baseline Configuration

- system: `faster-whisper`
- model: `base.en`
- device: CPU
- compute type: `int8`
- beam size: 5
- language: English
- VAD filter: disabled

This run captures the original local baseline. It is not the control used to
attribute changes to LoRA because it uses a different inference backend and
quantization mode from the Transformers training stack.

## Baseline Results

| split | clips | WER | CER | exact term hits | term exact rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| overall | 240 | 0.3704 | 0.1022 | 90 / 496 | 0.1815 |
| train | 96 | 0.3121 | 0.0801 | 76 / 224 | 0.3393 |
| heldout real | 72 | 0.3148 | 0.0973 | 13 / 137 | 0.0949 |
| heldout fake | 72 | 0.5180 | 0.1372 | 1 / 135 | 0.0074 |

The ordinary WER difference between train and heldout-real is small, while
exact technical-term accuracy drops from 33.9% to 9.5%. That is the central
baseline signal: surrounding language can look acceptable while the technical
entity is wrong.

`heldout_fake` is a stress test for unseen pronounceable names. It is not a
claim about normal production traffic.

## Speaker Variation

| speaker | WER | CER | exact term hits | term exact rate |
| --- | ---: | ---: | ---: | ---: |
| s01 | 0.3392 | 0.0848 | 15 / 83 | 0.1807 |
| s02 | 0.3292 | 0.0843 | 15 / 82 | 0.1829 |
| s03 | 0.4731 | 0.1509 | 9 / 81 | 0.1111 |
| s04 | 0.3750 | 0.1030 | 14 / 83 | 0.1687 |
| s05 | 0.3299 | 0.0810 | 17 / 82 | 0.2073 |
| s06 | 0.3771 | 0.1094 | 20 / 85 | 0.2353 |

Speaker variance is large enough that an all-speaker training split would hide
an important failure mode. This is why `s06` is now frozen as the final unseen
speaker.

## Leakage-Safe LoRA Path

Prepare metadata:

```bash
uv run python scripts/prepare_v2_lora_data.py
uv run python scripts/prepare_v2_lora_data.py --write
```

Inspect the exact training plan:

```bash
uv run --group train python scripts/train_whisper_lora.py \
  --train-metadata data/v2/lora/train.jsonl \
  --dev-metadata data/v2/lora/dev.jsonl \
  --output-dir results/finetunes/whisper-base-en-lora-v2-multispeaker \
  --dry-run
```

Training must use only the 64 train-vocabulary clips from `s01-s04`.
Development uses 16 train-vocabulary clips from unseen speaker `s05`.
No `heldout_real`, `heldout_fake`, or `s06` audio may affect checkpoint choice.

After training, evaluate separately:

- seen speakers plus unseen real terms
- seen speakers plus fake-term stress set
- unseen speaker `s06` with train vocabulary
- unseen speaker `s06` with unseen real terms
- unseen speaker `s06` with fake-term stress terms

The LoRA succeeds only if it improves the appropriate heldout slices without a
large regression on general words or the unseen speaker.

## First LoRA Result

The first leakage-safe LoRA run used:

- base model: `openai/whisper-base.en`
- train: 64 train-vocabulary clips from `s01-s04`
- dev: 16 train-vocabulary clips from unseen speaker `s05`
- final test speaker: all 40 `s06` clips untouched during training and selection
- LoRA rank 16, alpha 32, dropout 0.05
- 20 epochs, learning rate `1e-4`, effective batch size 8
- checkpoint selected by unseen-speaker dev loss
- final dev loss: 1.074

The comparison below uses `openai/whisper-base.en` through the same Transformers
inference script, MPS device, beam count, language prompt, 16 kHz loader, and
manifest for both runs. The only intended model difference is loading the LoRA
adapter.

| split | controlled base WER | LoRA WER | base term rate | LoRA term rate |
| --- | ---: | ---: | ---: | ---: |
| overall | 0.5507* | 0.2472 | 0.1915 | 0.3931 |
| train vocabulary | 0.3091 | 0.1152 | 0.3616 | 0.7366 |
| heldout real | 0.3148 | 0.2524 | 0.0949 | 0.1898 |
| heldout fake | 1.1692* | 0.4371 | 0.0074 | 0.0296 |

`*` The base model emitted a long punctuation loop on `s03_040`, producing a
55.5 clip-level WER and heavily inflating aggregate base WER. The heldout-real
WER and exact-term comparisons are not affected by that clip. Preserve the
failure as model behavior, but do not present the overall WER delta as a stable
estimate from this small dataset.

The adapter did more than memorize the 64 training recordings. Exact term
accuracy doubled on real terms that never appeared in training, from 9.5% to
19.0%. That is a real generalization result, but the absolute accuracy remains
low.

### Unseen Speaker S06

| term split | clips | base WER | LoRA WER | base term rate | LoRA term rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| train vocabulary | 16 | 0.3041 | 0.1637 | 0.4286 | 0.5952 |
| heldout real | 12 | 0.2910 | 0.2388 | 0.1429 | 0.2381 |
| heldout fake | 12 | 0.5877 | 0.4649 | 0.0000 | 0.0455 |

The unseen-speaker heldout-real result is 5 exact term hits out of 21 mentions,
up from 3 out of 21. The slice is too small for a broad production claim, but
it shows that the improvement is not confined to voices used in training.

Fake-name performance remains poor. LoRA raised the overall exact rate from
0.7% to 3.0%, which is not enough to claim open-vocabulary name handling.

Reproduce the full comparison:

```bash
uv run --group train python scripts/transcribe_whisper_lora.py \
  --manifest data/v2/manifest.tsv \
  --data-root data/v2 \
  --base-model-only \
  --out-dir results/baselines/whisper-base-en-transformers-v2-multispeaker \
  --device mps

uv run python scripts/compare_transcript_runs.py \
  --references data/v2/references.tsv \
  --manifest data/v2/manifest.tsv \
  --terms data/v2/domain_terms.txt \
  --run base=results/baselines/whisper-base-en-transformers-v2-multispeaker/transcripts.tsv \
  --run lora=results/finetunes/whisper-base-en-lora-v2-multispeaker/eval/transcripts.tsv \
  --out-dir results/comparisons/v2-multispeaker-controlled-base-vs-lora

uv run python scripts/compare_v2_slices.py \
  --run base=results/baselines/whisper-base-en-transformers-v2-multispeaker/transcripts.tsv \
  --run lora=results/finetunes/whisper-base-en-lora-v2-multispeaker/eval/transcripts.tsv \
  --out-dir results/comparisons/v2-multispeaker-controlled-slices
```
