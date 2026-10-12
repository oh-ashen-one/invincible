# Flips brief — owner request 2026-09-29 23:45 (P3 round 11 target, after round 10 lands)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.

**Owner, verbatim intent:** the flips must look like a gymnast — beautiful, controlled, athletic. Not a spinning ragdoll.

**Reference:** owner screen recording (24 s, 610×556, 50 fps), local only — never committed (footage of the real game):
`/Users/midir/sm2-n1/_scratch/refs/owner/flips_owner_2026-09-29.mov` + contact sheets `sheet_01..04.jpg` (3 fps).

**What the reference shows**
- Front and back flips off a swing release, often chained 2–3 per release; corkscrew twists while falling.
- Clear, held gymnastic shapes: tight tuck, pike, layout / spread-eagle, and an arched "swan" between rotations. Every pose reads as a silhouette.
- Wall-run up a facade → flip off the edge; point-launch over a roof edge with an inverted pass above the roof; edge grab → vault/flip → swing away.
- Rotation eases in and out (fast through the middle, slows into the held pose); limbs lead and follow (overlapping action); landing into the next web catch is continuous — no pop.

**Before building: measure the clip** (numeric SPEC, like docs/night1/traversal/SPEC.md): rotation rate (deg/s) per trick, rotations per release, hold time of the extended pose, phase of the swing at which the trick fires, body-axis tilt of the corkscrews, hero size on screen during tricks, camera behaviour (does it track the rotation or stay level?).

**Build:** P3 traversal worktree (owner of Source/WebHomage/Traversal + WebTravAnimInstance). Opus 5.5 high. Blender for any new keyed trick clips (retarget onto the hero rig), procedural blending in the anim instance for the chaining / eases.

**Judge:** fresh blind Opus critic, anonymous A/B vs the owner clip (abpack.py), moving clips not stills, scoring shape quality, rotation timing/easing, chaining, continuity into the next swing, and "gymnast beauty". A round closes only on MEETS TARGET with evidence.

## Also queued (owner, same session)
- Mouse look far too fast in the Unreal game (MouseRadPerUnit 0.033 was tuned for the browser). Fix later: find the value that feels right with a real mouse (~0.011 start), expose a sensitivity setting.
