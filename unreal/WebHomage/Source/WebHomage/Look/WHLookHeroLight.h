// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// P4 Look: night rim + fill lights that follow the player's pawn (the hero), on lighting channel 1 only, so the hero stays
// readable in dark street canyons without lighting the world around it. Placed in the night rig level by Scripts/build_look.py.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WHLookHeroLight.generated.h"

class USpotLightComponent;
class UPointLightComponent;

UCLASS()
class WEBHOMAGE_API AWHLookHeroLight : public AActor
{
	GENERATED_BODY()
public:
	AWHLookHeroLight();
	virtual void Tick(float Dt) override;

	/** Cool rim from behind and above (relative to the view camera). Candela. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Look") TObjectPtr<USpotLightComponent> Rim;
	/** Warm-neutral fill from the camera side. Candela. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Look") TObjectPtr<UPointLightComponent> Fill;
	/** Low top light (sky glow on the shoulders). Candela. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Look") TObjectPtr<UPointLightComponent> Top;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Look") float RimIntensity = 900.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Look") float FillIntensity = 380.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Look") float TopIntensity = 180.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Look") FLinearColor RimColor = FLinearColor(0.55f, 0.72f, 1.0f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Look") FLinearColor FillColor = FLinearColor(1.0f, 0.86f, 0.7f);
	/** Distances in cm from the hero centre. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Look") float FillDistance = 320.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Look") float RimDistance = 380.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Look") float RimHeight = 260.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Look") float FillHeight = 90.f;

	/** AWHCityLights drives the fill / top lights from the author's area ambient (never called when no AWHCityLights exists). */
	void SetAmbientDrive(const FLinearColor& NewFillColor, float NewFillIntensity, float NewTopIntensity);
	float GetBaseFillIntensity() const { return bBaseCaptured ? BaseFillIntensity : FillIntensity; }
	FLinearColor GetBaseFillColor() const { return bBaseCaptured ? BaseFillColor : FillColor; }

private:
	bool bBaseCaptured = false;
	float BaseFillIntensity = 0.f;
	FLinearColor BaseFillColor = FLinearColor::White;
	bool bLightsInit = false;
	TWeakObjectPtr<APawn> LitPawn;
	void SetPawnChannels(APawn* P);
};
