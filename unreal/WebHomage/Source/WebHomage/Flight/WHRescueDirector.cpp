// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
#include "Flight/WHRescueDirector.h"
#include "Flight/WHFlightWorld.h"
#include "WebHomage.h"
#include "CollisionQueryParams.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/EngineTypes.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

// Engine basic shapes are 100 cm (cube 100^3, sphere diameter 100, cylinder diameter 100 x height 100, all centred): scale = metres.
namespace
{
	const FVector DefaultStartCm(-2000.0, -23000.0, 150.0);   // Times Square start
	const double MinSiteDistCm = 15000.0, MaxSiteDistCm = 60000.0;
	const double SiteSpacingCm = 10000.0;
	const int32 Tries = 10;
	const int32 PeoplePerBatch = 2;

	FVector Flat(const FVector& V) { return FVector(V.X, V.Y, 0.0); }
	FVector DirFromDeg(double Deg) { const double R = FMath::DegreesToRadians(Deg); return FVector(FMath::Cos(R), FMath::Sin(R), 0.0); }
	double Ease(double K) { K = FMath::Clamp(K, 0.0, 1.0); return K * K * (3.0 - 2.0 * K); }
}

AWHRescueDirector::AWHRescueDirector()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = true;
	PrimaryActorTick.TickGroup = TG_PostPhysics;   // after the hero wrote its state for this frame
	SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
	SetCanBeDamaged(false);
}

AWHRescueDirector* AWHRescueDirector::Find(const UWorld* World)
{
	if (!World) return nullptr;
	for (TActorIterator<AWHRescueDirector> It(const_cast<UWorld*>(World)); It; ++It)
		if (IsValid(*It)) return *It;
	return nullptr;
}

// critic r2 (round 3 hero, fl17): carry anchor from the hero's anim instance (see the header)
void AWHRescueDirector::SetCarryAnchor(const USceneComponent* HeroMesh, const FTransform& LoadInMeshCS)
{
	CarryMesh = HeroMesh;
	CarryInMesh = LoadInMeshCS;
	CarryInMesh.SetScale3D(FVector::OneVector);
	const UWorld* W = GetWorld();
	CarryAnchorT = W ? W->GetTimeSeconds() : -1.0;
}

bool AWHRescueDirector::GetCarriedLoad(FTransform& OutLoadWorld, FVector& OutHalfCm) const
{
	for (const FWHEmergency& E : Emergencies)
	{
		if (E.Type != EWHEmergencyType::Crane || !E.bCarried || !E.Load) continue;
		OutLoadWorld = FTransform(E.LoadQ, E.LoadCm);
		OutHalfCm = E.Load->GetComponentScale() * 50.0;   // basic cube: 100 cm per unit scale
		return true;
	}
	return false;
}

const TCHAR* AWHRescueDirector::TypeName(EWHEmergencyType T)
{
	switch (T)
	{
	case EWHEmergencyType::Fire:  return TEXT("fire");
	case EWHEmergencyType::Crane: return TEXT("crane");
	case EWHEmergencyType::Bus:   return TEXT("bus");
	}
	return TEXT("?");
}

UWHFlightWorldSubsystem* AWHRescueDirector::Sub() const
{
	return UWHFlightWorldSubsystem::Get(this);
}

double AWHRescueDirector::GetNextWaveIn() const
{
	const UWorld* W = GetWorld();
	return (NextWaveT < 0 || !W) ? -1.0 : FMath::Max(0.0, NextWaveT - W->GetTimeSeconds());
}

void AWHRescueDirector::BeginPlay()
{
	Super::BeginPlay();
	const TCHAR* Cmd = FCommandLine::Get();
	int32 On = 1;
	FParse::Value(Cmd, TEXT("WHRescue="), On);
	FParse::Value(Cmd, TEXT("WHRescueSeed="), Seed);
	bEnabled = On != 0;
	Rng.Initialize(Seed);

	Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	Sphere = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	Cylinder = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	MGlow = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbFX.M_CmbFX"));
	MTrans = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbTrans.M_CmbTrans"));
	MSolid = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbSolid.M_CmbSolid"));
	if (!MGlow || !MTrans || !MSolid)
		UE_LOG(LogWebHomage, Warning, TEXT("WH_RESCUE materials missing (glow %d trans %d solid %d): run Scripts/build_combat.py"), MGlow ? 1 : 0, MTrans ? 1 : 0, MSolid ? 1 : 0);

	if (!bEnabled)
	{
		UE_LOG(LogWebHomage, Display, TEXT("WH_RESCUE disabled (-WHRescue=0)"));
		SetActorTickEnabled(false);
		return;
	}
	NextWaveT = GetWorld()->GetTimeSeconds() + FirstWaveDelayS;
	UE_LOG(LogWebHomage, Display, TEXT("WH_RESCUE director ready seed %d first wave in %.1f s"), Seed, FirstWaveDelayS);
}

void AWHRescueDirector::EndPlay(const EEndPlayReason::Type Reason)
{
	if (bEnabled)
	{
		const UWHFlightWorldSubsystem* S = Sub();
		UE_LOG(LogWebHomage, Display, TEXT("WH_RESCUE summary waves %d saved %d lost %d collateral $%.0f"),
			Wave, S ? S->LivesSaved : 0, S ? S->LivesLost : 0, S ? S->CollateralUSD : 0.f);
	}
	for (FWHEmergency& E : Emergencies) DestroyVisuals(E);
	Emergencies.Reset();
	for (FPuff& P : Puffs) if (IsValid(P.C)) P.C->DestroyComponent();
	Puffs.Reset();
	Super::EndPlay(Reason);
}

// ------------------------------------------------------------------------------------------------------------------------ traces

bool AWHRescueDirector::TraceLine(const FVector& A, const FVector& B, FHitResult& Hit, bool* bStartedInside) const
{
	if (bStartedInside) *bStartedInside = false;
	UWorld* W = GetWorld();
	if (!W) return false;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(WHRescueTrace), false, this);
	for (int32 i = 0; i < 6; ++i)
	{
		if (!W->LineTraceSingleByChannel(Hit, A, B, ECC_Visibility, Q)) return false;
		if (Hit.bStartPenetrating) { if (bStartedInside) *bStartedInside = true; return false; }
		AActor* HA = Hit.GetActor();
		if (HA && HA->IsA<APawn>()) { Q.AddIgnoredActor(HA); continue; }   // the hero / pedestrians are not sites
		return true;
	}
	return false;
}

bool AWHRescueDirector::GroundAt(const FVector& XY, double TopZ, double BottomZ, FVector& Out, bool* bBlocked) const
{
	FHitResult H;
	if (!TraceLine(FVector(XY.X, XY.Y, TopZ), FVector(XY.X, XY.Y, BottomZ), H, bBlocked)) return false;
	Out = H.ImpactPoint;
	return true;
}

double AWHRescueDirector::ProbeStreetZ(const FVector& Center) const
{
	// the lowest surface among a few probes around the hero = street level (the hero may stand on a roof)
	double Best = TNumericLimits<double>::Max();
	for (int32 i = 0; i < 9; ++i)
	{
		const FVector P = Center + (i == 0 ? FVector::ZeroVector : DirFromDeg(i * 45.0) * 4000.0);
		FVector G;
		if (GroundAt(P, Center.Z + 30000.0, Center.Z - 30000.0, G)) Best = FMath::Min(Best, G.Z);
	}
	return Best < TNumericLimits<double>::Max() ? Best : Center.Z - 150.0;
}

