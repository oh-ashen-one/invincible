# Flight suite checks (mechanical)

Telemetry gates only; pixels are judged separately by the critic. Fixed-step capture is not real-time FPS proof.

| case | result | failing checks (measured vs wanted) |
|---|---|---|
| fl01_takeoff_hover | PASS | - |
| fl02_takeoff_to_fly | PASS | - |
| fl04_boost_sonic | PASS | - |
| fl14_breach_cruise | FAIL | longest hidden run outside breaches (off-screen / occluded / dark) = 11 frames (11 total) (want <= 6) |
| fl15_breach_boost | PASS | - |
