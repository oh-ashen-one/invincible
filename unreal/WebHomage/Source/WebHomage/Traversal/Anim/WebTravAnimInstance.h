// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// Piece P3 round 04: C++ animation for the traversal hero (port of the essentials of src/player/anim/animator.js).
// No AnimBP graph: a native UAnimInstance picks a node from the C1 traversal anim struct (FWebTravAnim), crossfades
// nodes with the browser's per-transition blend times (TRANS), and its proxy samples + blends the authored clips of the
// hero GLB (/Game/Traversal/HeroDev/<clip>, names unchanged from the browser) and applies procedural layers:
// web-hand arm aim at the anchor, spine bank. Air phases between swings run a per-cycle flavor timeline
// (spread / tuck / rise / reach for the next web) that never repeats the previous cycle's flavor.
#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "Traversal/WebTravTypes.h"
#include "WebTravAnimInstance.generated.h"

class UAnimSequence;

struct FWebTravAnimLayer
{
	UAnimSequence* Seq = nullptr;
	float Time = 0.f;
	float Weight = 0.f;
	bool bLoop = true;
};

/** Everything the proxy needs for one evaluation (copied on the game thread). */
struct FWebTravAnimFrame
{
	TArray<FWebTravAnimLayer> Layers;
	bool bArmAim = false;
	bool bArmRight = true;
	float ArmAimWeight = 0.f;
	float ArmAimAge = 0.f;   // s since the firing arm started aiming (anticipation: shoulder raise)
	FVector ArmTargetCS = FVector::ZeroVector;   // component space (cm)
	FVector ArmStartCS = FVector::ZeroVector;    // launch direction held in world space, rebased for this evaluation
	float SpineBank = 0.f;                        // rad
	float BodyAlignW = 0.f;                       // round 07: hips->head turned onto the web (hips->anchor), 0..1
	// round 11 (flip programs, overlapping action): the legs follow their own shape layers (sampled FlipLag behind the upper
	// body), blended over the main pose's leg bones by LegW
	TArray<FWebTravAnimLayer> LegLayers;
	float LegW = 0.f;
	// round 19 (owner playtest: wall-run "super cooked"): procedural wall-run stride. Two-bone IK puts the feet and hands ON the facade
	// (component space, cm): contralateral gait, stance feet sweep down the wall (push), hands plant above the shoulder and pull down,
	// knees drive up-and-out between contacts, shoulders counter-twist with the arms. WallW = blend weight (0 = clip pose only).
	float WallW = 0.f;
	FVector WallN = FVector::ForwardVector, WallP = FVector::ZeroVector, WallU = FVector::UpVector;
	float GaitPh = 0.f;
	// round 22: upright side run (runner side-on to the facade): SideUpW = blend (0 = the r21 chest-to-wall stride), WallZ = the wall's up
	// axis (component space); WallU is then the run direction
	float SideUpW = 0.f;
	FVector WallZ = FVector::UpVector;
	// round 19 (owner: swing / in-air poses at speed): procedural leg shaping while swinging (legs trail the velocity at the arc bottom,
	// knees tuck on the rise) and the free arm opening against the arc; weights 0..1
	float SwingLegW = 0.f, SwingTuck = 0.f, SwingFreeArmW = 0.f;
	float SwingT = 9.f;   // round 10: seconds since the current web attached (9 = not swinging); the catch-window align slew budget keys off it
	// round 01 (Gap 4): SWING LIFE -- ported from the browser animator (spiderbench animator.js swingLife): per web one body style (split / tuck / long / stride, never the same twice
	// in a row); thighs, knees and the back run on springs (2.1 / 2.8 / 2.0 Hz, zeta .5-.6) toward phase-dependent targets, so the legs and torso lag the arc, swing through and overshoot.
	// SwTh = thigh pitch (rad, - = knee forward), SwKn = absolute knee flexion (rad), SwArch = back arch (rad); index 0 = left, 1 = right
	float SwLifeK = 0.f, SwArch = 0.f;
	float SwPhase = 0.f;   // round 04: swing phase (- = drop, + = upswing) for the free-arm swing
	int32 SwStyle = 0;
	float SwTh[2] = { 0.f, 0.f }, SwKn[2] = { 0.f, 0.f };
	FVector VelCS = FVector::ZeroVector;  // component-space velocity direction (unit)
	// round 19 (r18 critic): tight tuck (wrists to the shins, knees together) while a flip program is in a Tuck shape
	float TuckW = 0.f;
	// round 20 (critic r19: "on a zip the hero hangs limp"): both arms reach for the zip target through the flight (component space, cm)
	float ZipReachW = 0.f;
	FVector ZipTargetCS = FVector::ZeroVector;
	// round 20 (critic r19: "the air pose does not change with speed", "fallCalm stands upright at 43-51 m/s"): procedural sky-dive arch
	// (arms up and out, knees bent, legs apart) from 20 m/s blending into a streamlined track (arms swept back along the sides, legs
	// straight and together, toes pointed) by 30-44 m/s. AirFastW = layer weight, AirTrackK = arch (0) .. track (1)
	float AirFastW = 0.f, AirTrackK = 0.f;
	// round 20: swing pose by speed (0 slow .. 1 >= 55 m/s): legs trail further and straighter, the free arm sweeps back
	float SwingSpeedK = 0.f;
	// round 08 (critic r07 s4: the float reads as one symmetric spread > 1 s -- the six air clips share an arms-out silhouette, so the
	// node rotation alone does not move the outline): a slow alternating asymmetry over the air pose (one arm sweeps forward and down,
	// the other back, legs scissor the other way; a full left/right cycle every ~1.1 s). AirDriftW = weight, AirDriftPh = cycles
	float AirDriftW = 0.f, AirDriftPh = 0.f;
};

