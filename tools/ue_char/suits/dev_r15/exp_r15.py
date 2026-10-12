import sys, os, json, shutil, time, numpy as np
WT='/Users/midir/sm2-n1/characters'
sys.path.insert(0,WT+'/tools/ue_char/suit8'); sys.path.insert(0,WT+'/tools/ue_char'); sys.path.insert(0,WT+'/tools/ue_char/suits'); sys.path.insert(0,'/Users/midir/sm2-n1/_scratch/characters/r15')
import hero_head_r14 as HH, hero_lens_r14 as HL, hero_lens_r8 as H8, head_profile_r14 as HP, cpu_rim2 as C2
PREP='/Users/midir/sm2-n1/_scratch/characters/r15/work/SK_Hero_prepped.glb'
def build(params=None, lens=None, widen=None, out='/Users/midir/sm2-n1/_scratch/characters/r15/work/exp.glb', rim_taper=None):
    shutil.copy(PREP,out)
    HH.main(out, None, params, widen)
    import importlib; importlib.reload(HL)
    HL.setup(**(lens or {}))
    HL.main(out)
    return out
def evaluate(glb, poses=((-6,-84),(-7,-88),(-5,-88),(-8,-84))):
    r=HP.analyse(glb)
    o={k:r[k] for k in ('T1_pct_HH','T2_pct_HH','T2b_pct_HH','T3_nose_bump_pct_HH')}
    o['poses']={}
    for th,yw in poses:
        m=C2.measure(glb,yw,th); o['poses'][f'{th}/{yw}']=(m['rim_minus_brow'],m['glass_minus_brow'])
    return o
if __name__=='__main__':
    t=time.time(); g=build(); print('build',time.time()-t); print(evaluate(g)); print(time.time()-t)
