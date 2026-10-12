# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# P6 City life: run P2's citizen FBX exporter (tools/ue_char/eval/citizens.py, mode 'fbx') with its scratch / output paths
# redirected to THIS piece (P2's script hard-codes its own scratch dir and writes into art/night1/characters).
#   blender -b -P tools/life/citizens_fbx.py -- NAME [NAME ...]
# reads   public/assets/city/npc/citizens.{json,bin} + tiles prepared by tools/ue_char/eval/tiles.py into <SCR>/tiles
# writes  <SCR>/fbx/<NAME>.fbx (+ _basecolor.png): 18-bone crowd rig, actions walk / run / idle @ 30 fps
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..'))
EVAL = os.path.join(ROOT, 'tools/ue_char/eval')
SCR = os.environ.get('SM2_LIFE_CIT', '/Users/midir/sm2-n1/_scratch/life/citizens')
src = open(os.path.join(EVAL, 'citizens.py')).read()
# P2 round 05 moved its scratch path behind p2paths.scr('eval'); accept either form
_scr_line = "SCR = _scr('eval')" if src.count("SCR = _scr('eval')") == 1 else "SCR = '/Users/midir/sm2-n1/_scratch/characters/eval'"
subs = [(_scr_line, 'SCR = %r' % SCR),
        ("EXP = os.path.join(ROOT, 'art/night1/characters/export/citizens')", 'EXP = %r' % os.path.join(SCR, 'fbx')),
        ("DOCS = os.path.join(ROOT, 'docs/night1/characters/round-01/assets')", 'DOCS = %r' % os.path.join(SCR, 'docs'))]
for a, b in subs:
    if src.count(a) != 1: raise SystemExit('citizens.py changed, cannot redirect: ' + a)
    src = src.replace(a, b)
os.makedirs(os.path.join(SCR, 'stats'), exist_ok=True)
sys.path.insert(0, EVAL)
names = sys.argv[sys.argv.index('--') + 1:]
sys.argv = [sys.argv[0], '--', 'fbx'] + names
__file__ = os.path.join(EVAL, 'citizens.py')
exec(compile(src, __file__, 'exec'))
