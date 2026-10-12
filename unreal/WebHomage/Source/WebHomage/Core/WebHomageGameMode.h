// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "WebHomageGameMode.generated.h"

/** Foundation game mode: spawns AWebHomageCharacter. Pieces subclass or swap DefaultPawnClass. */
UCLASS()
class WEBHOMAGE_API AWebHomageGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AWebHomageGameMode();
};
