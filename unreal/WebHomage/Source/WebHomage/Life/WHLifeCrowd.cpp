// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
#include "Life/WHLifeCrowd.h"
#include "Look/WHNightK.h"
#include "Life/WHLifeTraffic.h"
#include "Characters/WHCharAnimInstance.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "CollisionQueryParams.h"
#include "Animation/AnimInstance.h"
#include "Camera/PlayerCameraManager.h"
#include "Kismet/GameplayStatics.h"
#include "HAL/PlatformTime.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

DEFINE_LOG_CATEGORY_STATIC(LogWHCrowd, Log, All);
using namespace WHLife;

namespace
{
	inline uint32 Xs(uint32& S) { S ^= S << 13; S ^= S >> 17; S ^= S << 5; return S; }
	inline float Ff(uint32& S) { return (Xs(S) & 0xFFFFFF) / 16777216.f; }
	inline float WrapPi(float A) { while (A > PI) A -= 2.f * PI; while (A < -PI) A += 2.f * PI; return A; }
	constexpr float CrossSpeed = 1.35f;   // m/s on a crosswalk
}

AWHLifeCrowd::AWHLifeCrowd()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PrePhysics;
	SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
}

double AWHLifeCrowd::SignalClock() const { return Traffic ? Traffic->GetSignalClock() : Clock; }

FVector AWHLifeCrowd::CameraLocation() const
{
	if (!FocusOverride.IsNearlyZero()) return FocusOverride;
	if (UWorld* W = GetWorld()) if (APlayerCameraManager* CM = UGameplayStatics::GetPlayerCameraManager(W, 0)) return CM->GetCameraLocation();
	return GetActorLocation();
}

void AWHLifeCrowd::ParseWalk()
{
	Pts.Reset(); Edges.Reset(); Adj.Reset();
	TArray<FString> Lines; WalkData.ParseIntoArrayLines(Lines);
	for (const FString& Ln : Lines)
	{
		if (Ln.IsEmpty() || Ln[0] == '#') continue;
		TArray<FString> P; Ln.ParseIntoArray(P, TEXT(" "), true);
		if (P[0] == TEXT("P") && P.Num() >= 4) Pts.Add(FVector2D(FCString::Atof(*P[2]), FCString::Atof(*P[3])));
		else if (P[0] == TEXT("E") && P.Num() >= 7)
		{
			FEdge E; E.A = FCString::Atoi(*P[2]); E.B = FCString::Atoi(*P[3]); E.Kind = FCString::Atoi(*P[4]); E.Axis = FCString::Atoi(*P[5]); E.Len = FCString::Atof(*P[6]); E.Side = P.Num() > 7 ? FCString::Atoi(*P[7]) : 0;
			Edges.Add(E);
		}
	}
	Adj.SetNum(Pts.Num());
	for (int32 I = 0; I < Edges.Num(); ++I)
	{
		FEdge& E = Edges[I];
		if (!Pts.IsValidIndex(E.A) || !Pts.IsValidIndex(E.B)) { E.Len = 0.f; continue; }
		const FVector2D D = Pts[E.B] - Pts[E.A]; E.Len = D.Size(); E.U = E.Len > 1e-3f ? D / E.Len : FVector2D(1, 0);
		Adj[E.A].Add(I); Adj[E.B].Add(I);
	}
	UE_LOG(LogWHCrowd, Log, TEXT("[crowd] walk graph: %d corners, %d edges"), Pts.Num(), Edges.Num());
}

// right-hand offset (m) of a walker on a sidewalk edge: a uniform pick inside the free band (toward the roadway is positive), turned into the walker's own right / left
float AWHLifeCrowd::LatFor(const FEdge& E, int8 Dir, uint32& R) const
{
	const float Lo = E.Axis == 0 ? AvenueBandMin : StreetBandMin, Hi = E.Axis == 0 ? AvenueBandMax : StreetBandMax;
	const float Sg = (float)Dir * (float)(E.Side == 0 ? 1 : E.Side);
	float A = Lo * Sg, B = Hi * Sg; if (A > B) Swap(A, B);   // right-hand offsets of the band edges (B = the walker's right side)
	const float C = 0.5f * (A + B);
	if (Ff(R) < KeepRight) return C + (B - C) * (0.1f + 0.9f * Ff(R));   // keep right: the right half of the band in the walker's own frame
	return A + Ff(R) * (B - A);
}

void AWHLifeCrowd::SpawnWalker(FWalker& W, int32 EI, uint32& R, int8 Dir, float S)
{
	const FEdge& E = Edges[EI];
	const int32 M = FMath::Max(1, Meshes.Num());
	const int32 Keep = W.Comp;
	W = FWalker(); W.Comp = Keep; W.Rng = R;
	W.Model = FMath::Min(M - 1, FMath::FloorToInt(Ff(R) * M));
	W.Edge = EI; W.Dir = Dir; W.S = Dir > 0 ? S : E.Len - S;
	W.Base = (SpeedMin + Ff(R) * (SpeedMax - SpeedMin)) / 100.f;
	if (Ff(R) < 0.08f) W.Base = 1.45f; // the odd hurried walker
	if (Ff(R) < 0.06f) W.Base = 0.85f; // and the dawdler
	W.Speed = W.Target = W.Base;
	W.Lat = LatFor(E, Dir, R);
	W.Scale = 0.95f + Ff(R) * 0.1f;
	W.Node = Dir > 0 ? E.B : E.A;
	const FVector2D Dv = E.U * Dir, Rt(-Dv.Y, Dv.X);
	W.Pos = LinePos(E, Dir, W.S) + Rt * W.Lat;
	W.Heading = FMath::Atan2(Dv.Y, Dv.X);
	W.Rng = R;
}

