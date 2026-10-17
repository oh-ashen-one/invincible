# Flight suite checks (mechanical)

Telemetry gates only; pixels are judged separately by the critic. Fixed-step capture is not real-time FPS proof.

| case | result | failing checks (measured vs wanted) |
|---|---|---|
| fl12_fast_land | FAIL | longest hidden run outside breaches (off-screen / occluded / dark) = 22 frames (37 total) (want <= 6) |
