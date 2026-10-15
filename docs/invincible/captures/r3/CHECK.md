# Flight suite checks (mechanical)

Telemetry gates only; pixels are judged separately by the critic. Fixed-step capture is not real-time FPS proof.

| case | result | failing checks (measured vs wanted) |
|---|---|---|
| fl01_takeoff_hover | PASS | - |
| fl03_cruise_hands_off | PASS | - |
| fl04_boost_sonic | PASS | - |
| fl13_soft_land_walk | PASS | - |
| fl14_breach_cruise | FAIL | longest hidden run outside breaches (off-screen / occluded / dark) = 9 frames (9 total) (want <= 6) |