bool AWHRescueDirector::FindEdge(const FVector& Top, double MinDrop, FVector& OutEdge, FVector& OutDir, FVector& OutBelow) const
{
	// walk outward from a raised surface in 8 directions; the edge is the last point on it before the ground drops by MinDrop
	double BestDist = TNumericLimits<double>::Max();
	const double Phase = FMath::Fmod(FMath::Abs(Top.X * 0.013 + Top.Y * 0.007), 45.0);
	for (int32 d = 0; d < 8; ++d)
	{
		const FVector Dir = DirFromDeg(Phase + d * 45.0);
		FVector Prev = Top;
		for (int32 Step = 1; Step <= 20; ++Step)
		{
			const FVector P = Top + Dir * (Step * 300.0);
			FVector G; bool bBlocked = false;
			const bool bHit = GroundAt(P, Top.Z + 400.0, StreetZRef - 3000.0, G, &bBlocked);
			if (bBlocked) break;                                          // a taller building: no edge this way
			if (!bHit) G = FVector(P.X, P.Y, StreetZRef);                 // nothing below (void / water): treat as street
			if (G.Z > Top.Z + 300.0) break;                               // a wall rises
			if (G.Z < Top.Z - MinDrop)
			{
				const double Dist = Step * 300.0;
				if (Dist < BestDist) { BestDist = Dist; OutEdge = Prev; OutDir = Dir; OutBelow = G; }
				break;
			}
			Prev = G;
		}
	}
	return BestDist < TNumericLimits<double>::Max();
}

bool AWHRescueDirector::FarFromUsed(const FVector& P) const
{
	for (const FVector& U : UsedSites)
		if (FVector::Dist2D(U, P) < SiteSpacingCm) return false;
	return true;
}

FVector AWHRescueDirector::Candidate(int32 Slot, int32 Try, const FVector& Center) const
{
	// deterministic per (seed, wave, slot, try): the three slots of a wave spread ~120 deg apart around the hero
	const FRandomStream WaveR(Seed * 31 + Wave * 977);
	const double WaveRot = WaveR.FRandRange(0.0, 360.0);
	FRandomStream R(Seed * 10007 + Wave * 7919 + Slot * 131 + Try * 17);
	const double Ang = WaveRot + Slot * 120.0 + R.FRandRange(-40.0, 40.0);
	const double Dist = FMath::Lerp(MinSiteDistCm, MaxSiteDistCm, R.FRand());
	return Flat(Center) + DirFromDeg(Ang) * Dist;
}

FVector AWHRescueDirector::HeroPos() const
{
	if (const UWHFlightWorldSubsystem* S = Sub())
		if (S->bHeroValid) return S->HeroPosCm;
	if (const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0)) return P->GetActorLocation();
	return DefaultStartCm;
}

// ------------------------------------------------------------------------------------------------------------------------ waves

bool AWHRescueDirector::SpawnWave(bool bAllowFallback)
{
	const FVector Center = HeroPos();
	StreetZRef = ProbeStreetZ(Center);
	const double Now = GetWorld()->GetTimeSeconds();
	const double BaseClock[3] = { 82.0, 100.0, 116.0 };
	FRandomStream R(Seed * 613 + Wave * 37);

	TArray<FWHEmergency> New;
	TArray<int32> Missing;
	for (int32 Slot = 0; Slot < 3; ++Slot)
	{
		FWHEmergency E;
		E.Type = Slot == 0 ? EWHEmergencyType::Fire : Slot == 1 ? EWHEmergencyType::Crane : EWHEmergencyType::Bus;
		E.DurationS = FMath::Clamp(BaseClock[(Slot + Wave) % 3] + R.FRandRange(-6.0, 4.0), 75.0, 120.0);
		E.StartT = Now; E.EndT = Now + E.DurationS; E.NextStimT = Now;
		const bool bOk = E.Type == EWHEmergencyType::Fire ? PlaceFire(E, Center, Slot, false)
		               : E.Type == EWHEmergencyType::Crane ? PlaceCrane(E, Center, Slot, false)
		               : PlaceBus(E, Center, Slot, false);
		if (bOk) { UsedSites.Add(E.SiteCm); New.Add(MoveTemp(E)); }
		else { Missing.Add(Slot); New.Add(MoveTemp(E)); }
	}
	if (Missing.Num() == 3 && !bAllowFallback)
	{
		UE_LOG(LogWebHomage, Display, TEXT("WH_RESCUE wave %d: no city geometry around (%.0f, %.0f, %.0f) yet, retrying"), Wave + 1, Center.X, Center.Y, Center.Z);
		return false;
	}
	for (int32 Slot : Missing)
	{
		FWHEmergency& E = New[Slot];
		if (E.Type == EWHEmergencyType::Fire) PlaceFire(E, Center, Slot, true);
		else if (E.Type == EWHEmergencyType::Crane) PlaceCrane(E, Center, Slot, true);
		else PlaceBus(E, Center, Slot, true);
		UsedSites.Add(E.SiteCm);
	}
	while (UsedSites.Num() > 9) UsedSites.RemoveAt(0);

	++Wave;
	UE_LOG(LogWebHomage, Display, TEXT("WH_RESCUE wave %d start hero (%.0f, %.0f, %.0f) street z %.0f"), Wave, Center.X, Center.Y, Center.Z, StreetZRef);
	UWHFlightWorldSubsystem* S = Sub();
	for (FWHEmergency& E : New)
	{
		E.Id = NextId++;
		E.LivesAtStake = 0;
		if (E.Type == EWHEmergencyType::Fire) for (int32 L : E.BatchLives) E.LivesAtStake += L;
		else if (E.Type == EWHEmergencyType::Crane) E.LivesAtStake = R.RandRange(3, 6);
		else E.LivesAtStake = R.RandRange(8, 15);
		E.RemainingS = E.DurationS;
		UE_LOG(LogWebHomage, Display, TEXT("WH_RESCUE spawn id %d type %s site %s at (%.0f, %.0f, %.0f) dist %.0f m lives %d clock %.0f s"),
			E.Id, TypeName(E.Type), E.SiteKind, E.FocusCm.X, E.FocusCm.Y, E.FocusCm.Z, FVector::Dist2D(E.FocusCm, Center) / 100.0, E.LivesAtStake, E.DurationS);
		if (S) S->PushStimulus(EWHCrowdStimulus::Emergency, E.DangerCm, StimulusRadiusCm, 1.f, StimulusEveryS + 1.f);
		Emergencies.Add(MoveTemp(E));
	}
	return true;
}

// ------------------------------------------------------------------------------------------------------------------------ placement

bool AWHRescueDirector::PlaceFire(FWHEmergency& E, const FVector& Center, int32 Slot, bool bFallback)
{
	E.BatchLives.Reset();
	FRandomStream R(Seed * 17 + Wave * 101 + Slot);
	for (int32 b = 0; b < 3; ++b) E.BatchLives.Add(R.RandRange(2, 4));

	bool bFound = false;
	for (int32 Try = 0; Try < Tries && !bFound && !bFallback; ++Try)
	{
		const FVector C = Candidate(Slot, Try, Center);
		if (!FarFromUsed(C)) continue;
		FVector G;
		if (!GroundAt(C, StreetZRef + 30000.0, StreetZRef - 5000.0, G)) continue;
		const FVector P = G + FVector(0, 0, R.FRandRange(1200.0, 3500.0));   // a floor a few storeys up, in the open air above G
		double Best = TNumericLimits<double>::Max();
		FHitResult BestHit;
		const double Phase = R.FRandRange(0.0, 45.0);
		for (int32 d = 0; d < 8; ++d)
		{
			FHitResult H;
			if (!TraceLine(P, P + DirFromDeg(Phase + d * 45.0) * 4500.0, H)) continue;
			if (FMath::Abs(H.ImpactNormal.Z) > 0.35) continue;               // a wall, not a ledge
			if (H.Distance < Best) { Best = H.Distance; BestHit = H; }
		}
		if (Best == TNumericLimits<double>::Max()) continue;
		const FVector N = Flat(BestHit.ImpactNormal).GetSafeNormal();
		E.SiteCm = BestHit.ImpactPoint + N * 60.0;
		E.OutDir = N;
		FVector Below;
		E.DangerCm = GroundAt(E.SiteCm + N * 500.0, E.SiteCm.Z, StreetZRef - 5000.0, Below) ? Below : FVector(E.SiteCm.X, E.SiteCm.Y, G.Z);
		E.bGeometry = true; E.SiteKind = TEXT("facade");
		bFound = true;
	}
	if (!bFound)
	{
		if (!bFallback) return false;
		const FVector C = Candidate(Slot, 0, Center);
		E.SiteCm = FVector(C.X, C.Y, StreetZRef + 400.0);
		E.OutDir = Flat(Center - C).GetSafeNormal();
		E.DangerCm = FVector(C.X, C.Y, StreetZRef);
		E.bGeometry = false; E.SiteKind = TEXT("fallback");
	}
	E.FocusCm = E.SiteCm;
	BuildFire(E);
	return true;
}

