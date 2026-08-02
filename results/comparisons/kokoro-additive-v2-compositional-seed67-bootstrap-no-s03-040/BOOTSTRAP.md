# Paired Bootstrap Comparison

Differences are `seed67 - human_only`. Negative WER and positive term-rate differences favor `seed67`.
Excluded clips: `s03_040`

| slice | clips | WER diff | 95% interval | term-rate diff | 95% interval |
| --- | ---: | ---: | ---: | ---: | ---: |
| overall | 239 | -0.0364 | [-0.0486, -0.0251] | 0.0547 | [0.0309, 0.0791] |
| train | 96 | -0.0162 | [-0.0310, -0.0010] | 0.0312 | [0.0044, 0.0599] |
| heldout_real | 72 | -0.0312 | [-0.0517, -0.0121] | 0.0511 | [0.0000, 0.1077] |
| heldout_fake | 71 | -0.0727 | [-0.0979, -0.0483] | 0.0977 | [0.0511, 0.1532] |
| train_speaker/train | 64 | -0.0167 | [-0.0291, -0.0061] | 0.0345 | [0.0070, 0.0658] |
| train_speaker/heldout_real | 48 | -0.0393 | [-0.0642, -0.0162] | 0.0645 | [0.0000, 0.1398] |
| train_speaker/heldout_fake | 47 | -0.0713 | [-0.1016, -0.0403] | 0.0899 | [0.0333, 0.1566] |
| dev_speaker/train | 16 | -0.0248 | [-0.0584, 0.0062] | 0.0270 | [-0.0556, 0.1176] |
| dev_speaker/heldout_real | 12 | 0.0084 | [-0.0410, 0.0574] | 0.0435 | [0.0000, 0.1364] |
| dev_speaker/heldout_fake | 12 | -0.0811 | [-0.1481, -0.0265] | 0.1818 | [0.0417, 0.3684] |
| test_speaker/train | 16 | -0.0058 | [-0.0734, 0.0629] | 0.0238 | [-0.0488, 0.1087] |
| test_speaker/heldout_real | 12 | -0.0373 | [-0.0846, 0.0000] | 0.0000 | [-0.1364, 0.1364] |
| test_speaker/heldout_fake | 12 | -0.0702 | [-0.1391, -0.0172] | 0.0455 | [0.0000, 0.1365] |

Intervals are clip-level paired percentile-bootstrap intervals, not proof of population-level significance. Small 12-clip slices are especially uncertain.
