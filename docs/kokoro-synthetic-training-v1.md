# Kokoro Synthetic Training V1

## Question

Can open-source synthetic speech improve technical ASR when every model is
selected and evaluated only on real-human audio?

## Frozen Design

- ASR base model: `openai/whisper-base.en`
- adaptation: LoRA rank 16, alpha 32, dropout 0.05
- optimizer budget: 160 updates for every arm
- effective batch size: 8
- development: 16 real-human train-vocabulary clips from unseen speaker `s05`
- evaluation: the same frozen 240 real-human TechSpeechBench v2 clips
- decoding: Transformers Whisper, MPS, English transcription prompt, beam size 5
- seed: 13

The synthetic corpus contains 62 new sentences: two for each of 31 train terms.
Kokoro rendered every sentence with four voices, producing 248 clips and
1,077.05 seconds of audio. No synthetic audio or held-out vocabulary entered
development or evaluation.

Canonical ASR labels remain separate from TTS input. For example, Kokoro hears
`requirements dot T X T`, while Whisper is trained to emit
`requirements.txt`.

## Quality Gates

1. Every spoken form was reviewed as text.
2. One `af_heart` clip per term passed human listening.
3. Four failed pronunciations were corrected and reviewed again.
4. The final 248 clips passed checksum, prompt mapping, voice coverage, 24 kHz
   mono PCM16, duration, clipping, and delivery-rate checks.
5. Base Whisper produced a nonempty, structurally complete transcript for all
   248 clips. Term errors were retained because those are the training target.

## Training Arms

| arm | records | composition |
| --- | ---: | --- |
| human-only | 64 | existing real clips from `s01-s04` |
| synthetic-only | 248 | all Kokoro clips |
| balanced | 496 | all 248 Kokoro clips plus 248 deterministic draws from the 64 human clips |

The balanced arm is exactly 50% human and 50% synthetic by training record. It
uses all synthetic clips and repeats human clips in seeded shuffled cycles.

## Real-Human Results

| split | arm | WER | exact terms |
| --- | --- | ---: | ---: |
| overall | human-only | 0.2472 | 195 / 496 |
| overall | synthetic-only | 0.3223 | 106 / 496 |
| overall | balanced | 0.2568 | 165 / 496 |
| train vocabulary | human-only | 0.1152 | 165 / 224 |
| train vocabulary | synthetic-only | 0.2525 | 92 / 224 |
| train vocabulary | balanced | 0.1576 | 131 / 224 |
| held-out real | human-only | 0.2524 | 26 / 137 |
| held-out real | synthetic-only | 0.2890 | 13 / 137 |
| held-out real | balanced | 0.2469 | 27 / 137 |
| held-out fake | human-only | 0.4371 | 4 / 135 |
| held-out fake | synthetic-only | 0.4626 | 1 / 135 |
| held-out fake | balanced | 0.4147 | 7 / 135 |

Synthetic-only improved some ordinary transcription errors relative to base
Whisper, but it did not improve exact recognition of unseen terms: both base
and synthetic-only scored 13/137 on held-out real terms and 1/135 on held-out
fake terms.

Do not use the large base-to-synthetic overall WER gap as the headline result.
The controlled base run emitted repeated punctuation for `s03_040`, giving that
single clip WER `55.5` and inflating base overall and held-out-fake WER. Exact
term counts are unaffected, and the main conclusion uses the cleaner
human-only versus balanced comparison.

Balanced training was weaker than human-only on seen train terms. Its held-out
point estimates were slightly better: one additional exact real-term hit and
three additional fake-term hits. This tradeoff left balanced overall WER 0.0096
higher and overall exact-term rate 0.0605 lower than human-only.

## Unseen Speaker

The fully untouched `s06` speaker is the cleanest generalization slice.

| vocabulary | arm | WER | exact terms |
| --- | --- | ---: | ---: |
| train | human-only | 0.1637 | 25 / 42 |
| train | balanced | 0.2222 | 20 / 42 |
| held-out real | human-only | 0.2388 | 5 / 21 |
| held-out real | balanced | 0.2090 | 6 / 21 |
| held-out fake | human-only | 0.4649 | 1 / 22 |
| held-out fake | balanced | 0.4298 | 1 / 22 |

Balanced again traded weaker seen-vocabulary performance for better held-out
WER point estimates. The held-out slices contain only 12 clips each.

## Uncertainty

A 10,000-iteration paired clip bootstrap compared balanced against human-only.

| slice | WER difference | 95% interval | term-rate difference | 95% interval |
| --- | ---: | ---: | ---: | ---: |
| overall | +0.0096 | [-0.0013, +0.0208] | -0.0605 | [-0.0874, -0.0347] |
| train vocabulary | +0.0424 | [+0.0269, +0.0589] | -0.1518 | [-0.1974, -0.1078] |
| held-out real | -0.0054 | [-0.0219, +0.0108] | +0.0073 | [-0.0296, +0.0451] |
| held-out fake | -0.0225 | [-0.0462, +0.0015] | +0.0222 | [0.0000, +0.0522] |

Negative WER differences and positive term-rate differences favor balanced.
The held-out WER intervals cross zero, so the apparent gains are not conclusive.
The bootstrap describes uncertainty in this fixed benchmark; it does not prove
population-level significance.

## Conclusion

This experiment supports three claims:

1. Synthetic speech alone is not a substitute for a small human dataset.
2. A 50/50 mix can preserve most human-only performance while improving some
   held-out point estimates.
3. Training on known technical terms did not teach synthetic-only Whisper a
   general ability to spell unseen technical names.

The result is useful, but it is not a win large enough to claim that synthetic
data solved technical-term generalization. A stronger claim needs repeated
training seeds and a larger frozen human holdout.

## Reproducible Artifacts

- corpus definition: `data/synthetic/kokoro-v1/`
- complete split comparison: `results/comparisons/kokoro-v1-controlled/`
- speaker slices: `results/comparisons/kokoro-v1-controlled-slices/`
- paired bootstrap: `results/comparisons/kokoro-v1-controlled/BOOTSTRAP.md`
- synthetic-only adapter: `results/finetunes/whisper-base-en-lora-kokoro-v1-synthetic-only/`
- balanced adapter: `results/finetunes/whisper-base-en-lora-kokoro-v1-balanced/`

Synthetic and human audio remain private pending an explicit release decision.
