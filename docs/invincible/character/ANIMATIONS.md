# Hero animation ledger

**Owner practice (2026-10-15): before keying ANY pose/animation, search the web for reference/inspiration of what it should look like (comic covers, pose references, animation breakdowns), note the takeaways, and match the owner's reference images.**

Rig: CustomUse/Cartwheel 52-bone biped on the v2 hero (`customuse/v2/rigged_hunyuanTex.glb`). Review: local viewer `tools/invincible/viewer/`.

| Clip | Source | Status | File | Notes |
|---|---|---|---|---|
| Hover idle (`HERO_hover_keyed`) | hand-keyed, `tools/invincible/hover_keyed.py` | **CONFIRMED by owner 2026-10-15** (commit a6e7d27d) | `meshy/hero_hover_keyed.glb` | 4 s seamless loop: helicopter bob (2 s), lagging limbs, torso sway, breathing back; show-reference posture |
| Superman flight (`HERO_fly_keyed`) | hand-keyed, `tools/invincible/fly_keyed.py` | **CONFIRMED by owner 2026-10-15** (commit e9768df1) | `meshy/hero_fly_keyed.glb` | owner: flying straight ahead = horizontal in the clip (body on the fly line, belly down, fists leading). Unreal integration must NOT pitch the body again |
| Launch straight up (`HERO_launch_up`) | `fly_keyed.py --vertical` | base for the takeoff (owner: the upright version is the launch) | `meshy/hero_launch_up.glb` | needs the crouch + jump-off from the ground before it |
| Shift boost (`HERO_boost_full` review; `_coil` 0.42 s, `_launch` 0.2 s, `_hold` 2 s loop) | hand-keyed (procedural pose blending), `tools/invincible/boost_keyed.py` | **rejected by owner** (robotic) | `meshy/hero_boost.glb` | owner: elbows to the knees, knees to the stomach, charge, then straight-in sonic boom at double speed; refs: anticipation = spring coil + tremble, overshoot release |
| Shift boost v2 (`HERO_motion_boost_a/b/c`) | Meshy text-to-motion (prime), retargeted | in review (B = best coil; D broken, dropped from the viewer list) | `meshy/hero_boost_meshy.glb` | launches come out diving forward-down (mocap); can be levelled onto the flight line |
| Meshy starter library (20 clips) | Meshy presets, retargeted | reviewed "looks good", not locked | `meshy/hero_meshy_clips.glb` | landings, slams, punches, kicks, idles |
| Meshy hover takes A/B/C | Meshy text-to-motion | rejected (hips forward) | `meshy/hero_hover.glb` | kept for reference |

Next: Shift boost (coil -> launch -> stretch), brake, slam dive, double-tap superhero landing.
