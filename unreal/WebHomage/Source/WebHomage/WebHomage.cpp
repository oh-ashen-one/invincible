// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "WebHomage.h"
#include "Modules/ModuleManager.h"
#include "Engine/LevelStreamingAlwaysLoaded.h"
#include "Engine/World.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

DEFINE_LOG_CATEGORY(LogWebHomage);

// The accepted R5b terrain map already combines the city, terrain, traversal actors,
// golden lighting and river water. Restore the current integrated crowd/traffic
// sublevel in the opt-in owner preview without opening or resaving any source map.
class FWebHomageModule final : public FDefaultGameModuleImpl
{
	FDelegateHandle PreviewWorldHandle;

	static void PrepareOwnerWorld(UWorld* World, const UWorld::InitializationValues)
	{
		if (!World || !World->IsGameWorld() ||
			!FParse::Param(FCommandLine::Get(), TEXT("WHPreparedPlaytest"))) return;
		const FString Package = World->GetOutermost()->GetName();
		if (!Package.Contains(TEXT("/TerrainR5b/Maps/")) ||
			!Package.EndsWith(TEXT("Manhattan_Terrain"))) return;
		const FName LifePackage(TEXT("/Game/Tests/Life/Life_Actors"));
		for (const ULevelStreaming* Level : World->GetStreamingLevels())
			if (Level && Level->GetWorldAssetPackageFName() == LifePackage) return;
		ULevelStreamingAlwaysLoaded* Life = NewObject<ULevelStreamingAlwaysLoaded>(World, NAME_None, RF_Transient);
		Life->SetWorldAssetByPackageName(LifePackage);
		Life->SetShouldBeLoaded(true);
		Life->SetShouldBeVisible(true);
		World->AddStreamingLevel(Life);
		UE_LOG(LogWebHomage, Display, TEXT("WH_PREVIEW added accepted Life_Actors to R5b terrain preview"));
	}

public:
	virtual void StartupModule() override
	{
		FDefaultGameModuleImpl::StartupModule();
		PreviewWorldHandle = FWorldDelegates::OnPostWorldInitialization.AddStatic(&PrepareOwnerWorld);
	}
	virtual void ShutdownModule() override
	{
		FWorldDelegates::OnPostWorldInitialization.Remove(PreviewWorldHandle);
		FDefaultGameModuleImpl::ShutdownModule();
	}
};

IMPLEMENT_PRIMARY_GAME_MODULE(FWebHomageModule, WebHomage, "WebHomage");
