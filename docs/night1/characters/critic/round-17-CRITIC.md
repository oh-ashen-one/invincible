# P2 hero skins, round 17: blind critic (Opus 5.5)
Homage fan game, not affiliated with Marvel, Sony or Insomniac.

## Scores (r14: 6, 5, 5, 5, 5; check (b): no regression)
- **Hero model & suit: 6.** CH1 met (0.547–0.548H).
  - Lenses are flat fills with one specular dot. The cloth is matte. The cheek cords read as tear-tracks.
- **Hero animation: 5.** The 9.933 s snap is fixed (diff 5.1 against 4.6/3.9; r16 was 15.6).
  - **Pawn bob is 4.04–4.10 Hz** (a peak every 14–15 frames), so CH6 fails.
- **Enemies: 5.** Check (a) passes: against r14, 0.45% (front) and 0.31% (3/4) of pixels differ by more than 20 luma.
  - The diffs sit on weapon and limb edges. There are no blotches or ghosts.
  - Twins remain in slots 1/6 and 2/7, and the bat is held in open fingers.
- **Civilians: 5.** The 7.483 s cut is gone (max diff 2.9 against 55.5 in r14).
  - Otherwise this is r14's clip (diff 0.82 at 4 s): a rigid coat and robe on an empty street.
- **Image quality: 5.** The Ash sash edge is fixed: residual 6.4 px against 19.9 in r16.
  - The Cinder seam is continuous through the chin.

## IP: PASS (8/8)
- Verdant's accent hue moved from 50° to 32° (copper), and the accent fell from 30% to 6.6% of the green. Yellow pixels went from 32,285 to 228. It no longer reads as the known wetsuit.
- No glyph, web, teardrop lens or text.

## A/B (decided blind)
- **Lineups:** r16-lineup B, progress-lineup A.
- **Chests and heads:**
  - r16-chest-ash B (no shelf); r16-headfront-cinder B (straight seam, tapered cords);
  - chests: ash A, cinder B, tessera A and verdant A win (bounded panels);
  - profile-verdant B (brow overhangs the rim).
- **Backs:** the side without front bleed wins (ash B, cinder A, plum B, saffron B, sage B, tessera A, verdant A). Glacier is a tie.
- **Swap-pawn:** A wins. B snaps at 9.933 s (18.3).
- **Ref-vs-ours:** ref wins every pair.

Not re-shot: the side run, the chase run and the fight.

## Single biggest gap
Retime the pawn run to 3.2–3.8 steps/s (a bob peak every 16–19 frames at 60 fps). Keep the start ramp.

**Test:** in swap_pawn_T_key.mp4, the head-top FFT over 1.5–11.4 s peaks at 3.2–3.8 Hz, and no frame diff exceeds 2× its neighbours.

## Secondary
1. Distinct twin heads; closed grips.
2. Re-shoot the fight: thugs at least 1.5 m apart, attacking in turns, with hit FX.
3. Add lens curvature and gloss, and a cloth sheen.
4. Coat/robe cloth motion; dressed crowd street.

## Verdict: **FAILS TARGET**
Lowest axis: 5.
