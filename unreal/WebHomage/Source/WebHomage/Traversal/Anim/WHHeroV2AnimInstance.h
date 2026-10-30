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
class UWHFlightComponent;

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
	/** r7 (critic r6 #3): this layer is AS_Hover -- its spine / collar rotations drive the extra breathing (FWHHeroV2Frame::BreathK) */
	bool bBreath = false;
	/** r7 (critic r6 #2): the arm override swings the upper arms in front of the chest where they cancel (the carry's arms-up blend) */
	bool bArmSwing = false;
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
	/** r7 (critic r6 #3, fl08 "torso moves 2 px over 2.6 s"): procedural hover layer. BobShift = root shift along UpCS (mesh units, signed);
	 *  the AS_Hover layer's own breathing (its local rotation of each BreathBone relative to the clip's mean BreathAvg) is extrapolated by
	 *  BreathK on the spine bones and BreathArmK on the collars (the carry's overhead arms: 0). */
	float BobShift = 0.f;
	float BreathK = 0.f, BreathArmK = 0.f;
	static constexpr int32 NumBreath = 4;
	FName BreathBone[NumBreath];          // spine2, spine3, left_collar, right_collar (NAME_None: not found)
	FQuat BreathAvg[NumBreath] = { FQuat::Identity, FQuat::Identity, FQuat::Identity, FQuat::Identity };
	/** r7 (critic r6 #2, fl17 "his side merges into the taxi door"): component-space root nudge (mesh units) that steps the floating hero
	 *  clear of a street vehicle (vehicles have no collision; see UWHHeroV2AnimInstance::UpdateStandClear) */
	FVector NudgeCS = FVector::ZeroVector;
	/** r9 (critic r8 fl12 "on all fours / splayed"): kneel contact on top of AS_LandHero's held three-point pose, after the ground lock.
	 *  The kneeling leg's thigh turns down under its hip until the knee joint sits KneeUp over the sole line (SoleUp), its shin turns so
	 *  its foot joint rests at the planted foot's height (RefFootUp); the fist arm reaches (two bones) until its knuckle sits FistUp over the
	 *  sole line. Mesh units along UpCS, weight KneelW (0 = off). Bones: hip, knee, ankle, foot / shoulder, elbow, wrist, middle1. */
	bool bKneelOk = false;
	float KneelW = 0.f, SoleUp = 0.f, KneeUp = 0.f, FistUp = 0.f;
	FName KneelLeg[4];
	FName FistArm[4];
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
	static const TCHAR* ClipRoot;   // /Game/Invincible/HeroV2/Anims (the shipped clip set; the default)
	/** In-game A/B (2026-10-30): -WHHeroV2Clips=<package path> (e.g. /Game/Invincible/HeroV2R/Anims) loads each AS_<clip> from that folder
	 *  first; a clip missing there falls back to ClipRoot. Empty (no flag, empty value, or the same folder as ClipRoot) = no override. */
	static FString ClipRootOverride();
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
	/** r9 (critic r8 fl12): AS_LandHero past its contact (the landing hold / kneel) -- the character keeps the mesh upright, yaw only */
	bool InLandContact() const { return CurrentState() == EWHHeroV2State::LandHero && bLandImpact && Tracks.Num() && !Tracks.Last().bDive; }

	/** r5 (critic r4 #5): takeoff anticipation. 1 while the feet stay planted on the take-off floor (the crouch plays there while the
	 *  flight body already rises), then 0 over TakeoffCatchT (the mesh catches up with the body: the leap). T = s since the takeoff. */
	float TakeoffPlantK(float T) const;

	/** Capture pre-roll end: back to the freshly initialised state (no blend from the pre-roll pose). */
	void ResetForSequenceStart() { Tracks.Reset(); bLandImpact = false; bLandSpent = false; PrevSpeed = 0.f; PrevVz = 0.f; UpWNow = 0.f; DipT = 99.f; LogPending = EWHHeroV2State::None;
		BurstS = -1.f; BobW = 0.f; StandWant = FVector::ZeroVector; StandNudge = FVector::ZeroVector; bStandHoldSet = false; bContactLogged = false; }

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
	// owner request 2026-10-16 ("always floating"): the airborne hero-landing hold (Air + sub landHero) rises into the hover float
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendLandToHover = 0.5f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendDash = 0.15f;           // dash <-> fly-type
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendDashUpright = 0.35f;    // r5 (critic r4 fl09: 90 deg in 0.15 s): dash <-> hover / launchUp
	// clip timing
	UPROPERTY(EditAnywhere, Category="HeroV2") float BoostBurstT = 0.42f;      // AS_BoostLaunch burst frame (= the flight's sonic boom)
	// r7 (critic r6 #4, fl04 "charge pose 1.450 -> full flight 1.467 in one frame"): AS_BoostLaunch goes from the coil to the stretched line
	// between two 30 fps keys (0.400 -> 0.433, head-feet 110 -> 174 cm, upper arms ~105 deg). Read at init (AnalyzeBoostClip): the charge
	// holds the clip at BoostCoilEndT (last coil frame); on the boom the BoostCoilEndT -> BoostBurstEndT span is spread over BoostBurstBlendS
	// (uniform steps of joint travel). Fallbacks = offline FK of hero_boost_game.glb.
	UPROPERTY(EditAnywhere, Category="HeroV2") float BoostCoilEndT = 0.367f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float BoostBurstEndT = 0.433f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float BoostBurstBlendS = 0.1f;   // s: 6 frames at 60 fps (5 in between)
	// r5 (critic r4 #3): AS_LandHero is read at init (pelvis height over the lowest foot): LandFeetT = feet under the body (half the kneel
	// height), LandImpactT = the kneel contact (92 % of it). These are the fallbacks (offline FK of hero_land.glb: 0.43 / 0.49 s).
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandImpactT = 0.49f;      // AS_LandHero contact frame (on the landing event)
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandFeetT = 0.43f;        // AS_LandHero frame where the body has turned feet-first
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandDiveHoldT = 0.2f;     // AS_LandHero frame held while the dive is still far from the floor
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandFlipLeadT = 0.36f;    // s before the impact the flip (hold -> LandFeetT) starts
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandFeetLeadT = 0.16f;    // s before the impact the body is feet-first (critic test: >= 8 frames)
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandFlipMaxRate = 3.f;    // clip-rate cap of the flip (a slam started close to the floor)
	// r7 (critic r6 #6, fl12 "spread-eagle splat"): a fly / boost / dash line descending at >= the flight's HeroLandMinSpeed (x FastLandVzK)
	// with TimeToImpact <= FastLandLeadT enters AS_LandHero's dive at the frame whose head line matches the path angle (AS_LandHero turns
	// head-down -> head-forward -> feet-first; table read at init), held there with no extra mesh pitch, then the usual flip and contact
	UPROPERTY(EditAnywhere, Category="HeroV2") float FastLandLeadT = 0.55f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float FastLandVzK = 1.05f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float BlendToLineDive = 0.2f;
	// r7 (critic r6 #6): the airborne landing hold keeps the kneel (knee + fist down, AS_LandHero 0.53 - 2.13 s) -- the clip is held at
	// LandKneelEndT while the flight's sub stays landHero (measured at init: the last frame before the stand-up)
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandKneelEndT = 2.1f;
	// r9 (critic r8 fl12 frames 3-6 "on all fours / splayed"): the hold freezes AS_LandHero on its settled contact frame LandHoldPoseT (the
	// first frame after LandImpactT where every limb joint moves < LandSettleK body heights / s; measured at init, offline FK ~0.62 s) instead
	// of playing on through the kneel (LandHoldFreeze 0 = r7: the kneel plays to LandKneelEndT). The kneel contact layer (FWHHeroV2Frame
	// KneelW) then puts the kneeling knee LandKneeCm and the fist's knuckle LandFistCm over the sole line (offline FK of the clip: knee
	// 24-27 cm, knuckle 9-12 cm, the kneeling leg splayed ~45 cm sideways). LandKneelContact 0 = off.
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandHoldPoseT = 0.62f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandSettleK = 0.5f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandHoldFreeze = 1.f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandKneelContact = 1.f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandKneeCm = 6.5f;
	UPROPERTY(EditAnywhere, Category="HeroV2") float LandFistCm = 2.5f;
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
	UPROPERTY(EditAnywhere, Category="HeroV2") float CarrySwingT = 0.6f;       // s: the caught load swings onto the fists (r7: 0.45 -> 0.6, rise first, then in)
	UPROPERTY(EditAnywhere, Category="HeroV2") float CarryFistCm = 6.f;        // load bottom this far past the middle-finger knuckles (fist top)
	UPROPERTY(EditAnywhere, Category="HeroV2") float CarryClearCm = 25.f;      // swing clearance between the load and the body capsule
	UPROPERTY(EditAnywhere, Category="HeroV2") float CarryMarginCm = 20.f;     // r7: soft band over that clearance (the sideways keep-out ramps in over it)
	// r7 (critic r6 #3): procedural hover layer (on top of AS_Hover, not in the clip). Bob amplitude at the chase hover distance: the r6
	// hover renders ~225 px/m (fl08 bbox 0.385 x 1080 px, 1.85 m), so 2.5 cm = 5 cm peak-to-peak = ~11 px; plus the clip's own head
	// motion (1.45 cm p-p) x HoverBreathGain. Phase-locked to the clip's own head rise (AnalyzeHoverClip). Fades out with speed / transitions.
	UPROPERTY(EditAnywhere, Category="HeroV2") float HoverBobCm = 2.5f;        // amplitude (cm) of the vertical root bob
	UPROPERTY(EditAnywhere, Category="HeroV2") float HoverBobCycles = 2.f;     // bob periods per AS_Hover loop (4 s clip: 0.5 Hz)
	UPROPERTY(EditAnywhere, Category="HeroV2") float HoverBobSpeedLo = 1.f;    // m/s: full bob below this ...
	UPROPERTY(EditAnywhere, Category="HeroV2") float HoverBobSpeedHi = 5.f;    // ... none above this
	UPROPERTY(EditAnywhere, Category="HeroV2") float HoverBobTau = 0.3f;       // s: easing of the layer weight
	UPROPERTY(EditAnywhere, Category="HeroV2") float HoverBreathGain = 1.5f;   // x the clip's spine2 / spine3 / collar breathing
	// r7 (critic r6 #2, fl17 end): floating (nearly) still within 1.5 m of the floor, the mesh steps clear of street vehicles (no collision)
	UPROPERTY(EditAnywhere, Category="HeroV2") float StandClearCm = 50.f;      // body surface -> vehicle box (0 = off)
	UPROPERTY(EditAnywhere, Category="HeroV2") float StandRadiusCm = 35.f;     // body radius
	UPROPERTY(EditAnywhere, Category="HeroV2") float StandClearMaxCm = 150.f;  // largest sideways nudge
	UPROPERTY(EditAnywhere, Category="HeroV2") float StandClearMaxSpeed = 2.5f;   // m/s
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
		bool bLine = false;      // r7: AS_LandHero dive entered from a fast fly line (no mesh pitch; the clip frame matches the path)
		float DiveT0 = 0.f;      // r7: clip time the dive started at (the flip / ground lock ramp from here)
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
	float DiveFlipK(float T, float T0 = 0.f) const;   // 0 hold (or the dive's entry frame T0) .. 1 feet-first along AS_LandHero
	void AnalyzeBoostClip();                      // r7: BoostCoilEndT / BoostBurstEndT + the burst's extension curve
	void AnalyzeHoverClip();                      // r7: bob phase + mean breathing rotations of AS_Hover
	float BurstClipT(float U) const;              // r7: AS_BoostLaunch time at burst progress U (0 coil end .. 1 stretched)
	float LineDiveStartT(float GammaDeg) const;   // r7: AS_LandHero frame whose head line points GammaDeg below the horizon
	bool FastLinePredict(const FWebTravAnim& A, float Vz, bool bStay, float& OutGammaDeg) const;   // r7: fly line about to hero-land
	void UpdateStandClear(const FWebTravAnim& A, const UWHFlightComponent* FlC, float Dt);   // r7: step clear of street vehicles

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
	// owner request 2026-10-16 (always floating): flight float mode on (never AS_GroundIdle), the flight's surface under the hero (m),
	// the last seen float-touch counter (knee dip on a touch)
	bool bFloat = false;
	double FlightSurfZ = -1000.0;
	int32 LastTouchCount = 0;
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
	// r7 boost burst (critic r6 #4): -1 = not started, >= 0 s into the spread burst, > 100 done
	float BurstS = -1.f;
	TArray<float> BurstCurveT, BurstCurveF;           // AS_BoostLaunch time -> joint-travel fraction over the burst span (init)
	// r7 fast line landing (critic r6 #6)
	TArray<float> LineDiveT, LineDiveElev;            // AS_LandHero time -> head-line elevation (deg) over the dive / flip (init)
	bool bLineWant = false;                           // this frame's pick is a predicted fly-line hero landing
	float LineGammaDeg = 0.f;
	float HeroLandMinV = 30.f;                        // m/s: the flight's HeroLandMinSpeed (descent at contact)
	// r7 hover layer (critic r6 #3)
	float HoverBobPhase = 0.f;                        // rad: AS_Hover's own head-rise phase at HoverBobCycles per loop
	float BobW = 0.f;
	// r7 stand clear (critic r6 #2)
	FVector StandWant = FVector::ZeroVector, StandNudge = FVector::ZeroVector;   // world cm
	float StandQueryT = 0.f;
	bool bStandLogged = false;
	bool bStandHoldSet = false;   // r9: the landing hold took its stand-clear step at the contact (no slide while kneeling)
	bool bContactLogged = false;  // r9: this landing's contact line was logged
	// rate-limited state log
	EWHHeroV2State LastLogged = EWHHeroV2State::None, LogPending = EWHHeroV2State::None;
	double LastLogReal = -1.0;
	int32 LogSuppressed = 0;
};
