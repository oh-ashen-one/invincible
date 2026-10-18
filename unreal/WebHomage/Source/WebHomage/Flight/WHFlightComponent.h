// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
// Invincible flight conversion (owner request 2026-10-15): the flying hero's body controller. It replaces the web-swing state
// machine of UWebTraversalComponent while it is on (-WHFlight=0 = the legacy Spider-Man traversal, untouched): the traversal
// component keeps owning the body state (position / velocity / mode / C1 anim contract), so the chase camera, the anim instance,
// telemetry and the capture harness keep working; this component steps that state with flight physics instead of swinging.
//
//   ground:  walk / run (the traversal's own ground step, jump / parkour / wall-run inputs filtered out)
//   takeoff: Space / Cross on the ground (or fly held)   -> vertical launch into a hover
//   hover:   stick strafes along the camera, Space climbs, C / Ctrl descends (and lands near the floor)
//   fly:     RMB / R2 held -> accelerate along the hero's NOSE (acceleration curve to CruiseSpeed). Owner feedback 2026-10-15 #3
//            (flight-sim feel): mouse / right stick move the nose (AimYaw / AimPitch, at most NoseLeadMaxDeg ahead of the travel), the
//            travel turns toward it at no more than FlyLatAccel of lateral acceleration (turn radius v^2 / a grows with speed), stick X
//            turns the nose at StickTurnRate with a StickRollDeg roll, climbing costs speed / diving gains a little (ClimbEnergyK), the
//            chase camera follows the hero's heading with lag (FWebTravCamera::bFlightAttitude). Space / C pitch while held.
//   super:   owner feedback #1: Shift / L3 from fly OR hover -> SONIC-BOOM SUPER BOOST: charge (SuperChargeTime real s: snap to a hang,
//            body coils, world slow-mo, camera pulls in, vapour gathers), sonic boom at the launch (event sonicBoom: vapour cone /
//            shock ring / flash, camera kick + FOV punch), launch at SuperLaunchK x SuperSpeed toward the stick (camera-relative) or
//            the nose, held Shift sustains SuperSpeed (steerable, SuperLatAccel: wide turns), release decelerates to cruise over
//            SuperDecelTime; SuperCooldown before the next one. (Replaces the old held boost to 160 m/s + boom at 120 m/s.)
//   brake:   E / Triangle -> instant stop into a hover
//   dash:    Q / L1 -> short burst along the stick (or the aim)
//   slam:    F / Square in the air -> dive straight down into a superhero landing (crater over HeroLandMinSpeed)
//   dive:    owner feedback #2: Space twice within DoubleTapTime while airborne -> the slam dive with hard acceleration (arrives from any
//            height in about DiveTime s) into the superhero landing; a single Space keeps its meaning (takeoff / climb)
//   breach:  hitting a facade above BreachSpeed carries through the building (destruction proxies at both faces, short slow-mo)
// The hero cannot be hurt: every contact is a slide, a breach or a landing.
// Simulation units are METRES (traversal convention), UE axes (Z up). Events carry metres; the breach director converts.
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Traversal/WebTravTypes.h"
#include "WHFlightComponent.generated.h"

class UWebTraversalComponent;
class AWHLifeTraffic;   // critic r6 #5 (camera lens guard: vehicle boxes)
struct FWHLensObb;      // r10 (Traversal/WebTravCamera.h)

/** Owner feedback 2026-10-15 #1: phases of the sonic-boom super boost (plain C++ enum, not reflected). */
enum class EWHSuperPhase : uint8 { None, Charge, Run, Decel };

