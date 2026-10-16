# Hero v2 integration notes (owner request 2026-10-15)

Builder pass: source only. Nothing here has been compiled, launched or captured; the root session builds, tests and commits.
Engine APIs were checked against the UE 5.8 headers under `/Users/Shared/Epic Games/UE_5.8/Engine/Source` and against patterns that already compile in this module (`WebTravAnimInstance.cpp`, `WHCharAnimInstance.cpp`).

## Files

| File | Change |
|---|---|
| `Source/WebHomage/Traversal/Anim/WHHeroV2AnimInstance.h/.cpp` | **new.** `UWHHeroV2AnimInstance` (C++ only, no Anim Blueprint) + `FWHHeroV2AnimProxy`. State machine on the game thread, up to 4 crossfading clip tracks, proxy samples + blends the clips, ground lock, `WH_HEROV2` log. Static `ComputeRefFrame` (mesh up / forward / height from the ref pose + imported bounds). |
| `Source/WebHomage/Traversal/WebTravCharacter.h` | Config props `HeroV2HeightCm` (185), `HeroV2MaxBankDeg` (25), `HeroV2MaxPitchDeg` (20), `HeroV2YawRate` (16 /s); private `SetupHeroV2Mesh`, `HeroV2Frame`, `bHeroV2` + yaw / pitch / bank state. |
| `Source/WebHomage/Traversal/WebTravCharacter.cpp` | include; `SetupHeroMesh` tries v2 first (flight on, `-WHHeroV2` not 0, no explicit `-WHHeroMesh=`), else the unchanged v1 / legacy code; new `SetupHeroV2Mesh` and `HeroV2Frame`; `PoseFigure` calls `HeroV2Frame` just before `FigureRoot->SetWorldLocationAndRotation` when v2 is active; pre-roll end also resets the v2 instance. |

`-WHFlight=0` never reaches the v2 path (legacy Spider-Man unchanged). `-WHHeroV2=0`, or a missing / unloadable `SK_InvincibleV2`, or a mesh without `head`, `pelvis`, `left_/right_foot`, `left_/right_ankle`, falls back to the existing v1 (`SK_Invincible`) / HeroDev path unchanged.

## Mesh setup (SetupHeroV2Mesh)

- `SetAnimationMode(AnimationBlueprint)` + `SetAnimInstanceClass(UWHHeroV2AnimInstance)` + `SetSkeletalMesh`, glTF material kept (no lens mesh, no SpiderSuit slot; `UWHHeroSuitSubsystem` only touches meshes with SpiderSuit / Lens slots).
- Frame from the asset: up = head − mid(feet), forward = Σ(foot − ankle) ⟂ up (same rule as `tools/invincible/post_take.py`), height = imported-bounds extent along up, sole = lowest bounds point along up.
- Relative transform on `FigureRoot` (the feet / capsule bottom): rotation = inverse(MakeFromXZ(fwd, up)), uniform scale = 185 cm / height, location puts the sole point under the pelvis at the origin (pelvis = the pivot of every flight clip).
- `SetBoundsScale(2)`: horizontal clips leave the A-pose bounds (the source mesh is 200 × 92 × 36 units: arms-down A pose).
- Source check (offline FK of the GLBs, no renderer): mesh vertices span exactly 200 units along glTF Y; ref joints pelvis +13.4, head +70.2, feet −97, soles −100. The Unreal unit scale depends on the Interchange conversion, so it is computed at runtime and logged.

## Orientation (HeroV2Frame)

