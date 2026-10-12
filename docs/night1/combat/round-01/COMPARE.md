# P5 combat round 01: Unreal fight vs browser fight (same script)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Unreal: `round-01/ue`  |  browser: `round-01/browser`

Both runs: fixed 1/60 s real step, seeded RNG, the same beats at the same REAL times. The worlds differ (Unreal: Combat_Street test street; browser: an open street spot in the browser city) and each engine has its own RNG stream, so the fights diverge after the first random choice; compare the rules (damage, hit-stop, slow-mo, move choice, AI tokens), not frame-exact positions.

## Totals

| metric | Unreal | browser |
|---|---|---|
| frames | 1620 | 1621 |
| real_s | 27.0 | 27.017 |
| game_s | 22.342 | 25.454 |
| enemies | 6 | 6 |
| enemies_alive | 2 | 3 |
| hero_hp | 67 | 31 |
| hero_focus | 2.45 | 0.79 |
| damage_taken | 33 | 69 |
| hits | 28 | 23 |
| whiffs | 0 | 0 |
| kos | 4 | 3 |
| launches | 2 | 1 |
| air_hits | 6 | 3 |
| finishers | 2 | 2 |
| dodges | 3 | 3 |
| perfect_dodges | 3 | 0 |
| web_hits | 6 | 6 |
| enemy_melee_hits | 1 | 4 |
| shots | 6 | 14 |
| shot_hits | 4 | 4 |
| hitstops | 27 | 26 |
| slowmos | 8 | 5 |
| min_timescale | 0.05 | 0.05 |
| slowmo_real_s | 7.567 | 4.617 |
| beats | 40 | 40 |
| beats_fired | 40 | 40 |
| slow-mo real s (telemetry) | 7.57 | 4.62 |
| min time scale (telemetry) | 0.050 | 0.050 |

## Beat by beat (first move started within 0.7 s; first hit / action event within 0.9 s)

