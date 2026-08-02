# Kokoro Compositional V1

This corpus teaches Whisper to emit unseen technical product-style names as
single CamelCase tokens. It does not contain any complete term from the
TechSpeechBench v2 benchmark.

## Public Definition

- `prompts.tsv`: 96 frozen sentences and canonical ASR labels
- generator seed: 29
- TTS model: `hexgrad/Kokoro-82M` at revision
  `f3ff3571791e39611d31c381e3a41a3af07b4987`
- voices: `af_heart`, `am_michael`, `bf_emma`, `bm_george`
- clips after generation: 384
- audio: mono 24 kHz PCM16 WAV

The canonical label contains a joined name such as `BatchForge`. Kokoro sees
the spoken form `Batch Forge`. The complete generated name is excluded when it
matches any real or fake benchmark term.

## Reproduce

```bash
uv run python scripts/prepare_kokoro_compositional_v1.py --write

PYTORCH_ENABLE_MPS_FALLBACK=1 \
~/.venvs/techspeechbench-tts/bin/python \
  scripts/generate_kokoro_pilot.py \
  --prompts data/synthetic/kokoro-compositional-v1/prompts.tsv \
  --allow-unlisted-terms \
  --private-dir data/synthetic/kokoro-compositional-v1/private \
  --write

~/.venvs/techspeechbench-tts/bin/python \
  scripts/check_kokoro_training_corpus.py \
  --prompts data/synthetic/kokoro-compositional-v1/prompts.tsv \
  --manifest data/synthetic/kokoro-compositional-v1/private/manifest.tsv \
  --report data/synthetic/kokoro-compositional-v1/private/qa-summary.json \
  --write-report
```

Generated audio and manifests remain private and ignored. The public prompt
sheet and pinned generator are sufficient to regenerate the corpus.
