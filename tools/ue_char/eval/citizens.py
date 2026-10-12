"""Crowd citizen evaluation clip / Unreal FBX export (Blender 5.2, headless).

Fan homage project, not official Marvel/Sony/Insomniac; no affiliation.

  blender -b -P tools/ue_char/eval/citizens.py -- render NAME [NAME ...]
  blender -b -P tools/ue_char/eval/citizens.py -- fbx NAME [NAME ...]
render: orbit while walking, 3/4 walk, side run (crowd clips walk/walkF + run), plus face close-up and stats JSON.
fbx:    art/night1/characters/export/citizens/<NAME>.fbx (+ _basecolor.png), clips walk, run, idle @30 fps.
        Armature object is named 'Armature' (UE's FBX importer does not add it as an extra root bone),
        root bone 'hips'. Units: Blender metres, exported with apply_unit_scale + FBX_SCALE_ALL so node
        scales stay 1.0 and UE reads centimetres from the file's unit scale.
"""
import bpy, sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); from p2paths import WT as _P2WT, scr as _scr  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio, citizen_rig
import numpy as np

ROOT = citizen_rig.ROOT
SCR = _scr('eval')
if not os.path.isdir(SCR):   # legacy fallback; tools/life/citizens_fbx.py (P6 city life) redirects exactly this line (and EXP / DOCS below) by string substitution
    SCR = '/Users/midir/sm2-n1/_scratch/characters/eval'
DOCS = os.path.join(ROOT, 'docs/night1/characters/round-01/assets')
EXP = os.path.join(ROOT, 'art/night1/characters/export/citizens')

args = sys.argv[sys.argv.index('--') + 1:]
mode, names = args[0], args[1:]
res = {}
for name in names:
    studio.reset()
    meta = json.load(open(os.path.join(citizen_rig.NPC, 'citizens.json')))
    var = next(x for x in meta['variants'] if x['name'] == name)
    walk = 'walkF' if var['female'] else 'walk'
    png = os.path.join(SCR, 'tiles', name + '.png')   # cropped by tiles.py (Blender's python has no Pillow)
    png = citizen_rig.refit_tex(name) or png            # round 06: the refit citizen's own 2048 px texture (refit.py), else the atlas tile
    if mode == 'fbx':
        import shutil
        os.makedirs(EXP, exist_ok=True)
        shutil.copy(png, os.path.join(EXP, name + '_basecolor.png'))
        png = os.path.join(EXP, name + '_basecolor.png')
    # round 04: every walk style goes into the FBX under its own take name (UE imports the takes of the first citizen only; all
    # citizens share the 18-bone skeleton), so the crowd can mix walk / walkF / walkBrisk / walkStroll / walkOld
    clips = ('walk', 'walkF', 'walkBrisk', 'walkStroll', 'walkOld', 'run', 'idle') if mode == 'fbx' else (walk, 'run')
    R = citizen_rig.build(name, clips=clips, tex=png)
    err = citizen_rig.recon_error(R, clip='idle' if mode == 'fbx' else 'run')   # idle / run keep its frame times (walks are time-warped since round 04)
    g = R['g']
    info = {'name': name, 'female': var['female'], 'verts': len(g['pos']), 'tris': len(g['idx']),
            'recon_err_m': err, 'fit_rms_cm': var.get('fit_rms_cm')}
    if mode == 'fbx':
        arm, ob = R['arm'], R['ob']
        # the mesh uses the exported PNG next to the FBX
        for o in bpy.context.scene.objects:
            o.select_set(o in (arm, ob))
        bpy.context.view_layer.objects.active = arm
        # rename actions to clean take names
        bpy.ops.export_scene.fbx(filepath=os.path.join(EXP, name + '.fbx'), use_selection=True,
            object_types={'ARMATURE', 'MESH'}, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
            axis_forward='-Z', axis_up='Y', add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X',
            bake_anim=True, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False,
            bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=0.0,
            mesh_smooth_type='FACE', use_mesh_modifiers=False, path_mode='STRIP', embed_textures=False)
        info['fbx'] = os.path.join(EXP, name + '.fbx')
        info['bones'] = [b.name for b in arm.data.bones]
        info['rest_heads'] = [[round(x, 5) for x in b.head_local] for b in arm.data.bones]
        info['clips'] = {k: [int(v.frame_range[0]), int(v.frame_range[1])] for k, v in R['acts'].items()}
    else:
        arm = R['arm']
        studio.nla_sequence(arm, [(R['acts'][walk], 1, studio.SEG2), (R['acts']['run'], studio.SEG2 + 1, studio.N)])
        studio.setup(height=1.75)
        studio.render(os.path.join(SCR, 'frames'), 'citizen_' + name, DOCS, still_frame=95, face=(1.55, 1.0))
    res[name] = info
    json.dump(info, open(os.path.join(SCR, 'stats', ('fbx_' if mode == 'fbx' else 'cit_') + name + '.json'), 'w'), indent=1)
    print('RESULT', json.dumps({k: v for k, v in info.items() if k not in ('rest_heads', 'bones')}))
