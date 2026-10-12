# r05 lawn-shadow diagnostics (1080p native stills, offscreen, through the GPU lock)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Question: why no tree shadow reads on the lawn (r04 critic). Runs (`diag*.sh`, frames in `_scratch/terrain/r05/diag*`):
- r04 content, V_p4: default vs `ShowFlag.DynamicShadows 0` (`cmp_shadow.jpg`): the crowns brighten without shadows, the open lawn does not change (luma ratio 0.93-1.0 except a few spots).
  `r.DynamicGlobalIlluminationMethod 0` had no effect at runtime; `ShowFlag.DirectLighting 0` / `r.Lumen.DiffuseIndirect.Allow 0` drew the default material (shader permutations not compiled), not usable.
- VB_p4 (the city alone, its own flat park land, `cmp_vb.jpg` left) shows long tree / building shadows on the flat land; V_p4 with VSM and with `r.Shadow.Virtual.Enable 0` (CSM, right) shows none on our lawn.
- p10 with CSM (`p10_csm.jpg`): the lamp post 10 m from the camera has no shadow and no sunlit side; the crowns 60-200 m north have sunlit tops.
- r05 test 2 (sun-facing turf normal, `t2_p4_crop.jpg`): the stone block top-centre has a sunlit top and a short dark wedge on the lawn beside it (the lawn receives shadows); the hatched strip
  across the Great Lawn is also in the city-only baseline VB_p4 (a city ground feature, not lighting). Under the golden rig's 9 deg sun (az 238) a crown 8-15 m up casts its shadow 50-95 m
  east-north-east of its trunk, stretched ~6x, so a tree's shadow does not touch the tree in the aerial views. Whether parts of the lawn sit in the West Side skyline's shadow could not be
  checked offline (the midtown collision / hinterland exports do not cover the park's west side).
- Measures taken: the turf normal bends toward the sun (`Lawn.ush lwTurfNormal`, the sun-facing blades of a low-sun lawn), material AO / albedo gain tried and set back to 1 (no visible effect
  beyond the auto exposure), the leaf cards use a fixed coverage threshold in the shadow pass.
- Every engine launch auto-starts UnrealTraceServer (listening on 1981 / 1989) unless `-notraceserver` is passed; r05 launches pass it from 04:05 on (the firewall already permits the binary; no dialog was raised).
- diag5 (R5b content, 1080p V_p4): `r.MegaLights.EnableForProject 0, r.MegaLights.Allowed 0` vs default: mean abs difference 0.23 luma (no change, `cmp_mega.jpg`);
  `r.Shadow.Virtual.NonNanite.IncludeInCoarsePages 1, ...UseRadiusThreshold 0, r.Shadow.RadiusThreshold 0`: 0.27 (no change). Neither MegaLights nor the non-Nanite VSM culling thresholds explain it.
- In the 4K p4 stills the sunlit strip across the east side of the Great Lawn carries crisp thin shadow lines (trunks / lamp posts) and no crown shadow; the R5b build's hidden
  shadow-only crown proxies (built for the conifers only in that build, `diff_5b.jpg`) changed nothing on the lawn either. Still open: whether the leaf-card materials write anything
  in the shadow-depth pass at all (next test: a debug map with one cards pool on an opaque two-sided material, and one big cube on the lawn).
