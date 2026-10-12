# Owner playtest handoff — 2026-10-04

Owner request: prepare the latest accepted polished 4K version, **DO NOT OPEN** an Unreal instance until the owner explicitly asks.

Worktree: /Users/midir/sm2-n1/owner-playtest-20261004
Branch: codex/owner-playtest-20261004
Base: 7094940146da974955a6daed8b4d9ce3ea16cc26 (Opus-5.5-Loop-Night-1)

Prepared: current integration Content + complete characters r17 + the preserved accepted TerrainR5b content checkpoint. Native module rebuilt successfully; required assets and suit references checked offline. See tools/owner_preview/README.md and unreal/WebHomage/Saved/OwnerPreview/prepared.json.

Two opt-in changes: WHPreparedPlaytest keeps requested ResX/ResY and starts at Cinematic/100%; the R5b terrain map adds current Life_Actors at world initialization. Other launches keep their prior behavior. This is not merged into the original integration branch.

NOT DONE: no editor, game, commandlet or renderer launch; no runtime asset-load check, visual verification, FPS measurement or owner gameplay acceptance. Upstream night and full-island work remain separate. The R5b scene layout predates city r11, while referenced City asset content is current. Inspect that combination on first launch.

The shared GPU PAUSED marker remains untouched from the prior freeze. No automatic launch or automation was created. Before opening on a new owner request, verify live health and recover the shared pause through the approved protocol; the launcher fails closed while it exists. Source checkouts of other tasks were not edited; their processes were not stopped.

Open only when requested: python3 tools/owner_preview/play.py --launch
Check only: python3 tools/owner_preview/play.py

Do not remove this prepared checkout while the owner is waiting to test it. Content/Binaries are local generated artifacts needed for that test; source and the preparation recipe are pushed on the task branch. The original integration handoff remains in its checkout and in Git at the base commit.
