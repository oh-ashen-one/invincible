"""Import the prepared owner track as /Game/Audio/Music/SW_CuriousGroove.

First run tools/audio/prepare_background_music.py. Then run this script in the task-owned Unreal project
through the shared GPU guard. WH_BACKGROUND_MUSIC_WAV may override the default Saved/AudioImport input.
Generated Content is ignored per CONTENT.md; the supplied MP3 and both scripts reproduce this asset.
"""
import json
import os
from pathlib import Path
import wave

import unreal

DESTINATION = "/Game/Audio/Music"
NAME = "SW_CuriousGroove"
ASSET_PATH = DESTINATION + "/" + NAME
project = Path(unreal.Paths.project_dir()).resolve()
source = Path(os.environ.get("WH_BACKGROUND_MUSIC_WAV", str(project / "Saved/AudioImport/CuriousGroove_Loop.wav"))).resolve()
if not source.is_file():
    raise FileNotFoundError("Prepare background music first: " + str(source))
with wave.open(str(source), "rb") as wav:
    if (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) != (48000, 2, 2):
        raise ValueError("Background music must be 48 kHz stereo PCM16 WAV")
    duration = wav.getnframes() / wav.getframerate()

unreal.EditorAssetLibrary.make_directory(DESTINATION)
task = unreal.AssetImportTask()
task.filename = str(source)
task.destination_path = DESTINATION
task.destination_name = NAME
task.automated = True
task.replace_existing = True
task.replace_existing_settings = True
task.save = False
task.factory = unreal.SoundFactory()
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
sound = unreal.EditorAssetLibrary.load_asset(ASSET_PATH)
if not isinstance(sound, unreal.SoundWave):
    raise RuntimeError("SoundWave import failed at " + ASSET_PATH)
sound.set_editor_property("looping", True)
sound.set_editor_property("sound_group", unreal.SoundGroup.SOUNDGROUP_MUSIC)
sound.set_editor_property("virtualization_mode", unreal.VirtualizationMode.PLAY_WHEN_SILENT)
sound.set_editor_property("loading_behavior", unreal.SoundWaveLoadingBehavior.FORCE_INLINE)
# PCM plus ForceInline keeps this modest stereo track resident and avoids a decoder/streaming restart at its seam.
sound.set_sound_asset_compression_type(unreal.SoundAssetCompressionType.PCM)
if not unreal.EditorAssetLibrary.save_loaded_asset(sound, only_if_is_dirty=False):
    raise RuntimeError("Failed to save background music at " + ASSET_PATH)
if not sound.get_editor_property("looping"):
    raise RuntimeError("Background music looping setting was not retained")
unreal.log("WH_BACKGROUND_MUSIC_IMPORTED " + json.dumps({
    "asset": sound.get_path_name(), "source_wav": str(source), "duration_seconds": duration,
    "looping": True, "compression": "PCM", "loading": "ForceInline", "channels": 2, "sample_rate": 48000,
}, sort_keys=True))