bool AWHRescueDirector::PlaceCrane(FWHEmergency& E, const FVector& Center, int32 Slot, bool bFallback)
{
	FRandomStream R(Seed * 23 + Wave * 211 + Slot);
	FVector MastBase, Tip;
	double MastH = 0;
	bool bFound = false;

	// 1) a roof (>= 20 m above the street) with an edge over the street: mast on the roof, boom over the edge
	for (int32 Try = 0; Try < Tries && !bFound && !bFallback; ++Try)
	{
		const FVector C = Candidate(Slot, Try, Center);
		if (!FarFromUsed(C)) continue;
		FVector G;
		if (!GroundAt(C, StreetZRef + 30000.0, StreetZRef - 5000.0, G) || G.Z < StreetZRef + 2000.0) continue;
		FVector Edge, Dir, Below;
		if (!FindEdge(G, 1500.0, Edge, Dir, Below)) continue;
		FVector Base;
		if (!GroundAt(Edge - Dir * 600.0, Edge.Z + 400.0, Edge.Z - 600.0, Base)) continue;
		MastH = 2200.0;
		Tip = Base + Dir * 1500.0 + FVector(0, 0, MastH);
		FVector Street;
		if (!GroundAt(Tip - FVector(0, 0, 700.0), Tip.Z - 700.0, StreetZRef - 5000.0, Street)) continue;
		if (Street.Z > Tip.Z - 1700.0) continue;                             // the load would hang over another roof
		MastBase = Base; E.OutDir = Dir; E.StreetZ = Street.Z;
		E.bGeometry = true; E.SiteKind = TEXT("roof");
		bFound = true;
	}
	// 2) a free-standing tower crane in a street
	for (int32 Try = 0; Try < Tries && !bFound && !bFallback; ++Try)
	{
		const FVector C = Candidate(Slot, Try + Tries, Center);
		if (!FarFromUsed(C)) continue;
		FVector G;
		if (!GroundAt(C, StreetZRef + 30000.0, StreetZRef - 5000.0, G) || G.Z > StreetZRef + 800.0) continue;
		const FVector Dir = DirFromDeg(R.FRandRange(0.0, 360.0));
		MastH = 4500.0;
		Tip = G + Dir * 1800.0 + FVector(0, 0, MastH);
		FHitResult H;
		if (TraceLine(G + FVector(0, 0, 300.0), Tip, H)) continue;           // the mast / boom would cut through a building
		FVector Street;
		if (!GroundAt(Tip - FVector(0, 0, 900.0), Tip.Z - 900.0, StreetZRef - 5000.0, Street) || Street.Z > Tip.Z - 2500.0) continue;
		MastBase = G; E.OutDir = Dir; E.StreetZ = Street.Z;
		E.bGeometry = true; E.SiteKind = TEXT("street");
		bFound = true;
	}
	if (!bFound)
	{
		if (!bFallback) return false;
		const FVector C = Candidate(Slot, 0, Center);
		const FVector Dir = Flat(Center - C).GetSafeNormal();
		MastH = 4500.0;
		MastBase = FVector(C.X, C.Y, StreetZRef);
		Tip = MastBase + Dir * 1800.0 + FVector(0, 0, MastH);
		E.OutDir = Dir; E.StreetZ = StreetZRef;
		E.bGeometry = false; E.SiteKind = TEXT("fallback");
	}
	E.SiteCm = MastBase;
	E.TipCm = Tip;
	const double CableCm = MastH > 3000.0 ? 900.0 : 600.0;
	E.LoadRestCm = Tip - FVector(0, 0, CableCm + 75.0);
	E.LoadCm = E.LoadRestCm;
	E.FocusCm = E.LoadCm;
	E.DangerCm = FVector(Tip.X, Tip.Y, E.StreetZ);
	// snap so that the impact lands on the clock's zero: jolt + free fall of the load's height above the street
	const double FallH = FMath::Max(100.0, E.LoadRestCm.Z - 75.0 - E.StreetZ);
	const double Lead = CraneJoltS + FMath::Sqrt(2.0 * FallH / FMath::Max(50.0, double(CraneFallGravity)));
	E.SnapAtT = E.EndT - Lead;
	BuildCrane(E, MastBase, MastH, Tip);
	return true;
}

bool AWHRescueDirector::PlaceBus(FWHEmergency& E, const FVector& Center, int32 Slot, bool bFallback)
{
	FVector Edge, Dir, Below;
	bool bFound = false;
	// pass 0: a low elevated deck (bridge / viaduct / low roof, 5-40 m), pass 1: any roof edge
	for (int32 Pass = 0; Pass < 2 && !bFound && !bFallback; ++Pass)
	{
		for (int32 Try = 0; Try < Tries && !bFound; ++Try)
		{
			const FVector C = Candidate(Slot, Try + Pass * Tries, Center);
			if (!FarFromUsed(C)) continue;
			FVector G;
			if (!GroundAt(C, StreetZRef + 30000.0, StreetZRef - 5000.0, G)) continue;
			const double H = G.Z - StreetZRef;
			if (H < 500.0 || (Pass == 0 && H > 4000.0)) continue;
			if (!FindEdge(G, 500.0, Edge, Dir, Below)) continue;
			E.SiteKind = Pass == 0 ? TEXT("bridge") : TEXT("roof");
			E.bGeometry = true;
			bFound = true;
		}
	}
	if (!bFound)
	{
		if (!bFallback) return false;
		const FVector C = Candidate(Slot, 0, Center);
		FVector G;
		Edge = GroundAt(C, StreetZRef + 30000.0, StreetZRef - 5000.0, G) ? G : FVector(C.X, C.Y, StreetZRef);
		Dir = Flat(C - Center).GetSafeNormal();
		Below = Edge;
		E.bGeometry = false; E.SiteKind = TEXT("fallback");
	}
	E.SiteCm = Edge;
	E.OutDir = Dir;
	E.BelowZ = Below.Z;
	E.DangerCm = Below;
	BuildBus(E, Edge);
	E.FocusCm = Edge + Dir * 80.0 + FVector(0, 0, 160.0);
	return true;
}

// ------------------------------------------------------------------------------------------------------------------------ visuals

