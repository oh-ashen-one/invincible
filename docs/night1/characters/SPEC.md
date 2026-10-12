# CHARACTERS-SPEC (P2 hero, suits, enemies, civilians, character animation) — fixed targets, measured from refs

> Homage fan game; not affiliated with Marvel, Sony or Insomniac. Refs private; the hero suit must not copy a studio-owned suit design
> (owner decision pending, director plan §5.1).
> Written 2026-09-29 by spec agent B. Instruments: `specs/tools/count_people_vehicles.py` (YOLO11x people/vehicles),
> `ref_hero_dets.py` (person masks). Heights are bbox height / frame height. "Unmeasurable from refs" = no number set from refs.
> Characters rounds fix **2 gaps per round** (enemy art + civilian locomotion touch different files).

## 1. Hero on screen and texel density (CH-A)
| id | target | measured from |
|---|---|---|
| CH1 | Ground third-person framing: hero height **0.48–0.62** of frame | YOLO: hero-idle-street-og .57, hero-idle-crosswalk-night .57, hero-rooftop-miles .59, hero-run-street-dn .48, press-duo-closeup .53 |
| CH2 | Run chase framing: hero height median **0.39–0.53** | run-crosswalk clip .488, run-toward-camera .389, walk-park-path .531 (YOLO, every 2nd frame) |
| CH3 | Suit texel density **≥ 680 texels/m** (≥ 340 at 1080p) so the CH1 view is not under-sampled at 4K | hero-idle-street-og: .57 × 2160 = 1231 px over ≈ 1.8 m → 684 screen px/m (derived) |
| CH4 | Closeup suit read (weave scale, raised web lines, lens rim/curvature/specular) | **unmeasurable as a number from refs**; judged side-by-side with press-suit-closeup-fire, suits-duo-closeup, miles-face-closeup at native 4K |
| CH5 | Captures that claim 4K are rendered at 3840×2160 internal for closeups (r02 found 1080p upscaled) | rule |
Checker `hero_px_check.py`: hero pixel mask on the lineup/turntable captures → CH1/CH2 heights; material texel density from UV area / mesh area.

## 2. Locomotion (CH-B)
| id | target | measured from |
|---|---|---|
| CH6 | Run step rate **3.2–3.8 steps/s**; jog ≈ 2.6 steps/s | dominant frequency of hero bbox-height oscillation (vertical bob = 1 per step): run-crosswalk 3.27 Hz, run-toward-camera 3.79 Hz, walk-park-path (jog) 2.58 Hz |
| CH7 | Sprint torso lean (hip→neck from vertical) **≥ 15°**; ref sprint frame shows ≈ 30° ± 5° | run-beside-traffic-dn__dn_0242 side view, hip ≈ (1830,1460) → neck ≈ (2060,1100) in 4K px = 33° (one frame, hand-read on a gridded crop) |
| CH8 | Arm swing amplitude | **unmeasurable from refs** (no clean side-on run cycle clip); critic may cite run-crosswalk 1.5–3.6 s qualitatively |
| CH9 | Foot slide during plant | **unmeasurable from refs numerically** (leg crops of run-crosswalk 2.2–3.6 s at 30 fps show planted feet). Engineering limit: ≤ 3 cm foot-bone drift per plant, from telemetry |
| CH10 | No pose pops: any locomotion state change blends ≥ 0.15 s; no T-pose frame | rule (T-pose = 0 frames) |
Checker `loco_check.py` (telemetry): step rate from foot-contact events, spine lean vs vertical per frame, foot drift per plant, blend times.

## 3. Enemies (CH-C)
| id | target | measured from |
|---|---|---|
| CH11 | Group fight: **5–7 enemies in frame** at ≥ 3 % height (people incl. hero: median 6–8) | combat clips, YOLO 2 fps: street-combo med 7 (max 9), street-fight-cars med 8 (max 13), plaza-fight med 6 |
| CH12 | Enemy screen height in fights **0.16–0.60** | combat stills: car-fight .23–.28, combo-hit .16–.48, fire-fight .26–.53, thugs-close .29–.56 |
| CH13 | Variety: in a 7-thug frame **≥ 5 distinct outfit silhouettes** (masks, caps, tank tops, vests, jackets) and **≥ 2 weapon types** | hand-read thugs-close-nm__nm_0947 (7 thugs ≥ 15 % height; pistol + bat) and thugs-group-nm__nm_0049 (crowbar, vest, balaclava) |
| CH14 | Modelled eyes/faces, five-finger hands, cloth folds, real shoes (r02) | judged side-by-side with thugs-close-nm, thug-closeup-dn |
| CH15 | Brute bulk vs thug | **not in refs** (no brute ref). r02's "≥ 1.3× shoulder width" is a design choice, owned by P2, not a ref line |
Checker `enemy_lineup_check.py`: lineup capture with ≥ 7 enemies; YOLO count + per-mesh unique material set count; texture seam test (CH18).

## 4. Civilians (CH-D)
| id | target | measured from |
|---|---|---|
| CH16 | Sidewalk density at street level: **people per frame 8–25** (median ≈ 16–25 on busy sidewalks) | street-life-pedestrians med 25 (22 at ≥ 3 % height), timessquare-plaza-walk 16, centralpark-path-walk 17, street-npcs-idle 8 |
| CH17 | Everyone walking moves legs (0 gliding/frozen walkers); ≥ 6 distinct civilian models in one frame; no identical twins in frame | rule from refs (all walkers in street-life-pedestrians animate); twin count unmeasurable automatically → hand check |
| CH18 | Zero seam cracks/sparkle pixels on character meshes at native 4K | rule (r01/r02 defects) |
| CH19 | Gait phases not in lockstep | unmeasured in refs; engineering: pairwise gait-phase difference spread ≥ 0.2 cycle across ≥ 6 walkers |
Checker `crowd_check.py`: YOLO count on our street capture + telemetry per walker (root speed > 0.3 m/s ⇒ foot-bone speed > 0; gait phase).

## 5. P2 dependency owed to P3 traversal (tracked here, not scored against P3)
The browser clip set lacks: wall-run cycle (alternating hands/feet), landing tiers (light / roll / three-point), sprint with lean, run start/stop,
trick library beyond releaseFlip/tuck, perch idle with breathing. P2 delivers these clips (retargeted to the hero skeleton) or states which are
out of scope; P3's T-E axis caps attributable to them are logged in `docs/night1/traversal/HANDOFF.md` with this section as the reason.

## 6. Axis → spec lines
| axis | lines |
|---|---|
| CH-A Hero model & suit | CH1, CH3, CH4, CH5 |
| CH-B Hero animation | CH6, CH7, CH9, CH10 (+ §5 clips) |
| CH-C Enemies | CH11–CH14 |
| CH-D Civilians | CH16, CH17, CH19 |
| CH-E Image quality | CH5, CH18 |
Critic rules: score against these lines; ADD observed gaps with file@time; contradict a line only by running the named tool on the ref.