void AWHLifeCrowd::Populate(const FVector& Cam)
{
	Walkers.Reset(); EdgeCum.Reset();
	float Cum = 0.f;
	for (int32 EI = 0; EI < Edges.Num(); ++EI)
	{
		const FEdge& E = Edges[EI];
		if (E.Kind == 0 && E.Len >= 3.f) Cum += E.Len * EdgeDensity(E);
		EdgeCum.Add(Cum);
	}
	uint32 R = 0xC0FFEE ^ (uint32)(Seed * 2654435761u); if (!R) R = 1;
	const float R2 = SpawnRadius * SpawnRadius;
	const FVector2D C2(Cam.X, Cam.Y);
	// expected population inside the disc: when it exceeds MaxWalkers every edge is thinned by the same factor (never truncated: the edge order would favour one side of the street)
	float Expect = 0.f;
	for (int32 EI = 0; EI < Edges.Num(); ++EI)
	{
		const FEdge& E = Edges[EI]; if (E.Kind != 0 || E.Len < 3.f) continue;
		const FVector2D Mid = (Pts[E.A] + Pts[E.B]) * 0.5f * 100.f;
		if ((Mid - C2).SizeSquared() > R2 * 1.2f) continue;
		Expect += E.Len / 1000.f * EdgeDensity(E);
	}
	const float Thin = Expect > (float)MaxWalkers ? (float)MaxWalkers / Expect : 1.f;
	for (int32 EI = 0; EI < Edges.Num(); ++EI)
	{
		const FEdge& E = Edges[EI]; if (E.Kind != 0 || E.Len < 3.f) continue;
		const float Dens = EdgeDensity(E) * Thin;
		const float Target = E.Len / 1000.f * Dens;
		int32 N = FMath::FloorToInt(Target); if (Ff(R) < Target - N) ++N;
		for (int32 I = 0; I < N && Walkers.Num() < MaxWalkers; ++I)
		{
			const float S = Ff(R) * E.Len; const int8 Dir = Ff(R) < 0.5f ? 1 : -1;
			const FVector2D P = LinePos(E, Dir, Dir > 0 ? S : E.Len - S);
			if ((FVector2D(P.X * 100.f, P.Y * 100.f) - C2).SizeSquared() > R2) continue;
			FWalker W; SpawnWalker(W, EI, R, Dir, S); Walkers.Add(W);
		}
	}
	NumWalkers = Walkers.Num();
	Center = Cam;
}

void AWHLifeCrowd::BuildRespawnEdges(const FVector& Cam)
{
	RespIdx.Reset(); RespCum.Reset();
	const FVector2D C2(Cam.X, Cam.Y);
	const float Lo = SpawnRadius * 0.6f, Hi = SpawnRadius;
	float Cum = 0.f;
	for (int32 EI = 0; EI < Edges.Num(); ++EI)
	{
		const FEdge& E = Edges[EI]; if (E.Kind != 0 || E.Len < 3.f) continue;
		bool bIn = false;
		for (int32 K = 0; K <= 6 && !bIn; ++K)
		{
			const FVector2D P = Pts[E.A] + E.U * (E.Len * K / 6.f);
			const float D = (FVector2D(P.X * 100.f, P.Y * 100.f) - C2).Size();
			if (D >= Lo && D <= Hi) bIn = true;
		}
		if (!bIn) continue;
		Cum += E.Len * EdgeDensity(E);
		RespIdx.Add(EI); RespCum.Add(Cum);
	}
}

// Recycle a walker that fell out of the camera disc to the far edge of the disc. A slow / still camera: anywhere on the ring, off-screen when possible (nobody sees it appear).
// A fast camera (a swing): AHEAD of its motion (within 60 deg of the velocity), so the sidewalks in front of a 25 m/s flight are as full as the ones it started over
// (recycling only off-screen used to leave the sidewalks ahead empty: round 02 swing clip, 0 people in 20 of 20 samples).
bool AWHLifeCrowd::Respawn(FWalker& W, const FVector& Cam, bool bPreferOffscreen)
{
	if (RespIdx.Num() == 0 || RespCum.Last() <= 0.f) return false;
	const FVector2D C2(Cam.X, Cam.Y);
	const float Sp = FVector2D(CamVel.X, CamVel.Y).Size();
	const bool bAhead = Sp > AheadSpeedCms;
	const FVector2D Dir = bAhead ? FVector2D(CamVel.X, CamVel.Y) / Sp : FVector2D::ZeroVector;
	APlayerController* PC = (bPreferOffscreen && !bAhead) ? UGameplayStatics::GetPlayerController(this, 0) : nullptr;
	int32 VW = 0, VH = 0; if (PC) PC->GetViewportSize(VW, VH);
	const float DMin = SpawnRadius * (bAhead ? 0.62f : 0.68f), DMax = SpawnRadius * 0.98f;
	for (int32 Try = 0; Try < 48; ++Try)
	{
		const float X = Ff(W.Rng) * RespCum.Last();
		int32 Lo = 0, Hi = RespCum.Num() - 1; while (Lo < Hi) { const int32 Mid = (Lo + Hi) / 2; if (RespCum[Mid] < X) Lo = Mid + 1; else Hi = Mid; }
		const int32 EI = RespIdx[Lo]; const FEdge& E = Edges[EI];
		const float S = Ff(W.Rng) * E.Len; const int8 D1 = Ff(W.Rng) < 0.5f ? 1 : -1;
		const FVector2D P = LinePos(E, D1, D1 > 0 ? S : E.Len - S);
		const FVector2D Off(P.X * 100.f - C2.X, P.Y * 100.f - C2.Y);
		const float D = Off.Size();
		if (D < DMin || D > DMax) continue;
		if (bAhead && Try < 40 && FVector2D::DotProduct(Off / D, Dir) < AheadCosMin) continue;
		if (PC && VW > 0 && Try < 30)
		{
			FVector2D Sc; if (PC->ProjectWorldLocationToScreen(FVector(P.X * 100.f, P.Y * 100.f, SidewalkZ + 90.f), Sc, false) && Sc.X > -80 && Sc.Y > -80 && Sc.X < VW + 80 && Sc.Y < VH + 80) continue;
		}
		uint32 R = W.Rng; SpawnWalker(W, EI, R, D1, S); W.Rng = R;
		return true;
	}
	return false;
}

bool AWHLifeCrowd::GetView(FVector& Loc, FVector& Fwd, float& HalfDeg) const
{
	UWorld* Wd = GetWorld(); if (!Wd) return false;
	if (!FocusOverride.IsNearlyZero()) { Loc = FocusOverride; Fwd = FVector::ForwardVector; HalfDeg = 181.f; return true; }
	APlayerCameraManager* CM = UGameplayStatics::GetPlayerCameraManager(Wd, 0); if (!CM) return false;
	Loc = CM->GetCameraLocation(); Fwd = CM->GetCameraRotation().Vector();
	int32 VW = 0, VH = 0; if (APlayerController* PC = CM->GetOwningPlayerController()) PC->GetViewportSize(VW, VH);
	const float Aspect = VH > 0 ? (float)VW / VH : 1.78f;
	const float TanH = FMath::Tan(FMath::DegreesToRadians(CM->GetFOVAngle()) * 0.5f), TanV = TanH / FMath::Max(0.5f, Aspect);
	HalfDeg = FMath::RadiansToDegrees(FMath::Atan(FMath::Sqrt(TanH * TanH + TanV * TanV))) + ViewMarginDeg;
	return true;
}

