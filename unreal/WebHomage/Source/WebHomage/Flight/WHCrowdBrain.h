// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
// Invincible flight conversion (owner request 2026-10-15): the crowd's DECISION HOOK, kept isolated from the crowd simulation so a
// different brain (the owner's Jev crowd brain from Markhor Meadow) can replace the rules here without touching AWHLifeCrowd:
// implement IWHCrowdBrain and call WHCrowdBrain::Register(MakeShared<FYourBrain>()). Plain C++ (no UObject), deterministic
// (every random choice comes from the agent's own seed), called at most a few times per second per reacting walker.
#pragma once

#include "CoreMinimal.h"
#include "Flight/WHFlightWorld.h"

enum class EWHCrowdAction : uint8
{
	Walk,    // carry on along the sidewalk graph
	LookUp,  // stop and look at the hero overhead
	Flee,    // run away along FleeDir
	Cower,   // stop dead (brace) for Hold s
	Gawk,    // stand and stare at LookAtCm (after the danger has passed)
};

struct FWHCrowdAgentView
{
	FVector PosCm = FVector::ZeroVector;      // feet
	FVector2D WalkDir = FVector2D(1, 0);      // the sidewalk direction the agent is walking (unit, world XY)
	EWHCrowdAction Current = EWHCrowdAction::Walk;
	float ActionT = 0.f;                      // s in the current action
	uint32 Seed = 1;
};

struct FWHCrowdHeroView
{
	FVector PosCm = FVector::ZeroVector;
	FVector VelCm = FVector::ZeroVector;
	bool bFlying = false;
	bool bValid = false;
};

struct FWHCrowdDecision
{
	EWHCrowdAction Action = EWHCrowdAction::Walk;
	FVector2D FleeDir = FVector2D::ZeroVector; // unit, world XY
	float SpeedMul = 1.f;                      // x the agent's walking speed
	FVector LookAtCm = FVector::ZeroVector;
	float Hold = 0.f;                          // s before the agent asks the brain again
};

class WEBHOMAGE_API IWHCrowdBrain
{
public:
	virtual ~IWHCrowdBrain() {}
	virtual const TCHAR* Name() const = 0;
	/** Now = world time (s) the stimuli are stamped against. */
	virtual void Decide(const FWHCrowdAgentView& Agent, TArrayView<const FWHCrowdStimulus> Stimuli, const FWHCrowdHeroView& Hero, float Now, FWHCrowdDecision& Out) const = 0;
};

/** The rules brain (default): flee impacts / landings / emergencies, brace when very close, look up at flyovers and booms, gawk after. */
class WEBHOMAGE_API FWHRulesCrowdBrain : public IWHCrowdBrain
{
public:
	virtual const TCHAR* Name() const override { return TEXT("rules"); }
	virtual void Decide(const FWHCrowdAgentView& Agent, TArrayView<const FWHCrowdStimulus> Stimuli, const FWHCrowdHeroView& Hero, float Now, FWHCrowdDecision& Out) const override;
	float RunMulMin = 2.8f, RunMulMax = 3.8f;    // flee speed x walk speed
	float FleeHoldMin = 3.f, FleeHoldMax = 6.f;
	float CowerRadiusK = 0.25f;                  // within this share of an impact's radius a strong impact braces first
	float LookHoldMin = 1.4f, LookHoldMax = 2.6f;
	float GawkAfter = 1.5f, GawkHold = 3.f;      // a landing older than GawkAfter s draws a GawkHold s stare
};

namespace WHCrowdBrain
{
	/** The active brain (the rules brain unless another was registered). */
	WEBHOMAGE_API const IWHCrowdBrain& Get();
	/** Swap in another brain (null restores the rules). */
	WEBHOMAGE_API void Register(TSharedPtr<IWHCrowdBrain> Brain);
}
