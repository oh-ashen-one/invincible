# Round 05 (builder SW)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Answers critic r04's three gaps (trick rotations/holds, camera occlusion, stiff swing poses). Build commit `d5198769`. Same maps / profile / settings as round 04 (`-WHSuit=tessera`, playable + Fast, 1920x1080, fixed 1/60 s, 1.5 s pre-roll cut).

## Code changes (all in owned paths)

- `WebTravFlips.cpp` — `backDouble`/`frontDouble` are now tuck → held pencil/throne (0.36 s) → tuck → kickout → reach (720 deg); `backTripleChain` (1080 deg) gained the owner-clip's mid-chain inverted pencil; `backLayout`/`fullTwist` gained short tuck entry/exit phases (their peaks were ~400/300 deg/s). The front/back stick pools lead with the doubles/triples, so a long release opens with a 2-3 rotation program (the air-fit test still falls back to singles in short air).
- `WebTraversalComponent.cpp/.h` — (a) the trick's final reach now also holds WITHOUT the swing button held (`FlipReachIdle` 0.8 s; the button-held `FlipReachHold` 0.2 s unchanged as the larger of the two): a scripted catch pressed after the program's end lands out of the held reach instead of a dead-glide gap. (b) hang cap: a swing stalled under `HangStallSpd` 5 m/s near the bottom for `HangCapS` 1.5 s releases and the held button re-fires (auto-continue).
- `WebTravCharacter.cpp` — the catch's residual flip rotation decays rate-limited (<= 340 deg/s) when <= 70 deg from the body frame instead of the 0.07 s snap; mid-program cancels keep the snap.
- `WebTravCamera.cpp/.h` — (a) visibility watchdog for the chase camera (swing/air/zip, never during the trick camera): while the hero's chest is out of the frustum or the lens->chest line is blocked, `VisBoostK` ramps over 0.15 s and relaxes the output slew caps (x4), adds chase distance (+35 %) and a lift; eases off when he is seen. (b) closed-loop chase distance from the projected hero bone box (`ChaseFbK` 0.75-1.45, targets 0.26 swing / 0.30 air) — the r04 note's pose-extent problem, via distance (FOV pinned by T14). (c) trick-camera feedback clamp widened 0.6-1.7 -> 0.5-1.9.
- `Anim/WebTravAnimInstance.cpp/.h` — swing-life leg targets (thigh/knee) sample a 24-entry phase ring 0.09 s behind the live arc phase (torso/free arm stay live); knee-drive bump at the bottom 0.75 -> 0.95; swing-leg shaping weight 0.65 -> 0.78, free-arm IK weight 0.55-0.8 -> 0.7-0.92.
- `tools/final/swing/make_scripts.py` + `docs/night1/traversal/scripts/final/s3_c*.json` — s3b case program picks retuned for the reordered pools (FlipKStart: c1 frontSingle, c2 backSingle, c3 corkscrew, c4 barani, c5 frontPikeSwan, c6 rudi, c7 fullTwist; all catch windows land by the fixed 2.0 s press). Keys / spawn / timing unchanged.
- `tools/final/swing/run_clip.py` — per-case admission retry (120 s waits, 8 attempts) with a per-case resume cache (`frames_done/`), and a coordinator FIFO-queue fallback (`tools/gpu/gpu_slot.sh capture`, the M1 commandlet path) when the resident-holder path (`with_holder.sh` -> `play.py`) cannot admit within 180 s; PAUSED and foreign-engine checks replicated from play.py; an engine that started but produced no frames is never auto-relaunched.

## Environment notes

- The post-restore workspace lacked the gitignored generated include `Shaders/Terrain/ParkData.ush`; restored bit-identical from the M5 backup (md5 74a41fef…, matches the m2 checkpoint copy) — check.py `missing: []` afterwards.
- Both GPU slots were held by foreign sessions all round (a parked `ark-mashup-editor` holder + a continuous Markhor check stream). The `with_holder.sh` path never admitted (it waits for zero holders / the m5-flash resident); every case ran through the coordinator's FIFO queue instead (wait 0-645 s per case). No PAUSED, no foreign UnrealEditor/Blender/Unity process at any launch.

## Measured (CHECK.txt for the full tables; flip_check = docs/night1/traversal/flip_check.py)

Gap 1 (tricks): s3 opens with frontDouble — rendered 2.20 rotations over 1.90 s (F2 mean 416 deg/s); the chain's tricks: frontDouble, frontPikeSwan, barani, frontSingle, backLayout, rudi, corkscrew (+wallFront top-out). s3b cases show fast tucks (flip_check peaks 556-715 deg/s on 6/7) and held open shapes 0.36-1.41 s. Catch delay after the last shape: median 0.00 s on s3 (8/8 <= 0.25) and s3b (7/7), vs r04's 0.70 s median on s3b. s3 flow web-on share 46 % (r04 ~38 %).

Gap 2 (camera): s1/s5 have ZERO frames with hero_occl > 0.5 (r04: hero fully occluded ~2.6 s at t 9.2-11.7, 26 no-pixel mask samples). Remaining: one 0.58 s stretch (t 9.42-9.98) plus three 0.07-0.12 s ones where the strict whole-padded-bone-box-in-frustum flag is 0 during the fast dive — the hero mask shows 65-84k px and occl 0.00 throughout (visible, box edge outside the frame). P1 (pixel hero height, >= 90 % in band): s1 swing 89 % / air 90 % (r04: 88/84, and 0 no-pixel samples vs 26); s3b 68/71 (r04: 54/46); s3 86/64; s2 81/63; s4 swing/air 81/62-ish — still below 90 % on most clips.

Gap 3 (poses): s1/s5 A1 still pass (92-100 % pairs >= 0.15); s2 has no < 5 m/s swing stretch over 0.5 s at all (r04's 4 s micro-rocking region now accelerates away); the hang cap never fired in any clip (no stall reached 1.5 s).

## Regressions / not reached (measured, vs round-04 CHECK)

- A5 chest-rate clause still fails: the lead-in turn onto the rope between the press and the attach runs 400-700 deg/s on the chest bone (median 520 s3b / 623 s3; catch-delay clause passes everywhere now). flip_check F8's "body <= 30 deg from upright at the catch" fails on 5/7 s3b cases (32-84 deg — the catch happens already turned toward the rope).
- flip_check rendered peaks exceed 800 deg/s on frontDouble (958), backLayout (1105) and frontPikeSwan (925) in s3 — the rendered axis adds the keyed shape-transition lean on top of the program rate. F4 hold just under 0.3 s on frontDouble's throne (0.29). F11 leg lag at shape changes 0.067-0.158 s (target 0.05-0.12).
- Small-sample flips vs r04: s3b W3 6/7 shots (was 7/7), s3b A1 83 % of 6 pairs (was 100 % of 6), s4 W3 7/8 (was 6/6), s4 A1 87 % (was 91 %), s4 W4 now passes (was FAIL). s2 A3 now passes (was 8/9).
- W5 by day unchanged in character: s1 24 % judged frames (r04: 33 %; strand median width 2.0-2.5 px; the chase distance sits slightly further out). Night (s5) passes 100 %.
- W2 on s1/s5 (12/13 swings within 30 deg), W7, s2's W3/W4/W9/W10 case failures: unchanged, not addressed this round.
- s3b t~22 hero size and the straight-down roof frame (r04 secondary): the trick-camera feedback clamp was widened (0.5-1.9); not separately measured this round.
- s1 t~6.5 strand faintness (r04 secondary): not addressed.
