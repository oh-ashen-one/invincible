// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
// Invincible flight conversion (owner request 2026-10-15): destruction PROXIES for through-building flight, crater landings and
// sonic booms. The procedural city is merged instanced geometry, so it is never fractured itself (that would cost the whole city
// its Nanite / instancing and break the two-renderer GPU budget). Instead, at each breach / landing a bounded set of proxies
// sells the destruction where the hero is:
//   - rubble chunks: pooled cubes simulated by Chaos rigid-body physics (hard cap MaxChunks, recycled oldest-first, 6 s life),
//   - glass spray: pooled thin shards integrated kinematically (no physics cost), tinted glass, fading,
//   - dust: the combat FX dust puffs (FWHCombatFx), a dark scorched-hole plate on the facade / a crater disc on the ground,
//   - optional authored fracture: if /Game/Invincible/Destruction/GC_FacadeChunk exists (a UGeometryCollection built in the editor,
//     see docs/invincible/HANDOFF steps), a crumbling geometry-collection actor is spawned at the hole too (cap MaxGcActors),
//   - optional crater decal: /Game/Invincible/FX/M_CraterDecal (deferred decal material) if it exists,
//   - a short global slow-mo when the camera cuts to the hero bursting out of a breach (-WHNoSlowMo or SlowMoScale 1 disables),
//   - synthesized audio (procedural sound waves: boom, crash, thud) when no authored cue exists at /Game/Invincible/Audio/S_*.
// Collateral damage is added to UWHFlightWorldSubsystem; the crowd reacts through the stimuli the flight component pushes.
//
// Round 3 (critic r2: breaches / sonic boom / craters looked fake). The assets below are built by Scripts/build_invincible_fx.py
// (headless commandlet) into /Game/Invincible/FX/ and are all OPTIONAL: every path falls back to the round-2 proxies when one is missing.
//   - M_BreachHole   deferred decal: procedural jagged near-black opening with a broken concrete rim, cracks and soot (facade, entry + exit),
//   - M_CraterDecal  deferred decal: scorched centre, fractured slab band, radial cracks (ground),
//   - M_InvVapour    translucent unlit fresnel-edged vapour (sonic-boom cone + rings, ground shock ring),
//   - M_InvDust      translucent lit eroded-edge dust puff (dense, larger, longer-lived smoke than the combat FX puffs),
//   - M_InvChunk     opaque lit concrete / brick speckle for debris pieces that did not get the hit facade's own material.
// Debris pieces take the material of the facade component the breach line-traces (opaque / masked surface materials only).
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Traversal/WebTravTypes.h"
#include "Combat/WHCombatFx.h"
#include "WHBreachDirector.generated.h"

class UStaticMeshComponent;
class UStaticMesh;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class USoundBase;
class UDecalComponent;

UCLASS()
class WEBHOMAGE_API AWHBreachDirector : public AActor
{
	GENERATED_BODY()
public:
	AWHBreachDirector();
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;

	/** Feed this frame's flight events (metres, from UWebTraversalComponent::Events). */
	void OnFlightEvents(const TArray<FWebTravEvent>& Events);

