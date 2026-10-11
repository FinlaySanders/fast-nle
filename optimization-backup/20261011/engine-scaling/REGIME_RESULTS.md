# NetHack throughput regime results — 10 October 2026

Full stack = attribution_v37 with retained engine, GPU fast kernels, entity fusions, 4 Muon lanes, gradient overlap + 32 connections, inference priority, blocking waits, 32 workers. Frozen-actor recorded-action replay (mature games), batch 262,144, minibatch 4096, replay 1.78 unless stated. Fast protocol: 12 measured epochs after the mature plateau (512 agents: epochs 16-27; 2048: 32-43). Long window (15m512 only): epochs 24-62. Controls bracket every set; "drift" = closing vs opening control.


## Leave-one-out: 15M model, 512 agents, LONG window

Full-stack mean 228,454 SPS (controls 229,344, 227,564, drift -0.78%).

| Arm | SPS | vs full | epoch ms | rollout tail ms | PPO tail ms |
|---|---:|---:|---:|---:|---:|
| full stack (control a) | 229,344 | +0.39% | 1137 | 0 | 184 |
| everything off (stock engine, no GPU flags, 1 lane, overlap off, 8 conn, priority off) | 120,707 | -47.16% | 2146 | 774 | 32 |
| engine -> stock fast-nle (vendored HEAD) | 130,800 | -42.75% | 1975 | 895 | 25 |
| engine -> September engine14 | 182,188 | -20.25% | 1424 | 312 | 25 |
| engine -> pre-compact-state (persist) | 212,803 | -6.85% | 1223 | 88 | 25 |
| GPU fast kernels off | 207,352 | -9.24% | 1257 | 0 | 268 |
| entity fusions off | 220,434 | -3.51% | 1183 | 0 | 211 |
| Muon lanes 4 -> 1 | 207,132 | -9.33% | 1259 | 0 | 324 |
| gradient overlap off + 8 connections | 224,742 | -1.62% | 1160 | 0 | 217 |
| inference priority off | 211,463 | -7.44% | 1230 | 116 | 25 |
| blocking wait / finish sleep off | 227,991 | -0.20% | 1144 | 0 | 158 |
| workers 32 -> 16 | 226,910 | -0.68% | 1149 | 0 | 138 |
| full stack (control b) | 227,564 | -0.39% | 1145 | 0 | 190 |

## Leave-one-out: 15M, 512 agents

Full-stack mean 228,439 SPS (controls 228,788, 228,090, drift -0.31%).

| Arm | SPS | vs full | epoch ms | rollout tail ms | PPO tail ms |
|---|---:|---:|---:|---:|---:|
| full stack (control a) | 228,788 | +0.15% | 1131 | 0 | 215 |
| everything off (stock engine, no GPU flags, 1 lane, overlap off, 8 conn, priority off) | 117,810 | -48.43% | 2143 | 777 | 106 |
| engine -> stock fast-nle (vendored HEAD) | 126,757 | -44.51% | 1976 | 904 | 84 |
| engine -> September engine14 | 177,433 | -22.33% | 1435 | 334 | 84 |
| engine -> pre-compact-state (persist) | 206,982 | -9.39% | 1241 | 119 | 84 |
| GPU fast kernels off | 207,421 | -9.20% | 1248 | 0 | 321 |
| entity fusions off | 220,745 | -3.37% | 1172 | 0 | 254 |
| Muon lanes 4 -> 1 | 207,310 | -9.25% | 1249 | 0 | 371 |
| gradient overlap off + 8 connections | 225,054 | -1.48% | 1150 | 0 | 252 |
| inference priority off | 208,122 | -8.89% | 1236 | 133 | 84 |
| blocking wait / finish sleep off | 228,255 | -0.08% | 1135 | 0 | 191 |
| workers 32 -> 16 | 227,288 | -0.50% | 1139 | 0 | 172 |
| full stack (control b) | 228,090 | -0.15% | 1135 | 0 | 230 |

## Leave-one-out: 5M, 512 agents

Full-stack mean 276,393 SPS (controls 275,778, 277,008, drift +0.45%).

