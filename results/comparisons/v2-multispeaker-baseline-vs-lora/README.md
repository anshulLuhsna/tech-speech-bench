# Transcript Run Comparison

| split | run | wer | cer | term exact | term rate | command exact |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| overall | baseline | 0.3704 | 0.1022 | 90 / 496 | 0.1815 | 21 / 47 |
| overall | lora | 0.2472 | 0.0709 | 195 / 496 | 0.3931 | 35 / 47 |
| train | baseline | 0.3121 | 0.0801 | 76 / 224 | 0.3393 | 21 / 47 |
| train | lora | 0.1152 | 0.0282 | 165 / 224 | 0.7366 | 35 / 47 |
| heldout_real | baseline | 0.3148 | 0.0973 | 13 / 137 | 0.0949 | 0 / 0 |
| heldout_real | lora | 0.2524 | 0.0800 | 26 / 137 | 0.1898 | 0 / 0 |
| heldout_fake | baseline | 0.5180 | 0.1372 | 1 / 135 | 0.0074 | 0 / 0 |
| heldout_fake | lora | 0.4371 | 0.1192 | 4 / 135 | 0.0296 | 0 / 0 |

## Worst Clips

### baseline

- `s03_024` (train), wer=1.2222, missed=FastAPI;Nginx;OpenAPI
  - ref: FastAPI served OpenAPI docs after Nginx forwarded the header.
  - hyp: First step is to open a PI Docs after engine x forwarded header
- `s02_038` (heldout_fake), wer=1.1250, missed=PromptForge;QueryMosaic;ToolSparrow
  - ref: PromptForge called ToolSparrow after QueryMosaic returned no candidates.
  - hyp: Prompt force call tool sparrow after query mosaic return no candidates
- `s03_039` (heldout_fake), wer=1.1250, missed=CacheWeaver;ModelCrate;TokenHarbor
  - ref: CacheWeaver warmed ModelCrate before TokenHarbor trimmed the prompt.
  - hyp: cache viewer, want model create, before token haber, trim the prompt
- `s01_027` (train), wer=1.0000, missed=FastAPI;pytest -k
  - ref: Use pytest -k websocket when debugging the FastAPI stream handler.
  - hyp: use pi test minus k web socket when the debugging the fast API stream handler
- `s03_023` (train), wer=1.0000, missed=Ruff;pytest -k;requirements.txt
  - ref: Run pytest -k billing after updating requirements.txt and Ruff.
  - hyp: current pi test dash k billing after updating requirements not txt and rough

### lora

- `s02_038` (heldout_fake), wer=0.8750, missed=PromptForge;QueryMosaic;ToolSparrow
  - ref: PromptForge called ToolSparrow after QueryMosaic returned no candidates.
  - hyp: Prommed force called Tool Sparrow after query Mosaic, return no candidates.
- `s03_033` (heldout_real), wer=0.8750, missed=LangGraph;Tavily
  - ref: LangGraph retried after Tavily returned an empty answer.
  - hyp: Line graph retried after the ugly return and empty answers.
- `s06_038` (heldout_fake), wer=0.7778, missed=EvalSpire;LatticeForge
  - ref: LatticeForge compared the output while EvalSpire flagged the mismatch.
  - hyp: Lattice Forge compared the output while Ewells by a flag to mismatch.
- `s06_039` (heldout_fake), wer=0.7778, missed=ShardMason;StreamHarbor
  - ref: ShardMason queued the batch after StreamHarbor sealed the partition.
  - hyp: Shard Mason cured the batch of the stream Harbor sealed the partition.
- `s03_039` (heldout_fake), wer=0.7500, missed=CacheWeaver;ModelCrate;TokenHarbor
  - ref: CacheWeaver warmed ModelCrate before TokenHarbor trimmed the prompt.
  - hyp: Cash viewer warmed model threat before token haber trimmed the prompt.
