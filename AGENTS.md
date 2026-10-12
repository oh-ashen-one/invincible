# PROJECT CLOSED — owner-authorized main merge, 2026-10-12

The owner explicitly declared this project complete and authorized merging all current work into main and deleting obsolete branches/worktrees. This supersedes the earlier unmerged/active-pass instructions below, which are historical records. Do not resume a refinement loop or fix known issues without a new request. The later owner request to play in Times Square authorizes that play session; do not close it as part of the earlier shutdown request.

Use main as the canonical source. Read `docs/controls/project-closeout-20261012/CLOSEOUT.md` for the closure, preservation manifests and known E-targeting/ledge-trap issues retained in the accepted build. The final local owner artifact is `/Users/midir/SpiderMan-Playtest-Feedback-20261012`; `Play-TimesSquare.command` launches the requested plaza start. Previous owner copies and authoring/reference assets remain preserved. No automatic Unreal launch or work loop is authorized after the owner's play session ends.

---

# Active owner playtest feedback — 2026-10-12

Continue PR4 on `codex/manual-camera-20261012` from c7c07fb8 in `/Users/midir/spider-man-2-playtest-feedback-20261012`. Owner has NOT approved merge. Scope: remove all gameplay/debug screen text while retaining readable settings; keep ray tracing/geometry features enabled; remove confusing inactive VSync control in forced-playable profile; improve enabled camera shake; show white web only during active swinging; split camera-facing forward boost from targeted perch zip; stationary ground/perch rest must use spider crouch. Existing camera fixes stay.

Existing bindings already separate E/Triangle zip and Q/L1 quick boost; retain these and make Q/L1 a true camera-direction boost with no nearest-anchor steering. E/Triangle remains targeted zip/perch. Root coordinates code ownership: UI worker Core/WHSettingsMenu.cpp/h + WebHomagePlayerController.cpp/h; traversal worker WebTraversalComponent.cpp/h + WebTravCharacter.cpp/h; rest worker Traversal/Anim/WebTravAnimInstance.cpp/h. Root owns WebTravCamera.cpp/h, build/runtime, docs and integration. Coordinate any cross-file edits. Workers use owner-selected GPT-6.1 Sol/xhigh; no worker engines/builds/Git mutations. Actual MacStudio M3Ultra, UE5.8, shared GPU cap2, root one guarded renderer. Current owner preview launcher76933/engine76943 belongs to this thread; root stops it gracefully before new runtime checks. Original dirty checkout and previous owner artifacts are protected. Use published Epic Unreal skills/routing at76b36ccd28a0; policy freshness live rechecked. Bounded corrections and playtest handoff only, no long polish loop.

---

# Active manual-camera repair — 2026-10-12

Owner requested exactly two fixes: tricks must not select a different camera angle; high mouse/gamepad sensitivity must remain stable. This supersedes the historical held three-quarter trick-camera requirement. Preserve animation, traversal and collision behavior. No broader polish loop.

Task branch `codex/manual-camera-20261012`, base main `9eb3a5a7`, worktree `/Users/midir/spider-man-2-manual-camera-20261012`. Original checkout and prior owner artifacts are read-only. Root owns builds and one guarded renderer; engineer owns WebTravCamera.cpp/h and the input timestep hunk in WebTravCharacter.cpp. Follow verified Epic Unreal routing and shared GPU admission. Evidence: `docs/controls/manual-camera-20261012/`; cache `/Users/midir/sm2-manual-camera-cache/`. Push task branch, stop after focused validation and an updated owner build. No new main merge is authorized by this repair request.

---

# Active four-fix pass — 2026-10-11 evening (UTC 2026-10-12)

Owner explicitly requested ONLY: fix camera loss, abrupt firing arm, repetitive catch poses and rotation-rate spikes from the round-13 critic. This supersedes the previous stop for exactly these four repairs. Stay on the existing round13 continuation thread; no city, lighting, web rendering, suit, progression or broad polish changes. Stop after focused verification, independent review and a pushed owner playtest checkpoint.

Integration: `/Users/midir/spider-man-2-r13-fixes`, branch `codex/round13-closeout-20261011`, baseline `ecb68aad`. Original checkout `/Users/midir/spider-man-2` and previous owner playtest `/Users/midir/SpiderMan-R13-OwnerPlaytest-20261011` are read-only. Actual host M3 Ultra Mac15,14 (`midirstudio.local`). Shared brain revision76b36ccd28a0 is live verified. Use Unreal router and Epic MCP skill for every worker; source edits/builds are appropriate for C++ changes. Only root launches engines through existing shared GPU guards; one task renderer, cap2 globally. Never clear PAUSED or operate foreign instances.

