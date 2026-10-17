# r9 notes: fast-dive landing pose (fl12) and the framing beside the truck (fl12)

This was a source-only builder pass. Nothing was compiled, launched, simulated or rendered in Unreal, and no git command was run. The root compiles, simulates, renders and commits.

**Offline tools used:** python/numpy FK of `docs/invincible/character/meshy/hero_land.glb` (the AS_LandHero source, reader `/tmp/r7anim/glb.py`; scripts in `/tmp/r9anim/`), and ffmpeg frame extraction from `~/sm2-invincible-cache/r8b/full/fl12_fast_land.mp4`. Read-only inputs: r8b telemetry/log, simR8c fl12 telemetry/log. All numbers below come from these offline checks, not from engine runs.

**Files:**
- `Traversal/Anim/WHHeroV2AnimInstance.h/.cpp`
- `Traversal/WebTravCamera.h/.cpp`
- `Traversal/WebTravCharacter.cpp`: only `HeroV2Frame`, the flight mesh orientation, 6 lines. This edit is in the character file but outside the camera block. Flagging it so the root can confirm it falls within this piece.

`WHFlightComponent` is unchanged.

**A/B switches:**
- `-WHHeroV2Tune=LandHoldFreeze=0,LandKneelContact=0` gives the r8 anim. The only exceptions are the stand-clear snap and the upright snap.
- `-WHCamTune=VehMaxDeg=0` gives the r8 camera, except the guard's raise direction.

## 1. Fast-dive landing pose

### What r8b actually showed (fl12, rows 160–239 = the 1.30 s hold)

**Clip time and blends:**
- The clip time reached the contact as intended. The log shows the dive started at clip t 0.38, 0.54 s before the floor, and contact came 0.55 s later.
- No impact jump was needed: the creep ends at LandImpactT − 0.02 = 0.48.
- The only track in the hold was AS_LandHero. Its weight reached 1 after 0.2 s, and no hover or fly state was logged until `land hold end`.

**Overlay check:** I projected the clip's FK skeleton at t ≈ 0.73 with the telemetry camera (`pcm_*`, hfov 104.6) onto video frame 175.
- It matches the rendered body: head, back leg, raised free arm and planted foot.
- So there was no 50 % AS_Hover/AS_Fly mix and no pitch. The upright mesh with yaw only is consistent with velocity 0, which gives PitchWant 0.

**Why it read as "all fours / splayed":**
1. **The clip's own kneel is splayed.** At t 0.62:
   - the back (left) knee joint is 26.6 cm over the sole line and 45 cm out to the side;
   - the back toes are 12 cm up;
   - the feet are 118 cm apart;
   - the fist's knuckle is 11 cm up.
2. **The camera viewed it from almost directly overhead.** During the hold the lens was 1.75–1.82 m away at pitch −62 to −77°. The guard had pulled it over the truck (see section 2).
3. **The hold kept playing the clip.** The kneel ran on from 0.48 to 1.78; the joints keep moving 20 cm through it.
4. **The mesh slid during the hold.** The stand-clear nudge (log: 57 cm in −x, tau 0.2 s) moved the kneeling mesh sideways across the crater.

### Changes (WHHeroV2AnimInstance)

- **Contact frame held (`LandHoldFreeze` 1):**
  - At init, `AnalyzeLandClip` measures `LandHoldPoseT`: the first frame after LandImpactT where pelvis, head, knees, feet, wrists and one knuckle all move less than `LandSettleK` (0.5 body heights/s).
  - Offline value: 0.617 s (1.6 m/s at 0.60, 0.5 m/s at 0.65).
  - During the hold the clip runs from the contact (0.48) to that frame, about 0.14 s, then freezes.
  - It never passes LandKneelEndT, so the stand-up only plays after the release.
  - Logs:
    - init: `WH_HEROV2 land clip r9: contact pose settles at t=… kneeling leg … fist …`
    - contact: `WH_HEROV2 land contact r9: AS_LandHero t=… other clips …`
    - release: `WH_HEROV2 land hold released r9: AS_LandHero t=… after … s`
