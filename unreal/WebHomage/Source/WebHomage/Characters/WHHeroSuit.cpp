// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Characters/WHHeroSuit.h"
#include "WebHomage.h"
#include "Core/WHSettings.h"

#include "Components/SkeletalMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformTime.h"
#include "InputCoreTypes.h"
#include "InputKeyEventArgs.h"
#include "Materials/MaterialInterface.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "UObject/UObjectIterator.h"

namespace
{
	const FName SuitSlot(TEXT("SpiderSuit"));
	const FName LensSlot(TEXT("Lens"));
	const FName FrameSlot(TEXT("LensFrame"));
	TWeakObjectPtr<UWHHeroSuitSubsystem> GLive;
	FString GPendingConsole;   // `wh.Suit <x>` typed before the subsystem finished its initial sync

	UWorld* FindGameWorld()
	{
		if (!GEngine) return nullptr;
		for (const FWorldContext& C : GEngine->GetWorldContexts())
			if ((C.WorldType == EWorldType::Game || C.WorldType == EWorldType::PIE) && C.World()) return C.World();
		return nullptr;
	}

	void ConsoleSuit(const TArray<FString>& Args, UWorld* World)
	{
		UWHHeroSuitSubsystem* S = UWHHeroSuitSubsystem::Get(World ? World : FindGameWorld());
		if (!S) { if (Args.Num() > 0) GPendingConsole = Args[0]; UE_LOG(LogWebHomage, Display, TEXT("WH_SUIT wh.Suit: no live suit set yet (queued)")); return; }
		if (Args.Num() == 0) { S->LogList(); return; }
		if (!S->SetSuitByName(Args[0], TEXT("console"))) UE_LOG(LogWebHomage, Warning, TEXT("WH_SUIT wh.Suit %s: no such suit (try wh.Suit with no argument)"), *Args[0]);
	}
	void ConsoleSuitNext(const TArray<FString>&, UWorld* World) { if (UWHHeroSuitSubsystem* S = UWHHeroSuitSubsystem::Get(World ? World : FindGameWorld())) S->Cycle(+1, TEXT("console next")); }
	void ConsoleSuitPrev(const TArray<FString>&, UWorld* World) { if (UWHHeroSuitSubsystem* S = UWHHeroSuitSubsystem::Get(World ? World : FindGameWorld())) S->Cycle(-1, TEXT("console prev")); }

	FAutoConsoleCommandWithWorldAndArgs GCmdSuit(TEXT("wh.Suit"), TEXT("wh.Suit [n|id]: switch the hero's ORIGINAL suit (no argument: list the suits). T / gamepad D-pad Up cycle in play."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&ConsoleSuit));
	FAutoConsoleCommandWithWorldAndArgs GCmdSuitNext(TEXT("wh.SuitNext"), TEXT("next hero suit"), FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&ConsoleSuitNext));
	FAutoConsoleCommandWithWorldAndArgs GCmdSuitPrev(TEXT("wh.SuitPrev"), TEXT("previous hero suit"), FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&ConsoleSuitPrev));
}

UWHHeroSuitSubsystem* UWHHeroSuitSubsystem::Get(const UObject* WorldContext)
{
	const UWorld* W = WorldContext ? WorldContext->GetWorld() : nullptr;
	return W ? W->GetSubsystem<UWHHeroSuitSubsystem>() : nullptr;
}

bool UWHHeroSuitSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	if (!Super::ShouldCreateSubsystem(Outer)) return false;
	const UWorld* W = Cast<UWorld>(Outer);
	return W && W->IsGameWorld();
}

TStatId UWHHeroSuitSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UWHHeroSuitSubsystem, STATGROUP_Tickables);
}

void UWHHeroSuitSubsystem::ParseCommandLine()
{
	const TCHAR* Cmd = FCommandLine::Get();
	FParse::Value(Cmd, TEXT("WHSuit="), CmdSuit, false);
	bPersist = FParse::Param(Cmd, TEXT("WHSuitPersist"));
	FString L;
	if (FParse::Value(Cmd, TEXT("WHSuitScript="), L, false) && !L.IsEmpty())
	{
		TArray<FString> Parts; L.ParseIntoArray(Parts, TEXT(","));
		for (const FString& P : Parts)
		{
			FString A, B;
			if (P.Split(TEXT(":"), &A, &B)) Script.Add({FCString::Atod(*A), B});
		}
		Script.Sort([](const FScriptStep& X, const FScriptStep& Y) { return X.T < Y.T; });
	}
	if (FParse::Value(Cmd, TEXT("WHSuitKeyScript="), L, false) && !L.IsEmpty())
	{
		TArray<FString> Parts; L.ParseIntoArray(Parts, TEXT(","));
		for (const FString& P : Parts) KeyScript.Add(FCString::Atod(*P));
		KeyScript.Sort();
	}
}

void UWHHeroSuitSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	GLive = this;
	ParseCommandLine();
	Set = LoadObject<UWHHeroSuitSet>(nullptr, SetPath);
	if (Set) Suits = Set->Suits;
	for (int32 i = Suits.Num() - 1; i >= 0; --i) if (!Suits[i].Material) { UE_LOG(LogWebHomage, Warning, TEXT("WH_SUIT entry %d (%s) has no material, dropped"), i, *Suits[i].Id.ToString()); Suits.RemoveAt(i); }
	if (Suits.Num() == 0)
	{
		UE_LOG(LogWebHomage, Display, TEXT("WH_SUIT no suit set at %s (run build_characters.py step 'skins'): suit swap disabled"), SetPath);
	}
	else
	{
		FString Ids; for (const FWHHeroSuitEntry& E : Suits) Ids += E.Id.ToString() + TEXT(" ");
		UE_LOG(LogWebHomage, Display, TEXT("WH_SUIT %d suits loaded: %s"), Suits.Num(), *Ids);
	}
}

void UWHHeroSuitSubsystem::Deinitialize()
{
	if (GLive.Get() == this) GLive.Reset();
	Super::Deinitialize();
}

FText UWHHeroSuitSubsystem::NameOf(int32 I) const
{
	return Suits.IsValidIndex(I) ? FText::FromString(Suits[I].DisplayName.IsEmpty() ? Suits[I].Id.ToString() : Suits[I].DisplayName) : FText::GetEmpty();
}

void UWHHeroSuitSubsystem::LogList() const
{
	for (int32 i = 0; i < Suits.Num(); ++i)
		UE_LOG(LogWebHomage, Display, TEXT("WH_SUIT list %d %s \"%s\"%s"), i, *Suits[i].Id.ToString(), *Suits[i].DisplayName, i == Index ? TEXT("  <- current") : TEXT(""));
}

bool UWHHeroSuitSubsystem::IsHeroSuitMaterial(const UMaterialInterface* M) const
{
	if (!M) return false;
	for (const FWHHeroSuitEntry& E : Suits) if (E.Material == M) return true;
	return M->GetName().StartsWith(TEXT("MI_Hero_Suit"));
}

void UWHHeroSuitSubsystem::CollectTargets(TArray<USkeletalMeshComponent*>& Out, bool bScanWorld) const
{
	const UWorld* W = GetWorld();
	if (!W) return;
	for (FConstPlayerControllerIterator It = W->GetPlayerControllerIterator(); It; ++It)
		if (const ACharacter* Ch = Cast<ACharacter>(It->IsValid() ? It->Get()->GetPawn() : nullptr))
			if (USkeletalMeshComponent* M = Ch->GetMesh()) Out.AddUnique(M);
	if (!bScanWorld) return;
	for (TObjectIterator<USkeletalMeshComponent> It; It; ++It)   // the capture stage's hero walker: any other mesh that wears a hero suit in the SpiderSuit slot
	{
		USkeletalMeshComponent* M = *It;
		if (!M || M->GetWorld() != W || M->IsTemplate() || !M->GetSkeletalMeshAsset()) continue;
		const int32 Slot = M->GetMaterialIndex(SuitSlot);
		if (Slot != INDEX_NONE && IsHeroSuitMaterial(M->GetMaterial(Slot))) Out.AddUnique(M);
	}
}

void UWHHeroSuitSubsystem::ApplyToHeroes(bool bScanWorld)
{
	if (!Suits.IsValidIndex(Index)) return;
	UMaterialInterface* Mat = Suits[Index].Material;
	UMaterialInterface* Lens = Suits[Index].LensMaterial;
	UMaterialInterface* Frame = Suits[Index].FrameMaterial;
	TArray<USkeletalMeshComponent*> T; CollectTargets(T, bScanWorld);
	for (USkeletalMeshComponent* M : T)
	{
		const int32 Slot = M->GetMaterialIndex(SuitSlot);
		if (Slot == INDEX_NONE) continue;
		if (M->GetMaterial(Slot) != Mat) { M->SetMaterial(Slot, Mat); M->SetTextureForceResidentFlag(true); }
		const int32 LSlot = Lens ? M->GetMaterialIndex(LensSlot) : INDEX_NONE;
		if (LSlot != INDEX_NONE && M->GetMaterial(LSlot) != Lens) M->SetMaterial(LSlot, Lens);
		const int32 FSlot = Frame ? M->GetMaterialIndex(FrameSlot) : INDEX_NONE;
		if (FSlot != INDEX_NONE && M->GetMaterial(FSlot) != Frame) M->SetMaterial(FSlot, Frame);
	}
}

