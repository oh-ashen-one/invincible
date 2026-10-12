// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// Piece P5 (combat): the combat hero pawn = P3's traversal hero (AWebTravCharacter, UNCHANGED) + combat.
// Integration without touching P3's files (see docs/night1/combat/HANDOFF.md, "P3 changes"):
//  * traversal still runs first every frame (its own input, camera, body); the combat director ticks after it and, while a
//    combat move is active, places the body through the component's public Teleport / SetVelocityM and re-places the actor;
//  * the mesh's anim instance is UWHCombatHeroAnim (a subclass of P3's UWebTravAnimInstance): the traversal animation is
//    evaluated unchanged and the combat clip stack is blended over it;
//  * combat keys are bound here (LMB attack / hold = launcher, F web shooter, E web strike, Q finisher, Z heal, R throw,
//    C / Ctrl dodge). Traversal keeps its own bindings (E zip, Q boost, C drop, F trick) — combat cannot swallow them yet.
#pragma once

#include "CoreMinimal.h"
#include "Traversal/WebTravCharacter.h"
#include "WHCombatHero.generated.h"

class AWHCombatDirector;
class UCameraComponent;

UCLASS(config=Game)
class WEBHOMAGE_API AWHCombatHero : public AWebTravCharacter
{
	GENERATED_BODY()

public:
	AWHCombatHero();
	UCameraComponent* Camera() const { return FollowCamera; }
	AWHCombatDirector* Director() const { return Dir; }
	/** Hand bone (m, world). */
	FVector HandM(bool bRight) const;
	FVector HeadM() const;

protected:
	virtual void BeginPlay() override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;

private:
	UPROPERTY(Transient) TObjectPtr<AWHCombatDirector> Dir;
	void KAttackDown(); void KAttackUp(); void KWeb(); void KStrike(); void KFinisher(); void KHeal(); void KThrow(); void KDodge();
};

/** Game mode for combat test maps: AWHCombatHero with the mouse-safe controller. */
UCLASS()
class WEBHOMAGE_API AWHCombatGameMode : public AGameModeBase
{
	GENERATED_BODY()
public:
	AWHCombatGameMode();
};