- **No foreign blend at the contact:**
  - A fly or boost share still fading in at the impact leaves within `BlendLandImpact` (0.08 s).
  - A direct entry into the airborne hold (no predicted dive) uses that blend instead of 0.15 s.
- **Kneel contact layer (`LandKneelContact` 1, proxy, component space, after the ground lock):**
  1. **Back thigh.** The kneeling leg's thigh (the lower knee, measured at init) turns down under its hip, keeping its horizontal heading, until the knee joint is `LandKneeCm` (6.5 cm) over the sole line. The turn is capped at 70°.
  2. **Back shin.** The shin turns about the knee (closed form) so its foot joint rests at the planted foot's joint height.
  3. **Fist arm.** The fist arm (the lower knuckle) gets a two-bone reach, with the elbow kept in its bend plane, until the middle knuckle is `LandFistCm` (2.5 cm) over the sole line. It uses 3 passes at gain 0.6.
  - **Weight:** the AS_LandHero grounded track weight, ramped in over LandImpactT → LandHoldPoseT, faded around LandKneelEndT ± 0.1, and multiplied by the ground lock weight.
  - The planted foot, head, torso and free arm are untouched.
  - **Offline FK of the same math at t 0.617:**

    | Joint | Before | After |
    |---|---|---|
    | Knee | 26.6 cm | 6.9 cm (thigh vertical, at full reach) |
    | Back toe | 12.2 cm | 3.3 cm (= planted foot joint) |
    | Knuckle | 11.1 cm | 2.6 cm |
    | Stance width | 118 cm | 64 cm |

  - The back thigh turns 50°.
  - Sheet: `/tmp/r9anim/kneel_r9.png`. Top row is before, bottom row after; views are rear chase, side, three-quarter and top-down.
- **Stand clear in the hold:** the step is taken once, on the contact frame, and kept until the release. There is no slide while kneeling.

### Upright (WebTravCharacter `HeroV2Frame`)

- While `InLandContact()` (AS_LandHero past its contact) is true, mesh pitch and bank are set to 0, so the orientation is yaw only.
- **Reason:** a hard landing that arrives without the predicted dive (boost hold, PitchFreedom 1) reached the contact pitched up to 45°, and that pitch only eased out at 8/s.
- **Lag:** the anim state is one frame behind, which affects the contact frame only.

**Float lift:** unchanged and already correct. The flight holds Pos.Z at the floor for the full 1.30 s (r8b z 0.942 constant on rows 160–239). The ground lock and kneel layer fade only with the AS_LandHero track after the release.

## 2. fl12 framing next to the truck

### Telemetry

**r8b render, landing beside a white box truck in the next lane, on the +x side of the hero:**
- **Hold:** the composed chase spot (yaw −105, behind-right) was in or behind the truck. The guard pulled and raised the lens to 1.8 m, giving the top-down view.
- **After takeoff:**
  - At 4.79 s the lens swung round his side at 13–57° per frame.
  - At 5.04–5.39 s (22 frames) it was 0.6 m ahead of him at 1.9 m, pitch −42 to −69. Every frame was `hero_in_frame` 0, with `cam_slew` 133 (orbit cap).
  - The raise fallback had placed the lens "behind the view" while the view looked back against his travel.

**simR8c, 6.03–6.18 s (10 frames):**
- He was flying at 55 m/s, 1.85 m up.
- The lens had been lifted over a vehicle box (z 3.97). It then jumped 6 m in one frame to 1.85 m from him at pitch −71.
- That jump was the guard: the lift could not see his chest, so it fell back to the pull-in, then the raise, then the body push.

### Changes (WebTravCamera)

