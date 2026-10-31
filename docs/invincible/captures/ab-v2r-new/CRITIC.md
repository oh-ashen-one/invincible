# In-game blind A/B: video2rig hero clips (new) vs shipped clips (old), 2026-10-31

Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation.

Same build, same scripted runs, default chase camera, 60 fps fixed step. New = `-WHHeroV2Clips=/Game/Invincible/HeroV2R/Anims`
(log: `override 3/12: AS_Hover AS_LandHero AS_Takeoff`); old = shipped `/Game/Invincible/HeroV2/Anims`. Pack built with
`tools/night1/abpack.py`; key unsealed after the verdict: B = new in both pairs. Critic: one Opus critic, pack only.

| pair | verdict | margin |
| --- | --- | --- |
| takeoff-hover (fl01) | TIE | none |
| slam-landing (fl11) | TIE | none |

- takeoff-hover: the run starts with the hero already rising (no crouch, push-off or touchdown on screen), so the new Takeoff is barely
  exercised. Both share an overhead-arm snap at 2.80-2.93 s. The new hover floats about 35 px higher with straighter legs and holds
  almost still (+-3 px), "a little more stiff and posed" than the old (which bobs about 18 px). This contradicts the matched CPU
  close-ups, where the new hover moved more; the game's hover playback needs a look before any re-run.
- slam-landing: new = "stronger head-first horizontal dive" and "a convincing low three-point landing ... real weight", but at
  3.65-3.95 s the left leg swings out sideways to hip height during the stand-up ("exactly the glitchy look the owner complained
  about"). Old = spread-eagle dive, an upright kneeling lunge with a fist overhead, clean but stiff.
- The leg swing is NOT in the exported clip: probing `LandHero_v2r_v1.glb` on the game rig, both feet stay on the floor
  (-0.77..-0.85 m armature) through the whole stand-up. It comes from the in-game playback/blend (likely the cut from the wide lunge,
  left foot 0.57 m out, into the next clip before the clip's own stand-up).
- Under the ship rule (visibly better, never a tie) NOTHING ships. Per the owner's rule a flat round = stop and report.
