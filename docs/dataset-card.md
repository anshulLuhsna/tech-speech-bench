# TechSpeechBench Dataset Card

## Dataset Summary

TechSpeechBench v0 is a small technical dictation benchmark for software engineering and AI engineering speech.

The dataset is intended to evaluate whether speech-to-text systems preserve technical terms that are easy to misrecognize or normalize incorrectly.

## Dataset Version

`v0`

## Data Fields

`data/v0/manifest.tsv`

- `clip_id`
- `speaker_id`
- `split`
- `condition`
- `category`
- `audio_path`
- `duration_seconds`
- `size_bytes`
- `transcript_status`

`data/v0/references.tsv`

- `clip_id`
- `reference_text`

## Splits

- `dev`: clips 001-080
- `dev_stress`: clips 081-090
- `heldout`: clips 091-100

## Categories

- `ai_eval`
- `llm_infra`
- `agent_systems`
- `vector_database`
- `commands_files`
- `technical_notes_issues`
- `messy_corrections`
- `software_engineering`
- `natural_technical_thinking`
- `heldout_stress`

## Intended Use

- benchmark STT systems on technical dictation
- measure domain-term preservation
- compare baseline STT, vocabulary boosting, post-correction, and fine-tuning
- produce open evaluation reports for technical speech recognition

## Out Of Scope

- general speech recognition
- emotional speech recognition
- medical, legal, or customer-support transcription
- private company or proprietary code transcription

## Release Status

Private local dataset until licensing and consent rules are finalized.

## Known Limitations

- v0 currently has one speaker.
- Clips are short, roughly 3 to 11 seconds.
- References were generated from the planned utterance list and should be manually checked against the audio before final evaluation.