	// critic r2 (breaches: "at least 20 debris chunks", mixed sizes): more, smaller pieces; the pool grew with them
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxChunks = 240;
	UPROPERTY(EditAnywhere, Category="Destruction") int32 ChunksPerBreach = 44;
	UPROPERTY(EditAnywhere, Category="Destruction") int32 ChunksPerCrater = 16;
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxShards = 120;
	UPROPERTY(EditAnywhere, Category="Destruction") int32 ShardsPerBreach = 26;
	UPROPERTY(EditAnywhere, Category="Destruction") float ChunkLife = 6.f;
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxScars = 24;           // fallback scar discs (no decal assets) kept in the world (oldest recycled)
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxHoleDecals = 12;      // r3: facade opening decals kept in the world (oldest recycled)
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxCraterDecals = 6;     // r3: crater decals kept in the world (oldest recycled)
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxPuffs = 110;          // r3: dense dust puffs alive at once
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxRubble = 72;          // r3: static crater-rim rubble pieces kept (oldest recycled)
	UPROPERTY(EditAnywhere, Category="Destruction") int32 PuffsPerBreach = 14;
	UPROPERTY(EditAnywhere, Category="Destruction") float FacadeChunkFraction = 0.5f;   // r3: share of debris pieces that wear the traced facade material (-WHFacadeChunks=)
	UPROPERTY(EditAnywhere, Category="Destruction") float HoleHalfCm = 400.f;      // r3: half size of the opening decal box (the opening is ~39 % of it: ~3.1 m across at severity 0, ~3.7 m at 1)
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxGcActors = 4;
	UPROPERTY(EditAnywhere, Category="Destruction") float SlowMoScale = 0.3f;      // global time dilation at the breach exit cut
	/** The pawn's camera cut to the breach exit: start the slow-mo beat. */
	void CutSlowMo();
	UPROPERTY(EditAnywhere, Category="Destruction") float SlowMoReal = 0.32f;      // real seconds at that scale (then eased back over 0.2 s)
	UPROPERTY(EditAnywhere, Category="Destruction") float BreachUSD = 1500000.f;   // + BreachUSDPerSev x severity
	UPROPERTY(EditAnywhere, Category="Destruction") float BreachUSDPerSev = 3000000.f;
	UPROPERTY(EditAnywhere, Category="Destruction") float CraterUSD = 40000.f;
	UPROPERTY(EditAnywhere, Category="Destruction") float CraterUSDPerSev = 400000.f;
	// r3 sonic boom (critic r2: "a vapour cone or ring at least 25 % of frame width stays visible for at least 0.3 s")
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomLife = 1.0f;         // s: cone life (rings 0.75 x)  (owner feedback 2026-10-15 #1: 0.9 -> 1.0)
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomFollow = 0.6f;       // s the cone / rings stay glued to the hero before they hang in the air behind him (0.45 -> 0.6)
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomConeLenM = 9.f;      // cone length at its birth (grows 1.6x) (7 -> 9)
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomConeRadM = 3.2f;     // cone base radius at its birth (grows 2.4x) (2.4 -> 3.2)
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomOpacity = 0.30f;     // peak of the material's Opacity parameter (0.62 whited out the screen once the vapour became exposure-correct)

	// ---- owner feedback 2026-10-15 #1 (Shift = sonic-boom super boost) / #3 (speed feedback): the charge's vapour gather + slow-mo, a bigger
	// boom (shock ring left at the launch point, shock shell, glass / dust shaken off nearby facades, street dust ring), and continuous
	// super-speed FX: world wind streaks the hero and the camera fly past, a vapour trail / two contrails glued to the body, a dust wake on
	// the street under a low pass. M_InvStreak (additive speed-line material, build_invincible_fx.py) is optional; M_InvVapour stands in.
	/** Per-frame flight state from the pawn: charge 0..1, super-speed weight 0..1, fast-cruise weight 0..1, hero body (m) and velocity (m/s). */
	void SetFlightFx(float ChargeK, float SuperK, float FastK, const FVector& PosM, const FVector& VelM);
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxVapours = 110;        // pooled vapour / streak pieces (was a fixed 24)
	UPROPERTY(EditAnywhere, Category="Destruction") float StreakRate = 60.f;       // world wind streaks per second at full super speed
	UPROPERTY(EditAnywhere, Category="Destruction") float FastStreakRate = 14.f;   // per second at full fast-cruise weight outside the super line
	UPROPERTY(EditAnywhere, Category="Destruction") float StreakOpacity = 0.30f;
	UPROPERTY(EditAnywhere, Category="Destruction") float TrailEvery = 0.05f;      // s between body vapour-trail pieces in the super line
	UPROPERTY(EditAnywhere, Category="Destruction") float TrailOpacity = 0.35f;
	UPROPERTY(EditAnywhere, Category="Destruction") float WakeMaxH = 35.f;         // m: a super pass lower than this raises street dust under him
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomRingRadM = 24.f;     // launch shock ring radius at its end
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomShakeRadM = 45.f;    // facades within this get glass / dust shaken off at the boom
	UPROPERTY(EditAnywhere, Category="Destruction") float GatherOpacity = 0.25f;   // the charge's gathering vapour shell / inward streaks

private:
	struct FChunk { UStaticMeshComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; FVector Scale = FVector::OneVector; double Born = -1e9, NextCheck = 0; bool bLive = false, bFrozen = false; };
	struct FShard { UStaticMeshComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; FVector Pos = FVector::ZeroVector, Vel = FVector::ZeroVector; FQuat Q = FQuat::Identity; FVector Spin = FVector::ZeroVector; double T = 0, Life = 1.5; bool bLive = false; };
	struct FScar { UStaticMeshComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; };
	struct FRing { UStaticMeshComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; FVector Pos = FVector::ZeroVector; FQuat Q = FQuat::Identity; double T = 0, Life = 0.7, R1 = 30; bool bLive = false; };
	/** r3: one dense dust puff (a sphere with the eroded-edge dust material). Hidden until Delay, then Life s; sizes in cm. */
	struct FPuff { UStaticMeshComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; FVector Pos = FVector::ZeroVector, Vel = FVector::ZeroVector; double T = 0, Delay = 0, Life = 1.6, S0 = 100, S1 = 300, Peak = 0.7, Drag = 2.2, Rise = 60; bool bLive = false, bShown = false; };
	/** r3: a vapour cone (sonic boom) or a thin pancake ring (boom rings, ground shock ring). Anchor follows the hero for Follow s.
	 *  Owner feedback 2026-10-15 #1: Shape 0 cone, 1 ring (pancake), 2 ball (sphere shell), 3 streak (ellipsoid along Dir, M_InvStreak);
	 *  VelCm drifts a piece that does not follow; SideCm offsets a glued piece sideways; Env 0 fade-out after 40 %, 1 gather (ramps up
	 *  to the end), 2 streak (quick in, fades over the second half). */
	struct FVapour { UStaticMeshComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; FVector Anchor = FVector::ZeroVector, Dir = FVector::ForwardVector; double T = 0, Life = 0.9, Follow = 0.45, OffsetCm = 0, Len0 = 700, Len1 = 1100, Rad0 = 240, Rad1 = 560, Peak = 0.55; bool bCone = true, bLive = false;
		int32 Shape = 0, Env = 0; FVector VelCm = FVector::ZeroVector, SideCm = FVector::ZeroVector; };
	/** r3: a deferred decal with an animated "Open" parameter (the opening / crater grows over Grow s). */
	struct FDecalItem { UDecalComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; double T = 0, Grow = 0.2; bool bGrowing = false; };
	/** r3: static (non-physics) rubble pieces of the crater rim: they sit on the traced ground, so they cannot hang in the air. */
	struct FRubble { UStaticMeshComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; FVector Pos = FVector::ZeroVector, Scale = FVector::OneVector; FQuat Q = FQuat::Identity; double T = 0, Delay = 0, Life = 25; bool bLive = false; };
	/** r3: what the line trace at a breach / crater found (cm). */
	struct FFacadeHit { bool bHit = false; FVector Point = FVector::ZeroVector, Normal = FVector::UpVector; UMaterialInterface* Mat = nullptr; };

