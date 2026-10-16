# Flight suite checks (mechanical)

Telemetry gates only; pixels are judged separately by the critic. Fixed-step capture is not real-time FPS proof.

| case | result | failing checks (measured vs wanted) |
|---|---|---|
| fl01_takeoff_hover | PASS | - |
| fl02_takeoff_to_fly | PASS | - |
| fl03_cruise_hands_off | PASS | - |
| fl04_boost_sonic | PASS | - |
| fl05_bank_turns | PASS | - |
| fl06_look_steer | PASS | - |
| fl07_climb_dive_keys | PASS | - |
| fl08_brake | PASS | - |
| fl09_dash | PASS | - |
| fl10_slow_flight | PASS | - |
| fl11_slam_crater | PASS | - |
| fl12_fast_land | PASS | - |
| fl13_soft_land_walk | PASS | - |
| fl14_breach_cruise | PASS | - |
| fl15_breach_boost | PASS | - |
| fl16_slow_facade_slide | PASS | - |
| fl17_rescue_crane | FAIL | longest hidden run outside breaches (off-screen / occluded / dark) = 9 frames (21 total) (want <= 6) |