The flight body quaternion is not applied to the v2 mesh. `FigureRoot` gets:
- yaw = `Traversal->Facing()` (travel heading in a fly line, camera heading in a hover), eased at `HeroV2YawRate`;
- roll = `Anim.Flight.Bank` clamped to ±25°, eased 8 /s, about the forward axis (− bank = right side down in a right turn, the flight's own convention);
- pitch = flight-path angle (atan2(vz, vh), climb = nose up) clamped to ±20° × `PitchFreedom()` (1 for fly / boostHold / dash / breach minus their LaunchUp blend, boostLaunch, the land dive; 0 for hover, launchUp, takeoff, brake, landHero after impact, ground), eased 8 /s. Documented exception allowed by the brief (≤ 20°).
- airborne root = body centre − Q·up × 95 cm; grounded root = `Anim.RootPos` (traversal feet point).

## State → clip

| Traversal / flight input | v2 state | Clip | Timing |
|---|---|---|---|
| mode Ground / Land (not landHero) | groundIdle | AS_GroundIdle (loop) | no walk clip; ground lock on |
| sub `takeoff` | takeoff | AS_Takeoff (one-shot) | starts at `TakeoffClipStart` 0.5 s (push-off ~0.55 s; the flight launches on the press); sticky through the following hover until done, then launchUp if vz > 5 m/s else hover |
| sub `hover`, Space held, vz > 5 m/s (off < 2.5) | launchUp | AS_LaunchUp (loop) | |
| sub `hover` | hover | AS_Hover (loop) | |
| sub `fly` | fly | AS_Fly (loop) + AS_LaunchUp blend | blend weight = smoothstep(50°, 70°, path pitch), eased 5 /s |
| sub `brake` + `Flight.ChargeK > 0` (super charge) | boostLaunch | AS_BoostLaunch (one-shot) | clip t = 0.42 × invsmoothstep(ChargeK) — ChargeK is smoothstep(SuperT / SuperChargeTime) in real seconds, so the 0.42 s burst frame lands on the sonic-boom frame regardless of the charge slow-mo |
| sub `boost` right after the boom | boostLaunch (continues) | AS_BoostLaunch | plays from the burst to its end (0.97 s), then boostHold |
| sub `boost` | boostHold | AS_BoostHold (loop) + AS_LaunchUp blend | |
| sub `brake` (no charge) | brake | AS_Brake (one-shot, rate 1.4) | sticky through the hover until done, then hover (clip ends on hover's first pose). A brake from < 8 m/s out of hover / launchUp / takeoff / ground keeps the hover (the clip starts horizontal) |
| sub `slam` (F / Square or double-tap Space dive) | landHero (dive) | AS_LandHero | plays 0 → 0.2 s (`LandDiveHoldT`) and holds; once time-to-impact (traversal ground index, same probe as the v1 anim) ≤ 0.37 − t it plays so that t = 0.37 s (`LandImpactT`) on the landing frame (catch-up ≤ 3×); an earlier impact jumps to 0.35 s with a 0.08 s blend |
| mode Land / Ground sub `landHero` | landHero (impact) | AS_LandHero | continues from the impact frame to the end (2.77 s), then groundIdle; walking after 0.3 s cuts to groundIdle; a hard landing without a dive enters at 0.29 s |
| sub `dash` | dash | AS_Fly at 1.6× + LaunchUp blend | |
| sub `breach` | breach | AS_BoostHold | hero is hidden in the solid |

Impact frame source: offline FK of `docs/invincible/character/meshy/hero_land.glb` — the lead wrist reaches its lowest point at frame 11 (0.367 s) while the pelvis descent stops (0.37 → 0.43 s); feet take over as the lowest point from 0.5 s.
Missing clips fall back: BoostHold / BoostLaunch / FlyingFistKick → Fly, Takeoff → LaunchUp, anything else → Hover, no Hover → reference pose.
AS_PunchCombo, AS_Jab, AS_FlyingFistKick are loaded but not triggered (no combat trigger in flight mode).

## Ground lock

Retargeted grounded clips keep the pelvis at the rest height, so their feet float (offline FK: AS_Takeoff crouch feet ~60 units = ~0.55 m above the soles, AS_LandHero kneel ~45–50 units, AS_LandHero end stance ~15 units). The proxy shifts the root bone along the mesh up axis so the lower foot joint sits at its ref-pose height, weighted by `GroundLockW`: 1 in groundIdle and landHero after impact, takeoff fading 1 → 0 over `TakeoffUnlockT` 0.2 s, 0 in the air; eased with `GroundLockTau` 0.06 s; shift clamped to 0.45 × body height. The dive → impact therefore drops the body onto the floor within ~0.1 s.

## Blend times (s, `-WHHeroV2Tune=Name=Value,...`)

BlendDefault 0.2 · BlendToTakeoff 0.1 · BlendTakeoffOut 0.25 · BlendHoverLaunchUp 0.25 · BlendFlyHover 0.3 (fly-type ↔ upright) · BlendToBoostLaunch 0.12 · BlendBoostLaunchOut 0.25 · BlendToBrake 0.15 · BlendBrakeToHover 0.2 · BlendToLandDive 0.15 · BlendLandImpact 0.08 · BlendLandToIdle 0.3 · BlendDash 0.15.

Other tunables (same flag): BoostBurstT 0.42, LandImpactT 0.37, LandDiveHoldT 0.2, TakeoffClipStart 0.5, TakeoffUnlockT 0.2, BrakeClipRate 1.4, DashRate 1.6, LaunchUpPitchDeg 60, LaunchUpBandDeg 10, UpBlendRate 5, HoverClimbVz 5, BrakeMinSpeed 8, GroundLockTau 0.06, LogMinInterval 0.05.
Character: `-WHHeroV2=0` (off), `-WHHeroV2Height=<cm>`; config `HeroV2MaxBankDeg`, `HeroV2MaxPitchDeg`, `HeroV2YawRate`.

## Log lines

- `WH_HEROV2 mesh /Game/Invincible/HeroV2/SK_InvincibleV2...: N bones, height H units -> 185 cm (scale S), up(asset)=... fwd(asset)=... bottom B footJoint F units` (once; or `... not built: v1 / legacy hero path`).
- `WH_HEROV2 anim init: 12/12 clips from /Game/Invincible/HeroV2/Anims (missing: none; skeleton mismatch: none), ref ok up ... fwd ... footUp ... height ...` — printed per anim-instance init; the first line may come from the init before `SetSkeletalMesh` (the second one, with the v2 mesh, is the relevant one).
- `WH_HEROV2 state <name> clip <AS_...> t=<world s> clipT=<s> blend=<s> from=<last logged> mode=<EWebTravMode int> sub=<sub> speed=<m/s>[ (+N suppressed)]`, at most one per 0.05 s real time; a state suppressed by the limit is printed later if it is still current.
- `WH_HEROV2 tune <Name> = <value>`.

## What to check in captures / logs

1. Mesh line: height units consistent with the bounds (source GLB = 200 units; ×100 if Interchange converted metres), scale giving 185 cm, up(asset) ≈ +Z and a horizontal fwd. Hero ~1.85 m next to the capsule / street props, feet on the street in idle, facing the camera-forward heading.
2. Init line: 12/12 clips, no skeleton mismatch, ref ok.
3. Fly: body horizontal from the clip, not double-pitched (no nose-down 90° extra), bank ≤ 25°, slight nose-up on climbs only; steep climb (> 60°) → upright LaunchUp blend.
4. Super boost: `state boostLaunch` at the `WH_FLIGHT super charge` line; burst pose on the `WH_FLIGHT sonic boom` frame; `boostHold` ~0.55 s later.
5. Double-tap dive: `state landHero` at `WH_FLIGHT double-tap dive`; held dive pose; impact pose on the `WH_FLIGHT heroLand` frame; three-point landing with feet on the floor (no 0.5 m float / sink); stand-up then `groundIdle`.
6. Takeoff from the street: no visible crouch hanging in the air; push-off pose at the launch; LaunchUp with Space held.
7. Brake from cruise: horizontal → pull-up → hover with no pop at the hand-off; E in a slow hover keeps the hover.
8. Crossfades: no one-frame pose pops at state changes (state lines give the frame).
9. `-WHFlight=0` and `-WHHeroV2=0` runs: unchanged legacy / v1 visuals and logs (no `WH_HEROV2 state` lines).

## Known limits / uncertain points

- The proxy frame is written into the proxy from `NativeUpdateAnimation` via `GetProxyOnGameThread` (UE 5.8 calls `PreUpdateAnimation` → proxy `PreUpdate` before `NativeUpdateAnimation`, so a PreUpdate copy would lag one frame). Pattern is standard but not yet exercised in this module.
- The ground lock assumes compact index 0 is the root bone with component-space local transform (true for any skeleton); if Interchange added an extra root above `pelvis`, the shift still applies to the whole body.
- `LandImpactT` / `TakeoffClipStart` come from the source GLBs; if the Interchange import resampled or trimmed the clips differently, retune via `-WHHeroV2Tune`.
- v1-bone telemetry in `WebTravCharacter.cpp` (`hand_L/R`, `hips`, `foot_L/R`, ... ) reads zero vectors for the v2 skeleton; the engine's "Could not find bone" message is Log verbosity on `LogAnimation` (default Warning), so it stays out of the log. The rescue crane carry pose (`UpdateCarry`) and the v1 procedural flight layers (wall-side tuck, fist swap, carry IK) live in `UWebTravAnimInstance` and are not active on v2.
- The hover stick lean of the flight body quaternion is not applied to v2 (upright hover clip only).
- No walk clip: AS_GroundIdle plays while walking.
