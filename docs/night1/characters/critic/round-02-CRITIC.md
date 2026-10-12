# P2 Characters, round 02: critic review (fresh eyes, pixels and motion only)

Captures: `characters/docs/night1/characters/round-02/captures/` (C/). The frames I extracted are in `_scratch/critic-P2-r02-work/`.

## 1) Axis scores
| Axis | Score | Evidence |
|---|---|---|
| Hero model & suit | **5** | C/lineup4k_04_t021.jpg: the weave normal is coarse and knit-like, closer to a sweater than fine hex. Web lines are thin, flat black print, broken and not joined, with no raised or glossy bead. The emblem is flat white paint. In C/lineup4k_00_t003.jpg the lenses are flat white with a thin rim, no curvature and no specular. Proportions are acceptable. Compared with refs/characters/press-duo-closeup, miles-face-closeup and the pack B still. |
| Hero animation | **4** | C/hero_run_side_34_hop.mp4 0–3 s: an upright jogger, torso almost vertical, with no sprint lean (refs/animation/clips/run-crosswalk). At 4.70–4.80 s the horizontal dive snaps to an upright run in about 2 frames, with no landing crouch or impact. The takeoff at about 4.0 s has no anticipation. The one plus: feet plant without skating at 1.0–1.6 s. |
| Enemies | **2** | C/thug_walk_1080.jpg and C/brute_walk_1080.jpg: prototype low-poly bodies, mitten hands, eyes that are sticker decals on a flat face, and clog-block shoes. The "brute" is the same mass as the thug, only hunched with bent knees. Nowhere near refs/characters/thugs-close-nm or thug-closeup-dn. |
| Civilians | **3** | C/citizens_walk.mp4: **nobody walks**. The woman stands in an idle pose for 0–5 s. The white-T man is frozen (arms and legs locked) for 5–9 s while the camera tracks him, and the worker is static at 9–13 s. The worker's face at 12 s is good, scan-grade. The "crowd" is hero clones jogging (citizens_wide_1080.jpg). Compared with the ref clip in pack/citizens. |
| Image quality | **4** | White seam cracks and sparkles on the woman's jacket, face and legs (citizens_wide_1080.jpg), and on the worker's jeans, vest and cheek (citizens_walk @12 s). At hero_turntable_walk @0.1 s the chest emblem is smeared as if at a low mip or TAA reset. The "4K" stills are internally 1920×1080, upscaled (lineup4k_perf.json), and there is a 2018 ms max-frame hitch. The flat test stage is not the cause of any of these. |

## 2) A/B decisions (judged before guessing which is which)
- **hero-run**: A is better. It has a forward lean, weight, contact shadows and a proper suit material. B is a stiff jogger. My guess: A is the reference.
- **hero-closeup**: B is better. It shows raised web lines, a thick lens rim and a fine micro-weave. A is a chest-only crop that hides the face and lenses. My guess: B is the reference.
- **citizens**: A is better. People move, react and are varied. In B they stand frozen. My guess: A is the reference.
- **thugs**: B is better. It has real faces, cloth folds and props. My guess: B is the reference.
- **progress-brute** (both ours): **B is better by a wide margin, about 2 points on the enemy axis.** At 4–7 s, A's second character has shredded, misassigned textures (a red polka-dot torso, white blotches and holes; see z_pbA_5s.jpg). B's brute is intact.

## 3) Single biggest gap: a testable instruction
Rebuild the **thug and the brute** at the fidelity of the construction-worker civilian. That means a realistic head with modelled eyes and skin visible around the mask, five-finger hands, cloth with folds, and real shoes. Scale the brute to at least 1.3× the thug's shoulder width and bulk, walking upright and heavy rather than crouched. Pass test: in a 3 m side-tracking walk clip at 60 fps, no decal eyes, no mitten hands, a brute/thug shoulder ratio of 1.3 or more, and both hold up next to refs/characters/thugs-close-nm__nm_0947.jpg and thug-closeup-dn__dn_0523.jpg.

## 4) Secondary issues
1. Civilians must actually walk: a looping walk with planted feet and arm swing, no idle or frozen poses, and at least 6 distinct civilians. Reference: refs/streets/clips/street-life-pedestrians.
2. The hero run needs a 10–15° forward lean and a full arm swing. The dive-to-run needs a landing crouch blended over 0.2–0.3 s.
3. Fix the seam cracks and sparkles on the civilian meshes. Test the fix at native 4K, not 1080p upscaled.
4. The suit's micro-weave is 3–4× too coarse. The web lines should be continuous, joined and raised, and the lenses need curvature and specular.

**Brand flag:** the hero's white long-legged spider emblem, white wrist cuffs and red leg stripes are a near-copy of the reference studio's "Advanced Suit" design. That is a studio or Marvel-owned design and it should be redesigned. I found no readable copied text or logos, although the brute's hoodie has small vertical lettering that I could not read.

## 5) Verdict: **FAILS** (lowest axis: enemies = 2)
