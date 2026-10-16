// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
// Invincible flight conversion (owner request 2026-10-15): the rescue clock. A few simultaneous emergencies across the city, each
// with its own countdown; the score is lives saved, not damage taken. The hero cannot die: nothing here touches the hero's body.
//   - Fire:     a burning facade spot with people trapped in batches. Hover within ~12 m and hold interact 2.5 s per batch.
//   - Crane:    a crane on a roof (or a free-standing tower crane in the street) whose load snaps loose when its clock runs low.
//               Touch the load (~6 m) before it reaches the street: caught, carried, set down. Interact while carrying drops it gently.
//   - Bus:      a bus teetering at an elevated edge (a bridge deck or roof edge). Hold interact within ~8 m for 2 s to pull it back.
// When every emergency of a wave is resolved the next wave starts ~20 s later at new sites. Lives saved / lost go to
// UWHFlightWorldSubsystem; an Emergency crowd stimulus is pushed around each active emergency every 2 s.
// Self-contained: spawned with a plain SpawnActor<AWHRescueDirector>() and finds its own sites with line traces (ECC_Visibility).
// Visuals are engine basic shapes with the combat FX materials (/Game/Combat/Materials/M_CmbFX, M_CmbTrans, M_CmbSolid).
// Log lines "WH_RESCUE ..." for every event (captures parse the log).
// Command line: -WHRescue=0 disables the director, -WHRescueSeed=N picks the deterministic site / clock stream.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WHRescueDirector.generated.h"

class UStaticMesh;
class USceneComponent;
class UStaticMeshComponent;
class UPointLightComponent;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class UWHFlightWorldSubsystem;

enum class EWHEmergencyType : uint8 { Fire, Crane, Bus };
enum class EWHEmergencyState : uint8 { Active, Saved, Lost };

/** One emergency. Plain data: the HUD reads it through AWHRescueDirector::GetEmergencies(). */
struct FWHEmergency
{
	int32 Id = 0;
	EWHEmergencyType Type = EWHEmergencyType::Fire;
	EWHEmergencyState State = EWHEmergencyState::Active;

	// ---- read by the HUD
	FVector FocusCm = FVector::ZeroVector;    // where the hero has to go (fire spot / crane load / bus centre), updated every tick
	double RemainingS = 0;                    // rescue clock (s); <= 0 once resolved
	double HoldProgress = 0;                  // 0..1 of the current hold-interact action (fire batch / bus pull)
	bool bHeroInRange = false;                // the hero is close enough to act
	bool bFalling = false;                    // crane: the load is falling
	bool bCarried = false;                    // crane: the hero carries the load
	int32 LivesAtStake = 0;                   // lives still in danger
	int32 LivesSaved = 0;
	int32 LivesLost = 0;

	// ---- internal
	FVector SiteCm = FVector::ZeroVector;     // anchor: fire spot / crane mast base / bus edge point
	FVector DangerCm = FVector::ZeroVector;   // street point the crowd flees from
	FVector OutDir = FVector::ForwardVector;  // horizontal: facade normal (fire) / boom direction (crane) / overhang direction (bus)
	double StartT = 0, DurationS = 90, EndT = 0, ResolvedT = 0, NextStimT = 0, HoldT = 0;
	bool bGeometry = false;                   // the site was found on real city geometry (false = fallback placement)
	const TCHAR* SiteKind = TEXT("fallback"); // log: facade / roof / street / bridge / fallback
	// fire
	int32 Batch = 0;
	TArray<int32> BatchLives;
	// crane
	FVector TipCm = FVector::ZeroVector;      // boom tip (the cable hangs from it)
	FVector LoadCm = FVector::ZeroVector, LoadVelCm = FVector::ZeroVector, LoadRestCm = FVector::ZeroVector;
	double StreetZ = 0, SnapAtT = 0, SnapT = -1, CarryT = 0;
	bool bSnapped = false, bLanded = false, bSettling = false;
	FVector SettleCm = FVector::ZeroVector;
	// critic r2 (round 3 hero, fl17): the load's rotation (it turns with the hero's body while carried) and the eased set-down
	// (from -> rest pose, levelled to its heading, clear of the hero's footprint)
	FQuat LoadQ = FQuat::Identity, SettleQ = FQuat::Identity, SettleFromQ = FQuat::Identity;
	FVector SettleFromCm = FVector::ZeroVector;
	double SettleT = 0, SettleDur = 1;
	double SettleXyT = 0.6;                   // r6 (critic r5 #1): s of the set-down's sideways ease (r2-r5: 0.6 s fixed)
	bool bDressed = false;                    // r6 (critic r5 #1 / #8): the load wears its shipping-container trims (DressLoad)
	// bus
	double PullT = 0;                         // seconds of the pull-back animation once saved
	double FallT = 0;                         // seconds of the fall once lost
	double BelowZ = 0;                        // ground under the overhang

