# Transcript Run Comparison

| split | run | wer | cer | term exact | term rate | command exact |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| overall | human_only | 0.2468 | 0.0707 | 195 / 494 | 0.3947 | 35 / 47 |
| overall | seed13 | 0.2158 | 0.0659 | 218 / 494 | 0.4413 | 35 / 47 |
| overall | seed67 | 0.2103 | 0.0650 | 222 / 494 | 0.4494 | 35 / 47 |
| train | human_only | 0.1152 | 0.0282 | 165 / 224 | 0.7366 | 35 / 47 |
| train | seed13 | 0.1000 | 0.0256 | 171 / 224 | 0.7634 | 35 / 47 |
| train | seed67 | 0.0990 | 0.0255 | 172 / 224 | 0.7679 | 35 / 47 |
| heldout_real | human_only | 0.2524 | 0.0800 | 26 / 137 | 0.1898 | 0 / 0 |
| heldout_real | seed13 | 0.2266 | 0.0728 | 30 / 137 | 0.2190 | 0 / 0 |
| heldout_real | seed67 | 0.2212 | 0.0706 | 33 / 137 | 0.2409 | 0 / 0 |
| heldout_fake | human_only | 0.4379 | 0.1193 | 4 / 133 | 0.0301 | 0 / 0 |
| heldout_fake | seed13 | 0.3773 | 0.1137 | 17 / 133 | 0.1278 | 0 / 0 |
| heldout_fake | seed67 | 0.3652 | 0.1132 | 17 / 133 | 0.1278 | 0 / 0 |

## Worst Clips

### human_only

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

### seed13

- `s05_038` (heldout_fake), wer=0.8889, missed=RAGStack;RAGStone
  - ref: No, I meant RAGStone, not RAGStack, for the reranker.
  - hyp: No, I'm in the RACS tool, not RACS stack for the re-ranker.
- `s03_033` (heldout_real), wer=0.8750, missed=LangGraph;Tavily
  - ref: LangGraph retried after Tavily returned an empty answer.
  - hyp: Line graph retried after the ugly return and empty answers.
- `s06_038` (heldout_fake), wer=0.7778, missed=EvalSpire;LatticeForge
  - ref: LatticeForge compared the output while EvalSpire flagged the mismatch.
  - hyp: Lattice forge compared the output while Ewells by a flag to mismatch.
- `s02_038` (heldout_fake), wer=0.7500, missed=PromptForge;QueryMosaic;ToolSparrow
  - ref: PromptForge called ToolSparrow after QueryMosaic returned no candidates.
  - hyp: Prommed force called ToolSparo after query Mosaic, return no candidates.
- `s02_039` (heldout_fake), wer=0.7500, missed=ModelCrate;TokenHarbor
  - ref: ModelCrate loaded slowly until TokenHarbor shortened the request.
  - hyp: Model create loaded slowly until token hire was shortened in the request.

### seed67

- `s03_033` (heldout_real), wer=0.8750, missed=LangGraph;Tavily
  - ref: LangGraph retried after Tavily returned an empty answer.
  - hyp: Line graph retried after the ugly return and empty answers.
- `s06_038` (heldout_fake), wer=0.7778, missed=EvalSpire;LatticeForge
  - ref: LatticeForge compared the output while EvalSpire flagged the mismatch.
  - hyp: Lattice Forge compared the output while Ewells by a flag to mismatch.
- `s02_038` (heldout_fake), wer=0.7500, missed=PromptForge;QueryMosaic;ToolSparrow
  - ref: PromptForge called ToolSparrow after QueryMosaic returned no candidates.
  - hyp: Prommed Force called ToolSparo after query Mosaic, return no candidates.
- `s03_039` (heldout_fake), wer=0.7500, missed=CacheWeaver;ModelCrate;TokenHarbor
  - ref: CacheWeaver warmed ModelCrate before TokenHarbor trimmed the prompt.
  - hyp: Cash viewer warmed model threat before token haber trimmed the prompt.
- `s02_019` (heldout_fake), wer=0.7000, missed=EvalSage;PromptForge
  - ref: PromptForge generated the fixture while EvalSage compared the answer traces.
  - hyp: Prompt4 generated the fixture where Ewell's age compared the answer to ACES.
