# Round 11 (first-pass piece G): the hero's ORIGINAL suits

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.
> No image generator, no reference image of any real suit, no scan, no trace: every texel is a function of the body's 3D position (planes, helices, hexagon / arch / rhombus distance fields), exactly like round 08's Tessera.

## What exists now

| piece | where |
|---|---|
| the generator: Tessera's `paint()` takes a **style** (a JSON override of `DEFAULT_STYLE`); `DEFAULT_STYLE` reproduces round 08 texel for texel (regression: 1024 px maps differ by max 0 / 255 from the round-08 code) | `tools/ue_char/suit8/design.py` |
| the suit list (8 styles, cycle order = list order) | `tools/ue_char/suits/suits.json` |
| evaluation on the hero atlas: base colour + normal (from the height map) + ORM per suit | `tools/ue_char/suits/gen_suits.py` (4096 px, ~45 s per suit on the CPU; Tessera keeps its 8192 px maps from `hero_suit_r8.py`) |
| content: textures (NeverStream), `MI_HeroSuit_<id>` + `MI_HeroLens_<id>` on `M_Char_Suit` / `M_Char_HeroLens`, the data asset `DA_HeroSuits` | `unreal/WebHomage/Scripts/build_characters.py` steps `skins`, `skinsmap` (nothing is committed under `/Content`) |
| the swap: `UWHHeroSuitSubsystem` | `unreal/WebHomage/Source/WebHomage/Characters/WHHeroSuit.*` |
| persistence + settings menu row | `Core/WHSettings.*` (`HeroSuit`, `HeroSuitId` in `GameUserSettings.ini [WebHomage.Settings]`), `Core/WHSettingsMenu.cpp` (section HERO) |

## The style knobs (every one is a field of `DEFAULT_STYLE`)

`palette` (body, crown, deep, ink, accent, accent_d, stitch, sole) | `flip` (mirror the whole layout) | `net.kind` = diamond (two helices) / hex (honeycomb, integer columns so it closes around a limb) / rib / square / chevron / brick / none, `scale`, `width` |
`sash.kind` = slash / vee (folded plane) / double / yoke (curved) / placket / none, its plane, width, curve | `wedge`, `trunks` (cut slope and height), `belt.buckle`, `spine` | `arm` (upper, forearm, other forearm) |
`greave`, `thigh_deep`, `sleeves` | `glyph.kind` = hexvane / orbit / tally / lattice / gate / keystone / ladder / chevrons (+ size, position) | `crown.kind` = honeycomb / racing / chevron / plain, `brow`, `vent` |
`hood`, `glove`, `boot` colour roles | `mott` (fabric mottling) | `fuzz` (cloth sheen tint, a material parameter). Adding a suit = one JSON entry, `gen_suits.py --only <id>`, rebuild step `skins`.

## The eight suits (cycle order = `wh.Suit n`)

| n | id | palette | net | sash | mark | hood | notes |
|---|---|---|---|---|---|---|---|
| 0 | tessera | slate teal / amber | diamond | slash | hex badge | honeycomb crown | the round-08 suit, unchanged (8192 px) |
| 1 | verdant | forest green / brass | rib | V yoke | eclipse ring | racing stripes | mirrored |
| 2 | plum | aubergine / jade | chevron | twin bands | tally bars | forward-V crown | |
| 3 | cinder | warm charcoal / cyan | brick | curved yoke | nested rhombus | plain | |
| 4 | glacier | ice grey-teal / slate / coral | honeycomb | sternum placket | arch | racing stripes, light hood | mirrored |
| 5 | ash | graphite / lime | large diamond | steep slash | keystone | forward-V crown | |
| 6 | saffron | ochre / umber / bone | square | leaning slash | ladder | honeycomb crown | |
| 7 | sage | sage / moss-dark / clay | honeycomb on limbs | none (clean chest) | chevron stack | racing stripes, light hood | mirrored |

Each suit also has its own lens tint (the accent colour, `MI_HeroLens_<id>`). Tessera keeps its amber lens.

## IP rules and how they are enforced

1. Never an official suit, emblem, web-line pattern or recognisable official colour blocking. No spider / bat / letter / star / shield / crescent / bolt mark: the glyph set is rings, bars, rhombi, arches and chevrons (`ip_guard.py` P7 allowed list).
2. No red-and-blue blocking, no red-dominant or blue-dominant suit, no near-black suit with white or red, no white-dominant suit (`ip_guard.py palette`, rules P1 - P5, measured on the atlas texels).
3. Every suit differs from every other by its (net, sash, mark) key AND by palette distance (>= 38 RGB units on the lit clusters, `ip_guard.py` P6).
4. OCR (tesseract, four quadrants, normal + inverted) of the atlases and of every 4K still against the project denylist + SPIDER / MARVEL / SONY / INSOMNIAC / VENOM ... (`ip_guard.py ocr`).
5. The blind critic reads every round for resemblance (`make_pairs_r11.py`: the notes ask explicitly).
6. The suit is evaluated on the game's own body mesh and UV atlas. Whether a masked, fitted-suit silhouette is itself too close to a studio character stays the owner's judgement (round 08, `SUIT_ORIGINALITY.md`).
