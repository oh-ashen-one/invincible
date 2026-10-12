# P3 round 26 -- hero suit in every capture and in a default launch (director hard line)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

- Suit content in this worktree: P2's 8 original suits of characters r14 (owner-approved 2026-10-02 11:35), built by `tools/build_suits_p3.py`
  from P2's committed generators (`tools/ue_char/hero_suit_r8.py` Tessera 8192, `tools/ue_char/suits/gen_suits.py` the other 7 at 4096) and P2's
  `Scripts/build_characters.py` helpers + 'skins' step: `DA_HeroSuits` = tessera verdant plum cinder glacier ash saffron sage.
  Before this round the worktree's `MI_Hero_Suit` / `T_Hero_*` were the 2026-09-29 import of the proxy's browser suit texture (red / blue
  with the back emblem) -- that is what every r24 / r25 capture showed.
- Pawn (`WebTravCharacter.cpp`): DA_HeroSuits entry 0 on the SpiderSuit slot at spawn, else MI_Hero_Suit, else the engine default
  material (never the proxy texture); `UWHHeroSuitSubsystem` then applies the start / saved suit every frame.
- Every r26 run logs `WH_TRAV hero suit: DA_HeroSuits entry MI_Hero_Suit` and `WH_SUIT start suit 0 (tessera) from default`
  (`CLIPS.md` column "suit (log)").
- `SUIT_SHEET_ALL.jpg`: 6 evenly spaced frames of every r26 clip (12 clips). `SUIT_SHEET.jpg`: the frame with the tallest hero box of
  every clip (cropped around the hero) + the two default-launch frames.
- Default launch (`default_launch_t3.jpg`, `default_launch_t7.jpg`): `Scripts/run_game.sh` on `/Game/Maps/Manhattan`, no traversal script,
  no -WHSuit / -WHSuitScript / -WHSuitPersist argument, 1920x1080, stills at 3 s and 7 s. Log:
      WH_SUIT 8 suits loaded: tessera verdant plum cinder glacier ash saffron sage 
      WH_SUIT 8 suits loaded: tessera verdant plum cinder glacier ash saffron sage 
      WH_TRAV hero suit: DA_HeroSuits entry MI_Hero_Suit
      WH_SUIT set 0/8 tessera (default) changed=1 t=0.401 frame=1 apply_ms=0.08
      WH_SUIT start suit 0 (tessera) from default, persist=0 live=0
  (an interactive launch reads `HeroSuitId` from GameUserSettings.ini; this worktree has none saved -> suit 0, Tessera). The project's
  `GameDefaultMap` (/Game/Maps/Foundation_Test) spawns F1's cylinder pawn (no hero mesh).
