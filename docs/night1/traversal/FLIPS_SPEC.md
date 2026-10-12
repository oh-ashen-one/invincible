# Flips spec (P3 round 11), measured from the owner reference clip

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.

**Source:** the owner's screen recording `_scratch/refs/owner/flips_owner_2026-09-29.mov` (24.3 s, 610×556, 50 fps; footage of the
real game, local only, never committed). **Method:** frames extracted at 10 fps (whole clip) and 25 fps (flip segments), each
frame timestamped; the body axis (hips → head) angle θ was read by hand per frame against the frame vertical (0° = head up,
180° = inverted). Rotation rates are Δθ/Δt between readings, so they carry roughly ±15° per reading (±40 °/s at 25 fps).
Segment notes below give the reading each number came from. The camera does not roll with the body in the clip, so θ in the frame
is close to the world angle. Where the view is foreshortened, the reading is marked "est.".

## Measured segments (owner clip time)

| Seg | Time (s) | What happens | Readings |
|---|---|---|---|
| S1 | 0.80–2.44 | Swing release → 180° in ~0.12 s (0.88 upright arms-up → 0.96–1.04 inverted) → tuck ball 1.08–1.16 → brief wall touch 1.2–1.6 → **horizontal layout held 1.72–2.04 (0.32 s, θ≈90, <100 °/s)** → tuck forming 2.08–2.16 → upright 2.24 → **web-catch arm up at 2.40–2.44** | catch comes 0.2 s out of the tuck, body within ~20° of upright |
| S2 | 4.60–5.96 | Edge vault: crouch / tuck over the roof edge 4.60–4.96 (θ 90→170) → **inverted pencil held ON the web 5.00–5.64 (0.64 s, θ 170–180)** → unwinds 180→0 while swinging down 5.64–5.96 (~600 °/s peak) | web stays attached through the pencil |
| S3 | 8.32–11.36 | Wall-run along the facade to 8.44 → off the wall into **three rotations in 2.8 s** over a roof: tuck 8.48–8.60 → spread layout ~90° 8.64–8.96 (≈150 °/s) → inverted 9.00–9.08 → upright spread **9.36–9.48** → inverted pencil **9.72–9.84** → tuck 9.88–10.00 → upright 10.08 → inverted straddle **10.40–10.56** → inverted crouch 10.6–10.8 → tuck → upright spread 11.28–11.36 | rotation 1: 0.88 s, rotation 2: 0.72 s, rotation 3: ~1.1 s; tuck phases 9.84→10.08: ~180° in 0.24–0.3 s (600–750 °/s) |
| S5 | 14.9–15.5 | Release → tuck ball 15.0–15.4 near a facade → catch | short (web-to-web) flip ~0.5 s |
| S6 | 21.32–23.80 | On the web inverted tuck 21.3–21.7 → pike, rope still on to ~22.08 → release → **inverted pencil 22.12–22.48 (0.36 s, 180±15)** → straddle 22.52–22.64 → unwinds 165→10° over 22.64–22.96 (~500 °/s peak) → **upright "throne" spread held 23.00–23.48 (0.48 s, 0–5°)** → pitches forward 23.52–23.72 (0→130°, ~650 °/s) into the next facade | hero 0.18–0.30 of frame height, against open sky, camera below and level, looking up |

## Numeric targets (what a round is measured against)

| Id | Line | Target (from the owner clip) |
|---|---|---|
| F1 | Rotations per release | 0.5–1 on a short web-to-web release; **2–3 per long release** (S3: 3 in 2.8 s; S6: 1 + the forward pitch) |
| F2 | Mean rotation rate over a multi-flip release | 300–500 °/s (S3: 1080° / 2.8 s = 385 °/s) |
| F3 | Peak rate (tuck / pike phases) | 450–750 °/s; never above 800 °/s; no constant-rate spin (critic r10 on ours: ~900 °/s uniform) |
| F4 | Held open shapes | At least one shape per trick held **≥ 0.3 s at ≤ 150 °/s** (pencil 0.36–0.64 s, throne 0.48 s, layout 0.32 s); the r10 critic asked ≥ 0.6 s for one hold |
| F5 | Easing | Peak / slowest rate inside one rotation ≥ 3 (the rate follows the shape: fast in the tuck, near-hold in the open shape) |
| F6 | Shape vocabulary | Tuck, pike, horizontal layout, inverted pencil, straddle / split, upright throne spread, swan / spread-eagle; each readable for ≥ 3 frames at 25 fps (0.12 s) |
| F7 | Corkscrew | Twist about the long axis while the body is tilted 60–110° from vertical (S3 8.7–8.9: ~180° twist in ~0.3 s while near horizontal); target ≥ 180° twist in 0.3–0.6 s |
| F8 | Continuity into the catch | Web catch ≤ 0.25 s after the last shape, out of a tuck / reach with the body ≤ 30° from upright (S1 2.24→2.44), or on the web from inverted, unwinding ≤ 0.35 s (S2) |
| F9 | Camera | No roll with the body (roll ≤ 5°); hero **0.18–0.36 of frame height** during tricks; camera level with or below the hero, looking up (sky behind the hero in most trick frames); the rotation plane seen from the side or 3/4 (not end-on from behind) |
| F10 | Timing | The trick starts ≤ 0.1 s after the release (S1: 0.08 s); off a wall-run the first rotation starts as the feet leave the wall (S3 8.44 → 8.48) |
| F11 | Overlap | Limbs do not switch shape on the same frame: arms lead, legs follow ~0.05–0.1 s (S3 9.36: arms open before the legs extend) — target: legs lag the arms by 0.05–0.12 s at shape changes |
| F12 | Wall-run into flip / edge vault | Present in the clip (S3, S2); a round shows the wall-run flip in the lit city |

## How ours is measured (round 11 on)
`docs/night1/traversal/flip_check.py <telemetry.csv> <label>` reads the per-frame program state (`flip_prog`, `flip_pitch_deg`,
`flip_twist_deg`, `flip_rate_dps`, `flip_shape`, `flip_shape_legs`) and the **rendered** body axis from the hero's bones
(`body_axis_deg`, `body_pitch_deg`: hips → head, one-row shift like every bone column), and prints F1–F5, F7, F8, F10, F11 per trick,
plus F9 from the camera columns (`pcm_roll`, `hero_bbox_h`, camera height vs hero). Rates from the rendered axis are taken over
0.04 s (the 25 fps reading step used on the owner clip). Pixel checks (hero height) need a rendered capture, not a -nullrhi probe.