void UWHHeroSuitSubsystem::Prewarm(int32 Around)
{
	const int32 N = Suits.Num();
	for (int32 d = -1; d <= 1; ++d)
	{
		const FWHHeroSuitEntry& E = Suits[((Around + d) % N + N) % N];
		TArray<UTexture*> Tex;
		E.Material->GetUsedTextures(Tex);
		for (UTexture* T : Tex) if (UTexture2D* T2 = Cast<UTexture2D>(T)) T2->SetForceMipLevelsToBeResident(20.f);
	}
}

bool UWHHeroSuitSubsystem::SetSuit(int32 I, const TCHAR* Why)
{
	const int32 N = Suits.Num();
	if (N == 0) return false;
	const double Wall0 = FPlatformTime::Seconds();
	if (!bSynced) bPreSync = true;   // a director shot / console command ran before the start-up choice: it wins
	I = ((I % N) + N) % N;
	const bool bChanged = I != Index;
	Index = I;
	FWHSettings& S = WHSettings();
	S.SuitIndex = I; S.SuitId = Suits[I].Id.ToString();
	if (S.bLive || bPersist) S.SaveSuit();
	ApplyToHeroes(/*bScanWorld*/ true);
	Prewarm(I);
	CheckFrames = 2; CheckWall0 = Wall0; CheckFrame0 = GFrameCounter; CheckIndex = I;
	UE_LOG(LogWebHomage, Display, TEXT("WH_SUIT set %d/%d %s (%s) changed=%d t=%.3f frame=%llu apply_ms=%.2f"), I, N, *Suits[I].Id.ToString(), Why, bChanged ? 1 : 0, Elapsed, GFrameCounter, (FPlatformTime::Seconds() - Wall0) * 1000.0);
	if (S.bLive && GEngine) GEngine->AddOnScreenDebugMessage(0x5017, 2.5f, FColor::White, FString::Printf(TEXT("SUIT %d / %d   %s"), I + 1, N, *Suits[I].DisplayName), true, FVector2D(2.f, 2.f));
	return true;
}

bool UWHHeroSuitSubsystem::SetSuitByName(const FString& X, const TCHAR* Why)
{
	if (Suits.Num() == 0) return false;
	if (X.IsNumeric()) return SetSuit(FCString::Atoi(*X), Why);
	for (int32 i = 0; i < Suits.Num(); ++i)
		if (Suits[i].Id.ToString().Equals(X, ESearchCase::IgnoreCase) || Suits[i].DisplayName.Equals(X, ESearchCase::IgnoreCase)) return SetSuit(i, Why);
	return false;
}

void UWHHeroSuitSubsystem::Cycle(int32 Dir, const TCHAR* Why)
{
	SetSuit(Index + Dir, Why);
}

void UWHHeroSuitSubsystem::InitialSync(APlayerController* PC)
{
	bSynced = true;
	FWHSettings& S = WHSettings();
	if (bPreSync) { UE_LOG(LogWebHomage, Display, TEXT("WH_SUIT start suit %d (%s) was set before the first sync: kept"), Index, Suits.IsValidIndex(Index) ? *Suits[Index].Id.ToString() : TEXT("?")); return; }
	if (bPersist && !S.bLive) S.LoadSuit();
	int32 Start = 0; const TCHAR* Src = TEXT("default");
	auto Find = [this](const FString& X) -> int32 { for (int32 i = 0; i < Suits.Num(); ++i) if (Suits[i].Id.ToString().Equals(X, ESearchCase::IgnoreCase)) return i; return INDEX_NONE; };
	if (!CmdSuit.IsEmpty()) { Start = CmdSuit.IsNumeric() ? FCString::Atoi(*CmdSuit) : FMath::Max(0, Find(CmdSuit)); Src = TEXT("-WHSuit"); }
	else if (S.bLive || bPersist)
	{
		const int32 ById = S.SuitId.IsEmpty() ? INDEX_NONE : Find(S.SuitId);
		Start = ById != INDEX_NONE ? ById : S.SuitIndex; Src = TEXT("settings");
	}
	Index = -1;   // force the apply + log of the first SetSuit
	const bool bWasPersist = bPersist; bPersist = false;   // the start-up choice is not a user change: do not write it back
	SetSuit(Start, Src);
	bPersist = bWasPersist;
	if (!GPendingConsole.IsEmpty()) { const FString P = GPendingConsole; GPendingConsole.Reset(); SetSuitByName(P, TEXT("console (queued)")); }
	UE_LOG(LogWebHomage, Display, TEXT("WH_SUIT start suit %d (%s) from %s, persist=%d live=%d"), Index, *Suits[Index].Id.ToString(), Src, bPersist ? 1 : 0, S.bLive ? 1 : 0);
}

