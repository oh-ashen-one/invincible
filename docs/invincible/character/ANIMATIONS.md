# Hero animation ledger

**Owner practice (2026-10-15): before keying ANY pose/animation, search the web for reference/inspiration of what it should look like (comic covers, pose references, animation breakdowns), note the takeaways, and match the owner's reference images.**

Rig: CustomUse/Cartwheel 52-bone biped on the v2 hero (`customuse/v2/rigged_hunyuanTex.glb`). Review: local viewer `tools/invincible/viewer/`.

| Clip | Source | Status | File | Notes |
|---|---|---|---|---|
| Hover idle (`HERO_hover_keyed`) | hand-keyed, `tools/invincible/hover_keyed.py` | **CONFIRMED by owner 2026-10-15** (commit a6e7d27d) | `meshy/hero_hover_keyed.glb` | 4 s seamless loop: helicopter bob (2 s), lagging limbs, torso sway, breathing back; show-reference posture |
| Superman flight (`HERO_fly_keyed`) | hand-keyed, `tools/invincible/fly_keyed.py` | in review | `meshy/hero_fly_keyed.glb` | owner refs: Invincible covers -- both fists straight up/forward overhead, legs together pointed; authored upright (game pitches body-up onto the fly line) |
| Meshy starter library (20 clips) | Meshy presets, retargeted | reviewed "looks good", not locked | `meshy/hero_meshy_clips.glb` | landings, slams, punches, kicks, idles |
| Meshy hover takes A/B/C | Meshy text-to-motion | rejected (hips forward) | `meshy/hero_hover.glb` | kept for reference |

Next: superman-line fly, Shift boost (coil -> launch -> stretch), brake, slam dive, double-tap superhero landing.