| Arm | SPS | vs full | epoch ms | rollout tail ms | PPO tail ms |
|---|---:|---:|---:|---:|---:|
| full stack (control a) | 275,778 | -0.22% | 913 | 316 | 46 |
| everything off (stock engine, no GPU flags, 1 lane, overlap off, 8 conn, priority off) | 123,854 | -55.19% | 1998 | 1229 | 61 |
| engine -> stock fast-nle (vendored HEAD) | 129,234 | -53.24% | 1901 | 1335 | 45 |
| engine -> September engine14 | 182,366 | -34.02% | 1359 | 783 | 45 |
| engine -> pre-compact-state (persist) | 213,515 | -22.75% | 1167 | 585 | 45 |
| GPU fast kernels off | 273,978 | -0.87% | 921 | 288 | 48 |
| entity fusions off | 276,675 | +0.10% | 913 | 279 | 48 |
| Muon lanes 4 -> 1 | 278,887 | +0.90% | 912 | 206 | 53 |
| gradient overlap off + 8 connections | 279,555 | +1.14% | 902 | 290 | 47 |
| inference priority off | 269,012 | -2.67% | 935 | 350 | 45 |
| blocking wait / finish sleep off | 266,378 | -3.62% | 944 | 352 | 45 |
| workers 32 -> 16 | 252,125 | -8.78% | 995 | 403 | 46 |
| full stack (control b) | 277,008 | +0.22% | 909 | 313 | 45 |

## Leave-one-out: 15M, 2048 agents

Full-stack mean 209,490 SPS (controls 209,281, 209,699, drift +0.20%).

| Arm | SPS | vs full | epoch ms | rollout tail ms | PPO tail ms |
|---|---:|---:|---:|---:|---:|
| full stack (control a) | 209,281 | -0.10% | 1223 | 191 | 80 |
| everything off (stock engine, no GPU flags, 1 lane, overlap off, 8 conn, priority off) | 130,462 | -37.72% | 1946 | 577 | 108 |
| engine -> stock fast-nle (vendored HEAD) | 133,753 | -36.15% | 1871 | 873 | 79 |
| engine -> September engine14 | 158,831 | -24.18% | 1587 | 577 | 79 |
| engine -> pre-compact-state (persist) | 177,680 | -15.18% | 1427 | 408 | 80 |
| GPU fast kernels off | 208,596 | -0.43% | 1242 | 14 | 96 |
| entity fusions off | 209,277 | -0.10% | 1226 | 151 | 82 |
| Muon lanes 4 -> 1 | 212,019 | +1.21% | 1217 | 65 | 88 |
| gradient overlap off + 8 connections | 218,442 | +4.27% | 1176 | 120 | 81 |
| inference priority off | 206,374 | -1.49% | 1238 | 209 | 80 |
| blocking wait / finish sleep off | 203,972 | -2.63% | 1254 | 224 | 79 |
| workers 32 -> 16 | 183,043 | -12.62% | 1387 | 368 | 80 |
| full stack (control b) | 209,699 | +0.10% | 1221 | 185 | 80 |

## Leave-one-out: 5M, 2048 agents

Full-stack mean 215,767 SPS (controls 214,952, 216,581, drift +0.76%).

| Arm | SPS | vs full | epoch ms | rollout tail ms | PPO tail ms |
|---|---:|---:|---:|---:|---:|
| full stack (control a) | 214,952 | -0.38% | 1153 | 637 | 41 |
| everything off (stock engine, no GPU flags, 1 lane, overlap off, 8 conn, priority off) | 131,468 | -39.07% | 1887 | 1104 | 63 |
| engine -> stock fast-nle (vendored HEAD) | 135,092 | -37.39% | 1815 | 1311 | 41 |
| engine -> September engine14 | 161,399 | -25.20% | 1525 | 1018 | 41 |
| engine -> pre-compact-state (persist) | 182,048 | -15.63% | 1357 | 847 | 41 |
| GPU fast kernels off | 214,814 | -0.44% | 1165 | 532 | 50 |
| entity fusions off | 214,825 | -0.44% | 1157 | 607 | 43 |
| Muon lanes 4 -> 1 | 218,422 | +1.23% | 1144 | 530 | 49 |
| gradient overlap off + 8 connections | 220,791 | +2.33% | 1126 | 594 | 42 |
| inference priority off | 215,691 | -0.04% | 1151 | 637 | 41 |
| blocking wait / finish sleep off | 211,442 | -2.00% | 1173 | 660 | 41 |
| workers 32 -> 16 | 187,918 | -12.91% | 1314 | 805 | 41 |
| full stack (control b) | 216,581 | +0.38% | 1146 | 631 | 41 |

