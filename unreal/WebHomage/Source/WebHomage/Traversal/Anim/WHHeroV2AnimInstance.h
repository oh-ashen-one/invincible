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
class AWHRescueDirector;

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
	/** r5 (critic r4 #5 / #6): the arm bones (collar .. fingers) of this layer come from ArmSeq at ArmTime, by ArmW (takeoff crouch: the
	 *  idle arms instead of the clip's arms-out crouch; rescue carry: AS_LaunchUp's arms overhead). */
	UAnimSequence* ArmSeq = nullptr;
	float ArmTime = 0.f;
	float ArmW = 0.f;
	bool bArmLoop = true;
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
	/** r5 (critic r4 #5, touchdown knee bend): every non-arm bone is blended toward DipSeq at DipTime by DipW (AS_Takeoff's crouch). */
	UAnimSequence* DipSeq = nullptr;
	float DipTime = 0.f;
	float DipW = 0.f;
	/** r5 (critic r4 #1, T-pose in the hover <-> fly crossfades): the per-bone crossfade of an arms-down and an arms-overhead pose turns the
	 *  arm out sideways through the shoulder line. Where the layers' upper-arm directions (in the collar's parent = chest frame) cancel,
	 *  the blended upper arm is swung through the chest's forward instead (ArmFix). Data per side (0 left, 1 right). */
	bool bArmFix = false;
	FVector ArmAxis[2] = { FVector::ForwardVector, FVector::ForwardVector };      // shoulder-local direction to the elbow (ref pose)
	FVector ChestFwd[2] = { FVector::ForwardVector, FVector::ForwardVector };     // body forward in the collar's parent frame (ref pose)
	float ArmFixStrength = 1.f, ArmFixLo = 0.2f, ArmFixHi = 0.45f;
};

struct FWHHeroV2AnimProxy : public FAnimInstanceProxy
{
	FWHHeroV2AnimProxy() = default;
	explicit FWHHeroV2AnimProxy(UAnimInstance* Inst) : FAnimInstanceProxy(Inst) {}
	virtual bool Evaluate(FPoseContext& Output) override;
	FWHHeroV2Frame Frame;
	/** true for the arm bones (left_/right_ collar, shoulder, elbow, wrist, fingers) */
	static bool IsArmBone(const FName& Bone);
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
	/** 0..1: weight of path-aligned clips (fly / boost / dash / breach minus their LaunchUp blend, the boost launch, the land dive until
	 *  its feet-first flip). The character pitches the upright mesh by the flight-path angle (<= HeroV2MaxPitchDeg) only by this share. */
	float PitchFreedom() const { return PitchFreedomV; }
	float GroundLockW() const { return Frame.GroundW; }

	/** r5 (critic r4 #5): takeoff anticipation. 1 while the feet stay planted on the take-off floor (the crouch plays there while the
	 *  flight body already rises), then 0 over TakeoffCatchT (the mesh catches up with the body: the leap). T = s since the takeoff. */
	float TakeoffPlantK(float T) const;

	/** Capture pre-roll end: back to the freshly initialised state (no blend from the pre-roll pose). */
	void ResetForSequenceStart() { Tracks.Reset(); bLandImpact = false; bLandSpent = false; PrevSpeed = 0.f; PrevVz = 0.f; UpWNow = 0.f; DipT = 99.f; LogPending = EWHHeroV2State::None; }