- **Vehicle side swing** (flight hero only; tunables `Veh*` in `-WHCamTune`):
  - **Test:** `GuardLens` runs `UpdateVehSwing` on this frame's composed lens before the offset. It checks the lens now and `VehLeadT` (0.2 s) along his travel. The spot counts as blocked when:
    - it is in a vehicle box expanded by 0.32 m; or
    - a box cuts its line to his chest; or
    - a box cuts its line to more than 2 of 5 body points (`VehVisMin` 0.6 = at least 60 % seen).
  - **Search:**
    - Azimuths round him in 10° steps up to 120°.
    - Side order: the side the goal is already on, else the side away from the inverse-square box mass.
    - A candidate must be clear of boxes now and at the lead, out of traversal solids and render collision, and must see his chest.
  - **Hysteresis:**
    - A clear goal is kept unless a spot at least 15° nearer is clear.
    - The goal returns to 0 after 0.4 s with a clear composed spot.
  - **Apply:** `Update` orbits the composed lens round him by `VehYawOff` and adds the same angle to the view yaw, so his screen position is unchanged.
    - Spring 0.12 s, hard cap 180°/s.
    - About 0.35 s for a 60° swing.
    - This runs before the output slew and orbit cap, so those see the swung spot (no ratchet).
  - **Signals:** `cam_slew` bit 1024 marks applied frames. Log: `WH_CAM r9 vehicle side swing: … -> azimuth offset … deg`.
  - **Not active:** during a breach pass or tail (goal 0), above 8 m (no boxes gathered), and for the legacy hero.
- **Guard raise direction:** when moving faster than 5 m/s with the view facing against his travel, the "rise over him" spot goes behind his travel instead of behind the view. This addresses the r8b 5.04 s lens ahead of him.

### Expectation for fl12

- **Hold:** the lens swings to the −x (open) side within about 0.4 s of the contact, to the composed distance of about 4 m.
- **Visibility:** hero at least 60 % visible, chest seen, no top-down close-up.
- **After takeoff:** no lens ahead of him, and no hidden run longer than 6 frames.

## Checks for the root (sim / render)

**fl12:**
- **Logs, in order:** `land clip r9` (LandHoldPoseT ≈ 0.62, left leg, right fist), then `land contact r9` (t ≈ 0.48, other clips 0.00), then `land hold released r9` (t ≈ 0.62, after ≈ 1.30 s).
- **Hold frames:**
  - knee and fist on the street, back leg under the hip;
  - mesh pitch 0;
  - no sideways slide after the contact frame.
- **Camera log/telemetry:** `WH_CAM r9 vehicle side swing` within about 0.1 s of the contact; `cam_slew` & 1024 on those frames.
- **Gates:**
  - `cam_dist_m` at least 2.8 for the rest of the hold;
  - longest hidden run outside breaches at most 6;
  - `hero_lands` = 1, `floating_end` unchanged.

**fl11, fl18:**
- the same three anim logs, and the kneel contact on the crater or roof;
- fl18 `camera_calm` unchanged.

**fl17:**
- The end hover beside parked cars may now swing the camera azimuth if a parked box blocks the composed spot.
- Watch for at most 4 vertical reversals (calm), and check the end yaw (r7 wanted about −180).

**All flight cases:** a count of bit-1024 frames, to confirm the swing stays off where no vehicle is near.

## Open points (not verifiable without a run)

- **Pose:** the kneel layer reshapes an approved clip (back thigh turned 50° inward). If the owner prefers the clip's own stance, `LandKneelContact=0` keeps the freeze and upright fixes only.
- **Skinning:** possible groin or knee skinning stretch at the 50° hip turn, not checked.
- **Parked boxes:** these use the union of both axes (r7), so a parked truck's cross can block more azimuths than the real body.
- **Moving vehicles:** each candidate is tested at now and +0.2 s only.
- **Stand-clear snap:** the 0.57 m stand-clear step now happens on the contact frame.
