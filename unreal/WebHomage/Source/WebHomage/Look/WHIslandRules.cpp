// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Look/WHIslandRules.h"
#include "WebHomage.h"
#include "Engine/World.h"
#include "Engine/Level.h"
#include "GameFramework/Actor.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "HAL/IConsoleManager.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/VolumetricCloudComponent.h"

// Playable profile (Config/PerfPlayable.cvars): the tree instances (ISM_ez_* leaves / bark, ISM_trees_* crowns of every tile) leave the hardware ray-tracing scene as their cells stream in
// (docs/night1/perf round 05: ~42 k leaf instances per Midtown block cost ~0.6 ms of FrameTime); raster, shadows and distance fields are untouched.
static TAutoConsoleVariable<int32> CVarTreesOutOfRT(TEXT("wh.Perf.TreesOutOfRT"), 0, TEXT("1: tree HISMs of streamed island cells are removed from the ray-tracing scene."));

// Playable profile: the look rigs' volumetric cloud march is capped at this distance (km): the cost is min(TracingMaxDistance, r.VolumetricCloud.DistanceToSampleMaxCount) of the full march
// (docs/night1/perf round 04-05: 20 km = the as-found step length with DistanceToSampleMaxCount 50; golden / midday rigs trace 50 / 40 km).
static TAutoConsoleVariable<float> CVarCloudKm(TEXT("wh.Perf.CloudKm"), 0.f, TEXT(">0: TracingMaxDistance (km) of every VolumetricCloud of a streamed level (rig level instances)."));

bool UWHIslandRules::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* W = Cast<UWorld>(Outer);
	return W && W->IsGameWorld() && (W->GetMapName().Contains(TEXT("Manhattan_Island")) || FParse::Param(FCommandLine::Get(), TEXT("WHIslandRules")));
}

void UWHIslandRules::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	Handle = FWorldDelegates::LevelAddedToWorld.AddUObject(this, &UWHIslandRules::OnLevelAdded);
	for (ULevel* L : InWorld.GetLevels()) if (L) OnLevelAdded(L, &InWorld);
}

void UWHIslandRules::Deinitialize()
{
	if (Handle.IsValid()) { FWorldDelegates::LevelAddedToWorld.Remove(Handle); Handle.Reset(); }
	Super::Deinitialize();
}

void UWHIslandRules::OnLevelAdded(ULevel* Level, UWorld* InWorld)
{
	if (InWorld != GetWorld() || !Level) return;
	const int32 N = HideLevel(Level);
	TotalHidden += N;
	if (N > 0) UE_LOG(LogWebHomage, Display, TEXT("WH_ISLAND hide +level %s: %d city actors hidden in game (park ribbons / lawns / ez park trees / flat water), total %d"), *Level->GetOuter()->GetName(), N, TotalHidden);
}

int32 UWHIslandRules::HideLevel(ULevel* Level)
{
	int32 N = 0, NTrees = 0;
#if WITH_EDITOR
	static const TCHAR* Prefix[] = { TEXT("ISM_ez_park"), TEXT("ISM_ez_elm"), TEXT("ISM_ez_conifer"), TEXT("ISM_trees_park_crownfar"), TEXT("ISM_trees_elm_crownfar"), TEXT("ISM_trees_conifer_crownfar") };
	if (CVarCloudKm.GetValueOnGameThread() > 0.f)
		for (AActor* A : Level->Actors)
			if (AVolumetricCloud* VC = Cast<AVolumetricCloud>(A))
				if (UVolumetricCloudComponent* C = VC->FindComponentByClass<UVolumetricCloudComponent>()) { C->SetTracingMaxDistance(CVarCloudKm.GetValueOnGameThread()); UE_LOG(LogWebHomage, Display, TEXT("WH_ISLAND cloud TracingMaxDistance -> %.0f km"), CVarCloudKm.GetValueOnGameThread()); }
	for (AActor* A : Level->Actors)
	{
		if (!A || A->IsHidden()) continue;
		FString L = A->GetActorLabel();
		L.ReplaceInline(TEXT("-"), TEXT("_"));
		bool bHide = false;
		for (const TCHAR* P : Prefix) if (L.StartsWith(P)) { bHide = true; break; }
		if (!bHide && A->IsA<AStaticMeshActor>() && (L.StartsWith(TEXT("parkPaths")) || L.StartsWith(TEXT("mapLawns")))) bHide = true;
		if (!bHide && (L == TEXT("WaterPlane") || L.StartsWith(TEXT("WaterPlane__")))) bHide = true;
		if (bHide) { A->SetActorHiddenInGame(true); ++N; }
		else if (CVarTreesOutOfRT.GetValueOnGameThread() > 0 && (L.StartsWith(TEXT("ISM_ez_")) || L.StartsWith(TEXT("ISM_trees_"))))
		{
			TInlineComponentArray<UInstancedStaticMeshComponent*> Is(A);
			for (UInstancedStaticMeshComponent* C : Is) if (C) { C->SetVisibleInRayTracing(false); ++NTrees; }
		}
	}
#endif
	if (NTrees > 0) UE_LOG(LogWebHomage, Display, TEXT("WH_ISLAND tree components out of ray tracing in %s: %d"), *Level->GetOuter()->GetName(), NTrees);
	return N;
}