struct FWebTravAnimProxy : public FAnimInstanceProxy
{
	FWebTravAnimProxy() = default;
	explicit FWebTravAnimProxy(UAnimInstance* Inst) : FAnimInstanceProxy(Inst) {}
	virtual void PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds) override;
	virtual bool Evaluate(FPoseContext& Output) override;
	FWebTravAnimFrame Frame;
	// round 06 (F8): the web-align hips rotation is slew-limited (its angle step per evaluated frame, not only its weight)
	FQuat AlignPrevQ = FQuat::Identity; float AlignPrevDt = 1.f / 60.f;
};

UCLASS(Transient, NotBlueprintable)
class WEBHOMAGE_API UWebTravAnimInstance : public UAnimInstance
{
	GENERATED_BODY()

public:
	/** Drive data from the character (game thread, before the mesh ticks). */
	void SetDrive(const FWebTravAnim& InAnim, bool bInWebActive, const FVector& InWebAnchorWorldCm, bool bInWebRight, bool bInSwingHeld,
		float InWebShootDuration, float InWebDrawAge);

	/** Name of the node / dominant clip of the last update (telemetry). */
	FName CurrentNode() const { return CurNode; }
	FName DominantClip() const { return Dominant; }
	float TotalClipWeight() const { return TotalWeight; }
	/** Visual strand flight starts after the firing arm finishes its smooth reach. */
	float WebVisualLaunchAge() const { return VisualLaunchAge; }
	int32 AirFlavor() const { return FlavorIdx; }
	bool InAirCycle() const { return bInAirCycle; }
	float AirCycleTime() const { return AirCycleT; }
	int32 AirCycleCount() const { return CycleCount; }
	/** Round 11: the Blender flip shape clips (flipTuck ...) are loaded -> flip programs drive the air tricks and the top-out. */
	bool HasFlipClips() const { return bFlipClips; }
	/** Round 06: capture pre-roll end — back to the freshly initialised state (no blend from the pre-roll pose). */
	void ResetForSequenceStart()
	{
		CurNode = NAME_None; Dominant = NAME_None; NodeT = 0.f; FadeT = 1.f; FadeDur = 0.2f; PrevLayers.Reset(); Frame.Layers.Reset();
		Frame.ArmAimWeight = 0.f; LocoPhase = 0.f; WallRunPhase = 0.f; bGroundWInit = false; bInAirCycle = false; AirCycleT = 0.f; FlavorIdx = -1; CycleCount = 0;
		Frame.ArmAimAge = 0.f; bWebAimPrev = false; PrevAimShotK = -1.f; VisualLaunchAge = 0.f;
		bReachRight = true; LastMode = EWebTravMode::Ground; Frame.LegLayers.Reset(); Frame.LegW = 0.f; PendingLegs.Reset();
	}

