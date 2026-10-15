# Hero animation ledger

Rig: CustomUse/Cartwheel 52-bone biped on the v2 hero (`customuse/v2/rigged_hunyuanTex.glb`). Review: local viewer `tools/invincible/viewer/`.

| Clip | Source | Status | File | Notes |
|---|---|---|---|---|
| Hover idle (`HERO_hover_keyed`) | hand-keyed, `tools/invincible/hover_keyed.py` | **CONFIRMED by owner 2026-10-15** (commit a6e7d27d) | `meshy/hero_hover_keyed.glb` | 4 s seamless loop: helicopter bob (2 s), lagging limbs, torso sway, breathing back; show-reference posture |
| Meshy starter library (20 clips) | Meshy presets, retargeted | reviewed "looks good", not locked | `meshy/hero_meshy_clips.glb` | landings, slams, punches, kicks, idles |
| Meshy hover takes A/B/C | Meshy text-to-motion | rejected (hips forward) | `meshy/hero_hover.glb` | kept for reference |

Next: superman-line fly, Shift boost (coil -> launch -> stretch), brake, slam dive, double-tap superhero landing.
