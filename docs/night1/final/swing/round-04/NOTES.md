# Round 04 (builder SW)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Pixel-measured (hero mask, Tessera suit). New check **P2**: hero silhouette (16x16 grid over the mask bbox, `hero_sil` column) IoU between frames 0.3 s apart < 0.85 on >= 90 % of swing/air frames, no pose held > 0.4 s (IoU >= 0.92 over 0.1 s).

## Done
- **Web shot with arm lead:** `WebAttach` starts the strand at Age -0.033 s (not drawn; the arm aim begins at the press), so the first drawn frame has tip length ~0 (first-frame progress 0.00 on every clip) and the tip lands 4-12 frames later (max per-frame growth <= 25 %).
  The s2 case 3 (wall-cancel facade) pop is fixed: the strand was re-shot across the avenue by the rope-wrap test (`reanchor (rope wrap, blocked at 2.6 m)`, now logged) because the body sits beside the wall of its own facade anchor; the wrap test is skipped for 0.4 s after an attach.
  Probe: strand stays on the facade anchor, tip 0.1 -> 2.6 -> 4.9 -> 7.1 -> 8.9 -> 9.9 m over 6 frames.
- **Anchor filters** (`AnchorElevMin`, `AnchorAheadMin`; default 0.14 / -0.05 in game): level and behind-the-line anchors are rejected. In the chain scripts they are relaxed (0.1 / off): with the defaults the s1 chain drifted off the avenue (web-on 51 %).
- **P2 (silhouette evolution) passes on all six clips**: IoU median 0.33-0.44 (p90 0.51-0.61), below 0.85 on 100 %, longest held 0.10-0.18 s. Swing-life motion enlarged (knees to chest, leg split up to -1.35 rad / +0.75, free arm swings back on the drop and forward on the upswing, torso curl x2.8).
- **Trick camera:** closed-loop distance from the projected hero bone box (`HeroProjH`, target 0.29, pixel ~0.93 of it). Hero centroid stays inside 0.25-0.70 (r03: 1 % outside).

## Not reached (P1 pixel hero height)
s1 swing 88 % / air 84 % (r03: 95 / 96; 26 samples have no hero pixels), s2 72 / 46, s3 flow 67 / 56, s3b 54 / 46, s4 81 / 62, s5 = s1 numbers. Trick frames swing between 0.06 and 0.55 of the frame as the pose rotates (a vertical pencil vs head-on); distance feedback cannot follow that, so 90 % needs a different approach (e.g. FOV / crop compensation from the pose extent along the screen axis).
Wall / foliage coverage <= 40 % and "camera at or below the hero with sky behind" were not measured or changed this round (s3b 21.2-21.9 and s3 4.4-5.9 not re-checked).

## Findings
- s3b 21.8 "strand vanishes mid-hang": the swing ran into the facade 0.3 s after the attach (anchor off to the side), the hero entered Wall mode and the web is released by design; the strand then fades over 0.30 s. Not a draw bug; the side anchor is the cause.
- s2 22.4-24.4 "2 s wall stall with no strand" is s2 case 7 (press with no anchor): the reach gesture plays, no strand by design.
- Chest pop at the attach in s2 case 3 came from the same re-shot: gone with the fix (W4 worst on s2 still 2181 deg/s from other cases).
- Dark rim: core fraction 0.5 (rim ~0.95 px each side at 3.8 px). W5 by day still fails (s1 36 % on the dev render); night passes.

## Open
P1 on s2/s3/s3b/s4 and a small s1 regression, W2/W3/W9/W10 on s2, W4 s2/s3/s4 in places, W5 by day, A5 catch timing, F11, s3 flow web-on (~38 %), the `with_holder.sh` admission refusals when the Qwen resident holds the slot (each clip needed up to 3 plain re-invocations: s4 x2, s5 x1, s3b x1, s2 x1).