	// visuals (owned by the director actor; destroyed when the emergency is removed)
	TArray<USceneComponent*> Parts;
	TArray<UStaticMeshComponent*> Flames;     // fire glow spheres (flicker)
	TArray<FVector> FlameBaseCm;
	TArray<float> FlameBaseM;
	TArray<UStaticMeshComponent*> People;     // fire: trapped figures, PeoplePerBatch per batch
	UStaticMeshComponent* Load = nullptr;     // crane load
	UStaticMeshComponent* Cable = nullptr;    // crane cable
	USceneComponent* BusRoot = nullptr;       // bus pivot at the edge (the bus parts are attached to it)
	UPointLightComponent* Light = nullptr;
	FRotator BusRestRot = FRotator::ZeroRotator;
};

UCLASS()
class WEBHOMAGE_API AWHRescueDirector : public AActor
{
	GENERATED_BODY()
public:
	AWHRescueDirector();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;
	virtual void Tick(float DeltaSeconds) override;

	/** The director of this world (nullptr if none). */
	static AWHRescueDirector* Find(const UWorld* World);

	/** All emergencies of the current wave (active and recently resolved; resolved ones linger a few seconds). */
	const TArray<FWHEmergency>& GetEmergencies() const { return Emergencies; }
	/** Waves started so far. */
	int32 GetWave() const { return Wave; }
	/** Seconds until the next wave starts (< 0: none pending). */
	double GetNextWaveIn() const;
	/** False if disabled with -WHRescue=0. */
	bool IsEnabled() const { return bEnabled; }

	static const TCHAR* TypeName(EWHEmergencyType T);

	/** Critic r2 (round 3 hero, fl17 "the hero stands on the load, no grip; the load leaves the frame in the carry dive"): the hero's
	 *  anim instance holds the carried crane load. Each frame it publishes where the load sits in the hero mesh's component space (cm,
	 *  rotation + translation, no scale); TickCrane (TG_PostPhysics, after the hero mesh ticked) renders the load at
	 *  LoadInMeshCS * HeroMesh->GetComponentTransform(), so the hands and the load agree in the same frame. Without a fresh anchor
	 *  (> 0.2 s old) the load follows the hero on the r2 fallback path. */
	void SetCarryAnchor(const USceneComponent* HeroMesh, const FTransform& LoadInMeshCS);
	/** Critic r2 (round 3 hero): the crane load being carried right now (false if none): its world transform (no scale) and half
	 *  extents (cm). Settling (set-down) loads are not carried. */
	bool GetCarriedLoad(FTransform& OutLoadWorld, FVector& OutHalfCm) const;
	/** r5 (critic r4 #6): set by the hero v2 anim instance (overhead carry). Then a load is caught from above only at CraneTouchAboveCm and
	 *  the crane's lives count on the set-down instead of the catch. Unset (v1 hero, -WHHeroV2=0): the r4 rules, unchanged. */
	void SetOverheadCarryHero(bool bOn) { bOverheadCarry = bOn; }

	// ---- tuning
	float FireRangeCm = 1200.f;
	float FireBatchHoldS = 2.5f;
	float CraneTouchCm = 600.f;
	float CraneTouchAboveCm = 300.f; // r5 (critic r4 #6): catch reach with the hero above the load (no landing on top of it)
	float CraneJoltS = 1.0f;         // the load jolts this long after the snap before it drops
	float CraneFallGravity = 520.f;  // cm/s^2: a slow, readable fall (~0.53 g); the snap is timed so the impact lands on the clock's zero
	float BusRangeCm = 800.f;
	float BusHoldS = 2.f;
	float MaxHoverSpeedCm = 2500.f;  // hold actions need the hero (nearly) hovering
	float WaveGapS = 20.f;
	float FirstWaveDelayS = 3.f;
	float StimulusEveryS = 2.f;
	float StimulusRadiusCm = 2500.f;
	float LingerS = 8.f;             // resolved emergencies stay visible this long
	float SetDownClearCm = 70.f;     // critic r2 (fl17): the set-down load's near face rests this far ahead of the hero's centre (he lands beside it)
	float SetDownSpeedCm = 600.f;    // critic r2: vertical speed scale of the eased set-down (duration = drop / this, 0.6-4 s)
	// r6 (critic r5 #1, overhead-carry hero only): the set-down lands beside / beyond the hero as seen from the camera (PickSetDown)
	float SetDownMinS = 1.2f;        // shortest eased set-down (he lowers it from overhead; r5: 0.6 s)
	float SetDownSideGapCm = 100.f;  // gap between the hero's centre line (camera -> hero) and the load's inner face, beside him
	float SetDownAheadCm = 150.f;    // load centre this far beyond the hero (plus half its depth) on the camera line
	float CarryMaxOverheadS = 40.f;  // auto set-down after this long (r5: 10 s for every hero; a carried street descent from ~135 m takes ~15 s)

private:
	// ---- waves / sites
	bool SpawnWave(bool bAllowFallback);
	FVector HeroPos() const;
	/** Line trace on ECC_Visibility ignoring this actor and pawns. False on no hit or when the start is inside geometry (bStartedInside). */
	bool TraceLine(const FVector& A, const FVector& B, FHitResult& Hit, bool* bStartedInside = nullptr) const;
	/** First surface straight down at XY between TopZ and BottomZ. */
	bool GroundAt(const FVector& XY, double TopZ, double BottomZ, FVector& Out, bool* bBlocked = nullptr) const;
	double ProbeStreetZ(const FVector& Center) const;
	bool FindEdge(const FVector& Top, double MinDrop, FVector& OutEdge, FVector& OutDir, FVector& OutBelow) const;
	bool FarFromUsed(const FVector& P) const;
	FVector Candidate(int32 Slot, int32 Try, const FVector& Center) const;

