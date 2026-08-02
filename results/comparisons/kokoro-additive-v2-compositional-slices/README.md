# V2 Slice Comparison

| speaker partition | term split | clips | run | WER | CER | term exact | term rate |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| train_speaker | train | 64 | human_only | 0.1018 | 0.0241 | 112 / 145 | 0.7724 |
| train_speaker | train | 64 | compositional_v2 | 0.0866 | 0.0217 | 117 / 145 | 0.8069 |
| train_speaker | heldout_real | 48 | human_only | 0.2686 | 0.0891 | 17 / 93 | 0.1828 |
| train_speaker | heldout_real | 48 | compositional_v2 | 0.2438 | 0.0807 | 19 / 93 | 0.2043 |
| train_speaker | heldout_fake | 48 | human_only | 0.4379 | 0.1213 | 2 / 91 | 0.0220 |
| train_speaker | heldout_fake | 48 | compositional_v2 | 0.3589 | 0.1119 | 12 / 91 | 0.1319 |
| dev_speaker | train | 16 | human_only | 0.1180 | 0.0296 | 28 / 37 | 0.7568 |
| dev_speaker | train | 16 | compositional_v2 | 0.0932 | 0.0229 | 29 / 37 | 0.7838 |
| dev_speaker | heldout_real | 12 | human_only | 0.2017 | 0.0540 | 4 / 23 | 0.1739 |
| dev_speaker | heldout_real | 12 | compositional_v2 | 0.1765 | 0.0515 | 6 / 23 | 0.2609 |
| dev_speaker | heldout_fake | 12 | human_only | 0.4054 | 0.0984 | 1 / 22 | 0.0455 |
| dev_speaker | heldout_fake | 12 | compositional_v2 | 0.3874 | 0.0919 | 4 / 22 | 0.1818 |
| test_speaker | train | 16 | human_only | 0.1637 | 0.0425 | 25 / 42 | 0.5952 |
| test_speaker | train | 16 | compositional_v2 | 0.1579 | 0.0434 | 25 / 42 | 0.5952 |
| test_speaker | heldout_real | 12 | human_only | 0.2388 | 0.0701 | 5 / 21 | 0.2381 |
| test_speaker | heldout_real | 12 | compositional_v2 | 0.2090 | 0.0633 | 5 / 21 | 0.2381 |
| test_speaker | heldout_fake | 12 | human_only | 0.4649 | 0.1309 | 1 / 22 | 0.0455 |
| test_speaker | heldout_fake | 12 | compositional_v2 | 0.4386 | 0.1372 | 1 / 22 | 0.0455 |
