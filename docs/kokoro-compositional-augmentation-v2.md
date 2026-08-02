# Kokoro Compositional Augmentation V2

## Question

Can synthetic speech teach a technical ASR model a reusable output convention
for unseen product-style names, while preserving performance on real speech?

## Why V1 Failed

Kokoro v1 trained only the 31 known real terms. The 50/50 arm also gave the
model half as many human examples as the human-only arm under the same update
budget. A 320-update additive rerun fixed that exposure mismatch and improved
overall WER from 0.2472 to 0.2413, but the gain remained concentrated on seen
vocabulary. Held-out fake WER worsened from 0.4371 to 0.4536.

The human-only predictions exposed a more specific target. Only 4 of 135
held-out coined-name mentions were exact, but 39 were already present after
removing spaces, punctuation, and case. Many errors were formatting failures
such as `Drift Pilot` instead of `DriftPilot`.

## Frozen V2 Recipe

The compositional corpus contains 96 new CamelCase names built from generic
technical morphemes. Every complete name is disjoint from all benchmark terms.
Kokoro speaks the components separately while the ASR label joins them. Four
voices produce 384 clips and 1,592.425 seconds of audio.

The final one-epoch mixture contains:

| source | records |
| --- | ---: |
| human, 64 sources repeated 20 times | 1,280 |
| Kokoro v1 real-term clips | 248 |
| Kokoro compositional clips | 384 |
| total | 1,912 |

Training uses Whisper base.en LoRA rank 16, alpha 32, dropout 0.05, learning
rate 1e-4, effective batch size 8, and 239 optimizer updates. Model selection
uses the same 16 real-human `s05` development clips. Evaluation is the same
240-clip real-human v2 benchmark with beam size 5.

## Seed 13 Result

| split | human-only WER | compositional WER | human-only exact | compositional exact |
| --- | ---: | ---: | ---: | ---: |
| overall | 0.2472 | 0.2163 | 195 / 496 | 218 / 496 |
| train vocabulary | 0.1152 | 0.1000 | 165 / 224 | 171 / 224 |
| held-out real | 0.2524 | 0.2266 | 26 / 137 | 30 / 137 |
| held-out coined | 0.4371 | 0.3772 | 4 / 135 | 17 / 135 |

The held-out coined exact-match count increased 4.25x even though none of the
complete held-out terms occurred in synthetic training.

No held-out coined term lost an exact hit. Gains occurred across six complete
unseen names: `TraceNest` (0 to 2), `SchemaHawk` (2 to 4), `DriftPilot` (1 to
5), `ModelCrate` (0 to 2), `VectorNook` (0 to 1), and `StreamLatch` (1 to 3).

## Paired Uncertainty

Differences are compositional minus human-only. Negative WER and positive term
rate favor compositional training.

| split | WER difference | 95% interval | term-rate difference | 95% interval |
| --- | ---: | ---: | ---: | ---: |
| overall | -0.0309 | [-0.0426, -0.0196] | +0.0464 | [+0.0246, +0.0692] |
| train vocabulary | -0.0152 | [-0.0312, 0.0000] | +0.0268 | [0.0000, +0.0545] |
| held-out real | -0.0258 | [-0.0422, -0.0109] | +0.0292 | [-0.0147, +0.0735] |
| held-out coined | -0.0599 | [-0.0871, -0.0320] | +0.0963 | [+0.0507, +0.1493] |

The intervals are 10,000-iteration paired clip bootstrap intervals. They
describe this fixed benchmark, not a population-level guarantee.

## Test Speaker

The unseen `s06` speaker improved on WER in every vocabulary slice:

| split | human-only | compositional |
| --- | ---: | ---: |
| train vocabulary | 0.1637 | 0.1579 |
| held-out real | 0.2388 | 0.2090 |
| held-out coined | 0.4649 | 0.4386 |

Each held-out test-speaker slice contains only 12 clips, and its paired
interval crosses zero. Exact held-out term counts did not improve on `s06`.

## Seed 67 Replication

A second run changed only the trainer seed from 13 to 67. Its selected dev loss
was 1.015 versus 1.020 for seed 13. It replicated the core transfer result:

| split | seed 13 WER | seed 67 raw WER | seed 13 exact | seed 67 exact |
| --- | ---: | ---: | ---: | ---: |
| train vocabulary | 0.1000 | 0.0990 | 171 / 224 | 172 / 224 |
| held-out real | 0.2266 | 0.2212 | 30 / 137 | 33 / 137 |
| held-out coined | 0.3772 | 1.0254 | 17 / 135 | 17 / 135 |

The raw seed 67 held-out-coined WER is dominated by one failure: `s03_040`
entered a repeated-punctuation decode loop. This exact pathology had occurred
in an earlier base-model run. It is retained in the raw result.

An explicit audit excluding only `s03_040` gives seed 67 overall WER 0.2103,
held-out-real WER 0.2212, and held-out-coined WER 0.3652. Seed 13 scores
0.2158, 0.2266, and 0.3773 on the same audit. The seed 67 paired audit intervals
against human-only exclude zero for overall WER, held-out-real WER,
held-out-coined WER, and held-out-coined exact-term rate.

The orthographic-transfer effect replicated: both seeds produced exactly 17
of 135 unseen coined-name mentions. End-to-end raw reliability did not fully
replicate because one seed produced one catastrophic decoding loop. The model
result and the decoder reliability issue should be reported separately.

## Causal Boundary

This is a genuine unseen-full-term result inside the current benchmark: all 96
synthetic names are disjoint from all benchmark names, and all evaluation audio
is real human speech. It is not yet a clean publication-grade final test. The
benchmark had already been inspected when the compositional hypothesis was
formed, so the result is exploratory and test-aware. The next publishable step
is to freeze this recipe and evaluate it on a newly collected or external human
holdout without changing the recipe.

## Artifacts

- prompt definition: `data/synthetic/kokoro-compositional-v1/`
- additive mixture: `data/synthetic/kokoro-additive-v2/`
- main comparison: `results/comparisons/kokoro-additive-v2-compositional/`
- speaker slices: `results/comparisons/kokoro-additive-v2-compositional-slices/`
- paired bootstrap: `results/comparisons/kokoro-additive-v2-compositional-bootstrap/`
- two-seed raw comparison: `results/comparisons/kokoro-additive-v2-compositional-seeds/`
- two-seed one-clip audit: `results/comparisons/kokoro-additive-v2-compositional-seeds-no-s03-040/`
- seed 67 audit bootstrap: `results/comparisons/kokoro-additive-v2-compositional-seed67-bootstrap-no-s03-040/`

Synthetic and human audio remain private. Trained adapters remain local.
