# P1 City: IP exclusions (Unreal port only)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Owner rule (2026-09-29): we copy nothing. The Times Square ad atlas `public/assets/city/tex/ts_ads.webp` and the storefront sign atlas
`ts_signs.webp` came from the upstream browser project and contain cells with Marvel-universe names and brands from the real game.
The browser atlas files are **not modified**. In the Unreal port `tools/export/prep_textures.py` calls `tools/export/ip_sanitize.py`,
which overwrites every excluded cell of the Unreal-side PNG copy with the pixels of another original-brand cell of the same
orientation (a UV-slot remap on the Unreal side). The table in `ip_sanitize.py` is the single source of truth; this page mirrors it.

Atlas layout (from `src/world/timessq.js`): `ts_ads.webp` 4096 x 4096, top half 64 landscape cells 512 x 256 (8 x 8, index = row * 8 + col),
bottom half 64 portrait cells 256 x 512 (16 x 4, index = row * 16 + col). `ts_signs.webp` 2048 x 2048, 64 signs 512 x 128 (4 x 16).

## ts_ads.webp: excluded cells and what replaces them

| kind / cell | content that is excluded | replaced by |
|---|---|---|
| L 0 | OSCORP, "Tomorrow, Engineered" | L 55 (Sonara headphones) |
| L 1 | RE-ELECT OSBORN, "Safe Streets. Strong City." | L 63 (Harborline insurance) |
| L 2 | THE DAILY BUGLE, cafe / newspaper | L 52 (Daybreak Roasters) |
| L 3 | ROXXON, "Powering New York" | L 53 (Volterra E7) |
| L 22 | EMPIRE STATE UNIVERSITY, "Enroll for Fall" | L 45 (Arcline Book) |
| L 26 | FROSTED HALOS, "Part of a Heavenly Breakfast" | L 43 (Citrus & Co) |
| L 33 | BOTANICA, "Now Playing, Majestic Theatre" | L 46 (Dinosaurs Alive) |
| L 34 | FROSTED HALOS, "Start Bright" | L 20 (Big Apple Burger) |
| L 39 | HELL'S KITCHEN BLUES, "New Season Streaming"; its round-05 donor L41 was the "NEON RACERS - OUT NOW" game key art (round-06 critic) | **original art**: NIGHT LANTERN MARKET (paper lanterns over a pier) |
| L 27 | COLTEX SPORT (sneaker brand; round-04 critic: too close to the real game's COLEXCO) | L 4 (Lumen X5) |
| P 27 | COLTEX - "Own the Court" (same brand, portrait cell); its round-04 donor P8 was a basketball-shoe photo | **original art**: PLANT A TREE leaf poster; caption 'MORE SHADE ON EVERY STREET' (r10: 'GREENER BLOCKS START HERE' was reworded by the integrator because the partial S3 crop 'LOCKS START' read like a games publisher's name; r11 sets the caption on three lines, MORE SHADE / ON EVERY / STREET, in the left 77 % of the board so every crop shows whole words) |
| P 38 | COLEXCO - "Run the City" (near-copy of the real game's brand) | P 15 (Skyward Air) |
| L 35 | COLEXCO SPORT (red-on-white sneaker ad; the "COLEX SPOR..." banner in S6, found after the round-04 critic note) | L 47 (Big Apple Tours) |
| L 32 | HAUTE UNLIMITED, "New York - Paris - Milan" (fictional brand copied from the real game; round-05 critic) | L 7 (Vantor) |
| L 59 | NEW YORK KNIGHTS, "Tickets on sale" (blue / orange basketball ad; conservative, evokes a real NBA club) | L 29 (Nova Fold) |
| L 60 | (donor changed: it used L 59) THE DAILY BUGLE, "New York's News" | L 16 (Harbor Mutual) |
| P 24 | HAUTE UNLIMITED (portrait, blue gown) | P 10 (Iva Deni) |
| P 32 | HAUTE UNLIMITED (portrait, dark gown; OCR "TAUTE UNLIMITED") | P 44 (Hudson Pier 26) |
| P 23 | LIVE AT MADISON ARENA, "One night only" (evokes Madison Square Garden) | P 3 (Patrol) |
| P 63 | NOVA LEE - MADISON ARENA - LIVE (evokes Madison Square Garden) | P 5 (Zero Sugar) |
| P 6 | OSCORP, "A Healthier Tomorrow" | P 20 (Spark) |
| P 7 | DAILY BUGLE, "Read All About It" | P 22 (Ashby & Cole) |
| P 13 | ROXXON, "Fueling Tomorrow" | P 31 (Sol Airways) |
| P 39 | FROSTED HALOS | P 49 (Chasing Waves) |
| P 41 | HYDRA PRO | P 18 (Glacier Spring) |
| L 23 | "SEE SOMETHING? SAY SOMETHING." + a call number, police-light strip (the real transit-authority slogan; round-06 critic, S6 near x 1270 y 210) | **original art**: RIVERSIDE GARDEN WEEKEND (flat hills, sun, flowers) |
| L 41 | "NEON RACERS - OUT NOW" (racing-franchise key art; round-06 critic, S5 / S6) | **original art**: HARBOR POOL (waves and a sun disc) |
| L 61 | "STAR RAIDERS 3 - OUT NOW" (game key art, same pattern; not named by the critic, removed with L39 / L41) | **original art**: LATE NIGHT BAKERY (crescent moon, bread) |
| P 8 | KINETIX "RISE ABOVE": basketball-shoe photograph, the S3 wall mural (round-06 critic: "looks like real product photography") | **original art**: GOOD MORNING, CITY (painted skyline sunrise, no photograph, no shoe) |

The six `original art` cells are drawn from scratch by `tools/export/ip_original_art.py` (PIL shapes and system fonts, no source imagery, no
generated-image prompt): `ip_sanitize.py` calls it for every table row whose donor is `art`. Round 07 additions: L23, L41, L61, P8 and the rewritten
L39 / P27 rows above.

Reasons: Oscorp, Osborn, Roxxon, Daily Bugle, Empire State University and Hydra are Marvel-universe names; Frosted Halos and Botanica are
brands from the real game (named by the critic, round 03); "Hell's Kitchen Blues" points at the Marvel / Netflix Hell's Kitchen material.

## ts_signs.webp

| cell | excluded | replaced by |
|---|---|---|
| S 48 | HOTEL MIRA (brand from the real game) | S 51 (BAKERY) |
| S 15 | HOTEL ASTORIA (evokes the real Hotel Astor / Waldorf Astoria; round-05 critic) | S 53 (COMEDY CLUB) |
| S 41 | BOREAL OUTDOOR (critic read "...REAL OUTDOOR": evokes L'Oreal / an outdoor brand) | S 55 (SNEAKERS) |

## Reviewed, kept

All other cells were read (OCR of every cell plus a visual pass): fictional brands only (Kinetix, Coltex, Colexco, Nova, Zest, Fizzo,
Vantor, Sonara, Harborline, Meridian Trust, Skyward Air ...). Not excluded on purpose, owner may still veto (round 06: the Times Square place name in five ts_signs cells, e.g. "PIZZA / COFFEE / CAMERAS / RAMEN / RECORDS ... TIMES SQUARE", is a real place name, not a brand, and stays): the "Majestic Theatre" show
ads (Gilded Fox, Queen of Hearts), "Iron Borough", "Nova" products (NOVA is also a Marvel name but a generic brand word here),
`city_signart.webp` (period ghost signs: Knickerbocker, Fulton Warehouse ...; no IP found) and `signs.png` (facade storefront signs:
generic trades plus a "CHASE BANK" cell, a real-world brand, not Marvel / game IP). The Times Square news ticker text
(`ts_ticker.webp`) mentions a "MASKED HERO" heist headline (generic).

Not used in the Unreal port but listed for whoever ports traffic (P6): `vehicles_atlas2.webp` carries "DAILY BUGLE - THE TRUTH, EVERY
MORNING" and "A HEALTHIER TOMORROW" (Oscorp) livery cells; exclude them the same way (`ip_sanitize.py` has the pattern).

## Round 05: original signage (nothing copied)

The street-level kit (`tools/export/street_kit.py`, `tools/export/gen_street_signs.py`) draws its own fascia boards and awning valances from
invented generic shop names with system fonts (Halvorsen & Daughters books, Silver Fern Cafe, Osteria Luna, Pine Street Pharmacy, Golden Lotus,
Kestrel Watch & Clock, Harbor Hardware, North Corner Deli, Sunrise Bagels, Velvet & Vine, Antonelli Pizza, Bluebird Laundry, Mercer Optical,
Copper Kettle Tea Room, Rosa's Flowers, Iron Gate Fitness, Lark & Finch, Harbor Light Photo, The Paper Mill, Dr. Amara Voss, Haley's Shoe Repair,
Orchard Street Bakery, First Harbor Credit Union, Lotus Nail & Spa, Anchor & Oak, Salt & Pepper Diner, Maple Leaf Fruit Market, Quill & Ink,
Cornerstone Medical, Neon Dragon Noodles, Sage Health Food; 48 generic valance lines such as "FRESH BAKED DAILY"). No logos, no marks of any
real or fictional franchise. If any of these turns out to collide with a real brand, edit the `FASCIA` list in `gen_street_signs.py`.

## Verification (re-run each round)

`python3 tools/export/ip_ocr_check.py docs/night1/city/round-NN [_scratch/city/tex]` OCRs the eight 4K frames of the round and every cell of the sanitised atlases against the denylist
(Oscorp, Osborn, Roxxon, Bugle, Frosted Halos, Botanica, Mira, Hydra, Empire State, Coltex, Colexco, Haute, Astor, Madison, Boreal, Outdoor, Knights, see something / say something, neo / neon racer, out now ...; the list lives in `docs/night1/city/spec_regions.json`, key `ip_denylist`, shared with `tools/export/city_spec_check.py --ip`).

### How the exclusions were built

`python3 tools/export/ip_sanitize.py` writes previews of both sanitised atlases to
`_scratch/city/r04/atlas/`. Rebuild in Unreal: `SKIP_EXPORT=1 STEPS=tex tools/export/build_city.sh` (re-imports the sanitised PNGs).
Round-04 captures of S5 / S6 show the replacement cells (billboards that read Roxxon / Frosted Halos / Botanica / Hotel Mira in round 03
now show Sol Airways / Chasing Waves / Dinosaurs Alive / Hotel Astoria).
