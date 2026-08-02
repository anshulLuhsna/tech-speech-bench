# Paired Bootstrap Comparison

Differences are `compositional_v2 - human_only`. Negative WER and positive term-rate differences favor `compositional_v2`.

| slice | clips | WER diff | 95% interval | term-rate diff | 95% interval |
| --- | ---: | ---: | ---: | ---: | ---: |
| overall | 240 | -0.0309 | [-0.0426, -0.0196] | 0.0464 | [0.0246, 0.0692] |
| train | 96 | -0.0152 | [-0.0312, 0.0000] | 0.0268 | [0.0000, 0.0545] |
| heldout_real | 72 | -0.0258 | [-0.0422, -0.0109] | 0.0292 | [-0.0147, 0.0735] |
| heldout_fake | 72 | -0.0599 | [-0.0871, -0.0320] | 0.0963 | [0.0507, 0.1493] |
| train_speaker/train | 64 | -0.0152 | [-0.0275, -0.0046] | 0.0345 | [0.0070, 0.0676] |
| train_speaker/heldout_real | 48 | -0.0248 | [-0.0431, -0.0082] | 0.0215 | [-0.0306, 0.0745] |
| train_speaker/heldout_fake | 48 | -0.0790 | [-0.1129, -0.0449] | 0.1099 | [0.0521, 0.1778] |
| dev_speaker/train | 16 | -0.0248 | [-0.0759, 0.0185] | 0.0270 | [-0.0556, 0.1176] |
| dev_speaker/heldout_real | 12 | -0.0252 | [-0.0635, 0.0000] | 0.0870 | [0.0000, 0.1923] |
| dev_speaker/heldout_fake | 12 | -0.0180 | [-0.0741, 0.0374] | 0.1364 | [0.0000, 0.3158] |
| test_speaker/train | 16 | -0.0058 | [-0.0719, 0.0632] | 0.0000 | [-0.0667, 0.0667] |
| test_speaker/heldout_real | 12 | -0.0299 | [-0.0827, 0.0146] | 0.0000 | [-0.1364, 0.1364] |
| test_speaker/heldout_fake | 12 | -0.0263 | [-0.0973, 0.0351] | 0.0000 | [0.0000, 0.0000] |

Intervals are clip-level paired percentile-bootstrap intervals, not proof of population-level significance. Small 12-clip slices are especially uncertain.
