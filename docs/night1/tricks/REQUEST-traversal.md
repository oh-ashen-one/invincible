# Request to traversal (P3 / B) from Tricks (C)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Tricks owns `WebTravFlips.{h,cpp}`, the flip programs / clips (`docs/night1/traversal/blender/make_flip_shapes.py` keys) and the trick input
mapping, but the hooks that CALL them live in traversal-owned files. Round 1 needs these two one-line hooks (not done by C):

1. **Auto / player choice uses the new programs.** `UWebTraversalComponent::ChooseTrick` (WebTraversalComponent.cpp, the `!bLegacyTricks`
   branch) still cycles `SkyP = {backDouble, frontPikeSwan, corkscrew}` / `LowP`. Replace both lists with
   `WebFlips::ChooseForInput(InD0.Y_forward, S.TrickLat, S.AutoFlipK++, Air, S.LastTrickName)` (stick forward / lateral at the trick press;
   `Air` = `AirTimeToClear()` for a plain release, `<= 0` for flow / sky flips whose air is solved) and pass the result through `FitFlip`.
   Until then only scripts (`"flip": "a,b,..."`) reach the 8 new programs (frontSingle, frontDouble, backPike, backLayout, barani, fullTwist,
   rudi, backTripleChain).
2. **`FitFlip`'s fallback** returns `backSingle` when the wanted program does not fit; with 12 programs it should ask
   `WebFlips::ChooseForInput(0, 0, K, Air, Last)` for the longest one that fits instead.

Nothing else in traversal is needed: programs, shapes, tempo variation and the pose logger are inside WebTravFlips.cpp.

## Seen in the round-1 reel (traversal-owned, not fixed by C)
3. **Trick camera inside a facade at an avenue turn.** `t60_trick_reel` ~13.6-13.9 s (frontDouble's kick-out while the chain turns from the
   y -560 street into 5th Av at x ~250): the held 3/4 trick view sits inside / against the corner building's facade (blurred brick fills
   the frame). The held world azimuth (TRICK_CAMERA_SPEC) does not re-check obstruction when the travel heading turns under it.
4. **A flip whose catch swings into a corner tower starts a vertical wall-run** (probe, a west turn into the 10 m cross street at y 80
   mid-backTripleChain: 30 s of wall-run up a 166 m tower). Not in the reel (route changed), noted for the corridor / catch logic.

## After traversal r26 (Tricks C r01 resume, 2026-10-03)
5. **r26 critic T4 gap (a_swing_chain 12.4-13.1 s, held fallCalm).** A trick program can fill it only if the release that precedes it
   asks for one: the shortest release program at base tempo (`WebFlips::FindBase(..)->CatchT()`) is backLayout / backPike, ~1.2-1.3 s,
   so a 0.7 s fall needs either a re-attach (traversal) or the hook in item 1 with `Air` from `AirTimeToClear()` (ChooseForInput
   returns NAME_None when nothing fits). In the tricks reel the same pattern appears after a program ends before the catch
   (e.g. probe 13.35 s: backLayout ends, node `air_fallCalm` until the next web); WebTravFlips now keeps the final reach / kick-out moving
   while the flip node is active, but the fallCalm node itself is traversal's.
6. Items 1-2 are still open (the reel reaches the 8 new programs through its script's `flip` list only).
