# P5 Combat: shot list (r04)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Map `/Game/Tests/Combat/Combat_Street` (procedural test street, dusk), the real game (`-game`, offscreen), scripted hero (`scripts/fight30.json`, frozen from the
reactive record run `fight30_record.json`), 60 fps fixed step, output 1920x1080 for the movie and 3840x2160 for stills, both with `r.ScreenPercentage 100` (native internal
resolution; r04 passes it explicitly for the movie too and logs `WH_CMB_RES` = output size, r.ScreenPercentage and the internal size: `round-04/ue/render_res.txt`).

| id | what | how | matching reference |
|---|---|---|---|
| M1 | 32 s fight, 9 + 13 enemies, 3 launchers + air juggles, 2 finishers, web shots / strike / pin, dodges | `run_fight.sh movie` (1080p60 `-dumpmovie`), mp4 <= 15 MB | `street-combo__nm_0214-0224`, `street-fight-cars__nm_0500-0510`, `plaza-fight__dn_0818-0828`, `night-street-fight__nt_0755-0805` |
| S1 | group ring with telegraphs (hero + 5-7 enemies, mid-high camera) | 4K still at a ring moment | `group-fight-nm__nm_0223` |
| S2 | contact frames (hit-stop, r04 starburst on the victim): light @1.87, ender @2.66, launcher @7.01, slam @8.22, finisher @15.65, ender @22.14 | 4K stills 0.04 s after the contact | `combo-hit-nm__nm_0217` |
| S3 | launcher / air juggle | 4K still while the victim is airborne | `air-combat-nm__nm_0248` |
| S4 | web strike / web shot line | 4K still with a strand out | `web-shooter-nm__nm_0244` |
| S5 | finisher beat (push-in) | 4K still at the cine peak | `symbiote-finisher__nm_0530-0538` (clip) |
| S6 | gunman aim line + brute silhouette | 4K stills | `street-fight-nm__nm_0501` |
| M2 | measurement rerun: the same fight with `-WHCmbFlare=0` (no starburst); abs(A - B) is exactly the flare | `run_fight.sh movie` with `WHCMB_EXTRA=-WHCmbFlare=0` (not published) | - |
| X1 | previous round vs this round | r03 `round-03/fight30_1080p60.mp4` vs r04 `round-04/fight30_1080p60.mp4`, and the same instant @15.65 (disc vs starburst) | - |
