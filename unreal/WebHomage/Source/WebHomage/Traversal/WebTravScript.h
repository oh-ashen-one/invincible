// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// Piece P3: deterministic scripted input playback + per-frame telemetry for traversal captures.
//
//   -WHTravScript=<abs path to .json>   timed input keys replayed instead of the live keyboard / pad
//   -WHTravCsv=<abs path to .csv>       per-frame telemetry (default <WHShotDir>/<WHShotName>_telemetry.csv when a
//                                       script is active)
//   -WHTravSeed=<int>                   trick RNG seed (default 1234)
//
// Script format (metres, UE axes, degrees for yaw):
// {
//   "name": "a_swing_chain",
//   "spawn": { "pos": [x, y, z], "yaw": 0, "camPitch": 0.14 },
//   "keys": [ { "t": 0.0, "move": [0, 1], "swing": true, "sprint": false, "jump": false, "zip": false, "drop": false,
//               "quick": false, "look": [yawRateDegPerSec, pitchDownRateDegPerSec],
//               "autoChain": true, "releasePhase": 0.45, "gap": 0.3, "repressVz": 2.0, "heading": 0 }, ... ]
// "heading" (world yaw, deg; "heading": false clears it) replaces the stick direction with that world direction expressed in
// camera-relative stick terms every frame (a player who keeps steering down the avenue); |move| stays the stick magnitude.
// "spawn" may also carry "vel": [vx, vy, vz] (m/s). "autoChain" drives the swing button with a deterministic rhythm rule
// (hold while swinging until the arc's front phase > releasePhase while rising, let go, re-press once `gap` s have passed
// and the vertical speed has dropped below `repressVz` m/s, i.e. near the apex like a player); the
// baked timed keys can be recovered from the telemetry column in_swing.
// }
// Each key holds its values from `t` until the next key; omitted fields keep the previous value. Game time starts at the
// first traversal tick, so the same file replays the same movement under -benchmark -fps=60.
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Traversal/WebTravTypes.h"
#include "WebTravScript.generated.h"

UCLASS()
class WEBHOMAGE_API UWebTravScript : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	bool IsActive() const { return bActive; }
	bool HasSpawn() const { return bHasSpawn; }
	FVector SpawnPosM() const { return SpawnPos; }
	double SpawnYawDeg() const { return SpawnYaw; }
	double SpawnCamPitch() const { return SpawnCamPitch_; }
	FVector SpawnVelM() const { return SpawnVel; }
	/** "autoChain" rule active at time T (release phase, re-press gap); false when off. */
	bool AutoChainAt(double T, double& OutReleasePhase, double& OutGap, double& OutRepressVz) const;
	/** autoChain "trickEvery": N > 0 = press trick on every Nth release (counting from the first). */
	int32 TrickEveryAt(double T) const;
	/** Round 10 autoChain "skyEvery": N > 0 = every Nth release is a SKY LAUNCH (jump-release + trick), `skyTricks` tricks chained
	 *  in the air, the next web pressed once falling below `skyRepressH` m over the floor (or `skyMax` s after the release);
	 *  the sky release waits for swing phase `skyPhase` (higher on the rising front than `releasePhase`). */
	int32 SkyEveryAt(double T, double& OutRepressH, int32& OutTricks, double& OutMax, double& OutPhase) const;
	int32 Seed() const { return SeedValue; }
	/** Round 17: the script's own "tune" / "camTune" strings ("Name=V,..."; empty = none). */
	const FString& TuneString() const { return TuneStr; }
	const FString& CamTuneString() const { return CamTuneStr; }

	/** Held input at script time T (seconds since the first traversal tick). Look is returned as a rate (rad/s). */
	FWebTravInput Sample(double T, FVector2D& OutLookRate) const;
	/** World-space steering at time T: true + yaw (deg) when a "heading" key is active (converted to camera-relative stick). */
	bool HeadingAt(double T, double& OutYawDeg) const;

	bool WantsTelemetry() const { return !CsvPath.IsEmpty(); }
	void AddTelemetryRow(const FString& Row);
	void SetTelemetryHeader(const FString& Header) { if (CsvHeader.IsEmpty()) CsvHeader = Header; }

private:
	struct FKey
	{
		double T = 0;
		TOptional<FVector2D> Move, Look;
		TOptional<double> Heading; // world yaw (deg) the stick steers toward; NaN-free: set "heading": null to clear
		TOptional<bool> Swing, Jump, Sprint, Zip, Drop, Quick, AutoChain, Trick;
		TOptional<FString> Flip; // round 11: flip program list for the next tricks ("backDouble,corkscrew"; "" = automatic)
		int32 TrickEvery = 0;
		int32 SkyEvery = 0, SkyTricks = 2;
		double SkyRepressH = 18, SkyMax = 3.0, SkyPhase = 0.8;
		double ReleasePhase = 0.45, Gap = 0.3, RepressVz = 1e9;
	};
	void Flush();

	bool bActive = false;
	bool bHasSpawn = false;
	FVector SpawnPos = FVector::ZeroVector, SpawnVel = FVector::ZeroVector;
	double SpawnYaw = 0, SpawnCamPitch_ = 0.14;
	int32 SeedValue = 1234;
	TArray<FKey> Keys;
	FString ScriptName;
	FString TuneStr, CamTuneStr;
	FString CsvPath, CsvHeader;
	TArray<FString> Rows;
	bool bWroteHeader = false;
};
