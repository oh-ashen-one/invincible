// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
// Invincible flight conversion (owner request 2026-10-15): the shared hub between the flying hero, the destruction proxies,
// the crowd and the rescue clock. One per game world. Everything here is plain data written by its owner system and read by the
// others, so each system can be built, tested and replaced on its own:
//   - the hero (AWebTravCharacter + UWHFlightComponent) writes HeroPosCm / HeroVelCm / bHeroFlying and the interact press,
//     and pushes crowd stimuli for flyovers, sonic booms, breaches and landings;
//   - AWHBreachDirector (destruction proxies) adds collateral and pushes impact stimuli;
//   - the crowd (AWHLifeCrowd through the IWHCrowdBrain hook) reads the stimuli;
//   - AWHRescueDirector (emergencies + rescue clock) reads the hero state / interact press and writes the score.
// Units: centimetres (Unreal world), seconds of game time (UWorld::GetTimeSeconds).
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "WHFlightWorld.generated.h"

UENUM(BlueprintType)
enum class EWHCrowdStimulus : uint8
{
	Flyover,    // the hero passes overhead (pedestrians look up)
	SonicBoom,  // the hero crossed the boom speed (look up, some flinch)
	Impact,     // a facade breach / crater / falling debris (flee)
	Landing,    // superhero landing (flee a short distance, then gawk)
	Emergency,  // a rescue emergency in progress (flee the danger zone)
};

USTRUCT(BlueprintType)
struct WEBHOMAGE_API FWHCrowdStimulus
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly, Category="Crowd") EWHCrowdStimulus Type = EWHCrowdStimulus::Flyover;
	UPROPERTY(BlueprintReadOnly, Category="Crowd") FVector PosCm = FVector::ZeroVector;
	UPROPERTY(BlueprintReadOnly, Category="Crowd") FVector VelCm = FVector::ZeroVector;   // source velocity (cm/s), e.g. the hero's
	UPROPERTY(BlueprintReadOnly, Category="Crowd") float RadiusCm = 3000.f;               // reaction radius
	UPROPERTY(BlueprintReadOnly, Category="Crowd") float Strength = 1.f;                  // 0..1
	UPROPERTY(BlueprintReadOnly, Category="Crowd") float Time = 0.f;                      // world time when pushed (s)
	UPROPERTY(BlueprintReadOnly, Category="Crowd") float Life = 4.f;                      // seconds the stimulus stays active
};

UCLASS()
class WEBHOMAGE_API UWHFlightWorldSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()
public:
	static UWHFlightWorldSubsystem* Get(const UObject* WorldContext);

	// ---- hero state (written by the hero every frame)
	FVector HeroPosCm = FVector::ZeroVector;
	FVector HeroVelCm = FVector::ZeroVector;
	bool bHeroFlying = false;
	bool bHeroValid = false;
	/** True for exactly the frame the interact button (E / Triangle) was pressed. */
	bool bInteractPressed = false;
	/** True while the interact button is held. */
	bool bInteractHeld = false;
	/** Flight mode is on (Invincible). False = the legacy web-swing hero: crowd / rescue / HUD stay dormant. */
	bool bFlightMode = false;

	// ---- crowd stimuli
	void PushStimulus(const FWHCrowdStimulus& S);
	void PushStimulus(EWHCrowdStimulus Type, const FVector& PosCm, float RadiusCm, float Strength, float Life, const FVector& VelCm = FVector::ZeroVector);
	/** Stimuli still alive at world time Now (pruned on read). */
	const TArray<FWHCrowdStimulus>& ActiveStimuli(float Now);

	// ---- chase villain (enemy-race mini-game, owner request 2026-10-25): written by AWHChaseVillain every
	// tick, read by AWHFlightHUD. Positions are centimetres, same as the hero state above.
	FVector VillainPosCm = FVector::ZeroVector;
	FVector VillainVelCm = FVector::ZeroVector;
	int32 VillainState = 0;          // 0 absent, 1 roam, 2 flee, 3 caught
	FString VillainTaunt;            // current taunt line (empty = none showing)
	float VillainTauntUntil = 0.f;   // world seconds until the taunt clears
	bool bVillainActive = false;
	bool bVillainCaught = false;
	float ChaseStartT = -1.f;        // world time the chase began (villain spawn)
	double ChaseCaughtT = 0.0;       // world time of the catch
	// ---- enemy-race cutscene: the villain's dialogue line for the HUD subtitle (speaker prefixed), while bChaseScene
	FString ChaseLine;
	float ChaseLineUntil = 0.f;
	bool bChaseScene = false;

	// ---- score
	UPROPERTY(BlueprintReadOnly, Category="Flight") float CollateralUSD = 0.f;
	UPROPERTY(BlueprintReadOnly, Category="Flight") int32 Breaches = 0;
	UPROPERTY(BlueprintReadOnly, Category="Flight") int32 Craters = 0;
	UPROPERTY(BlueprintReadOnly, Category="Flight") int32 LivesSaved = 0;
	UPROPERTY(BlueprintReadOnly, Category="Flight") int32 LivesLost = 0;
	void AddCollateral(float USD, const TCHAR* Why);

private:
	TArray<FWHCrowdStimulus> Stimuli;
};
