> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

# Morning acceptance pass — Night 1 → Day 2 (Fable 5.1 max, 2026-10-01 07:40 EDT)

Evidence read: `HANDOFF.md`, `progress.json`, `model-ledger.json` (50 rounds), `PLAN-night2.md`, every piece branch's latest critic (traversal r15–r18, characters r8–r10, perf r5–r6, city r9–r10, life r2–r3, combat r3–r4, look r2–r3), the piece HANDOFFs (characters r11, perf r7, look r4 WIP), the 07:22 headless rebuild log, the S4 guard re-run by me on the rebuilt frame, and the rebuilt hero / S4 stills themselves. No engine was launched for this pass.

## 1. Merge rulings (rule: no axis below the merged round; a round without its blind critic is not a candidate)

| Piece | In the build | Scores (blind Opus 5.5 critic) | Previous merged | Builder | Verdict |
|---|---|---|---|---|---|
| P3 Traversal + flips | **r18** (`cdc7ae9`) | swing 7 · camera 6 · web 6 · moves 6 · body 6 · **flips 7** | r15 [7,5,6,6,6,7] | Opus 5.5 high | FAILS target (lowest 6) — merge confirmed |
| P1 City | **r10** (`ad93a86`) | [5,5,5,5,5] | r9 [5,5,4,5,5] | Sonnet 5.5 xhigh | FAILS (5) — merge confirmed, guard below |
| P6 City life | **r3** (`d87a224`) | [5,5,6,4,4] | r2 [5,5,5,4,4] | Sonnet 5.5 xhigh | FAILS (4) — merge confirmed |
| P5 Combat | **r4** (`b2a3636`) | [6,5,5,4,4] | r3 [5,5,5,4,4] | Opus 5.5 high | FAILS (4) — merge confirmed |
| P4 Look | **r3** (`9a0cafe`) | [6,4,4,4,5,5] | r2 [4,4,4,4,5,5] | Sonnet 5.5 xhigh | FAILS (4) — merge confirmed |
| P2 Characters | **r8** (held at r8) | [5,5,5,5,5] | — | Sonnet 5.5 xhigh | FAILS (5) |
| F 4K/60 perf | **r5 preset** (`perf60` + TSR 50 %) | validity 8 · shipped 7 · life 3 · visual 4 · margin 4 | r4 | Opus 5.5 high | APPROACHES — ships as the only preset with a critic pass on the empty-street line |
| Water | Opus A/B winner | [4,5,5,1,4] (3.8 vs Sonnet 3.4) | — | Opus 5.5 high | FAILS vs reference |

**Not mergeable, confirmed strict:**
- Traversal r17 [7,6,6,6,6,6]: superseded by r18 (flips 6 → 7); its commits are ancestors of r18 and are already in the build — nothing to do.
- Characters r9 [5,5,6,5,**4**] and r10 [5,5,6,5,**4**]: image quality 5 → 4 (hood hair seam ~570 px, beard flat card 125×220 px, collar wedge at 4K). The fight choreography in r10 (2 knockdowns, 6 reactions) is real progress but it cannot ride in with an axis regression. Characters r11 is WIP on the branch with no critic. Held.
- Perf r6 [8,**3**,5,7,**3**]: shipped-numbers 7 → 3 (life-on p95 53–54.5 fps) and an undisclosed S2/S7 foliage loss that the critic voided. Perf r7 has no critic (chain stopped at the 02:02 reset). Held; the r5 preset ships.
- Look r4: WIP commits only (instruments, sweeps), no critic. Held.

**No reverts.** City r10 guard on the rebuilt S4 frame (`tools/export/s4_far_check.py`, re-run by me): T2 0.8 % > 204 (PASS, ≤10); T1 18.6 px by the gradient method (PASS, ≥12) — the two threshold methods read 0.0 because under look r3's golden haze no far pixel is below Y 215 or below sky−12, so they measure nothing, not a flat silhouette; C11, C14, C15 pass; **C12 dBR +12.8 (limit ±10) and C13 far−sky −7.4 Y (spec 15–32) FAIL**. Those two lines are far-band luma/tint, which PLAN-night2 §3d assigns to the look piece (aerial perspective), not to city (albedo + silhouette). Visual check of the frame: varied far-shore towers, piers, bridges, a readable silhouette — faint, but a real skyline. City stays; the −7 Y band is the first look r4 line (below).

