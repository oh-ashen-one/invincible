// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Core/WebHomageGameMode.h"
#include "Core/WebHomageCharacter.h"
#include "Core/WebHomagePlayerController.h"

AWebHomageGameMode::AWebHomageGameMode()
{
	DefaultPawnClass = AWebHomageCharacter::StaticClass();
	PlayerControllerClass = AWebHomagePlayerController::StaticClass();
}
