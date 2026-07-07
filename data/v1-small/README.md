# TechSpeechBench V1 Small

## Current State

`manifest.tsv` contains 120 generated candidate utterances.

Columns:

```text
id
split
category
terms
utterance
```

## Split Counts

- `train`: 40 rows
- `heldout_real`: 40 rows
- `heldout_fake`: 40 rows

This differs from the earlier suggested 80/20/20 split. It is still usable as a candidate pool, but before recording v1 we should decide whether to keep this balanced 40/40/40 design or generate more train rows.

## Validation Notes

Basic checks passed:

- 120 rows parse as TSV.
- IDs are continuous from `tsb_v1_001` to `tsb_v1_120`.
- No duplicate IDs found.
- No overlap between train, held-out real, and held-out fake term sets.
- No obviously empty utterance or term fields found.

Important caveat:

- `v1-small` should be treated as a new generalization benchmark design, not as a continuation of v0. Some terms that appeared in v0 may appear in `v1-small` held-out real. That is acceptable only if v0 is not used to tune v1 experiments.

## Recommendation

Use this file as a candidate pool, not a final recording script yet.

Next review steps:

1. Remove any utterance that feels unnatural to say aloud.
2. Decide target split balance.
3. Optionally generate 40-80 more train rows before recording.
4. Freeze the term split before recording audio.

