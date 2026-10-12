// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
// P6 City life: measurement probe. At the requested game times it logs how many vehicles / people are inside the player's camera
// frustum (projected, NOT occlusion tested; with a minimum apparent size so specks do not count), and it watches the planted feet of
// the nearest walkers to measure foot sliding. Lines start with WH_LIFE_ so capture scripts can grep them.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WHLifeProbe.generated.h"

class AWHLifeTraffic;
class AWHLifeCrowd;
class USkeletalMeshComponent;

UCLASS()
class WEBHOMAGE_API AWHLifeProbe : public AActor
{
	GENERATED_BODY()
public:
	AWHLifeProbe();
	virtual void BeginPlay() override;
	virtual void Tick(float Dt) override;

	UPROPERTY(EditAnywhere, Category="Probe") TObjectPtr<AWHLifeTraffic> Traffic;
	UPROPERTY(EditAnywhere, Category="Probe") TObjectPtr<AWHLifeCrowd> Crowd;
	/** Game seconds at which a frame report is logged. */
	UPROPERTY(EditAnywhere, Category="Probe") TArray<float> ReportAt;
	/** Foot-slide watch window (game seconds). */
	UPROPERTY(EditAnywhere, Category="Probe") float FootFrom = 0.f;
	UPROPERTY(EditAnywhere, Category="Probe") float FootTo = 0.f;
	UPROPERTY(EditAnywhere, Category="Probe") int32 FootWalkers = 14;
	/** Minimum apparent height in pixels for a vehicle / person to count. */
	UPROPERTY(EditAnywhere, Category="Probe") float MinCarPx = 22.f;
	UPROPERTY(EditAnywhere, Category="Probe") float MinPersonPx = 28.f;
	/** Periodic sampler (game seconds): every SampleEvery s between SampleFrom and SampleTo one WH_LIFE_SAMPLE line (frustum counts, lane motion, box stops, queue links). */
	UPROPERTY(EditAnywhere, Category="Probe") float SampleEvery = 0.f;
	UPROPERTY(EditAnywhere, Category="Probe") float SampleFrom = 0.f;
	UPROPERTY(EditAnywhere, Category="Probe") float SampleTo = 0.f;
	/** Lane link file ids whose queue (cars on the link, stopped, distance of the front car to the stop line) is logged at every sample. */
	UPROPERTY(EditAnywhere, Category="Probe") TArray<int32> QueueLinks;

private:
	float T = 0.f;
	TSet<int32> Done;
	// foot watch
	struct FFoot { TWeakObjectPtr<USkeletalMeshComponent> Comp; FVector PrevL = FVector::ZeroVector, PrevR = FVector::ZeroVector; bool bHave = false; float RootSpeed = 0.f;
		bool bContact[2] = { false, false }; FVector Start[2] = { FVector::ZeroVector, FVector::ZeroVector }, Last[2] = { FVector::ZeroVector, FVector::ZeroVector }; float ContactT[2] = { 0.f, 0.f }; TArray<float> Disp; };
	TArray<FFoot> Feet;
	FString FootCsv;
	bool bFeetInit = false, bFeetDone = false;
	void Report(int32 Idx);
	void Sample();
	float NextSample = 0.f;
	void FootStep(float Dt);
	void FootReport();
};
