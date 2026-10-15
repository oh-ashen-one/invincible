# Invincible flight conversion — results

Owner request 2026-10-15 (Hari): replace Spider-Man / web-swinging in the UE 5.8 WebHomage project with a flying hero in the style of Mark Grayson ("Invincible" comic homage, no cape). Unofficial, non-commercial homage; see `DISCLAIMER.md` and `LICENSE` (the original author attribution to Shikhar / xikhar stands).

## Status: source only, nothing verified

| Item | State |
|---|---|
| Flight controller (takeoff, hover, fly, boost + sonic boom, bank, pitch, instant stop, dash, slam, superhero landing + crater) | written, **not compiled** |
| Through-building flight (destruction proxies, glass, dust, slow-mo) | written, **not compiled** |
| Crowd flee / look-up (isolated brain hook) | written, **not compiled** |
| Collateral counter + rescue clock (fire, crane, bus) + HUD | written, **not compiled** |
| Flight poses in the anim instance | written, **not compiled** |
| Invincible-homage suit / character | see `character/README.md`; **nothing generated or rendered** |
| 17-case flight capture suite + critic pass | case files and runner written; **not run** |
| Staged owner copy with `Play-Invincible.command` | stager written; **not staged** |
| Omni-Man-style boss (stretch) | not started |

The builder ran in a cloud container that could not reach the Mac Studio, so there are no builds, stills, clips, telemetry or critic verdicts yet. When the studio session produces them, this page gets:

- before / after stills (web-swing hero vs. flying hero, same Times Square shots),
- the fixed-step clips of the 17 cases with per-case checks (`captures/PLAN.md`),
- the independent critic's verdict with quoted defects,
- a clear note that **fixed-step capture footage is not real-time FPS proof**; real-time performance is measured only from a game launched inside the logged-in desktop session.

No owner gameplay acceptance is claimed or implied by anything on this branch.
