// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// P2 Characters: in-game capture director for the character lineup map. Owns a camera, takes over player 0's view
// target and cycles through shots (orbit / side / three-quarter / close-up / wide) around target actors, so
// Scripts/run_game.sh -movie / -shots capture the RUNNING game. -WHCharShot=N starts at shot N.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WHCharShowDirector.generated.h"

class ACameraActor;

UENUM(BlueprintType)
enum class EWHShotKind : uint8 { Orbit, Side, ThreeQuarter, Closeup, Wide, Front };

USTRUCT(BlueprintType)
struct WEBHOMAGE_API FWHShot
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Shot") TObjectPtr<AActor> Target = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Shot") EWHShotKind Kind = EWHShotKind::Orbit;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Shot") float Duration = 5.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Shot") float Distance = 350.f;
	/** Height of the aim point above the target origin (cm). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Shot") float AimHeight = 100.f;
	/** Camera height relative to the aim point (cm). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Shot") float CamHeight = 10.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Shot") float FOV = 40.f;
	/** Orbit speed (deg/s) for Orbit shots; start azimuth for all target-relative shots. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Shot") float OrbitDegPerSec = 40.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Shot") float Azimuth = 0.f;
	/** Wide shots: fixed camera location. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Shot") FVector WorldLocation = FVector::ZeroVector;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Shot") FString Label;
	/** Line-mode walkers restarted when this shot begins (so a side-tracking clip always starts with the walkers at the same place). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Shot") TArray<TObjectPtr<AActor>> RestartWalkers;
	/** Round 05: with a non-empty Director.ManagedActors list, only these (plus the shot's target) are visible during the shot; every other managed actor is hidden. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Shot") TArray<TObjectPtr<AActor>> ShowActors;
	/** Round 11 (hero skins): >= 0 = switch the hero to this suit when the shot starts (UWHHeroSuitSubsystem, the same path as `wh.Suit`). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Shot") int32 Suit = -1;
	/** Round 11: the shot's target is player 0's pawn (the real playable hero) instead of Target. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Shot") bool bTargetPlayer = false;
	/** Round 16 (P2 skins): a CLOSEUP portrait that follows the target's HEAD bone: the stage camera is moved into the head's midsagittal plane (the actor's right axis turned
	 *  with the head = the plane's normal) and its up axis kept in that plane, so the idle head turn / roll does not swing the face off the camera axis (a nod does not move
	 *  that plane and is not followed).  Used by the 'headfront' still: the face's centre seam then projects to a straight vertical line. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Shot") bool bHeadLock = false;
};

UCLASS()
class WEBHOMAGE_API AWHCharShowDirector : public AActor
{
	GENERATED_BODY()
public:
	AWHCharShowDirector();
	virtual void BeginPlay() override;
	virtual void Tick(float Dt) override;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Director") TArray<FWHShot> Shots;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Director") bool bLoop = true;
	/** Round 05: actors whose visibility the director controls per shot (see FWHShot::ShowActors): a hero shot never shows another hero or a thug in the background. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Director") TArray<TObjectPtr<AActor>> ManagedActors;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
	void LogBones(float Ts);
	FString BoneLogPath, BoneLogBuf;
	// round 09: -WHStageShot=t1,t2 (stage clock = this director's shot clock): screenshots at STAGE times, not at the automation's own clock, which leads the stage clock by a
	// varying 0.4 - 2.4 s in a real-time run (measured on the round-09 fight stills); files <WHShotDir>/<WHShotName>_<nn>_t<ttt.t>.png like -WHShotAt
	TArray<double> StageShots; int32 NextStageShot = 0; FString StageShotDir, StageShotName;
	// round 16: -WHStageShotQuit = quit the game 3 s (stage clock) after the LAST stage shot (a contended GPU slows the stage clock: a process-time -quit lost 33 of 56 stills)
	bool bStageShotQuit = false; double StageQuitAt = -1.0; bool bStageQuitDone = false;
	int32 WaitTexDoneShot = -1; double WaitTexWall = 0.0;     // round 16: -WHStageWaitTextures
	// round 17 capture protocol (-WHSettleFrames=N [-WHSettleSeconds=S] [-WHStageShotRel]): a stage shot is NOT taken the moment its stage time arrives.  The stage clock, every skeletal animation and the
	// camera are frozen; the shot waits until (1) no asset (texture / material) is still compiling, no shader is compiling and every texture of the visible actors is fully resident
	// (r16: the lineup was taken 5 frames / 9 s into a 0.55 fps run: copper blotches = unresident / unconverged, ghost weapons = TAA history), then (2) counts N RENDERED frames (GFrameCounter ticks)
	// in which the camera and the poses did not move AND at least S world seconds (auto exposure), and only then requests the screenshot.  Any movement resets the count.
	int32 SettleFrames = 0; double SettleSeconds = 2.0; bool bStageShotRel = false;
	int32 SettleState = 0;                       // 0 idle, 1 waiting for residency, 2 counting static frames, 3 screenshot requested
	int32 SettleCount = 0, SettleResets = 0, SettleLastTexBad = 0; uint64 SettleShotFrame = 0, SettleFrame0 = 0; double SettleWall0 = 0.0, SettleWorld0 = 0.0, SettleCountWorld0 = 0.0;
	FVector SettleSigLoc = FVector::ZeroVector; FRotator SettleSigRot = FRotator::ZeroRotator; double SettleSigPose = 0.0; bool bSettleSigValid = false;
	bool bSettleCvars = false, bSettleFinished = false; uint64 SettleQuitFrame = 0; double SettleQuitWall = 0.0;
	int32 PreloadTicks = 0;                      // round 17: -WHPreload (movies): finish every asset compile + stream everything in on the 2nd tick, before the first recorded frame
	// round 17 (resume): the r17a lineup run never settled because the Char_Lineup map also holds LANE walkers (AWHCharLoopWalker: they move in Tick, in world time) -> the pose signature changed every
	// frame forever.  While a shot settles every walker's Tick is disabled (and the stage clock offset is re-synced afterwards), the timeout is checked BEFORE the reset branch, and the reset reasons are logged.
	TArray<TWeakObjectPtr<AActor>> FrozenWalkers;
	TArray<int32> SettleDumpCounts; int32 NextDump = 0; bool bSettleDumpAll = false;      // -WHSettleDump=1,2,4,8,16,32 : extra screenshots after that many static frames (the convergence curve of a shot)
	TArray<int32> ShotFrames; int32 NextShotFrame = 0; FString ShotFrameDir, ShotFrameName; bool bShotFramesQuit = false; uint64 ShotFramesQuitAt = 0;     // -WHShotFrames=3,6,9,... : plain screenshots at ENGINE FRAME numbers (no settle: the r16 protocol seen by frame count), with the residency probe at that frame
	int32 ProbeFrames = 0; int32 ProbeTick = 0;                                             // -WHProbeFrames=N : per-frame residency probe for the first N director ticks (the r16-style runs without the settle protocol)
	TMap<const void*, double> PoseParts; FString LastMover;
	void FreezeWalkers(bool bFreeze);
	void TickSettle();
	void PauseAllAnims(bool bPause);
	bool AllVisibleTexturesResident(int32& OutBad, FString& OutFirstBad) const;
	double PoseSignature() const;
	UPROPERTY() TObjectPtr<ACameraActor> Cam;
	float T = 0.f;
	int32 LastShot = -1;
	FVector SmoothAim = FVector::ZeroVector;
};
