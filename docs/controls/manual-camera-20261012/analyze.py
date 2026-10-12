#!/usr/bin/env python3
"""Summarize real camera telemetry; no rendered/physical-controller claim is inferred."""
import csv,gzip,json,math,sys
from pathlib import Path

def wrap(a): return (a+180)%360-180

def report(path):
    rows=list(csv.DictReader(gzip.open(path,'rt') if str(path).endswith('.gz') else Path(path).open()))
    yaw=[]; orbit=[]; err=[]; reverse=0
    for i,r in enumerate(rows):
        x,y=float(r['cam_x'])-float(r['x_m']),float(r['cam_y'])-float(r['y_m'])
        bearing=math.degrees(math.atan2(-y,-x))
        err.append(abs(wrap(float(r['cam_yaw_deg'])-bearing)))
        if i:
            p=rows[i-1]
            yaw.append(wrap(float(r['cam_yaw_deg'])-float(p['cam_yaw_deg'])))
            prev=math.degrees(math.atan2(float(p['cam_y'])-float(p['y_m']),float(p['cam_x'])-float(p['x_m'])))
            step=wrap(math.degrees(math.atan2(y,x))-prev)
            orbit.append(step)
            if .85<float(r['t'])<2.4 and step < -.1: reverse+=1
    return {'file':str(path),'frames':len(rows),'camera_in_geometry':sum(float(r['cam_in_geometry'])>0 for r in rows),
        'body_not_fully_in_frame':sum(float(r['hero_in_frame'])<.5 for r in rows),
        'max_horizontal_aim_error_degrees':round(max(err,default=0),3),
        'max_yaw_step_degrees':round(max(map(abs,yaw),default=0),3),
        'reverse_orbit_frames_during_positive_input':reverse if any(n in Path(path).name for n in ('high-look','mouse-')) else None,
        'yaw_phase_body_not_fully_in_frame':sum(float(r['hero_in_frame'])<.5 for r in rows if .85<float(r['t'])<2.4) if any(n in Path(path).name for n in ('high-look','mouse-','clear-air')) else None,
        'yaw_slew_frames':sum(int(r['cam_slew'])&4!=0 for r in rows),
        'max_trick_camera_blend':max((float(r['flipcam_k']) for r in rows),default=0),
        'active_trick_frames':sum(bool(r['flip_prog'].strip()) for r in rows)}
if __name__=='__main__': print(json.dumps([report(p) for p in sys.argv[1:]],indent=2))
