// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
// Hero v2 (owner-approved model, 2026-10-15): clip-driven C++ anim instance for /Game/Invincible/HeroV2/SK_InvincibleV2 (its own 52-bone
// skeleton). No Anim Blueprint: the game thread picks a state from the traversal / flight anim contract (FWebTravAnim + FWebTravAnimFlight)
// every frame, keeps up to four crossfading clip tracks (per-transition blend times, tunable), and the proxy samples + blends the clips
// (UAnimSequence::GetAnimationPose + FAnimationRuntime::BlendTwoPosesTogetherInPlace). Loops wrap, one-shots clamp and report completion.
// The fly / boost / brake / land clips carry the body pitch themselves (horizontal flight is IN the clip); AWebTravCharacter keeps the
// v2 mesh upright (yaw + small bank + small path pitch, see PitchFreedom()). Clip ledger: docs/invincible/character/ANIMATIONS.md;
// integration notes: docs/invincible/loop/heroV2_integration_NOTES.md. Log: "WH_HEROV2 state <name> clip <clip> t=<sec>".
#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "Traversal/WebTravTypes.h"
#include "WHHeroV2AnimInstance.generated.h"

class UAnimSequence;
class USkeletalMesh;

/** Hero v2 states (plain C++ enum, not reflected). Names in the log: see UWHHeroV2AnimInstance::StateName. */
enum class EWHHeroV2State : uint8 { None, GroundIdle, Takeoff, Hover, LaunchUp, Fly, Dash, BoostLaunch, BoostHold, Brake, LandHero, Breach, Num };

/** The 12 imported clips (/Game/Invincible/HeroV2/Anims/AS_<name>). */
enum class EWHHeroV2Clip : uint8 { Hover, Fly, LaunchUp, BoostLaunch, BoostHold, Brake, LandHero, Takeoff, GroundIdle, PunchCombo, Jab, FlyingFistKick, Num };

/** Reference-pose frame of the v2 mesh (mesh / component space, mesh units): from the bones + imported bounds (glTF unit scale unknown). */
struct WEBHOMAGE_API FWHHeroV2RefFrame
{
	FVector Up = FVector::UpVector;          // feet -> head
	FVector Fwd = FVector::ForwardVector;    // ankle -> foot (toes), perpendicular to Up
	FVector Pelvis = FVector::ZeroVector;    // pelvis joint (the pivot of every flight clip)
	double RefFootUp = 0.0;                  // lowest foot joint along Up (ground contact height of the foot joints)
	double BottomUp = 0.0;                   // lowest vertex along Up (imported bounds)
	double HeightUnits = 0.0;                // body height along Up (imported bounds)
};

/** One sampled clip layer for the proxy. */
struct FWHHeroV2Layer
{
	UAnimSequence* Seq = nullptr;
	float Time = 0.f;
	float Weight = 0.f;
	bool bLoop = true;
};

/** Everything the proxy needs for one evaluation (written on the game thread straight into the proxy, see NativeUpdateAnimation). */
struct FWHHeroV2Frame
{
	TArray<FWHHeroV2Layer> Layers;
	/** 0..1: the root bone is shifted along UpCS so the lowest foot joint sits at RefFootUp (grounded clips whose retargeted pelvis
	 *  stayed at the rest height: the takeoff crouch floats ~0.5 m, the landing kneel ~0.45 m without it). */
	float GroundW = 0.f;
	FVector UpCS = FVector::UpVector;
	float RefFootUp = 0.f;
	float MaxShift = 0.f;    // mesh units
	bool bRefOk = false;
};

struct FWHHeroV2AnimProxy : public FAnimInstanceProxy
{
	FWHHeroV2AnimProxy() = default;
	explicit FWHHeroV2AnimProxy(UAnimInstance* Inst) : FAnimInstanceProxy(Inst) {}
	virtual bool Evaluate(FPoseContext& Output) override;
	FWHHeroV2Frame Frame;
};

UCLASS(Transient, NotBlueprintable)
class WEBHOMAGE_API UWHHeroV2AnimInstance : public UAnimInstance
{
	GENERATED_BODY()

public:
	static const TCHAR* ClipRoot;   // /Game/Invincible/HeroV2/Anims
	static const TCHAR* ClipAsset(EWHHeroV2Clip C);
	static const TCHAR* StateName(EWHHeroV2State S);

	/** Reference frame of the v2 mesh; false if a required bone (head, pelvis, left_/right_foot, left_/right_ankle) is missing. */
	static bool ComputeRefFrame(const USkeletalMesh* Mesh, FWHHeroV2RefFrame& Out);

	// ---- telemetry (game thread, state of the last update)
	EWHHeroV2State CurrentState() const { return Tracks.Num() ? Tracks.Last().State : EWHHeroV2State::None; }
	const TCHAR* CurrentStateName() const { return StateName(CurrentState()); }
	const TCHAR* CurrentClipName() const;
	float CurrentClipTime() const { return Tracks.Num() ? Tracks.Last().T : 0.f; }
	/** 0..1: weight of path-aligned clips (fly / boost / dash / breach minus their LaunchUp blend, the boost launch, the land dive). The
	 *  character pitches the upright mesh by the flight-path angle (<= HeroV2MaxPitchDeg) only by this share. */
	float PitchFreedom() const { return PitchFreedomV; }
	float GroundLockW() const { return Frame.GroundW; }

	/** Capture pre-roll end: back to the freshly initialised state (no blend from the pre-roll pose). */
	void ResetForSequenceStart() { Tracks.Reset(); bLandImpact = false; bLandSpent = false; PrevSpeed = 0.f; UpWNow = 0.f; LogPending = EWHHeroV2State::None; }

