# Kokoro Additive V2

This is the frozen LoRA mixture used for the compositional augmentation
experiment.

| source | records | exposure rule |
| --- | ---: | --- |
| real human | 1,280 | each of 64 sources repeated exactly 20 times |
| Kokoro real-term v1 | 248 | every clip once |
| Kokoro compositional v1 | 384 | every clip once |
| total | 1,912 | one epoch, 239 updates at effective batch size 8 |

`lora/experiment-plan.json` records the exact counts and verifies that all 96
compositional full terms are disjoint from every benchmark term.

Rebuild the metadata after regenerating both private synthetic corpora:

```bash
uv run python scripts/prepare_kokoro_additive_v2.py --write
```
