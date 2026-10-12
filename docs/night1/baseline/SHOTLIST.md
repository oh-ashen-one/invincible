# F3 shot list: browser baseline captures and the reference each one is judged against

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.
> Reference paths are in the private repo `~/spiderman-learnings/refs/` (never copied here).

## Clips (`clips/*.mp4`, 1920x1080, frame-stepped 60 fps of game time; script in `tools/playtest.mjs`)

| clip | length | what happens | compare with |
|---|---|---|---|
| `swingChain` | 22.0 s | jump from the avenue spawn, 12 RMB swings chained down the canyon, tricks on release, wall touch at 9 s, fall at 21 s | `traversal/swing-canyon-chase-high__nm_0141`, `swing-avenue-chase__nm_0642`, clip `swing-canyon-chase` |
| `trickZip` | 14.5 s | 3 swings, Space-release trick, dive (C), look up + E web zip (peak 60 m/s) to a roof terrace at 110 m, lands and idles | `traversal/trick-sky-pose__nm_0428`, `dive-empire-blur__nm_0032`, `zip-rooftop-og__og_0029` |
| `wallRun` | 22.2 s | Shift + W into a 215 m tower facade (approach proven by a dry run), wall zips (E taps), top-out over two setbacks to 235 m | `traversal/wallrun-glass-tower__nm_0816`, `wallrun-empire__nm_0008`, clip `wallrun-empire` |
| `street` | 29.0 s | steered sprint 260 m along the east sidewalk, Shift parkour run from 10 s (camera falls top-down at 10 s, bug 1) | `animation/run-toward-cam-dn__dn_0421`, `streets/street-sidewalk-pedestrians__dn_0721` |
| `fight` | 25.8 s | 8 thugs (`__cmb.debug.fight('mmgb', 8)`), 3 rounds of combo / dodge / web shooter / launcher / web strike / finisher | `combat/street-fight-nm__nm_0501`, `group-fight-nm__nm_0223` |
| `water` | 14.0 s | run west off the Hudson seawall at z=-440, dive, point launch back out, swing along the shore, wall touch | `traversal/webwings-river-dn__dn_1244`, `webwings-waterfront-dn__dn_0026` |
| `skins` | 26.4 s | 8 suits (advanced, iron, symbiote, claude, codex, gemini, kimi, qwen), 3 s each while swinging | `characters/suits-duo-closeup*`, `suits-render-trailer` |
| `crowd` | 18.4 s | walk up to the nearest dog walker, follow 7 s, walk to the nearest street critter | `streets/street-sidewalk-pedestrians__dn_0721`, `centralpark-plaza-crowd__cp_0121` |
| `carBlock` | see `logs/carBlock.json` | run straight at a parked car (bug 4) | none (bug evidence) |

## Stills (`stills/*.jpg`, 3840x2160, `?shot=<name>`, `src/shots.js`)

`street`, `wall`, `swing`, `swingBack`, `climb`, `suit` (refs 1-5 compositions and the suit close-up); `gulls`, `pond`, `riverHigh`, `eastRiver`, `splash`, `underwater`, `waterline`, `surfacing`, `riverLow` (water); `parkHigh`, `parkLow`, `parkClose`, `streetTrees` (vegetation); `glassBreak`, `glassBreakLate`, `hydrantBreak`, `benchBreak`, `newsBreak`, `crateBreak`, `carBreak` (destruction). Time-of-day: `street_tod_sunset`, `street_tod_night`, `swing_tod_sunset`, `swing_tod_night`, `parkHigh_tod_sunset`, `parkHigh_tod_night` (`&tod=sunset` / `&tod=night`).

Suit close-ups: `stills/skins/<suit>_<front|threeq|back|side|head>.jpg` for the 8 suits at 1920x1080 (`head` frames head + chest); `stills/bugs/` holds single-bug evidence.
