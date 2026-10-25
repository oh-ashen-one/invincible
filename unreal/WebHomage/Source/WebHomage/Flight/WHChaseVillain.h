// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
// Enemy-race chase mini-game (owner request 2026-10-25): the evil double. The same Invincible v2 body
// (SK_InvincibleV2, single-node clips) wearing a dark "evil" skin (M_CmbSolid MID), driven by its own
// kinematic flight brain instead of the player-input flight component:
//   roam   -- free flight around the map: wander waypoints picked in a ring around the hero, weaving
//   flee   -- the hero closing in starts the chase: he accelerates away with weaves and short bursts
//   taunt  -- a HUD line every few seconds while the hero is close ("Catch me if you can!")
//   caught -- the hero reaches him (touch, or E / Triangle held while close): he slows to a hover, done
// Spawned by the hero (WebTravCharacter) in flight mode; -WHChase=0 disables. Everything is kinematic:
// he does not breach buildings, he steers over / around them with two forward + down line traces.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WHChaseVillain.generated.h"

class USkeletalMeshComponent;
class USkeletalMesh;
class UAnimSequence;
class UMaterialInstanceDynamic;
class UMaterialInterface;

UCLASS()
class WEBHOMAGE_API AWHChaseVillain : public AActor
{
	GENERATED_BODY()
public:
	AWHChaseVillain();
	virtual void BeginPlay() override;
	virtual void Tick(float Dt) override;

	// WaitHere = the marked spawn-in-place phase (beacon + hover until the hero arrives); Scene = the dialogue
	// cutscene before he bolts. Roam / Flee / Caught keep their old values (the HUD reads these ints).
	enum class EState : uint8 { Roam = 1, Flee = 2, Caught = 3, WaitHere = 4, Scene = 5 };

	/** -WHChaseTune=Name=Value,... overrides the tunables below (same convention as -WHFlightTune). */
	void ApplyTune(const FString& S);
	/** B restarts the chase after a catch: he re-spawns on a fresh bearing, chase clock resets. */
	void RestartChase(float Now);

private:
	void SetupBody();
	void StepBrain(float Dt);
	void StepMove(float Dt);
	void StepScene(float Dt);
	void Publish(UWorld* W);
	void PickWaypoint();
	void MaybeTaunt(float Now, double DistM, float Dt);
	void OnCaught(float Now);
	void SetClip(UAnimSequence* Seq);
	void BeginScene(const FVector& HeroPosCm);
	void EndScene();

	UPROPERTY(VisibleAnywhere) TObjectPtr<USkeletalMeshComponent> Body;

	// ---- tunables (m/s; hero cruise 55, super 300 -- the flee line is beatable but the bursts are not)
	float RoamSpeed = 38.f;      // free-flight wander
	float FleeSpeed = 50.f;      // escape run while the hero is inside FleeRadius
	float BurstSpeed = 130.f;    // short burst, FleeBurstDur s every FleeBurstEvery s
	float BurstDur = 1.1f;
	float BurstEvery = 5.5f;
	float FleeRadiusM = 90.f;    // hero this close starts the chase
	float CatchRadiusM = 9.f;    // E / Triangle held this close = caught
	float TouchRadiusM = 3.5f;   // body contact = caught, no button needed
	float MinAltM = 12.f;        // stay off the street while roaming
	float MaxAltM = 260.f;

	EState State = EState::Roam;
	FVector PosCm = FVector::ZeroVector;
	FVector VelCm = FVector::ZeroVector;      // cm/s
	FVector WayCm = FVector::ZeroVector;      // current roam waypoint
	bool bHaveWay = false;
	float WeaveT = 0.f;
	float BurstT = 0.f, BurstCd = 0.f;
	float TauntCd = 0.f;
	float StimT = 0.f;
	float SpawnT = 0.f;
	float FleeHoldT = 0.f;   // keep fleeing briefly after the hero falls out of the radius
	float CaughtT = -1.f;
	float BreachCd = 0.f;    // s until the next facade punch-through is allowed
	bool bPrevB = false;     // B key last frame (restart edge)
	TWeakObjectPtr<class AWHBreachDirector> Breach;

	// ---- spawn / cutscene: a tall glow column marks his spot until the hero closes in
	UPROPERTY(Transient) TObjectPtr<class UStaticMeshComponent> Beacon;
	float SceneT = 0.f;
	TWeakObjectPtr<class ACameraActor> SceneCam;
	float TalkRangeM = 35.f;   // hero this close while he waits = start the cutscene

	TObjectPtr<UAnimSequence> SeqHover;
	TObjectPtr<UAnimSequence> SeqFly;
	TObjectPtr<UAnimSequence> SeqBoost;
	UAnimSequence* CurSeq = nullptr;
	float FlyPitch = 0.f;    // smoothed path pitch applied to the actor while in a path-aligned clip

	static const TCHAR* Taunts[];
};