UStaticMeshComponent* AWHRescueDirector::AddMesh(FWHEmergency& E, UStaticMesh* Mesh, UMaterialInterface* Mat, const FLinearColor& Color,
	const FVector& PosCm, const FRotator& Rot, const FVector& ScaleM, float Emissive, float Opacity, USceneComponent* Parent)
{
	UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
	C->SetMobility(EComponentMobility::Movable);
	C->SetStaticMesh(Mesh);
	C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	C->SetGenerateOverlapEvents(false);
	C->SetCanEverAffectNavigation(false);
	C->SetCastShadow(Mat == MSolid.Get());
	if (Parent)
	{
		C->SetupAttachment(Parent);
		C->SetRelativeTransform(FTransform(Rot, PosCm, ScaleM));
		C->RegisterComponent();
	}
	else
	{
		C->SetUsingAbsoluteLocation(true); C->SetUsingAbsoluteRotation(true); C->SetUsingAbsoluteScale(true);
		C->SetupAttachment(GetRootComponent());
		C->RegisterComponent();
		C->SetWorldLocationAndRotation(PosCm, Rot);
		C->SetWorldScale3D(ScaleM);
	}
	if (Mat)
	{
		UMaterialInstanceDynamic* M = UMaterialInstanceDynamic::Create(Mat, this);
		M->SetVectorParameterValue(TEXT("Color"), Color);
		M->SetScalarParameterValue(TEXT("Opacity"), Opacity);
		M->SetScalarParameterValue(TEXT("Emissive"), Emissive);
		if (Mat == MSolid.Get()) M->SetScalarParameterValue(TEXT("Rough"), 0.55f);
		C->SetMaterial(0, M);
	}
	E.Parts.Add(C);
	return C;
}

UPointLightComponent* AWHRescueDirector::AddLight(FWHEmergency& E, const FVector& PosCm, const FLinearColor& Color, float Candela, float RadiusCm)
{
	UPointLightComponent* L = NewObject<UPointLightComponent>(this);
	L->SetMobility(EComponentMobility::Movable);
	L->SetUsingAbsoluteLocation(true);
	L->SetupAttachment(GetRootComponent());
	L->SetIntensityUnits(ELightUnits::Candelas);
	L->SetIntensity(Candela);
	L->SetLightColor(Color);
	L->SetAttenuationRadius(RadiusCm);
	L->SetCastShadows(false);
	L->RegisterComponent();
	L->SetWorldLocation(PosCm);
	E.Parts.Add(L);
	return L;
}

void AWHRescueDirector::SetGlow(UStaticMeshComponent* C, const FLinearColor& Color, float Opacity)
{
	if (!C) return;
	if (UMaterialInstanceDynamic* M = Cast<UMaterialInstanceDynamic>(C->GetMaterial(0)))
	{
		M->SetVectorParameterValue(TEXT("Color"), Color);
		M->SetScalarParameterValue(TEXT("Opacity"), Opacity);
	}
}

void AWHRescueDirector::BuildFire(FWHEmergency& E)
{
	FRandomStream R(int32(FMath::Fmod(FMath::Abs(E.SiteCm.X * 0.1 + E.SiteCm.Y * 0.37), 1.0e6)));
	const FVector N = E.OutDir;
	const FVector T = FVector::CrossProduct(FVector::UpVector, N).GetSafeNormal();
	// flames: a cluster of additive glow spheres hugging the facade, bigger at the bottom
	for (int32 i = 0; i < 9; ++i)
	{
		const double Up = R.FRandRange(-150.0, 450.0), Side = R.FRandRange(-400.0, 400.0);
		const FVector P = E.SiteCm + T * Side + FVector(0, 0, Up) + N * R.FRandRange(20.0, 160.0);
		const float SizeM = float(R.FRandRange(1.6, 3.2) * (1.0 - 0.25 * FMath::Clamp(Up / 450.0, 0.0, 1.0)));
		UStaticMeshComponent* F = AddMesh(E, Sphere, MGlow, FLinearColor(3.0f, 1.1f, 0.2f), P, FRotator::ZeroRotator, FVector(SizeM), 0.f, 0.8f);
		E.Flames.Add(F); E.FlameBaseCm.Add(P); E.FlameBaseM.Add(SizeM);
	}
	// smoke: dark translucent puffs rising above the flames
	for (int32 i = 0; i < 4; ++i)
	{
		const FVector P = E.SiteCm + T * R.FRandRange(-300.0, 300.0) + N * 250.0 + FVector(0, 0, 650.0 + i * 280.0);
		const double S = 3.0 + i * 0.9;
		AddMesh(E, Sphere, MTrans, FLinearColor(0.05f, 0.045f, 0.04f), P, FRotator::ZeroRotator, FVector(S, S, S * 0.8), 0.f, 0.35f - 0.05f * i);
	}
	// trapped people: dark figures on a ledge beside the fire, PeoplePerBatch per batch
	for (int32 b = 0; b < E.BatchLives.Num(); ++b)
		for (int32 j = 0; j < PeoplePerBatch; ++j)
		{
			const double Side = 520.0 + b * 170.0 + j * 65.0;   // beside the flames, in groups
			const FVector P = E.SiteCm + T * Side + N * 120.0 + FVector(0, 0, -60.0);
			E.People.Add(AddMesh(E, Cylinder, MSolid, FLinearColor(0.08f, 0.07f, 0.07f), P, FRotator::ZeroRotator, FVector(0.45, 0.45, 1.75)));
		}
	E.Light = AddLight(E, E.SiteCm + N * 400.0, FLinearColor(1.0f, 0.45f, 0.12f), 4000.f, 3500.f);
}

void AWHRescueDirector::BuildCrane(FWHEmergency& E, const FVector& MastBase, double MastH, const FVector& TipCm)
{
	const FLinearColor Yellow(0.85f, 0.55f, 0.04f), Steel(0.25f, 0.27f, 0.3f), Concrete(0.35f, 0.34f, 0.32f);
	const FVector Dir = E.OutDir;
	const FRotator Yaw(0.0, Dir.Rotation().Yaw, 0.0);
	const FVector Top = MastBase + FVector(0, 0, MastH);
	// mast
	AddMesh(E, Cube, MSolid, Yellow, MastBase + FVector(0, 0, MastH * 0.5), Yaw, FVector(1.4, 1.4, MastH / 100.0));
	// jib (from the counter-jib end to the tip) + counterweight + cab
	const double JibLen = FVector::Dist2D(Top, TipCm) + 600.0;
	const FVector JibMid = (Top - Dir * 600.0 + FVector(TipCm.X, TipCm.Y, Top.Z)) * 0.5 + FVector(0, 0, 60.0);
	AddMesh(E, Cube, MSolid, Yellow, JibMid, Yaw, FVector(JibLen / 100.0, 1.0, 1.0));
	AddMesh(E, Cube, MSolid, Concrete, Top - Dir * 520.0 + FVector(0, 0, -80.0), Yaw, FVector(2.2, 2.0, 1.8));
	AddMesh(E, Cube, MSolid, Steel, Top + Dir * 120.0 + FVector(0, 0, -120.0), Yaw, FVector(1.6, 1.6, 1.4), 0.3f);
	// cable + load (a steel bundle)
	E.Cable = AddMesh(E, Cylinder, MSolid, FLinearColor(0.05f, 0.05f, 0.05f), (TipCm + E.LoadCm) * 0.5, FRotator::ZeroRotator,
		FVector(0.06, 0.06, (TipCm.Z - E.LoadCm.Z) / 100.0));
	E.Load = AddMesh(E, Cube, MSolid, Steel, E.LoadCm, Yaw, FVector(4.0, 1.8, 1.5));
	E.LoadQ = Yaw.Quaternion();   // critic r2 (round 3 hero): the load's rotation is tracked from here on (it turns with the hero while carried)
	// a red warning beacon at the tip
	AddMesh(E, Sphere, MGlow, FLinearColor(4.0f, 0.2f, 0.1f), TipCm + FVector(0, 0, 90.0), FRotator::ZeroRotator, FVector(0.5), 0.f, 0.9f);
}

