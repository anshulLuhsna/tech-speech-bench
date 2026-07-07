# Utterance Generation Prompt

Use this prompt with ChatGPT, Claude, Gemini, or another LLM to generate candidate utterances for TechSpeechBench.

The generated output is not the dataset by itself. Treat it as a candidate script. Review, edit, deduplicate, and split terms before recording.

This prompt is designed for multi-model batching. Run it in one AI, save the TSV, then attach that TSV to the next AI and ask it to continue from the next ID without repeating sentence shapes or terms too heavily.

## Prompt

```text
You are helping create TechSpeechBench, an open-source benchmark for software-engineering and AI-engineering speech-to-text.

Goal:
Generate short spoken utterances that a technical person might realistically say aloud while dictating software-engineering, AI-engineering, infrastructure, debugging, testing, data, or developer-tooling notes.

The benchmark is testing whether ASR systems can correctly preserve technical terms, code-like phrases, acronyms, casing, spacing, package names, file names, commands, configuration names, metrics, and tool names.

Do not generate private company examples, customer data, proprietary code, personal names, startup names, location-specific jargon, or anything that sounds like a private work conversation.

Important:
This dataset must test generalization, not memorization.

INPUTS:

START_ID:
[PASTE NEXT NUMERIC ID HERE, FOR EXAMPLE 001 OR 101]

COUNT:
[PASTE HOW MANY NEW ROWS TO GENERATE, FOR EXAMPLE 50]

ALLOWED SPLITS:
[PASTE SPLITS TO USE, FOR EXAMPLE train OR heldout_real OR heldout_fake]

GROUP A: TRAIN TERMS
These terms may appear in training/dev utterances.
[PASTE TRAIN TERMS HERE]

GROUP B: HELD-OUT REAL TERMS
These terms must appear only in held-out evaluation utterances.
[PASTE HELD-OUT REAL TERMS HERE]

GROUP C: FAKE BUT REALISTIC TERMS
Invented package/tool names. These test whether the system learned code-like structure rather than memorizing known terms.
[PASTE FAKE TERMS HERE]

PREVIOUS TSV ROWS:
[PASTE ALL PREVIOUSLY GENERATED TSV ROWS HERE. IF THIS IS THE FIRST BATCH, WRITE NONE.]

Task:
Generate COUNT new utterances, starting at START_ID and continuing sequentially.

If PREVIOUS TSV ROWS is not NONE:
- Do not repeat any previous utterance.
- Do not reuse the same sentence template with only term substitutions.
- Do not overuse the same verbs, such as "compare", "add", "run", or "check".
- Avoid using the same primary technical term distribution as the previous batch.
- Continue numbering from START_ID.

Split rules:
- If split is train, use only GROUP A terms.
- If split is heldout_real, use only GROUP B terms plus ordinary software words.
- If split is heldout_fake, use only GROUP C terms plus ordinary software words.
- Never leak held-out real or fake terms into train rows.
- Never use GROUP A terms as the main technical target in heldout_fake rows unless they are ordinary supporting context and not the test term.

Each utterance should be:
- 6 to 18 seconds when spoken aloud
- one sentence or two short sentences
- realistic for technical dictation
- safe for open-source release
- not a tongue-twister
- not a list of terms with no context
- focused on technical work, not private productivity journaling

Good utterance types:
- bug report notes
- issue descriptions
- implementation notes
- test failure summaries
- code review notes
- deployment notes
- eval result notes
- logging and observability notes
- data pipeline notes
- command/file/config references
- messy spoken corrections, such as "actually replace that with..."

Include these categories:
- AI evals and model behavior
- LLM infra and serving
- agent systems and tool calls
- vector databases and retrieval
- backend services and deployment
- commands and file names
- CI/CD and testing
- observability and metrics
- configuration and environment files
- data pipelines and queues
- messy spoken corrections, such as "actually replace that with..."

Output only valid TSV inside one fenced code block.

Columns:
id	split	category	terms	utterance

Rules:
- id format: tsb_v1_001, tsb_v1_002, etc., starting from START_ID
- split must be one of: train, heldout_real, heldout_fake
- terms must be semicolon-separated
- utterance must preserve exact spelling/casing of technical terms
- utterance must not contain tabs
- use varied categories and sentence structures
- include some utterances with natural corrections, but do not make every row a correction
- do not include markdown bullets outside the TSV
- do not include explanations
```

## How To Use

1. Fill the three term groups.
2. For the first AI, set `START_ID` to `001`, choose a `COUNT`, and set `PREVIOUS TSV ROWS` to `NONE`.
3. Save its output under `docs/generated-candidates/`, for example `batch-001-chatgpt.tsv`.
4. For the next AI, set `START_ID` to the next unused number and paste the previous TSV rows into `PREVIOUS TSV ROWS`.
5. Repeat with 2-4 different AIs.
6. Manually review:
   - remove weird utterances
   - remove duplicate sentence shapes
   - remove private or unrealistic examples
   - verify held-out terms do not leak into train examples
   - verify numbering is continuous
7. Create a final `data/v1/references.tsv`.

## Suggested Batch Plan

Batch 1:

```text
START_ID: 001
COUNT: 40
ALLOWED SPLITS: train
PREVIOUS TSV ROWS: NONE
```

Batch 2:

```text
START_ID: 041
COUNT: 40
ALLOWED SPLITS: train
PREVIOUS TSV ROWS: paste batch 1
```

Batch 3:

```text
START_ID: 081
COUNT: 20
ALLOWED SPLITS: heldout_real
PREVIOUS TSV ROWS: paste batches 1 and 2
```

Batch 4:

```text
START_ID: 101
COUNT: 20
ALLOWED SPLITS: heldout_fake
PREVIOUS TSV ROWS: paste batches 1, 2, and 3
```

## Example Term Groups

Train terms:

```text
RAGAS
LangGraph
pgvector
LoRA
FastAPI
Pydantic
Dockerfile
pytest
OpenTelemetry
Redis
Celery
WebSocket
```

Held-out real terms:

```text
LlamaIndex
Qdrant
DSPy
LiteLLM
Ray Serve
uvicorn
Weaviate
Chroma
Arize Phoenix
OpenRouter
```

Fake but realistic terms:

```text
GraphForge
VectorPilot
EvalMint
TraceKit
CacheGraph
PromptHarbor
MetricFlow
RouteLens
ShardPilot
ToolSmith
```
