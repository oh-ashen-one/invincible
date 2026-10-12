// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// P2 Characters: lineup actor for judging characters while moving. A skeletal mesh that walks/runs an elliptical
// loop at a set ground speed (optionally hopping every N s to exercise jump/fall/land), or turns in place
// (turntable) while its locomotion plays at ForcedSpeed, walks a straight line (Line: for side-tracking clips), or just stands.
// Drives UWHCharAnimInstance.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Characters/WHCharAnimInstance.h"
#include "WHCharLoopWalker.generated.h"

class USkeletalMeshComponent;

UENUM(BlueprintType)
enum class EWHWalkerMode : uint8 { Loop, Turntable, Stand, Line };

/** Round 09: one key of a choreographed path (Stand mode): the actor's world location and yaw at stage time Time (WHCharStage.h). */
USTRUCT(BlueprintType)
struct WEBHOMAGE_API FWHPathKey
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Path") float Time = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Path") FVector Loc = FVector::ZeroVector;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Path") float Yaw = 0.f;
};

UCLASS()
class WEBHOMAGE_API AWHCharLoopWalker : public AActor
{
	GENERATED_BODY()
public:
	AWHCharLoopWalker();
	virtual void BeginPlay() override;
	virtual void Tick(float Dt) override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;
	/** Line mode: jump back to LineStart (and reposition now). The director calls this at the start of the shots that list this walker. */
	UFUNCTION(BlueprintCallable, Category="Walker") void RestartLine();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Walker") TObjectPtr<USkeletalMeshComponent> Mesh;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Walker") EWHWalkerMode Mode = EWHWalkerMode::Loop;
	/** Ground speed in cm/s (also fed to the AnimInstance as ForcedSpeed). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Walker") float Speed = 140.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Walker") float RadiusX = 600.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Walker") float RadiusY = 300.f;
	/** Start angle on the ellipse, degrees. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Walker") float StartAngle = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Walker") bool bClockwise = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Walker") float TurntableDegPerSec = 30.f;
	/** 0 = never; otherwise hop every N seconds (Loop and Line modes). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Walker") float HopInterval = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Walker") float HopVelocity = 520.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Walker") float Gravity = 1470.f;
	/** Grounded anticipation before each hop (s): the AnimInstance plays its Takeoff crouch, then the actor leaves the ground. 0 = none. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Walker") float TakeoffTime = 0.f;
	/** First hop this many seconds after BeginPlay / RestartLine (<0: HopInterval). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Walker") float FirstHopDelay = -1.f;
	/** Line mode: walks along the actor's initial yaw (0 = +X, 180 = -X) from Center - LineLength/2, starting LineStart cm along it, and wraps at LineLength (cm). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Walker") float LineLength = 3000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Walker") float LineStart = 0.f;

	/** Seconds added to this actor's idle / sequence clock (AnimInstance IdleOffset): identical AnimBPs are not in lockstep. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Walker") float AnimOffset = 0.f;

	/** Round 09 (choreographed fight, Stand mode): when non-empty the actor's location / yaw are a pure function of the stage time (keys linearly
	 *  interpolated, yaw along the shorter arc); the horizontal speed it implies drives the locomotion blend, so a walk-in plays the walk clip. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Script") TArray<FWHPathKey> StagePath;
	/** Round 09: timed clips played over the guard idle (copied to the AnimInstance): hit reactions, strikes, get-ups (FWHScriptBeat). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Script") TArray<FWHScriptBeat> Script;

	/** World-space centre of the loop (set from the actor location at BeginPlay). */
	UPROPERTY(BlueprintReadOnly, Category="Walker") FVector Center = FVector::ZeroVector;

	// ---- Round 07: walker avoidance (Line mode).  Every Line walker with bAvoid is a capsule of AvoidRadius (cm) in the ground plane; the group is
	// stepped once per frame by the first member that ticks (order independent): each walker looks AvoidLookAhead s ahead at where the others will
	// be and moves sideways (never faster than AvoidLateralSpeed, prefers its right-hand side) so that no two capsules overlap; whatever is left at
	// the current instant is pushed apart (hard limit).  Telemetry: -WHWalkerLog=<csv> writes frame,time,label,x,y,yaw,offset,min_pair_dist.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Avoid") bool bAvoid = false;
	/** Capsule radius, cm (the brief asks for >= 35). Two capsules never overlap = centres stay >= 2 x AvoidRadius apart. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Avoid") float AvoidRadius = 40.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Avoid") float AvoidLateralSpeed = 55.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Avoid") float AvoidMargin = 15.f;
	/** Sideways offset from the lane (cm, to the walker's right) and the smallest centre distance to another avoiding walker in the last step. */
	UPROPERTY(BlueprintReadOnly, Category="Avoid") float LaneOffset = 0.f;
	UPROPERTY(BlueprintReadOnly, Category="Avoid") float MinPairDistance = 1e9f;

private:
	bool SamplePath(float T, FVector& OutP, float& OutYaw) const;
	TWeakObjectPtr<UAnimInstance> ScriptTarget;
	bool bPathFirst = true;
	float Theta = 0.f, HopT = 0.f, Z = 0.f, Vz = 0.f, Yaw = 0.f, LineD = 0.f, TakeoffT = -1.f;
	bool bAir = false;
	void TickHop(float Dt);
	// avoidance state
	float LatVel = 0.f;
	uint64 StepStamp = 0;
	bool bStarted = false;
	FVector AvoidPos(float Tau, float Off) const;
	void ApplyLine();
	void StepAvoidGroup(float Dt, bool bForce);
};
