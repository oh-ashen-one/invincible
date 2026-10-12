#!/bin/zsh
# Owner rule 2026-09-29: never add an Unreal process while the hard cap (4 across all agents since the 16:43 GPU incident; SM2_MAX_UNREAL) is reached; wait (poll every 60 s). ONE Unreal process per agent at a time: never background several captures.
# Instances of THIS worktree do not count against the limit of others but count in the total, so call this BEFORE launching.
while [ "$(pgrep -f 'MacOS/UnrealEditor( |$)' | wc -l)" -ge ${SM2_MAX_UNREAL:-4} ]; do echo "wait_slot: ${SM2_MAX_UNREAL:-4}+ Unreal instances running, waiting 60 s"; sleep 60; done