Hero in the rebuilt `/Game/Maps/Manhattan`: log `WH_TRAV hero suit: ORIGINAL (MI_Hero_Suit, slot SpiderSuit)`; the still shows the teal/orange Tessera suit with its own hexagon emblem, pedestrians on both sidewalks, traffic in both directions. The combat hero (`AWHCombatHero : AWebTravCharacter`) inherits the same forcing, but it has not been captured on `Combat_Street` since the merge: the orchestrator must grep the Combat_Street game log for the same `ORIGINAL` line before the owner opens that map (the r4 critic saw a copied emblem in the combat branch's own clip, which predates the forcing).

Build: all steps rc 0 at 07:22 (`morning_build.sh`: build_manhattan with the new `city_extra` step, water, life, add_life into Manhattan / _Midday / _Night, combat map, `COMBAT_STREET_OK actors=191`). The 48 "error" lines in the hero check log are Unreal's own UnifiedErrorTest self-tests and the EditorToolset Python plugin init; none is ours.

## 2. What to try in the playable build

Launch (orchestrator, when you say so): standalone `-game -windowed -ResX=1920 -ResY=1080`, map `/Game/Maps/Manhattan` (golden hour). Console is the tilde key (`~`); Escape releases the mouse, left-click recaptures it. Mouse sensitivity: `wh.MouseSensitivity 0.5` (default 1.0; lowered 3× since your showcase note).

Maps (type in the console): `open /Game/Maps/Manhattan` (golden) · `open /Game/Maps/Manhattan_Midday` (overcast) · `open /Game/Maps/Manhattan_Night` · `open /Game/Tests/Combat/Combat_Street` (the combat test street; combat is not in the city map yet).

Controls (keyboard / gamepad):
- Move WASD or arrows (left stick) · look mouse (right stick) · **Shift** sprint (R2 on the ground)
- **Right mouse (hold)** web swing (R2) · **Space** jump, and at the top of a swing: release (A)
- **F** trick / flip (X) — hold it as you release at the apex, or tap it in the air; tap again mid-air to chain a second trick
- **E** or middle mouse: zip to point (Y) · **C** or Ctrl: drop / dive (B) · **Q** quick action (LB)
- Combat (Combat_Street only): **left mouse** attack, **E** / middle mouse web-strike, **F** web, **Q** finisher, **R** throw, **C** / Ctrl dodge, **Z** heal (gamepad X attack, B dodge)

Try, in this order:
1. **Gymnast flips, golden hour.** From the PlayerStart on the avenue: hold RMB, let the swing climb, press Space near the top with F held. Sky-backed apex flips (the r16–r18 work): a layout, a straddle, a pike and a tuck with limbs that keep moving (0 frozen samples in r18). Press F again at the top of the next swing to chain. Release above the roofline (longer first swing) so the flip is against sky, not facades. Known: every program is the same replay (identical rate curves, fixed 1.57 / 1.40 / 1.48 s) and the tuck is loose — that is the r19 target.
2. **Perch and skyline.** Zip (E) up a river-side tower and look across: the new far-shore band (varied towers, piers, bridges) under golden haze, then `open /Game/Maps/Manhattan_Night` for the same spot (lamp pools and wet asphalt are the look piece's best element; the skyline is still day-for-night) and `Manhattan_Midday` (overcast — flat sky, crisp shadows that should not be there).
3. **Combat.** `open /Game/Tests/Combat/Combat_Street`: LMB combo, E web-strike, Q finisher, C dodge. r4's additive impact bursts keep the victim readable and every blow moves him; the knockdowns travel 3–7 m. Expect the known faults: backlit opening, hero too small in frame, hero blown-out white in the first seconds, flat untextured street.
4. **Street level.** Walk a block: crowds on both sidewalks, cars queuing at the lights and leaving on green, storefront signs (all invented brands). Watch the feet — they slide (r4 target).
5. **Wall-run.** Sprint into a facade: the climb cycle and top-out; the run itself is still a crawl (r19 secondary).

Performance disclosure: the shipped preset renders 4K output at TSR 50 % (1920×1080 internal). Measured at 4K on the scripted route (perf r5, exclusive GPU): empty-street p50 63.8 / p95 56.3 fps; with traffic + crowd p50 58.4 / p95 51 fps — the playable city does **not** hold 60 at 4K with life on. The 1920×1080 window you will open has not been measured; it should sit well above that, but no number is claimed.

## 3. Known weaknesses per piece (from the critics, not self-assessment)

- **Traversal (r18, 7/6/6/6/6/7).** Tricks are canned replays (identical flip-rate curves across instances, fixed durations); loose tuck (knees apart, arms out); wall-run is a crawl (c 2.3–3.6 s); web visible 53 % of the swing clip (limit 45 %); swing low points dip into tree canopies and the camera does not count foliage as occlusion (TC-G); TC-C hero-height p90 .370 on f3. Reference won 5 of 6 blind pairs.
- **City (r10, 5×5).** S8 glass 70 % blown (unchanged three rounds); far-shore towers are untextured two-tone extrusions with no windows (25 % flat 8×8 blocks); S6 red steps a pink glow (sat 0.30 vs ≥0.44); S6 curb 14.7 % clipped; S3 white untextured roof props; cars toy-like with blank plates; S2 traffic 25 (limit 22). In the integrated map the far band sits only 7 Y below the sky.
- **City life (r3, 5/5/6/4/4).** Feet slide (stance foot 47–54 cm/s, ~40 % of walk speed), ankle lift 31 cm, all gait periods 1.00–1.10 s (lockstep look); legs clip through coats; a group walks mid-roadway; a haze column down the road centre (asphalt luma 183 vs 100–131); bus rear a hollow smeared box; untextured white plaza; candy-saturated outfits, pink twins, one hi-vis look ×4; cars 30 px at swing height vs 47 px in the reference.
- **Combat (r4, 6/5/5/4/4).** Opening backlit (20.5 % dark pixels) with a blown-out white hero (40–57k near-white pixels); hero median 27 % of frame height (ref ~40 %); a 29.2 snap at 15.3 s; the burst is one shape, shuts off without decay, hides the victim for 10 frames at 14.32; light blows move the victim 43–60 px on a 310 px body; finisher victim static for 24 frames; brute never flinches; flat untextured street, no environment hits, no blur. Reference won 11 of 11.
- **Look (r3, 6/4/4/4/5/5).** Golden shadows lifted and flat (p5 Y 17.6–39.6 vs refs 8–11; p95/p5 4.6–11 vs 18–26), no sun/shade split on S1/S5/S6; far band fails L10 at every time of day; glass is a flat fill that reflects nothing; midday S2 tower glows gold; overcast has crisp cast shadows and a purple far field; clipping on S3/S7; night skyline day-for-night (median Y 58 vs ref 37, window points 0.96 % vs 4.4 %); Times Square screens are gradient placeholders; neon-green trees under lamps; no motion blur while swinging (L18).
- **Characters (r8 in the build, 5×5).** Hero head an unsculpted egg (no brow/nose); hero showcase too large in frame (CH1); run is a treadmill loop with no start/stop/turn/idle; the build's street fight is r8's: thugs idle in guard, 0 reactions, 0 knockdowns (r10's fixed fight is on the branch, held by IQ 4); tee-mask see-through holes (198 px), thug collar skin wedge; civilian coats rigid, swing knee at 0.15–0.2 stature; crowd 10 vs 16–25 on busy streets.
- **Perf (r5 preset).** Life-on line fails (above); S1 canopy crop SSIM 0.93 vs the 0.97 gate; recess light leak +71 % (fixed in r6, which is not shipped); r6's p95 work cost S2/S7 foliage without disclosure; r7 found the slow life frames are the GPU-heavy windows (probe gather 3.6 vs 3.0 ms), not a CPU/GPU sync.
- **Water (3.8).** Ring artifact, no fine ripples or sun glints, too bright (C14), lacks the piling foam the Sonnet build had.

Incident: **02:02** — WindowServer reset with only 2 engines running (GPU pinned ~2 min, WS main thread stuck in a Metal submit), the desktop session restarted and the orchestrating session died at 02:05; the loop sat idle until 06:37; no work lost (WIP pushed 06:40); engine cap is now **1** with an automatic starvation governor.

## 4. Night-2 targets per piece, one GPU renderer (serial)

Cap 1 means every capture, build commandlet and perf session queues on one slot (7–26 min per hold last night). Builders do CPU work off-slot (Blender, choreography, pose curves, Nanite settings, CSV analysis) and queue only a finished pack. Pixels-only critics need no GPU. Budget: ~8 h ≈ one round per piece at 45–60 GPU-minutes each; traversal gets a second round if time remains, life is dropped first.

GPU order (and why): **1 traversal → 2 combat → 3 look → 4 characters → 5 city → 6 life → 7 perf.** Owner value first, short 1080p captures before long chains, the far-band fix (look) before the city re-captures its S4 so the two owners stop moving the same pixels, and perf **last and exclusive** because its numbers only mean something on the night's final content and it needs the GPU alone (`gpu_procs.py`: any other GPU user, including the MLX model, voids the run).

| # | Piece | Model | Round target (merge bar = the critic's tests, no axis below the merged round) |
|---|---|---|---|
| 1 | Traversal r19 | **Opus 5.5 high** | Per-instance variation: scale each program's duration and peak rate ±10–20 % from release speed and apex height, vary arm timing; tight tuck (wrists ≤0.15 m from shins, knees ≤0.25 m apart, held ≥0.25 s, logged in telemetry). Tests: same-type tricks differ ≥40°/s in ≥1 rate sample; tuck numbers pass on f1/f5; `pose.py` 0 slow samples stays a gate; TC-A..K frozen (no camera edits). Secondary: hero_occl counts leaves (T7 canopy), web ≤45 %, wall-run sprint stride. Bar: flips ≥7 kept, camera ≥6, nothing below r18. |
| 2 | Combat r5 | **Opus 5.5 high** | Combat camera + lighting: hero ≥35 % frame height at contacts; opening ≤15 % px < gray 30 and not backlit; ≤2 % hero pixels V≥250/S<60 outside bursts; no 60 fps diff >25 except deliberate cuts; finisher close-up cut ≥1 s at 0.3×; burst decays over frames 6–10 and varies by blow; light blow moves the victim ≥25 % body height in 0.3 s. First: confirm `WH_TRAV hero suit: ORIGINAL` in the Combat_Street log. Bar: camera ≥5, impact ≥6. |
| 3 | Look r4 | **Opus 5.5 high** (already launched on Opus; keep) | Owns far-band luma: golden S4 far band 15–32 Y below the sky, B−R within ±10 (fixes the integrated C13 −7.4 / C12 +12.8), same on midday S4. Golden key/fill: p5 Y ≤12, p95/p5 ≥16, mean saturation ≥0.44 with L1 held; sun/shade facade pair ratio ≥3 on S1/S5/S6. Night S4: window points ≥3 %, median Y ≤42. City must not touch `FarGain` or far luma. Bar: GI & shadows ≥5, atmosphere ≥5, nothing below r3. |
| 4 | Characters r11 | **Sonnet 5.5 xhigh** (asset work; the r10 fight is kept as is) | One hair asset per head in Blender, no patch cards: at 4K no colour seam >40 px, no detached card ≥20 px, no background between hair and skin, no skin blob ≥15×15 px in the thug collar (move the nape strip into the hood collar or shade it to the hood's hue). Builder runs the critic's 4K crop checks before packing. Bar: IQ ≥5 with enemies ≥6 → r9/r10's fight finally reaches the build. Secondary: enemies spread 2–4 m, no guard >2 s. |
| 5 | City r11 | **Sonnet 5.5 xhigh** | S4 far-LOD facades with a window grid, crown/setback variation, albedo 0.25–0.35 (≤10 % flat bright 8×8 blocks; T1/C11/C14/C15 still pass); S8 glass ≤1.5 % >204 (stuck at 70 % for three rounds — treat as the real gap); S6 curb ≤1.5 %, red steps sat ≥0.44 V ≤200; texture the S3 roof props; S2 traffic ≤22. No far-band luma edits. Bar: skyline ≥6, nothing below 5. |
| 6 | Life r4 | **Sonnet 5.5 xhigh** (dropped first if the queue is behind) | Plant the feet: stance ankle speed median ≤10 cm/s (match stride length × cadence to move speed per walker; scale play-rate from the clip's root speed), ankle lift ≤20 cm, gait periods spread ≥0.25 s. Secondary: kill the road-centre haze column, crowd mix (no look >2× in 30 m, no twins, desaturated outfits), closed LOD0 bus/van rears, nobody in the roadway. Scored at the traversal camera as is. Bar: ped motion ≥5. |
| 7 | Perf r7 (finish) | **Opus 5.5 high**, exclusive, last | Precondition: `look_gate.py` PASS (S2 tree line via Nanite error 6 + preserve-area already passes; S1 canopy / S7 reflected tree must be restored before any number is recorded). Then 3/3 life-on runs with CSV p95 ≤18.0 ms and top-5 % FT−GPU gap ≤1.2 ms; the r7 finding says the slow windows are GPU-heavy (probe gather), so the lever is per-window probe/content cost, not a sync hunt. If it does not pass, r5 stays and HANDOFF states the internal resolution. Bar: shipped-numbers ≥7 with no undisclosed look loss. |

Oscillations reconciled (one directive each, unchanged from PLAN-night2 §3 where still true): traversal fixes pose curves only, TC lines frozen; look owns the far band's luma, city its albedo and silhouette; perf records no number until the look gate passes; characters authors hair as one asset and pre-checks the 4K crops; life does not touch the camera; combat is monotonic, keep going. Critics: fresh blind Opus 5.5 high every round, never skipped. No Fable builds.

Standing safety: every launch through `gpu_slot.sh`, cap 1 until the owner raises it, `stop_ue.sh` only (SIGTERM first), no listeners, orchestrator in `tmux`.
