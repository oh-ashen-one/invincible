# Round 11 SPEC CHECK (piece G, hero skins)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. Numbers are read from `evidence/` by `tools/ue_char/suits/spec_check_r11.py`.

## Skins acceptance (PLAN-firstpass section 4)

| line | target | measured | verdict |
|---|---|---|---|
| original suits | >= 6 | **8** (`suits.json`, ids tessera, verdant, plum, cinder, glacier, ash, saffron, sage) | PASS |
| no red-and-blue blocking / red- or blue-dominant / black+white / white-dominant (P1 - P5, P7) | 0 failures | max red 0.000, max blue 0.006, max white 0.001 | PASS |
| every suit differs from every other (P6: unique net|sash|mark key, lit-palette distance >= 38) | 0 failures | min palette distance **47.1** over 28 pairs; 8 unique keys | PASS |
| no UV seam > 40 px at 4K (texture level: both sides of 1921 seam edges (15.1 m), Lab dE > 18, 660 px/m = hero 0.55 of a 2160 px frame) | 0 runs > 40 px | worst run **4.6 px**, runs > 40 px: 0, runs > 10 px: 0 | PASS |
| OCR finds no official emblem / name | 0 hits | atlases: 0 hits (8 images), 4K stills: 1 hits (32 images); denylist 42 terms | PASS after review (`evidence/ocr_review.txt`: 1 hit reviewed by eye on the 4K frame: skin_verdant_chest_4k.jpg "MILES" is tesseract noise on the horizontal rib stripes (the same image yields CAKES, MALES, RABIES, PUKE, ORCA ...); the chest holds only a ring-and-dot mark, ribs and a V yoke, no text.) |
| swap <= 0.5 s, REAL-TIME 4K run (swap request to 2 frames later, `WH_SUIT swap_done`) | <= 500 ms | 17 swaps: median 65 ms, worst **68 ms** (3 frames at ~23 ms; textures resident 17/17 at that point for all but the first start-up swap) | PASS |
| swap <= 0.5 s, pixels of the fixed-step movie | <= 500 ms | 7 of 7 injected T presses found on the pixels (+ 1 unmatched histogram steps = the director camera cut at 10 s), worst key-to-pixel latency **33.3 ms** ([2] frames at 60 fps, `analyze_swap.py` on the fixed-step movie); engine: `apply_ms` max 0.39, `swap_done` wall_ms max 745.7 (a -movie run spends ~0.22 s of wall time per dumped PNG frame, so this wall figure is the dump, not the game latency; the real-time number is the row above), textures resident ['3/4', '4/4'] | PASS |
| IQ >= 6 | blind critic | see `critic/round-11-CRITIC.md` | critic |

## Resolution disclosure of the 4K stills

`evidence/stills_perf.json`: output 3840x2160, internal 3840x2160 (`r.ScreenPercentage 100`), screen-percentage mode manual. Real-time run: frame times are NOT a performance result (shared GPU, other agents; the lock logged `contaminated=true`).

## Other numbers

- texel density: 4096 px atlas x 0.569 UV units / m = **2331 texels / m** (CH3 target >= 680); Tessera 8192 px = 4662 texels / m.
- persistence: pawn run end: WH_SETTINGS suit saved to GameUserSettings: HeroSuit=1 HeroSuitId=verdant; relaunch:     WH_SUIT start suit 1 (verdant) from settings, persist=1 live=0; menu:         WH_SUIT start suit 1 (verdant) from settings, persist=1 live=0; ini:          HeroSuit=1 HeroSuitId=verdant
- key paths: T / Shift+T, gamepad D-pad Up / LB + D-pad Up, settings-menu row, console `wh.Suit <n|id>`, `wh.SuitNext`, `wh.SuitPrev`.