## Agent-count scaling at constant batch (full stack, matched game age = 4096 recorded steps per env)

| Model | Agents x horizon | SPS | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---|---:|---:|---:|---:|---:|
| 15M | 512 x 512 | 228,468 | 1133 | 1133 | 0 | 217 |
| 15M | 1024 x 256 | 225,994 | 1140 | 1072 | 68 | 81 |
| 15M | 2048 x 128 | 209,490 | 1222 | 1034 | 188 | 80 |
| 15M | 4096 x 64 | 209,478 | 1222 | 1031 | 191 | 80 |
| 5M | 512 x 512 | 275,258 | 915 | 597 | 318 | 45 |
| 5M | 1024 x 256 | 234,722 | 1062 | 538 | 524 | 42 |
| 5M | 2048 x 128 | 215,767 | 1150 | 516 | 634 | 41 |
| 5M | 4096 x 64 | 213,658 | 1159 | 507 | 652 | 40 |

## Fused small-matrix Muon (PUF_MUON_FUSED_SMALL=64, 21 matrices), 15M/512


**15m512** — controls 227,868, 228,050 (drift +0.08%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| base_a | 227,868 | -0.04% | 1136 | 1136 | 0 | 219 |
| fused64_a | 232,062 | +1.80% | 1115 | 1115 | 0 | 204 |
| fused64_b | 232,301 | +1.90% | 1114 | 1114 | 0 | 202 |
| base_b | 228,050 | +0.04% | 1135 | 1135 | 0 | 228 |

## Phase-dependent GPU scheduling, collection-bound regimes


**5m2048** — controls 216,600, 216,435 (drift -0.08%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| full_a | 216,600 | +0.04% | 1146 | 515 | 631 | 41 |
| pipe_off_conn32 | 219,748 | +1.49% | 1131 | 531 | 601 | 42 |
| pipe3_conn8 | 158,644 | -26.73% | 1551 | 488 | 1062 | 42 |
| off_conn8_lanes1 | 221,244 | +2.18% | 1131 | 627 | 505 | 50 |
| full_b | 216,435 | -0.04% | 1147 | 515 | 631 | 41 |

**15m2048** — controls 211,331, 210,605 (drift -0.34%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| full_a | 211,331 | +0.17% | 1212 | 1032 | 180 | 79 |
| pipe_off_conn32 | 216,044 | +2.41% | 1188 | 1053 | 135 | 81 |
| pipe3_conn8 | 125,098 | -40.70% | 1996 | 952 | 1044 | 79 |
| off_conn8_lanes1 | 217,433 | +3.06% | 1190 | 1171 | 19 | 90 |
| full_b | 210,605 | -0.17% | 1216 | 1034 | 182 | 79 |

## Minibatch size (replay 1.78 fixed; updates/batch 113 -> 56 -> 28 -> 14)


**15m512** — controls 227,977, 228,205 (drift +0.10%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| mb4096_a | 227,977 | -0.05% | 1135 | 1135 | 0 | 219 |
| mb8192 | 253,821 | +11.28% | 1014 | 970 | 44 | 71 |
| mb16384 | 247,194 | +8.37% | 1031 | 857 | 174 | 63 |
| mb32768 | 243,779 | +6.88% | 1040 | 780 | 260 | 58 |
| mb4096_b | 228,205 | +0.05% | 1134 | 1134 | 0 | 226 |

**15m2048** — controls 211,238, 210,532 (drift -0.33%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| mb4096_a | 211,238 | +0.17% | 1213 | 1036 | 177 | 80 |
| mb32768 | 213,741 | +1.35% | 1180 | 767 | 413 | 60 |
| mb4096_b | 210,532 | -0.17% | 1216 | 1035 | 181 | 80 |

**5m512** — controls 275,796, 276,436 (drift +0.23%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| mb4096_a | 275,796 | -0.12% | 913 | 597 | 316 | 46 |
| mb32768 | 267,621 | -3.08% | 926 | 416 | 510 | 32 |
| mb4096_b | 276,436 | +0.12% | 911 | 597 | 314 | 45 |

## Best known 15M/512 combination: minibatch 8192 + fused Muon


**** — controls 247,308, 247,038 (drift -0.11%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| mb8192_a | 247,308 | +0.05% | 1039 | 958 | 80 | 70 |
| mb8192_fused64_a | 245,835 | -0.54% | 1044 | 948 | 96 | 70 |
| mb8192_fused64_b | 247,170 | -0.00% | 1038 | 950 | 88 | 70 |
| mb8192_b | 247,038 | -0.05% | 1040 | 963 | 77 | 71 |

## Parked engine patches in the collection-bound full pipeline (controls = PGO retained; see non-PGO control below)


**5m2048** — controls 216,000, 216,074 (drift +0.03%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| full_a | 216,000 | -0.02% | 1148 | 514 | 634 | 41 |
| liquid | 207,826 | -3.80% | 1193 | 512 | 680 | 41 |
| immutable | 207,657 | -3.88% | 1193 | 513 | 680 | 41 |
| full_b | 216,074 | +0.02% | 1147 | 515 | 632 | 41 |

**15m2048** — controls 210,160, 209,271 (drift -0.42%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| full_a | 210,160 | +0.21% | 1218 | 1031 | 188 | 79 |
| liquid | 203,187 | -3.11% | 1257 | 1028 | 229 | 79 |
| immutable | 202,513 | -3.43% | 1261 | 1029 | 232 | 79 |
| full_b | 209,271 | -0.21% | 1223 | 1033 | 191 | 79 |

## Non-PGO retained engine control (fair baseline for ordinary-LTO candidates; PGO itself = +4.9%)


**5m2048** — controls 205,775, 205,260 (drift -0.25%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| nonpgo_a | 205,775 | +0.13% | 1203 | 515 | 688 | 41 |
| nonpgo_b | 205,260 | -0.13% | 1206 | 514 | 692 | 41 |

**15m2048** — controls 197,868, 200,976 (drift +1.57%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| nonpgo_a | 197,868 | -0.78% | 1289 | 1026 | 263 | 79 |
| nonpgo_b | 200,976 | +0.78% | 1271 | 1028 | 243 | 79 |

## Candidate A: incremental glyph export (engine incexport2) and incremental packer (trainer incpack_v38), vs non-PGO retained


**5m2048** — controls 207,070, 206,674 (drift -0.19%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| ctrl_a | 207,070 | +0.10% | 1197 | 512 | 685 | 41 |
| incexport | 214,335 | +3.61% | 1158 | 514 | 644 | 41 |
| incpack | 215,780 | +4.31% | 1149 | 514 | 635 | 41 |
| ctrl_b | 206,674 | -0.10% | 1199 | 513 | 685 | 41 |

**15m2048** — controls 201,645, 201,769 (drift +0.06%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| ctrl_a | 201,645 | -0.03% | 1265 | 1027 | 238 | 79 |
| incexport | 208,716 | +3.47% | 1226 | 1030 | 196 | 79 |
| incpack | 210,753 | +4.48% | 1214 | 1033 | 181 | 80 |
| ctrl_b | 201,769 | +0.03% | 1265 | 1030 | 235 | 79 |

**15m512** — controls 228,240, 227,963 (drift -0.12%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| ctrl_a | 228,240 | +0.06% | 1134 | 1134 | 0 | 139 |
| incexport | 228,390 | +0.13% | 1133 | 1133 | 0 | 170 |
| incpack | 228,359 | +0.11% | 1133 | 1133 | 0 | 179 |
| ctrl_b | 227,963 | -0.06% | 1135 | 1135 | 0 | 150 |

## Stacked candidate: incstack engine (incremental export + liquid + immutable), with and without the packer trainer, vs non-PGO retained


**5m2048** — controls 207,039, 207,447 (drift +0.20%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| ctrl_a | 207,039 | -0.10% | 1197 | 512 | 684 | 41 |
| stack_engine | 218,609 | +5.48% | 1135 | 514 | 622 | 41 |
| stack_packer | 219,942 | +6.13% | 1129 | 514 | 615 | 41 |
| ctrl_b | 207,447 | +0.10% | 1196 | 513 | 682 | 41 |

**15m2048** — controls 202,311, 201,678 (drift -0.31%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| ctrl_a | 202,311 | +0.16% | 1262 | 1027 | 235 | 79 |
| stack_engine | 212,128 | +5.02% | 1207 | 1034 | 173 | 79 |
| stack_packer | 214,236 | +6.06% | 1196 | 1035 | 161 | 80 |
| ctrl_b | 201,678 | -0.16% | 1266 | 1031 | 235 | 79 |

## LANDING comparison: retained PGO engine + v37 trainer (current full stack) vs incstack PGO engine + incpack_v38 trainer


**5m2048** — controls 216,402, 216,550 (drift +0.07%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| ctrl_a | 216,402 | -0.03% | 1147 | 514 | 633 | 41 |
| landing | 230,259 | +6.37% | 1078 | 515 | 564 | 41 |
| landing_b | 230,536 | +6.49% | 1078 | 516 | 561 | 41 |
| ctrl_b | 216,550 | +0.03% | 1145 | 515 | 631 | 41 |

**15m2048** — controls 210,961, 210,965 (drift +0.00%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| ctrl_a | 210,961 | -0.00% | 1214 | 1031 | 183 | 79 |
| landing | 223,282 | +5.84% | 1151 | 1038 | 113 | 80 |
| landing_b | 222,684 | +5.56% | 1153 | 1039 | 114 | 80 |
| ctrl_b | 210,965 | +0.00% | 1214 | 1034 | 179 | 79 |

**15m512** — controls 228,195, 228,060 (drift -0.06%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| ctrl_a | 228,195 | +0.03% | 1134 | 1134 | 0 | 226 |
| landing | 228,585 | +0.20% | 1132 | 1132 | 0 | 269 |
| landing_b | 228,501 | +0.16% | 1133 | 1133 | 0 | 268 |
| ctrl_b | 228,060 | -0.03% | 1135 | 1135 | 0 | 223 |

## LANDING (final, fixed export): retained PGO + v37 vs incstack2 PGO + incpack_v38 — all gates clean


**5m2048** — controls 216,594, 216,514 (drift -0.04%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| ctrl_a | 216,594 | +0.02% | 1146 | 513 | 633 | 41 |
| landing | 230,989 | +6.67% | 1076 | 516 | 560 | 41 |
| landing_b | 230,779 | +6.57% | 1077 | 516 | 562 | 41 |
| ctrl_b | 216,514 | -0.02% | 1146 | 515 | 630 | 41 |

**15m2048** — controls 211,002, 211,378 (drift +0.18%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| ctrl_a | 211,002 | -0.09% | 1213 | 1032 | 181 | 79 |
| landing | 223,618 | +5.88% | 1149 | 1038 | 111 | 79 |
| landing_b | 223,156 | +5.67% | 1151 | 1039 | 113 | 79 |
| ctrl_b | 211,378 | +0.09% | 1212 | 1034 | 178 | 79 |

**15m512** — controls 228,137, 228,112 (drift -0.01%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| ctrl_a | 228,137 | +0.01% | 1134 | 1134 | 0 | 223 |
| landing | 228,663 | +0.24% | 1132 | 1132 | 0 | 273 |
| landing_b | 228,431 | +0.13% | 1133 | 1133 | 0 | 268 |
| ctrl_b | 228,112 | -0.01% | 1135 | 1135 | 0 | 224 |

## Worker pinning (PUF_CPU_AFFINITY=2, one worker per logical CPU) in the full pipeline, incpack_v39 vs incpack_v38, both on incstack2 PGO


**5m2048** — controls 231,590, 231,819 (drift +0.10%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| ctrl_a | 231,590 | -0.05% | 1074 | 515 | 559 | 41 |
| pin_a | 233,626 | +0.83% | 1065 | 516 | 548 | 41 |
| pin_b | 233,283 | +0.68% | 1067 | 517 | 550 | 41 |
| ctrl_b | 231,819 | +0.05% | 1073 | 516 | 557 | 41 |

**15m2048** — controls 224,710, 224,732 (drift +0.01%)

| Arm | SPS | vs control | epoch ms | PPO est ms | rollout tail | PPO tail |
|---|---:|---:|---:|---:|---:|---:|
| ctrl_a | 224,710 | -0.00% | 1144 | 1038 | 107 | 79 |
| pin_a | 225,502 | +0.35% | 1140 | 1040 | 101 | 79 |
| pin_b | 225,666 | +0.42% | 1139 | 1040 | 99 | 80 |
| ctrl_b | 224,732 | +0.00% | 1144 | 1041 | 103 | 80 |