void AWHRescueDirector::BuildBus(FWHEmergency& E, const FVector& EdgeCm)
{
	// pivot at the edge; the bus (12 x 2.6 x 3 m) lies along +X of the pivot, its centre 0.8 m past the edge: teetering
	USceneComponent* Root = NewObject<USceneComponent>(this);
	Root->SetMobility(EComponentMobility::Movable);
	Root->SetUsingAbsoluteLocation(true); Root->SetUsingAbsoluteRotation(true); Root->SetUsingAbsoluteScale(true);
	Root->SetupAttachment(GetRootComponent());
	Root->RegisterComponent();
	E.BusRestRot = FRotator(-5.0, E.OutDir.Rotation().Yaw, 0.0);
	Root->SetWorldLocationAndRotation(EdgeCm, E.BusRestRot);
	E.BusRoot = Root;
	E.Parts.Add(Root);

	const FLinearColor Paint(0.95f, 0.5f, 0.03f), Glass(0.03f, 0.04f, 0.05f), Tyre(0.02f, 0.02f, 0.02f);
	const double Cx = 80.0, Cz = 190.0;
	AddMesh(E, Cube, MSolid, Paint, FVector(Cx, 0, Cz), FRotator::ZeroRotator, FVector(12.0, 2.6, 2.8), 0.f, 1.f, Root);
	AddMesh(E, Cube, MSolid, Glass, FVector(Cx + 20.0, 0, Cz + 55.0), FRotator::ZeroRotator, FVector(11.2, 2.66, 0.9), 0.f, 1.f, Root);
	AddMesh(E, Cube, MSolid, Glass, FVector(Cx + 601.0, 0, Cz + 20.0), FRotator::ZeroRotator, FVector(0.05, 2.3, 1.4), 0.f, 1.f, Root);
	for (int32 i = 0; i < 4; ++i)
	{
		const double X = Cx + (i < 2 ? 380.0 : -380.0), Y = (i % 2 == 0) ? 120.0 : -120.0;
		AddMesh(E, Cylinder, MSolid, Tyre, FVector(X, Y, 50.0), FRotator(0.0, 0.0, 90.0), FVector(1.0, 1.0, 0.35), 0.f, 1.f, Root);
	}
	// hazard flashers (front corners)
	E.Flames.Add(AddMesh(E, Sphere, MGlow, FLinearColor(4.0f, 1.8f, 0.1f), FVector(Cx + 605.0, 110.0, Cz - 90.0), FRotator::ZeroRotator, FVector(0.3), 0.f, 0.9f, Root));
	E.Flames.Add(AddMesh(E, Sphere, MGlow, FLinearColor(4.0f, 1.8f, 0.1f), FVector(Cx + 605.0, -110.0, Cz - 90.0), FRotator::ZeroRotator, FVector(0.3), 0.f, 0.9f, Root));
}

void AWHRescueDirector::Burst(const FVector& PosCm, double SizeM)
{
	FWHEmergency Dummy;   // only for AddMesh's bookkeeping; the puffs live in Puffs
	for (int32 i = 0; i < 10; ++i)
	{
		const FVector D = (Rng.GetUnitVector() * FVector(1.0, 1.0, 0.4) + FVector(0, 0, 0.5)).GetSafeNormal();
		FPuff P;
		P.C = AddMesh(Dummy, Sphere, MTrans, FLinearColor(0.16f, 0.15f, 0.13f), PosCm + D * 100.0, FRotator::ZeroRotator, FVector(SizeM * 0.4), 0.f, 0.5f);
		P.Vel = D * Rng.FRandRange(300.0, 900.0) * SizeM * 0.4;
		P.Life = Rng.FRandRange(1.4, 2.4);
		P.Size = SizeM;
		Puffs.Add(P);
	}
}

void AWHRescueDirector::DestroyVisuals(FWHEmergency& E)
{
	for (USceneComponent* C : E.Parts)
		if (IsValid(C)) C->DestroyComponent();
	E.Parts.Reset(); E.Flames.Reset(); E.FlameBaseCm.Reset(); E.FlameBaseM.Reset(); E.People.Reset();
	E.Load = nullptr; E.Cable = nullptr; E.BusRoot = nullptr; E.Light = nullptr;
}

// ------------------------------------------------------------------------------------------------------------------------ score

void AWHRescueDirector::SaveLives(FWHEmergency& E, int32 N, const TCHAR* Why)
{
	N = FMath::Clamp(N, 0, E.LivesAtStake);
	if (N <= 0) return;
	E.LivesAtStake -= N; E.LivesSaved += N;
	UWHFlightWorldSubsystem* S = Sub();
	if (S) S->LivesSaved += N;
	UE_LOG(LogWebHomage, Display, TEXT("WH_RESCUE saved id %d type %s +%d (%s) total saved %d"), E.Id, TypeName(E.Type), N, Why, S ? S->LivesSaved : 0);
}

void AWHRescueDirector::LoseLives(FWHEmergency& E, int32 N, const TCHAR* Why)
{
	N = FMath::Clamp(N, 0, E.LivesAtStake);
	if (N <= 0) return;
	E.LivesAtStake -= N; E.LivesLost += N;
	UWHFlightWorldSubsystem* S = Sub();
	if (S) S->LivesLost += N;
	UE_LOG(LogWebHomage, Display, TEXT("WH_RESCUE lost id %d type %s -%d (%s) total lost %d"), E.Id, TypeName(E.Type), N, Why, S ? S->LivesLost : 0);
}

void AWHRescueDirector::Resolve(FWHEmergency& E, EWHEmergencyState NewState, double Now, const TCHAR* Why)
{
	if (E.State != EWHEmergencyState::Active) return;
	E.State = NewState;
	E.ResolvedT = Now;
	E.HoldProgress = 0; E.HoldT = 0; E.bHeroInRange = false;
	E.RemainingS = FMath::Max(0.0, E.EndT - Now);
	UE_LOG(LogWebHomage, Display, TEXT("WH_RESCUE resolved id %d type %s result %s (%s) saved %d lost %d clock left %.1f s"),
		E.Id, TypeName(E.Type), NewState == EWHEmergencyState::Saved ? TEXT("saved") : TEXT("lost"), Why, E.LivesSaved, E.LivesLost, E.RemainingS);
}

// ------------------------------------------------------------------------------------------------------------------------ tick

void AWHRescueDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bEnabled) return;
	UWorld* W = GetWorld();
	if (!W) return;
	UWHFlightWorldSubsystem* S = Sub();
	if (S && !S->bFlightMode && !bStarted) return;   // the legacy web-swing hero: stay dormant
	const double Now = W->GetTimeSeconds();
	const double Dt = FMath::Min(double(DeltaSeconds), 0.1);

	// impact puffs
	for (int32 i = Puffs.Num() - 1; i >= 0; --i)
	{
		FPuff& P = Puffs[i];
		P.T += Dt;
		if (!IsValid(P.C) || P.T >= P.Life)
		{
			if (IsValid(P.C)) P.C->DestroyComponent();
			Puffs.RemoveAtSwap(i);
			continue;
		}
		P.Vel *= FMath::Exp(-1.6 * Dt);
		P.C->SetWorldLocation(P.C->GetComponentLocation() + P.Vel * Dt);
		const double K = P.T / P.Life;
		P.C->SetWorldScale3D(FVector(P.Size * (0.4 + 1.4 * K)));
		SetGlow(P.C, FLinearColor(0.16f, 0.15f, 0.13f), float(0.5 * (1.0 - K)));
	}

	// waves
	if (NextWaveT >= 0 && Now >= NextWaveT)
	{
		++SpawnAttempts;
		if (SpawnWave(SpawnAttempts >= 6)) { NextWaveT = -1; SpawnAttempts = 0; bStarted = true; }
		else NextWaveT = Now + 1.5;   // the procedural city may still be building: retry
	}

	const FVector Hero = HeroPos();
	const bool bHover = !S || S->HeroVelCm.Size() < MaxHoverSpeedCm;
	for (FWHEmergency& E : Emergencies)
	{
		if (E.State == EWHEmergencyState::Active)
		{
			E.RemainingS = FMath::Max(0.0, E.EndT - Now);
			if (S && Now >= E.NextStimT)
			{
				S->PushStimulus(EWHCrowdStimulus::Emergency, E.DangerCm, StimulusRadiusCm, 1.f, StimulusEveryS + 1.f);
				E.NextStimT = Now + StimulusEveryS;
			}
		}
		switch (E.Type)
		{
		case EWHEmergencyType::Fire:  TickFire(E, Now, Dt, Hero, bHover); break;
		case EWHEmergencyType::Crane: TickCrane(E, Now, Dt, Hero); break;
		case EWHEmergencyType::Bus:   TickBus(E, Now, Dt, Hero, bHover); break;
		}
	}

	// remove resolved emergencies after they lingered (a carried load stays until it is set down)
	bool bAnyActive = false;
	for (int32 i = Emergencies.Num() - 1; i >= 0; --i)
	{
		FWHEmergency& E = Emergencies[i];
		if (E.State == EWHEmergencyState::Active) { bAnyActive = true; continue; }
		if (E.bCarried || E.bSettling) continue;
		if (E.Type == EWHEmergencyType::Bus && E.State == EWHEmergencyState::Lost && !E.bLanded) continue;   // still falling
		if (Now - E.ResolvedT > LingerS) { DestroyVisuals(E); Emergencies.RemoveAt(i); }
	}
	if (bStarted && !bAnyActive && NextWaveT < 0)
	{
		NextWaveT = Now + WaveGapS;
		const UWHFlightWorldSubsystem* SS = Sub();
		UE_LOG(LogWebHomage, Display, TEXT("WH_RESCUE wave %d clear: saved %d lost %d total, next wave in %.0f s"), Wave, SS ? SS->LivesSaved : 0, SS ? SS->LivesLost : 0, WaveGapS);
	}
}

void AWHRescueDirector::TickFire(FWHEmergency& E, double Now, double Dt, const FVector& Hero, bool bHover)
{
	const UWHFlightWorldSubsystem* S = Sub();
	if (E.State == EWHEmergencyState::Active)
	{
		E.bHeroInRange = FVector::Dist(Hero, E.SiteCm) < FireRangeCm;
		const bool bHeld = S && S->bInteractHeld;
		if (E.bHeroInRange && bHeld && bHover) E.HoldT += Dt;
		else E.HoldT = FMath::Max(0.0, E.HoldT - 2.0 * Dt);
		E.HoldProgress = FMath::Clamp(E.HoldT / FireBatchHoldS, 0.0, 1.0);
		if (E.HoldT >= FireBatchHoldS && E.BatchLives.IsValidIndex(E.Batch))
		{
			SaveLives(E, E.BatchLives[E.Batch], TEXT("evacuated a group"));
			for (int32 j = 0; j < PeoplePerBatch; ++j)
				if (E.People.IsValidIndex(E.Batch * PeoplePerBatch + j) && E.People[E.Batch * PeoplePerBatch + j])
					E.People[E.Batch * PeoplePerBatch + j]->SetVisibility(false);
			++E.Batch;
			E.HoldT = 0; E.HoldProgress = 0;
			UE_LOG(LogWebHomage, Display, TEXT("WH_RESCUE fire id %d batch %d/%d out"), E.Id, E.Batch, E.BatchLives.Num());
			if (E.Batch >= E.BatchLives.Num()) Resolve(E, EWHEmergencyState::Saved, Now, TEXT("everyone out"));
		}
		if (E.State == EWHEmergencyState::Active && Now >= E.EndT)
		{
			LoseLives(E, E.LivesAtStake, TEXT("the fire spread"));
			Resolve(E, EWHEmergencyState::Lost, Now, TEXT("clock ran out"));
		}
	}

	// flicker; saved: the fire dies down over 3 s; lost: it keeps burning, a little lower
	double K = 1.0 - 0.15 * E.Batch;
	if (E.State == EWHEmergencyState::Saved) K *= 1.0 - Ease((Now - E.ResolvedT) / 3.0);
	else if (E.State == EWHEmergencyState::Lost) K *= 0.75;
	for (int32 i = 0; i < E.Flames.Num(); ++i)
	{
		UStaticMeshComponent* F = E.Flames[i];
		if (!F) continue;
		const double Fl = 0.8 + 0.12 * FMath::Sin(Now * (7.0 + i * 1.3) + i * 2.1) + 0.08 * FMath::Sin(Now * (17.0 + i * 0.7) + i);
		const double Sz = E.FlameBaseM[i] * K * Fl;
		F->SetVisibility(Sz > 0.05);
		F->SetWorldLocation(E.FlameBaseCm[i] + FVector(0, 0, 40.0 * FMath::Sin(Now * 3.0 + i)));
		F->SetWorldScale3D(FVector(Sz, Sz, Sz * 1.25));
		SetGlow(F, FLinearColor(3.0f, float(0.9 + 0.35 * Fl), 0.2f), float(0.8 * Fl));
	}
	if (E.Light)
	{
		const double Fl = 0.85 + 0.15 * FMath::Sin(Now * 11.0) * FMath::Sin(Now * 4.3 + 1.0);
		E.Light->SetIntensity(float(4000.0 * K * Fl));
	}
}

