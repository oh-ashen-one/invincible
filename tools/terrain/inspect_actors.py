#!/usr/bin/env python3
"""Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
Terrain r04 helper: list the static-mesh actors of the integrated map whose bounds are small and lie in a box (UE cm), to find what draws an unexpected object.
Run only with none of your engines running, as a nullrhi commandlet: UnrealEditor <uproject> -run=pythonscript -script=<this file> -unattended -nullrhi -nosplash -RenderOffScreen -NoSound -abslog=<log>
Edit OUT and the box below first. r04 result: nothing small in the p3 bank box (the lumps are not individual actors of Terrain_Land / City_Geo_T)."""
import unreal, traceback
OUT = '/Users/midir/sm2-n1/_scratch/terrain/r04/inspect5.txt'
lines = []
try:
    unreal.EditorLoadingAndSavingUtils.load_map('/Game/TerrainR4/Maps/Manhattan_Terrain')
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    acts = eas.get_all_level_actors()
    # the south bank of the Lake in front of the p3 camera: UE cm x -6000..12000, y -102000..-92000 (eggs at p3 right half)
    for a in acts:
        try:
            o, e = a.get_actor_bounds(False)
        except Exception:
            continue
        if e.x > 6000 or e.y > 6000: continue
        if o.x + e.x < -6000 or o.x - e.x > 12000 or o.y + e.y < -112000 or o.y - e.y > -92000: continue
        lv = a.get_level().get_outer().get_name() if a.get_level() else '?'
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            sm = c.static_mesh
            lines.append('[%s] %s | %s | mesh=%s | mats=%s | at %.0f,%.0f,%.0f ext %.0f,%.0f,%.0f' % (lv, a.get_actor_label(), c.get_class().get_name(), sm.get_name() if sm else None, [m.get_name() if m else None for m in c.get_materials()][:3], o.x, o.y, o.z, e.x, e.y, e.z))
    lines.append('count %d' % len(lines))
except Exception:
    lines.append(traceback.format_exc())
open(OUT, 'w').write('\n'.join(lines))
