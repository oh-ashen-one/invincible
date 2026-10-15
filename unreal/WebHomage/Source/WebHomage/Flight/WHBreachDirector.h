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

	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxChunks = 140;
	UPROPERTY(EditAnywhere, Category="Destruction") int32 ChunksPerBreach = 34;
	UPROPERTY(EditAnywhere, Category="Destruction") int32 ChunksPerCrater = 14;
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxShards = 220;
	UPROPERTY(EditAnywhere, Category="Destruction") int32 ShardsPerBreach = 70;
	UPROPERTY(EditAnywhere, Category="Destruction") float ChunkLife = 6.f;
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxScars = 24;           // holes + craters kept in the world (oldest recycled)
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxGcActors = 4;
	UPROPERTY(EditAnywhere, Category="Destruction") float SlowMoScale = 0.3f;      // global time dilation at the breach exit cut
	/** The pawn's camera cut to the breach exit: start the slow-mo beat. */
	void CutSlowMo();
	UPROPERTY(EditAnywhere, Category="Destruction") float SlowMoReal = 0.32f;      // real seconds at that scale (then eased back over 0.2 s)
	UPROPERTY(EditAnywhere, Category="Destruction") float BreachUSD = 1500000.f;   // + BreachUSDPerSev x severity
	UPROPERTY(EditAnywhere, Category="Destruction") float BreachUSDPerSev = 3000000.f;
	UPROPERTY(EditAnywhere, Category="Destruction") float CraterUSD = 40000.f;
	UPROPERTY(EditAnywhere, Category="Destruction") float CraterUSDPerSev = 400000.f;

private:
	struct FChunk { UStaticMeshComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; double Born = -1e9; bool bLive = false; };
	struct FShard { UStaticMeshComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; FVector Pos = FVector::ZeroVector, Vel = FVector::ZeroVector; FQuat Q = FQuat::Identity; FVector Spin = FVector::ZeroVector; double T = 0, Life = 1.5; bool bLive = false; };
	struct FScar { UStaticMeshComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; };
	struct FRing { UStaticMeshComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; FVector Pos = FVector::ZeroVector; FQuat Q = FQuat::Identity; double T = 0, Life = 0.7, R1 = 30; bool bLive = false; };

	void Breach(const FVector& PosM, const FVector& DirM, float Sev, bool bEntry);
	void Crater(const FVector& PosM, float Sev);
	void Boom(const FVector& PosM, const FVector& DirM);
	void Bump(const FVector& PosM, const FVector& NormalM, float Sev);
	void SpawnChunks(const FVector& PosCm, const FVector& DirN, int32 N, double SpeedCms, const FLinearColor& Tint, double SizeCm);
	void SpawnShards(const FVector& PosCm, const FVector& DirN, int32 N, double SpeedCms);
	void PlaceScar(const FVector& PosCm, const FQuat& Q, const FVector& ScaleM, const FLinearColor& Color);
	void SpawnGc(const FVector& PosCm, const FVector& DirN);
	void StartSlowMo();
	void PlaySynth(int32 Kind, const FVector& PosCm, float Volume);   // 0 boom, 1 crash, 2 thud
	USoundBase* Authored(int32 Kind) const;
	UStaticMeshComponent* MakeComp(UStaticMesh* Mesh, UMaterialInterface* Base, UMaterialInstanceDynamic*& OutMid, bool bShadow);

	FWHCombatFx Fx;
	UPROPERTY(Transient) TObjectPtr<UStaticMesh> Cube;
	UPROPERTY(Transient) TObjectPtr<UStaticMesh> Cyl;
	UPROPERTY(Transient) TObjectPtr<UStaticMesh> Sphere;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MSolid;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MTrans;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MGlow;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MDecal;
	UPROPERTY(Transient) TObjectPtr<UObject> GcAsset;
	UPROPERTY(Transient) TArray<TObjectPtr<UObject>> KeepAlive;   // components / sound waves created at runtime
	UPROPERTY(Transient) TArray<TObjectPtr<AActor>> GcActors;
	UPROPERTY(Transient) TArray<TObjectPtr<UDecalComponent>> Decals;
	TArray<FChunk> Chunks;
	TArray<FShard> Shards;
	TArray<FScar> Scars;
	TArray<FRing> Rings;
	int32 NextChunk = 0, NextShard = 0, NextScar = 0, NextGc = 0, NextDecal = 0;
	FRandomStream Rng = FRandomStream(20261015);
	double SlowMoUntil = -1.0, SlowMoEaseEnd = -1.0;
	bool bSlowMo = false, bNoSlowMo = false, bNoAudio = false;
	double LastCutSlowMoT = -100.0;
	FVector LastBreachEntry = FVector::ZeroVector;
};
