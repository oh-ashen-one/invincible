// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
#include "Life/WHLifeProbe.h"
#include "Life/WHLifeTraffic.h"
#include "Life/WHLifeCrowd.h"
#include "Components/SkeletalMeshComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Math/RotationMatrix.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

DEFINE_LOG_CATEGORY_STATIC(LogWHLifeProbe, Log, All);

AWHLifeProbe::AWHLifeProbe()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PostUpdateWork;
	SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
}

void AWHLifeProbe::BeginPlay()
{
	Super::BeginPlay();
	// -WHLifeSample=<from>:<to>:<every>  -WHLifeQueue=<link id>,<link id>...
	FString S;
	if (FParse::Value(FCommandLine::Get(), TEXT("WHLifeSample="), S))
	{
		TArray<FString> P; S.ParseIntoArray(P, TEXT(":"), true);
		if (P.Num() >= 3) { SampleFrom = FCString::Atof(*P[0]); SampleTo = FCString::Atof(*P[1]); SampleEvery = FCString::Atof(*P[2]); }
	}
	if (FParse::Value(FCommandLine::Get(), TEXT("WHLifeFoot="), S))
	{
		TArray<FString> P; S.ParseIntoArray(P, TEXT(":"), true);
		if (P.Num() >= 2) { FootFrom = FCString::Atof(*P[0]); FootTo = FCString::Atof(*P[1]); }
	}
	if (FParse::Value(FCommandLine::Get(), TEXT("WHLifeQueue="), S, false))
	{
		TArray<FString> P; S.ParseIntoArray(P, TEXT(","), true);
		for (const FString& X : P) QueueLinks.Add(FCString::Atoi(*X));
	}
}

void AWHLifeProbe::Tick(float Dt)
{
	Super::Tick(Dt);
	T += Dt;
	for (int32 I = 0; I < ReportAt.Num(); ++I) if (!Done.Contains(I) && T >= ReportAt[I]) { Done.Add(I); Report(I); }
	if (SampleEvery > 0.f && T >= SampleFrom && T <= SampleTo + 0.001f) { if (NextSample < SampleFrom) NextSample = SampleFrom; if (T >= NextSample) { NextSample += SampleEvery; Sample(); } }
	if (FootTo > FootFrom && T >= FootFrom && T <= FootTo) FootStep(Dt);
	else if (bFeetInit && !bFeetDone && T > FootTo) { bFeetDone = true; FootReport(); }
}

