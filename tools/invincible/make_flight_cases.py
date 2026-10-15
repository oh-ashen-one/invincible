#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation. See DISCLAIMER.md.
# Writes the Invincible flight capture cases (tools/invincible/flight_cases/*.json) for UWebTravScript (-WHTravScript).
# Flight bindings in script keys: swing = fly (RMB/R2), sprint = boost, jump = climb / takeoff, drop = descend, zip = brake /
# rescue interact, quick = dash, trick = slam. Map /Game/Showcase/Maps/Manhattan_Island (metres, UE axes, north = -Y):
# 5th Av runs along x 250, Times Square plaza at (-20, -230), cross streets at y 640 and y -560.
# Each case: name, note, quit (s of script time), extra game args, spawn, keys. checks: see check_flight.py.
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'flight_cases'
LEVEL_T, BRAKE_T, STRAFE, DROP_S, DIVE_T, SET_T = 8.0, 14.1, -0.25, 2.4, 17.6, 20.6   # fl17 route timing (rescue probe: climb at 50 deg, level at crane height, brake at the load)
TS = [-20.0, -230.0, 0.9]   # body centre (0.95 m over the feet) on the Times Square plaza floor (-0.06 m)
AV = [250.0, 300.0, 0.95]   # 5th Av roadway (open street: no TKTS steps / billboards / crowd between the camera and the hero)


def K(t, **kw):
    kw['t'] = t
    return kw


