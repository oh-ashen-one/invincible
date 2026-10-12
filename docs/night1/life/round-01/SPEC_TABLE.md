# P6 City life round 01: spec table

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Counts come from the engine itself (`WHLifeProbe`, log lines `WH_LIFE_FRAME`): every vehicle / person whose centre projects into the frame, is at least N pixels tall and is reached by a visibility ray from the camera (city geometry blocks it; other vehicles and people do not). No YOLO model is installed on this machine, so these are NOT detector counts: the spec numbers were measured with YOLO on the reference, which misses small and partly hidden objects, so compare with the LARGER size threshold (>= 44 px vehicles / >= 56 px people) as well as the small one. Median (min-max) over the reports at game t = 8, 14, 20, 28 s of each run; "twins/looks" = people in frame that share model AND outfit with another person in frame. Verdicts use the 4K runs.

| id | target (SPEC) | measured (this build) | verdict |
|---|---|---|---|
| C4 cars, S1 street frame | 5-19 (median ~11) | vehicles moving + parked, >= 22 px: 4K 21.5 (20-23); 1080p 9 (9-10); >= 44 px: 4K 9.0 (8-12); 1080p 5 (4-6) | MEETS at >= 44 px (>= 22 px counts small far cars: above the range) |
| C4 people, S1 street frame | 6-32 (median ~24) | people >= 28 px: 4K 15.0 (12-19); 1080p 12 (10-13); >= 56 px: 4K 12.0 (9-13); 1080p 5 (5-5) | MEETS (median below the ~24 of the reference) |
| C4 traffic lights >= 1 | >= 1 | P1 street-kit signal heads are in the S1 frame (stills); they are P1 props and are NOT driven by the life signal clock | present, not driven |
| S1 parked cars incl. taxis | >= 5 parked cars incl. taxis | parked in frame >= 22 px: 4K 12.0 (12-12); 1080p 4 (4-4); parked taxis: 4K 1.0 (1-1); 1080p 1 (1-1) | MEETS |
| C6 vehicles, S2 avenue from swing height | median 14-22 per frame | vehicles moving + parked, >= 22 px: 4K 14 (10-16); 1080p 0.0 (0-0) (>= 44 px: none, the avenue is 60-500 m away) | MEETS |
| CH16 people per frame (street level) | 8-25 | S1 people >= 28 px: 4K 15.0 (12-19); 1080p 12 (10-13) | MEETS |
| CH17 >= 6 distinct civilian models in one frame, no identical twins | >= 6 models; 0 twins | S1 looks (model + outfit) in frame: 4K 15.0 (12-19); 1080p 12 (10-13); identical looks in frame: 4K 0.0 (0-0); 1080p 0 (0-0). 60 looks = 20 citizen meshes x 3 outfits; the mesh alone repeats | MEETS |
| CH17 no gliding / frozen walkers | 0 | planted-stance ankle displacement, S1 4K: `ankle world displacement during a planted stance (cm; ~20-25 = heel-toe roll, a stride is ~55) median 15.7 p95 33.8 max 49.5 | stances > 45 cm (sliding) 7 (2.2 %)`; S1 1080p: `ankle world displacement during a planted stance (cm; ~20-25 = heel-toe roll, a stride is ~55) median 21.7 p95 41.9 max 58.6 | stances > 45 cm (sliding) 11 (3.6 %)` (details below) | see notes |
| CH19 gait phases not in lockstep | pairwise phase difference spread >= 0.2 cycle across >= 6 walkers | 14 walkers: max pairwise difference 0.490 cycle, mean 0.264, resultant length R 0.074 (0 = evenly spread), pairs within 0.05 cycle: 8 of 91 | MEETS |

