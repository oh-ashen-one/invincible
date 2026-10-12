# P2 Characters, round 09: blind critic (Opus 5.5)

Homage fan game, not affiliated with Marvel, Sony or Insomniac. Coordinates are 1080p unless marked 4K.

## Scores
| Axis | Score | Evidence |
|---|---|---|
| Hero model & suit | **5** | No new capture. The pack head is an unsculpted egg. CH1 fails: pack hero-standing spans ≥0.92H. |
| Hero animation | **5** | CH6 met: head-bob peak 3.52 Hz. The run never starts, stops, turns or idles (CH10, §5). |
| Enemies | **6** | `street_fight_34` has 2 knockdowns; one stays grounded 4.67–7.30 s. `street_fight_wide` has 0. The red-hoodie thug guards in all 32 frames (0–7.75 s). |
| Civilians | **5** | The hijab walker's rear shin is horizontal, with the knee about 0.2 stature above the ground (0, 1, 2 s). The crowd pair is identical (mean diff 2/255). |
| Image quality | **4** | Mask holes are fixed (largest 18 px at 4K, was 198). New: the hero's left arm is an untextured grey limb at 1.30–1.50 s. The collar smear is still about 135×180 px at 4K. |

## A/B decisions
- **Ref vs ours:** the ref wins every pair. In fight-34 it has 5 or more enemies down plus launches at 9.0 s, against 1 down in ours. It also has lit streets against our blank plane.
- **Our progress pairs:**
  - progress-fight and progress-fight-still: **A**. B is an idle ring.
  - progress-tee-mask: **A**. B has holes of 195 and 98 px.
  - tee-mouth-3x: **B**.
  - progress-thug-collar and thug-collar-3x: **B**. The wedge is still there, just less pink.
  - knockdown-3x: **B**.
  - progress-crowd: **tie**.
- **Brand check:** no copied logo or text.

## Single biggest gap
In every 8 s fight clip, including `street_fight_wide`, show:
- at least 4 hit reactions, each moving the head or torso by 0.1 stature or more within 0.2 s of contact
- at least 2 knockdowns, with 2 enemies grounded at the same time for 1 s or more
- at least 2 distinct get-ups; one backward roll is reused at 3.2 s, 7.3 s and orbit 4.5 s
- no enemy holding the same guard for more than 2 s

## Secondary issues
1. Remove the default-material hero arm at `street_fight_34` 1.30–1.50 s (about 860–930, 450–520).
2. Fix the get-up pop. At 7.68→7.75 s the body yaws about 180° and goes from lying to crouched in 0.13 s, against the 0.15 s blend in CH10. The bat leaves the ground at 7.45 and reappears in the hand at 7.58. The hero's feet sink into the downed thug from 1.5 to 3.0 s.
3. Keep the walker's swing knee at 0.25 stature or higher, and let the coat hem follow the legs.
4. Fix the hair cards. `beard_face_4k` has a detached rear hair shell with a background gap. `hood_face_4k` has loose ribbon strands. Also give the hero head brow and nose volume.

## Verdict: **FAILS TARGET**
Lowest axis: 4.