void AWHLifeCrowd::BeginPlay()
{
	Super::BeginPlay();
	FParse::Value(FCommandLine::Get(), TEXT("WHLifeStats="), StatsInterval);
	if (FParse::Param(FCommandLine::Get(), TEXT("WHLifeRT"))) bVisibleInRayTracing = true;
	if (FParse::Param(FCommandLine::Get(), TEXT("WHLifeNoShadow"))) bCastShadows = false;
	if (FParse::Param(FCommandLine::Get(), TEXT("WHLifeOff")) || FParse::Param(FCommandLine::Get(), TEXT("WHCrowdOff"))) { UE_LOG(LogWHCrowd, Display, TEXT("[crowd] disabled by command line")); return; }
	if (Meshes.Num() == 0 || !AnimClass) { UE_LOG(LogWHCrowd, Warning, TEXT("[crowd] no citizen meshes / anim class")); return; }
	{ // command-line experiments (no map rebuild): -WHLifePerKm=<avenue>:<street> -WHLifeNearAll=<m> -WHLifeMargin=<deg> -WHLifeBand=<avMin>:<avMax>:<stMin>:<stMax> -WHLifeFill / -WHLifeFillSteps / -WHLifeFillPitch
		FString S;
		if (FParse::Value(FCommandLine::Get(), TEXT("WHLifePerKm="), S)) { TArray<FString> P; S.ParseIntoArray(P, TEXT(":"), true); if (P.Num() >= 2) { PerKmAvenue = FCString::Atof(*P[0]); PerKmStreet = FCString::Atof(*P[1]); } }
		float V = 0.f;
		if (FParse::Value(FCommandLine::Get(), TEXT("WHLifeNearAll="), V)) NearAllRadius = V * 100.f;
		if (FParse::Value(FCommandLine::Get(), TEXT("WHLifeMargin="), V)) ViewMarginDeg = V;
		if (FParse::Value(FCommandLine::Get(), TEXT("WHLifeShadowR="), V)) ShadowRadius = V * 100.f;
		if (FParse::Value(FCommandLine::Get(), TEXT("WHLifeLiveR="), V)) { LiveRadius = V * 100.f; LiveRadiusHigh = FMath::Max(LiveRadiusHigh, LiveRadius); }
		if (FParse::Value(FCommandLine::Get(), TEXT("WHLifeFill="), V)) FillLux = V;
		if (FParse::Value(FCommandLine::Get(), TEXT("WHLifeFillPitch="), V)) FillPitchDeg = V;
		if (FParse::Param(FCommandLine::Get(), TEXT("WHLifeFillAll"))) bFillShadeOnly = false;
		if (FParse::Value(FCommandLine::Get(), TEXT("WHLifeAheadCos="), V)) AheadCosMin = V;
		if (FParse::Value(FCommandLine::Get(), TEXT("WHLifeAheadSpeed="), V)) AheadSpeedCms = V;   // cm/s; 1e9 = the round 02 behaviour (recycle off-screen only)
		if (FParse::Value(FCommandLine::Get(), TEXT("WHLifeBand="), S)) { TArray<FString> P; S.ParseIntoArray(P, TEXT(":"), true); if (P.Num() >= 4) { AvenueBandMin = FCString::Atof(*P[0]); AvenueBandMax = FCString::Atof(*P[1]); StreetBandMin = FCString::Atof(*P[2]); StreetBandMax = FCString::Atof(*P[3]); } }
		FillSteps.Reset();
		if (FParse::Value(FCommandLine::Get(), TEXT("WHLifeFillSteps="), S, false))   // false: do not stop at the commas
		{
			TArray<FString> P; S.ParseIntoArray(P, TEXT(","), true);
			for (const FString& Q : P) { TArray<FString> TL; Q.ParseIntoArray(TL, TEXT(":"), true); if (TL.Num() >= 2) FillSteps.Add(TPair<float, float>(FCString::Atof(*TL[0]), FCString::Atof(*TL[1]))); }
		}
	}
	const bool bFill = FillLux > 0.f || FillSteps.Num() > 0;
	if (bFill)
	{
		FillLight = NewObject<UDirectionalLightComponent>(this, TEXT("CrowdFill"));
		FillLight->SetupAttachment(GetRootComponent());
		FillLight->SetMobility(EComponentMobility::Movable);
		FillLight->SetIntensity(FillLux);
		FillLight->SetUseTemperature(true); FillLight->SetTemperature(FillTemperature);
		FillLight->SetAtmosphereSunLight(false);   // a NewObject directional light is an atmosphere sun (index 0) by default: this 1800 lux fill outranked the night rig's 83 lux moon and lit the whole sky
		FillLight->SetCastShadows(false);
		FillLight->SetIndirectLightingIntensity(0.f);
		FillLight->SetVolumetricScatteringIntensity(0.f);
		FillLight->SetLightingChannels(false, true, false);
		FillLight->RegisterComponent();
		UE_LOG(LogWHCrowd, Log, TEXT("[crowd] fill light %.0f lux (steps %d), pitch %.0f, lighting channel 1"), FillLux, FillSteps.Num(), FillPitchDeg);
	}
	UE_LOG(LogWHCrowd, Log, TEXT("[crowd] density %.0f / %.0f per km (east avenue sidewalks x %.2f), near-all %.0f m, margin %.0f deg, band av %.2f..%.2f st %.2f..%.2f"), PerKmAvenue, PerKmStreet, AvenueEastFactor, NearAllRadius / 100.f, ViewMarginDeg, AvenueBandMin, AvenueBandMax, StreetBandMin, StreetBandMax);
	ParseWalk();
	Pool.Reset(); PoolModel.Reset(); SlotOwner.Reset(); FreeSlots.SetNum(Meshes.Num());
	for (int32 M = 0; M < Meshes.Num(); ++M)
	{
		for (int32 K = 0; K < PoolPerModel; ++K)
		{
			USkeletalMeshComponent* C = NewObject<USkeletalMeshComponent>(this, *FString::Printf(TEXT("Cit_%d_%d"), M, K));
			C->SetupAttachment(GetRootComponent());
			C->SetSkeletalMesh(Meshes[M]);
			C->SetAnimationMode(EAnimationMode::AnimationBlueprint);
			C->SetAnimInstanceClass(AnimClass);
			if (MaterialOverrides.IsValidIndex(M) && MaterialOverrides[M]) for (int32 Mi = 0; Mi < FMath::Max(1, C->GetNumMaterials()); ++Mi) C->SetMaterial(Mi, MaterialOverrides[M]);
			C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			C->SetCanEverAffectNavigation(false);
			if (bFill) C->SetLightingChannels(true, !bFillShadeOnly, false);   // shade-only: channel 1 is switched on per walker by UpdateShade / Assign
			C->SetCastShadow(bCastShadows);
			C->SetVisibleInRayTracing(bVisibleInRayTracing);
			C->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
			C->RegisterComponent();
			C->SetVisibility(false); C->SetComponentTickEnabled(false);
			FreeSlots[M].Add(Pool.Num()); PoolModel.Add(M); SlotOwner.Add(-1); Pool.Add(C);
		}
	}
	uint32 Rc = 0xBEEF1u ^ (uint32)Seed; Clock = 5.0 + Ff(Rc) * 30.0;
	bCentered = false; bReady = false; FirstRefreshes = 0;   // the population is created around the camera on the first tick that has one
	UE_LOG(LogWHCrowd, Log, TEXT("[crowd] BeginPlay: %d citizen looks, pool %d, walk graph %d edges"), Meshes.Num(), Pool.Num(), Edges.Num());
}

