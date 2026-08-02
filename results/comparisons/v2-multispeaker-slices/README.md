# V2 Slice Comparison

| speaker partition | term split | clips | run | WER | CER | term exact | term rate |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| train_speaker | train | 64 | baseline | 0.3237 | 0.0807 | 44 / 145 | 0.3034 |
| train_speaker | train | 64 | lora | 0.1018 | 0.0241 | 112 / 145 | 0.7724 |
| train_speaker | heldout_real | 48 | baseline | 0.3347 | 0.1108 | 9 / 93 | 0.0968 |
| train_speaker | heldout_real | 48 | lora | 0.2686 | 0.0891 | 17 / 93 | 0.1828 |
| train_speaker | heldout_fake | 48 | baseline | 0.5079 | 0.1335 | 0 / 91 | 0.0000 |
| train_speaker | heldout_fake | 48 | lora | 0.4379 | 0.1213 | 2 / 91 | 0.0220 |
| dev_speaker | train | 16 | baseline | 0.2981 | 0.0774 | 14 / 37 | 0.3784 |
| dev_speaker | train | 16 | lora | 0.1180 | 0.0296 | 28 / 37 | 0.7568 |
| dev_speaker | heldout_real | 12 | baseline | 0.2269 | 0.0515 | 2 / 23 | 0.0870 |
| dev_speaker | heldout_real | 12 | lora | 0.2017 | 0.0540 | 4 / 23 | 0.1739 |
| dev_speaker | heldout_fake | 12 | baseline | 0.4865 | 0.1168 | 1 / 22 | 0.0455 |
| dev_speaker | heldout_fake | 12 | lora | 0.4054 | 0.0984 | 1 / 22 | 0.0455 |
| test_speaker | train | 16 | baseline | 0.2807 | 0.0803 | 18 / 42 | 0.4286 |
| test_speaker | train | 16 | lora | 0.1637 | 0.0425 | 25 / 42 | 0.5952 |
| test_speaker | heldout_real | 12 | baseline | 0.3209 | 0.0893 | 2 / 21 | 0.0952 |
| test_speaker | heldout_real | 12 | lora | 0.2388 | 0.0701 | 5 / 21 | 0.2381 |
| test_speaker | heldout_fake | 12 | baseline | 0.5877 | 0.1708 | 0 / 22 | 0.0000 |
| test_speaker | heldout_fake | 12 | lora | 0.4649 | 0.1309 | 1 / 22 | 0.0455 |