Models remain owner-selected: GPT-6 Astra/high orchestration; GPT-6.1 Sol/xhigh engineering and fresh critic; GPT-6 Sol/high scout/tooling. Engineering workers use task-owned sparse worktrees; do not modify integration directly. Camera worker owns WebTravCamera.cpp/h. Flip/catch worker owns WebTravFlips.cpp/h plus explicitly coordinated pose/catch hunks. Root owns firing-arm animation and integration. Scout is read-only until assigned tooling paths. Do not weaken specs/checkers, fake case results, or obtain variety solely by relabeling identical poses.

Output: `docs/night1/final/swing/round-13-four-fixes/`; task cache `/Users/midir/sm2-r13-fourfix-cache/`. Preserve previous clips as before evidence. Verification must reproduce the cited roof case (s3_c6), press case (s2_c1), all seven primary flips and secondary wall tail; inspect actual pixels as well as telemetry. Owner subjective input acceptance remains separate.

---

# Active round-13 closeout — 2026-10-11

Owner explicitly authorized this continuation on the verified M3 Ultra (`midirstudio.local`, Mac15,14). This worktree is task-owned on `codex/round13-closeout-20261011`; `/Users/midir/spider-man-2` is the preserved original and must remain untouched. Existing M5 migration instructions below are historical, not this host identity.

Scope: finish existing round-13 flip held poses/tuck-open transitions, trick-camera containment during flip/cancel/landing, and existing web continuity/retract edits; create one consistent capture set, one independent critique, push and stop for owner playtest. No next round or broad game polish. Three-hour cap from 2026-10-11 18:48 UTC.

User-selected roles: orchestrator GPT-6 Astra/high; difficult engineering and independent critic GPT-6.1 Sol/xhigh; scoped tooling and scouting GPT-6 Sol/high. Native Epic Unreal guidance is mandatory, using published brain revision76b36ccd28a0. Only the orchestrator starts/stops engines through the existing shared coordinator at `~/.cache/gpu-slot`; at most one task-owned renderer, global hard cap two. Never clear PAUSED or touch foreign processes.

Task output is `docs/night1/final/swing/round-13-closeout/`; raw capture cache is `/Users/midir/sm2-r13-closeout-cache/`. Never run unmodified shared-scratch round-13 capture paths or reuse prior-build case caches. Current handoff and RUN.json carry status.

---

# Spider-Man on the M5

Working project: ~/spider-man-2. Owner authorized migration from M3, not a playtest or a new improvement loop. Read HANDOFF.md first. Work on codex/m5-migration-20261006 or a separately authorized task branch; never push main without explicit owner permission.

Verify target live: midirstudio2@midirstudio2.local, Mac17,15, M5 Ultra. The historical `studio` SSH alias points to the M3. Do not use it for M5 work. Preserve M3 originals and other agents' files/processes.

Read current shared-brain policy before an implementation or engine loop. The verified migration-time policy cache and Claude job brief are in ~/Documents/Codex/m5-unreal-setup-20261006. Policy revision: 3be383eed8647847fe37fe066df7756ff6ec98f3. This cache is private; never commit its contents or credentials to this public repository.

Source tools/m5/env.sh for M5 paths. Generated Content is present locally and excluded from Git. Do not use owner_preview/prepare.py --stage here: its original donor paths are M3 provenance. Check-only prepare.py is supported.

No editor, game, commandlet or renderer launch until the owner asks. Never claim owner gameplay acceptance from a build. Shared GPU root on M5 is ~/.cache/gpu-slot; do not create a second namespace. Hard global cap: two renderers. Do not clear PAUSED, bypass admission, stop foreign jobs, or auto-relaunch after two crashes. Manual preview uses tools/owner_preview/play.py and tools/m5/guarded_preview.py. It conservatively refuses any existing renderer or holder and uses the existing perf/capture locks. Legacy build/export loop scripts contain historical direct-launch and GPU code; review/adapt their admission before running them. Use only processes you own. Stop drivers, then SIGTERM, wait up to 60 seconds, then SIGKILL only as last resort.

.mcp.json is intentionally disconnected until there is a task-owned Unreal instance and verified endpoint. Restore from docs/migration/mcp.example.json only after checking instance ownership; localhost:8765 could belong to somebody else's editor.

The target is a visually polished 4K Manhattan swinging showcase, using the original author's newer night mode. Quests, skill trees and progression are outside the priority. Do not blindly merge rejected/unfinished branch work into the accepted preview. Keep one rolling HANDOFF.md and push task branches in the same session.
