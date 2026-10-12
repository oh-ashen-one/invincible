# P6 City life: IP exclusions (owner rule: we copy nothing)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Nothing here is meant to infringe. See `DISCLAIMER.md`.

Source of the vehicle liveries: `public/assets/city/tex/vehicles_atlas2.webp` (2048 x 2048, an image-generation pack used by the browser build; the vehicle GLB has
no materials, everything is drawn from this atlas by UV). The Unreal port never imports the original: `tools/life/prep_vehicles.py` writes a sanitised copy
(`_scratch/life/vehicles/vehicles_atlas_clean.png`) and only that copy is imported as `/Game/Life/Vehicles/T_VehiclesAtlas`.

## Excluded (painted out of the atlas, never selectable)

The taxi-topper ad tiles are the 2 x 4 grid in the top-right quarter of the atlas (tile k: x = 1024 + (k mod 2) * 512, y = floor(k / 2) * 170, 512 x 170 px). The
material picks one of tiles 0, 2, 4, 6 per taxi (`M_LifeVehicle`, part 15), so 1, 3, 5, 7 are unreachable AND their pixels are replaced by a plain grey panel.

| cell | content read (OCR + eyes) | reason | action |
|---|---|---|---|
| ad tile 1 | "DAILY BUGLE - THE TRUTH, EVERY MORNING" newspaper masthead | Marvel-universe brand | blanked + never selected |
| ad tile 3 | "ROXXON ENERGY - POWERING NEW YORK" | Marvel-universe brand | blanked + never selected |
| ad tile 5 | "OSCORP - A HEALTHIER TOMORROW" | Marvel-universe brand | blanked + never selected |
| ad tile 7 | "SKYLINE SNEAKERS - RUN THE CITY", a running shoe with an orange swoosh-like flash | resembles a real sportswear mark | blanked + never selected (precaution) |
| bus destination band | "M15 SELECT BUS 2 AV" | a real transit route name | repainted "CROSSTOWN LOCAL" |
| bus agency band | "NYC TRANSIT" | a real transit agency | repainted "CITY TRANSIT" |

## Reviewed and kept

| cell | content | why kept |
|---|---|---|
| ad tiles 0, 2, 4, 6 | "Fuhgeddaboutit Pizza", "Wolf & Sheep - now on Broadway" (invented musical), "Empire Bagel Co.", "Hudson Injury Law" | generic or invented business names, no logo of a real company (the bagel and law tiles carry a generic skyline silhouette) |
| truck cells | "METRO LOCAL SHIPPING" (212-555-0147), "BRONX BROS PLUMBING & HEATING" (718-555-0162), "EMPIRE MOVING & STORAGE" (1-800-555-0199) | invented names with reserved 555 numbers |
| tour bus band | "BIG APPLE SIGHTSEEING" | descriptive text |
| taxi cells | "NY TAXI" / "KGT-4821" plates | generic descriptive text; the plate number is invented (the "NYC TAXI" door / roof label was reviewed and kept in rounds 01-02, repainted in round 03, see below) |
| interior cards | dark cabin photographs with a driver / passengers | generated imagery, not identifiable persons; visible only through tinted glass |

## Crowd

The 20 citizens are the browser's own crowd pack (`public/assets/city/npc/citizens.*`, invented people, no lettering); they are exported through P2's exporter
(`tools/ue_char/eval/citizens.py`, redirected by `tools/life/citizens_fbx.py`). No brand text on the clothing was found in the atlas tiles at review scale. `tools/life/citizen_variants.py` only recolours these tiles (clothes hue / brightness; round 02: hair,
beard and skin tone through the head masks of `tools/life/citizen_headmask.py`), it adds nothing.

## Round 02 additions (nothing new is drawn or imported from a third party)

| item | what | IP note |
|---|---|---|
| signal lenses | `AWHLifeTraffic::BuildSignals`: flat emissive discs (engine cylinder mesh, procedural material `M_LifeSignal`) on P1's signal props | no texture, no lettering |
| head variants | hair / beard / skin / head-covering recolour of the 20 crowd citizens, four recolours per citizen (100 looks) | recolour of the existing pack only, nothing drawn or imported |
| buses on screen more often | same bus mesh and atlas cells as round 01 (destination band repainted "CROSSTOWN LOCAL", agency band "CITY TRANSIT"; ad panel = the reviewed "Hudson Injury Law" tile) | unchanged, see the table above |

## Round 03 additions

| item | what | IP note |
|---|---|---|
| taxi label | the black rounded-square sticker on the taxi door / roof-light cell of the atlas (x 768-1024, y 1024-1150 of the 2048 px atlas) read "NYC" + "TAXI" (the NYC taxi mark, flagged by the round 02 critic). `tools/life/prep_vehicles.py` repaints the three letters as "CITY" (Helvetica Bold, taxi yellow on the same black square); the word TAXI stays (a generic word) | the imported atlas no longer carries "NYC TAXI" |
| crowd fill light, crosswalk clearing, curb gaps, keep-right lanes | code / lighting only (`Source/WebHomage/Life`), no art or text added | none |

## Verification (re-run each round)

`python3 tools/life/ip_check.py <sanitised atlas png> <round>/stills/*.jpg` OCRs the sanitised atlas cell by cell and the 4K captures against the denylist
(Oscorp, Osborn, Roxx, Bugle, Hydra, Stark, Wayne, Marvel, M15, Select Bus, NYC Transit, MTA, Skyline Sneakers, ...). Round 01 result: `round-01/ip_check.txt`; round 02 (atlas + final S1 / S2 4K stills + street and signal clip frames): `round-02/ip_check.txt`, 0 hits.
Control: the unsanitised atlas hits BUGLE and ROXX, so the checker sees these cells.