void AWHRescueDirector::TickCrane(FWHEmergency& E, double Now, double Dt, const FVector& Hero)
{
	UWHFlightWorldSubsystem* S = Sub();
	if (E.State == EWHEmergencyState::Active)
	{
		if (!E.bSnapped)
		{
			// the load sways on its cable; it snaps loose so the impact lands on the clock's zero
			const double Sway = 1.0 + 3.0 * FMath::Clamp(1.0 - (E.SnapAtT - Now) / 20.0, 0.0, 1.0);   // more violent near the snap
			E.LoadCm = E.LoadRestCm + E.OutDir * (12.0 * Sway * FMath::Sin(Now * 1.3)) + FVector(0, 0, 4.0 * Sway * FMath::Sin(Now * 2.6));
			if (Now >= E.SnapAtT)
			{
				E.bSnapped = true; E.SnapT = Now;
				UE_LOG(LogWebHomage, Display, TEXT("WH_RESCUE crane id %d load snapped, %.1f s to impact"), E.Id, E.EndT - Now);
				if (S) S->PushStimulus(EWHCrowdStimulus::Emergency, E.DangerCm, StimulusRadiusCm * 1.3f, 1.f, 4.f);
			}
		}
		else if (Now - E.SnapT < CraneJoltS)
		{
			// a short jolt: the load drops a little and swings
			const double J = (Now - E.SnapT) / CraneJoltS;
			E.LoadCm = E.LoadRestCm + FVector(0, 0, -60.0 * J) + E.OutDir * (30.0 * FMath::Sin(J * 18.0));
		}
		else
		{
			E.bFalling = true;
			E.LoadVelCm.Z -= CraneFallGravity * Dt;
			E.LoadCm += E.LoadVelCm * Dt;
			if (E.LoadCm.Z - 75.0 <= E.StreetZ)
			{
				E.LoadCm.Z = E.StreetZ + 75.0;
				E.bFalling = false; E.bLanded = true;
				LoseLives(E, E.LivesAtStake, TEXT("crushed by the load"));
				if (S)
				{
					S->PushStimulus(EWHCrowdStimulus::Impact, E.LoadCm, 3000.f, 1.f, 5.f);
					S->AddCollateral(350000.f, TEXT("crane load hit the street"));
				}
				Burst(E.LoadCm, 3.0);
				Resolve(E, EWHEmergencyState::Lost, Now, TEXT("the load hit the street"));
			}
		}
		// catch: touch the load any time before it lands
		// r5 (critic r4 #6, fl17 "he stands on the load"; overhead-carry hero only): caught from below / beside at CraneTouchCm; with the hero
		// above the load (his feet over its top face) only at CraneTouchAboveCm, i.e. just before he would reach it -- the hero's anim then
		// swings it round his front onto his raised fists (UWHHeroV2AnimInstance, SetCarryAnchor), so he is never set standing on it.
		if (E.State == EWHEmergencyState::Active)
		{
			const double D = FVector::Dist(Hero, E.LoadCm);
			const double LoadHalfZ = E.Load ? E.Load->GetComponentScale().Z * 50.0 : 75.0;
			const bool bAbove = bOverheadCarry && Hero.Z - E.LoadCm.Z > LoadHalfZ + 95.0;   // hero centre over the top face + his feet-to-centre height
			E.bHeroInRange = D < CraneTouchCm * 2.0;
			if (D < (bAbove ? FMath::Min(double(CraneTouchAboveCm), double(CraneTouchCm)) : double(CraneTouchCm)))
			{
				E.bCarried = true; E.bFalling = false; E.CarryT = 0;
				E.LoadVelCm = FVector::ZeroVector;
				if (bOverheadCarry)
				{
					UE_LOG(LogWebHomage, Display, TEXT("WH_RESCUE crane id %d load caught %s at %.0f m above the street from %s (%.1f m)"), E.Id, E.bSnapped ? TEXT("falling") : TEXT("hanging"),
						(E.LoadCm.Z - E.StreetZ) / 100.0, bAbove ? TEXT("above") : TEXT("below / beside"), D / 100.0);
				}
				else
				{
					UE_LOG(LogWebHomage, Display, TEXT("WH_RESCUE crane id %d load caught %s at %.0f m above the street"), E.Id, E.bSnapped ? TEXT("falling") : TEXT("hanging"), (E.LoadCm.Z - E.StreetZ) / 100.0);
				}
				// r5 (critic r4 fl17: "lives saved jumps to 5 at 17.61 s mid-air rather than on set-down"): overhead carry counts on the set-down
				if (!bOverheadCarry) SaveLives(E, E.LivesAtStake, TEXT("load caught"));
				Resolve(E, EWHEmergencyState::Saved, Now, TEXT("load caught"));
			}
		}
		// safety: never let the clock run past zero without an outcome
		if (E.State == EWHEmergencyState::Active && Now > E.EndT + 8.0)
		{
			LoseLives(E, E.LivesAtStake, TEXT("load fell"));
			Resolve(E, EWHEmergencyState::Lost, Now, TEXT("clock ran out"));
		}
	}
	else if (E.bCarried)
	{
		// carried under the hero; interact (after a beat) or 10 s sets it down gently on the ground below
		E.CarryT += Dt;
		// critic r2 (fl17 17.0 s: "the hero standing / sitting on top of the box, no grip"; 18.4-20.4 s: "the load is nowhere in frame during
		// the carry dive"): the load is held in the hero's hands -- his anim instance publishes its place in the hero mesh's component
		// space every frame (overhead / ahead of the head, turning with his body), rendered here in the same frame. The r1 placement below
		// (world-down offset under the body centre, smoothed: he stood on it, and it lagged out of frame at dive speed) is only the fallback
		// when no fresh anchor exists.
		const USceneComponent* HeroMesh = CarryMesh.Get();
		if (HeroMesh && CarryAnchorT >= 0.0 && Now - CarryAnchorT < 0.2)
		{
			const FTransform Held = CarryInMesh * HeroMesh->GetComponentTransform();
			E.LoadCm = Held.GetLocation();
			E.LoadQ = Held.GetRotation().GetNormalized();
		}
		else
		{
			const FVector Want = Hero - FVector(0, 0, 170.0);   // critic r1 (fl17: never visibly held): top of the load at his hands, not 2.5 m below
			E.LoadCm = FMath::Lerp(E.LoadCm, Want, float(1.0 - FMath::Exp(-10.0 * Dt)));
		}
		const bool bDrop = (S && S->bInteractPressed && E.CarryT > 0.4) || E.CarryT > 10.0;
		if (bDrop)
		{
			// critic r2 (fl17; test: "the set-down leaves the load resting on the surface below with the hero landing beside it, not on top"):
			// the load is levelled to its heading (the hero's facing), slid clear ahead of the hero (near face SetDownClearCm ahead of his
			// centre, so a straight descent lands him beside it) and rests on the HIGHEST surface under its footprint (centre + 4 corners;
			// it never sinks into a step or a roof edge). r1/r2: straight down under the load centre at 9 m/s.
			const FVector HalfCm = E.Load ? E.Load->GetComponentScale() * 50.0 : FVector(200.0, 90.0, 75.0);
			FVector FwdH = Flat(E.LoadQ.GetAxisY());                      // the load's depth axis = the hero's body forward while carried
			if (FwdH.Size() < 0.3) FwdH = Flat(E.LoadQ.GetAxisZ());       // carried on the fly line: body up = the travel
			if (FwdH.Size() < 0.3) FwdH = Flat(E.LoadCm - Hero);
			FwdH = FwdH.Size() > 1e-3 ? FwdH.GetSafeNormal() : E.OutDir;
			const FVector SideH = FVector::CrossProduct(FVector::UpVector, FwdH).GetSafeNormal();
			const FVector C = Flat(Hero) + FwdH * (double(SetDownClearCm) + HalfCm.Y);
			const double TopZ = FMath::Max(E.LoadCm.Z, Hero.Z) + 100.0;
			double RestZ = -TNumericLimits<double>::Max();
			const double Px[5] = { 0.0, 0.9, 0.9, -0.9, -0.9 }, Py[5] = { 0.0, 0.9, -0.9, 0.9, -0.9 };
			for (int32 k = 0; k < 5; ++k)
			{
				FVector G;
				const FVector P = C + SideH * (Px[k] * HalfCm.X) + FwdH * (Py[k] * HalfCm.Y);
				if (GroundAt(P, TopZ, TopZ - 100000.0, G)) RestZ = FMath::Max(RestZ, G.Z);
			}
			if (RestZ <= -TNumericLimits<double>::Max()) RestZ = E.StreetZ;
			E.SettleCm = FVector(C.X, C.Y, RestZ + HalfCm.Z);
			E.SettleQ = FRotationMatrix::MakeFromYZ(FwdH, FVector::UpVector).ToQuat();
			E.SettleFromCm = E.LoadCm; E.SettleFromQ = E.LoadQ; E.SettleT = 0.0;
			E.SettleDur = FMath::Clamp(FMath::Abs(E.SettleFromCm.Z - E.SettleCm.Z) / FMath::Max(100.0, double(SetDownSpeedCm)), 0.6, 4.0);
			E.bCarried = false; E.bSettling = true;
			UE_LOG(LogWebHomage, Display, TEXT("WH_RESCUE crane id %d load set down at (%.0f, %.0f, %.0f) over %.1f s, hero at (%.0f, %.0f, %.0f)"),
				E.Id, E.SettleCm.X, E.SettleCm.Y, E.SettleCm.Z, E.SettleDur, Hero.X, Hero.Y, Hero.Z);
			SaveLives(E, E.LivesAtStake, TEXT("load set down"));   // r5: overhead carry counts here (v1: already 0 at stake since the catch)
		}
	}
	else if (E.bSettling)
	{
		// critic r2 (fl17): an eased set-down -- clear of the hero and levelled within 0.6 s, lowered onto the rest surface over SettleDur
		// (ease in-out: it touches down slowly). r2: a linear 9 m/s slide to the point under the load.
		E.SettleT += Dt;
		const double Kxy = Ease(E.SettleT / 0.6);
		const double Kz = Ease(E.SettleT / FMath::Max(0.3, E.SettleDur));
		E.LoadCm = FVector(FMath::Lerp(E.SettleFromCm.X, E.SettleCm.X, Kxy), FMath::Lerp(E.SettleFromCm.Y, E.SettleCm.Y, Kxy), FMath::Lerp(E.SettleFromCm.Z, E.SettleCm.Z, Kz));
		E.LoadQ = FQuat::Slerp(E.SettleFromQ, E.SettleQ, Kxy).GetNormalized();
		if (E.SettleT >= FMath::Max(0.6, E.SettleDur))
		{
			E.LoadCm = E.SettleCm; E.LoadQ = E.SettleQ; E.bSettling = false; E.ResolvedT = Now;
			UE_LOG(LogWebHomage, Display, TEXT("WH_RESCUE crane id %d load rests at (%.0f, %.0f, %.0f)"), E.Id, E.LoadCm.X, E.LoadCm.Y, E.LoadCm.Z);
		}
	}

	E.FocusCm = E.LoadCm;
	if (E.Load) E.Load->SetWorldLocationAndRotation(E.LoadCm, E.LoadQ);   // critic r2: + rotation (r2: SetWorldLocation only)
	if (E.Cable)
	{
		const bool bShow = !E.bSnapped && E.State == EWHEmergencyState::Active;
		E.Cable->SetVisibility(bShow);
		if (bShow)
		{
			const FVector Top = E.TipCm, Bot = E.LoadCm + FVector(0, 0, 75.0);
			const FVector D = Top - Bot;
			E.Cable->SetWorldLocationAndRotation((Top + Bot) * 0.5, FQuat::FindBetweenNormals(FVector::UpVector, D.GetSafeNormal()));
			E.Cable->SetWorldScale3D(FVector(0.06, 0.06, D.Size() / 100.0));
		}
	}
}

