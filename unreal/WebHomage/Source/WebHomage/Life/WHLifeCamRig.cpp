// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
#include "Life/WHLifeCamRig.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/PlayerController.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

AWHLifeCamRig::AWHLifeCamRig()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PrePhysics;
}

void AWHLifeCamRig::BeginPlay()
{
	Super::BeginPlay();
	// -WHLifeRig=<start x>:<start z>:<end x>:<end z>:<eye cm>:<aim x>:<aim y>:<aim z>:<fov>[:<hold>[:<duration>]]  (browser metres; y up) overrides the rig without a map rebuild
	FString RigArg;
	if (FParse::Value(FCommandLine::Get(), TEXT("WHLifeRig="), RigArg))
	{
		TArray<FString> P; RigArg.ParseIntoArray(P, TEXT(":"), true);
		if (P.Num() >= 9)
		{
			const float G = Start.Z;   // ground height (cm) stays
			Start = FVector(FCString::Atof(*P[0]) * 100.f, FCString::Atof(*P[1]) * 100.f, G); End = FVector(FCString::Atof(*P[2]) * 100.f, FCString::Atof(*P[3]) * 100.f, G);
			EyeHeight = FCString::Atof(*P[4]); bAimAtTarget = true; AimTarget = FVector(FCString::Atof(*P[5]) * 100.f, FCString::Atof(*P[7]) * 100.f, FCString::Atof(*P[6]) * 100.f);
			FovDegrees = FCString::Atof(*P[8]);
			if (P.Num() >= 10) HoldSeconds = FCString::Atof(*P[9]);
			if (P.Num() >= 11) Duration = FCString::Atof(*P[10]);
		}
	}
	FString AimArg;
	if (FParse::Value(FCommandLine::Get(), TEXT("WHLifeAimAhead="), AimArg))
	{
		TArray<FString> P; AimArg.ParseIntoArray(P, TEXT(":"), true);
		if (P.Num() >= 2) { AimAheadCm = FCString::Atof(*P[0]) * 100.f; AimAheadHeightCm = FCString::Atof(*P[1]) * 100.f; }
	}
	if (GetCameraComponent()) { GetCameraComponent()->SetFieldOfView(FovDegrees); GetCameraComponent()->bConstrainAspectRatio = false; }
	T = 0.f; Place();
	if (UWorld* W = GetWorld()) if (APlayerController* PC = W->GetFirstPlayerController()) PC->SetViewTarget(this); // the game mode's pawn is not the view
}

void AWHLifeCamRig::Place()
{
	const float Tm = FMath::Max(0.f, T - HoldSeconds);
	const float A = Duration > 0.f ? (bLoop ? FMath::Fmod(Tm, Duration) : FMath::Min(Tm, Duration)) / Duration : 0.f;
	FVector P = FMath::Lerp(Start, End, A); P.Z = Start.Z + EyeHeight;
	FVector Dir = (End - Start); Dir.Z = 0.f; Dir = Dir.GetSafeNormal();
	const float Sway = FMath::Sin(Tm * 0.55f) * YawSwayDeg;
	FRotator R = Dir.Rotation(); R.Yaw += Sway; R.Pitch = FMath::RadiansToDegrees(FMath::Atan2(LookHeightDelta, LookAheadCm));
	if (AimAheadCm > 0.f) { const FVector Aim = FVector(P.X, P.Y, Start.Z + AimAheadHeightCm) + Dir * AimAheadCm; SetActorLocationAndRotation(P, (Aim - P).Rotation()); return; }
	if (bAimAtTarget) { SetActorLocationAndRotation(P, (AimTarget - P).Rotation()); return; }
	// gentle head-bob
	P.Z += FMath::Sin(Tm * 2.0f * PI * 1.7f) * 1.5f;
	SetActorLocationAndRotation(P, R);
}

void AWHLifeCamRig::Tick(float Dt)
{
	Super::Tick(Dt);
	T += Dt; Place();
}
