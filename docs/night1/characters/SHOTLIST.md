# CHARACTERS SHOTLIST, first-pass piece G (hero skins)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.
> Scope since 2026-10-01 (director PLAN-firstpass.md, piece G): the HERO only; thugs / fight / crowd are paused. The older fight / crowd / lineup shots are in `HANDOFF.md` (rounds 05 - 10).

Round 17: the same shots, files in `round-17/`; every STILL and LINEUP is taken by the settle protocol (`-WHSettleFrames=32`: the director freezes the stage clock, every animation, the lane walkers and the camera, waits for 0 compiling assets / shaders and every visible texture resident, counts 32+ static rendered frames, then takes the shot); movies run `-WHPreload`. The pawn map's side shot lasts 16 s and the crowd tracking shot 12 s (the r16 'yaw snap' at 9.933 s and the 7.483 s crowd cut were director shot ends). New files: `VERDANT_BEFORE_AFTER.jpg` (the Verdant re-block, r16 | r17), `evidence/lineup_cause.json` (the corruption-cause measurement), `evidence/measures/lineup/` (diff maps, weapon crops).

Round 16: the same shots, files in `round-16/`; EVERY still is committed at 4K now (the backs too); the `headfront` portrait follows the head bone (`WHShot.bHeadLock`: camera in the head's midsagittal plane); the stills run quits 3 s after its last stage shot (`-WHStageShotQuit`); the stage-hero / fight / crowd clips were not re-shot (round-15 files, content unchanged).

Round 15: the same shots, files in `round-15/`; the base colours are 8192 px, so the first still waits 12 s of stage time (`P2_FIRST_EXTRA=9`, `first_extra` in `skins_shots.json`), and the pawn (`pawn_run.json`) spawns on the ground (z 0.95); the pawn movie is trimmed by 0.1 s (camera-binding frames).

Every shot below is the REAL game (UE 5.8.3, `-game`, offscreen) through `gpu_slot.sh`, driven by `tools/ue_char/suits/chain_r11.sh`. Map `Char_Skins` = plain floor, key sun + four fills on the hero only;
`Char_SkinsPlay` = the same stage with the PLAYABLE pawn (`WebTravGameMode`, `AWebTravCharacter` wearing `/Game/Characters/Hero/SK_Hero` and the P2 hero clips). The suit is switched with the game's own code
(`UWHHeroSuitSubsystem`: director shots call `SetSuit` = `wh.Suit n`; the pawn movie injects real T key presses into the player controller).

| id | what | map / director shots | how | file (round-11/) |
|---|---|---|---|---|
| S1 | every suit, front, full body | `Char_Skins` shots 0, 4, 8 ... (suit i, view `front`), camera 5.6 m, FOV 40, aim 0.92 m | 4K real-time stills (`r.ScreenPercentage 100`, internal 3840x2160), stage-clock screenshot 2.2 s into the shot | `stills/skin_<suit>_front_4k.jpg` |
| S2 | every suit, back | views `back` (camera behind) | same | `stills/skin_<suit>_back_4k.jpg` |
| S3 | every suit, chest close-up (glyph, net, sash, stitching) | view `chest`, 1.5 m, FOV 30 (0.45 m of chest over 2160 px = 4800 px/m against 2330 texels/m) | same | `stills/skin_<suit>_chest_4k.jpg` |
| S4 | every suit, head close-up (round 13: the sculpted mask) | view `head`: 12 deg off the face axis, 1.0 m, FOV 26, aim 164 | same | `stills/skin_<suit>_head_4k.jpg` |
| S4b | every suit, head in the ROUND-12 framing (25 deg, 1.0 m, aim 160): the lens-width comparison against r12 | view `head34` | same | `stills/skin_<suit>_head34_4k.jpg` |
| S4c | every suit, head PROFILE (the nose bump against the head height) | view `headside`: 90 deg off the face axis, 1.25 m, aim 166.5 (whole head in frame) | same | `stills/skin_<suit>_headside_4k.jpg` |
| S4d | every suit, head straight on (round 14: the cheek-line luma test of the critic's "front stills"; also the best view of the brow shelf / cheek planes) | view `headfront`: 0 deg off the face axis (CLOSEUP azimuth -25), 1.0 m, FOV 26, aim 164 | same | `stills/skin_<suit>_headfront_4k.jpg` |
| E1 | the 7-enemy lineup (round 13: the grey hood is back, -0.6 EV, weaker fill) | `Char_Lineup` shots 5 (wide) and 6 (3/4) | 4K real-time stills at 3.0 s | `enemy_lineup_4k.jpg`, `enemy_lineup_34_4k.jpg` |
| S5 | swatch sheet of all suits (front + back + chest) | composed from S1 - S3 | `tools/ue_char/suits/swatch_sheet.py` | `SWATCH_SHEET.jpg` |
| S6 | the playable hero cycling through all suits with the T key | `Char_SkinsPlay` pawn shot 0 (side tracking, 10 s) | 1080p `-movie` (fixed 1/60 s), 7 injected T presses at 1.5, 2.7 ... 8.7 s | `swap_pawn_T_key.mp4` |
| S7 | persistence: a second launch starts in the suit the first one ended in | `Char_SkinsPlay` | 960x540 still at 3 s, `-WHSuitPersist` | `persist_start.jpg`, `evidence/persist_*` |
| S8 | the stage hero in every suit, one continuous orbit, swap every 1.5 s | `Char_Skins` orbit shots (index 32 ...) | 1080p `-movie` | `orbit_all_suits.mp4` |
| M1 | swap latency, in the engine log and on the pixels of S6 | log lines `WH_SUIT set / swap_done`, `analyze_swap.py` | | `evidence/swap_latency.json` |

CPU-side checks (no engine): `suit_seams.py` (UV seams, spec CH18), `ip_guard.py palette` (colour blocking + structural uniqueness) and `ip_guard.py ocr` (OCR of the atlases and of every 4K still),
`swatch_cpu.py` (design-aid renders). Numbers: `round-11/SPEC_CHECK.md`.
