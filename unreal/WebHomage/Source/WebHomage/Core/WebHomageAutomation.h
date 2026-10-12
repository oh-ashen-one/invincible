// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Tickable.h"
#include "WebHomageAutomation.generated.h"

/**
 * Command-line driven capture / perf director for unattended runs of the real game
 * (standalone -game or PIE). All times are GAME seconds since the subsystem started
 * (deterministic under -benchmark -fps=60, ~wall clock otherwise).
 *
 *   -WHShotAt=3,8.5        screenshots (true back-buffer size, no UI) at those times
 *   -WHShotDir=<abs dir>   output folder (default <Project>/Saved/WHCaptures)
 *   -WHShotName=<prefix>   file prefix (default "shot")
 *   -WHShotCam=<file.json>  matched-camera shots: a JSON list of {t, name, ue_pos_cm, ue_target_cm, fov (horizontal deg), hero_visible}. At each t a free camera is
 *                          placed there (view target override; the hero hidden unless hero_visible), -WHShotCamWait=<s> (default 1.0) later the shot
 *                          <dir>/<prefix>_<NN>_<name>.png is taken (exposure / TSR settle in between). Optional per entry: hero_pos_m [X, Y, Z] (UE axes, metres, feet position) and
 *                          hero_yaw_deg: the traversal hero is teleported there (and held there every tick until the shot)
 *   -WHPerfFrom=3 -WHPerfTo=13   frame-time window: writes <dir>/<prefix>_perf.json and logs
 *                          "WH_PERF ..." (avg/p50/p95/p99 frame ms, GPU ms, render size)
 *   -WHCsv                 also run CsvProfile Start/Stop over the perf window
 *   -WHQuitAt=15           request clean exit at that time
 *   -WHAutoMove            (character) run/turn/jump automatically
 * See unreal/WebHomage/CAPTURE.md.
 */
UCLASS()
class WEBHOMAGE_API UWebHomageAutomation : public UGameInstanceSubsystem, public FTickableGameObject
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	// FTickableGameObject
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	virtual bool IsTickable() const override { return bActive; }
	virtual ETickableTickType GetTickableTickType() const override { return ETickableTickType::Conditional; }
	virtual bool IsTickableWhenPaused() const override { return true; }

private:
	void WritePerf();

	bool bActive = false;
	double Elapsed = 0.0;
	double LastWall = 0.0;

	struct FCamShot { double T = 0; FString Name; FVector Pos = FVector::ZeroVector, Target = FVector::ZeroVector; float Fov = 90.f; bool bHero = false; bool bPlaced = false, bShot = false; bool bHeroPos = false; FVector HeroPosM = FVector::ZeroVector; double HeroYawDeg = 0.0; };
	TArray<FCamShot> CamShots;
	double CamWait = 1.0;
	TWeakObjectPtr<class ACameraActor> CamActor;
	bool bHeroHidden = false;
	void TickCamShots(class UWorld* World);
	TArray<double> ShotTimes;
	int32 NextShot = 0;
	TArray<TPair<double, FString>> ExecAt;   // -WHExecAt=<t>:<command>[;<t>:<command>...] console commands at game seconds (ProfileGPU in a perf window)
	int32 NextExec = 0;
	FString ShotDir;
	FString ShotName = TEXT("shot");

	double PerfFrom = -1.0;
	double PerfTo = -1.0;
	bool bCsv = false;
	bool bPerfRunning = false;
	bool bPerfDone = false;
	TArray<float> FrameMs;
	TArray<float> FrameT;   // game seconds of each perf-window frame (<name>_frames.csv)
	TArray<float> GpuMs;

	double QuitAt = -1.0;
	bool bQuitRequested = false;
};
