# CRITIC — P1 City, round 05 (pixels only)

## 1) Axis scores
1. **Facade & building fidelity — 5.** S8/S2 brick towers with setbacks, cornices, AC units and fire escapes read well at distance. Up close they fall apart. S1 storefront interiors are blurry shelf cards (4K crop x0–1700 y560–1560). Sign sub-lines smear at 4K. The curtain-wall towers in S1 are flat and dark.
2. **Street-level dressing — 4.** On the S1 near-left sidewalk I count 0 trees, 1 trash can, 1 hydrant, 3 planters, 0 news/mail boxes, 0 steam vents and one uniform asphalt tone. Ref sidewalk-pedestrians__dn_0721 has pavers, planting beds, litter and bollards. The S6 plaza repeats kiosks and glowing white floor squares.
3. **Rooftops & skyline — 3.** The S4 far shore is untextured lavender boxes: mean RGB (188,202,225), so blue minus red is +37. The shore strip is near-white (228,232,235), brighter than the water (219,226,233), and reads as snow or void. In the S4 mid-ground crop (x1500–2600 y700–1700), most blocks behind the front row have no window grid. The S3 roof has one tower and a few vents.
4. **Composition / Manhattan believability — 4.** The S1/S2 canyons and the S6 red steps read as NYC. Times Square billboard coverage is far thinner than timessquare-day-trailer__eny_0046. S8 is framed with no street visible, so I judged it as if the street weakness showed.
5. **Image quality — 5.** Edges are clean, but S3 is crushed (62.9% of pixels have luma <25) and S7 is too (59.1%), with a clipped sun. That is lighting's fault, but it still hides the city. Signage and interior textures are under-resolved at 4K.

## 2) A/B
- avenue-street, intersection, sidewalk, perch-skyline, aerial, timessq-street: **B better in all six, by a wide margin.** B has warm bounce light, worn and patched asphalt, parked cars and taxis, dense street trees, deep window reveals, and a textured far shore with bridges running to the horizon.
- avenue-swing-height: **A better**, although the hero fills about 50% of that frame. Its sunlit brick, fire escapes and tree canopy beat B's clean, empty canyon.
- **progress-street: A slightly better.** B's left canopy spans about 45% of the frame width, hides the storefront row and brings back a blurry interior card. B does add the street trees that A lacks.
- **progress-canyon: B slightly better.** It adds fire escapes on the left tower and the right brownstone, plus awnings. The difference is small.

## 3) Biggest gap: far field (S4, and every view past about 1 km)
Every building beyond the first two rows needs a readable window grid and a brick, stone or glass material at 1080p. No flat-colour boxes should remain.

- **Far shore colour.** Tint it to the mid-ground's warm-neutral hue (red and blue channels within ±10).
- **Shore strip.** Replace the white strip with a darker embankment, piers and an esplanade. Test: crop 4K x0–2800 y550–700 and confirm its luma is below the water's.
- **Water.** It should reflect the far shore.

Reference: streets/skyline-perch-nm__nm_0846.jpg and river-queens-aerial__gr_0936.jpg.

## 4) Secondary issues
1. **Sidewalks (S1/S6).** Add paver joints, cracks, wet patches, news and mail boxes, steam vents, and at least 2 trees per 20 m on both sides. Ref: street-sidewalk-pedestrians__dn_0721.
2. **Storefronts.** Replace the card interiors with parallax or 3D interiors. Signage needs twice the texel density.
3. **Times Square.** Cover every facade above the 2nd floor with emissive panels, and remove the pure-white floor light squares.
4. **Rooftops.** Add water towers, bulkheads, antennae and clutter to the S3/S4 roofs. Ref: rooftops-watertowers-golden__nm_0314.

## Brand/IP flags
- **"HAUTE UNLIMITED" (S5, 4K ~x900–1400 y450–800).** This is a fictional brand from the reference game (visible in timessquare-day-trailer). It was copied and must be removed.
- **"HOTEL ASTOR(IA)" (S5/S6).** This evokes the real Hotel Astor and Waldorf Astoria.
- **"LIVE AT MADISON … ARENA".** This evokes Madison Square Garden.
- **"…REAL OUTDOOR" (S6).** Partly obscured; possibly evokes L'Oréal. Rename it.

## 5) Verdict: **FAILS**
