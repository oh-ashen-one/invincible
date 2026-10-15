// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
#include "Flight/WHCrowdBrain.h"

namespace
{
	inline uint32 CbHash(uint32 X) { X ^= X >> 16; X *= 0x7feb352dU; X ^= X >> 15; X *= 0x846ca68bU; X ^= X >> 16; return X; }
	inline float CbU01(uint32 Seed, uint32 Salt) { return (CbHash(Seed * 2654435761U + Salt) & 0xFFFFFF) / 16777216.f; }
	TSharedPtr<IWHCrowdBrain>& CbCustom() { static TSharedPtr<IWHCrowdBrain> B; return B; }
	const FWHRulesCrowdBrain& CbRules() { static FWHRulesCrowdBrain B; return B; }
}

const IWHCrowdBrain& WHCrowdBrain::Get()
{
	return CbCustom().IsValid() ? *CbCustom() : static_cast<const IWHCrowdBrain&>(CbRules());
}

void WHCrowdBrain::Register(TSharedPtr<IWHCrowdBrain> Brain)
{
	CbCustom() = Brain;
}

void FWHRulesCrowdBrain::Decide(const FWHCrowdAgentView& Agent, TArrayView<const FWHCrowdStimulus> Stimuli, const FWHCrowdHeroView& Hero, float Now, FWHCrowdDecision& Out) const
{
	Out = FWHCrowdDecision();
	const uint32 Bucket = uint32(FMath::Max(0.f, Now) * 2.f); // decisions vary with time but replay identically
	// strongest danger (flee) and strongest spectacle (look) in reach
	float BestDanger = 0.f, BestLook = 0.f, BestGawk = 0.f;
	const FWHCrowdStimulus* Danger = nullptr; const FWHCrowdStimulus* Look = nullptr; const FWHCrowdStimulus* Gawk = nullptr;
	for (const FWHCrowdStimulus& S : Stimuli)
	{
		const float D2 = FVector2D::Distance(FVector2D(Agent.PosCm), FVector2D(S.PosCm));
		if (D2 > S.RadiusCm) continue;
		const float W = S.Strength * (1.f - D2 / FMath::Max(1.f, S.RadiusCm));
		const float Age = Now - S.Time;
		switch (S.Type)
		{
		case EWHCrowdStimulus::Impact:
		case EWHCrowdStimulus::Emergency:
			if (W > BestDanger) { BestDanger = W; Danger = &S; }
			break;
		case EWHCrowdStimulus::Landing:
			if (Age < GawkAfter) { if (W > BestDanger) { BestDanger = W; Danger = &S; } }
			else if (W > BestGawk) { BestGawk = W; Gawk = &S; }
			break;
		case EWHCrowdStimulus::Flyover:
		case EWHCrowdStimulus::SonicBoom:
			if (W > BestLook) { BestLook = W; Look = &S; }
			break;
		}
	}
	if (Danger)
	{
		const FVector2D Away = FVector2D(Agent.PosCm - Danger->PosCm);
		const FVector2D AwayN = Away.SizeSquared() > 1.f ? Away.GetSafeNormal() : Agent.WalkDir;
		// flee along the sidewalk (people do not run into the buildings): the walking direction or its reverse, whichever leads away
		const FVector2D Along = FVector2D::DotProduct(Agent.WalkDir, AwayN) >= 0.f ? Agent.WalkDir : -Agent.WalkDir;
		const float D2 = FVector2D::Distance(FVector2D(Agent.PosCm), FVector2D(Danger->PosCm));
		const bool bBrace = Danger->Type == EWHCrowdStimulus::Impact && Danger->Strength > 0.7f && D2 < Danger->RadiusCm * CowerRadiusK
			&& Agent.Current != EWHCrowdAction::Cower && Agent.Current != EWHCrowdAction::Flee;
		if (bBrace)
		{
			Out.Action = EWHCrowdAction::Cower; Out.Hold = 0.45f + 0.4f * CbU01(Agent.Seed, Bucket + 11);
			Out.LookAtCm = Danger->PosCm;
			return;
		}
		Out.Action = EWHCrowdAction::Flee;
		Out.FleeDir = (Along * 0.85f + AwayN * 0.15f).GetSafeNormal();
		Out.SpeedMul = FMath::Lerp(RunMulMin, RunMulMax, CbU01(Agent.Seed, Bucket + 23));
		Out.Hold = FMath::Lerp(FleeHoldMin, FleeHoldMax, CbU01(Agent.Seed, Bucket + 37));
		Out.LookAtCm = Danger->PosCm;
		return;
	}
	if (Look)
	{
		Out.Action = EWHCrowdAction::LookUp;
		Out.LookAtCm = Hero.bValid ? Hero.PosCm : Look->PosCm;
		Out.Hold = FMath::Lerp(LookHoldMin, LookHoldMax, CbU01(Agent.Seed, Bucket + 51));
		return;
	}
	if (Gawk)
	{
		Out.Action = EWHCrowdAction::Gawk;
		Out.LookAtCm = Hero.bValid && !Hero.bFlying ? Hero.PosCm : Gawk->PosCm;
		Out.Hold = GawkHold * (0.8f + 0.4f * CbU01(Agent.Seed, Bucket + 67));
		return;
	}
	Out.Action = EWHCrowdAction::Walk;
	Out.Hold = 0.5f;
}
