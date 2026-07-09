# V2 Data Generation Prompt

Use this prompt with another AI to generate new open-source-safe read-aloud transcripts for TechSpeechBench v2.

The goal is more speaker and wording variety, not memorization of v1.

```text
you are generating read-aloud transcript rows for an open-source speech recognition benchmark called techspeechbench.

purpose:
create short spoken utterances that test whether asr/stt systems can transcribe software engineering and ai engineering terms correctly.

important:
- output only tsv
- no markdown
- no explanations
- no copyrighted text
- no private company/internal names
- no real people's private info
- keep every row speakable aloud in one breath
- each utterance should sound like something an engineer might say during debugging, dictation, a meeting note, or a technical handoff
- do not make the lines poetic or marketing-like
- do not repeat the attached examples
- do not reuse exact sentence structure from attached examples
- preserve exact spelling/casing in the `terms` column

columns:
id	category	split	utterance	terms	notes

id rules:
- if i provide an existing max id, continue from the next id
- format ids as tsb_v2_001, tsb_v2_002, etc.

split rules:
- use only these split names: train, heldout_real, heldout_fake
- 40% train, 30% heldout_real, 30% heldout_fake
- do not place the same target term in more than one split
- heldout_real must contain real software/ai terms not used in train
- heldout_fake must contain plausible fake product/library names not used in train or heldout_real

categories:
- backend services and deployment
- configuration and environment files
- commands and file names
- data pipelines and queues
- vector databases and retrieval
- ai evals and model behavior
- agent systems and tool calls
- observability and metrics
- model serving and inference
- messy spoken corrections

utterance rules:
- 8 to 18 words per utterance
- include 1 to 3 target terms per row
- mix sentence shapes
- include some messy spoken correction rows, for example "wait, change x to y" or "no, i meant x"
- include some command/file rows with strings like `.env`, `Dockerfile`, `requirements.txt`, `pytest -k`, `tsconfig.json`
- include some acronym/casing traps like `LoRA`, `vLLM`, `CI/CD`, `OpenAPI`, `JWT`
- include some terms that asr often normalizes into common words, like `Qdrant`, `pgvector`, `Dagster`, `Sentry`, `Modal`
- heldout_fake terms should be pronounceable and plausible, such as `VectorMesh`, `PromptForge`, `CacheWeaver`, but do not use those exact examples if they appear in attached prior data

quality bar:
- each row should be useful if spoken by multiple speakers
- avoid tongue twisters
- avoid ultra-rare terms nobody would say
- avoid long lists of tools
- avoid sentences that only exist to stuff keywords
- make the technical term important to the meaning of the sentence

generate 120 rows.

before producing final tsv, internally check:
- ids are sequential
- all rows have 6 columns
- split ratios are correct
- target terms do not leak across splits
- heldout_fake terms are fake but plausible
- no attached prior utterance is repeated

now output only the tsv.
```

## How To Use With Multiple AIs

When asking the next AI, attach all rows generated so far and add:

```text
continue from the next unused id.
do not repeat any utterance, target term, fake term, or sentence structure from the attached rows.
keep the same tsv schema and split rules.
generate another 120 rows.
```

## Recording Plan

For the next real dataset, prioritize:

- 3 to 5 speakers minimum
- each speaker records 40 to 80 rows
- mix iPhone, MacBook mic, and earphones mic
- keep train/heldout split by transcript term, not by audio file
- keep exact transcript text fixed before recording
- do not edit the heldout transcripts after hearing model outputs

The next claim should be:

```text
does lora improve unseen technical terms across speakers and mics?
```
