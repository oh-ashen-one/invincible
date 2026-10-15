// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
#include "Flight/WHFlightWorld.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "WebHomage.h"

UWHFlightWorldSubsystem* UWHFlightWorldSubsystem::Get(const UObject* WorldContext)
{
	const UWorld* W = WorldContext ? GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::ReturnNull) : nullptr;
	return W ? W->GetSubsystem<UWHFlightWorldSubsystem>() : nullptr;
}

void UWHFlightWorldSubsystem::PushStimulus(const FWHCrowdStimulus& S)
{
	// bounded: the crowd reads every live stimulus per walker decision; 64 is far above what one hero produces in 4 s
	if (Stimuli.Num() >= 64) Stimuli.RemoveAt(0, 1, EAllowShrinking::No);
	Stimuli.Add(S);
}

void UWHFlightWorldSubsystem::PushStimulus(EWHCrowdStimulus Type, const FVector& PosCm, float RadiusCm, float Strength, float Life, const FVector& VelCm)
{
	FWHCrowdStimulus S;
	S.Type = Type; S.PosCm = PosCm; S.RadiusCm = RadiusCm; S.Strength = Strength; S.Life = Life; S.VelCm = VelCm;
	S.Time = GetWorld() ? float(GetWorld()->GetTimeSeconds()) : 0.f;
	PushStimulus(S);
}

const TArray<FWHCrowdStimulus>& UWHFlightWorldSubsystem::ActiveStimuli(float Now)
{
	Stimuli.RemoveAll([Now](const FWHCrowdStimulus& S) { return Now - S.Time > S.Life; });
	return Stimuli;
}

void UWHFlightWorldSubsystem::AddCollateral(float USD, const TCHAR* Why)
{
	CollateralUSD += FMath::Max(0.f, USD);
	UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT collateral +$%.0f (%s) total $%.0f"), USD, Why, CollateralUSD);
}
