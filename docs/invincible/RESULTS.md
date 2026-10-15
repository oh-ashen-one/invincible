# Invincible flight conversion — results

Owner request 2026-10-15 (Hari): replace Spider-Man / web-swinging in the UE 5.8 WebHomage project with a flying hero in the style of Mark Grayson ("Invincible" comic homage, no cape). Unofficial, non-commercial homage; see `DISCLAIMER.md` and `LICENSE` (the original author attribution to Shikhar / xikhar stands).

## Status after the overnight loop (2026-10-15, 00:30-06:00 ET, Mac Studio M3 Ultra, UE 5.8)

**Independent critic verdict: FAILS TARGET** (round 1 lowest axis 2/10, round 2 lowest axis 2/10). The flight controller, suite and
hero mesh work and are measurably better than at the start of the night, but the look of destruction, the sonic boom, the flight
silhouette and the rescue presentation are not at the reference bar. No owner gameplay acceptance is claimed. Fixed-step capture
footage is **not** real-time FPS evidence; no real-time performance was measured this night.

| Item | State |
|---|---|
| Flight controller (takeoff, hover, fly, boost + sonic boom, bank, climb/dive, brake, dash, slow flight, slam, landings) | compiled, captured, mechanically gated (17-case suite) |
| Through-building breach | works; camera holds on the impact and cuts to the exit; **looks fake** (proxy cubes, sprite dust), critic top defect |
| Rescue (crane) | fl17: caught, carried down, set down on a roof, touchdown; **presentation weak** (hero stands on the load, load out of frame in the dive) |
| Hero mesh | `SK_Invincible` (Blender fallback: yellow/blue/black zones with clean seams, dark hair cap, yellow goggles, no cape) imported and used by default in flight mode; face is feature-light (mask sculpt base) |
| Capture suite + gates | `tools/invincible/` + `docs/invincible/captures/PLAN.md`; pixel gates (occlusion, luma, frozen) added after critic r1 |
| Omni-Man boss, authored fracture/decal/audio, customuse character | not done |

## Rounds

| Round | Build | Render | Mechanical / pixel gates | Critic |
|---|---|---|---|---|
| r1 | `7acea119` | 17 cases, 1080p fixed 60 | 17/17 on the first gates; **11/17** once the r1-critic pixel gates were added | FAILS TARGET; silhouette 3, suit 5, camera 2, speed 3, FX 2, glitches 2 (`captures/r1/CRITIC.md`) |
| r2 | `ca3caa22` | 17 cases | **15/17** (fl14 hidden 49 frames before its breach, fl17 hidden 40 frames: the carried load occludes him) | FAILS TARGET; silhouette 3, suit 5, camera 3, speed 3, FX 2, glitches 2 (`captures/r2/CRITIC.md`) |
| r2b | `45580f5c` | fl01, fl02, fl04, fl14, fl15 | 4/5 (fl14 11 hidden frames) | not reviewed (targeted replay of the r2 sheet fixes) |
| r3 | source of `04832f78` (built before that commit; RUN.json shows head 45580f5c + dirty) | fl01, fl03, fl04, fl13, fl14 | 4/5 (fl14 9 hidden frames); fl13 touchdown contact 10 -> ~5 m/s; hero larger in frame | not reviewed (final targeted replay; the r2 critic's other findings still stand) |

## What the night fixed (each from a sim, a sheet or the critic, each re-captured)

- Hands-off flight dived 51 m in 9 s (the fly aim was the camera's hero-framing look-down); the fly line now keeps its own pitch, moved only by vertical look input. fl03 holds 60.0 -> 60.0 m.
- Hover descents breached down through the street (box-index solid without render collision at Times Square); breaches are now horizontal only, never exit under the street, time-bounded (0.3 s) and slow flight cannot tunnel.
- Flying head-on into a facade pinned him motionless; fly held now punches through after 0.3 s. Sliding along a wall froze him (the sweep grazed the wall it rested 2 cm from) while speed read 19 m/s; he now stands 5 cm clear and the push-out removes the velocity it pushes against (fl10 / fl16 frozen frames 285 / 293 -> 0 in sim).
- Every swept landing sank him 0.5 m into the street (sweep-sphere contact height) and he dropped into a hover; fixed (fl11 lands grounded).
- Breach camera followed him into the solid (black frames); it now holds on the impact and cuts behind him once a chase spot is clear, keeping the player's heading; one slow-mo beat per burst at the cut. Breach scar plates (flat black discs) removed.
- Flying hero rested in the spider crouch (and the pre-roll frame 0 showed it / the bind pose); upright idle now. Hover arms softened.
- Sonic boom had no visual; vapour-puff collars ahead of the line + flash (still weak, see open defects). HUD scaled 1.45x.
- Shots moved out of the cluttered Times Square spot (TKTS steps, billboards and crowd hid the hero) onto open 5th Av; fl17 restarts facing the open plaza.
- Times Square spawn was 0.6 m in the air (the flying hero hovered at spawn); body now on the plaza floor.
- Hover descent eases out over the last 4 m (was a 10 m/s stop in one frame); flight chase camera closer, smaller FOV add.

Clips in the repo are 960x540 review copies (`<case>_540p.mp4`; the critics judged the full-res `<case>.mp4`, kept only in the disposable
cache `~/sm2-invincible-cache/<tag>/full/`); telemetry is gzipped.

## Open defects (critic r2 top 8, verbatim themes; acceptance tests in `captures/r2/CRITIC.md`)

1. Breaches look fake: flat discs (removed after r2), see-through sprite smoke, light card-like cube debris. Needs a real fracture asset (`/Game/Invincible/Destruction/GC_FacadeChunk` is already loaded when present) and facade-textured debris.
2. fl14 after the breach: the exit lands him in a courtyard at low speed; critic wants > 40 m/s after the exit and no dark frames.
3. In flight the hero reads as a "blue egg" from behind (glutes dominate, head/arms hidden): needs a higher/side chase angle in flight and a mesh with better proportions (customuse path).
4. Sonic boom still barely visible (needs a vapour-cone mesh/material, not dust puffs).
5. Slam/landing impact: crater is a flat decal, debris cubes.
6. Rescue presentation: hero stands on the load instead of holding it; load out of frame in the carry dive; one accidental breach on the route.
7. Clipping through fire escapes / glass (fl16, fl17).
8. Gentle touchdowns stopped from 10 m/s (eased after r2, r3 replay) and clip-start crouch pop (fixed in r2b).

Also: in sim15 (final build) fl17 shows 74 hidden frames by projection during the carry dive (the closer chase camera vs the carried load) -- re-check fl17 in a render before trusting the closer camera there.
Also: telemetry `hero_bbox_h` overstates the hero's size ~1.8x vs pixel count (critic r2); every rendered run logs a pre-existing engine ensure `OriginX <= OriginMax` at frame 0 (also in the pre-change smoke log; reported, not gated).
