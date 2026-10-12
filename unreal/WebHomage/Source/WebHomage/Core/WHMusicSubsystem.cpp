// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Core/WHMusicSubsystem.h"
#include "WebHomage.h"

#include "Components/AudioComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Sound/SoundWave.h"

UWHMusicSubsystem::UWHMusicSubsystem()
	: MusicAsset(FSoftObjectPath(TEXT("/Game/Audio/Music/SW_CuriousGroove.SW_CuriousGroove")))
{
}

void UWHMusicSubsystem::EnsureStarted(const UObject* WorldContextObject)
{
	if (IsValid(MusicComponent) || !WorldContextObject || !GEngine || !GEngine->UseSound()) return;
	UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull);
	if (!World || !World->IsGameWorld() || World->GetNetMode() == NM_DedicatedServer || World->GetGameInstance() != GetGameInstance()) return;

	USoundWave* Wave = MusicAsset.LoadSynchronous();
	if (!Wave)
	{
		UE_LOG(LogWebHomage, Warning, TEXT("WH_MUSIC missing %s; run Scripts/import_background_music.py"), *MusicAsset.ToString());
		return;
	}
	// The import saves these settings too. Enforce the runtime contract for regenerated content.
	Wave->bLooping = true;
	Wave->VirtualizationMode = EVirtualizationMode::PlayWhenSilent;
	Wave->OverrideLoadingBehavior(ESoundWaveLoadingBehavior::ForceInline);
	// Optional diagnostic seek for a short native check of the loop boundary; ordinary play starts at zero.
	float StartTime = 0.f;
	if (FParse::Value(FCommandLine::Get(), TEXT("WHMusicStartAt="), StartTime))
		StartTime = FMath::IsFinite(StartTime) ? FMath::Clamp(StartTime, 0.f, FMath::Max(0.f, Wave->Duration - 0.01f)) : 0.f;
	// Configure the 2D component before Play(), so it keeps playing while the game is paused.
	// Persistence creates it without a controller/world owner and excludes it from level-transition flushing.
	MusicComponent = UGameplayStatics::CreateSound2D(WorldContextObject, Wave, 0.25f, 1.f, StartTime, nullptr, true, false);
	if (IsValid(MusicComponent))
	{
		MusicComponent->SetUISound(true);
		if (FParse::Param(FCommandLine::Get(), TEXT("WHMusicVerify")))
		{
			MusicComponent->OnAudioPlaybackPercentNative.AddWeakLambda(this,
				[this](const UAudioComponent* Component, const USoundWave*, const float Progress)
				{
					// UE's mixer reports cumulative percent for looping waves (it clamps only non-looping sounds).
					if (!bLoopProofReported && Progress > 1.001f)
					{
						bLoopProofReported = true;
						UE_LOG(LogWebHomage, Display, TEXT("WH_MUSIC loop verified progress=%.5f playing=%d"), Progress, Component->IsPlaying() ? 1 : 0);
					}
				});
		}
		MusicComponent->Play(StartTime);
		UE_LOG(LogWebHomage, Display, TEXT("WH_MUSIC started asset=%s duration=%.3f start=%.3f volume=0.25 loop=1 persistent=1 ui=1"),
			*Wave->GetPathName(), Wave->Duration, StartTime);
	}
}

void UWHMusicSubsystem::Deinitialize()
{
	if (IsValid(MusicComponent))
	{
		MusicComponent->Stop();
		MusicComponent->DestroyComponent();
	}
	MusicComponent = nullptr;
	Super::Deinitialize();
}
