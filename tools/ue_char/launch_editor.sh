#!/bin/sh
# Launch the P2 Characters editor (own instance, MCP :8772, python mailbox). Fan homage project.
WT="$(cd "$(dirname "$0")/../.." && pwd)"
GPU_SLOT="${GPU_SLOT:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh}"   # shared GPU lock (docs/night1/gpu/PROTOCOL.md)
"$WT/tools/ue_char/ue_wait.sh"   # owner rule: never a 3rd+ Unreal instance; close the editor when not in use
# owner rule (16:43 incident): every Unreal launch, editor included, holds a GPU-lock capture slot; the slot is held while the editor runs
nohup "$GPU_SLOT" capture --label characters -- "/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" "$WT/unreal/WebHomage/WebHomage.uproject" \
  -RenderOffScreen -NoSound -NoCrashReports -ModelContextProtocolStartServer -ModelContextProtocolPort=8772 \
  -EnablePlugins=PythonScriptPlugin,EditorScriptingUtilities,MovieRenderPipeline,SequencerScripting,IKRig,ControlRig \
  -ExecCmds="py $WT/tools/ue_char/ue_mailbox.py" \
  "-ini:Input:[/Script/Engine.InputSettings]:bCaptureMouseOnLaunch=False" "-ini:Input:[/Script/Engine.InputSettings]:DefaultViewportMouseCaptureMode=NoCapture" -abslog=$WT/unreal/WebHomage/Saved/Logs/characters.log < /dev/null > "$WT/unreal/WebHomage/Saved/Logs/characters_launch.out" 2>&1 &