bool AWHLifeCrowd::MayCross(const FEdge& E, float Speed) const
{
	const double T = SignalClock();
	if (AWHLifeTraffic::SigPhase(T, E.Axis) != 0) return false;
	double C = FMath::Fmod(T, 40.0); if (C < 0.0) C += 40.0;
	double Rem = 0.0;
	if (E.Axis == 0) Rem = 40.0 - C;                       // avenue traffic red 25..40
	else Rem = C < 26.0 ? 26.0 - C : (C >= 39.0 ? 40.0 - C + 26.0 : 0.0); // street traffic red 39..40 + 0..26
	return Rem >= 0.7 * E.Len / CrossSpeed;
}

bool AWHLifeCrowd::CrosswalkClear(int32 EI)
{
	if (!Traffic || !Edges.IsValidIndex(EI)) return true;
	const double Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0;
	if (const TPair<double, bool>* C = XClear.Find(EI)) if (Now - C->Key < 0.25) return C->Value;
	const FEdge& E = Edges[EI];
	const bool bClear = !Traffic->AnyCarNearSegment(Pts[E.A], Pts[E.B], 2.4f);
	XClear.Add(EI, TPair<double, bool>(Now, bClear));
	return bClear;
}

void AWHLifeCrowd::EnterEdge(FWalker& W, int32 Edge, int32 FromNode, bool)
{
	const FEdge& E = Edges[Edge];
	W.Edge = Edge; W.Dir = (E.A == FromNode) ? 1 : -1; W.State = 0; W.WaitT = 0.f;
	W.Lat = E.Kind == 1 ? 0.3f + Ff(W.Rng) * 1.0f : LatFor(E, W.Dir, W.Rng);
	W.Target = E.Kind == 1 ? FMath::Max(W.Base, CrossSpeed) : W.Base; W.bDecided = false;
	const FVector2D Dv = E.U * W.Dir;
	W.S = FMath::Clamp(FVector2D::DotProduct(W.Pos - LinePos(E, W.Dir, 0.f), Dv), 0.f, E.Len);
	W.Node = W.Dir > 0 ? E.B : E.A;
}

void AWHLifeCrowd::PickNextEdge(FWalker& W)
{
	const FEdge& Cur = Edges[W.Edge];
	const FVector2D Dv = Cur.U * W.Dir;
	const int32 Node = W.Node;
	TArray<float, TInlineAllocator<4>> Wt; TArray<int32, TInlineAllocator<4>> Ids;
	float Tot = 0.f;
	for (int32 EI : Adj[Node])
	{
		if (EI == W.Edge) continue;
		const FEdge& E = Edges[EI];
		const FVector2D Out = (E.A == Node ? E.U : -E.U);
		const float Dot = FVector2D::DotProduct(Out, Dv);
		float X;
		if (Dot > 0.7f) X = E.Kind == 0 ? 0.55f : 0.5f;
		else if (Dot < -0.7f) X = 0.02f;
		else X = E.Kind == 0 ? 0.3f : 0.3f;
		Wt.Add(X); Ids.Add(EI); Tot += X;
	}
	if (Ids.Num() == 0) { W.NextEdge = W.Edge; return; } // dead end: turn round on the same edge
	float R = Ff(W.Rng) * Tot;
	for (int32 I = 0; I < Ids.Num(); ++I) { R -= Wt[I]; if (R <= 0.f) { W.NextEdge = Ids[I]; return; } }
	W.NextEdge = Ids.Last();
}

void AWHLifeCrowd::StepWalker(FWalker& W, float Dt)
{
	if (W.Edge < 0) return;
	if (W.State == 1)
	{
		W.WaitT += Dt; W.Speed = 0.f;
		if (MayCross(Edges[W.NextEdge], W.Base) && (W.WaitT > 30.f || CrosswalkClear(W.NextEdge))) EnterEdge(W, W.NextEdge, W.Node, true);
		return;
	}
	const FEdge& E = Edges[W.Edge];
	const float ToEnd = E.Len - W.S;
	// decide the next edge early, and brake in time when it is a crosswalk that is not open (people do not stop dead: the gait follows the ground speed)
	if (!W.bDecided && ToEnd < 3.0f) { PickNextEdge(W); W.bDecided = true; }
	float Tgt = W.Target;
	if (W.bDecided && Edges[W.NextEdge].Kind == 1 && (!MayCross(Edges[W.NextEdge], W.Base) || !CrosswalkClear(W.NextEdge)) && ToEnd < W.Speed * W.Speed / (2.f * 2.2f) + 0.6f) Tgt = ToEnd > 0.55f ? 0.3f : 0.f;
	W.Speed = FMath::FInterpConstantTo(W.Speed, Tgt, Dt, Tgt > W.Speed ? 1.6f : 2.2f);
	const FVector2D Dv = E.U * W.Dir, Rt(-Dv.Y, Dv.X);
	const float S2 = FMath::Min(W.S + 1.6f, E.Len);
	W.LatAdj = FMath::FInterpTo(W.LatAdj, W.AdjTarget, Dt, 3.f);
	const FVector2D Tp = LinePos(E, W.Dir, S2) + Rt * (W.Lat + W.LatAdj);
	const FVector2D To = Tp - W.Pos;
	if (To.SizeSquared() > 1e-4f)
	{
		const float Des = FMath::Atan2(To.Y, To.X);
		const float D = WrapPi(Des - W.Heading);
		const float MaxTurn = 4.5f * Dt;
		W.Heading = WrapPi(W.Heading + FMath::Clamp(D, -MaxTurn, MaxTurn));
	}
	W.Pos += FVector2D(FMath::Cos(W.Heading), FMath::Sin(W.Heading)) * (W.Speed * Dt);
	if (bAvoid)
	{ // personal space around a street-level camera: walkers slide around it instead of through it
		FVector2D Dc = W.Pos - AvoidM; const float D = Dc.Size();
		if (D < CameraAvoidRadius) { if (D < 1e-3f) Dc = FVector2D(-Dv.Y, Dv.X); else Dc /= D; W.Pos = AvoidM + Dc * CameraAvoidRadius; }
	}
	W.S = FMath::Clamp(FVector2D::DotProduct(W.Pos - LinePos(E, W.Dir, 0.f), Dv), 0.f, E.Len);
	if (W.S >= E.Len - 0.45f)
	{
		if (!W.bDecided) { PickNextEdge(W); W.bDecided = true; }
		const FEdge& N = Edges[W.NextEdge];
		if (N.Kind == 1 && (!MayCross(N, W.Base) || !CrosswalkClear(W.NextEdge))) { W.State = 1; W.WaitT = 0.f; W.Speed = 0.f; }
		else EnterEdge(W, W.NextEdge, W.Node, true);
	}
}

