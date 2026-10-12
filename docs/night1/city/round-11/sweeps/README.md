# r11 sweeps (plan files for tools/export/r11_plan.sh and the S4 scores of each hold)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

`plan*.txt` = the plan files run inside one `gpu_slot.sh capture` hold each; `scores_h*.txt` = `s4_score.py` JSON per S4 frame of that hold (tag, map id, JSON: T1, T2_pct, T4_bright / T4_all, sky / far / river Y, C13-C15).
h1 = baseline of the r10 code on the fresh export (T2 29.57 %, as r10) and the first r11 build with S4 atmosphere variants f1-f3; h3 = FarLitK 0.45 and fog 0.003 variants; h4 = FarFill 0.12 / 0.24; h5 = fog start-distance variants (i1-i4);
h6 = the final S4 configuration. Hold 8 (grazing-angle glass check, S8 0.72 %) and the S8 F0Scale sweep (g1-g4, 70.4 -> 43.6 -> 6.8 -> 3.1 -> 3.0 % above 204) have no score files (the S8 numbers are in `README.md`). Frames of the sweeps are not committed.