UCLASS(ClassGroup=(WebHomage), meta=(BlueprintSpawnableComponent))
class WEBHOMAGE_API UWHFlightComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UWHFlightComponent();

	/** Flight owns the body (default on; -WHFlight=0 turns it off at BeginPlay of the hero). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") bool bFlightOn = true;

	// ---- speeds (m/s). Game scale, not physics: the city is a few km across.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float HoverSpeed = 9.f;      // stick strafe in a hover
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float VertSpeed = 10.f;      // Space / C climb and descent in a hover
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float CruiseSpeed = 55.f;    // fly held
	// (owner feedback #1: Shift no longer ramps to BoostSpeed; it stays the reference "fast" speed for turn / FX / severity scales)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BoostSpeed = 160.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SonicSpeed = 120.f;    // the boost pose (sub "boost") shows above 0.8 x this
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SonicReset = 95.f;     // (unused since owner feedback #1: the boom fires only at a super launch)
	// ---- acceleration curve: a(v) = Accel x (1 - (v / target)^AccelExp) toward the target, Decel x (v - target) above it
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float Accel = 70.f;          // m/s^2 at rest (cruise)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BoostAccel = 150.f;     // (unused since owner feedback #1: SuperAccel)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float AccelExp = 2.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float Decel = 1.4f;          // 1/s above the target speed (boost released: ~1.5 s glide down to cruise)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float HoverRate = 4.f;       // 1/s approach of the hover velocity (low speed)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float HoverGlideRate = 1.6f; // 1/s approach of the hover velocity coming out of fast flight
	// ---- steering: turn rate of the velocity toward the aim (deg/s). Owner feedback #3: the rate is min(TurnRateSlow, LatAccel / speed)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float TurnRateSlow = 240.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float TurnRateFast = 75.f;   // (unused since owner feedback #3: FlyLatAccel / SuperLatAccel)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float StickYawDeg = 35.f;    // (unused since owner feedback #3: StickTurnRate)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float ClimbPitchDeg = 30.f;   // Space / C pitch the aim up / down this much while flying
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BankMaxDeg = 70.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float HoverLeanDeg = 14.f;
	// ---- moves
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float TakeoffVz = 16.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float TakeoffDur = 0.4f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BrakeDur = 0.3f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BrakeRate = 28.f;      // 1/s velocity decay through the brake
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float DashDv = 45.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float DashDur = 0.28f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float DashCooldown = 0.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SlamSpeed = 95.f;
	// ---- contacts
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BreachSpeed = 45.f;    // facade hit at or above this = through-building
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BreachKeep = 0.8f;     // speed kept through a building
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BreachMaxDepth = 80.f; // m: deeper solids are not breached (slide instead)
	// critic r5 #3 (hidden 12-24 frames per breach): 0.3 -> 0.06 s, ~4 frames at 60 fps (the pass is a punch-through; the camera holds on the hole)
	// critic r6 #1 (r7, breach jump cut): the camera now follows him THROUGH the solid at <= 3 m per frame, so the pass speed is bounded by
	// BreachPassStepM per rendered frame (156 m/s at 60 fps) and the time bound is 0.14 s (a 20 m block ~8 frames, never slow-mo: world time is 1)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BreachMaxTime = 0.14f; // s: pass time target (speed raised up to the cap below)
	// critic r6 #1: the pass (and the first BreachExitHoldT s after the exit) never moves the body more than this per rendered frame (m; 0 = r6)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BreachPassStepM = 2.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BreachPassMaxV = 240.f; // m/s ceiling of that cap at high frame rates
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BreachExitHoldT = 0.2f; // s after the exit the speed stays at the pass cap
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BreachCooldown = 0.25f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float PunchPinTime = 0.3f;  // s of fly held head-on against a facade before punching through
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float HeroLandMinSpeed = 30.f; // impact speed for a crater landing
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SoftLandSpeed = 12.f;    // under this a floor contact is a gentle touchdown
	// critic r2 (fl13: hover touchdowns still met the floor at ~5 m/s): a hover descent (drop held) is capped at
	// sqrt(TouchdownV^2 + 2 TouchdownDecel max(0, h - TouchdownSlowH)) m/s at h m over the floor -- constant deceleration from VertSpeed
	// (~4 m up) to TouchdownV, held at TouchdownV through the last TouchdownSlowH m (0 = none; 2.0 with TouchdownV 1.95 / Decel 26 gives
	// |vz| <= 2 over the final 2 m at ~0.95 s extra)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float TouchdownV = 1.4f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float TouchdownDecel = 12.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float TouchdownSlowH = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float HeroLandLock = 0.9f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float FlyoverEvery = 0.5f;     // s between flyover crowd stimuli
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float FlyoverMaxH = 140.f;     // m over the street: higher passes are not noticed

	// ---- owner feedback 2026-10-15 #1: Shift = sonic-boom super boost
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SuperChargeTime = 0.42f;  // REAL s of the charge (snap stop, coil, slow-mo)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SuperChargeStopRate = 16.f; // 1/s velocity decay through the charge (55 m/s -> ~0 in 0.4 s)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SuperChargeSlowMo = 0.6f; // global time dilation through the charge (1 = none; -WHNoSlowMo disables)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SuperChargeLean = 0.35f;  // rad: the body leans back (coils) through the charge
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SuperSpeed = 300.f;       // m/s held super-speed line
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SuperLaunchK = 0.8f;      // share of SuperSpeed the launch ramp reaches (the rest within ~0.2 s)
	// critic r4 fl04 (0 -> 243 m/s in one telemetry step): the launch accelerates from SuperLaunchV0 to SuperLaunchK x SuperSpeed over
	// SuperLaunchRampT s (explosive start, smooth arrival; 0 = the old one-frame launch)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SuperLaunchRampT = 0.16f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SuperLaunchV0 = 30.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SuperAccel = 380.f;       // m/s^2 at rest toward SuperSpeed
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SuperLatAccel = 110.f;    // m/s^2 lateral in the super line (turn radius 818 m at 300 m/s)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SuperDecelTime = 1.5f;    // s: Shift released -> back at cruise
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SuperDecelRate = 2.0f;    // 1/s exponential approach to cruise in that time (5 % left at 1.5 s)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SuperCooldown = 2.0f;     // s after the super line ends before the next charge
	// camera / FX feel of the super boost (pushed to FWebTravCamera by AWebTravCharacter::FlightFrame)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SuperChargePullM = 1.1f;  // m the flight camera pulls in through the charge
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SuperFovAdd = 14.f;       // deg of extra vertical FOV at full super speed (cap CamFovCap)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SuperShake = 0.16f;       // continuous camera shake floor at full super speed (0..0.75)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SuperBlur = 1.4f;         // motion-blur floor at full super speed (camera MotionBlur units)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BoomFovDeg = 12.f;        // deg FOV punch at the boom (springs back ~0.35 s)
	// critic r4 fl04 / fl12 (the hang let the lens fall 3.2 -> 24 m behind, hero ~12 px): 0.14 -> 0 (off); the boom reads through the FOV
	// punch + kick + shake, and the camera leash (FWebTravCamera::FlightLeashM) bounds any lag
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float LaunchLagT = 0.0f;        // s the camera hangs back at the launch (he rockets away from it)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float LaunchLagK = 0.35f;       // camera speed during that hang, share of the hero's
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float CamFovCap = 90.f;         // deg vertical cap for the flight FOV terms
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float CamLeashM = 5.5f;         // critic r4 fl04: the flight lens never trails the hero by more (m; 0 = off)
	// critic r4 fl16 (glued 5.5 s to a facade, head in a fire escape): a slow fly line (under breach speed) keeps the body centre
	// WallStandoffM off a facade (+ WallHeadReachM when heading into it), bleeds the speed into the wall smoothly (WallApproachRate 1/s)
	// and turns it along the wall toward the free side (tangential travel, else up / left / right), at least SlideMinSpeed with fly held
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float WallStandoffM = 1.1f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float WallHeadReachM = 0.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float WallApproachRate = 6.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SlideMinSpeed = 4.f;
	// ---- owner feedback #2: double-tap Space = superhero-landing dive
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float DoubleTapTime = 0.3f;     // s between the two airborne Space presses
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float DiveAccel = 160.f;        // m/s^2 minimum downward acceleration of the dive
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float DiveTime = 2.2f;          // s: from higher up the acceleration grows so the floor is reached in ~this
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float DiveMaxSpeed = 600.f;     // m/s cap
	// ---- owner feedback #3: flight-simulator feel (the plane is the hero)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float FlyLatAccel = 60.f;       // m/s^2 lateral in the fly line (turn radius 50 m at 55 m/s, 427 m at 160)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float NoseLeadMaxDeg = 60.f;    // deg the nose may lead the travel heading
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float LookYawK = 1.0f;          // nose yaw per rad of horizontal look input
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float LookPitchK = 1.0f;        // nose pitch per rad of vertical look input
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float StickTurnRate = 70.f;     // deg/s nose turn from stick X in the fly / super line
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float StickRollDeg = 20.f;      // deg extra roll from stick X
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float ClimbEnergyK = 1.2f;      // x g x sin(climb angle): speed lost climbing / gained diving
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float NoseBodyK = 0.2f;         // the body points this share toward the nose (angle of attack)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float CamYawLagT = 0.32f;       // s smooth time of the camera heading chasing the hero
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float CamLeadK = 0.35f;         // share of the nose lead the camera heading takes (looks into the turn)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float CamRollK = 0.18f;         // camera roll per rad of hero bank (horizon rolls with the bank)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float CamRollMaxDeg = 12.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float FlyFovAdd = 9.f;          // deg of FOV widening over 40 m/s .. BoostSpeed (was a fixed 7)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SpeedShake = 0.07f;       // camera shake floor at BoostSpeed in ordinary flight
	// ---- owner request 2026-10-16 ("even if you're near the floor you should still always be floating"; roof hero-landing freeze): in
	// flight mode the hero never enters the traversal's GROUND mode. A hero landing is an airborne hold (sub landHero, velocity zero,
	// feet on the surface the flight found) of LandHoldTime s, then he rises into the float; every other floor contact is a touch into the
	// float. The float = the hover sub held FloatHeightM over the surface under him (traversal index ray from the body centre + a downward
	// sphere sweep against the same collision the flight sweep lands on). WASD = hover glide, Space climbs, C / Ctrl settles to the float
	// height instead of touching down. -WHFloat=0 restores the r6 ground mode (A/B only).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") bool bAlwaysFloat = true;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float FloatHeightM = 0.45f;     // feet over the surface while floating near it
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float FloatCatchM = 1.6f;       // hands-off: the float pulls him down within this height (above: the hover holds its altitude)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float FloatUpK = 5.f;           // 1/s: rise toward the float height (from a landing hold / a step up)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float FloatDownK = 3.f;         // 1/s: settle down onto it
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float FloatRiseMax = 4.f;       // m/s cap of that rise
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float FloatVzRate = 16.f;       // 1/s approach of the float's vertical speed (with the gains above: no bob, zeta 0.9 / 1.15)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float FloatFloorFall = 8.f;     // 1/s: the surface estimate follows a lower surface (a higher one at once)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float FloatProbeM = 8.f;        // m of the downward sweep from the body centre (per substep)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float LandHoldTime = 1.3f;      // s: the hero landing holds still (AS_LandHero) before the rise
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float LandHoldCancelT = 0.9f;   // s: Space / fly press may end the hold after this
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float TouchKeepH = 0.6f;        // share of the horizontal speed a non-hero floor touch keeps
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float DiveMinHeightM = 2.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SkimLiftM = 0.9f;        // r8 render fl12: a fly line skimming the street holds this much extra height (the prone body slid on the asphalt)    // the double-tap dive needs this much room below (lower: the second tap climbs)

	bool IsFlightOn() const { return bFlightOn; }
	// owner request 2026-10-16 (always floating): state read by the v2 anim instance / telemetry
	bool IsFloatOn() const { return bFlightOn && bAlwaysFloat; }
	bool IsLandHold() const { return bLandHold; }
	double LandHoldS() const { return LandHoldT; }               // s into the current hero-landing hold
	double SurfaceBelowZ() const { return SurfBelowZ; }          // m: the surface under the hero this frame (-1000 = none within 400 m)
	double FloatGapM() const { return FloatGap; }                // m: feet over the float surface this frame (99 = none)
	int32 FloatTouchCount() const { return TouchCount; }         // increments on each non-hero floor touch (anim knee dip)
	double FloatTouchSpeed() const { return TouchVz; }           // m/s downward speed of the last touch
	/** One frame of the hero body under flight (called by UWebTraversalComponent::UpdateTraversal while flight is on). */
	void StepFlight(UWebTraversalComponent& T, double Dt, FWebTravInput I);
	/** -WHFlightTune=Name=Value,... (float properties). */
	void ApplyTune(const FString& Tune);

	// ---- telemetry (read-only)
	FName FlightSub() const { return Sub; }
	double SpeedNow() const { return SpeedM; }
	int32 BoomCount = 0, BreachCount = 0, HeroLandCount = 0, DashCount = 0, BrakeCount = 0;
	int32 SuperCount = 0, DiveCount = 0;   // owner feedback #1 / #2
	bool IsBreaching() const { return bBreach; }
	FVector BreachDirection() const { return BreachDir; }   // critic r6 #1: the pass direction (unit) for the follow-through camera
	// critic r6 #5 (camera lens guard, flight mode): the traffic vehicles (moving + parked, AWHLifeTraffic) within RadiusM (horizontal) of
	// NearM, in metres. r10: oriented boxes from each vehicle's real mesh bounds and render transform (AWHLifeTraffic::GetCarBoxes)
	void GatherVehicleBoxes(const FVector& NearM, double RadiusM, TArray<FWHLensObb>& Out) const;
	// critic r6 #5: render-collision lens queries on the visibility channel (metres), ignoring the hero (owner) and Ignore
	bool LensOverlapExt(const FVector& PM, double RM, const AActor* Ignore) const;
	bool LensSweepExt(const FVector& AM, const FVector& BM, double RM, const AActor* Ignore, double& OutDistM) const;
	// owner feedback #1 / #3: state the pawn pushes to the camera / breach director each frame
	bool IsAttitude() const { return bAttitude; }              // look input steers the nose; the camera chases the hero's heading
	double CameraYawGoal() const { return CamYawGoal; }        // rad: heading the camera chases (travel + CamLeadK x nose lead)
	bool IsSuperCharging() const { return SuperState == EWHSuperPhase::Charge; }
	bool IsSuperOn() const { return SuperState != EWHSuperPhase::None; }
	double ChargeKNow() const { return ChargeK; }              // 0..1 through the charge
	double SuperKNow() const { return SuperK; }                // 0..1 super-speed weight (falls with the speed while decelerating)

