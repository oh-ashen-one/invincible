# P2 Characters, round 10: blind critic (Opus 5.5)

Homage fan game, not affiliated with Marvel, Sony or Insomniac. Coordinates are 1080p unless marked 4K.

## Scores
- **Hero model & suit: 5.** CH1 is unproven: pack hero-standing spans 0.92H. The head is an egg. The lattice panels are asymmetric. In `street_fight_34` at 1.30–1.50 s, the forearm sinks into the chest.
- **Hero animation: 5.** CH7 is met: lean is 26° (hero-run 1.0 s). The run is a treadmill loop with no start, stop or turn (CH10, §5).
- **Enemies: 6.**
  - Met: CH11–13 (7 enemies; bat, crowbar and pistol).
  - Met: 2 enemies grounded together in every clip (34 2.5–4.25 s, wide 2.75–4.25 s, orbit 3.5–5.25 s).
  - Failed: blue-cap holds his guard 0–3.25 s (diff ≤20/255). Red-jacket holds his 0–5.0 s (≤34/255). Everyone is packed within 1 hero-height.
- **Civilians: 5.** The clip is reused. The walker's knee is at 0.15 stature (0–4 s), and the coat hem is rigid.
- **Image quality: 4.** The grey arm is fixed. Defects at 4K:
  - `hood_face`: two overlapping hair meshes with a seam about 570 px long.
  - `beard_face`: a flat card of at least 125×220 px at (2480,380).
  - `thug_face`: a collar wedge of 72×151 px at (1746,1358).

## A/B decisions
- **Ref vs ours:** the ref wins every pair. In fight-34 it has 5 or more enemies down at 8.5–9.5 s, spaced 3–6 m apart. Ours is a tight ring on a blank plane.
- **Our progress pairs:**
  - progress-fight-34: **B**. It has 2 knockdowns, against 1.
  - progress-fight-wide: **A**.
  - progress-fight-still: **A**.
  - arm-3x: **A**.
  - hero-limbs-34: **B**. The other side has the grey limb.
  - hero-limbs-wide and hero-limbs-orbit: **tie**.
  - thug-collar-3x: **tie**.
  - beard-hair-3x: **B**. A has the card.
  - hood-hair-3x: **B**.
- **Brand check:** no copied logo or text.

## Single biggest gap
Give every head one hair asset. On `hood_face`, `beard_face` and `tee_face` at 4K, there must be:
- no colour seam longer than 40 px inside the hair
- no detached opaque card wider than 20 px
- no background showing between hair and skin
- no skin-toned blob larger than 15×15 px in the `thug_face` collar

## Secondary issues
1. Spread the enemies to 2–4 m from the hero. No enemy may hold a guard for more than 2 s (torso diff above 30/255).
2. Fix the forearm going through the chest. Make the lattice panels symmetric.
3. Make a new CH1 still at 0.48–0.62H, plus run start, stop and turn clips.
4. Re-capture the crowd with the swing knee at 0.25 stature or higher.

## Verdict: **FAILS TARGET**
Lowest axis: 4.