	// ---- tunables (-WHHeroV2Tune=Name=Value,...; s unless noted)
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendDefault = 0.2f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendToTakeoff = 0.06f;      // r5: the crouch is reached within ~4 frames (critic r4 #5)
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendTakeoffOut = 0.25f;     // takeoff -> launchUp / hover / fly
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendHoverLaunchUp = 0.25f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendFlyHover = 0.3f;        // fly <-> hover / launchUp
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendToBoostLaunch = 0.12f;  // the coil snaps in with the charge
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendBoostLaunchOut = 0.25f; // boostLaunch -> boostHold / fly
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendToBrake = 0.3f;         // r5: fly line -> the upright brake entry (BrakeEnterT)
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendBrakeToHover = 0.2f;    // AS_Brake ends on AS_Hover's first pose
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendToLandDive = 0.15f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendLandImpact = 0.08f;     // dive cut short by an early impact: jump to the impact frame
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendLandToIdle = 0.3f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendDash = 0.15f;           // dash <-> fly-type
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendDashUpright = 0.35f;    // r5 (critic r4 fl09: 90 deg in 0.15 s): dash <-> hover / launchUp
	// clip timing
	UPROPERTY(EditAnywhere, Category="HeroV2") float BoostBurstT = 0.42f;      // AS_BoostLaunch burst frame (= the flight's sonic boom)
	// r5 (critic r4 #3): AS_LandHero is read at init (pelvis height over the lowest foot): LandFeetT = feet under the body (half the kneel
	// height), LandImpactT = the kneel contact (92 % of it). These are the fallbacks (offline FK of hero_land.glb: 0.43 / 0.49 s).
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandImpactT = 0.49f;      // AS_LandHero contact frame (on the landing event)
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandFeetT = 0.43f;        // AS_LandHero frame where the body has turned feet-first
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandDiveHoldT = 0.2f;     // AS_LandHero frame held while the dive is still far from the floor
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandFlipLeadT = 0.36f;    // s before the impact the flip (hold -> LandFeetT) starts
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandFeetLeadT = 0.16f;    // s before the impact the body is feet-first (critic test: >= 8 frames)
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandFlipMaxRate = 3.f;    // clip-rate cap of the flip (a slam started close to the floor)
	UPROPERTY(EditAnywhere, Category="HeroV2") float TakeoffClipStart = 0.35f; // r5: AS_Takeoff starts in its crouch (static 0 - 0.45 s, push-off 0.5 - 0.75 s)
	UPROPERTY(EditAnywhere, Category="HeroV2") float TakeoffRate = 1.5f;       // r5: crouch end at the plant end, push-off during the catch-up
	UPROPERTY(EditAnywhere, Category="HeroV2") float TakeoffPlantT = 0.0f;     // r5: no floor plant -- any plant + catch-up dropped the mesh out of the bottom of the rising camera frame (sim: 14 frames at 0.12 s, 10 at 0.05 s); the crouch plays while he rises
	UPROPERTY(EditAnywhere, Category="HeroV2") float TakeoffCatchT = 0.15f;    // r5: then the mesh rejoins the rising flight body
	UPROPERTY(EditAnywhere, Category="HeroV2") float TakeoffArmsT0 = 0.5f;     // r5: AS_Takeoff's arms-out crouch shows the idle arms until this clip t ...
	UPROPERTY(EditAnywhere, Category="HeroV2") float TakeoffArmsT1 = 0.62f;    // ... and its own arms (swinging up) from this clip t
	UPROPERTY(EditAnywhere, Category="HeroV2") float BrakeEnterT = 1.5f;       // r5 (critic r4 #2): AS_Brake entered here (its 0.15 - 0.95 s part rolls him onto his side)
	UPROPERTY(EditAnywhere, Category="HeroV2") float BrakeClipRate = 1.f;      // AS_Brake playback rate from BrakeEnterT
	UPROPERTY(EditAnywhere, Category="HeroV2") float DashRate = 1.f;           // r5: dash = AS_BoostHold (parallel fists) at this rate
	// r5 (critic r4 #5, touchdown): knee-bend dip after a soft landing = AS_Takeoff's crouch on the non-arm bones
	UPROPERTY(EditAnywhere, Category="HeroV2") float DipPoseT = 0.3f;          // AS_Takeoff crouch frame used
	UPROPERTY(EditAnywhere, Category="HeroV2") float DipPeak = 0.3f;           // dip weight at a 0 m/s touchdown ...
	UPROPERTY(EditAnywhere, Category="HeroV2") float DipPeakPerMps = 0.03f;    // ... + this per m/s of descent ...
	UPROPERTY(EditAnywhere, Category="HeroV2") float DipMax = 0.6f;            // ... at most
	UPROPERTY(EditAnywhere, Category="HeroV2") float DipInT = 0.08f;           // s to the deepest bend
	UPROPERTY(EditAnywhere, Category="HeroV2") float DipOutT = 0.35f;          // s back to the idle
	// r5 (critic r4 #1): arm swing through the chest's forward in cancelling crossfades (see FWHHeroV2Frame::bArmFix)
	UPROPERTY(EditAnywhere, Category="HeroV2") float ArmFixStrength = 1.f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float ArmFixLo = 0.2f;          // cancellation (1 - |mean upper-arm direction|) where the fix starts ...
	UPROPERTY(EditAnywhere, Category="HeroV2") float ArmFixHi = 0.45f;         // ... and is full
	// r5 (critic r4 #6): rescue carry
	UPROPERTY(EditAnywhere, Category="HeroV2") float CarryInT = 0.25f;         // s: AS_LaunchUp arms overhead blend in at the catch ...
	UPROPERTY(EditAnywhere, Category="HeroV2") float CarryOutT = 0.8f;         // ... and out after the set-down (r6, critic r5 #1: lowered with the eased set-down, was 0.3)
	UPROPERTY(EditAnywhere, Category="HeroV2") float CarrySwingT = 0.45f;      // s: the caught load swings round the front onto the fists
	UPROPERTY(EditAnywhere, Category="HeroV2") float CarryFistCm = 6.f;        // load bottom this far past the middle-finger knuckles (fist top)
	UPROPERTY(EditAnywhere, Category="HeroV2") float CarryClearCm = 25.f;      // swing clearance between the load and the body capsule
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
	virtual void NativePostEvaluateAnimation() override;   // r5: rescue carry anchor from this frame's evaluated hand bones
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
	void AnalyzeLandClip();                       // r5: LandFeetT / LandImpactT from AS_LandHero's own bones
	void InitArmFix(const USkeletalMesh* Mesh);   // r5: FWHHeroV2Frame arm-fix constants from the reference pose
	void UpdateCarry(const FWebTravAnim& A, float Dt);
	float DiveFlipK(float T) const;               // 0 hold .. 1 feet-first along AS_LandHero

