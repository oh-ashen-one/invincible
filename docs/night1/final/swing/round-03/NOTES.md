# Round 03 (builder SW)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Renders now run with `-WHTravMask` (hero-only depth pass; px_top/px_bottom, 1080 scale, previous-frame mask) and `-WHSuit=tessera`. `final_check.py` line **P1** = hero height by pixels (swing 0.15-0.30, air/trick 0.18-0.36, >= 90 % of 10 fps samples).

## Hero suit (report only)
Round 00-02 renders did NOT use Tessera: the capture profile's `Saved/Showcase/User/Saved/Config/MacEditor/GameUserSettings.ini` has `HeroSuit=3 / HeroSuitId=cinder`, and the route logs show
`WH_SETTINGS suit saved ... HeroSuitId=cinder` / `WH_SUIT start suit 3 (cinder) from settings`. The pale-grey "mannequin" was Cinder, not a fallback texture. Round 03 passes `-WHSuit=tessera`
(`WHHeroSuit.cpp` reads it before the settings): the hero is teal / black / orange like SUIT_SHEET.jpg. (The settings file is not touched.)

## Camera
Chase lens narrowed: `CamFovScale 0.862` (50 deg vertical at the 58 deg menu default), speed add 6 deg (was 13 -> 8 -> 6), free-flight pitch cap 10 deg down, dive pitch cap 14-20 deg, flip camera
FlipDist 5.4 / FlipDistMax 7.5 / FlipDistCompact 3.8 / FlipExtK 4.0, yaw slew <= 120 deg/s kept. Telemetry bbox vs pixels: s1 `hero_bbox_h` median 0.29 vs pixel median 0.23-0.28.
P1 per clip is in `CHECK.txt`: s1 and s5 pass (swing 95 %, air 96 %); s2, s3 (flow), s3b, s4 fail (see CHECK.txt for the percentiles). Tricks vary 0.12-0.48 of the frame with the pose (tuck vs layout); the
flip camera follows hero extent but not enough to hold 0.18-0.36 on 90 %.

## Flips / body
- Diff r01 -> r02 touching trick poses: the free-fall lean cap (Orient, outside tricks), the air-cycle flavors (PickNode, only after a release when no flip program plays), glide -> fallCalm, the swing-life layer
  (`Mode == Swing` only). None changes an active flip program (A6 passes with 7 distinct end clips in the continuous s3; A7 94 %: one 1-frame shape segment). What read as the "prone superman" is the post-flip free fall
  (lean from velocity: a 40 m/s vertical fall leaned 80 deg). Cap lowered to 63 deg (dive 46 deg), air-cycle flavors cut into segments <= 0.35 s (A4 s4 pass).
- s3 is now ONE 24 s flow chain (a flow flip on each release, stick changing): 9 tricks, 7 distinct end clips (frontSingle, frontPikeSwan, barani, wallFront, rudi, corkscrew). s3b = the old 7 cases.
- The 1.2 s "dangle" in s2 10.0-11.2 is a wall run (climbing 14 m/s up the facade); not changed.

## Anchors / release
`AnchorAltDeg 8` in the chain tune (was 15): s1 anchors median 38 deg off the travel heading (6 of 15 above 45; r02: 55 deg, 11 of 15), elevation median 20 deg; web-on 77 %, longest gap 0.40 s.
Released strand on a dev render (s4 1.7-2.2 s): visible near the hero, thin and slack for ~0.2 s, gone by ~0.3 s.

## Open
W4 on s2/s3 (up to 2619 deg/s after flips), s2 W2/W3/W9/W10 (case-specific), W5 by day, A5 catch timing, F11, trick/air framing P1 on s2/s3/s3b/s4.
Launch note: `with_holder.sh` gave up (10 refusals) on the first case of s3b and s2 in the batch run; each was re-invoked once and ran normally.
