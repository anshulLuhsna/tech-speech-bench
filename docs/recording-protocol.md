# Recording Protocol

## Goal

Collect short technical utterances that expose where generic dictation systems fail on software engineering and AI engineering vocabulary.

## V0 Rules

- Record each utterance as a separate clip.
- Preserve original audio files.
- Avoid WhatsApp or other messaging-app transfer paths that may compress or transcode audio.
- Use stable IDs such as `tsb_v0_001.m4a`.
- Keep held-out eval clips untouched until after the first baseline report.

## Recommended Device Workflow

1. Record on iPhone with Voice Memos.
2. Export through Files, iCloud Drive, or AirDrop.
3. Keep the original `.m4a` files under `data/v0/audio/raw/`.
4. Convert copies to `.wav` only when a model or tool requires it.

## Metadata

Every clip should have:

```text
clip_id
speaker_id
split
condition
category
audio_path
duration_seconds
size_bytes
transcript_status
```

## Consent

For any future multi-speaker version, collect explicit consent before adding audio.

Suggested consent levels:

- private training/evaluation only
- demo snippets allowed
- public dataset release allowed

Do not collect proprietary company data, private user data, customer data, or unreleased code.