void AWHLifeProbe::Report(int32 Idx)
{
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	if (!PC) return;
	int32 W = 0, H = 0; PC->GetViewportSize(W, H);
	const float Fov = PC->PlayerCameraManager ? PC->PlayerCameraManager->GetFOVAngle() : 90.f;
	FVector Eye; FRotator Rot; PC->GetPlayerViewPoint(Eye, Rot);
	const float Aspect = H > 0 ? (float)W / H : 1.78f;
	const float VFov = 2.f * FMath::Atan(FMath::Tan(FMath::DegreesToRadians(Fov) * 0.5f) / Aspect);
	const float FocalPx = (H * 0.5f) / FMath::Tan(VFov * 0.5f);
	FCollisionQueryParams Q(SCENE_QUERY_STAT(LifeProbe), true);
	if (PC->GetPawn()) Q.AddIgnoredActor(PC->GetPawn());
	// on screen + apparent height >= MinPx + (optional) a visibility ray from the camera reaches the point (city geometry blocks it)
	auto Vis = [&](const FVector& P, float HeightCm, float MinPx, bool bOcc) -> bool
	{
		FVector2D Sc; if (!PC->ProjectWorldLocationToScreen(P, Sc, false)) return false;
		if (Sc.X < 0 || Sc.Y < 0 || Sc.X > W || Sc.Y > H) return false;
		const float D = FVector::Dist(Eye, P); if (D < 50.f) return false;
		if (HeightCm * FocalPx / D < MinPx) return false;
		if (!bOcc) return true;
		FHitResult Hit; const bool bHit = GetWorld()->LineTraceSingleByChannel(Hit, Eye, P, ECC_Visibility, Q);
		if (bHit && Hit.Distance <= D - 60.f) { static int32 Logged = 0; if (Logged < 6) { ++Logged; UE_LOG(LogWHLifeProbe, Display, TEXT("WH_LIFE_OCC blocked at %.1f of %.1f m by %s / %s"), Hit.Distance / 100.f, D / 100.f, *GetNameSafe(Hit.GetActor()), *GetNameSafe(Hit.GetComponent())); } return false; }
		return true;
	};
	const float CarPx[2] = { MinCarPx, 2.f * MinCarPx }, PplPx[2] = { MinPersonPx, 2.f * MinPersonPx };
	int32 Mov[2] = {0, 0}, Par[2] = {0, 0}, ParTaxi[2] = {0, 0}, MovTaxi[2] = {0, 0}, MovProj = 0, ParProj = 0;
	if (Traffic)
	{
		TArray<FVector> M, P; TArray<int32> MT, PT; Traffic->GetPoints(M, MT, P, PT);
		for (int32 I = 0; I < M.Num(); ++I) { MovProj += Vis(M[I], 160.f, 0.f, false); for (int32 K = 0; K < 2; ++K) if (Vis(M[I], 160.f, CarPx[K], true)) { ++Mov[K]; MovTaxi[K] += MT[I] <= 3; } }
		for (int32 I = 0; I < P.Num(); ++I) { ParProj += Vis(P[I], 160.f, 0.f, false); for (int32 K = 0; K < 2; ++K) if (Vis(P[I], 160.f, CarPx[K], true)) { ++Par[K]; ParTaxi[K] += PT[I] <= 3; } }
	}
	int32 People[2] = {0, 0}, PplProj = 0; TSet<int32> Models[2];
	int32 HandL = 0, HandR = 0, HandNear = 0, HandNearL = 0, HandNearR = 0;   // people >= 20 px (a size a person can count by eye), unoccluded, left / right of the view axis; Near = within 80 m on the ground
	if (Crowd)
	{
		const FVector Rgt = FRotationMatrix(Rot).GetScaledAxis(EAxis::Y);
		TArray<FVector> Pos; TArray<int32> Mod; TArray<USkeletalMeshComponent*> Comps; TArray<float> Sp; Crowd->GetLive(Pos, Mod, Comps, Sp);
		for (int32 I = 0; I < Pos.Num(); ++I)
		{
			PplProj += Vis(Pos[I], 175.f, 0.f, false);
			for (int32 K = 0; K < 2; ++K) if (Vis(Pos[I], 175.f, PplPx[K], true)) { ++People[K]; Models[K].Add(Mod[I]); }
			if (Vis(Pos[I], 175.f, 20.f, true))
			{
				const bool bR = FVector::DotProduct(Pos[I] - Eye, Rgt) > 0.f; (bR ? HandR : HandL)++;
				if (FVector2D::Distance(FVector2D(Pos[I].X, Pos[I].Y), FVector2D(Eye.X, Eye.Y)) < 8000.f) { ++HandNear; (bR ? HandNearR : HandNearL)++; }
			}
		}
	}
	TMap<int32, int32> TwinMap; int32 Twins = 0;
	if (Crowd)
	{
		TArray<FVector> Pos; TArray<int32> Mod; TArray<USkeletalMeshComponent*> Comps; TArray<float> Sp; Crowd->GetLive(Pos, Mod, Comps, Sp);
		for (int32 I = 0; I < Pos.Num(); ++I) if (Vis(Pos[I], 175.f, PplPx[0], true)) { int32& N = TwinMap.FindOrAdd(Mod[I]); if (N++ > 0) ++Twins; }
	}
	UE_LOG(LogWHLifeProbe, Display, TEXT("WH_LIFE_FRAME t=%.1f res=%dx%d fov=%.0f cam=(%.1f,%.1f,%.1f)m | vehicles unoccluded >=%.0fpx: moving=%d (taxi %d) parked=%d (taxi %d) total=%d | >=%.0fpx: moving=%d parked=%d (taxi %d) total=%d | people unoccluded >=%.0fpx: %d (models %d, identical looks in frame %d) | >=%.0fpx: %d (models %d) | projected only (no size / occlusion test): vehicles moving=%d parked=%d people=%d | people >=20px unoccluded: %d (left of view axis %d, right %d; within 80 m %d: left %d right %d)"),
		T, W, H, Fov, Eye.X / 100.f, Eye.Y / 100.f, Eye.Z / 100.f, CarPx[0], Mov[0], MovTaxi[0], Par[0], ParTaxi[0], Mov[0] + Par[0], CarPx[1], Mov[1], Par[1], ParTaxi[1], Mov[1] + Par[1],
		PplPx[0], People[0], Models[0].Num(), Twins, PplPx[1], People[1], Models[1].Num(), MovProj, ParProj, PplProj, HandL + HandR, HandL, HandR, HandNear, HandNearL, HandNearR);
	if (Traffic) { UE_LOG(LogWHLifeProbe, Display, TEXT("WH_LIFE_TRAFFIC %s"), *Traffic->StatsString()); Traffic->DumpCars(FPaths::ProjectSavedDir() / FString::Printf(TEXT("Logs/life_cars_%d.csv"), Idx)); }
	if (Crowd) UE_LOG(LogWHLifeProbe, Display, TEXT("WH_LIFE_CROWD %s"), *Crowd->StatsString());
}

