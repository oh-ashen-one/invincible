# Critic r08 — swing/web/flips, blind. Pixels only; ffmpeg/PIL measurements in critic-r08/.

## Scores
1. **Web deployment: 7** — s2 t=2.36–2.42 (60fps, press1/): arm reaches to anchor, strand starts at the palm, tip travels speck→full over 3–4 frames (~0.05–0.07 s, at/below W3's 0.06 floor). Release s1 t≈4.85–4.92: strand 950→950→950→800→~150→0 px over 5 60fps frames = retract ~0.07 s vs W8's 0.15–0.40 s — near-vanish. No wrong-origin or through-wall seen.
2. **Web read: 7** — scans on s2 g_008: core 1–3 px (W5 wants 2–4); reads on golden facades (s1) and night sky (s5 t=4.5–7), slightly glowy at night, no gaps sampled.
3. **Swing body: 6** — phases and per-swing variety present (s1 t=3.8–5.4, s2), but a horizontal superman pose is held through bottoms and leg lag is subtle vs swing-canyon-chase.
4. **Flips/tricks: 5** — s3b t=9.7–10.4 zoom: tuck→unwind→held spread, eased, readable; but no tight pencil/pike (legs bent in open shapes), ~1 rotation per release vs owner's 2–3, no wall-run flip (F12); s3 canyon flips show hero ≈0.15 of frame height vs F9's 0.18–0.36.
5. **Air/transitions: 5** — s4 t=10–13 float evolves and catches clean; but s3 loses the hero off-screen t≈16.0–17.6 (0 hero pixels on a_026/028/030/035/041; camera on empty alley walls), then ~2 s idle in a black courtyard (t≈18–20).
6. **Camera: 4** — s1/s2/s5 chase competent, no roll; s4 floats shot top-down, hero 65–87 px tall (f_0010/f_0025/f_0055/f_0085; reference chase ~0.2–0.3 of height); s3 ends buried in a facade (t≈17.5).

## A/B (better → identity)
- swing-chain: **B** (kinetic chase, speed blur). Obvious: A=ours, B=reference.
- swing-presses: **A** (press anticipation). Obvious: A=reference, B=ours.
- night-swing: **A** (lower/closer/faster). Obvious: A=reference, B=ours.
- release-air: **B** (hero big vs sunset; A a 60–90 px speck). Obvious: A=ours, B=reference.
- aerial-flips: **B** (held open shapes vs sky). Fairly obvious: B=reference, A=ours.
- progress-flips: **A** (airborne vs sky; B crawls a shaded facade, camera in wall at t=17.5). Guess B=current, A=previous.
- progress-swing: **B** marginally (steadier strand at t=7.9). Guess B=current; not obvious.
- progress-presses: **tie**. Low-confidence guess B=current.
- progress-night: **B** (strands more visible). Guess B=current.

## Biggest gaps (by score impact)
1. **Camera tracking/framing (axes 6+5):** hero fully in frame at 0.18–0.36 of frame height through every release→trick→catch; no top-down far cam (s4: hero 65–87 px all clip); no alley/wall burial (s3 t=16.0–17.6 off-screen, t≈17.5 in facade). Reference: trick-release-sky. Test: hero bbox 195–390 px, in-frame ≥95 % of s3/s4 frames.
2. **Flip vocabulary + wall-run flip (axis 4):** straight-leg pencil, tight pike (hip ≤60°), one held open shape ≥0.3 s per trick (F4), 2–3 rotations on long releases (F1), wall-run→flip (F12). Reference: owner clip S2/S3/S6. Test: flip_check F1–F8 + frame strips vs owner clip.
3. **Release retract (axis 1, W8):** s1 t≈4.85–4.92 measured ~0.07 s; make slack/retract last 0.15–0.40 s. Test: strand drawn length per 60fps frame around every s1/s2 release, 100 % in window.

## Secondary
- Shot travel ~0.05–0.07 s (s2 t=2.36–2.42) — at/below W3's floor; stretch to 0.10–0.15 s.
- Night strand halo slightly beam-like (s5 t≈5–7).
- s3 t≈18–20: ~2 s idle in a black courtyard — dead air.
- s1 t≈4.9–5.2: hero bbox touches the right frame edge (xmax=1917) for 3+ consecutive 60fps frames.

## Verdict
**FAILS TARGET** — axes 3–6 below 8; camera (4) and the s3 hero-loss sequence are the floor.
