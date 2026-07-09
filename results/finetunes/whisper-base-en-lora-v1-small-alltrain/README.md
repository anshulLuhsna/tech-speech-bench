# Whisper Base English LoRA V1 Small All-Train

Second TechSpeechBench LoRA run.

This adapter uses the same base model and hyperparameters as the first LoRA run, but trains on all 40 v1-small train clips instead of holding 8 train clips out as an internal dev set.

Heldout splits remain untouched.

## Training Setup

- Method: PEFT LoRA
- Base model: `openai/whisper-base.en`
- Train source: `data/v1-small/train/metadata.jsonl`
- Train clips: all 40 clips from the `train` split
- External evaluation: all 120 clips from `data/v1-small/prepared/manifest.tsv`
- LoRA target modules: `q_proj`, `v_proj`
- Trainable params: 589,824
- Total params: 73,183,232
- Trainable percent: 0.8060
- Epochs: 20
- Runtime on local Apple MPS: about 206 seconds

## Overall Result

Compared with the faster-whisper `base.en` baseline and the first LoRA run:

| metric | baseline | LoRA dev | LoRA all-train |
| --- | ---: | ---: | ---: |
| WER | 0.1991 | 0.1539 | 0.1399 |
| CER | 0.0421 | 0.0464 | 0.0354 |
| domain term exact match | 64 / 241 | 99 / 241 | 100 / 241 |
| domain term exact rate | 0.2656 | 0.4108 | 0.4149 |
| command exact match | 4 / 6 | 6 / 6 | 6 / 6 |

## Split Result

| split | baseline WER | LoRA dev WER | LoRA all-train WER | baseline terms | LoRA dev terms | LoRA all-train terms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| train | 0.1330 | 0.0922 | 0.0727 | 34 / 84 | 50 / 84 | 52 / 84 |
| heldout_real | 0.1440 | 0.1440 | 0.1401 | 22 / 77 | 27 / 77 | 27 / 77 |
| heldout_fake | 0.3347 | 0.2361 | 0.2177 | 8 / 80 | 22 / 80 | 21 / 80 |

## Interpretation

All-train is the best run by overall WER and CER.

It also fixed the worst decode failure from the first LoRA run: `tsb_v1_097` no longer produces corrupted replacement characters.

The tradeoff: domain-term exact match barely changed. It improved from 99 to 100 total hits, and heldout-real term exact stayed at 27 / 77.

So this is a better checkpoint, but it does not change the main conclusion:

```text
current bottleneck is data variety, not model size.
```

## Example Failures

- `tsb_v1_075`: `LoRA` and `FlashAttention` are dropped into a shorter paraphrase.
- `tsb_v1_095`: `EmbedForge` becomes `embedded force`; `CacheWeaver` becomes `cache we were`.
- `tsb_v1_101`: `FastServeX` still becomes `faster wrecks`.
- `tsb_v1_119`: `EmbedForge` becomes `embed force`; `QueryForge` becomes `query force`.

## Files

- Adapter: `adapter_model.safetensors`
- Adapter config: `adapter_config.json`
- Training config: `train_config.json`
- Eval run: `eval/run.json`
- Eval metrics: `eval/metrics.json`

Transcript tables and per-clip error tables are generated locally and ignored by git.
