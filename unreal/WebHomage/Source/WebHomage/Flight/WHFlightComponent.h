// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
// Invincible flight conversion (owner request 2026-10-15): the flying hero's body controller. It replaces the web-swing state
// machine of UWebTraversalComponent while it is on (-WHFlight=0 = the legacy Spider-Man traversal, untouched): the traversal
// component keeps owning the body state (position / velocity / mode / C1 anim contract), so the chase camera, the anim instance,
// telemetry and the capture harness keep working; this component steps that state with flight physics instead of swinging.
//
//   ground:  walk / run (the traversal's own ground step, jump / parkour / wall-run inputs filtered out)
//   takeoff: Space / Cross on the ground (or fly held)   -> vertical launch into a hover
//   hover:   stick strafes along the camera, Space climbs, C / Ctrl descends (and lands near the floor)
//   fly:     RMB / R2 held -> accelerate along the camera aim (acceleration curve to CruiseSpeed); stick X yaws, Space / C pitch
//   boost:   Shift / L3 while flying -> BoostSpeed; crossing SonicSpeed fires a sonic boom (event + crowd stimulus + camera kick)
//   brake:   E / Triangle -> instant stop into a hover
//   dash:    Q / L1 -> short burst along the stick (or the aim)
//   slam:    F / Square in the air -> dive straight down into a superhero landing (crater over HeroLandMinSpeed)
//   breach:  hitting a facade above BreachSpeed carries through the building (destruction proxies at both faces, short slow-mo)
// The hero cannot be hurt: every contact is a slide, a breach or a landing.
// Simulation units are METRES (traversal convention), UE axes (Z up). Events carry metres; the breach director converts.
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Traversal/WebTravTypes.h"
#include "WHFlightComponent.generated.h"

class UWebTraversalComponent;

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
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BoostSpeed = 160.f;    // fly + boost held
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SonicSpeed = 120.f;    // crossing this upward = sonic boom
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SonicReset = 95.f;     // must drop under this before the next boom
	// ---- acceleration curve: a(v) = Accel x (1 - (v / target)^AccelExp) toward the target, Decel x (v - target) above it
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float Accel = 70.f;          // m/s^2 at rest (cruise)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BoostAccel = 150.f;     // m/s^2 at rest (boost)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float AccelExp = 2.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float Decel = 1.4f;          // 1/s above the target speed (boost released: ~1.5 s glide down to cruise)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float HoverRate = 4.f;       // 1/s approach of the hover velocity (low speed)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float HoverGlideRate = 1.6f; // 1/s approach of the hover velocity coming out of fast flight
	// ---- steering: turn rate of the velocity toward the aim (deg/s) from slow to boost speed
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float TurnRateSlow = 240.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float TurnRateFast = 75.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float StickYawDeg = 35.f;     // stick X adds this much yaw to the aim while flying
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
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BreachMaxTime = 0.45f; // s: longest pass through a solid (the hero is hidden in it)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float BreachCooldown = 0.25f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float PunchPinTime = 0.3f;  // s of fly held head-on against a facade before punching through
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float HeroLandMinSpeed = 30.f; // impact speed for a crater landing
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float SoftLandSpeed = 12.f;    // under this a floor contact is a gentle touchdown
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float HeroLandLock = 0.9f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float FlyoverEvery = 0.5f;     // s between flyover crowd stimuli
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Flight") float FlyoverMaxH = 140.f;     // m over the street: higher passes are not noticed

	bool IsFlightOn() const { return bFlightOn; }
	/** One frame of the hero body under flight (called by UWebTraversalComponent::UpdateTraversal while flight is on). */
	void StepFlight(UWebTraversalComponent& T, double Dt, FWebTravInput I);
	/** -WHFlightTune=Name=Value,... (float properties). */
	void ApplyTune(const FString& Tune);

	// ---- telemetry (read-only)
	FName FlightSub() const { return Sub; }
	double SpeedNow() const { return SpeedM; }
	int32 BoomCount = 0, BreachCount = 0, HeroLandCount = 0, DashCount = 0, BrakeCount = 0;
	bool IsBreaching() const { return bBreach; }

private:
	void StepAirSub(UWebTraversalComponent& T, double H, const FWebTravInput& I);
	bool MoveAndCollide(UWebTraversalComponent& T, double H, const FWebTravInput& I);
	bool StartBreach(UWebTraversalComponent& T, const FVector& HitPos, const FVector& HitN, const FVector& Dir);
	void StepBreach(UWebTraversalComponent& T, double H);
	void HeroLand(UWebTraversalComponent& T, double Floor, double ImpactSpeed, bool bSlam);
	void Takeoff(UWebTraversalComponent& T);
	FQuat FlightOrient(UWebTraversalComponent& T, double Dt, const FWebTravInput& I);
	void SetFlySub(UWebTraversalComponent& T, FName NewSub);
	void Event(UWebTraversalComponent& T, FName Type, float Sev, const FVector& Pos, const FVector& Dir, float K = 1.f);

	FName Sub;
	double SubT = 0.0, FlightT = 0.0, SpeedM = 0.0;
	double DashCd = 0.0, BreachCd = 0.0, FlyoverT = 0.0, BoomK = 0.0;
	FVector DashDir = FVector::ForwardVector;
	bool bBoomArmed = true, bSlam = false, bRightFist = true;
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
	bool bAimWasLive = false;
	bool bFlyHeldPrev = false;
};