void AWHRescueDirector::TickBus(FWHEmergency& E, double Now, double Dt, const FVector& Hero, bool bHover)
{
	UWHFlightWorldSubsystem* S = Sub();
	FRotator Rot = E.BusRestRot;
	FVector Pivot = E.SiteCm;
	if (E.State == EWHEmergencyState::Active)
	{
		// distance to the bus's long axis (+-5 m around its centre)
		const FVector C = E.SiteCm + E.OutDir * 80.0 + FVector(0, 0, 160.0);
		const FVector Closest = FMath::ClosestPointOnSegment(Hero, C - E.OutDir * 500.0, C + E.OutDir * 500.0);
		E.bHeroInRange = FVector::Dist(Hero, Closest) < BusRangeCm;
		const bool bHeld = S && S->bInteractHeld;
		if (E.bHeroInRange && bHeld && bHover) E.HoldT += Dt;
		else E.HoldT = FMath::Max(0.0, E.HoldT - 2.0 * Dt);
		E.HoldProgress = FMath::Clamp(E.HoldT / BusHoldS, 0.0, 1.0);

		// teeter: worse as the clock runs down; steadier while the hero holds it
		const double Urgency = FMath::Clamp(1.0 - E.RemainingS / FMath::Max(1.0, E.DurationS), 0.0, 1.0);
		const double Amp = (1.5 + 5.0 * Urgency) * (1.0 - 0.8 * E.HoldProgress);
		Rot.Pitch = E.BusRestRot.Pitch - 4.0 * Urgency * (1.0 - E.HoldProgress) + Amp * FMath::Sin(Now * (1.7 + 1.5 * Urgency));
		Rot.Pitch += 5.0 * E.HoldProgress;   // the hero lifts the overhang

		if (E.HoldT >= BusHoldS)
		{
			SaveLives(E, E.LivesAtStake, TEXT("bus pulled back"));
			Resolve(E, EWHEmergencyState::Saved, Now, TEXT("bus pulled back"));
		}
		else if (Now >= E.EndT)
		{
			Resolve(E, EWHEmergencyState::Lost, Now, TEXT("clock ran out"));
			// the lives are lost when the bus lands (below)
		}
	}
	if (E.State == EWHEmergencyState::Saved)
	{
		// pulled back onto the deck over 1.5 s, level
		E.PullT += Dt;
		const double K = Ease(E.PullT / 1.5);
		Pivot = E.SiteCm - E.OutDir * (650.0 * K);
		Rot.Pitch = FMath::Lerp(E.BusRestRot.Pitch, 0.0, K);
	}
	else if (E.State == EWHEmergencyState::Lost && E.bGeometry && E.SiteCm.Z - E.BelowZ > 300.0)
	{
		// tips over the edge and falls; on landing the passengers are lost
		if (!E.bLanded)
		{
			E.FallT += Dt;
			const double T = E.FallT;
			Pivot = E.SiteCm + E.OutDir * (250.0 * T) - FVector(0, 0, 0.5 * 980.0 * T * T);
			Rot.Pitch = E.BusRestRot.Pitch - FMath::Min(70.0, 90.0 * T);
			if (Pivot.Z <= E.BelowZ + 100.0)
			{
				E.bLanded = true;
				LoseLives(E, E.LivesAtStake, TEXT("bus fell"));
				if (S)
				{
					S->PushStimulus(EWHCrowdStimulus::Impact, FVector(Pivot.X, Pivot.Y, E.BelowZ), 3500.f, 1.f, 5.f);
					S->AddCollateral(450000.f, TEXT("bus fell"));
				}
				Burst(FVector(Pivot.X, Pivot.Y, E.BelowZ + 100.0), 4.0);
				UE_LOG(LogWebHomage, Display, TEXT("WH_RESCUE bus id %d hit the ground"), E.Id);
			}
		}
		if (E.bLanded)
		{
			const double T = E.FallT;
			Pivot = E.SiteCm + E.OutDir * (250.0 * T);
			Pivot.Z = E.BelowZ + 100.0;
			Rot.Pitch = E.BusRestRot.Pitch - FMath::Min(70.0, 90.0 * T);
		}
	}
	else if (E.State == EWHEmergencyState::Lost && !E.bLanded)
	{
		// fallback site (no real drop): the bus slumps; the passengers are lost
		E.bLanded = true;
		LoseLives(E, E.LivesAtStake, TEXT("bus fell"));
		if (S) S->AddCollateral(250000.f, TEXT("bus wrecked"));
		Burst(E.SiteCm + FVector(0, 0, 100.0), 3.0);
	}
	if (E.State == EWHEmergencyState::Lost && !E.bGeometry) Rot.Pitch = E.BusRestRot.Pitch - 12.0;

	if (E.BusRoot) E.BusRoot->SetWorldLocationAndRotation(Pivot, Rot);
	E.FocusCm = Pivot + Rot.RotateVector(FVector(80.0, 0.0, 190.0));
	// hazard flashers blink
	const bool bOn = FMath::Frac(Now * 1.4) < 0.5 && E.State == EWHEmergencyState::Active;
	for (UStaticMeshComponent* F : E.Flames) if (F) F->SetVisibility(bOn);
}