void AWHLifeCrowd::Assign(int32 WI, int32 Slot)
{
	FWalker& W = Walkers[WI]; USkeletalMeshComponent* C = Pool[Slot];
	W.Comp = Slot; SlotOwner[Slot] = WI;
	C->SetVisibility(true); C->SetComponentTickEnabled(true);
	if (FillLight)
	{
		if (bFillShadeOnly && bHaveSun && GetWorld()) { FCollisionQueryParams Q(SCENE_QUERY_STAT(LifeShade), true); W.ShadeT = 0.f; TestShade(W, Q, GetWorld()->GetTimeSeconds()); W.ShadeT = GetWorld()->GetTimeSeconds() + 0.5 + 0.9 * Ff(W.Rng); }
		C->SetLightingChannels(true, !bFillShadeOnly || W.Shade != 0, false);
	}
	Apply(W);
	// random gait phase: run the (native, speed-synced) walk cycle forward by 0 .. ~2 s before the first visible frame
	if (UWHCharAnimInstance* AI = Cast<UWHCharAnimInstance>(C->GetAnimInstance()))
	{
		AI->ForcedSpeed = W.State == 0 ? W.Speed * 100.f : 0.f;
		const int32 N = 6 + FMath::FloorToInt(Ff(W.Rng) * 58.f);
		for (int32 I = 0; I < N; ++I) C->TickAnimation(1.f / 30.f, false);
		C->RefreshBoneTransforms();
	}
}

void AWHLifeCrowd::Unassign(int32 WI)
{
	FWalker& W = Walkers[WI]; W.AdjTarget = 0.f; if (W.Comp < 0) return;
	USkeletalMeshComponent* C = Pool[W.Comp];
	C->SetVisibility(false); C->SetComponentTickEnabled(false);
	FreeSlots[PoolModel[W.Comp]].Add(W.Comp); SlotOwner[W.Comp] = -1; W.Comp = -1;
}

void AWHLifeCrowd::Apply(FWalker& W)
{
	if (W.Comp < 0) return;
	USkeletalMeshComponent* C = Pool[W.Comp];
	const float Z = (W.Edge >= 0 && Edges[W.Edge].Kind == 1) ? 2.f : SidewalkZ;
	// P2: glTF +Z forward -> actor +X is a -90 deg yaw of the mesh
	C->SetWorldLocationAndRotation(FVector(W.Pos.X * 100.f, W.Pos.Y * 100.f, Z), FRotator(0.f, FMath::RadiansToDegrees(W.Heading) - 90.f, 0.f));
	C->SetWorldScale3D(FVector(W.Scale));
	if (UWHCharAnimInstance* AI = Cast<UWHCharAnimInstance>(C->GetAnimInstance())) AI->ForcedSpeed = W.State == 0 ? W.Speed * 100.f : 0.f;
}

