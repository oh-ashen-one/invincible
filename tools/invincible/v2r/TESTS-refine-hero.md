Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation.

# refine_hero.py: offline tests (2026-10-30)

No video, no spend, no engine, no GPU. Blender 5 `-b --factory-startup`, one process at a time. The fixtures are game clips on
the project rig (known-good motion), so the tests prove the plumbing and the gates, not refinement quality.
Work dir (gitignored): `Local/video2rig/hero/work/export_test/refine_test/` (= `$W` below). `$V` = `tools/invincible/v2r`.

## Fixtures

```
cp Local/video2rig/hero/work/export_test/test_fit.blend $W/test_fit.blend          # old A_Hover, 121 keys every 0.8 frames (30/s), 4.000 s
Blender -b --factory-startup -P $V/make_test_fit_land.py -- \
  unreal/WebHomage/Saved/P2Build/invincible/SK_InvincibleV2.glb $W/land_fit.blend
# TESTFIT saved ... action landhero_testfit keys 0.000..66.400 (2.767 s at 24 fps) shift_z 0.8914 m lowest_vertex_last 0.00000 m lowest_vertex_first 0.5558 m
```

## 1. Hover loop, no plant

```
cd $W && Blender -b --factory-startup -P $V/refine_hero.py -- test_fit.blend --loop --no-plant --xfade 12
REFINE fk check frame 0: max joint error 0.001 mm (FK vs evaluated pose)
REFINE loop {"end_sample": 120, "cost": 0.0, "xfade": 12, "offset_total_rad": 0.0, "seam_ratio_before": 0.0, ...}
REFINE_GATE hover_testfit seam 1.11 foot_drift_mm n/a toe_min_mm -1113.8 peakhand_L 60 peakhand_R 58
```
The loop is already closed (end key equals frame 0, offset 0). The loop seam is the last distinct frame to frame 0 divided by the
median step, so a clean loop reads about 1 (one ordinary step), not 0. The toe height is -1.1 m because this fixture is not on
the floor (origin at the pelvis). Re-opened: one action, `hover_testfit_refined`, active, 121 keys. The 156 identity scale
F-curves were dropped.

## 2. LandHero one-shot, plant on (three runs)

```
S=Local/video2rig/hero/rig-stand/rig.json
# a. literal Brute semantics (return target = frame 0)
Blender -b --factory-startup -P $V/refine_hero.py -- land_fit.blend --return-to-stance --stance-rig $S --out land_fit_frame0_refined.blend
REFINE_GATE landhero_testfit seam 0.00 foot_drift_mm 0.1 toe_min_mm 17.1 peakhand_L 78 peakhand_R 80
# b. hero: return to the stance rig
Blender -b --factory-startup -P $V/refine_hero.py -- land_fit.blend --return-to-stance --return-target stance --stance-rig $S
REFINE_GATE landhero_testfit seam 0.03 foot_drift_mm 9.4 toe_min_mm 21.1 peakhand_L 69 peakhand_R 77
# c. hero: return to the stance rig, turned to face the same way as the clip's end
Blender -b --factory-startup -P $V/refine_hero.py -- land_fit.blend --return-to-stance --return-target stance --stance-yaw-align --stance-rig $S --out land_fit_stanceyaw_refined.blend
REFINE_GATE landhero_testfit seam 0.01 foot_drift_mm 11.9 toe_min_mm 24.5 peakhand_L 69 peakhand_R 11
```
- **a is wrong for this clip, even though its gate line looks clean.** The Brute return-to-stance blends the end onto frame 0.
  A_LandHero's frame 0 is the head-first dive, so the last 9 samples turn the standing end back into the dive. The last sample's
  soles end up 2255 mm and 1833 mm above the floor (`feet.last_sample_sole_mm`).
- In all three runs, no dive sample is planted. The Brute test plants only near the clip's own lowest foot height. The new floor
  guard removed 0 samples (`feet.floor_guard`). Plants were found at samples 73-83 for both feet in b and c, and 72/73-76 in a.
- Planted soles in run c: minimum 0.03 mm (left) and 0.08 mm (right) above the floor. The per-plant maximum is about 40 mm,
  reached as the foot arrives; in the source pose the left foot rests 40 mm up at the end.
- In the game clip, the three-point-landing crouch (samples 15-66) floats 0.30-0.50 m above the end pose's floor. The pelvis
  stays at 0.98 m throughout. The plant never lowers a foot (z is kept), so it leaves this crouch alone.
- In b and c, the left foot misses its pin by more than 5 mm at samples 74-76/77 (`ik_reach`). The raw clip's left leg is straight
  there and 36 mm under the floor, so the pin is out of reach. That accounts for the 9-12 mm toe drift.
- rig-stand faces about 30 deg off -Y (hip-line heading -119.7 deg). The LandHero end faces -87.6 deg. Run b therefore turns the
  body 32 deg in the 0.3 s return. Run c removes that turn.

## 3. Export of the refined blends

```
Blender -b --factory-startup <refined.blend> -P $V/export_hero_clip.py -- --out $W/<name>_test.glb --name Test_refined
test_fit_refined             EXPORT_GATE Test_refined max_vertex_delta_mm 0.0006 frames 6 PASS   (121 frames, 4.000 s)
land_fit_frame0_refined      EXPORT_GATE Test_refined max_vertex_delta_mm 0.0013 frames 6 PASS   (84 frames, 2.767 s)
land_fit_refined (b)         EXPORT_GATE Test_refined max_vertex_delta_mm 0.0013 frames 6 PASS
land_fit_stanceyaw_refined   EXPORT_GATE Test_refined max_vertex_delta_mm 0.0013 frames 6 PASS
```

## Smoke (exit 0, outputs in the session scratchpad)
- `--return-to-stance --return-target stance --stance-yaw-align --compress-holds --max-seconds 2.2 --stance-snap 6 --lock-yaw --keep-travel`
  on land_fit.blend: hold compression took the clip from 2.767 s to 2.133 s, the yaw lock found `hero/creature.json` (-Y), and
  the run ended with `yaw_locked 34.3`.
- `--loop --treadmill --window 10 110 --trim 0` on test_fit.blend: runs to completion. The fixture's feet sit 1.1 m under z = 0,
  so the floor-mismatch warning fires, as it should.
