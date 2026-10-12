// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// P2 Characters: minimal native locomotion AnimInstance (idle / walk / jog / run / sprint 1D blend by speed with a
// shared, speed-synced phase, plus jump / fall / land). The AnimBP assets (/Game/Characters/*/ABP_*) are Blueprint
// children of this class that only set the clip references; the pose is produced natively in the proxy, so the
// AnimBPs are fully script-built (no hand-edited AnimGraph). Speed comes from the owner's CharacterMovement if it has
// one, otherwise from the component's world motion, or from ForcedSpeed (lineup walkers / turntables).
#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "WHCharAnimInstance.generated.h"

class UAnimSequence;

USTRUCT(BlueprintType)
struct WEBHOMAGE_API FWHLocoSample
{
	GENERATED_BODY()
	/** Looping locomotion clip (in place). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Locomotion") TObjectPtr<UAnimSequence> Clip = nullptr;
	/** Ground speed (cm/s) at which this clip plays at rate 1 without foot sliding. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Locomotion") float Speed = 150.f;
};

/** Round 09: one timed action of a choreography (a hit reaction, a strike, a get-up): the clip starts at stage time Start (WHCharStage.h), blends in
 *  over BlendIn, plays at Rate from ClipStart, then holds its last pose for Hold seconds (< 0 = for ever) and blends out over BlendOut back to
 *  whatever is underneath (guard idle / locomotion).  Weight caps the blend (a flinch that only half overrides the guard).  Overlapping beats
 *  cross-fade (their weights are normalised when they sum past 1). */
USTRUCT(BlueprintType)
struct WEBHOMAGE_API FWHScriptBeat
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Script") TObjectPtr<UAnimSequence> Clip = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Script") float Start = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Script") float Rate = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Script") float BlendIn = 0.08f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Script") float BlendOut = 0.15f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Script") float Hold = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Script") float Weight = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Script") float ClipStart = 0.f;
};

struct FWHAnimLayer
{
	TObjectPtr<UAnimSequence> Seq = nullptr;
	float Time = 0.f;
	float Weight = 0.f;
	bool bLoop = true;
};

struct FWHCharAnimProxy : public FAnimInstanceProxy
{
	FWHCharAnimProxy() = default;
	explicit FWHCharAnimProxy(UAnimInstance* In) : FAnimInstanceProxy(In) {}
	virtual void PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds) override;
	virtual bool Evaluate(FPoseContext& Output) override;
	TArray<FWHAnimLayer> Layers;
};

UCLASS(Blueprintable, Transient)
class WEBHOMAGE_API UWHCharAnimInstance : public UAnimInstance
{
	GENERATED_BODY()
public:
	/** Locomotion samples, any order (sorted by Speed at init). Idle is the implicit speed-0 sample. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Locomotion") TArray<FWHLocoSample> Loco;
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Locomotion") TObjectPtr<UAnimSequence> Idle = nullptr;
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Air") TObjectPtr<UAnimSequence> JumpUp = nullptr;
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Air") TObjectPtr<UAnimSequence> Fall = nullptr;
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Air") TObjectPtr<UAnimSequence> Land = nullptr;
	/** Grounded anticipation crouch played while TakeoffTime >= 0 (set by the owner before it leaves the ground), blended in over TakeoffBlendIn. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Air") TObjectPtr<UAnimSequence> Takeoff = nullptr;
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Air") float TakeoffBlendIn = 0.07f;
	/** Round 05: when non-empty this replaces Idle while standing: the clips play back to back in a loop, each cross-faded into the next over
	 *  SequenceBlend seconds (a staged fight: guard -> punch -> guard ...).  One clip = that clip looped with a cross-faded seam. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Locomotion") TArray<TObjectPtr<UAnimSequence>> Sequence;
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Locomotion") float SequenceBlend = 0.15f;
	/** Round 09: choreographed beats (see FWHScriptBeat), copied from the owning walker; empty = none. */
	UPROPERTY(BlueprintReadWrite, Category="Script") TArray<FWHScriptBeat> Script;
	/** Seconds added to the idle / sequence clock (per actor, set by the owner) so a crowd of identical ABPs is not in lockstep. */
	UPROPERTY(BlueprintReadWrite, Category="State") float IdleOffset = 0.f;
	/** Round 05: alternate air clips: jump n plays JumpVariants[n % Num] (and Takeoff stays the same); empty = JumpUp every time. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Air") TArray<TObjectPtr<UAnimSequence>> JumpVariants;
	/** Rate (1/s) at which the air layer blends in after lift-off (14 = about 0.1 s; a running leap uses ~7 so the pose hand-over takes >= 0.15 s). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Air") float AirBlendIn = 14.f;
	/** True: the jump / leap clip keeps playing (and holds its last pose) until landing instead of handing over to Fall once the ascent ends. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Air") bool bJumpHoldsThroughDescent = false;
	/** Seconds the last takeoff pose is held under the air blend after lift-off. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Air") float TakeoffHoldTime = 0.12f;
	/** Below this speed (cm/s) the idle fully takes over. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Locomotion") float IdleSpeed = 20.f;
	/** Cadence/stride split: rate = (v/v_clip)^CadenceExp; the rest of the speed ratio is (visually) stride. 1 = pure rate. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Locomotion") float CadenceExp = 1.f;

	/** >= 0 overrides the measured ground speed (cm/s). */
	UPROPERTY(BlueprintReadWrite, Category="State") float ForcedSpeed = -1.f;
	/** Set by non-Character owners (e.g. AWHCharLoopWalker hops). */
	UPROPERTY(BlueprintReadWrite, Category="State") bool bForceAir = false;
	UPROPERTY(BlueprintReadWrite, Category="State") float ForcedVerticalSpeed = 0.f;
	/** >= 0: seconds into a grounded takeoff (anticipation crouch); < 0: none. */
	UPROPERTY(BlueprintReadWrite, Category="State") float TakeoffTime = -1.f;

	UPROPERTY(BlueprintReadOnly, Category="State") float Speed = 0.f;
	UPROPERTY(BlueprintReadOnly, Category="State") float VerticalSpeed = 0.f;
	UPROPERTY(BlueprintReadOnly, Category="State") bool bInAir = false;

	virtual void NativeInitializeAnimation() override;
	virtual void NativeUpdateAnimation(float DeltaSeconds) override;

	TArray<FWHAnimLayer> GameLayers;

protected:
	virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override { return new FWHCharAnimProxy(this); }
	virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* P) override { delete P; }

private:
	FVector LastPos = FVector::ZeroVector;
	bool bHasLast = false;
	int32 JumpCount = 0;
	float Phase = 0.f, IdleTime = 0.f, AirAlpha = 0.f, AirTime = 0.f, FallAlpha = 0.f, LandTime = 1e3f, SmoothedSpeed = 0.f, TakeoffHold = 0.f, LastTakeoff = -1.f;
	bool bWasInAir = false;
};
