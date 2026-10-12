// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// Piece P5 (combat): animation.
//  * UWHCombatHeroAnim — the traversal hero's anim instance (P3's UWebTravAnimInstance, unchanged) with the combat clip stack
//    blended on top (port of poselayer.js: combat clips over the traversal animator's output). Installed by AWHCombatHero.
//  * UWHEnemyAnim — native anim instance for the street thugs (P2 meshes on the hero skeleton): a clip stack with mixer-style
//    cross-fades (crime actors' play()), plus the procedural layer of enemy.js late(): hit flinch (spine / head snap) and the
//    gunman's aim pitch.
// Both pin the hips' horizontal translation (clips play in place; the owner moves the body / applies root motion).
#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "Traversal/Anim/WebTravAnimInstance.h"
#include "Combat/WHClipStack.h"
#include "WHCombatAnim.generated.h"

/** Procedural additive values (radians). */
struct FWHProcLayer
{
	float Flinch = 0.f;      // 0..1 spine / head snap back
	float FlinchDir = 1.f;   // head tilt side
	float AimPitch = 0.f;    // + = chest pitched up (gunman aiming at a hero above)
};

namespace WHCmbAnim
{
	/** Blend clip samples over Output (which already holds the base pose). bFirstFull: the first sample replaces the base. */
	void ApplySamples(FAnimInstanceProxy& Proxy, FPoseContext& Output, const TArray<FWHClipSample>& Samples, bool bFirstFull);
	/** Flinch / aim pitch on spine2 + head in component space. */
	void ApplyProc(FPoseContext& Output, const FWHProcLayer& P);
}

// ------------------------------------------------------------------------------------------------ hero
struct FWHCombatHeroProxy : public FWebTravAnimProxy
{
	FWHCombatHeroProxy() = default;
	explicit FWHCombatHeroProxy(UAnimInstance* Inst) : FWebTravAnimProxy(Inst) {}
	virtual void PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds) override;
	virtual bool Evaluate(FPoseContext& Output) override;
	TArray<FWHClipSample> Samples;
};

UCLASS(Transient, NotBlueprintable)
class WEBHOMAGE_API UWHCombatHeroAnim : public UWebTravAnimInstance
{
	GENERATED_BODY()
public:
	/** Combat clip by browser name (e.g. punch1), from the hero clip folder (UWebTravAnimInstance::ClipRoot). */
	UAnimSequence* CombatClip(FName Name);
	/** Set by AWHCombatHero every frame (game thread, before the mesh ticks). */
	void SetCombatSamples(const TArray<FWHClipSample>& In) { Samples = In; }
	TArray<FWHClipSample> Samples;

protected:
	virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override { return new FWHCombatHeroProxy(this); }
	UPROPERTY(Transient) TMap<FName, TObjectPtr<UAnimSequence>> CClips;
};

// ------------------------------------------------------------------------------------------------ enemy
struct FWHEnemyProxy : public FAnimInstanceProxy
{
	FWHEnemyProxy() = default;
	explicit FWHEnemyProxy(UAnimInstance* Inst) : FAnimInstanceProxy(Inst) {}
	virtual void PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds) override;
	virtual bool Evaluate(FPoseContext& Output) override;
	TArray<FWHClipSample> Samples;
	FWHProcLayer Proc;
};

UCLASS(Transient, NotBlueprintable)
class WEBHOMAGE_API UWHEnemyAnim : public UAnimInstance
{
	GENERATED_BODY()
public:
	void SetFrame(const TArray<FWHClipSample>& In, const FWHProcLayer& P) { Samples = In; Proc = P; }
	TArray<FWHClipSample> Samples;
	FWHProcLayer Proc;
protected:
	virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override { return new FWHEnemyProxy(this); }
	virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy) override { delete InProxy; }
};