	void Breach(const FVector& PosM, const FVector& DirM, float Sev, bool bEntry);
	void Crater(const FVector& PosM, float Sev);
	void Boom(const FVector& PosM, const FVector& DirM);
	void Bump(const FVector& PosM, const FVector& NormalM, float Sev);
	/** the old signature: debris along DirN (kept for the fallback paths) */
	void SpawnChunks(const FVector& PosCm, const FVector& DirN, int32 N, double SpeedCms, const FLinearColor& Tint, double SizeCm);
	/** r3 debris: N pieces of mixed size (many 8-25 cm, a few to 50 cm) scattered on a disc of SpawnRadiusCm around OriginCm, flung along Axis (share AxisBias) and radially;
	 *  a share of them (FacadeChunkFraction) wears Look (the traced facade material), the rest M_InvChunk / flat tints (Brick = share of those that are brick). */
	void SpawnDebris(const FVector& OriginCm, const FVector& Axis, double SpawnRadiusCm, double SpeedCms, double AxisBias, int32 N, UMaterialInterface* Look, const FLinearColor& Tint, float Brick);
	void SpawnShards(const FVector& PosCm, const FVector& DirN, int32 N, double SpeedCms);
	void PlaceScar(const FVector& PosCm, const FQuat& Q, const FVector& ScaleM, const FLinearColor& Color);
	void SpawnGc(const FVector& PosCm, const FVector& DirN);
	void StartSlowMo();
	void PlaySynth(int32 Kind, const FVector& PosCm, float Volume);   // 0 boom, 1 crash, 2 thud
	USoundBase* Authored(int32 Kind) const;
	UStaticMeshComponent* MakeComp(UStaticMesh* Mesh, UMaterialInterface* Base, UMaterialInstanceDynamic*& OutMid, bool bShadow);

