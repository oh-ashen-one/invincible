# Round-04 critic's measuring scripts (copied unchanged from the critic's work dir, 2026-09-29)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation.

Run by the builder before every capture review from round 05 on (yolo weights: `/Users/midir/sm2-n1/_scratch/city/yolo/yolo11x-seg.pt`, device `mps`;
venv with ultralytics: `$P2_SCRATCH/r4/yv`):

- `cracks.py IMG...` : YOLO person masks; for every dark-clothed person (median V < 140) it counts thin bright slivers (bright vs the person's median by > 90, area 6-600 px, aspect >= 3) inside the mask eroded by 9 px. CH18 target: 0 slivers.
- `count.py VIDEO...` : YOLO people per frame (2 samples per second): median / p10 / max people, people >= 3 % height, height median / p90 / max (fraction of frame height).
- `hero_track.py VIDEO OUT.npy` : red/blue hero blob per frame -> height fraction and the dominant frequency of the bbox height (step rate).