void AWHLifeProbe::FootStep(float Dt)
{
	if (!Crowd || Dt <= 0.f) return;
	if (!bFeetInit)
	{
		bFeetInit = true;
		APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
		FVector Eye = FVector::ZeroVector; FRotator Rot; if (PC) PC->GetPlayerViewPoint(Eye, Rot);
		TArray<FVector> Pos; TArray<int32> Mod; TArray<USkeletalMeshComponent*> Comps; TArray<float> Sp; Crowd->GetLive(Pos, Mod, Comps, Sp);
		TArray<TPair<float, int32>> Order; for (int32 I = 0; I < Pos.Num(); ++I) if (Sp[I] > 0.3f) Order.Add(TPair<float, int32>(FVector::Dist(Eye, Pos[I]), I));
		Order.Sort([](const TPair<float, int32>& A, const TPair<float, int32>& B) { return A.Key < B.Key; });
		for (int32 K = 0; K < Order.Num() && K < FootWalkers; ++K) { FFoot F; F.Comp = Comps[Order[K].Value]; F.RootSpeed = Sp[Order[K].Value]; Feet.Add(F); }
		UE_LOG(LogWHLifeProbe, Display, TEXT("WH_LIFE_FOOT watching %d walkers"), Feet.Num());
	}
	for (FFoot& F : Feet)
	{
		USkeletalMeshComponent* C = F.Comp.Get(); if (!C || !C->IsVisible()) continue;
		const FVector L = C->GetSocketLocation(TEXT("footL")), R = C->GetSocketLocation(TEXT("footR"));
		// stance phase = the ankle bone is within 12 cm of its floor height (rest height ~8 cm); while it is planted its WORLD position should barely move
		// (only the heel-to-toe roll of the ankle, ~20-25 cm); a slid foot travels a large part of the stride (~50+ cm)
		const float Floor = C->GetComponentLocation().Z;
		const FVector Ft[2] = { L, R };
		for (int32 K = 0; K < 2; ++K)
		{
			const bool bOn = Ft[K].Z < Floor + 10.5f;
			if (bOn && !F.bContact[K]) { F.bContact[K] = true; F.Start[K] = Ft[K]; F.ContactT[K] = 0.f; }
			if (bOn) { F.Last[K] = Ft[K]; F.ContactT[K] += Dt; }
			if (!bOn && F.bContact[K])
			{
				F.bContact[K] = false;
				if (F.ContactT[K] >= 0.12f) F.Disp.Add(FVector2D(F.Last[K].X - F.Start[K].X, F.Last[K].Y - F.Start[K].Y).Size());
			}
		}
		F.PrevL = L; F.PrevR = R; F.bHave = true;
		const FVector O = C->GetComponentLocation();
		FootCsv += FString::Printf(TEXT("%.3f,%d,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f\n"), T, (int32)(&F - Feet.GetData()), O.X, O.Y, O.Z, L.X, L.Y, L.Z, R.X, R.Y, R.Z, F.RootSpeed);
	}
}

void AWHLifeProbe::FootReport()
{
	FFileHelper::SaveStringToFile(FString(TEXT("t,walker,ox,oy,oz,lx,ly,lz,rx,ry,rz,rootspeed\n")) + FootCsv, *(FPaths::ProjectSavedDir() / TEXT("Logs/life_feet.csv")));
	TArray<float> All; int32 Walkers = 0, Slid = 0;
	for (const FFoot& F : Feet) { if (F.Disp.Num() > 2) { ++Walkers; All.Append(F.Disp); } }
	for (float D : All) if (D > 45.f) ++Slid;
	All.Sort();
	const float Med = All.Num() ? All[All.Num() / 2] : 0.f, P95 = All.Num() ? All[FMath::Min(All.Num() - 1, (int32)(All.Num() * 0.95f))] : 0.f, Mx = All.Num() ? All.Last() : 0.f;
	UE_LOG(LogWHLifeProbe, Display, TEXT("WH_LIFE_FOOT walkers=%d stance phases=%d | ankle world displacement during a planted stance (cm; ~20-25 = heel-toe roll, a stride is ~55) median %.1f p95 %.1f max %.1f | stances > 45 cm (sliding) %d (%.1f %%)"),
		Walkers, All.Num(), Med, P95, Mx, Slid, All.Num() ? 100.f * Slid / All.Num() : 0.f);
}