| t (s) | beat | key | Unreal move (+s) | Unreal event | browser move (+s) | browser event |
|---|---|---|---|---|---|---|
| 1.50 | combo A 1 (jab/cross) | attack | strike (0.0) | action attack: cross: strike flyingKick->e4 gap 5.3 | strike (0.0) | move strike -> e4 |
| 1.95 | combo A 2 | attack | - (None) | action attack: hook: strike punch3->e4 gap 0.0 run 0.00s | - (None) | hit light -> e4 dmg 11 hp 30 state stagger combo 2 focus 0.16 |
| 2.40 | combo A 3 | attack | - (None) | action attack: kick: strike kick->e4 gap 0.0 run 0.00s | down (0.467) | hit light -> e4 dmg 11 hp 19 state stagger combo 3 focus 0.26 |
| 2.85 | combo A ender | attack | hit (0.333) | action attack: riser: strike uppercut->e4 gap 0.1 run 0.00s | down (0.017) | move down -> e4 |
| 3.65 | counter | attack | strike (0.0) | action attack: cross: strike punch2->e4 gap 2.6 run 0.25s | - (None) | - |
| 4.60 | combo B 1 | attack | strike (0.0) | action attack: hook: strike punch3->e6 gap 2.6 run 0.25s | dodge (0.217) | dodge plain threat=none |
| 4.66 | perfect dodge 1 (slow-mo) | dodge | strike (0.333) | dodge PERFECT threat=e3 | dodge (0.15) | dodge plain threat=none |
| 5.00 | launcher (hold) | attack | strike (0.0) | action attack: jab: strike punch1->e6 gap 2.2 run 0.21s COUNTER | strike (0.2) | move strike -> e6 |
| 5.95 | air combo 1 | attack | air (0.15) | action attack: airStrike seg 0 -> e6 | strike (0.0) | move strike -> e4 |
| 6.30 | air combo 2 | attack | air (0.233) | action attack: airStrike seg 1 -> e6 | dive (0.067) | move dive -> e4 |
| 6.65 | air combo 3 (slam) | attack | airStrike (0.0) | action attack: airStrike seg 2 -> e6 | strike (0.0) | move strike -> e4 |
| 7.80 | web shooter -> gunman e2 (disarm) | web | hit (0.017) | action web: webShoot -> e1 | - (None) | web hit e2 web 0.17 state hold |
| 8.15 | web shooter -> e2 | web | hit (0.2) | action web: webShoot -> e1 | - (None) | web hit e2 web 0.50 state hold |
| 8.60 | web shooter -> gunman e5 (disarm) | web | - (None) | action web: webShoot -> e5 | - (None) | web hit e1 web 0.34 state approach |
| 8.95 | web shooter -> e5 | web | - (None) | action web: webShoot -> e5 | - (None) | web hit e6 web 0.34 state hold |
| 9.70 | web strike (E) | strike | webStrike (0.0) | action strike: webStrike -> e2 10.3 m | webStrike (0.0) | move webStrike -> e2 |
| 9.90 | perfect dodge 2 | dodge | - (None) | hit strike -> e2 dmg 20 hp 18 KNOCKED  combo 1 focus 1.63 | - (None) | hit strike -> e2 dmg 20 hp 18 state knock combo 1 focus 0.85 |
| 11.40 | combo C 1 | attack | strike (0.0) | action attack: cross: strike punch2->e1 gap 3.8 run 0.34s | strike (0.0) | move strike -> e1 |
| 11.85 | combo C 2 | attack | - (None) | hit light -> e1 dmg 10 hp 40 stagger  combo 2 focus 1.72 | dive (0.0) | move dive -> e1 |
| 12.30 | combo C 3 | attack | strike (0.45) | action attack: jab: strike punch1->e1 gap 0.0 run 0.00s | strike (0.0) | move strike -> e1 |
| 12.75 | combo C ender | attack | strike (0.0) | action attack: roundhouse: strike kick->e1 gap 0.0 run 0.00s | dodge (0.617) | hit light -> e1 dmg 9 hp 5 state stagger combo 4 focus 1.28 |
| 13.36 | perfect dodge 3 | dodge | - (None) | dodge PERFECT threat=e5 | hit (0.683) | move hit -> e1 |
| 14.60 | finisher (Q) | finisher | finisher (0.0) | cine finisher e2 1.45 s | finisher (0.0) | move finisher -> e6 |
| 16.76 | web brute 1 | web | - (None) | action web: webShoot -> e3 | - (None) | web hit e3 web 0.34 state hold |
| 17.15 | web brute 2 (stun) | web | strike (0.4) | action web: webShoot -> e3 | strike (0.4) | web hit e3 web 0.66 state hold |
| 17.55 | strike stunned brute | attack | strike (0.0) | action attack: cross: strike punch2->e3 gap 1.6 run 0.16s | strike (0.0) | move strike -> e3 |
| 17.95 | launcher brute (hold) | attack | launch (0.233) | action attack: hook: strike punch3->e3 gap 0.0 run 0.00s | strike (0.017) | move strike -> e3 |
| 18.90 | air 1 | attack | airStrike (0.0) | action attack: airStrike seg 0 -> e3 | airStrike (0.0) | move airStrike -> e3 |
| 19.25 | air 2 | attack | airStrike (0.0) | action attack: airStrike seg 1 -> e3 | airStrike (0.0) | move airStrike -> e3 |
| 19.60 | air 3 (slam) | attack | airStrike (0.0) | action attack: airStrike seg 2 -> e3 | airStrike (0.0) | move airStrike -> e3 |
| 20.50 | counter 2 | attack | strike (0.0) | action attack: jab: strike punch1->e1 gap 3.3 run 0.30s | strike (0.0) | move strike -> e1 |
| 20.83 | perfect dodge 4 | dodge | dodge (0.0) | dodge PERFECT threat=e5 | dodge (0.0) | move dodge -> e1 |
| 22.00 | combo D 2 | attack | strike (0.0) | action attack: cross: strike punch2->e1 gap 1.9 run 0.19s COUNTER | strike (0.0) | move strike -> e1 |
| 22.40 | combo D 3 | attack | - (None) | action attack: hook: strike punch3->e1 gap 0.2 run 0.00s | - (None) | hit light -> e1 dmg 10 hp 0 state knock combo 6 focus 1.12 |
| 22.80 | combo D ender | attack | finisher (0.467) | action attack: jab: strike punch1->e1 gap 1.0 run 0.12s | finisher (0.467) | hit light -> e1 dmg 11 hp 0 state knock combo 7 focus 1.23 |
| 23.26 | finisher 2 (brute) | finisher | - (None) | cine finisher e1 1.45 s | - (None) | - |
| 24.75 | combo E 2 | attack | strike (0.6) | action attack: cross: strike punch2->e5 gap 3.0 run 0.28s | strike (0.683) | cine pin e1 1.00 s |
| 25.20 | combo E 3 | attack | strike (0.15) | action attack: cross: strike punch2->e5 gap 3.0 run 0.28s | strike (0.233) | cine pin e1 1.00 s |
| 25.30 | combo E 1 | attack | strike (0.05) | action attack: cross: strike punch2->e5 gap 3.0 run 0.28s | strike (0.133) | move strike -> e5 |
| 25.65 | combo E ender | attack | - (None) | hit light -> e5 dmg 10 hp 28 stagger  combo 16 focus 2.30 | - (None) | hit light -> e5 dmg 9 hp 29 state stagger combo 9 focus 0.67 |

Beats whose first move matches: **26 / 40**.

