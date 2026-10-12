// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "UObject/SoftObjectPtr.h"
#include "WHMusicSubsystem.generated.h"

class UAudioComponent;
class USoundWave;

/** One background music player for the game instance, including pause/settings and map changes. */
UCLASS()
class WEBHOMAGE_API UWHMusicSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UWHMusicSubsystem();
	/** Call from the local controller's BeginPlay; repeated calls preserve the existing playback position. */
	void EnsureStarted(const UObject* WorldContextObject);
	virtual void Deinitialize() override;

private:
	bool bLoopProofReported = false;
	// A serialized default asset reference also makes the track visible to the cooker.
	UPROPERTY()
	TSoftObjectPtr<USoundWave> MusicAsset;

	// CreateSound2D creates an ownerless persistent component; this game instance retains and cleans it up.
	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> MusicComponent = nullptr;
};
