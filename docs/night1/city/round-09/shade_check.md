# shade_check (tools/export/shade_check.py) — round 09

Critic r08 test formulas on the 1920x1080 frames; r08 for comparison: S1 crops 22.5 / 19.7, S3 72.2 %, S7 62.5 % (`round-08` frames, same script).

```
Test 1 (S1 crops mean Y >= 52):
  S1 left crop   (0, 0, 480, 300)  meanY   66.6  share<25   0.7%  PASS
  S1 right crop  (1360, 0, 1740, 400)  meanY   53.8  share<25   3.1%  PASS
Test 2 (share of Y<25, whole frame):
  S3_rooftop_watertower     19.7%  (limit 25.0%)  frame meanY 53.6  PASS
  S7_sunset_crosstown        3.6%  (limit 30.0%)  frame meanY 62.8  PASS
All frames (share Y<25 / share Y>204 / mean Y):
  S1_avenue_street_1920x1080.jpg           3.9%   2.52%    74.2
  S2_avenue_swing_1920x1080.jpg            3.2%   1.83%    88.8
  S3_rooftop_watertower_1920x1080.jpg     19.7%   0.02%    53.6
  S4_perch_skyline_1920x1080.jpg           0.8%  22.42%   154.7
  S5_timessq_south_1920x1080.jpg           9.0%   6.33%    80.4
  S6_timessq_street_1920x1080.jpg          3.4%   5.63%    83.2
  S7_sunset_crosstown_1920x1080.jpg        3.6%   1.11%    62.8
  S8_aerial_midtown_1920x1080.jpg          8.0%  11.67%   100.4
```
