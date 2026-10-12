# Round 15 design aids (CPU, not part of the build)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation.

Scripts I used to design the r15 head and net changes without an engine hold (they hard-code the scratch paths of the Studio, `/Users/midir/sm2-n1/_scratch/characters/r15/...`; edit the paths first):

- `cpu_rim2.py`: `measure(glb, yaw, pitch)` = a perspective id-render of the head GLB (mask / rim / glass) at the profile camera (1.25 m, FOV 26, aim 1.665) with the head pitched about (0, 1.60, -0.02): brow x, rim front x, glass front x in px. The real stills match pitch -7 / yaw -88 (rim +13 / glass -18 px against the real +14 / -18).
- `cpu_fit.py`: fits pitch / yaw / shifts by matching the front silhouette of a REAL headside still against the model (r14 Verdant: pitch -6, yaw -84, rms 2.9 px).
- `exp_r15.py`: `build(params, lens)` = prepped GLB -> `hero_head_r14.main` -> `hero_lens_r14.main` in 1 s, `evaluate(glb)` = T1 / T2 / T2b + the rim offsets at four poses. Needs `$P2_SCRATCH/r15/work/SK_Hero_prepped.glb` (= `prep_glbs.py` output).
- `stretch_probe.py`: surface-area stretch of the sculpt per face triangle (sqrt of the area ratio sculpted / refined flat).
- `dbg_layer.py <suit> <layer>`: dead-end blobs of one net layer of one suit with the cord mask in green (`net_end_check_r15.py` gives the totals).
- `cpu_view.py <maps dir> <suit> <armpitR|chest|front|back> <out.png>`: rest-pose CPU render of a map set (`swatch_cpu.py`'s renderer).
