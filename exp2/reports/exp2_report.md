# exp2 消融实验汇总

说明：baseline 与 mbv3 为 exp1 正式训练结果复用，不在 exp2 重复训练。

| Model | Precision | Recall | mAP50 | mAP50-95 | Params(M) | FPS |
| --- | --- | --- | --- | --- | --- | --- |
| baseline (exp1 reference) | 0.9190 | 0.9208 | 0.9587 | 0.8927 | 9.417 | 66.16 |
| mbv3 (exp1 reference) | 0.9332 | 0.9101 | 0.9598 | 0.8916 | 7.465 | 45.40 |
| p2_simam | N/A | N/A | N/A | N/A | N/A | N/A |
| p2_simam_dwconv | N/A | N/A | N/A | N/A | N/A | N/A |
| p2_simam_shuffle | N/A | N/A | N/A | N/A | N/A | N/A |
| p2_simam_dwconv_p075ghost | N/A | N/A | N/A | N/A | N/A | N/A |