CASES = [
    dict(name='fl01_takeoff_hover', quit=12.0, note='Ground takeoff (jump) into a hover over 5th Av, climb, strafe both ways, descend to a gentle touchdown.',
         spawn=dict(pos=AV, yaw=-90, camPitch=0.14),
         keys=[K(0, move=[0, 0]), K(1.0, jump=True), K(1.25, jump=False), K(2.5, jump=True), K(4.0, jump=False),
               K(4.5, move=[1, 0]), K(6.0, move=[-1, 0]), K(7.5, move=[0, 0]), K(8.0, drop=True)],
         checks=dict(subs=['takeoff', 'hover'], grounded_end=True, max_hero_lands=0)),
    dict(name='fl02_takeoff_to_fly', quit=10.0, note='Fly + climb pressed on the ground: takeoff blends straight into a climbing fly line; climb released at 2.5 s levels out.',
         spawn=dict(pos=AV, yaw=-90, camPitch=0.14),
         keys=[K(0, move=[0, 0]), K(1.0, swing=True, jump=True), K(3.2, jump=False)],
         checks=dict(subs=['takeoff', 'fly'], min_speed=45.0, min_rise_m=10.0)),
    dict(name='fl03_cruise_hands_off', quit=10.0, note='Airborne over 5th Av at 60 m heading north, fly held, no look input: the fly line should hold its altitude (a player does not have to fight the camera).',
         spawn=dict(pos=[250, 600, 60], yaw=-90, camPitch=0.0, vel=[0, -20, 0]),
         keys=[K(0, move=[0, 0]), K(0.1, swing=True)],
         checks=dict(subs=['fly'], min_speed=50.0, max_alt_drift_m=12.0, max_hero_lands=0)),
    dict(name='fl04_boost_sonic', quit=12.0, note='Cruise, then boost from 1.0 s to 8.0 s: one sonic boom past 120 m/s, then boost released glides back to cruise.',
         spawn=dict(pos=[250, 1400, 120], yaw=-90, camPitch=0.0, vel=[0, -40, 0]),
         keys=[K(0, move=[0, 0]), K(0.1, swing=True), K(1.0, sprint=True), K(8.0, sprint=False)],
         checks=dict(subs=['fly', 'boost'], min_speed=140.0, booms=1)),
    dict(name='fl05_bank_turns', quit=12.0, note='Cruise east over the y 640 cross street at 260 m (above the towers); stick right 2-4 s, centre, stick left 5-7.5 s: banked turns.',
         spawn=dict(pos=[-400, 640, 260], yaw=0, camPitch=0.0, vel=[30, 0, 0]),
         keys=[K(0, move=[0, 0]), K(0.1, swing=True), K(2.0, move=[1, 0]), K(4.0, move=[0, 0]), K(5.0, move=[-1, 0]), K(7.5, move=[0, 0])],
         checks=dict(subs=['fly'], min_abs_bank_deg=20.0, max_hero_lands=0)),
    dict(name='fl06_look_steer', quit=10.0, note='Fly held, steering with the camera only: yaw right 45 deg/s 2-4 s, pitch up 5-6 s, pitch down 6.5-7.5 s.',
         spawn=dict(pos=[250, 800, 80], yaw=-90, camPitch=0.0, vel=[0, -30, 0]),
         keys=[K(0, move=[0, 0]), K(0.1, swing=True), K(2.0, look=[45, 0]), K(4.0, look=[0, 0]), K(5.0, look=[0, -20]), K(6.0, look=[0, 0]),
               K(6.5, look=[0, 25]), K(7.5, look=[0, 0])],
         checks=dict(subs=['fly'], min_yaw_change_deg=60.0, max_hero_lands=0)),
    dict(name='fl07_climb_dive_keys', quit=10.0, note='Fly held: climb key 2-4 s pitches the line up, descend key 5.5-7 s pitches it down, released holds.',
         spawn=dict(pos=[250, 800, 70], yaw=-90, camPitch=0.0, vel=[0, -40, 0]),
         keys=[K(0, move=[0, 0]), K(0.1, swing=True), K(2.0, jump=True), K(4.0, jump=False), K(5.5, drop=True), K(7.0, drop=False)],
         checks=dict(subs=['fly'], min_rise_m=15.0, max_hero_lands=0)),
    dict(name='fl08_brake', quit=8.0, note='Cruise, then brake (E) at 3.5 s: instant stop into a hover, held in place.',
         spawn=dict(pos=[250, 600, 60], yaw=-90, camPitch=0.0, vel=[0, -50, 0]),
         keys=[K(0, move=[0, 0]), K(0.1, swing=True), K(3.5, zip=True, swing=False), K(3.6, zip=False)],
         checks=dict(subs=['fly', 'brake', 'hover'], brakes=1, max_end_speed=3.0)),
    dict(name='fl09_dash', quit=8.0, note='Hover over 5th Av at 30 m; dash right 1.5 s, left 3.0 s, forward 4.5 s.',
         spawn=dict(pos=[250, 300, 30], yaw=-90, camPitch=0.2),
         keys=[K(0, move=[0, 0]), K(1.5, move=[1, 0], quick=True), K(1.6, quick=False), K(2.2, move=[0, 0]), K(3.0, move=[-1, 0], quick=True), K(3.1, quick=False),
               K(3.7, move=[0, 0]), K(4.5, move=[0, 1], quick=True), K(4.6, quick=False), K(5.2, move=[0, 0])],
         checks=dict(subs=['hover', 'dash'], dashes=3, max_hero_lands=0)),
    dict(name='fl10_slow_flight', quit=8.0, note='Fly held with the stick pulled back: slow flight (~35 % of cruise) for precise approaches.',
         spawn=dict(pos=[250, 600, 50], yaw=-90, camPitch=0.0),
         keys=[K(0, move=[0, -1]), K(0.1, swing=True)],
         checks=dict(subs=['fly'], max_speed=24.0, min_speed=12.0, max_hero_lands=0)),
    dict(name='fl11_slam_crater', quit=7.0, note='Hover 60 m over 5th Av, slam (F) at 1.5 s: straight dive into a superhero landing with a crater.',
         spawn=dict(pos=[250, 300, 60], yaw=-90, camPitch=0.3),
         keys=[K(0, move=[0, 0]), K(1.5, trick=True), K(1.6, trick=False)],
         checks=dict(subs=['slam'], hero_lands=1, grounded_end=True)),
    dict(name='fl12_fast_land', quit=8.0, note='Boost from 160 m, look down 40 deg (0.5-1.5 s): high-speed street impact = superhero landing without the slam key.',
         spawn=dict(pos=[250, 500, 160], yaw=-90, camPitch=0.14, vel=[0, -20, 0]),
         keys=[K(0, move=[0, 0]), K(0.1, swing=True, sprint=True), K(0.5, look=[0, 40]), K(1.5, look=[0, 0])],
         checks=dict(subs=['fly'], hero_lands=1, grounded_end=True, min_speed=90.0)),
    dict(name='fl13_soft_land_walk', quit=11.0, note='Hover descent from 25 m to a gentle touchdown on 5th Av, walk forward on the street, take off again.',
         spawn=dict(pos=[250, 300, 25], yaw=-90, camPitch=0.2),
         keys=[K(0, move=[0, 0]), K(0.5, drop=True), K(6.5, drop=False), K(7.0, move=[0, 1]), K(9.0, move=[0, 0]), K(9.5, jump=True), K(9.8, jump=False)],
         checks=dict(subs=['hover', 'takeoff'], max_hero_lands=0, walked=True)),
    dict(name='fl14_breach_cruise', quit=8.0, note='Cruise north up 5th Av at 35 m, turn the camera right into the east facade at > 45 m/s: through-building breach.',
         spawn=dict(pos=[250, 500, 35], yaw=-90, camPitch=0.0, vel=[0, -55, 0]),
         keys=[K(0, move=[0, 0]), K(0.1, swing=True), K(1.5, look=[90, 0]), K(2.5, look=[0, 0])],
         checks=dict(subs=['fly', 'breach'], breaches=1)),
    dict(name='fl15_breach_boost', quit=10.0, note='Boost east along the y 640 cross street at 40 m, then steer right (south) into the block at boost speed.',
         spawn=dict(pos=[-500, 640, 40], yaw=0, camPitch=0.0, vel=[60, 0, 0]),
         keys=[K(0, move=[0, 0]), K(0.1, swing=True, sprint=True), K(3.0, look=[90, 0]), K(4.0, look=[0, 0])],
         checks=dict(subs=['boost', 'breach'], breaches=1, min_speed=110.0)),
    dict(name='fl16_slow_facade_slide', quit=8.0, note='Slow flight (stick back) straight into the 5th Av east facade at 30 m: no breach under 45 m/s, slides along the wall.',
         spawn=dict(pos=[240, 500, 30], yaw=0, camPitch=0.0),
         keys=[K(0, move=[0, -1]), K(0.1, swing=True)],
         checks=dict(subs=['fly'], breaches=0, max_hero_lands=0)),
    dict(name='fl17_rescue_crane', quit=23.0, args=['-WHRescue=1', '-WHRescueSeed=1977'],
         note='Rescue wave 1 (seed 1977, hero at Times Square): wait for the wave, fly over to the crane load (straight through the tower block east of 5th Av, which tops 185 m on this line), brake, drop onto it (catch), dive down with it, set it down on the street (E), touch down.',
         spawn=dict(pos=TS, yaw=90, camPitch=0.14),   # crane load logged by the seed-1977 probe: (355.7, -324.3, 135.3) m, heading -14.1 deg
         keys=[K(0, move=[0, 0]), K(3.3, jump=True), K(3.55, jump=False), K(3.7, jump=True), K(4.0, look=[-104.09, 0]), K(5.0, look=[0, 0]),
               K(5.2, jump=False), K(5.4, swing=True, look=[0, -130]), K(5.9, look=[0, 0]), K(LEVEL_T, look=[0, 130]), K(LEVEL_T + 0.5, look=[0, 0]),
               K(BRAKE_T, zip=True, swing=False), K(BRAKE_T + 0.1, zip=False), K(BRAKE_T + 0.35, drop=True, move=[0, STRAFE]),
               K(BRAKE_T + 0.35 + DROP_S, drop=False, move=[0, 0]),
               # carry the caught load down: dive steeply, brake low over the street (the interact press sets it down), touch down beside it
               K(DIVE_T - 0.7, look=[-360, 0]), K(DIVE_T - 0.2, look=[0, 0]), K(DIVE_T, swing=True, look=[0, 110]), K(DIVE_T + 0.5, look=[0, 0]), K(SET_T, zip=True, swing=False), K(SET_T + 0.1, zip=False),
               K(SET_T + 0.4, drop=True)],
         checks=dict(rescue_saved_min=1, breaches=1)),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob('*.json'):
        old.unlink()
    for c in CASES:
        d = {'name': c['name'], 'note': c['note'], 'seed': 1234, 'spawn': c['spawn'], 'keys': c['keys']}
        (OUT / (c['name'] + '.json')).write_text(json.dumps(d, indent=1) + '\n')
    meta = {c['name']: {'quit': c['quit'], 'args': c.get('args', []), 'checks': c['checks'], 'note': c['note']} for c in CASES}
    (OUT / 'cases.json').write_text(json.dumps(meta, indent=1) + '\n')
    print('wrote %d cases -> %s' % (len(CASES), OUT))


if __name__ == '__main__':
    main()
