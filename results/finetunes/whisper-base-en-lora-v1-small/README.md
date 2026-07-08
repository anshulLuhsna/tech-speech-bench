# Whisper Base English LoRA V1 Small

This is the first TechSpeechBench LoRA fine-tune.

It is a small adapter, not a full model. The base model is `openai/whisper-base.en`.

## Training Setup

- Method: PEFT LoRA
- Base model: `openai/whisper-base.en`
- Train source: `data/v1-small/train/metadata.jsonl`
- Train clips: 40 total, with 32 used for training and 8 held out internally as a dev set
- External evaluation: all 120 clips from `data/v1-small/prepared/manifest.tsv`
- LoRA target modules: `q_proj`, `v_proj`
- Trainable params: 589,824
- Total params: 73,183,232
- Trainable percent: 0.8060
- Epochs: 20
- Runtime on local Apple MPS: about 187 seconds

The internal dev split is only a training health check. The benchmark claim comes from the external v1-small split metrics below.

## Overall Result

Compared with the faster-whisper `base.en` baseline:

| metric | baseline | LoRA |
| --- | ---: | ---: |
| WER | 0.1991 | 0.1539 |
| CER | 0.0421 | 0.0464 |
| domain term exact match | 64 / 241 | 99 / 241 |
| domain term exact rate | 0.2656 | 0.4108 |
| command exact match | 4 / 6 | 6 / 6 |

Overall WER and domain-term exact match improved. CER got slightly worse, partly because some wrong outputs are longer or contain odd generated text.

## Split Result

| split | baseline WER | LoRA WER | baseline term exact | LoRA term exact |
| --- | ---: | ---: | ---: | ---: |
| train | 0.1351 | 0.0932 | 34 / 84 | 50 / 84 |
| heldout_real | 0.1460 | 0.1461 | 22 / 77 | 27 / 77 |
| heldout_fake | 0.3411 | 0.2425 | 8 / 80 | 22 / 80 |

The adapter clearly improved the train split and substantially improved fake heldout term exact match. The real heldout split is more modest: term exact match improved, but WER was basically flat.

## Interpretation

This is a useful first signal, not a final claim.

What looks good:

- The adapter did not only memorize the train split.
- `heldout_fake` improved from 8/80 to 22/80 exact term hits.
- Overall domain-term exact match improved from 26.6% to 41.1%.
- Command-like text improved from 4/6 to 6/6 exact matches.

What is still weak:

- `heldout_real` WER did not improve.
- `heldout_real` term exact improved only from 22/77 to 27/77.
- The model still normalizes many technical names into common words.
- One fake clip produced corrupted-looking text, so decoding needs investigation.

## Example Failures

- `tsb_v1_041`: `vLLM` became `VLLM`.
- `tsb_v1_046`: `Qdrant` became `QDrunt`; `pgvector` became `PC vector`.
- `tsb_v1_074`: `Redis Stack` became `ReadyStack`; `ClickHouse` became `Clickhouse`.
- `tsb_v1_097`: output became corrupted-looking repeated replacement characters.
- `tsb_v1_101`: `FastServeX` became `faster wrecks`.

## Files

- Adapter: `adapter_model.safetensors`
- Adapter config: `adapter_config.json`
- Training config: `train_config.json`
- Eval run: `eval/run.json`
- Eval metrics: `eval/metrics.json`

Transcript tables and per-clip error tables are generated locally and ignored by git.

## Next Move

The next serious move is not a larger model yet. It is a cleaner second data pass:

- more speakers
- more microphone conditions
- more heldout real technical terms
- more fake-but-plausible product/library names
- fewer single-speaker artifacts

Then rerun the same LoRA pipeline and check whether `heldout_real` moves.
