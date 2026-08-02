# V2 Slice Comparison

| speaker partition | term split | clips | run | WER | CER | term exact | term rate |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| train_speaker | train | 64 | base | 0.3116 | 0.0790 | 48 / 145 | 0.3310 |
| train_speaker | train | 64 | human_only | 0.1018 | 0.0241 | 112 / 145 | 0.7724 |
| train_speaker | train | 64 | synthetic_only | 0.2492 | 0.0659 | 57 / 145 | 0.3931 |
| train_speaker | train | 64 | balanced | 0.1337 | 0.0282 | 90 / 145 | 0.6207 |
| train_speaker | heldout_real | 48 | base | 0.3409 | 0.1096 | 8 / 93 | 0.0860 |
| train_speaker | heldout_real | 48 | human_only | 0.2686 | 0.0891 | 17 / 93 | 0.1828 |
| train_speaker | heldout_real | 48 | synthetic_only | 0.3120 | 0.1030 | 8 / 93 | 0.0860 |
| train_speaker | heldout_real | 48 | balanced | 0.2645 | 0.0835 | 16 / 93 | 0.1720 |
| train_speaker | heldout_fake | 48 | base | 1.4966 | 0.4127 | 0 / 91 | 0.0000 |
| train_speaker | heldout_fake | 48 | human_only | 0.4379 | 0.1213 | 2 / 91 | 0.0220 |
| train_speaker | heldout_fake | 48 | synthetic_only | 0.4650 | 0.1296 | 0 / 91 | 0.0000 |
| train_speaker | heldout_fake | 48 | balanced | 0.4221 | 0.1168 | 4 / 91 | 0.0440 |
| dev_speaker | train | 16 | base | 0.3043 | 0.0717 | 15 / 37 | 0.4054 |
| dev_speaker | train | 16 | human_only | 0.1180 | 0.0296 | 28 / 37 | 0.7568 |
| dev_speaker | train | 16 | synthetic_only | 0.2360 | 0.0507 | 18 / 37 | 0.4865 |
| dev_speaker | train | 16 | balanced | 0.1863 | 0.0468 | 21 / 37 | 0.5676 |
| dev_speaker | heldout_real | 12 | base | 0.2353 | 0.0540 | 2 / 23 | 0.0870 |
| dev_speaker | heldout_real | 12 | human_only | 0.2017 | 0.0540 | 4 / 23 | 0.1739 |
| dev_speaker | heldout_real | 12 | synthetic_only | 0.2185 | 0.0540 | 2 / 23 | 0.0870 |
| dev_speaker | heldout_real | 12 | balanced | 0.2185 | 0.0578 | 5 / 23 | 0.2174 |
| dev_speaker | heldout_fake | 12 | base | 0.4595 | 0.1010 | 1 / 22 | 0.0455 |
| dev_speaker | heldout_fake | 12 | human_only | 0.4054 | 0.0984 | 1 / 22 | 0.0455 |
| dev_speaker | heldout_fake | 12 | synthetic_only | 0.4234 | 0.1063 | 1 / 22 | 0.0455 |
| dev_speaker | heldout_fake | 12 | balanced | 0.3694 | 0.0906 | 2 / 22 | 0.0909 |
| test_speaker | train | 16 | base | 0.3041 | 0.0831 | 18 / 42 | 0.4286 |
| test_speaker | train | 16 | human_only | 0.1637 | 0.0425 | 25 / 42 | 0.5952 |
| test_speaker | train | 16 | synthetic_only | 0.2807 | 0.0785 | 17 / 42 | 0.4048 |
| test_speaker | train | 16 | balanced | 0.2222 | 0.0572 | 20 / 42 | 0.4762 |
| test_speaker | heldout_real | 12 | base | 0.2910 | 0.0836 | 3 / 21 | 0.1429 |
| test_speaker | heldout_real | 12 | human_only | 0.2388 | 0.0701 | 5 / 21 | 0.2381 |
| test_speaker | heldout_real | 12 | synthetic_only | 0.2687 | 0.0701 | 3 / 21 | 0.1429 |
| test_speaker | heldout_real | 12 | balanced | 0.2090 | 0.0621 | 6 / 21 | 0.2857 |
| test_speaker | heldout_fake | 12 | base | 0.5877 | 0.1509 | 0 / 22 | 0.0000 |
| test_speaker | heldout_fake | 12 | human_only | 0.4649 | 0.1309 | 1 / 22 | 0.0455 |
| test_speaker | heldout_fake | 12 | synthetic_only | 0.4912 | 0.1671 | 0 / 22 | 0.0000 |
| test_speaker | heldout_fake | 12 | balanced | 0.4298 | 0.1135 | 1 / 22 | 0.0455 |
