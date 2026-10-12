# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 r26 (cross-piece, minimal): the ORIGINAL hero suits of characters r14 in THIS worktree's /Game/Characters, built only by P2's committed
# Scripts/build_characters.py (helpers + its 'skins' step), from the CPU-made maps of P2's committed generators:
#   python3 tools/ue_char/hero_suit_r8.py          -> art/night1/characters/hero/tex/suit_*_r8.png (Tessera, 8192) + shared/suit_twill_n.png
#   python3 tools/ue_char/suits/gen_suits.py       -> art/night1/characters/hero/suits/<id>_*.png (the 7 other suits, 4096)
# then (commandlet, -nullrhi):
#   UnrealEditor <uproject> -run=pythonscript -script=<this file> -unattended -nullrhi
# What it does: re-imports T_Hero_BaseColor / Normal / ORM from the r8 Tessera maps (P2 'tex' step, hero part only: this worktree's copies were
# the pre-round-08 browser suit texture), re-makes MI_Hero_Suit on the EXISTING M_Char_Suit master (P2 'mat' step, MI_Hero_Suit line only: the
# master is not rebuilt because MI_Thug / citizens / people instances parent it), MI_Hero_Lens (glossy lens), then P2's 'skins' step
# (DA_HeroSuits + MI_HeroSuit_<id>). UWHHeroSuitSubsystem applies suit 0 (Tessera) to the player pawn on every frame from the second tick.
import os, unreal
WT = os.path.abspath(os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), '..', '..'))
SRC = WT + '/unreal/WebHomage/Scripts/build_characters.py'
CODE = compile(open(SRC).read(), SRC, 'exec')


def run(steps):
    g = {'__name__': '__main__', 'ARGS': {'steps': steps}}
    exec(CODE, g)
    return g


g = run('none')                       # helpers only (no step named 'none')
ART, ROOT, EAL = g['ART'], g['ROOT'], g['EAL']
H = ART + '/hero/tex'
for f in ('suit_basecolor_r8.png', 'suit_normal_r8.png', 'suit_orm_r8.png', 'suit_r8.json'):
    if not os.path.exists(H + '/' + f): raise SystemExit('P3SUITS: missing %s/%s (run tools/ue_char/hero_suit_r8.py)' % (H, f))
g['import_tex'](H + '/suit_basecolor_r8.png', ROOT + '/Hero/Textures', 'T_Hero_BaseColor', 'srgb')
g['import_tex'](H + '/suit_normal_r8.png', ROOT + '/Hero/Textures', 'T_Hero_Normal', 'normal_gl')
g['import_tex'](H + '/suit_orm_r8.png', ROOT + '/Hero/Textures', 'T_Hero_ORM', 'linear')
if os.path.exists(ART + '/shared/suit_twill_n.png'):
    g['import_tex'](ART + '/shared/suit_twill_n.png', ROOT + '/Shared/Textures', 'T_Fabric_Twill_N', 'normal_gl')
EAL.save_directory(ROOT, only_if_is_dirty=True, recursive=True)
suit = g['load'](ROOT + '/Shared/Materials/M_Char_Suit')
_fine = EAL.does_asset_exist(ROOT + '/Shared/Textures/T_Fabric_Twill_N')
_tile = float(g['_json0'].load(open(H + '/suit_r8.json'))['detail_tiling']) if _fine else 48.0
g['mi']('MI_Hero_Suit', ROOT + '/Hero/Materials', suit,
        tex={'BaseColor': ROOT + '/Hero/Textures/T_Hero_BaseColor', 'ORM': ROOT + '/Hero/Textures/T_Hero_ORM',
             'Normal': ROOT + '/Hero/Textures/T_Hero_Normal',
             'DetailNormal': ROOT + ('/Shared/Textures/T_Fabric_Twill_N' if _fine else '/Shared/Textures/T_Fabric_Knit_N')},
        scal={'DetailTiling': _tile, 'DetailStrength': 0.8 if _fine else 0.6, 'Cloth': 0.45, 'Specular': 0.5}, vec={'FuzzColor': (0.50, 0.62, 0.68, 1)},
        switches={'HasORM': True})
try:
    hl = g['build_hero_lens']()
    g['mi']('MI_Hero_Lens', ROOT + '/Hero/Materials', hl, scal={'Roughness': 0.06, 'Specular': 0.7, 'EdgeDarken': 0.7, 'Emissive': 0.30}, vec={'Color': (0.50, 0.13, 0.01, 1)})
except Exception as ex:
    print('P3SUITS: hero lens kept (%s)' % str(ex)[:160])
EAL.save_directory(ROOT, only_if_is_dirty=True, recursive=True)
print('P3SUITS: MI_Hero_Suit = Tessera r8 (tiling %.1f, twill %s)' % (_tile, _fine))
g2 = run('skins')
da = unreal.load_asset(ROOT + '/Hero/Suits/DA_HeroSuits')
n = len(da.get_editor_property('suits')) if da else 0
print('P3SUITS: done, DA_HeroSuits suits=%d' % n)
