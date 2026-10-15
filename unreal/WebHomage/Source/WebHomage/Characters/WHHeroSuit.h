// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// P2 Characters, first-pass piece G (round 11): the hero's ORIGINAL suits and the in-game swap.
//
// Content: /Game/Characters/Hero/Suits/DA_HeroSuits (a UWHHeroSuitSet) lists one material instance of M_Char_Suit per suit
// (tools/ue_char/suits/suits.json -> gen_suits.py -> Scripts/build_characters.py step 'skins'); the order is the cycle order.
// Swap: T (Shift+T = previous), gamepad D-pad Up (LB + D-pad Up = previous), the settings menu row "Hero suit", console `wh.Suit <n|id>`
// (no argument lists the suits), `wh.SuitNext`, `wh.SuitPrev`. The choice persists in GameUserSettings.ini [WebHomage.Settings]
// (HeroSuit = index, HeroSuitId = id; WHSettings.h). A swap is one SetMaterial on the SpiderSuit slot of the player pawn's mesh and of every
// other hero-suit mesh in the world (the capture stage's hero): the textures are NeverStream (or force-resident), so it takes one frame.
//
// Automation (never active in interactive play unless given):
//   -WHSuit=<n|id>              start with this suit (before the saved one)
//   -WHSuitScript=2.5:3,5:1     at game seconds t switch to suit n (same code path as the console command)
//   -WHSuitKeyScript=2,4.5      at game seconds t inject a T key press into the player controller (the real key path)
//   -WHSuitPersist              read / write the suit keys of GameUserSettings.ini even in an automated run (persistence test)
//
// 2026-10-15 (Invincible conversion, owner-approved): DA_HeroSuits names a DEFAULT suit (suits.json "default" -> DefaultSuitId; 'invincible').
// Start-up order: -WHSuit > the saved choice > the default. A default that is NEW to this install (GameUserSettings.ini
// [WebHomage.Settings] HeroSuitDefaultSeen != DefaultSuitId) wins once over the saved choice, so an owner whose ini still says
// HeroSuitId=tessera from the Spider-Man build starts in the new default; T / the menu / wh.Suit keep every other suit selectable and
// the choice persists as before. A suit with bTintLensMesh also re-materials the separate lens mesh of the playable pawn (the HeroDev
// proxy's 'HeroLenses' component, slots Lens / LensFrame); switching to a suit without it restores that mesh's own materials.
#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Subsystems/WorldSubsystem.h"
#include "WHHeroSuit.generated.h"

class UMaterialInterface;
class USkeletalMeshComponent;
class UTexture;

USTRUCT(BlueprintType)
struct WEBHOMAGE_API FWHHeroSuitEntry
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Suit") FName Id;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Suit") FString DisplayName;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Suit") TObjectPtr<UMaterialInterface> Material = nullptr;
	/** Optional: the lens material of this suit (slot 'Lens'); null keeps whatever the mesh has. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Suit") TObjectPtr<UMaterialInterface> LensMaterial = nullptr;
	/** Round 13, optional: the rim material of this suit's eyes (slot 'LensFrame'): a dark graphite rim on a mid / pale mask, a gunmetal one on a near-black mask; null keeps whatever the mesh has. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Suit") TObjectPtr<UMaterialInterface> FrameMaterial = nullptr;
	/** 2026-10-15: also apply LensMaterial / FrameMaterial to the playable pawn's separate lens mesh (slots 'Lens' / 'LensFrame'); false keeps that mesh's own lenses. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Suit") bool bTintLensMesh = false;
};

UCLASS(BlueprintType)
class WEBHOMAGE_API UWHHeroSuitSet : public UDataAsset
{
	GENERATED_BODY()
public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Suit") TArray<FWHHeroSuitEntry> Suits;
	/** 2026-10-15: the start-up suit when neither -WHSuit nor a saved choice applies (None = the first entry). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Suit") FName DefaultSuitId;
};

UCLASS()
class WEBHOMAGE_API UWHHeroSuitSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()
public:
	static constexpr const TCHAR* SetPath = TEXT("/Game/Characters/Hero/Suits/DA_HeroSuits.DA_HeroSuits");

	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	virtual bool IsTickableWhenPaused() const override { return true; }

	static UWHHeroSuitSubsystem* Get(const UObject* WorldContext);

	int32 Count() const { return Suits.Num(); }
	int32 Current() const { return Index; }
	FText NameOf(int32 I) const;
	/** Wraps I into range, applies it to every hero-suit mesh, persists it. Returns false when no suit set is loaded. */
	bool SetSuit(int32 I, const TCHAR* Why);
	bool SetSuitByName(const FString& NameOrIndex, const TCHAR* Why);
	void Cycle(int32 Dir, const TCHAR* Why);
	/** Console `wh.Suit` with no argument. */
	void LogList() const;

private:
	void CollectTargets(TArray<USkeletalMeshComponent*>& Out, bool bScanWorld) const;
	void ApplyToHeroes(bool bScanWorld);
	void Prewarm(int32 Around);
	bool IsHeroSuitMaterial(const UMaterialInterface* M) const;
	void InitialSync(class APlayerController* PC);
	void ParseCommandLine();
	/** 2026-10-15: index of Set->DefaultSuitId in Suits (0 when unset / missing). */
	int32 DefaultIndex() const;
	/** 2026-10-15: the player pawns' separate lens meshes (bTintLensMesh suits; restores the originals otherwise). */
	void ApplyLensMeshes();

	UPROPERTY(Transient) TObjectPtr<UWHHeroSuitSet> Set;
	TArray<FWHHeroSuitEntry> Suits;
	int32 Index = 0;
	bool bSynced = false;
	bool bPreSync = false;
	bool bPersist = false;
	int32 TicksWithPC = 0;
	double Elapsed = 0.0;
	double NextScan = 0.0;
	bool bPrevT = false, bPrevPad = false;
	FString CmdSuit;
	struct FScriptStep { double T; FString Suit; bool bDone = false; };
	TArray<FScriptStep> Script;
	TArray<double> KeyScript; int32 NextKey = 0; bool bReleaseT = false;
	FName DefaultId;
	struct FLensOrig { TWeakObjectPtr<UMaterialInterface> Lens, Frame; };
	TMap<TWeakObjectPtr<USkeletalMeshComponent>, FLensOrig> LensOrig;
	// swap latency probe
	int32 CheckFrames = -1; double CheckWall0 = 0.0; uint64 CheckFrame0 = 0; int32 CheckIndex = -1;
};

/** Plain accessors for the settings menu / other code (no world pointer needed). */
namespace WHHeroSuits
{
	WEBHOMAGE_API int32 Count();
	WEBHOMAGE_API int32 Current();
	WEBHOMAGE_API FText Name(int32 Index);
	WEBHOMAGE_API void Set(int32 Index, const TCHAR* Why);
}