void UWHHeroSuitSubsystem::Tick(float DeltaTime)
{
	if (Suits.Num() == 0) return;   // (UTickableWorldSubsystem::Tick is pure virtual: no Super call)
	const UWorld* W = GetWorld();
	Elapsed += DeltaTime;
	APlayerController* PC = W ? W->GetFirstPlayerController() : nullptr;
	if (!bSynced)
	{
		if (PC && PC->HasActorBegunPlay() && ++TicksWithPC >= 2) InitialSync(PC);
		return;
	}
	// the pawn re-applies the proxy / default suit when it spawns (SetupHeroMesh): keep the chosen one on the player's mesh every frame, scan the world twice a second
	const bool bScan = Elapsed >= NextScan;
	if (bScan) NextScan = Elapsed + 0.5;
	ApplyToHeroes(bScan);

	for (FScriptStep& St : Script)
		if (!St.bDone && Elapsed >= St.T) { St.bDone = true; SetSuitByName(St.Suit, TEXT("-WHSuitScript")); }
	if (PC)
	{
		if (bReleaseT) { PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::T, IE_Released, 0.f)); bReleaseT = false; }
		else if (NextKey < KeyScript.Num() && Elapsed >= KeyScript[NextKey])
		{
			PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::T, IE_Pressed, 1.f));   // the real key path: PlayerInput -> IsInputKeyDown below
			bReleaseT = true; ++NextKey;
			UE_LOG(LogWebHomage, Display, TEXT("WH_SUIT injected T press t=%.3f frame=%llu"), Elapsed, GFrameCounter);
		}
		if (!W->IsPaused())
		{
			const bool bT = PC->IsInputKeyDown(EKeys::T);
			const bool bPad = PC->IsInputKeyDown(EKeys::Gamepad_DPad_Up);
			// (macOS reports the GLOBAL modifier state: a Shift the owner holds in another game reached the first round-11 pawn run; a scripted run ignores modifiers)
			const bool bShift = KeyScript.Num() == 0 && (PC->IsInputKeyDown(EKeys::LeftShift) || PC->IsInputKeyDown(EKeys::RightShift));
			const bool bLB = PC->IsInputKeyDown(EKeys::Gamepad_LeftShoulder);
			if (bT && !bPrevT) Cycle(bShift ? -1 : +1, bShift ? TEXT("key Shift+T") : TEXT("key T"));
			if (bPad && !bPrevPad) Cycle(bLB ? -1 : +1, bLB ? TEXT("pad LB+D-pad Up") : TEXT("pad D-pad Up"));
			bPrevT = bT; bPrevPad = bPad;
		}
	}
	if (CheckFrames >= 0 && --CheckFrames < 0 && Suits.IsValidIndex(CheckIndex))   // two frames after a swap: is everything resident?
	{
		TArray<UTexture*> Tex; Suits[CheckIndex].Material->GetUsedTextures(Tex);
		int32 NTex = 0, NRes = 0;
		for (UTexture* T : Tex) if (UTexture2D* T2 = Cast<UTexture2D>(T)) { ++NTex; if (T2->IsFullyStreamedIn()) ++NRes; }
		UE_LOG(LogWebHomage, Display, TEXT("WH_SUIT swap_done %d %s wall_ms=%.1f frames=%llu textures_resident=%d/%d"), CheckIndex, *Suits[CheckIndex].Id.ToString(),
			(FPlatformTime::Seconds() - CheckWall0) * 1000.0, GFrameCounter - CheckFrame0, NRes, NTex);
		CheckIndex = -1;
	}
}

namespace WHHeroSuits
{
	int32 Count() { const UWHHeroSuitSubsystem* S = GLive.Get(); return S ? S->Count() : 0; }
	int32 Current() { const UWHHeroSuitSubsystem* S = GLive.Get(); return S ? S->Current() : 0; }
	FText Name(int32 I) { const UWHHeroSuitSubsystem* S = GLive.Get(); return S ? S->NameOf(I) : FText::GetEmpty(); }
	void Set(int32 I, const TCHAR* Why) { if (UWHHeroSuitSubsystem* S = GLive.Get()) S->SetSuit(I, Why); }
}