	// ---- round 3
	/** line trace A -> B (cm) against the world's solids; fills point / normal of the first hit and the first visible opaque surface material along the line */
	bool TraceFacade(const FVector& StartCm, const FVector& EndCm, FFacadeHit& Out) const;
	/** nearest ground below P (cm): z of the surface (or P.Z when nothing is found) and its material */
	double TraceGroundZ(const FVector& PCm, UMaterialInterface** OutMat = nullptr) const;
	void ProbeCone();
	void ExcludeHeroFromDecals();
	FDecalItem* AcquireDecal(TArray<FDecalItem>& Pool, int32& Next, int32 MaxN, UMaterialInterface* Mat);
	void PlaceHole(const FVector& PointCm, const FVector& IntoWall, float Sev);
	void PlaceCraterDecal(const FVector& PCm, float Sev);
	void SpawnPuff(const FVector& PosCm, const FVector& VelCms, double S0, double S1, double Life, double Peak, double DelayS, const FLinearColor& Col);
	void BreachDust(const FVector& PointCm, const FVector& OutN, const FVector& FlightDir, float Sev, bool bEntry);
	void CraterDust(const FVector& PCm, float Sev);
	void SpawnVapour(bool bCone, const FVector& AnchorCm, const FVector& Dir, double FollowS, double OffsetCm, double Len0, double Len1, double Rad0, double Rad1, double Peak, double Life, float EdgePow);
	void SpawnRim(const FVector& PCm, float Sev, UMaterialInterface* GroundMat);
	// owner feedback 2026-10-15 #1 / #3
	FVapour* SpawnShape(int32 Shape, const FVector& AnchorCm, const FVector& Dir, double FollowS, double OffsetCm, double Len0, double Len1, double Rad0, double Rad1, double Peak, double Life, float EdgePow, int32 Env);
	void ChargeFx(const FVector& PosM, const FVector& DirM, float SlowScale, float RealDur);
	void ShakeFacades(const FVector& PCm);
	void FlightFxTick(double Dt);
	void EndChargeSlowMo();

	FWHCombatFx Fx;
	UPROPERTY(Transient) TObjectPtr<UStaticMesh> Cube;
	UPROPERTY(Transient) TObjectPtr<UStaticMesh> Cyl;
	UPROPERTY(Transient) TObjectPtr<UStaticMesh> Sphere;
	UPROPERTY(Transient) TObjectPtr<UStaticMesh> Cone;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MSolid;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MTrans;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MGlow;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MDecal;     // crater decal (M_CraterDecal)
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MHole;      // facade opening decal (M_BreachHole)
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MVapour;    // M_InvVapour
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MDust;      // M_InvDust
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MChunk;     // M_InvChunk
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MStreak;    // M_InvStreak (owner feedback 2026-10-15: additive speed lines; optional)
	UPROPERTY(Transient) TObjectPtr<UObject> GcAsset;
	UPROPERTY(Transient) TArray<TObjectPtr<UObject>> KeepAlive;   // components / MIDs created at runtime (never trimmed)
	UPROPERTY(Transient) TArray<TObjectPtr<UObject>> AudioKeep;   // procedural sound waves (trimmed)
	UPROPERTY(Transient) TArray<TObjectPtr<AActor>> GcActors;
	TWeakObjectPtr<UMaterialInterface> LastFacadeMat;             // the last traced facade material (bumps reuse it)
	TArray<FChunk> Chunks;
	TArray<FShard> Shards;
	TArray<FScar> Scars;
	TArray<FRing> Rings;
	TArray<FPuff> Puffs;
	TArray<FVapour> Vapours;
	TArray<FDecalItem> HoleDecals, CraterDecals;
	TArray<FRubble> Rubble;
	int32 NextChunk = 0, NextShard = 0, NextScar = 0, NextGc = 0, NextPuff = 0, NextVapour = 0, NextHole = 0, NextCrater = 0, NextRubble = 0;
	FRandomStream Rng = FRandomStream(20261015);
	double SlowMoUntil = -1.0, SlowMoEaseEnd = -1.0;
	bool bSlowMo = false, bNoSlowMo = false, bNoAudio = false;
	double LastCutSlowMoT = -100.0;
	double LastBumpTraceT = -100.0;
	double ConeHCm = 100.0, ConeWCm = 100.0, ConeMidZCm = 0.0;   // /Engine/BasicShapes/Cone bounds (cm) and which end is the apex
	bool bConeApexUp = true;
	FVector LastBreachEntry = FVector::ZeroVector;
	// owner feedback 2026-10-15 #1 / #3: flight FX state (set by SetFlightFx every pawn frame; cm / cm/s) and the charge slow-mo (real time)
	float FxChargeK = 0.f, FxSuperK = 0.f, FxFastK = 0.f;
	FVector FxPosCm = FVector::ZeroVector, FxVelCm = FVector::ZeroVector;
	bool bFxValid = false;
	double StreakAcc = 0.0, TrailT = 0.0, WakeT = 0.0, GatherT = 0.0;
	bool bChargeSlow = false;
	double ChargeSlowEnd = 0.0;
};