	/** Content folder with the hero clips and the asset-name prefix (set from AWebTravCharacter::HeroClipRoot / HeroClipPrefix). */
	static FString ClipRoot;
	static FString ClipPrefix;

	FWebTravAnimFrame Frame;

protected:
	virtual void NativeInitializeAnimation() override;
	virtual void NativeUpdateAnimation(float DeltaSeconds) override;
	virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override { return new FWebTravAnimProxy(this); }
	virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy) override { delete InProxy; }

private:
	UAnimSequence* Clip(FName Name);
	FName PickNode(float Dt);
	void BuildNode(FName Node, float NodeT, TArray<FWebTravAnimLayer>& Out);
	static FName Category(FName Node);
	static float BlendTime(FName FromCat, FName ToCat);

	UPROPERTY(Transient) TMap<FName, TObjectPtr<UAnimSequence>> Clips;
	FWebTravAnim A;
	bool bWebActive = false, bWebRight = true, bSwingHeld = false;
	bool bWebAimPrev = false;
	float PrevAimShotK = -1.f;
	float WebShootDuration = 0.1f, WebDrawAge = 0.f, ArmAimDuration = 0.1f;
	float VisualLaunchAge = 0.f;
	FVector ArmStartWorld = FVector::ZeroVector;
	FVector WebAnchorWorld = FVector::ZeroVector;

	FName CurNode, Dominant;
	float NodeT = 0.f, FadeT = 1.f, FadeDur = 0.2f, TotalWeight = 0.f;
	TArray<FWebTravAnimLayer> PrevLayers;
	float LocoPhase = 0.f, WallRunPhase = 0.f;
	// Smoothed ground locomotion weights: spider rest crouch / walk / jog / run / sprint.
	// The existing blend prevents a one-frame rest -> run weight pop.
	float GroundW[5] = { 1.f, 0.f, 0.f, 0.f, 0.f };
	bool bGroundWInit = false;
	float WallGaitPh = 0.f;
	float PendingTuckW = 0.f;
public:
	/** Round 19: procedural wall-run stride on (default) -- -WHWallGait=0 restores the round-06 sprint-clip wall run (A/B). */
	static bool bWallGait;
	/** Round 20: speed-dependent air pose + swing shaping (-WHAirSpeedPose=0 = r19); ChestSign flips the body-front axis if a rig needs it. */
	static bool bAirSpeedPose;
	static double ChestSign;
private:
	// air cycle
	// swing life state (game thread)
	struct FSwSpring { double X = 0.0, V = 0.0; void Step(double Target, double FreqHz, double Zeta, double Dt) { const double W = 2.0 * PI * FreqHz; const int32 N = FMath::Max(1, FMath::CeilToInt(Dt / (1.0 / 120.0))); const double H = Dt / N; for (int32 I = 0; I < N; ++I) { const double Acc = W * W * (Target - X) - 2.0 * Zeta * W * V; V += Acc * H; X += V * H; } } };
	FSwSpring SwThS[2], SwKnS[2], SwArchS;
	int32 SwLastStyle = -1, SwCount = 0; double SwT0 = 0.0, SwTime = 0.0, SwStp = 0.0; bool bSwPrev = false;
	// round 05 (critic r04 gap 3: "legs lag the arc by 0.05-0.15 s"): ring of the swing phase over the last ~0.4 s; the leg
	// targets (thigh / knee) sample it 0.09 s behind while the torso and arms stay on the live phase
	double SwPhT[24] = { 0 }; float SwPhV[24] = { 0 }; int32 SwPhH = 0, SwPhN = 0;
	bool bInAirCycle = false;
	float AirCycleT = 0.f;
	int32 FlavorIdx = -1, CycleCount = 0;
	bool bReachRight = true;
	EWebTravMode LastMode = EWebTravMode::Ground;
	bool bFlipClips = false;
	TArray<FWebTravAnimLayer> PendingLegs;
	void BuildFlipLayers(FName Program, float T, TArray<FWebTravAnimLayer>& Out, TArray<FWebTravAnimLayer>& OutLegs);
};
