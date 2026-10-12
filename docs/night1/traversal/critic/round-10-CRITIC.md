# P3 traversal + camera, round 10: blind critic (Opus 5.5)

*Homage fan game. Not an official Marvel, Sony or Insomniac game.*

Pixels only. Tools: `vp_cam.py`, `nearflow.py 8`, `ref_hero_dets.py` at 10 fps, and hand-read 10 fps crops. Data is in `_scratch/critic-P3-r10-work/`. "a" is `a_swing_chain`.

## Scores

**Swing arc and rhythm: 6**
- T1, T2 and T7 pass: holds last 0.6–1.3 s, with 3 and 2 attaches per 8 s. The hero is high at 3.8 s and one storey up at 6.7 s.
- T4 fails: the arms-spread pose is held at 12.4–13.0 s with no web.

**Camera: 6**
- T8 (.213), T9, T11 (2.6/10.2/22°), T12–T14 (103°), T17, T20 (.39) and T21 (2.17) pass.
- T10 (.198) and T18 (p50 .68) fail narrowly.
- In b, hFOV is 96° and pitch p95 is 32°.

**Web read: 6**
- T3 passes at about 29% per 8 s (hand-read; the detector picked up tower edges).
- T5 and T6 pass: at 5.4 s the rope runs hand to top edge at 20°, 3–4 px wide.
- The line is faint grey.

**Moves and transitions: 5**
- T22 passes (c: 42–52° up), but the wall-run lasts only 1.2 s.
- T23 fails: the b trick is framed against a facade.
- b ends clinging to a wall with no zip.

**Body animation: 5**
- The arms-out pose held at 8.7 s and 12.4–13.0 s looks like a mannequin.
- The body lines up with the rope at 5.4 s.

**Flips and air tricks: 4**
- Ours: two 180° flips in 0.2 s each (about 900°/s) at 1.9–3.4 s. No shape holds longer than 0.3 s, and the flips are seen foreshortened from behind.
- The reference (release-trick-dive A) instead does a tuck, then a 0.8 s inverted pencil, then a 1.2 s inverted swan that unwinds at about 150°/s. The hero is about 0.3 of frame height, side-on against open sky.

## A/B decisions
The reference is better in every pair against ours:
- swing-chain: A is the reference.
- swing-chain-2: A is the reference.
- release-trick-dive: A is the reference.
- wallrun: A is the reference.
- sprint-jump-swing: B is the reference.

progress-swing compares two of our own builds. B (lit city) beats A (gray box) on altitude, flips and rope time.

## Biggest gap
Build every web-less trick as three beats:
1. a 180° rotation in 0.35 s or less;
2. one extended shape (pencil or swan) held for at least 0.6 s, rotating at no more than 150°/s;
3. an ease of 0.4 s or less into the next attach.

Frame it side-on, with the hero at least 0.20 of frame height against sky above the roofline.

Test: every trick shows at least 6 consecutive 10 fps crops with the same silhouette, and there is at most one flip per second.

## Secondary issues
1. The hero is hard to read in three places:
   - a 6.7 s: black blob, luma 28, height .07;
   - a 14.8 s: legs washed white by haze;
   - c 2.3–3.5 s: the suit reads black.
2. T10, T18 and b's hFOV are just out of band.
3. T4 fails on the held pose at 12.4–13.0 s.
4. The b trick is framed against a facade, b has no zip, and the wall-run is short.

No copied brands or logos seen.

## Verdict: FAILS TARGET
The lowest axis is flips and air tricks, at 4.
