// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
// P6 City life: a camera that walks a straight street-level path (for the 1080p60 street clip and other life captures).
#pragma once

#include "CoreMinimal.h"
#include "Camera/CameraActor.h"
#include "WHLifeCamRig.generated.h"

UCLASS()
class WEBHOMAGE_API AWHLifeCamRig : public ACameraActor
{
	GENERATED_BODY()
public:
	AWHLifeCamRig();
	virtual void BeginPlay() override;
	virtual void Tick(float Dt) override;

	/** Start / end of the path (cm). The camera looks along the path (plus LookOffset) at the given eye height above Start.Z. */
	UPROPERTY(EditAnywhere, Category="Rig") FVector Start = FVector::ZeroVector;
	UPROPERTY(EditAnywhere, Category="Rig") FVector End = FVector(0, -6000, 0);
	UPROPERTY(EditAnywhere, Category="Rig") float Duration = 20.f;
	UPROPERTY(EditAnywhere, Category="Rig") float EyeHeight = 170.f;
	UPROPERTY(EditAnywhere, Category="Rig") float LookAheadCm = 4000.f;
	UPROPERTY(EditAnywhere, Category="Rig") float LookHeightDelta = 250.f;
	UPROPERTY(EditAnywhere, Category="Rig") float YawSwayDeg = 6.f;
	UPROPERTY(EditAnywhere, Category="Rig") bool bLoop = true;
	UPROPERTY(EditAnywhere, Category="Rig") float FovDegrees = 70.f;
	/** Aim at a fixed world point (cm) from wherever the rig is (swing-height and fixed signal shots); no sway or head-bob. */
	UPROPERTY(EditAnywhere, Category="Rig") bool bAimAtTarget = false;
	UPROPERTY(EditAnywhere, Category="Rig") FVector AimTarget = FVector::ZeroVector;
	/** Aim at a point this far AHEAD of the rig along its path and AimAheadHeight above the ground at Start.Z (a swing camera: constant downward pitch instead of a fixed world target);
	 *  0 = off (bAimAtTarget / look-ahead as before). Command line: -WHLifeAimAhead=<ahead m>:<aim height m>. */
	UPROPERTY(EditAnywhere, Category="Rig") float AimAheadCm = 0.f;
	UPROPERTY(EditAnywhere, Category="Rig") float AimAheadHeightCm = 0.f;
	/** The rig waits at Start for this many seconds (warm-up: lighting / TSR settle) before moving; the capture script trims these frames. */
	UPROPERTY(EditAnywhere, Category="Rig") float HoldSeconds = 0.f;
private:
	float T = 0.f;
	void Place();
};