	UPROPERTY(Transient) TArray<TObjectPtr<UAnimSequence>> Clips;
	TArray<FTrack> Tracks;          // oldest first; Last() = the current state
	float BlendDur = 0.2f;          // fade-in of the newest track
	FWHHeroV2Frame Frame;
	FWHHeroV2RefFrame Ref;
	bool bRefOk = false;
	bool bLandImpact = false;       // AS_LandHero past the impact (grounded part)
	bool bLandSpent = false;        // this landing's AS_LandHero has been shown (the traversal sub can stay "landHero" afterwards)
	float PrevSpeed = 0.f;          // m/s last frame (brake start speed)
	float PrevVz = 0.f;             // m/s last frame (touchdown dip depth, dive acceleration)
	float FallAccel = 0.f;          // m/s^2 eased downward acceleration of the dive (time to impact)
	float UpWNow = 0.f;             // eased LaunchUp blend of the current fly-type track
	float PitchFreedomV = 0.f;
	float StateT = 0.f;             // s in the current state
	// r5 touchdown dip
	float DipT = 99.f, DipPeakNow = 0.f;
	// r5 rescue carry (critic r4 #6)
	TWeakObjectPtr<AWHRescueDirector> RescueDir;
	float RescueFindT = 0.f;
	bool bCarry = false;            // the director reports a carried load this frame
	bool bCarryCatch = false;       // first anchor of this carry still to be taken (catch transform)
	float CarryW = 0.f, CarryT = 0.f, CarryArmT = 0.f;
	FTransform CarryCatchCS = FTransform::Identity;   // the load relative to the mesh at the catch (mesh units, no scale)
	FVector CarryHalfCm = FVector::ZeroVector;        // the carried load's half extents (cm)
	FName ChestBone = NAME_None;                      // the collars' parent (spine3) and the body forward in its frame (ref pose)
	FVector ChestFwdLocal = FVector::ForwardVector;
	// rate-limited state log
	EWHHeroV2State LastLogged = EWHHeroV2State::None, LogPending = EWHHeroV2State::None;
	double LastLogReal = -1.0;
	int32 LogSuppressed = 0;
};
