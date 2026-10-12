# Island (piece A): IP exclusions (Unreal port only)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Owner rule (2026-09-29): we copy nothing. The browser atlas files are **not modified**; the Unreal-side PNG copies are sanitised by
`tools/export/ip_sanitize.py` when `tools/export/prep_textures.py` converts them (build step `city_prep`). The tables in `ip_sanitize.py`
are the single source of truth; this page mirrors the island's additions. The Times Square ad / sign cells (`ts_ads`, `ts_signs`) are
listed in `docs/night1/city/IP_EXCLUSIONS.md` (unchanged).

## signs.png (facade shop-fascia atlas, 1024 x 2048: 16 one-row signs of 1024 x 128)

`src/world/facade.js` (`tSigns`) picks one row per shop fascia (`row = floor(hash * 16)`) and stretches the whole row over the board; the
billboard path samples a quarter of a row. Every excluded row is repainted from its own left-edge vertical profile (board colour, bevel and
border kept, lettering removed) and new original lettering is drawn on it (system font Arial Black, supersampled 3x). No pixels are copied.

| row | excluded lettering | why | replaced by |
|---|---|---|---|
| 4 | CHASE BANK (white on blue) | a real bank's name (round-02 critic, r2 t=25.0 s) | HARBOR SAVINGS (white on the same blue board) |
| 2 | DUANE PHARMACY (red on white) | evokes the real Duane Reade chain (conservative) | CORNER PHARMACY |
| 8 | SUBWAY EATS (yellow on green) | a real sandwich chain's name in its yellow-on-green colours (conservative) | HERO SUBS |

Rows kept (generic trade names): DELI & GROCERY, PIZZA, BAGELS & CAFE, NAILS SPA, WINE & LIQUOR, HARDWARE, DINER, SHOES, THAI KITCHEN,
DRY CLEANERS, OPTICAL, COFFEE, HALAL GYRO.

## Reviewed, not changed this round (round-02 critic asked for a review)

| what | where | status |
|---|---|---|
| CHOCO LOCO | Times Square ad / sign art | not changed this round; flagged for the next IP pass (image review needed) |
| TOKKA | sign art | not changed this round; flagged for the next IP pass |
| IRON GUARDIAN mural | wall-ad art | not changed this round; flagged for the next IP pass (the name evokes armoured-hero branding) |
| THE MARQUIS THEATRE | street-level marquee / blade sign on the x 0 avenue near y 1730 (round-03 r5 frames, `r5_m2_avenue_t20s`); baked into the browser signage atlas (`src/world/signage.js` THEATRE cells, city piece's `ts_signs` family) | the name of a real Broadway venue (generic words, but a real marquee) | not changed this round (the atlas is the city piece's; needs an image review); flagged for the next IP pass |

Verification: `python3 tools/export/ip_sanitize.py public/assets/city/tex <out>` writes `signs_clean.jpg` (contact check). The built
texture is `/Game/City/Textures/signs` (from `<scratch>/tex/signs.png`).
