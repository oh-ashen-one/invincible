// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// Island showcase maps (Manhattan_Island*): the terrain level supersedes the city's park ribbons / lawns / ez park woodland and the flat water plane. build_terrain.py hides the same
// class of actors in City_Geo_T (a private copy of the midtown geometry level); the island city lives in World Partition cells, so the rule runs here as cells stream in:
// bHiddenInGame, collision kept (traversal floor).
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "WHIslandRules.generated.h"

UCLASS()
class WEBHOMAGE_API UWHIslandRules : public UWorldSubsystem
{
	GENERATED_BODY()
public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;
	virtual void Deinitialize() override;
private:
	void OnLevelAdded(ULevel* Level, UWorld* InWorld);
	int32 HideLevel(ULevel* Level);
	FDelegateHandle Handle;
	int32 TotalHidden = 0;
};