void AWHLifeCrowd::RefreshLive(const FVector& Cam)
{
	FVector Eye, Fwd; float HalfDeg = 181.f; GetView(Eye, Fwd, HalfDeg);
	const FVector2D C2(Cam.X, Cam.Y);
	// the population follows the camera: a jump means a teleport -> repopulate; otherwise walkers that fell behind are recycled to the far edge of the disc
	if (bCentered && FVector2D::Distance(C2, FVector2D(Center.X, Center.Y)) > SpawnRadius * 0.8f)
	{
		for (int32 I = 0; I < Walkers.Num(); ++I) Unassign(I);
		Populate(Cam); FirstRefreshes = 0;
	}
	else
	{
		const float Rr2 = (SpawnRadius * 1.12f) * (SpawnRadius * 1.12f);
		bool bBuilt = false;
		// a fast camera recycles everything that is 60 m or more BEHIND it too (nobody sees them, and waiting for the far edge of the disc left the sidewalks ahead empty for the first
		// seconds of a flight that starts at the edge of the city), and puts them on the ring ahead
		const float VSp = FVector2D(CamVel.X, CamVel.Y).Size(); const bool bFastCam = VSp > AheadSpeedCms; const FVector2D VDir = bFastCam ? FVector2D(CamVel.X, CamVel.Y) / VSp : FVector2D::ZeroVector;
		int32 BehindBudget = 28;   // the flight sweeps about 6 m of avenue per refresh (2 sidewalks x 1.6 walkers / m ~ 20 walkers): recycle a few more than that per refresh, never the whole trailing half at once
		for (int32 I = 0; I < Walkers.Num(); ++I)
		{
			const FVector2D Off = FVector2D(Walkers[I].Pos.X * 100.f, Walkers[I].Pos.Y * 100.f) - C2;
			const bool bFar = Off.SizeSquared() > Rr2;
			if (!bFar && !(bFastCam && BehindBudget > 0 && FVector2D::DotProduct(Off, VDir) < -6000.f)) continue;
			if (!bFar) --BehindBudget;
			if (!bBuilt) { BuildRespawnEdges(Cam); bBuilt = true; }
			Unassign(I); Respawn(Walkers[I], Cam, true);
		}
	}
	Center = Cam;
	const float LiveR = FMath::Lerp(LiveRadius, LiveRadiusHigh, FMath::Clamp((Eye.Z - HighCamFromCm) / FMath::Max(1.f, HighCamToCm - HighCamFromCm), 0.f, 1.f));
	const float R2 = LiveR * LiveR, Rd2 = (LiveR * 1.08f) * (LiveR * 1.08f);
	const float CosIn = FMath::Cos(FMath::DegreesToRadians(FMath::Min(HalfDeg, 180.f))), CosOut = FMath::Cos(FMath::DegreesToRadians(FMath::Min(HalfDeg + 8.f, 180.f)));
	const float NearR2 = NearAllRadius * NearAllRadius, NearRo2 = (NearAllRadius * 1.1f) * (NearAllRadius * 1.1f);
	auto InView = [&](const FWalker& W, bool bHyst) -> bool
	{
		const FVector D(W.Pos.X * 100.f - Eye.X, W.Pos.Y * 100.f - Eye.Y, SidewalkZ + 90.f - Eye.Z);
		const float D2 = D.SizeSquared();
		if (D2 < (bHyst ? NearRo2 : NearR2)) return true;
		if (HalfDeg > 180.f) return true;
		return FVector::DotProduct(D / FMath::Sqrt(D2), Fwd) > (bHyst ? CosOut : CosIn);
	};
	// release walkers that left the live disc / the view cone
	for (int32 I = 0; I < Walkers.Num(); ++I)
		if (Walkers[I].Comp >= 0 && ((FVector2D(Walkers[I].Pos.X * 100.f, Walkers[I].Pos.Y * 100.f) - C2).SizeSquared() > Rd2 || !InView(Walkers[I], true))) Unassign(I);
	// The look (mesh + outfit + head colouring) is chosen at assignment time: the look that is not worn by a live walker within 45 m (weight 1000) or 90 m (100), with a
	// different citizen mesh than the walkers within 30 m where possible (40), the walker's default look breaking ties. Nearest walkers are served first, a few per refresh
	// so a turning camera cannot hitch (the first refreshes are unlimited). Looks are variant-major: look = variant * NB + citizen.
	const int32 NB = FMath::Max(1, Meshes.Num() / FMath::Max(1, NumVariants));
	TArray<TArray<FVector2D>> LiveByBase, LiveByLook; LiveByBase.SetNum(NB); LiveByLook.SetNum(Meshes.Num());
	for (const FWalker& W : Walkers) if (W.Comp >= 0) { const FVector2D P(W.Pos.X * 100.f, W.Pos.Y * 100.f); LiveByBase[W.Model % NB].Add(P); LiveByLook[W.Model].Add(P); }
	TArray<TPair<float, int32>, TInlineAllocator<256>> Cand;
	for (int32 I = 0; I < Walkers.Num(); ++I)
	{
		if (Walkers[I].Comp >= 0) continue;
		const float D2 = (FVector2D(Walkers[I].Pos.X * 100.f, Walkers[I].Pos.Y * 100.f) - C2).SizeSquared();
		if (D2 < R2 && InView(Walkers[I], false)) Cand.Add(TPair<float, int32>(D2, I));
	}
	Cand.Sort([](const TPair<float, int32>& A, const TPair<float, int32>& B) { return A.Key < B.Key; });
	constexpr float Look45 = 4500.f * 4500.f, Look90 = 9000.f * 9000.f, Base30 = 3000.f * 3000.f;
	const bool bFast = FVector2D(CamVel.X, CamVel.Y).Size() > AheadSpeedCms;
	const int32 Limit = FirstRefreshes < 3 ? INT32_MAX : (bFast ? MaxAssignPerRefresh * 2 : MaxAssignPerRefresh);
	int32 Assigned = 0;
	for (const TPair<float, int32>& P : Cand)
	{
		if (Assigned >= Limit) break;
		FWalker& W = Walkers[P.Value];
		const FVector2D Me(W.Pos.X * 100.f, W.Pos.Y * 100.f);
		int32 Best = -1; float BestScore = 1e9f;
		for (int32 M = 0; M < Meshes.Num(); ++M)
		{
			if (FreeSlots[M].Num() == 0) continue;
			int32 SameLook45 = 0, SameLook90 = 0, SameBase30 = 0;
			for (const FVector2D& Q : LiveByLook[M]) { const float D = (Q - Me).SizeSquared(); if (D < Look90) { ++SameLook90; if (D < Look45) ++SameLook45; } }
			for (const FVector2D& Q : LiveByBase[M % NB]) if ((Q - Me).SizeSquared() < Base30) ++SameBase30;
			const float Score = SameLook45 * 1000.f + SameLook90 * 100.f + SameBase30 * 40.f + (M == W.Model ? 0.f : 1.f);
			if (Score < BestScore) { BestScore = Score; Best = M; }
		}
		if (Best < 0) continue;
		W.Model = Best; LiveByBase[Best % NB].Add(Me); LiveByLook[Best].Add(Me);
		Assign(P.Value, FreeSlots[Best].Pop()); ++Assigned;
	}
	++FirstRefreshes;
	// identical looks in the CAMERA'S frame: among the walkers that project inside the viewport and are within 60 m, a look may appear once. When two share one, the farther
	// walker (never closer than 30 m, so a swap is a few dozen pixels at most) takes a look that is not on screen (a different citizen mesh first); at most 10 swaps per refresh
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
	{
		int32 VW = 0, VH = 0; PC->GetViewportSize(VW, VH);
		if (VW > 0 && VH > 0)
		{
			TArray<int32> OnCount; OnCount.Init(0, Meshes.Num()); TArray<int32> OnBase; OnBase.Init(0, NB);
			TArray<TPair<float, int32>> On;
			for (int32 I = 0; I < Walkers.Num(); ++I)
			{
				const FWalker& W = Walkers[I]; if (W.Comp < 0) continue;
				FVector2D Sc; const FVector P(W.Pos.X * 100.f, W.Pos.Y * 100.f, SidewalkZ + 90.f);
				const float Dist = FVector::Dist(Eye, P);
				if (Dist > 6000.f || !PC->ProjectWorldLocationToScreen(P, Sc, false) || Sc.X < 0 || Sc.Y < 0 || Sc.X > VW || Sc.Y > VH) continue;
				On.Add(TPair<float, int32>(Dist, I)); ++OnCount[W.Model]; ++OnBase[W.Model % NB];
			}
			On.Sort([](const TPair<float, int32>& A, const TPair<float, int32>& B) { return A.Key > B.Key; }); // farthest first
			int32 Swaps = 0;
			for (const TPair<float, int32>& E : On)
			{
				if (Swaps >= 10) break;
				FWalker& W = Walkers[E.Value];
				if (OnCount[W.Model] <= 1 || E.Key < 3000.f) continue;
				int32 Best = -1;
				for (int32 Pass = 0; Pass < 2 && Best < 0; ++Pass)   // pass 0: a look whose citizen mesh is not on screen either; pass 1: any unused look
					for (int32 M = 0; M < Meshes.Num(); ++M) if (M != W.Model && OnCount[M] == 0 && (Pass == 1 || OnBase[M % NB] == 0) && FreeSlots[M].Num() > 0) { Best = M; break; }
				if (Best < 0) continue;
				--OnCount[W.Model]; --OnBase[W.Model % NB]; Unassign(E.Value); W.Model = Best; ++OnCount[Best]; ++OnBase[Best % NB]; Assign(E.Value, FreeSlots[Best].Pop()); ++Swaps;
			}
		}
	}
	NumLive = 0; NumWaiting = 0; NumShade = 0;
	for (const FWalker& W : Walkers)
	{
		NumLive += W.Comp >= 0; NumWaiting += W.State == 1; NumShade += (W.Comp >= 0 && W.Shade);
		if (W.Comp >= 0)
		{
			const bool bShadow = bCastShadows && FVector2D::DistSquared(FVector2D(W.Pos.X * 100.f, W.Pos.Y * 100.f), C2) < ShadowRadius * ShadowRadius;
			USkeletalMeshComponent* Cm = Pool[W.Comp]; if (Cm->CastShadow != bShadow) Cm->SetCastShadow(bShadow);
		}
	}
}