private:
	using ESuper = EWHSuperPhase;
	void SuperLaunch(UWebTraversalComponent& T, const FVector& Aim, const FVector& RightN, const FWebTravInput& I);
	void EndSuper(bool bCooldown);
	void StartDive(UWebTraversalComponent& T);
	void StepAirSub(UWebTraversalComponent& T, double H, const FWebTravInput& I);
	bool MoveAndCollide(UWebTraversalComponent& T, double H, const FWebTravInput& I);
	bool StartBreach(UWebTraversalComponent& T, const FVector& HitPos, const FVector& HitN, const FVector& Dir);
	void StepBreach(UWebTraversalComponent& T, double H);
	/** critic r2 fl14: keep Speed, turned along the facade (normal HitN) toward the free direction (no dead stop against a solid). */
	void DeflectFree(UWebTraversalComponent& T, const FVector& HitN, double Speed);
	/** the free direction along a facade (normal HitN) for a deflection: the tangential travel when it is at least TanShare of Speed, else
	 *  up / along the wall to either side, whichever has the longest clear run (ties: up) */
	FVector FreeAlong(UWebTraversalComponent& T, const FVector& HitN, double Speed, double TanShare) const;
	/** critic r4 fl16: the slow-flight facade standoff (see WallStandoffM); true when a facade is within range */
	bool WallStandoff(UWebTraversalComponent& T, double H, const FWebTravInput& I);
	void HeroLand(UWebTraversalComponent& T, double Floor, double ImpactSpeed, bool bSlam);
	// owner request 2026-10-16 (always floating)
	/** the surface under the body centre within Reach m: max of the traversal index ray (from the centre, so a surface the feet touch is
	 *  never started under) and a downward sphere sweep (the collision the flight lands on); -1000 = none */
	double SurfaceUnder(const UWebTraversalComponent& T, double Reach) const;
	/** SurfaceUnder(FloatProbeM), filtered: a higher surface at once, a lower one at FloatFloorFall (a drop over FloatCatchM at once) */
	double FloatSurface(const UWebTraversalComponent& T, double H);
	void StepLandHold(UWebTraversalComponent& T, double H, bool bCancelPress);
	/** float mode: a fly-type line (fly / boost / dash / breach) meeting the floor under HeroLandMinSpeed of descent skims it (no touch) */
	bool FloorSkim(double Impact) const;
	void SkimFloor(UWebTraversalComponent& T, double Impact, const FVector& At);
	void EnterFloat(UWebTraversalComponent& T, const TCHAR* Why);
	void Takeoff(UWebTraversalComponent& T);
	FQuat FlightOrient(UWebTraversalComponent& T, double Dt, const FWebTravInput& I);
	void SetFlySub(UWebTraversalComponent& T, FName NewSub);
	void Event(UWebTraversalComponent& T, FName Type, float Sev, const FVector& Pos, const FVector& Dir, float K = 1.f);

	FName Sub;
	double SubT = 0.0, FlightT = 0.0, SpeedM = 0.0;
	double DashCd = 0.0, BreachCd = 0.0, FlyoverT = 0.0, BoomK = 0.0;
	FVector DashDir = FVector::ForwardVector;
	bool bSlam = false, bRightFist = true;
	// owner feedback #1: super boost state. SuperT = REAL seconds in the charge (game seconds in Run / Decel); SuperCd = cooldown
	ESuper SuperState = ESuper::None;
	double SuperT = 0.0, SuperCd = 0.0, ChargeK = 0.0, SuperK = 0.0, LaunchK = 0.0;
	// critic r4 fl04: the launch ramp (s into it, < 0 = none), its direction and end speed
	double LaunchRampS = -1.0, LaunchVEnd = 240.0;
	FVector LaunchDir = FVector::ForwardVector;
	// critic r4 fl16: the slide direction picked for a head-on facade contact, held SlideDirT s so it does not flip-flop
	FVector SlideDir = FVector::ZeroVector;
	double SlideDirT = 0.0;
	FVector WallNLast = FVector::ZeroVector;
	FVector CamWallN = FVector::ZeroVector;   // critic r5 #7: the facade of the live slide contact (standoff or swept), for the camera yaw goal
	// owner feedback #2: seconds since the last airborne Space press (double-tap window); the dive's downward acceleration
	double JumpTapT = 99.0, DiveAccelNow = 160.0;
	bool bDiveDrop = false;
	// owner feedback #3: the nose (attitude) heading the fly line steers by, and the heading the camera chases
	double AimYaw = 0.0, CamYawGoal = 0.0;
	bool bAttitude = false;
	// breach: straight segment through the solid, entry -> exit (m), at BreachV m/s
	bool bBreach = false;
	FVector BreachA = FVector::ZeroVector, BreachB = FVector::ZeroVector, BreachDir = FVector::ForwardVector;
	double BreachLen = 0.0, BreachS = 0.0, BreachV = 0.0, BreachExitV = 0.0, PinT = 0.0;
	FVector BreachExitN = FVector::ForwardVector;
	// critic r6 #1: last rendered frame time (pass speed cap), and the post-exit speed hold (s left, m/s)
	double LastFrameDt = 1.0 / 60.0, ExitCapT = 0.0, ExitCapV = 0.0;
	// critic r6 #5: the traffic actor for GatherVehicleBoxes (looked up again at most every 2 s while missing)
	mutable TWeakObjectPtr<AWHLifeTraffic> TrafficRef;
	mutable double TrafficLookT = -100.0;
	// orientation springs
	double Bank = 0.0, Pitch = 0.0, RollS = 0.0, LastVelYaw = 0.0, FlyK = 0.0, HoverYaw = 0.0;
	bool bHaveVelYaw = false, bHoverYawInit = false;
	FVector2D StickBody = FVector2D::ZeroVector;
	double Climb = 0.0;
	// flight aim pitch (rad, + = down, same sign as the camera): the chase camera's output pitch is its look-down at the hero plus a look
	// offset that decays 1.5 s after the stick is released, so steering by Cam->Forward() made every hands-off fly line dive (fl03 sim:
	// -51 m in 9 s) and let a held climb fade out. The fly line keeps its own pitch instead, moved only by vertical look input.
	double AimPitch = 0.0;
	double WallSideV = 0.0, WallDistV = 99.0, WallT = 0.0;   // last facade slide contact (anim wall-side tuck), held 0.25 s
	bool bFlyHeldPrev = false;
	// owner request 2026-10-16 (always floating): hero-landing hold, float surface estimate, touch counter
	bool bLandHold = false, bFloatFloorValid = false, bFloatInit = false;
	double LandHoldT = 0.0, HoldFloorZ = 0.0, FloatFloorZ = 0.0, SurfBelowZ = -1000.0, FloatGap = 99.0, TouchVz = 0.0;
	int32 TouchCount = 0;
};