	bool PlaceFire(FWHEmergency& E, const FVector& Center, int32 Slot, bool bFallback);
	bool PlaceCrane(FWHEmergency& E, const FVector& Center, int32 Slot, bool bFallback);
	bool PlaceBus(FWHEmergency& E, const FVector& Center, int32 Slot, bool bFallback);

	// ---- per-type update
	void TickFire(FWHEmergency& E, double Now, double Dt, const FVector& Hero, bool bHover);
	void TickCrane(FWHEmergency& E, double Now, double Dt, const FVector& Hero);
	void TickBus(FWHEmergency& E, double Now, double Dt, const FVector& Hero, bool bHover);
	void Resolve(FWHEmergency& E, EWHEmergencyState S, double Now, const TCHAR* Why);
	void SaveLives(FWHEmergency& E, int32 N, const TCHAR* Why);
	void LoseLives(FWHEmergency& E, int32 N, const TCHAR* Why);
	void DestroyVisuals(FWHEmergency& E);

	// ---- visuals
	UStaticMeshComponent* AddMesh(FWHEmergency& E, UStaticMesh* Mesh, UMaterialInterface* Mat, const FLinearColor& Color,
		const FVector& PosCm, const FRotator& Rot, const FVector& ScaleM, float Emissive = 0.f, float Opacity = 1.f, USceneComponent* Parent = nullptr);
	UPointLightComponent* AddLight(FWHEmergency& E, const FVector& PosCm, const FLinearColor& Color, float Candela, float RadiusCm);
	void SetGlow(UStaticMeshComponent* C, const FLinearColor& Color, float Opacity);
	void BuildFire(FWHEmergency& E);
	void BuildCrane(FWHEmergency& E, const FVector& MastBase, double MastH, const FVector& TipCm);
	void BuildBus(FWHEmergency& E, const FVector& EdgeCm);
	/** r6 (critic r5 #1 / #8, fl17 "the load is an untextured flat grey box"): shipping-container dress of the crane load (overhead-carry hero). */
	void DressLoad(FWHEmergency& E);
	/** r6 (critic r5 #1): set-down spot beside / beyond the hero relative to the camera line, on level street-height ground with a clear line
	 *  from the hero and room around it. False: no candidate passed (the caller keeps the r2 placement). OutFS = (beyond, side) in m. */
	bool PickSetDown(const FVector& Hero, const FVector& HalfCm, FVector& OutCenterCm, FQuat& OutQ, FVector2D& OutFS) const;
	void Burst(const FVector& PosCm, double SizeM);   // dust / debris puff at an impact (short-lived, own list)

	struct FPuff { UStaticMeshComponent* C = nullptr; double T = 0, Life = 1.2, Size = 1; FVector Vel = FVector::ZeroVector; };
	TArray<FPuff> Puffs;

	TArray<FWHEmergency> Emergencies;
	TArray<FVector> UsedSites;
	// critic r2 (round 3 hero): carry anchor published by the hero's anim instance (SetCarryAnchor)
	TWeakObjectPtr<const USceneComponent> CarryMesh;
	FTransform CarryInMesh = FTransform::Identity;
	double CarryAnchorT = -1.0;
	bool bOverheadCarry = false;   // r5: see SetOverheadCarryHero
	UWHFlightWorldSubsystem* Sub() const;

	bool bEnabled = true;
	bool bStarted = false;
	int32 Wave = 0;
	int32 NextId = 1;
	int32 SpawnAttempts = 0;
	double NextWaveT = -1;
	double StreetZRef = 0;
	int32 Seed = 1977;
	FRandomStream Rng;

	UPROPERTY(Transient) TObjectPtr<UStaticMesh> Cube;
	UPROPERTY(Transient) TObjectPtr<UStaticMesh> Sphere;
	UPROPERTY(Transient) TObjectPtr<UStaticMesh> Cylinder;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MGlow;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MTrans;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MSolid;
};
