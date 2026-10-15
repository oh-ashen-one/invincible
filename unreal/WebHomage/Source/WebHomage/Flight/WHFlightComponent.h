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
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BreachMaxTime = 0.3f; // s: longest pass through a solid (the hero is hidden in it)
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
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SuperLaunchK = 0.8f;      // share of SuperSpeed at the boom (the rest within ~0.2 s)
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
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float LaunchLagT = 0.14f;       // s the camera hangs back at the launch (he rockets away from it)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float LaunchLagK = 0.35f;       // camera speed during that hang, share of the hero's
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float CamFovCap = 90.f;         // deg vertical cap for the flight FOV terms
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

	bool IsFlightOn() const { return bFlightOn; }
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
	void HeroLand(UWebTraversalComponent& T, double Floor, double ImpactSpeed, bool bSlam);
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
};
