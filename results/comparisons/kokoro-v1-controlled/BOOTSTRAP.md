# Paired Bootstrap Comparison

Differences are `balanced - human_only`. Negative WER and positive term-rate differences favor `balanced`.

| slice | clips | WER diff | 95% interval | term-rate diff | 95% interval |
| --- | ---: | ---: | ---: | ---: | ---: |
| overall | 240 | 0.0096 | [-0.0013, 0.0208] | -0.0605 | [-0.0874, -0.0347] |
| train | 96 | 0.0424 | [0.0269, 0.0589] | -0.1518 | [-0.1974, -0.1078] |
| heldout_real | 72 | -0.0054 | [-0.0219, 0.0108] | 0.0073 | [-0.0296, 0.0451] |
| heldout_fake | 72 | -0.0225 | [-0.0462, 0.0015] | 0.0222 | [0.0000, 0.0522] |
| train_speaker/train | 64 | 0.0319 | [0.0166, 0.0489] | -0.1517 | [-0.2053, -0.1020] |
| train_speaker/heldout_real | 48 | -0.0041 | [-0.0204, 0.0124] | -0.0108 | [-0.0581, 0.0337] |
| train_speaker/heldout_fake | 48 | -0.0158 | [-0.0423, 0.0092] | 0.0220 | [0.0000, 0.0581] |
| dev_speaker/train | 16 | 0.0683 | [0.0296, 0.1132] | -0.1892 | [-0.3421, -0.0556] |
| dev_speaker/heldout_real | 12 | 0.0168 | [-0.0168, 0.0598] | 0.0435 | [0.0000, 0.1364] |
| dev_speaker/heldout_fake | 12 | -0.0360 | [-0.1043, 0.0360] | 0.0455 | [0.0000, 0.1500] |
| test_speaker/train | 16 | 0.0585 | [0.0000, 0.1159] | -0.1190 | [-0.2439, -0.0233] |
| test_speaker/heldout_real | 12 | -0.0299 | [-0.0902, 0.0148] | 0.0476 | [0.0000, 0.1430] |
| test_speaker/heldout_fake | 12 | -0.0351 | [-0.1130, 0.0351] | 0.0000 | [0.0000, 0.0000] |

Intervals are clip-level paired percentile-bootstrap intervals, not proof of population-level significance. Small 12-clip slices are especially uncertain.
