# Transcript Run Comparison

| split | run | wer | cer | term exact | term rate | command exact |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| overall | baseline | 0.1991 | 0.0421 | 64 / 241 | 0.2656 | 4 / 6 |
| overall | lora-dev | 0.1539 | 0.0464 | 99 / 241 | 0.4108 | 6 / 6 |
| overall | lora-alltrain | 0.1399 | 0.0354 | 100 / 241 | 0.4149 | 6 / 6 |
| train | baseline | 0.1330 | 0.0346 | 34 / 84 | 0.4048 | 4 / 6 |
| train | lora-dev | 0.0922 | 0.0253 | 50 / 84 | 0.5952 | 6 / 6 |
| train | lora-alltrain | 0.0727 | 0.0176 | 52 / 84 | 0.6190 | 6 / 6 |
| heldout_real | baseline | 0.1440 | 0.0343 | 22 / 77 | 0.2857 | 0 / 0 |
| heldout_real | lora-dev | 0.1440 | 0.0448 | 27 / 77 | 0.3506 | 0 / 0 |
| heldout_real | lora-alltrain | 0.1401 | 0.0436 | 27 / 77 | 0.3506 | 0 / 0 |
| heldout_fake | baseline | 0.3347 | 0.0580 | 8 / 80 | 0.1000 | 0 / 0 |
| heldout_fake | lora-dev | 0.2361 | 0.0707 | 22 / 80 | 0.2750 | 0 / 0 |
| heldout_fake | lora-alltrain | 0.2177 | 0.0464 | 21 / 80 | 0.2625 | 0 / 0 |

## Worst Clips

### baseline

- `tsb_v1_101` (heldout_fake), wer=0.7000, missed=FastServeX;ModelStack
  - ref: ModelStack should preload the small checkpoint before FastServeX accepts traffic.
  - hyp: Model stack should preload the small checkpoint before faster wrecks except stuff it.
- `tsb_v1_119` (heldout_fake), wer=0.6667, missed=EmbedForge;QueryForge
  - ref: Set EmbedForge to read-only during the QueryForge regression test.
  - hyp: Set embed force to read only during the query force regression test.
- `tsb_v1_120` (heldout_fake), wer=0.6364, missed=CacheWeaver;ModelStack
  - ref: CacheWeaver masks the slow response until ModelStack emits the cold-start metric.
  - hyp: cache weaver masks the slow response until model stack emits the cold start metric
- `tsb_v1_098` (heldout_fake), wer=0.6000, missed=ContextDB;GraphForge
  - ref: GraphForge deploys cleanly, but ContextDB needs a manual index refresh.
  - hyp: Graph 4 is deployed cleanly, but contents DB needs a manual index refresh.
- `tsb_v1_106` (heldout_fake), wer=0.5833, missed=DataForgeX;StreamForge
  - ref: StreamForge replays the missing window, and DataForgeX marks three rows as malformed.
  - hyp: Stream force replace the missing window and data force X marks 3 rows as malformed.

### lora-dev

- `tsb_v1_097` (heldout_fake), wer=1.0000, missed=NeuroWeave;StreamMesh
  - ref: NeuroWeave enriches the records before StreamMesh pushes them to the downstream queue.
  - hyp: [replacement-char][replacement-char][replacement-char][replacement-char][replacement-char][replacement-char][replacement-char][replacement-char][replacement-char][replacement-ch...
- `tsb_v1_119` (heldout_fake), wer=0.6667, missed=EmbedForge;QueryForge
  - ref: Set EmbedForge to read-only during the QueryForge regression test.
  - hyp: Set embed force to read only during the query force regression test.
- `tsb_v1_075` (heldout_real), wer=0.6154, missed=FlashAttention;LoRA
  - ref: Enable LoRA for the adapter test, wait, disable FlashAttention for the reproducibility run.
  - hyp: Enable flash attention for the reproducibility run.
- `tsb_v1_101` (heldout_fake), wer=0.5000, missed=FastServeX
  - ref: ModelStack should preload the small checkpoint before FastServeX accepts traffic.
  - hyp: ModelStack should preload the small checkpoint before faster wrecks, except stuff it.
- `tsb_v1_106` (heldout_fake), wer=0.5000, missed=DataForgeX;StreamForge
  - ref: StreamForge replays the missing window, and DataForgeX marks three rows as malformed.
  - hyp: Stream Force replaced the missing window and Data Force X marks three rows as malformed.

### lora-alltrain

- `tsb_v1_119` (heldout_fake), wer=0.6667, missed=EmbedForge;QueryForge
  - ref: Set EmbedForge to read-only during the QueryForge regression test.
  - hyp: Set embed force to read only during the query force regression test.
- `tsb_v1_075` (heldout_real), wer=0.6154, missed=FlashAttention;LoRA
  - ref: Enable LoRA for the adapter test, wait, disable FlashAttention for the reproducibility run.
  - hyp: Enable flash attention for the reproducibility run.
- `tsb_v1_095` (heldout_fake), wer=0.5000, missed=CacheWeaver;EmbedForge
  - ref: Refresh EmbedForge after the import, actually invalidate CacheWeaver before rerunning the query.
  - hyp: Refresh embedded force after the import, actually invalidate the cache we were before rerunning the query.
- `tsb_v1_101` (heldout_fake), wer=0.5000, missed=FastServeX
  - ref: ModelStack should preload the small checkpoint before FastServeX accepts traffic.
  - hyp: ModelStack should preload the small checkpoint before faster wrecks, except stuff it.
- `tsb_v1_106` (heldout_fake), wer=0.5000, missed=DataForgeX;StreamForge
  - ref: StreamForge replays the missing window, and DataForgeX marks three rows as malformed.
  - hyp: Stream Force replaced the missing window and Data Force X marks three rows as malformed.
