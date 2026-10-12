// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Look/WHLookHeroLight.h"
#include "Components/SpotLightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Camera/PlayerCameraManager.h"
#include "Kismet/GameplayStatics.h"

static void InitHeroLight(ULocalLightComponent* L, const FLinearColor& C, float Candela, float Radius)
{
	L->SetMobility(EComponentMobility::Movable);
	L->SetLightColor(C);
	L->SetIntensityUnits(ELightUnits::Candelas);
	L->SetIntensity(Candela);
	L->SetCastShadows(false);
	L->SetVolumetricScatteringIntensity(0.f);
	L->SetIndirectLightingIntensity(0.f); // no GI from the hero lights: they must not light the street
	L->SetLightingChannels(false, true, false); // channel 1 only: the pawn's meshes are on 0 + 1, the world on 0
	L->SetAttenuationRadius(Radius);
	if (UPointLightComponent* PL = Cast<UPointLightComponent>(L)) PL->SourceRadius = 15.f;
}

AWHLookHeroLight::AWHLookHeroLight()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PostUpdateWork;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	Rim = CreateDefaultSubobject<USpotLightComponent>(TEXT("Rim"));
	Fill = CreateDefaultSubobject<UPointLightComponent>(TEXT("Fill"));
	Top = CreateDefaultSubobject<UPointLightComponent>(TEXT("Top"));
	Rim->SetupAttachment(RootComponent); Fill->SetupAttachment(RootComponent); Top->SetupAttachment(RootComponent);
	Rim->SetOuterConeAngle(50.f); Rim->SetInnerConeAngle(20.f);
}

void AWHLookHeroLight::SetAmbientDrive(const FLinearColor& NewFillColor, float NewFillIntensity, float NewTopIntensity)
{
	if (!bBaseCaptured) { bBaseCaptured = true; BaseFillIntensity = FillIntensity; BaseFillColor = FillColor; }
	FillColor = NewFillColor; FillIntensity = NewFillIntensity; TopIntensity = NewTopIntensity;
	if (bLightsInit)
	{
		Fill->SetLightColor(FillColor); Fill->SetIntensity(FillIntensity);
		Top->SetIntensity(TopIntensity);
	}
}

void AWHLookHeroLight::SetPawnChannels(APawn* P)
{
	TInlineComponentArray<UPrimitiveComponent*> Prims; P->GetComponents(Prims);
	for (UPrimitiveComponent* C : Prims)
	{
		if (Cast<USkeletalMeshComponent>(C) || Cast<UStaticMeshComponent>(C)) C->SetLightingChannels(true, true, false);
	}
	LitPawn = P;
}

void AWHLookHeroLight::Tick(float Dt)
{
	Super::Tick(Dt);
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	APawn* P = PC ? PC->GetPawn() : nullptr;
	if (!P) return;
	if (LitPawn.Get() != P) SetPawnChannels(P);
	if (!bLightsInit)
	{
		bLightsInit = true;
		InitHeroLight(Rim, RimColor, RimIntensity, 1500.f); InitHeroLight(Fill, FillColor, FillIntensity, 1200.f); InitHeroLight(Top, FLinearColor(0.7f, 0.8f, 1.f), TopIntensity, 1000.f);
	}
	const FVector Hero = P->GetActorLocation() + FVector(0, 0, 40.f);
	FVector Cam = PC->PlayerCameraManager ? PC->PlayerCameraManager->GetCameraLocation() : Hero + FVector(-500, 0, 100);
	FVector ToCam = (Cam - Hero); ToCam.Z = 0; ToCam = ToCam.GetSafeNormal();
	if (ToCam.IsNearlyZero()) ToCam = FVector(-1, 0, 0);
	Fill->SetWorldLocation(Hero + ToCam * FillDistance + FVector(0, 0, FillHeight));
	const FVector RimPos = Hero - ToCam * RimDistance + FVector(0, 0, RimHeight);
	Rim->SetWorldLocation(RimPos);
	Rim->SetWorldRotation((Hero - RimPos).Rotation());
	Top->SetWorldLocation(Hero + FVector(0, 0, 320.f));
}
