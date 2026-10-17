# Flight suite checks (mechanical)

Telemetry gates only; pixels are judged separately by the critic. Fixed-step capture is not real-time FPS proof.

| case | result | failing checks (measured vs wanted) |
|---|---|---|
| fl11_slam_crater | PASS | - |
| fl12_fast_land | FAIL | longest hidden run outside breaches (off-screen / occluded / dark) = 51 frames (53 total) (want <= 6); dark frames outside breaches (luma < 40) = 1 (want 0) |
