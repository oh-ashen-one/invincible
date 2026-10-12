# Terrain shot list (piece E) — every round captures these from the RUNNING game

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Map `/Game/Terrain/Maps/Manhattan_Terrain` (integrated golden Manhattan sublevels + `Terrain_Land`); the baseline for "previous round" pairs is the same camera on
`/Game/Maps/Manhattan` (the city alone: flat land colour under the park). Every run goes through `/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label terrain`;
hero placed by `-WHTravScript` (`docs/night1/terrain/scripts/*.json`, UE metres: x east, y south, z up, yaw in degrees, camPitch radians looking down).

| id | what | why | reference (private refs/) |
|---|---|---|---|
| P1 | still 3840x2160: swing height (~70 m) over the park's south end looking north (Sheep-Meadow-like lawn, ponds, paths, woods, skyline behind) | E1 / E4 park crops | `streets/skyline-perch-dn__dn_1438.jpg`, `streets/swing-over-city-golden-trailer__st_0052.jpg` |
| P2 | still 3840x2160: ~45 m over the Reservoir looking north-east | water edge + running track | `streets/skyline-queens-aerial__gr_0033.jpg` |
| P3 | still 3840x2160: ~35 m over the Lake / Ramble woods | paths through woodland, banks | `streets/rooftops-watertowers-golden__nm_0314.jpg` |
| P4 | 15 s movie 1920x1080: sprint along a lawn then a path (ground level, grass tufts, collision) | E2 / E7 | `traversal/` ground frames |
| P5 | 15 s movie: low swing pass over the park (hero ~25-40 m) | ground at swing height | `traversal/` swing frames |
| P6 | still: Hudson-side esplanade / seawall from ~30 m, looking along the shore | E3 shoreline | `streets/` waterfront frames |
| P7 | 15 s movie: shore walk (sprint) along an esplanade | E3 continuity from the hero's view | |
| B1-B3 | baseline: P1 / P2 / P3 cameras on `/Game/Maps/Manhattan` | previous-vs-this pair | |
