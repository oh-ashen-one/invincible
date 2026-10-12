// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// MPC_City NightK (0 day .. 1 night) as every night-aware system reads it (AWHCityLights, the hero fill, the crowd fill).
#pragma once

#include "CoreMinimal.h"
#include "Engine/World.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"

inline float WHReadNightK(UWorld* World)
{
	static TWeakObjectPtr<UMaterialParameterCollection> Mpc;
	if (!World) return 0.f;
	if (!Mpc.IsValid()) Mpc = LoadObject<UMaterialParameterCollection>(nullptr, TEXT("/Game/City/Materials/MPC_City.MPC_City"));
	return Mpc.IsValid() ? FMath::Clamp(UKismetMaterialLibrary::GetScalarParameterValue(World, Mpc.Get(), TEXT("NightK")), 0.f, 1.f) : 0.f;
}