void AWHLifeCrowd::Tick(float Dt)
{
	Super::Tick(Dt);
	if (!bCentered)
	{
		// the population is created around the first valid camera (the fixed shot camera / the rig / the player's view)
		FVector Eye, Fwd; float Half = 0.f;
		const bool bHave = GetView(Eye, Fwd, Half) && !Eye.IsNearlyZero(50.f);
		if (!bHave && (!GetWorld() || GetWorld()->GetTimeSeconds() < 2.0)) return;
		if (Edges.Num() == 0) return;
		const FVector Cam = bHave ? Eye : GetActorLocation();
		Populate(Cam);
		uint32 Rc = 0xBEEF1u ^ (uint32)Seed; Clock = 5.0 + Ff(Rc) * 30.0;
		for (int32 I = 0; I < 40; ++I) { for (FWalker& W : Walkers) StepWalker(W, 0.5f); Clock += 0.5; } // let the crowd mix before the first frame
		bCentered = true; bReady = true; FirstRefreshes = 0;
		RefreshLive(Cam);
		UE_LOG(LogWHCrowd, Log, TEXT("[crowd] populated around (%.0f, %.0f) m: %d walkers, %d live, %d looks, pool %d"), Cam.X / 100.f, Cam.Y / 100.f, NumWalkers, NumLive, Meshes.Num(), Pool.Num());
		return;
	}
	if (!bReady) return;
	const double T0 = FPlatformTime::Seconds();
	{ // camera velocity (cm/s, smoothed): a fast camera recycles walkers ahead of itself
		const FVector CamNow = CameraLocation();
		if (bHavePrevCam && Dt > 1e-4f) { const FVector V = (CamNow - PrevCam) / Dt; CamVel = V.Size() < 9000.f ? FMath::Lerp(CamVel, V, FMath::Clamp(Dt * 6.f, 0.f, 1.f)) : FVector::ZeroVector; }
		PrevCam = CamNow; bHavePrevCam = true;
	}
	UpdateFill();
	UpdateShade();
	Dt = FMath::Min(Dt, 0.1f);
	if (!Traffic) Clock += Dt;
	{ FVector Eye, Fwd; float Half = 0.f; bAvoid = GetView(Eye, Fwd, Half) && FocusOverride.IsNearlyZero() && Eye.Z < 450.f; if (bAvoid) AvoidM = FVector2D(Eye.X, Eye.Y) * 0.01f; }
	++TickCount;
	for (int32 I = 0; I < Walkers.Num(); ++I)   // live walkers every tick; the rest (no mesh) a quarter of the ticks with 4 x Dt: the 190 m population costs a fraction of its size
	{
		FWalker& W = Walkers[I];
		if (W.Comp >= 0) StepWalker(W, Dt); else if (((I + TickCount) & 3) == 0) StepWalker(W, Dt * 4.f);
	}
	RefreshT += Dt;
	if (RefreshT > 0.25f) { RefreshT = 0.f; RefreshLive(CameraLocation()); UpdateAvoidance(); }
	for (FWalker& W : Walkers) if (W.Comp >= 0) Apply(W);
	LastSimMs = (FPlatformTime::Seconds() - T0) * 1000.f;
	if (StatsInterval > 0.f) { StatsT += Dt; if (StatsT >= StatsInterval) { StatsT = 0.f; UE_LOG(LogWHCrowd, Log, TEXT("%s"), *StatsString()); } }
}

// Live walkers sidestep around the walkers in their way (2.5-3 m ahead, less than 0.75 m to either side): a smooth lateral offset the heading controller follows, so people
// slide past each other instead of through each other (round 02 critic: interpenetrating walkers). 3 m grid over the live set, run with every live-set refresh.
void AWHLifeCrowd::UpdateAvoidance()
{
	TArray<int32> Live; Live.Reserve(NumLive + 8);
	for (int32 I = 0; I < Walkers.Num(); ++I) if (Walkers[I].Comp >= 0 && Walkers[I].State == 0) Live.Add(I);
	auto Key = [](int32 CX, int32 CY) -> int64 { return ((int64)CX << 32) ^ (int64)(uint32)CY; };
	TMap<int64, TArray<int32, TInlineAllocator<6>>> Grid; Grid.Reserve(Live.Num());
	for (int32 I : Live) { const FVector2D P = Walkers[I].Pos; Grid.FindOrAdd(Key(FMath::FloorToInt(P.X / 3.f), FMath::FloorToInt(P.Y / 3.f))).Add(I); }
	for (int32 I : Live)
	{
		FWalker& W = Walkers[I];
		const FVector2D Fwd(FMath::Cos(W.Heading), FMath::Sin(W.Heading)), Rt(-Fwd.Y, Fwd.X);
		const int32 CX = FMath::FloorToInt(W.Pos.X / 3.f), CY = FMath::FloorToInt(W.Pos.Y / 3.f);
		float Push = 0.f;
		for (int32 DX = -1; DX <= 1; ++DX) for (int32 DY = -1; DY <= 1; ++DY)
		{
			const TArray<int32, TInlineAllocator<6>>* Cell = Grid.Find(Key(CX + DX, CY + DY)); if (!Cell) continue;
			for (int32 J : *Cell)
			{
				if (J == I) continue;
				const FVector2D D = Walkers[J].Pos - W.Pos;
				const float F = FVector2D::DotProduct(D, Fwd); if (F < -0.25f || F > 3.f) continue;
				const float L = FVector2D::DotProduct(D, Rt); if (FMath::Abs(L) > 0.75f) continue;
				const float Wt = FMath::Clamp(1.15f - F / 3.f, 0.2f, 1.f);
				const float Away = L > 0.05f ? -1.f : (L < -0.05f ? 1.f : (I < J ? 1.f : -1.f));   // neighbour on my right -> step left; dead ahead -> the lower id steps right
				Push += Away * (0.85f - FMath::Abs(L)) * 1.1f * Wt;
			}
		}
		W.AdjTarget = FMath::Clamp(Push, -0.8f, 0.8f);
	}
}

