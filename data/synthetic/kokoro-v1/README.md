# Kokoro Synthetic Training V1

## Purpose

This dataset tests whether open-source synthetic speech can improve a Whisper
LoRA adapter on frozen, real-human TechSpeechBench evaluation audio.

Kokoro generates training audio. Whisper `base.en` is the ASR model being
fine-tuned. Kokoro audio must never enter development or evaluation splits.

## Frozen Scope

- 31 train-vocabulary terms from `data/v2/domain_terms.tsv`
- no `heldout_real` or `heldout_fake` terms in synthetic prompts
- pronunciation labels remain separate from TTS spoken forms
- one human listening gate before any multi-voice generation
- final target after approval: 2 new sentences per term x 4 voices = 248 clips

## Gate Protocol

Review `pronunciation-review.tsv`. Each row contains:

- the canonical term and sentence used as the ASR label
- the exact spoken form and sentence Kokoro will receive
- a plain pronunciation cue
- the final `review_status`

Allowed statuses are `pending`, `approved`, and `revise`. The preparation
script blocks audio generation until every row is `approved`. All 31 rows are
now approved.

After text approval, the next gate is one `af_heart` clip per term. Only after
all 31 clips pass human listening review may the four-voice dataset be built.

The listening gate is split into six ordered montages. Every montage inserts
0.75 seconds of silence between clips, and the private `review-index.tsv`
records the exact position, term, and expected pronunciation. Human listening,
not ASR output, determines approval.

### Audio Review Round 1

On 2026-08-03, 27 of 31 `af_heart` clips passed human listening review. Four
spoken forms failed and were corrected without changing their canonical ASR
labels:

- `kpg008` `tsconfig.json`: force JSON to sound like `jay-sawn`
- `kpg010` `FastAPI`: force all three letters in `A. P. I.`
- `kpg011` `Redis`: use `red iss`, not `ready`
- `kpg024` `Postgres`: use `post gress`, not `postgers`

Only these four masters were regenerated. The other 27 manifest rows and WAV
checksums were verified unchanged. The user approved all four replacements on
2026-08-03, closing the 31-term pronunciation gate.

## Training Corpus

`training-sentences.tsv` contains two new canonical sentences for each of the
31 train-vocabulary terms. The preparation script rejects held-out vocabulary,
other target terms in the same sentence, duplicate sentences, and exact reuse
of any real benchmark or pronunciation-gate sentence. It then derives private
TTS input from the approved spoken forms without changing the canonical ASR
label.

## Experiment Arms

The frozen comparison contains:

1. existing human-only Whisper LoRA
2. synthetic-only Whisper LoRA
3. balanced human-plus-synthetic Whisper LoRA

All new arms use the same real-human development split, optimizer-update
budget, and untouched 240-clip human evaluation manifest.

## Result

Synthetic-only did not match human-only and did not improve exact unseen-term
recognition over base Whisper. The balanced arm was weaker on seen train terms,
but produced slightly better held-out point estimates than human-only:

- held-out real: WER `0.2469` vs `0.2524`; exact terms `27/137` vs `26/137`
- held-out fake: WER `0.4147` vs `0.4371`; exact terms `7/135` vs `4/135`
- unseen-speaker held-out real: WER `0.2090` vs `0.2388`; exact terms `6/21` vs `5/21`

Paired bootstrap intervals include zero for the held-out WER differences, so
these are promising point estimates rather than a conclusive generalization
gain. See `docs/kokoro-synthetic-training-v1.md` for the full protocol,
results, and limitations.
