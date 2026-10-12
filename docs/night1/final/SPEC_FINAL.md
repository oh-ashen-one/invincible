# Final refinement spec: swing, air, flips, web deployment (orchestrator, 2026-10-08)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Standing targets carried over (still apply, do not regress): `docs/night1/traversal/SPEC.md` (swing T-lines),
`docs/night1/traversal/FLIPS_SPEC.md` (F1-F12, measured from the owner clip), `docs/night1/traversal/TRICK_CAMERA_SPEC.md`.
Owner reference for aerobatics: `~/sm2-n1/_scratch/refs/owner/flips_owner_2026-09-29.mov` (= the owner's 2026-09-29 screen recording).
Reference library: `~/spiderman-learnings/refs/traversal/clips/` (local only, never committed).

Critics score against these lines, may add gaps they observe, and may not contradict a line unless they measure that the reference
violates it. Each line needs a checker the builder runs on every round's telemetry/frames (`tools/final/swing/`).

## W: web deployment and appearance (new; the owner's "awkward swing press" complaint)
| Id | Line | Target |
|---|---|---|
| W1 | Origin | On every frame a strand is drawn, its start is within 8 cm of the firing hand's palm (hand bone + palm offset), including the press frame, attach frame and release frame. Never from the hips/chest/root or a stale position. |
| W2 | Firing arm | The firing arm starts moving toward the anchor ≤ 0.05 s after the press; by the time the strand tip arrives the shoulder→wrist direction is within 20° of shoulder→anchor; it stays within 30° for the whole swing (elbow eased, no hyper-extension, no arm through the head/torso). |
| W3 | Shot travel | The strand tip travels hand→anchor visibly over 0.06-0.20 s (speed 150-400 m/s, scaled by distance); it never appears full length in one frame; swing tension starts when the tip lands, not before. |
| W4 | Attach transition | No pose pop at attach: chest angular rate ≤ 400°/s on ≥ 90 % of attaches and never > 700°/s; hand speed in the attach frame ≤ 2.5x the previous frame. The body leads into the swing (hips swing under the anchor) within 0.15-0.35 s. |
| W5 | Readability | Strand 2-4 px wide at 1080p for 5-60 m from the lens, visible on ≥ 95 % of web-on frames against sky, facades and night; slight taper toward the anchor; no flicker or segment gaps. |
| W6 | Shape | In flight the strand shows a slight travelling wave/curvature that straightens within 0.10 s of the tip landing; under tension it is a straight line hand→anchor. |
| W7 | Clearance | Hand→anchor line clear of building geometry and tree canopies on 100 % of web-on frames (no strand through walls or crowns). |
| W8 | Release | On release the strand leaves the hand and goes slack/retracts over 0.15-0.40 s; it never vanishes in one frame or stays attached to the hand. |
| W9 | Hand choice | The firing hand matches the anchor side (anchor right of the travel line → right hand) on ≥ 90 % of attaches; consecutive swings alternate where the anchors alternate. |
| W10 | Every press resolves | Every swing press either fires a visible web within 0.05 s or plays a readable "no anchor" reach (arm out, no strand) — never a press with no visible response, an instant teleport-attach, or a strand to an anchor behind the hero. |

## A: swing body and airborne motion
| Id | Line | Target |
|---|---|---|
| A1 | Swing phases | Within one swing the body reads drop-in → bottom (legs tucked/driven under) → upswing (legs extend forward) → release; legs lag the arc by 0.05-0.15 s; pose signature changes ≥ 0.15 between 0.3 s samples during a swing. |
| A2 | Variety | Consecutive swings differ (style per web: at least 3 distinct swing body styles in any 6 consecutive swings), no identical swing loop. |
| A3 | Release | Release pops with forward/upward momentum; the body opens within 0.1 s of release; no frozen pose. |
| A4 | Float / air | No held identical air pose > 0.6 s (r26 T4); falling/float poses evolve (arms/legs move, silhouette changes every 0.1 s sample) and blend into the next attach without pops. |
| A5 | Catch out of a trick | The trick's last 0.3 s blends toward the next rope (arm already reaching toward the anchor), catch ≤ 0.25 s after the last shape (F8), chest rate ≤ 400°/s through the catch on ≥ 90 % of catches (r01 measured 16/21 catches > 400°/s, peak 1894°/s). |
| A6 | End-pose variety | Across 6 tricks at least 3 visibly different end/catch poses (not all the same Reach). |
| A7 | Flip shapes | Pike and pencil read tight (pike hip angle ≤ 60°, pencil body straight within 15°); triple chains are not macroblocked mush (each shape readable ≥ 3 frames at 25 fps). |

## Shot list (fixed for every round; spawn/inputs in `docs/night1/final/swing/SHOTLIST.md`, written in round 00)
Real `-game`, map `/Game/Showcase/Maps/Manhattan_Island` (golden) unless noted, playable profile with the Fast preset
(`-WHProfile=playable -WHResScale=100 -WHPerfPreset=<repo>/unreal/WebHomage/Config/PerfPlayableFast.cvars`), output 1920x1080,
internal 1920x1080 (100 %), TSR, fixed 1/60 s `-benchmark -fps=60 -dumpmovie`, 1.5 s pre-roll cut, original suit (Tessera).
Clips: `s1_swing_chain`, `s2_press_variety` (the awkward-press cases), `s3_flip_chain` (F with forward/back/side/neutral stick),
`s4_release_float` (releases with no trick, long airtime), `s5_night_swing` (s1 inputs on `Manhattan_Island_Night`).
Each clip: mp4 + per-frame telemetry CSV (existing columns + W/A checker columns: strand start, tip, hand bone, firing hand, anchor,
chest angular rate).
