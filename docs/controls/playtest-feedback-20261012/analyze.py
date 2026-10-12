#!/usr/bin/env python3
"""Check actual telemetry for this owner's finite feedback pass."""
import argparse,csv,gzip,json,math,re
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('capture_dir',type=Path);a=ap.parse_args();out={};data={}
for path in sorted(a.capture_dir.glob('*_telemetry.csv*')):
 name=path.name.split('_telemetry')[0]
 with (gzip.open(path,'rt') if path.suffix=='.gz' else path.open()) as f:rows=list(csv.DictReader(f))
 if not rows:continue
 data[name]=rows
 bad=[r for r in rows if r['mode']!='swing' and any(float(r.get(k) or 0)>0 for k in ['rope_drawn','fw_s0_drawn','fw_s1_drawn'])]
 out[name]={'frames':len(rows),'non_swing_web_frames':len(bad),'visible_swing_web_frames':sum(r['mode']=='swing' and float(r['rope_drawn'])>0 for r in rows),'perch_frames':sum(r['mode']=='perch' for r in rows),'crouch_clip_frames':sum(r['anim_clip']=='perchIdle' for r in rows)}
 assert not bad,(name,'web drawn outside swing')
if 'boost-flip' in data:
 r=data['boost-flip'];i=next(i for i in range(1,len(r)) if r[i]['in_quick']=='1' and r[i-1]['in_quick']=='0');b,n=r[i-1],r[i]
 gain=float(n['speed_mps'])-float(b['speed_mps']);assert gain>8,(gain,'missing boost')
 assert b['flip_prog'] and b['flip_prog']==n['flip_prog'],'boost interrupted trick'
 out['boost-flip']['press_speed_before_after_mps']=[float(b['speed_mps']),float(n['speed_mps'])];out['boost-flip']['trick_continued']=n['flip_prog']
if 'web-release-zip' in data:
 assert out['web-release-zip']['perch_frames']>60,'zip did not reach and hold perch'
 assert out['web-release-zip']['visible_swing_web_frames']>0,'all swing webs hidden'
if {'swing-on','swing-off'}<=data.keys():
 x,y=data['swing-on'],data['swing-off'];assert len(x)==len(y)
 differences={k:round(max(abs((float(p[k])-float(q[k])+180)%360-180) for p,q in zip(x,y)),4) for k in ['cam_pitch_deg','cam_yaw_deg','pcm_roll']}
 assert max(differences.values())>.05,'on/off camera effect not verified'
 out['shake_on_off']={'max_angle_difference_degrees':differences,'max_physics_position_difference_m':max(math.dist([float(p[k]) for k in ['x_m','y_m','z_m']],[float(q[k]) for k in ['x_m','y_m','z_m']]) for p,q in zip(x,y))}
log=a.capture_dir/'music.log'
if log.exists():
 text=log.read_text(errors='replace');proof=re.search(r'WH_MUSIC loop verified progress=([0-9.]+) playing=1',text)
 assert proof,'native music loop crossing not verified'
 out['music']={'loop_verified':bool(proof),'cumulative_playback_fraction':float(proof[1]) if proof else None,'started_count':len(re.findall(r'WH_MUSIC started asset=',text)),'pause_commands':len(re.findall(r'WH_EXEC t=[0-9.]+ pause',text))}
print(json.dumps(out,indent=2))