	// ---- tunables (-WHHeroV2Tune=Name=Value,...; s unless noted)
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendDefault = 0.2f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendToTakeoff = 0.1f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendTakeoffOut = 0.25f;     // takeoff -> launchUp / hover / fly
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendHoverLaunchUp = 0.25f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendFlyHover = 0.3f;        // fly <-> hover / launchUp
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendToBoostLaunch = 0.12f;  // the coil snaps in with the charge
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendBoostLaunchOut = 0.25f; // boostLaunch -> boostHold / fly
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendToBrake = 0.15f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendBrakeToHover = 0.2f;    // AS_Brake ends on AS_Hover's first pose
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendToLandDive = 0.15f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendLandImpact = 0.08f;     // dive cut short by an early impact: jump to the impact frame
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendLandToIdle = 0.3f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendDash = 0.15f;
	// clip timing
	UPROPERTY(EditAnywhere, Category="HeroV2") float BoostBurstT = 0.42f;      // AS_BoostLaunch burst frame (= the flight's sonic boom)
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandImpactT = 0.37f;      // AS_LandHero impact frame (fist / feet contact; FK of hero_land.glb f11)
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandDiveHoldT = 0.2f;     // AS_LandHero frame held while the dive is still far from the floor
	UPROPERTY(EditAnywhere, Category="HeroV2") float TakeoffClipStart = 0.5f;  // AS_Takeoff starts here (crouch end, push-off ~0.55 s) -- the flight launches at once
	UPROPERTY(EditAnywhere, Category="HeroV2") float TakeoffUnlockT = 0.2f;    // ground lock fades out over this after the takeoff starts
	UPROPERTY(EditAnywhere, Category="HeroV2") float BrakeClipRate = 1.4f;     // AS_Brake playback rate (the flight stops in 0.3 s; the clip pull-up is ~1 s at 1x)
	UPROPERTY(EditAnywhere, Category="HeroV2") float DashRate = 1.6f;          // dash = AS_Fly at this rate
	// state rules
	UPROPERTY(EditAnywhere, Category="HeroV2") float LaunchUpPitchDeg = 60.f;  // fly / boost line pitched up past this blends to AS_LaunchUp
	UPROPERTY(EditAnywhere, Category="HeroV2") float LaunchUpBandDeg = 10.f;   // +- band of that blend
	UPROPERTY(EditAnywhere, Category="HeroV2") float UpBlendRate = 5.f;        // 1/s easing of the LaunchUp blend weight
	UPROPERTY(EditAnywhere, Category="HeroV2") float HoverClimbVz = 5.f;       // m/s: hover climbing faster (Space held) = AS_LaunchUp
	UPROPERTY(EditAnywhere, Category="HeroV2") float BrakeMinSpeed = 8.f;      // m/s: a brake from slower than this keeps the hover (AS_Brake starts horizontal)
	UPROPERTY(EditAnywhere, Category="HeroV2") float GroundLockTau = 0.06f;    // s time constant of the ground lock weight
	UPROPERTY(EditAnywhere, Category="HeroV2") float LogMinInterval = 0.05f;   // s (real) between WH_HEROV2 state lines

protected:
	virtual void NativeInitializeAnimation() override;
	virtual void NativeUpdateAnimation(float DeltaSeconds) override;
	virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override { return new FWHHeroV2AnimProxy(this); }
	virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy) override { delete InProxy; }

private:
	struct FTrack
	{
		EWHHeroV2State State = EWHHeroV2State::None;
		int32 Clip = -1;         // EWHHeroV2Clip index (resolved through the missing-clip fallbacks)
		int32 UpClip = -1;       // AS_LaunchUp blend for fly-type states (-1 none)
		float T = 0.f, UpT = 0.f, Rate = 1.f, W = 0.f, UpW = 0.f;
		bool bLoop = true, bDone = false, bDive = false;
	};

	UAnimSequence* ClipSeq(int32 C) const;
	float ClipLen(int32 C) const;
	int32 ResolveClip(EWHHeroV2Clip Want) const;
	static bool IsLoopClip(int32 C);
	EWHHeroV2State PickState(const FWebTravAnim& A, float Vz, float& OutUpTarget);
	float BlendTime(EWHHeroV2State From, EWHHeroV2State To) const;
	void StartTrack(EWHHeroV2State S, float StartT, float Blend);
	void AdvanceTracks(float Dt);
	float TimeToImpact(const FWebTravAnim& A) const;
	void LogState(const FWebTravAnim& A);
	void ApplyTune(const FString& Tune);

	UPROPERTY(Transient) TArray<TObjectPtr<UAnimSequence>> Clips;
	TArray<FTrack> Tracks;          // oldest first; Last() = the current state
	float BlendDur = 0.2f;          // fade-in of the newest track
	FWHHeroV2Frame Frame;
	FWHHeroV2RefFrame Ref;
	bool bRefOk = false;
	bool bLandImpact = false;       // AS_LandHero past the impact (grounded part)
	bool bLandSpent = false;        // this landing's AS_LandHero has been shown (the traversal sub can stay "landHero" afterwards)
	float PrevSpeed = 0.f;          // m/s last frame (brake start speed)
	float UpWNow = 0.f;             // eased LaunchUp blend of the current fly-type track
	float PitchFreedomV = 0.f;
	float StateT = 0.f;             // s in the current state
	// rate-limited state log
	EWHHeroV2State LastLogged = EWHHeroV2State::None, LogPending = EWHHeroV2State::None;
	double LastLogReal = -1.0;
	int32 LogSuppressed = 0;
};
