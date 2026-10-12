# Curious Groove

The owner supplied `Curious Groove.mp3` on 2026-10-12 for looping background music in WebHomage. The original file is preserved unchanged (SHA-256 `197687ce53b99fc785d0e0578b4539bc40ad7796c892f8f3267b3f47d3ec2626`).

Run `python3 -B tools/audio/prepare_background_music.py` from the repository root, then run `unreal/WebHomage/Scripts/import_background_music.py` in the task-owned Unreal project using the shared GPU coordinator. Preparation uses ffmpeg and Python/NumPy, trims quiet padding and applies a 0.4-second circular crossfade. It produces a 147.07-second PCM16 stereo loop at 48 kHz; metadata records all input/output hashes. Generated WAV and Unreal Content remain excluded under the project content policy.

The game-instance music subsystem loads `/Game/Audio/Music/SW_CuriousGroove`, plays it at 25% volume, loops it, continues through the settings/pause menu and keeps one persistent component across level transitions. Closing the game stops it. `-WHMusicStartAt=145 -WHMusicVerify` is a diagnostic seek that logs mixer progress crossing the loop boundary; ordinary play starts from the beginning.
