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
