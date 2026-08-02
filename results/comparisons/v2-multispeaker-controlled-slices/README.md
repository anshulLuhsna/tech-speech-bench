# V2 Slice Comparison

| speaker partition | term split | clips | run | WER | CER | term exact | term rate |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| train_speaker | train | 64 | base | 0.3116 | 0.0790 | 48 / 145 | 0.3310 |
| train_speaker | train | 64 | lora | 0.1018 | 0.0241 | 112 / 145 | 0.7724 |
| train_speaker | heldout_real | 48 | base | 0.3409 | 0.1096 | 8 / 93 | 0.0860 |
| train_speaker | heldout_real | 48 | lora | 0.2686 | 0.0891 | 17 / 93 | 0.1828 |
| train_speaker | heldout_fake | 48 | base | 1.4966 | 0.4127 | 0 / 91 | 0.0000 |
| train_speaker | heldout_fake | 48 | lora | 0.4379 | 0.1213 | 2 / 91 | 0.0220 |
| dev_speaker | train | 16 | base | 0.3043 | 0.0717 | 15 / 37 | 0.4054 |
| dev_speaker | train | 16 | lora | 0.1180 | 0.0296 | 28 / 37 | 0.7568 |
| dev_speaker | heldout_real | 12 | base | 0.2353 | 0.0540 | 2 / 23 | 0.0870 |
| dev_speaker | heldout_real | 12 | lora | 0.2017 | 0.0540 | 4 / 23 | 0.1739 |
| dev_speaker | heldout_fake | 12 | base | 0.4595 | 0.1010 | 1 / 22 | 0.0455 |
| dev_speaker | heldout_fake | 12 | lora | 0.4054 | 0.0984 | 1 / 22 | 0.0455 |
| test_speaker | train | 16 | base | 0.3041 | 0.0831 | 18 / 42 | 0.4286 |
| test_speaker | train | 16 | lora | 0.1637 | 0.0425 | 25 / 42 | 0.5952 |
| test_speaker | heldout_real | 12 | base | 0.2910 | 0.0836 | 3 / 21 | 0.1429 |
| test_speaker | heldout_real | 12 | lora | 0.2388 | 0.0701 | 5 / 21 | 0.2381 |
| test_speaker | heldout_fake | 12 | base | 0.5877 | 0.1509 | 0 / 22 | 0.0000 |
| test_speaker | heldout_fake | 12 | lora | 0.4649 | 0.1309 | 1 / 22 | 0.0455 |
