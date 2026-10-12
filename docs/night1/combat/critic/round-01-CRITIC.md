# P5 Combat r01 — independent critic (pixels only)

Our clip: combat/docs/night1/combat/round-01/fight25_1080p60.mp4 (ours@t). Refs: refs/combat/clips/street-combo__nm_0214-0224, street-fight-cars__nm_0500-0510, plaza-fight__dn_0818-0828, night-street-fight__nt_0755-0805; stills group-fight-nm, air-combat-nm.

## Scores (0-10 vs Marvel's Spider-Man 2)
1. Impact & feedback: **3**. No hit-stop. The whole-frame diff at 30 fps has 0.0% of frames below 0.3; the refs have 0.3-2.7%. A 60 fps hero crop through contacts @3.25-3.60, @13.10-13.45 and @18.35-18.70 never goes below a diff of 3.4, so no frame is held. Impact VFX is an opaque white disc about 12% of frame width: @3.40-3.47 it covers the contact and @13.23-13.33 it fills the middle of the frame. The black-jacket thug struck @3.30-3.45 shows no flinch. The launch @18.55-18.85 does read, and downed enemies stay down.
2. Move set & flow: **4**. Present: jab combo, flip dodges (@5.3, @14.0), an uppercut-launch that carries the enemy up (@18.4-18.9), web-stick to a wall (@16.6-17.0) and web shots (@8.8-9.4). Missing: web-strike zip-to-enemy, an air juggle beyond one hit, and any finisher. The leap @23.9-24.5 floats for 0.6 s with no strike arc.
3. Enemy behaviour: **3**. For 0.93 s (@8.93-9.87, 29 frames under the motion floor) three thugs stand in guard and nobody attacks. The bat thug stands idle while the hero lands beside him (@24.0-24.5). No telegraph indicator appears over any attacker: the gunman fires @17.1-17.2 with no warning. Enemies in frame (hand count, 2 fps sheet): 4-6 in 1-4 s, then 1-3 from 6 s on. CH11 needs 5-7, and the refs show 7-9. The brute @18.2 is not bulkier than the thugs. There is one getup crawl @23.9-24.5.
4. Combat camera: **3**. The hero is cut at the frame edge @5.5-6.5 and @12.0-13.3 (only the torso is visible at the bottom border), a bat fills the foreground @13.2, and the camera sits at eye level instead of mid-high about 5 m back. There are no cinematic cuts. A whole-frame diff of 25.8 @16.73 is a camera snap.
5. Spectacle & variety: **3**. The clip reads as a sparse duel sequence, not a brawl. The ref street-combo shows 7-9 enemies, web tethers and gadgets in 10 s. Ours has about 1 of those beats every 3-4 s (median frame motion 5.4 vs 7.9-13.7 in the refs).

## A/B (judged on quality, then identity guessed)
- street-combo: **A better**, because of dense choreography, a web-line strike, launches and a readable ring of attackers. B is sparse and floaty. Guess: B is ours.
- street-fight-2: **B better**, for the same reasons (tethers, a car-side slam, 8+ enemies). Guess: A is ours.
- group-still: **B better**. It shows 6 spaced enemies, a web-strike line and a mid-high camera. In A the hero is cut off at the bottom and only 2 enemies show. Guess: A is ours.
- air-still: **A better**. It shows a dynamic airborne pose with motion blur. B is a grounded standoff, so it does not show air combat at all. Guess: B is ours.

## Ranked gaps (testable)
1. **Hit-stop plus a readable reaction on every contact.** Freeze hero and victim for 3-5 frames at 60 fps (50-80 ms), then play a directional flinch or stagger within 2 frames, with the victim's root displaced at least 0.3 m. Replace the opaque disc with a small additive spark burst (no more than 3% of frame area, faded within 6 frames). Ref: street-combo @0.5-1.5. Test: a 60 fps victim crop diff below 1.0 for at least 3 consecutive frames at each contact, and flash-area pixels below 3%.
2. **Enemy aggression and telegraphs.** In a 5-7 enemy ring, no 1.0 s window should be without an attack windup. Each attacker shows an indicator over its head at least 0.4 s before the hit, and gunmen show a line or indicator before they fire. Ref: plaza-fight, night-street-fight. Test: in a 30 s capture, the maximum gap between attack starts is 1.0 s or less, and at least 5 enemies (5% or more of frame height) are in frame for 80% of frames (CH11).
3. **Combat camera.** Place the camera mid-high, 4-6 m back, pitched down 15-25°, and frame the hero plus the 3 nearest enemies. The hero's bounding box must never touch the frame edge, and no prop or enemy may occlude more than 15% of the frame. Ref: group-fight-nm, street-fight-cars. Test: per-frame hero bbox margin at least 5% on all sides in 100% of frames.

## Secondary
- There is no finisher beat (no camera cut or slow-mo takedown).
- The air combo stops after the launch (@18.9): there is no follow-up juggle.
- The brute is not distinguishable by silhouette (CH15, CH13 variety).
- The white-sky, low-contrast test street flattens the silhouettes and adds to the low readability.

## Verdict: **FAILS** (lowest axis 3; every axis is below 8)