void AWHLifeProbe::Sample()
{
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	if (!PC) return;
	int32 W = 0, H = 0; PC->GetViewportSize(W, H);
	const float Fov = PC->PlayerCameraManager ? PC->PlayerCameraManager->GetFOVAngle() : 90.f;
	FVector Eye; FRotator Rot; PC->GetPlayerViewPoint(Eye, Rot);
	const float Aspect = H > 0 ? (float)W / H : 1.78f;
	const float VFov = 2.f * FMath::Atan(FMath::Tan(FMath::DegreesToRadians(Fov) * 0.5f) / Aspect);
	const float FocalPx = (H * 0.5f) / FMath::Tan(VFov * 0.5f);
	FCollisionQueryParams Q(SCENE_QUERY_STAT(LifeSample), true);
	if (PC->GetPawn()) Q.AddIgnoredActor(PC->GetPawn());
	auto Vis = [&](const FVector& P, float HeightCm, float MinPx) -> bool
	{
		FVector2D Sc; if (!PC->ProjectWorldLocationToScreen(P, Sc, false)) return false;
		if (Sc.X < 0 || Sc.Y < 0 || Sc.X > W || Sc.Y > H) return false;
		const float D = FVector::Dist(Eye, P); if (D < 50.f) return false;
		if (HeightCm * FocalPx / D < MinPx) return false;
		FHitResult Hit; return !(GetWorld()->LineTraceSingleByChannel(Hit, Eye, P, ECC_Visibility, Q) && Hit.Distance <= D - 60.f);
	};
	auto VisP = [&](const FVector& P, float HeightCm, float MinPx) -> bool
	{
		FVector2D Sc; if (!PC->ProjectWorldLocationToScreen(P, Sc, false)) return false;
		if (Sc.X < 0 || Sc.Y < 0 || Sc.X > W || Sc.Y > H) return false;
		const float D = FVector::Dist(Eye, P); return D >= 50.f && HeightCm * FocalPx / D >= MinPx;
	};
	int32 Mov = 0, MovFast = 0, Stopped = 0, Par = 0, Buses = 0; float NearestCar = 1e9f; TMap<int32, TPair<int32, int32>> Lanes;   // lane key -> (moving > 1 m/s, stopped), projected + size test only
	if (Traffic)
	{
		TArray<FVector> P; TArray<float> Sp; TArray<int32> Key; Traffic->GetMovingInfo(P, Sp, Key);
		for (int32 I = 0; I < P.Num(); ++I)
		{
			NearestCar = FMath::Min(NearestCar, FVector::Dist(Eye, P[I]) / 100.f);
			if (Vis(P[I], 160.f, MinCarPx)) ++Mov;
			if (VisP(P[I], 160.f, MinCarPx)) { TPair<int32, int32>& L = Lanes.FindOrAdd(Key[I]); if (Sp[I] > 1.f) { ++MovFast; ++L.Key; } else { ++Stopped; ++L.Value; } }
		}
		TArray<FVector> M; TArray<int32> MT, PT; TArray<FVector> PP; Traffic->GetPoints(M, MT, PP, PT);
		for (int32 I = 0; I < PP.Num(); ++I) Par += Vis(PP[I], 160.f, MinCarPx);
		for (int32 I = 0; I < M.Num(); ++I) if (MT[I] >= 13 && Vis(M[I], 300.f, MinCarPx)) ++Buses;
	}
	int32 People = 0, Walking = 0, DupHeads60 = 0, DupHeads30 = 0, DupBase30 = 0, Within60 = 0; TSet<int32> Looks, Heads; int32 Nearest = 0; float NearestM = 1e9f;
	int32 HandL = 0, HandR = 0, HandNear = 0, HandNearL = 0, HandNearR = 0;   // people >= 20 px unoccluded, left / right of the view axis; Near = within 80 m on the ground
	if (Crowd)
	{
		const FVector Rgt = FRotationMatrix(Rot).GetScaledAxis(EAxis::Y);
		{
			TArray<FVector> Pos; TArray<int32> Mod; TArray<USkeletalMeshComponent*> Comps; TArray<float> Sp; Crowd->GetLive(Pos, Mod, Comps, Sp);
			for (int32 I = 0; I < Pos.Num(); ++I) if (Vis(Pos[I], 175.f, 20.f))
			{
				const bool bR = FVector::DotProduct(Pos[I] - Eye, Rgt) > 0.f; (bR ? HandR : HandL)++;
				if (FVector2D::Distance(FVector2D(Pos[I].X, Pos[I].Y), FVector2D(Eye.X, Eye.Y)) < 8000.f) { ++HandNear; (bR ? HandNearR : HandNearL)++; }
			}
		}
		TArray<FVector> Pos; TArray<int32> Mod; TArray<USkeletalMeshComponent*> Comps; TArray<float> Sp; Crowd->GetLive(Pos, Mod, Comps, Sp);
		const int32 NB = FMath::Max(1, Crowd->Meshes.Num() / FMath::Max(1, Crowd->NumVariants));
		TMap<int32, int32> HeadCount60; TMap<int32, int32> HeadCount30; TMap<int32, int32> BaseCount30;
		for (int32 I = 0; I < Pos.Num(); ++I) if (Vis(Pos[I], 175.f, MinPersonPx))
		{
			++People; Walking += Sp[I] > 0.3f; Looks.Add(Mod[I]); Heads.Add(Mod[I] % NB);
			const float Dm = FVector::Dist(Eye, Pos[I]) / 100.f; NearestM = FMath::Min(NearestM, Dm);
			if (Dm < 60.f) { int32& N = HeadCount60.FindOrAdd(Mod[I]); if (N++ > 0) ++DupHeads60; }
			if (Dm < 30.f) { int32& N = HeadCount30.FindOrAdd(Mod[I]); if (N++ > 0) ++DupHeads30; int32& B = BaseCount30.FindOrAdd(Mod[I] % NB); if (B++ > 0) ++DupBase30; }
			if (Dm < 60.f) ++Within60;
		}
		(void)Nearest;
	}
	FString LaneStr; { TArray<int32> Ks; Lanes.GetKeys(Ks); Ks.Sort(); for (int32 K : Ks) LaneStr += FString::Printf(TEXT(" %d:%d/%d"), K, Lanes[K].Key, Lanes[K].Value); }
	FString QStr;
	if (Traffic) for (int32 Id : QueueLinks) { int32 N = 0, S = 0; float F = -1.f; Traffic->GetLinkQueue(Id, N, S, F); QStr += FString::Printf(TEXT(" | link %d cars %d stopped %d front %.1f m"), Id, N, S, F); }
	UE_LOG(LogWHLifeProbe, Display, TEXT("WH_LIFE_SAMPLE t=%.2f cam=(%.1f,%.1f,%.1f)m yaw=%.0f | vehicles unoccluded >=%.0fpx: moving %d (>1 m/s %d, standing %d) parked %d buses %d | nearest moving car %.1f m | lanes in view (projected, >= size) key:moving/standing%s | people >=%.0fpx: %d (walking %d, looks %d, citizen meshes %d, nearest %.1f m; within 60 m %d: repeated looks %d, within 30 m repeated looks %d / repeated citizen meshes %d) | people >=20px: %d (left %d right %d; within 80 m %d: left %d right %d) | signal av/st %d/%d | junction-box stops now %d worst %d%s"),
		T, Eye.X / 100.f, Eye.Y / 100.f, Eye.Z / 100.f, Rot.Yaw, MinCarPx, Mov, MovFast, Stopped, Par, Buses, NearestCar > 1e8f ? -1.f : NearestCar, *LaneStr, MinPersonPx, People, Walking, Looks.Num(), Heads.Num(), NearestM > 1e8f ? -1.f : NearestM, Within60, DupHeads60, DupHeads30, DupBase30,
		HandL + HandR, HandL, HandR, HandNear, HandNearL, HandNearR,
		Traffic ? Traffic->CurrentPhase(0) : -1, Traffic ? Traffic->CurrentPhase(1) : -1, Traffic ? Traffic->NumBoxStopped : -1, Traffic ? Traffic->MaxBoxStopped : -1, *QStr);
}