void AWHLifeCrowd::TestShade(FWalker& W, FCollisionQueryParams& Q, double Now)
{
	if (W.Comp < 0) return;
	const FVector S(W.Pos.X * 100.f, W.Pos.Y * 100.f, SidewalkZ + 120.f);
	const bool bBlocked = GetWorld()->LineTraceTestByChannel(S, S + SunDir * 12000.f, ECC_Visibility, Q);
	W.ShadeT = Now + 0.8 + 0.6 * Ff(W.Rng);
	if ((uint8)bBlocked != W.Shade) { W.Shade = bBlocked ? 1 : 0; if (bFillShadeOnly) Pool[W.Comp]->SetLightingChannels(true, W.Shade != 0, false); }
}

// Fill light for walkers in shade: a line trace towards the sun from each live walker (24 per tick at most, each walker again every ~1 s). The sun is the atmosphere sun light of the Look rig.
void AWHLifeCrowd::UpdateShade()
{
	if (!FillLight || !bFillShadeOnly) return;
	UWorld* Wd = GetWorld(); if (!Wd) return;
	const double Now = Wd->GetTimeSeconds();
	if (!bHaveSun)
	{
		if (Now < NextSunSearch) return;
		NextSunSearch = Now + 1.0;
		for (TActorIterator<ADirectionalLight> It(Wd); It; ++It)
			if (ULightComponent* LC = It->GetLightComponent())
				if (LC != FillLight && LC->IsUsedAsAtmosphereSunLight() && LC->GetAtmosphereSunLightIndex() == 0) { SunDir = -It->GetActorForwardVector(); bHaveSun = true; UE_LOG(LogWHCrowd, Log, TEXT("[crowd] sun for the shade test: %s dir (%.2f %.2f %.2f)"), *It->GetName(), SunDir.X, SunDir.Y, SunDir.Z); break; }
		if (!bHaveSun)
		{
			if (Now > 5.0) { bFillShadeOnly = false; for (USkeletalMeshComponent* C : Pool) if (C) C->SetLightingChannels(true, true, false); UE_LOG(LogWHCrowd, Warning, TEXT("[crowd] no atmosphere sun light found: the fill applies to every walker")); }
			return;
		}
	}
	FCollisionQueryParams Q(SCENE_QUERY_STAT(LifeShade), true);
	const int32 N = Walkers.Num(); int32 Done = 0;
	for (int32 K = 0; K < 240 && N > 0 && Done < 24; ++K)
	{
		FWalker& W = Walkers[(ShadeCursor++) % N];
		if (W.Comp < 0 || Now < W.ShadeT) continue;
		TestShade(W, Q, Now); ++Done;
	}
}

void AWHLifeCrowd::UpdateFill()
{
	if (!FillLight) return;
	float Lux = FillLux;
	if (FillSteps.Num() && GetWorld()) { const float T = GetWorld()->GetTimeSeconds(); for (const TPair<float, float>& P : FillSteps) if (T >= P.Key) Lux = P.Value; }
	Lux *= 1.f - WHReadNightK(GetWorld());   // the fill is tuned for the day sun: it fades out with the night factor (MPC_City NightK)
	if (!FMath::IsNearlyEqual(FillLight->Intensity, Lux)) FillLight->SetIntensity(Lux);
	FillLight->SetVisibility(Lux > 0.f);
	FVector Eye, Fwd; float H = 0.f;
	if (GetView(Eye, Fwd, H)) FillLight->SetWorldRotation(FRotator(-FillPitchDeg, Fwd.Rotation().Yaw, 0.f));
}

FString AWHLifeCrowd::StatsString() const
{
	return FString::Printf(TEXT("[crowd] walkers %d live %d waiting %d in shade %d models %d sim+apply %.2f ms"), NumWalkers, NumLive, NumWaiting, NumShade, Meshes.Num(), LastSimMs);
}

void AWHLifeCrowd::GetLive(TArray<FVector>& Pos, TArray<int32>& Model, TArray<USkeletalMeshComponent*>& Comps, TArray<float>& Speed) const
{
	Pos.Reset(); Model.Reset(); Comps.Reset(); Speed.Reset();
	for (const FWalker& W : Walkers)
	{
		if (W.Comp < 0) continue;
		Pos.Add(FVector(W.Pos.X * 100.f, W.Pos.Y * 100.f, SidewalkZ + 90.f)); Model.Add(W.Model); Comps.Add(Pool[W.Comp]); Speed.Add(W.State == 0 ? W.Speed : 0.f);
	}
}

int32 AWHLifeCrowd::CountInCone(FVector Eye, FVector Forward, float HalfAngleDeg, float Range, int32& OutModels) const
{
	int32 N = 0; TSet<int32> Models; const FVector F = Forward.GetSafeNormal(); const float CosA = FMath::Cos(FMath::DegreesToRadians(HalfAngleDeg));
	for (const FWalker& W : Walkers)
	{
		if (W.Comp < 0) continue;
		const FVector P(W.Pos.X * 100.f, W.Pos.Y * 100.f, SidewalkZ + 90.f);
		const FVector D = P - Eye; const float Dist = D.Size();
		if (Dist < Range && Dist > 100.f && FVector::DotProduct(D / Dist, F) > CosA) { ++N; Models.Add(W.Model); }
	}
	OutModels = Models.Num();
	return N;
}
