# Where Unreal content lives

> Homage fan project, not an official Marvel/Sony/Insomniac game.

- **Source of truth = scripts + source files in this repo.** Every `.uasset`/`.umap` under `Content/` must be reproducible by a committed script (`Scripts/*.py` editor-Python run headless via `-run=pythonscript`, or `tools/*` exporters) from committed source files (GLBs, textures, JSON). `Content/` is git-ignored here: GitHub refuses new Git LFS objects on a public fork, and plain binary commits would bloat the fork.
- Each piece keeps a `Scripts/build_<piece>.py` (idempotent; deletes and recreates its own `/Game/<Piece>` folder). `Scripts/build_all.py` runs them in dependency order.
- **No binary snapshots on GitHub.** The account's Git LFS budget is exhausted (2026-09-29: pushes to private repos are refused too), so the private repo `oh-ashen-one/webhomage-unreal-content` stays empty. Scripts are the only source of truth; anything that can't be scripted yet must be flagged as a gap.
