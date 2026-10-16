// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
// Invincible flight conversion (owner request 2026-10-15). See WHBreachDirector.h.
#include "Flight/WHBreachDirector.h"
#include "Flight/WHFlightWorld.h"
#include "WebHomage.h"
#include "Components/StaticMeshComponent.h"
#include "Components/DecalComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/Material.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "GameFramework/Pawn.h"
#include "StaticMeshResources.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundWaveProcedural.h"
#include "GeometryCollection/GeometryCollectionActor.h"
#include "GeometryCollection/GeometryCollectionComponent.h"
#include "GeometryCollection/GeometryCollectionObject.h"
#include "HAL/PlatformTime.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace
{
	const FName NB_breachIn(TEXT("breachIn")), NB_breachOut(TEXT("breachOut")), NB_heroLand(TEXT("heroLand")), NB_sonicBoom(TEXT("sonicBoom")),
		NB_flyBump(TEXT("flyBump")), NB_takeoff(TEXT("takeoff"));
	// owner feedback 2026-10-15 #1: super-boost charge start (Severity = slow-mo dilation, K = real charge seconds)
	const FName NB_superCharge(TEXT("superCharge"));
	const FLinearColor BdConcrete(0.42f, 0.40f, 0.37f), BdBrick(0.38f, 0.22f, 0.16f), BdSteel(0.20f, 0.21f, 0.23f), BdScorch(0.025f, 0.022f, 0.02f);
	// r3: dust / rubble tones (linear): concrete dust, brick dust, dark asphalt
	const FLinearColor BdDust(0.34f, 0.31f, 0.27f), BdBrickDust(0.36f, 0.28f, 0.22f), BdAsphalt(0.075f, 0.075f, 0.08f);
	FVector BdAnyPerp(const FVector& N) { return FVector::CrossProduct(N, FMath::Abs(N.Z) < 0.9 ? FVector::UpVector : FVector::ForwardVector).GetSafeNormal(); }
	/** owner feedback 2026-10-15: a unit vector perpendicular to D at angle A around it */
	FVector BdRingDir(const FVector& D, double A)
	{
		const FVector P = BdAnyPerp(D), Q = FVector::CrossProduct(D, P);
		return P * FMath::Cos(A) + Q * FMath::Sin(A);
	}
	double BdSmooth01(double X) { X = FMath::Clamp(X, 0.0, 1.0); return X * X * (3.0 - 2.0 * X); }
	double BdEaseOut(double K) { K = FMath::Clamp(K, 0.0, 1.0); return 1.0 - (1.0 - K) * (1.0 - K); }
	/** in-plane axes of a surface with normal N: U horizontal, V up-ish (a wall); any perpendicular pair for floors / roofs */
	void BdPlaneBasis(const FVector& N, FVector& U, FVector& V)
	{
		if (FMath::Abs(N.Z) > 0.92) { U = BdAnyPerp(N); V = FVector::CrossProduct(N, U).GetSafeNormal(); return; }
		U = FVector::CrossProduct(FVector::UpVector, N).GetSafeNormal();
		V = FVector::CrossProduct(N, U).GetSafeNormal();
		if (V.Z < 0.0) V = -V;
	}
	/** r3: a surface material a debris cube can wear: opaque / masked surface materials of a game material (never the engine's defaults, glass, decals, post process) */
	bool BdDebrisMaterialOk(UMaterialInterface* M)
	{
		if (!M) return false;
		const UMaterial* B = M->GetMaterial();
		if (!B || B->MaterialDomain != MD_Surface) return false;
		const EBlendMode BM = M->GetBlendMode();
		if (BM != BLEND_Opaque && BM != BLEND_Masked) return false;
		return !B->GetPathName().StartsWith(TEXT("/Engine/"));
	}
}

AWHBreachDirector::AWHBreachDirector()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bTickEvenWhenPaused = false;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

void AWHBreachDirector::BeginPlay()
{
	Super::BeginPlay();
	Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	Cyl = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	Sphere = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	MSolid = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbSolid.M_CmbSolid"));
	MTrans = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbTrans.M_CmbTrans"));
	MGlow = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbFX.M_CmbFX"));
	if (!MSolid) MSolid = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	MDecal = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Invincible/FX/M_CraterDecal.M_CraterDecal"));
	// critic r2 round 3: the FX assets of Scripts/build_invincible_fx.py (each optional; the r2 proxies are the fallback)
	MHole = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Invincible/FX/M_BreachHole.M_BreachHole"));
	MVapour = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Invincible/FX/M_InvVapour.M_InvVapour"));
	MDust = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Invincible/FX/M_InvDust.M_InvDust"));
	MChunk = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Invincible/FX/M_InvChunk.M_InvChunk"));
	// owner feedback 2026-10-15 #1: additive speed-line material (optional; the streaks fall back to M_InvVapour)
	MStreak = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Invincible/FX/M_InvStreak.M_InvStreak"));
	Cone = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cone.Cone"));
	ProbeCone();
	GcAsset = LoadObject<UGeometryCollection>(nullptr, TEXT("/Game/Invincible/Destruction/GC_FacadeChunk.GC_FacadeChunk"));
	bNoSlowMo = FParse::Param(FCommandLine::Get(), TEXT("WHNoSlowMo"));
	bNoAudio = FParse::Param(FCommandLine::Get(), TEXT("WHNoFlightAudio"));
	{ float Fc = FacadeChunkFraction; if (FParse::Value(FCommandLine::Get(), TEXT("-WHFacadeChunks="), Fc)) FacadeChunkFraction = FMath::Clamp(Fc, 0.f, 1.f); }
	Fx.Init(this);
	ExcludeHeroFromDecals();   // r3: the opening / crater decals must not paint the hero when he flies through them
	UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT breach director ready: materials %s, authored fracture %s, crater decal %s, slow-mo %s"),
		MSolid && MTrans ? TEXT("ok") : TEXT("FALLBACK"), GcAsset ? TEXT("yes") : TEXT("no (proxy chunks only)"), MDecal ? TEXT("yes") : TEXT("no (disc)"),
		bNoSlowMo ? TEXT("off") : TEXT("on"));
	UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT breach fx r3: hole decal %s, vapour %s (cone mesh %s, apex %s, %.0f x %.0f cm), dust %s, chunk material %s, facade chunk share %.2f"),
		MHole ? TEXT("yes") : TEXT("no"), MVapour ? TEXT("yes") : TEXT("no (r2 rings)"), Cone ? TEXT("yes") : TEXT("no"), bConeApexUp ? TEXT("+Z") : TEXT("-Z"), ConeWCm, ConeHCm,
		MDust ? TEXT("yes") : TEXT("no (combat puffs)"), MChunk ? TEXT("yes") : TEXT("no (flat tints)"), FacadeChunkFraction);
	UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT flight fx (owner feedback 2026-10-15): streak material %s, vapour pool cap %d"),
		MStreak ? TEXT("M_InvStreak") : (MVapour ? TEXT("M_InvVapour (fallback)") : TEXT("none (no streaks)")), MaxVapours);
}

/** r3: bounds of /Engine/BasicShapes/Cone and which end is the apex (the vapour cone is built from it; its pivot / orientation are not assumed) */
void AWHBreachDirector::ProbeCone()
{
	ConeHCm = 100.0; ConeWCm = 100.0; ConeMidZCm = 0.0; bConeApexUp = true;
	if (!Cone) return;
	const FBox B = Cone->GetBoundingBox();
	if (B.IsValid)
	{
		ConeHCm = FMath::Max(1.0, double(B.Max.Z - B.Min.Z));
		ConeWCm = FMath::Max(1.0, FMath::Max(double(B.Max.X - B.Min.X), double(B.Max.Y - B.Min.Y)));
		ConeMidZCm = 0.5 * double(B.Max.Z + B.Min.Z);
	}
	const FStaticMeshRenderData* RD = Cone->GetRenderData();
	if (RD && RD->LODResources.Num() > 0)
	{
		const FPositionVertexBuffer& PB = RD->LODResources[0].VertexBuffers.PositionVertexBuffer;
		const uint32 NV = PB.GetNumVertices();
		if (NV > 8 && PB.GetAllocatedSize() > 0)   // (CPU copy present: uncooked / editor builds)
		{
			double RadTop = 0.0, RadBot = 0.0; int32 NTop = 0, NBot = 0;
			for (uint32 I = 0; I < NV; ++I)
			{
				const FVector3f P = PB.VertexPosition(I);
				const double R = FMath::Sqrt(double(P.X) * double(P.X) + double(P.Y) * double(P.Y));
				if (double(P.Z) > ConeMidZCm) { RadTop += R; ++NTop; } else { RadBot += R; ++NBot; }
			}
			if (NTop > 0 && NBot > 0) bConeApexUp = (RadTop / NTop) <= (RadBot / NBot);   // the apex end has the smaller mean radius
		}
	}
}

/** r3: decals project onto everything that receives them; the hero flying through a hole decal / standing in a crater decal must not be painted */
void AWHBreachDirector::ExcludeHeroFromDecals()
{
	APawn* Hero = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Hero) return;
	TArray<UPrimitiveComponent*> Comps;
	Hero->GetComponents<UPrimitiveComponent>(Comps);
	for (UPrimitiveComponent* C : Comps) if (C && C->bReceivesDecals) C->SetReceivesDecals(false);
}

void AWHBreachDirector::EndPlay(const EEndPlayReason::Type Reason)
{
	if (bSlowMo || bChargeSlow) UGameplayStatics::SetGlobalTimeDilation(this, 1.f);
	bChargeSlow = false;
	Fx.Clear();
	Super::EndPlay(Reason);
}

UStaticMeshComponent* AWHBreachDirector::MakeComp(UStaticMesh* Mesh, UMaterialInterface* Base, UMaterialInstanceDynamic*& OutMid, bool bShadow)
{
	UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
	C->SetStaticMesh(Mesh);
	C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	C->SetCastShadow(bShadow);
	C->SetReceivesDecals(false);   // r3: debris / dust / vapour never wear the opening and crater decals
	C->SetUsingAbsoluteLocation(true); C->SetUsingAbsoluteRotation(true); C->SetUsingAbsoluteScale(true);
	C->SetupAttachment(RootComponent);
	C->SetMobility(EComponentMobility::Movable);
	C->RegisterComponent();
	OutMid = Base ? UMaterialInstanceDynamic::Create(Base, this) : nullptr;
	if (OutMid) { C->SetMaterial(0, OutMid); KeepAlive.Add(OutMid); }   // (r3: a piece can switch to the facade material; its MID must outlive that)
	C->SetVisibility(false);
	return C;
}

void AWHBreachDirector::OnFlightEvents(const TArray<FWebTravEvent>& Events)
{
	for (const FWebTravEvent& E : Events)
	{
		if (E.Type == NB_breachIn) Breach(E.Pos, E.Dir, E.Severity, true);
		else if (E.Type == NB_breachOut) Breach(E.Pos, E.Dir, E.Severity, false);
		else if (E.Type == NB_heroLand) Crater(E.Pos, E.Severity);
		else if (E.Type == NB_sonicBoom) { EndChargeSlowMo(); Boom(E.Pos, E.Dir); }   // owner feedback #1: the boom ends the charge slow-mo
		else if (E.Type == NB_flyBump) Bump(E.Pos, E.Dir, E.Severity);
		else if (E.Type == NB_takeoff) Fx.Dust(E.Pos, 0.6);
		else if (E.Type == NB_superCharge) ChargeFx(E.Pos, E.Dir, E.Severity, E.K);
	}
}

void AWHBreachDirector::Breach(const FVector& PosM, const FVector& DirM, float Sev, bool bEntry)
{
	const FVector P = PosM * 100.0;
	const FVector D = DirM.GetSafeNormal();
	ExcludeHeroFromDecals();
	// critic r2 (top defect: "breaches look fake"): find the facade the hero went through. The entry point sits on the wall he hit (trace along
	// the flight line); the exit point is 0.6 m outside the far wall (trace back into it from 3 m outside). The hit gives the true surface point
	// and normal for the opening decal, and the facade component's material for the debris pieces.
	FFacadeHit Hit;
	TraceFacade(bEntry ? P - D * 200.0 : P + D * 300.0, bEntry ? P + D * 200.0 : P - D * 200.0, Hit);
	FVector Pt = P, OutN = bEntry ? -D : D;   // outward facade normal (fallbacks: the flight line is ~ square-on)
	if (Hit.bHit && FVector::Dist(Hit.Point, P) < 260.0 && FMath::Abs(Hit.Normal.Z) < 0.8)
	{
		Pt = Hit.Point; OutN = Hit.Normal;
		if (FVector::DotProduct(OutN, D) * (bEntry ? 1.0 : -1.0) > 0.0) OutN = -OutN;   // entry: faces against the flight; exit: along it
	}
	if (Hit.Mat) LastFacadeMat = Hit.Mat;
	UMaterialInterface* Look = Hit.Mat ? Hit.Mat : LastFacadeMat.Get();
	// debris: >= 20 pieces (ChunksPerBreach = 44) of mixed size, many small 8-25 cm and a few to 50 cm, scattered over the opening on the outside
	// of the wall. Entry: they spray sideways / up / out of the hole (the wall is solid, the camera is outside); exit: they are blown out ahead.
	const double Sp = 700.0 + 1300.0 * Sev;   // (r2: 18-44 m/s, the pieces left the frame within 0.2 s)
	if (Cube)
	{
		SpawnDebris(Pt + OutN * 18.0, OutN, HoleHalfCm * 0.40, Sp, bEntry ? 0.35 : 0.8, ChunksPerBreach, Look, bEntry ? BdConcrete : BdBrick, bEntry ? 0.25f : 0.6f);
		SpawnShards(Pt + OutN * 18.0, bEntry ? OutN : D, ShardsPerBreach, Sp * 1.2);
	}
	// dust: dense, larger, longer-lived puffs around the opening (critic r2: "see-through bubble smoke")
	if (MDust && Sphere) BreachDust(Pt, OutN, D, Sev, bEntry);
	else
	{
		Fx.Dust(PosM, 2.5 + 2.5 * Sev);
		Fx.Dust(PosM + D * 3.0, 2.0 + 2.0 * Sev);
	}
	{ FLinearColor Spark(3.0f, 2.2f, 1.4f); Fx.Hit(Pt / 100.0, bEntry ? OutN : D, 1.0, &Spark); }
	// the hole: a deferred decal on the facade at the entry and the exit (M_BreachHole: jagged near-black opening, broken concrete rim, cracks);
	// facing the facade normal (~ -D at the entry), it grows open over 0.18 s.
	// (critic r1 + r2 capture fl14: the scorched plate -- a flat 3-5 m cylinder disc flush with the facade -- read as a black ellipse
	//  stamped on an intact wall and filled the frame when the camera was close; no plate when the decal asset is missing)
	if (MHole) PlaceHole(Pt, -OutN, Sev);
	if (GcAsset) SpawnGc(P, D);
	PlaySynth(1, P, 0.8f + 0.2f * Sev);
	// suite r2 sims: no slow-mo on the entry any more (the hero is hidden inside the solid then, so the held impact view stared at a hole
	// for ~1.5 s); the pawn starts it with CutSlowMo() when the camera cuts to him bursting out of the exit
	if (bEntry)
	{
		LastBreachEntry = P;
		if (UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this))
		{
			++FW->Breaches;
			FW->AddCollateral(BreachUSD + BreachUSDPerSev * Sev, TEXT("building breach"));
		}
	}
	UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT breach %s fx at %s sev %.2f (chunks live %d; facade trace %s%s, facade material %s, hole decal %s, dust %s)"), bEntry ? TEXT("in") : TEXT("out"), *PosM.ToString(), Sev,
		Chunks.FilterByPredicate([](const FChunk& C) { return C.bLive; }).Num(), Hit.bHit ? TEXT("hit") : TEXT("miss"), Hit.bHit ? *FString::Printf(TEXT(" n (%.2f, %.2f, %.2f)"), OutN.X, OutN.Y, OutN.Z) : TEXT(""),
		Look ? *Look->GetName() : TEXT("none"), MHole ? TEXT("yes") : TEXT("no"), MDust ? TEXT("dense") : TEXT("combat puffs"));
}

void AWHBreachDirector::CutSlowMo()
{
	// one beat per burst: a chain of buildings smashed back to back would otherwise stack the slow-mo into every next pass
	const double Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0;
	if (Now - LastCutSlowMoT < 2.0) return;
	LastCutSlowMoT = Now;
	if (!bNoSlowMo && SlowMoScale < 0.999f) StartSlowMo();
}

void AWHBreachDirector::Crater(const FVector& PosM, float Sev)
{
	FVector P = PosM * 100.0;
	ExcludeHeroFromDecals();
	// critic r2 (fl11 / fl12: "a flat dark disc", debris cubes, an opaque flash disc): the crater sits on the traced ground (its material is also
	// the look of part of the ejecta), wears the cracked / scorched decal, gets a raised rim of settled rubble and a translucent shock ring
	UMaterialInterface* GroundMat = nullptr;
	{ const double Gz = TraceGroundZ(P, &GroundMat); if (FMath::Abs(Gz - P.Z) < 120.0) P.Z = Gz; }
	if (MDecal) PlaceCraterDecal(P, Sev);
	else
	{ // suite r1 (fl11: one 8 m flat disc read as an asphalt patch): a smaller black scorched core inside a dark soot apron
		PlaceScar(P + FVector(0, 0, 1.5), FQuat::Identity, FVector(3.4 + 2.4 * Sev, 3.4 + 2.4 * Sev, 0.02), BdConcrete * 0.18f);
		PlaceScar(P + FVector(0, 0, 2.5), FQuat::Identity, FVector(1.6 + 1.4 * Sev, 1.6 + 1.4 * Sev, 0.02), BdScorch);
	}
	if (Cube)
	{
		// ejecta: pieces flung up and out (physics), mixed sizes; the rim below is static and sits on the ground
		SpawnDebris(P + FVector(0, 0, 18.0), FVector::UpVector, 90.0, 520.0 + 700.0 * Sev, 0.7, ChunksPerCrater, GroundMat, BdConcrete, 0.1f);
		SpawnRim(P, Sev, GroundMat);
	}
	if (MDust && Sphere) CraterDust(P, Sev);
	else Fx.Dust(P / 100.0, 3.0 + 4.0 * Sev);
	// shock ring: a thin translucent pancake of vapour (critic r2: the opaque flash discs at fl11 2.35 s / fl12 3.6 s were lit translucent pancakes
	// up to 21 m wide; with no vapour material there is no ring at all)
	if (MVapour && Sphere) SpawnVapour(false, P + FVector(0, 0, 25.0), FVector::UpVector, 0.0, 0.0, 0.0, 0.0, 80.0, 480.0 + 380.0 * Sev, 0.5, 0.55, 1.0f);
	PlaySynth(2, P, 0.6f + 0.4f * Sev);
	if (UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this))
	{
		++FW->Craters;
		FW->AddCollateral(CraterUSD + CraterUSDPerSev * Sev, TEXT("crater landing"));
	}
}

void AWHBreachDirector::Boom(const FVector& PosM, const FVector& DirM)
{
	FVector D = DirM.GetSafeNormal();
	if (D.IsNearlyZero()) D = FVector::ForwardVector;
	const FVector PCm = PosM * 100.0;
	// critic r2 (fl04 / fl15: "no shock shape in frames 98-112"): a translucent vapour cone opening behind the hero (apex 1.4 m ahead of him) that
	// follows him for BoomFollow s while it grows and fades, plus three thin vapour rings hanging behind it. The chase camera sits inside / just
	// behind the cone, so its fresnel-lit walls fill the periphery of the frame (>= 25 % of the width) for ~0.5 s.
	bool bVapour = false;
	if (MVapour)
	{
		if (Cone)
		{
			SpawnVapour(true, PCm + D * 140.0, D, BoomFollow, 140.0, BoomConeLenM * 100.0, BoomConeLenM * 160.0, BoomConeRadM * 100.0, BoomConeRadM * 240.0, BoomOpacity, BoomLife, 1.5f);
			bVapour = true;
		}
		if (Sphere)
		{
			for (int32 R = 0; R < 3; ++R)
				SpawnVapour(false, PCm - D * (150.0 + 380.0 * R), D, BoomFollow * 0.7, -(150.0 + 380.0 * R), 0.0, 0.0, 120.0 + 40.0 * R, 520.0 + 150.0 * R, BoomOpacity * 1.1, BoomLife * 0.75, 1.2f);
			bVapour = true;
		}
	}
	if (!bVapour)
	{
		// round 2 fallback (assets missing): a shock ring square-on to the flight line, expanding over ~0.7 s
		FRing* Rg = nullptr;
		for (FRing& R : Rings) if (!R.bLive) { Rg = &R; break; }
		UMaterialInterface* RingBase = MGlow ? MGlow.Get() : MTrans.Get();
		if (!Rg && Sphere && RingBase) { FRing N; N.Comp = MakeComp(Sphere, RingBase, N.Mid, false); KeepAlive.Add(N.Comp); Rings.Add(N); Rg = &Rings.Last(); }
		if (Rg)
		{
			Rg->bLive = true; Rg->T = 0; Rg->Life = 0.7; Rg->R1 = 28.0;
			Rg->Pos = PCm - D * 150.0;
			Rg->Q = FRotationMatrix::MakeFromZX(D, BdAnyPerp(D)).ToQuat();
			Rg->Comp->SetVisibility(true);
		}
		{ // critic r1 (fl04: the boom had no visible trace): a vapour collar -- a ring of puffs square-on to the flight line just behind him --
		  // and a white flash on the line
			const FVector A = BdAnyPerp(D), B = FVector::CrossProduct(D, A);
			// (r2 capture: puffs behind him were passed by the chase camera within a few frames -- the collars sit ahead on the line, so the
			//  camera sees him punch through them at 120+ m/s)
			for (int32 R = 0; R < 3; ++R)
				for (int32 K = 0; K < 12; ++K)
				{
					const double Ang = 2.0 * PI * (K + 0.5 * R) / 12.0;
					Fx.Dust(PosM + D * (10.0 + 9.0 * R) + (A * FMath::Cos(Ang) + B * FMath::Sin(Ang)) * (2.6 + 0.9 * R), 2.6);
				}
		}
	}
	{ // the white flash on the line (additive sparks, small; r3: no opaque / lit flash disc)
		const FLinearColor Flash(4.f, 4.f, 4.2f);
		Fx.Hit(PosM - D * 1.5, -D, 1.0, &Flash);
		// owner feedback 2026-10-15 #1: a second, brighter flash right at the body (the boom now marks the super launch)
		const FLinearColor Flash2(7.f, 7.f, 7.5f);
		Fx.Hit(PosM, D, 1.0, &Flash2);
	}
	// owner feedback 2026-10-15 #1 ("big expanding vapour ring / cone + flash + shock ring ... dust / glass shake on nearby facades"): the super
	// launch leaves a big shock ring square-on to the launch line where it fired (BoomRingRadM, it hangs there as he rockets away from the
	// lagging camera), a faint expanding shock shell, glass / dust shaken off facades within BoomShakeRadM and a dust ring on a street below
	if (MVapour && Sphere)
	{
		SpawnVapour(false, PCm, D, 0.0, 0.0, 0.0, 0.0, 150.0, double(BoomRingRadM) * 100.0, BoomOpacity * 0.95, 0.75, 1.0f);
		SpawnVapour(false, PCm - D * 250.0, D, 0.0, 0.0, 0.0, 0.0, 90.0, double(BoomRingRadM) * 60.0, BoomOpacity * 0.8, 0.6, 1.2f);
		SpawnShape(2, PCm, D, 0.0, 0.0, 0.0, 0.0, 100.0, 1600.0, 0.08, 0.5, 2.2f, 0);   // shock shell: faint (it engulfs the camera)
	}
	ShakeFacades(PCm);
	PlaySynth(0, PosM * 100.0, 1.f);
}

// owner feedback 2026-10-15 #1: the super-boost charge -- a short global slow-mo (real time, ended by the boom) and a vapour shell that gathers
// onto the hero (shrinking 7 m -> 1.4 m, opacity ramping up to the launch); the inward streaks run in FlightFxTick while ChargeK > 0
void AWHBreachDirector::ChargeFx(const FVector& PosM, const FVector& DirM, float SlowScale, float RealDur)
{
	const FVector PCm = PosM * 100.0;
	FVector D = DirM.GetSafeNormal();
	if (D.IsNearlyZero()) D = FVector::ForwardVector;
	const double Dur = FMath::Clamp(double(RealDur), 0.1, 2.0);
	const double Scale = FMath::Clamp(double(SlowScale), 0.05, 1.0);
	if (!bNoSlowMo && !bSlowMo && Scale < 0.999)
	{
		UGameplayStatics::SetGlobalTimeDilation(this, float(Scale));
		bChargeSlow = true;
		ChargeSlowEnd = FPlatformTime::Seconds() + Dur + 0.25;   // safety end (the boom or a cancelled charge ends it first)
	}
	const double LifeGame = Dur * (bChargeSlow ? Scale : 1.0);   // this director ticks in game seconds
	if (MVapour && Sphere)
	{
		SpawnShape(2, PCm, D, LifeGame, 0.0, 0.0, 0.0, 700.0, 140.0, GatherOpacity, LifeGame, 2.6f, 1);
		SpawnShape(2, PCm, D, LifeGame, 0.0, 0.0, 0.0, 420.0, 110.0, GatherOpacity * 0.7, LifeGame, 1.8f, 1);
	}
	GatherT = 0.0;
	Fx.Dust(PosM - FVector(0.0, 0.0, 1.0), 0.8);
}

void AWHBreachDirector::EndChargeSlowMo()
{
	if (!bChargeSlow) return;
	bChargeSlow = false;
	if (!bSlowMo) UGameplayStatics::SetGlobalTimeDilation(this, 1.f);
}

// owner feedback 2026-10-15 #1: the boom's pressure wave -- 12 horizontal / downward rays; facades within BoomShakeRadM shed glass glints and a
// small dust burst, a street within 30 m below gets a dust ring (cheap: 13 traces once per boom)
void AWHBreachDirector::ShakeFacades(const FVector& PCm)
{
	const double R = FMath::Max(5.0, double(BoomShakeRadM)) * 100.0;
	int32 NHit = 0;
	for (int32 K = 0; K < 12; ++K)
	{
		const double A = 2.0 * PI * (K + 0.37) / 12.0;
		const double Down = (K % 3 == 0) ? -0.35 : 0.0;
		const FVector Dir = FVector(FMath::Cos(A), FMath::Sin(A), Down).GetSafeNormal();
		FFacadeHit H;
		if (!TraceFacade(PCm, PCm + Dir * R, H) || FMath::Abs(H.Normal.Z) > 0.6) continue;
		++NHit;
		const double Near = 1.0 - FMath::Clamp(FVector::Dist(PCm, H.Point) / R, 0.0, 1.0);
		if (Cube) SpawnShards(H.Point + H.Normal * 30.0, H.Normal, 3 + int32(5 * Near), 300.0 + 500.0 * Near);
		if (MDust && Sphere)
		{
			FVector U, V; BdPlaneBasis(H.Normal, U, V);
			for (int32 P = 0; P < 2; ++P)
			{
				const FVector Rad = U * Rng.FRandRange(-1.f, 1.f) + V * Rng.FRandRange(-0.5f, 1.f);
				const double S0 = Rng.FRandRange(70.f, 120.f);
				SpawnPuff(H.Point + H.Normal * 40.0 + Rad * 120.0, H.Normal * Rng.FRandRange(100.f, 260.f) + Rad * 120.0, S0, S0 * 2.8, 1.3, 0.5, Rng.FRandRange(0.f, 0.1f), BdDust * Rng.FRandRange(0.85f, 1.05f));
			}
		}
	}
	FFacadeHit G;
	if (TraceFacade(PCm, PCm - FVector(0.0, 0.0, 3000.0), G) && G.Normal.Z > 0.5 && MDust && Sphere)
		CraterDust(G.Point, float(0.6 * (1.0 - FMath::Clamp((PCm.Z - G.Point.Z) / 3000.0, 0.0, 1.0))));
	UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT boom shake: %d facades within %.0f m%s"), NHit, R / 100.0, G.bHit ? TEXT(", street dust ring") : TEXT(""));
}

// owner feedback 2026-10-15 #1 / #3: the pawn's per-frame flight state for the continuous FX (FlightFxTick); a charge that ends without a boom
// (brake / slam / landing) ends its slow-mo here
void AWHBreachDirector::SetFlightFx(float ChargeK, float SuperK, float FastK, const FVector& PosM, const FVector& VelM)
{
	FxChargeK = FMath::Clamp(ChargeK, 0.f, 1.f);
	FxSuperK = FMath::Clamp(SuperK, 0.f, 1.f);
	FxFastK = FMath::Clamp(FastK, 0.f, 1.f);
	FxPosCm = PosM * 100.0;
	FxVelCm = VelM * 100.0;
	bFxValid = true;
	if (bChargeSlow && FxChargeK <= 0.f) EndChargeSlowMo();
}

// owner feedback 2026-10-15 #1 / #3 (speed read): continuous flight FX, game seconds
//  - charge: streaks converging on the hero from 4.5-7.5 m (0.22 s each), the "pressure gathering"
//  - super line / fast cruise: world wind streaks spawned ahead of him around the flight line (2.5-11 m out) that he and the chase camera
//    fly past in 0.15-0.35 s (StreakRate x SuperK + FastStreakRate x FastK per second)
//  - super line: a vapour trail glued to the body (TrailEvery) and two thinner contrails 45 cm to either side
//  - super line under WakeMaxH: a dust wake blown out sideways on the street below
void AWHBreachDirector::FlightFxTick(double Dt)
{
	if (!bFxValid || Dt <= 0.0) return;
	const double Sp = FxVelCm.Size();
	const FVector Vd = Sp > 1.0 ? FxVelCm / Sp : FVector::ForwardVector;
	if (FxChargeK > 0.f && MVapour && Sphere)
	{
		GatherT += Dt;
		while (GatherT >= 0.035)
		{
			GatherT -= 0.035;
			for (int32 K = 0; K < 2; ++K)
			{
				const FVector U = Rng.GetUnitVector();
				const double R = Rng.FRandRange(450.f, 750.f);
				const double Life = 0.22;
				if (FVapour* Vp = SpawnShape(3, FxPosCm + U * R, -U, 0.0, 0.0, Rng.FRandRange(150.f, 300.f), 80.0, Rng.FRandRange(4.f, 8.f), 3.0, GatherOpacity * (0.6 + 0.6 * FxChargeK), Life, 1.0f, 2))
					Vp->VelCm = -U * (R / Life);
			}
		}
	}
	else GatherT = 0.0;
	const double StreakPerS = double(StreakRate) * FxSuperK + double(FastStreakRate) * FxFastK * (1.0 - FxSuperK);
	if (StreakPerS > 0.01 && Sp > 2000.0 && Sphere && (MStreak || MVapour))
	{
		StreakAcc += StreakPerS * Dt;
		int32 N = 0;
		while (StreakAcc >= 1.0 && N < 10)
		{
			StreakAcc -= 1.0; ++N;
			const double Ahead = Sp * Rng.FRandRange(0.15f, 0.35f);
			const double R = Rng.FRandRange(250.f, 1100.f);
			const FVector At = FxPosCm + Vd * Ahead + BdRingDir(Vd, Rng.FRandRange(0.f, 2.f * PI)) * R;
			const double Len = FMath::Clamp(Sp * 0.035, 400.0, 1400.0) * Rng.FRandRange(0.7f, 1.2f);
			const double Rad = Rng.FRandRange(5.f, 11.f);
			SpawnShape(3, At, Vd, 0.0, 0.0, Len, Len, Rad, Rad, double(StreakOpacity) * Rng.FRandRange(0.5f, 1.f) * FMath::Max(double(FxSuperK), 0.45), 0.5, 1.0f, 2);
		}
		if (N >= 10) StreakAcc = 0.0;
	}
	else StreakAcc = 0.0;
	if (FxSuperK > 0.05f && Sphere && (MStreak || MVapour))
	{
		TrailT += Dt;
		if (TrailT >= FMath::Max(0.02f, TrailEvery))
		{
			TrailT = 0.0;
			const double Len = 900.0 + 600.0 * FxSuperK;
			const double Peak = double(TrailOpacity) * FxSuperK;
			const double Life = 0.16;
			// the body trail: centre half a length behind the chest, glued to him
			SpawnShape(3, FxPosCm - Vd * (Len * 0.5 + 40.0), Vd, Life, -(Len * 0.5 + 40.0), Len, Len * 1.1, 30.0, 55.0, Peak, Life, 1.0f, 2);
			FVector Side = FVector::CrossProduct(Vd, FVector::UpVector);
			if (Side.IsNearlyZero()) Side = BdAnyPerp(Vd);
			Side = Side.GetSafeNormal();
			for (const double S : { -1.0, 1.0 })
				if (FVapour* Vp = SpawnShape(3, FxPosCm - Vd * (Len * 0.6) + Side * (45.0 * S), Vd, Life, -(Len * 0.6), Len * 1.2, Len * 1.3, 8.0, 14.0, Peak * 0.8, Life, 1.0f, 2))
					Vp->SideCm = Side * (45.0 * S);
		}
	}
	else TrailT = 0.0;
	if (FxSuperK > 0.3f && MDust && Sphere)
	{
		WakeT += Dt;
		if (WakeT >= 0.08)
		{
			WakeT = 0.0;
			FFacadeHit G;
			const double MaxH = FMath::Max(1.0, double(WakeMaxH)) * 100.0;
			if (TraceFacade(FxPosCm, FxPosCm - FVector(0.0, 0.0, MaxH), G) && G.Normal.Z > 0.5)
			{
				const double K = 1.0 - FMath::Clamp((FxPosCm.Z - G.Point.Z) / MaxH, 0.0, 1.0);
				FVector Side = FVector::CrossProduct(FVector(Vd.X, Vd.Y, 0.0).GetSafeNormal(), FVector::UpVector);
				if (Side.IsNearlyZero()) Side = FVector::RightVector;
				for (const double S : { -1.0, 1.0 })
				{
					const double S0 = Rng.FRandRange(110.f, 170.f) * (0.7 + 0.6 * K);
					SpawnPuff(G.Point + FVector(0.0, 0.0, 40.0) + Side * (S * Rng.FRandRange(80.f, 200.f)),
						Side * (S * Rng.FRandRange(500.f, 1100.f) * K) + FVector(Vd.X, Vd.Y, 0.0) * 300.0 + FVector(0.0, 0.0, Rng.FRandRange(60.f, 200.f)),
						S0, S0 * Rng.FRandRange(2.6f, 3.4f), Rng.FRandRange(1.2f, 1.7f), 0.45 + 0.25 * K, 0.0, BdDust * Rng.FRandRange(0.85f, 1.05f));
				}
			}
		}
	}
	else WakeT = 0.0;
}

void AWHBreachDirector::Bump(const FVector& PosM, const FVector& NormalM, float Sev)
{
	const FVector P = PosM * 100.0;
	FVector N = NormalM.GetSafeNormal();
	if (N.IsNearlyZero()) N = FVector::UpVector;
	if (MDust && Sphere)
	{ // a small dense puff burst on the facade (r3), not the translucent combat puffs
		FVector U, V; BdPlaneBasis(N, U, V);
		const int32 NP = 4 + int32(4 * Sev);
		for (int32 K = 0; K < NP; ++K)
		{
			const FVector Rad = U * Rng.FRandRange(-1.f, 1.f) + V * Rng.FRandRange(-1.f, 1.f);
			const double S0 = Rng.FRandRange(50.f, 90.f);
			SpawnPuff(P + N * Rng.FRandRange(15.f, 40.f) + Rad * 25.0, N * Rng.FRandRange(60.f, 160.f) + Rad * Rng.FRandRange(60.f, 200.f), S0, S0 * Rng.FRandRange(2.4f, 3.2f),
				Rng.FRandRange(1.0f, 1.4f), Rng.FRandRange(0.45f, 0.6f), Rng.FRandRange(0.f, 0.08f), BdDust * Rng.FRandRange(0.8f, 1.05f));
		}
	}
	else Fx.Dust(PosM, 0.8 + 1.2 * Sev);
	if (Cube)
	{
		// the scrape chips take the facade's material (one trace per 0.4 s: scrapes come in runs)
		const double Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0;
		if (Now - LastBumpTraceT > 0.4)
		{
			LastBumpTraceT = Now;
			FFacadeHit H;
			if (TraceFacade(P + N * 120.0, P - N * 120.0, H) && H.Mat) LastFacadeMat = H.Mat;
		}
		SpawnDebris(P + N * 12.0, N, 40.0, 450.0 + 650.0 * Sev, 0.5, 4 + int32(6 * Sev), LastFacadeMat.Get(), BdConcrete, 0.2f);
	}
	if (UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this)) FW->AddCollateral(5000.f + 20000.f * Sev, TEXT("facade scrape"));
}

void AWHBreachDirector::SpawnChunks(const FVector& PosCm, const FVector& DirN, int32 N, double SpeedCms, const FLinearColor& Tint, double SizeCm)
{
	(void)SizeCm;   // r3: piece sizes come from SpawnDebris' mixed distribution (8-25 cm mostly, a few to 50 cm)
	SpawnDebris(PosCm, DirN, 100.0, SpeedCms, 0.7, N, nullptr, Tint, 0.2f);
}

void AWHBreachDirector::SpawnDebris(const FVector& OriginCm, const FVector& Axis, double SpawnRadiusCm, double SpeedCms, double AxisBias, int32 N, UMaterialInterface* Look, const FLinearColor& Tint, float Brick)
{
	if (!Cube) return;
	FVector Ax = Axis.GetSafeNormal();
	if (Ax.IsNearlyZero()) Ax = FVector::UpVector;
	FVector U, V; BdPlaneBasis(Ax, U, V);
	const double Now = GetWorld()->GetTimeSeconds();
	for (int32 K = 0; K < N; ++K)
	{
		FChunk* Ch = nullptr;
		if (Chunks.Num() < MaxChunks)
		{
			FChunk New;
			New.Comp = MakeComp(Cube, MChunk ? MChunk.Get() : MSolid.Get(), New.Mid, true);
			New.Comp->SetCollisionProfileName(TEXT("PhysicsActor"));
			New.Comp->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
			New.Comp->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
			New.Comp->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
			New.Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			KeepAlive.Add(New.Comp);
			Chunks.Add(New);
			Ch = &Chunks.Last();
		}
		else { Ch = &Chunks[NextChunk % Chunks.Num()]; ++NextChunk; } // recycle the oldest
		UStaticMeshComponent* C = Ch->Comp;
		C->SetSimulatePhysics(false);
		// critic r2 (breach: "no single piece or flat shape covers > 5 % of the frame at ~4 m"; r2 pieces were one size band of 9-47 cm cubes):
		// 66 % small 8-25 cm, 26 % medium 20-34 cm, 8 % large 34-50 cm (longest side); blocks, slabs and bars so the pile does not read as dice
		const float Pick = Rng.FRand();
		const double L = Pick < 0.66f ? Rng.FRandRange(8.f, 25.f) : Pick < 0.92f ? Rng.FRandRange(20.f, 34.f) : Rng.FRandRange(34.f, 50.f);
		const float Shape = Rng.FRand();
		const FVector Dim = Shape < 0.45f ? FVector(L, L * Rng.FRandRange(0.55f, 1.f), L * Rng.FRandRange(0.45f, 0.9f))          // block
			: Shape < 0.8f ? FVector(L, L * Rng.FRandRange(0.5f, 0.95f), L * Rng.FRandRange(0.14f, 0.3f))                            // slab
			: FVector(L, L * Rng.FRandRange(0.2f, 0.4f), L * Rng.FRandRange(0.2f, 0.4f));                                           // bar
		const double Ang = Rng.FRand() * 2.0 * PI;
		const FVector Rad = U * FMath::Cos(Ang) + V * FMath::Sin(Ang);
		const FVector Pos = OriginCm + Rad * SpawnRadiusCm * FMath::Sqrt(double(Rng.FRand())) + Ax * Rng.FRandRange(0.f, 20.f);
		C->SetWorldLocationAndRotation(Pos, FRotator(Rng.FRandRange(0.f, 360.f), Rng.FRandRange(0.f, 360.f), Rng.FRandRange(0.f, 360.f)));
		Ch->Scale = Dim / 100.0;
		C->SetWorldScale3D(Ch->Scale);
		// look: part of the pieces wear the material of the facade (or ground) the line trace hit; the rest the M_InvChunk concrete / brick speckle
		// (or, without that asset, the r2 flat tints: darker mixed rubble, suite r1 sheet review)
		if (Look && Rng.FRand() < FacadeChunkFraction) C->SetMaterial(0, Look);
		else if (Ch->Mid)
		{
			C->SetMaterial(0, Ch->Mid);
			const bool bBrick = Rng.FRand() < Brick;
			const float Pick2 = Rng.FRand();
			const FLinearColor Base = bBrick ? BdBrick : Pick2 < 0.6f ? Tint : Pick2 < 0.8f ? BdConcrete : Pick2 < 0.92f ? BdSteel : BdScorch * 4.f;
			const float Vv = Rng.FRandRange(0.35f, 0.75f);
			Ch->Mid->SetVectorParameterValue(TEXT("Color"), FLinearColor(Base.R * Vv, Base.G * Vv, Base.B * Vv, 1.f));
			Ch->Mid->SetScalarParameterValue(TEXT("Rough"), 0.9f);
			Ch->Mid->SetScalarParameterValue(TEXT("Brick"), bBrick ? 1.f : 0.f);
			Ch->Mid->SetScalarParameterValue(TEXT("Seed"), Rng.FRandRange(0.f, 20.f));
		}
		C->SetVisibility(true);
		C->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		C->SetSimulatePhysics(true);
		const FVector Dir = (Ax * AxisBias * Rng.FRandRange(0.35f, 1.0f) + Rad * (1.0 - AxisBias) * Rng.FRandRange(0.25f, 1.0f) + FVector(0.0, 0.0, Rng.FRandRange(0.05f, 0.35f))).GetSafeNormal();
		C->SetPhysicsLinearVelocity(Dir * SpeedCms * Rng.FRandRange(0.3f, 1.0f));
		C->SetPhysicsAngularVelocityInDegrees(FVector(Rng.FRandRange(-720.f, 720.f), Rng.FRandRange(-720.f, 720.f), Rng.FRandRange(-720.f, 720.f)));
		Ch->bLive = true; Ch->bFrozen = false; Ch->Born = Now; Ch->NextCheck = Now + 1.2;
	}
}

void AWHBreachDirector::SpawnShards(const FVector& PosCm, const FVector& DirN, int32 N, double SpeedCms)
{
	if (!Cube) return;
	const FVector Side = BdAnyPerp(DirN), Up = FVector::CrossProduct(DirN, Side);
	for (int32 K = 0; K < N; ++K)
	{
		FShard* Sh = nullptr;
		if (Shards.Num() < MaxShards)
		{
			FShard New;
			New.Comp = MakeComp(Cube, MTrans ? MTrans.Get() : MSolid.Get(), New.Mid, false);
			KeepAlive.Add(New.Comp);
			Shards.Add(New);
			Sh = &Shards.Last();
		}
		else { Sh = &Shards[NextShard % Shards.Num()]; ++NextShard; }
		Sh->bLive = true; Sh->T = 0; Sh->Life = Rng.FRandRange(0.9f, 1.8f);
		Sh->Pos = PosCm + Side * Rng.FRandRange(-150.f, 150.f) + Up * Rng.FRandRange(-120.f, 150.f);
		Sh->Vel = (DirN + Side * Rng.FRandRange(-0.8f, 0.8f) + Up * Rng.FRandRange(-0.4f, 0.9f)).GetSafeNormal() * SpeedCms * Rng.FRandRange(0.3f, 1.0f);
		Sh->Q = FRotator(Rng.FRandRange(0.f, 360.f), Rng.FRandRange(0.f, 360.f), 0.f).Quaternion();
		Sh->Spin = FVector(Rng.FRandRange(-12.f, 12.f), Rng.FRandRange(-12.f, 12.f), Rng.FRandRange(-12.f, 12.f));
		// critic r2 ("paper-card debris"): fewer, smaller (4-12 cm), thinner and brighter (glints) glass pieces; r2 had 6-22 cm cards
		const float S = Rng.FRandRange(0.04f, 0.12f);
		Sh->Comp->SetWorldScale3D(FVector(S, S * Rng.FRandRange(0.5f, 1.2f), 0.004f));
		if (Sh->Mid)
		{
			Sh->Mid->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.62f, 0.78f, 0.86f, 1.f));
			Sh->Mid->SetScalarParameterValue(TEXT("Opacity"), 0.7f);
			Sh->Mid->SetScalarParameterValue(TEXT("Emissive"), 0.9f);
		}
		Sh->Comp->SetVisibility(true);
	}
}

// ---------------------------------------------------------------------------------------------------------------- round 3 helpers
bool AWHBreachDirector::TraceFacade(const FVector& StartCm, const FVector& EndCm, FFacadeHit& Out) const
{
	UWorld* W = GetWorld();
	if (!W) return false;
	// the world's solids are traced like the traversal does it (WorldStatic + WorldDynamic objects, complex = the visual triangles of the merged
	// meshes); components already hit are ignored on the next pass, so an invisible collision cube in front of the visual facade does not hide its material
	FCollisionQueryParams Q(SCENE_QUERY_STAT(WHBreachFacade), /*bTraceComplex*/ true);
	Q.bReturnFaceIndex = true;
	if (APawn* Hero = UGameplayStatics::GetPlayerPawn(this, 0)) Q.AddIgnoredActor(Hero);
	FCollisionObjectQueryParams Obj;
	Obj.AddObjectTypesToQuery(ECC_WorldStatic);
	Obj.AddObjectTypesToQuery(ECC_WorldDynamic);
	for (int32 K = 0; K < 5; ++K)
	{
		FHitResult H;
		if (!W->LineTraceSingleByObjectType(H, StartCm, EndCm, Obj, Q)) break;
		UPrimitiveComponent* C = H.GetComponent();
		if (!Out.bHit && !H.bStartPenetrating) { Out.bHit = true; Out.Point = H.ImpactPoint; Out.Normal = H.ImpactNormal.GetSafeNormal(); }
		if (C)
		{
			if (!Out.Mat && C->IsVisible() && !C->bHiddenInGame)
			{
				int32 Sec = 0;
				UMaterialInterface* M = H.FaceIndex >= 0 ? C->GetMaterialFromCollisionFaceIndex(H.FaceIndex, Sec) : nullptr;
				if (!M) M = C->GetMaterial(int32(H.ElementIndex));
				if (!M) M = C->GetMaterial(0);
				if (BdDebrisMaterialOk(M)) Out.Mat = M;
			}
			Q.AddIgnoredComponent(C);
		}
		if (Out.bHit && Out.Mat) break;
	}
	return Out.bHit;
}

double AWHBreachDirector::TraceGroundZ(const FVector& PCm, UMaterialInterface** OutMat) const
{
	FFacadeHit H;
	if (TraceFacade(PCm + FVector(0.0, 0.0, 150.0), PCm - FVector(0.0, 0.0, 300.0), H) && H.Normal.Z > 0.5)
	{
		if (OutMat) *OutMat = H.Mat;
		return H.Point.Z;
	}
	return PCm.Z;
}

AWHBreachDirector::FDecalItem* AWHBreachDirector::AcquireDecal(TArray<FDecalItem>& Pool, int32& Next, int32 MaxN, UMaterialInterface* Mat)
{
	if (!Mat || MaxN <= 0) return nullptr;
	if (Pool.Num() < MaxN)
	{
		FDecalItem N;
		N.Comp = NewObject<UDecalComponent>(this);
		N.Comp->SetupAttachment(RootComponent);
		N.Comp->SetUsingAbsoluteLocation(true); N.Comp->SetUsingAbsoluteRotation(true); N.Comp->SetUsingAbsoluteScale(true);
		N.Comp->DecalSize = FVector(90.0, 300.0, 300.0);
		N.Comp->FadeScreenSize = 0.0004f;   // (the default 0.01 drops a decal that covers < 1 % of the screen: a hole seen from across a street)
		N.Comp->SetDecalMaterial(Mat);
		N.Comp->RegisterComponent();
		N.Mid = N.Comp->CreateDynamicMaterialInstance();
		KeepAlive.Add(N.Comp);
		if (N.Mid) KeepAlive.Add(N.Mid);
		Pool.Add(N);
		return &Pool.Last();
	}
	FDecalItem* It = &Pool[Next % Pool.Num()];
	++Next;
	return It;   // recycle the oldest
}

void AWHBreachDirector::PlaceHole(const FVector& PointCm, const FVector& IntoWall, float Sev)
{
	FDecalItem* It = AcquireDecal(HoleDecals, NextHole, MaxHoleDecals, MHole);
	if (!It || !It->Comp) return;
	FVector Into = IntoWall.GetSafeNormal();
	if (Into.IsNearlyZero()) Into = FVector::ForwardVector;
	const double Half = HoleHalfCm * (1.0 + 0.18 * Sev);
	It->Comp->DecalSize = FVector(90.0, Half, Half);   // projects 0.9 m either side of the surface along its X axis (into the wall)
	const FRotator Rot = FMath::Abs(Into.Z) > 0.9 ? FRotationMatrix::MakeFromX(Into).Rotator() : FRotationMatrix::MakeFromXZ(Into, FVector::UpVector).Rotator();
	It->Comp->SetWorldLocationAndRotation(PointCm, Rot);
	It->Comp->SetSortOrder(2);
	It->Comp->SetVisibility(true);
	if (It->Mid)
	{
		const float T = Rng.FRandRange(0.8f, 1.15f);
		It->Mid->SetScalarParameterValue(TEXT("Seed"), Rng.FRandRange(0.f, 9.f));
		It->Mid->SetScalarParameterValue(TEXT("Open"), 0.f);
		It->Mid->SetVectorParameterValue(TEXT("RimCol"), FLinearColor(0.30f * T, 0.28f * T, 0.25f * T, 1.f));
	}
	It->T = 0.0; It->Grow = 0.18; It->bGrowing = true;
}

void AWHBreachDirector::PlaceCraterDecal(const FVector& PCm, float Sev)
{
	FDecalItem* It = AcquireDecal(CraterDecals, NextCrater, MaxCraterDecals, MDecal);
	if (!It || !It->Comp) return;
	const double R = 220.0 + 260.0 * Sev;
	// a shallow slab: the ground is flat, and the only other things in the volume are boots, wheels and rubble (the hero's meshes have decals off)
	It->Comp->DecalSize = FVector(28.0, R, R);
	It->Comp->SetWorldLocationAndRotation(PCm + FVector(0.0, 0.0, 6.0), FRotator(-90.0, Rng.FRandRange(0.f, 360.f), 0.f));
	It->Comp->SetSortOrder(1);
	It->Comp->SetVisibility(true);
	if (It->Mid)
	{
		It->Mid->SetScalarParameterValue(TEXT("Seed"), Rng.FRandRange(0.f, 9.f));
		It->Mid->SetScalarParameterValue(TEXT("Open"), 0.f);
	}
	It->T = 0.0; It->Grow = 0.30; It->bGrowing = true;
}

void AWHBreachDirector::SpawnPuff(const FVector& PosCm, const FVector& VelCms, double S0, double S1, double Life, double Peak, double DelayS, const FLinearColor& Col)
{
	if (!Sphere || !MDust) return;
	FPuff* Pf = nullptr;
	if (Puffs.Num() < MaxPuffs)
	{
		FPuff N;
		N.Comp = MakeComp(Sphere, MDust, N.Mid, false);
		KeepAlive.Add(N.Comp);
		Puffs.Add(N);
		Pf = &Puffs.Last();
	}
	else { Pf = &Puffs[NextPuff % Puffs.Num()]; ++NextPuff; }   // recycle the oldest
	Pf->Pos = PosCm; Pf->Vel = VelCms; Pf->T = 0.0; Pf->Delay = DelayS; Pf->Life = Life; Pf->S0 = S0; Pf->S1 = S1; Pf->Peak = Peak;
	Pf->Drag = Rng.FRandRange(1.8f, 2.8f); Pf->Rise = Rng.FRandRange(40.f, 110.f);
	Pf->bLive = true; Pf->bShown = false;
	Pf->Comp->SetVisibility(false);
	if (Pf->Mid)
	{
		Pf->Mid->SetVectorParameterValue(TEXT("Color"), Col);
		Pf->Mid->SetScalarParameterValue(TEXT("Seed"), Rng.FRandRange(0.f, 20.f));
		Pf->Mid->SetScalarParameterValue(TEXT("Opacity"), 0.f);
	}
}

void AWHBreachDirector::BreachDust(const FVector& PointCm, const FVector& OutN, const FVector& FlightDir, float Sev, bool bEntry)
{
	// critic r2 ("see-through bubble smoke"): fewer, larger, more opaque puffs that linger ~1.5 s. They start on a ring AROUND the opening (so the
	// dark hole stays readable 0.3 s after the impact) and billow outward along the wall; at the exit a share is blown out ahead of the hero.
	FVector U, V; BdPlaneBasis(OutN, U, V);
	const int32 N = PuffsPerBreach + int32(6 * Sev);
	const double HoleR = HoleHalfCm * 0.42;
	const FLinearColor Base = bEntry ? BdDust : BdBrickDust;
	for (int32 K = 0; K < N; ++K)
	{
		const double A = 2.0 * PI * (K + Rng.FRand() * 0.8) / N;
		const FVector Rad = U * FMath::Cos(A) + V * FMath::Sin(A);
		FVector Pos, Vel;
		if (!bEntry && Rng.FRand() < 0.3f)
		{
			Pos = PointCm + FlightDir * Rng.FRandRange(150.f, 700.f) + Rad * Rng.FRandRange(0.f, 120.f);
			Vel = FlightDir * Rng.FRandRange(200.f, 500.f) + Rad * Rng.FRandRange(50.f, 200.f);
		}
		else
		{
			Pos = PointCm + OutN * Rng.FRandRange(25.f, 70.f) + Rad * HoleR * Rng.FRandRange(0.95f, 1.5f);
			Vel = Rad * Rng.FRandRange(180.f, 480.f) + OutN * (bEntry ? Rng.FRandRange(60.f, 220.f) : Rng.FRandRange(300.f, 700.f)) + FVector(0.0, 0.0, Rng.FRandRange(0.f, 120.f));
		}
		const double S0 = Rng.FRandRange(90.f, 150.f) * (0.9 + 0.3 * Sev);
		SpawnPuff(Pos, Vel, S0, S0 * Rng.FRandRange(2.6f, 3.4f), Rng.FRandRange(1.35f, 1.9f), Rng.FRandRange(0.62f, 0.78f), Rng.FRandRange(0.f, 0.15f), Base * Rng.FRandRange(0.75f, 1.1f));
	}
}

void AWHBreachDirector::CraterDust(const FVector& PCm, float Sev)
{
	// a ring of dense puffs thrown outward and up from the impact, starting outside the hero's body
	const int32 N = 14 + int32(8 * Sev);
	for (int32 K = 0; K < N; ++K)
	{
		const double A = 2.0 * PI * (K + Rng.FRand() * 0.8) / N;
		const FVector Rad(FMath::Cos(A), FMath::Sin(A), 0.0);
		const double S0 = Rng.FRandRange(90.f, 140.f) * (0.9 + 0.3 * Sev);
		SpawnPuff(PCm + Rad * Rng.FRandRange(80.f, 220.f) + FVector(0.0, 0.0, Rng.FRandRange(20.f, 60.f)), Rad * Rng.FRandRange(300.f, 800.f) + FVector(0.0, 0.0, Rng.FRandRange(80.f, 220.f)),
			S0, S0 * Rng.FRandRange(2.4f, 3.2f), Rng.FRandRange(1.3f, 1.8f), Rng.FRandRange(0.6f, 0.74f), Rng.FRandRange(0.f, 0.1f), BdDust * Rng.FRandRange(0.8f, 1.05f));
	}
}

void AWHBreachDirector::SpawnVapour(bool bCone, const FVector& AnchorCm, const FVector& Dir, double FollowS, double OffsetCm, double Len0, double Len1, double Rad0, double Rad1, double Peak, double Life, float EdgePow)
{
	SpawnShape(bCone ? 0 : 1, AnchorCm, Dir, FollowS, OffsetCm, Len0, Len1, Rad0, Rad1, Peak, Life, EdgePow, 0);
}

// owner feedback 2026-10-15 #1 / #3: the pooled vapour pieces in four shapes (0 cone, 1 ring, 2 ball, 3 streak); streaks wear M_InvStreak when it
// exists (its Dir / HalfLen parameters fade it along its length), else M_InvVapour. Pool cap MaxVapours (was a fixed 24); a full pool skips.
AWHBreachDirector::FVapour* AWHBreachDirector::SpawnShape(int32 Shape, const FVector& AnchorCm, const FVector& Dir, double FollowS, double OffsetCm, double Len0, double Len1, double Rad0, double Rad1, double Peak, double Life, float EdgePow, int32 Env)
{
	UStaticMesh* Mesh = Shape == 0 ? Cone.Get() : Sphere.Get();
	UMaterialInterface* Base = (Shape == 3 && MStreak) ? MStreak.Get() : MVapour.Get();
	if (!Mesh || !Base) return nullptr;
	FVapour* Vp = nullptr;
	for (FVapour& X : Vapours) if (!X.bLive && X.Shape == Shape) { Vp = &X; break; }
	if (!Vp)
	{
		if (Vapours.Num() >= FMath::Max(24, MaxVapours)) return nullptr;
		FVapour N; N.bCone = Shape == 0; N.Shape = Shape;
		N.Comp = MakeComp(Mesh, Base, N.Mid, false);
		KeepAlive.Add(N.Comp);
		Vapours.Add(N);
		Vp = &Vapours.Last();
	}
	FVector Dn = Dir.GetSafeNormal();
	if (Dn.IsNearlyZero()) Dn = FVector::ForwardVector;
	Vp->Anchor = AnchorCm; Vp->Dir = Dn; Vp->T = 0.0; Vp->Life = FMath::Max(0.02, Life); Vp->Follow = FollowS; Vp->OffsetCm = OffsetCm;
	Vp->Len0 = Len0; Vp->Len1 = Len1; Vp->Rad0 = Rad0; Vp->Rad1 = Rad1; Vp->Peak = Peak;
	Vp->Env = Env; Vp->VelCm = FVector::ZeroVector; Vp->SideCm = FVector::ZeroVector;
	Vp->bLive = true;
	if (Vp->Mid)
	{
		Vp->Mid->SetVectorParameterValue(TEXT("Color"), Shape == 0 ? FLinearColor(0.92f, 0.95f, 1.0f, 1.f) : FLinearColor(0.9f, 0.93f, 1.0f, 1.f));
		Vp->Mid->SetScalarParameterValue(TEXT("EdgePow"), EdgePow);
		Vp->Mid->SetScalarParameterValue(TEXT("Opacity"), 0.f);
		if (Shape == 3)
		{ // M_InvStreak: the axis and half length (cm) the speed line fades along (ignored by M_InvVapour)
			Vp->Mid->SetVectorParameterValue(TEXT("Dir"), FLinearColor(float(Dn.X), float(Dn.Y), float(Dn.Z), 0.f));
			Vp->Mid->SetScalarParameterValue(TEXT("HalfLen"), float(FMath::Max(1.0, Len0 * 0.5)));
		}
	}
	Vp->Comp->SetVisibility(true);
	return Vp;
}

void AWHBreachDirector::SpawnRim(const FVector& PCm, float Sev, UMaterialInterface* GroundMat)
{
	// critic r2 (fl11 / fl12: "a raised rubble rim of facade / asphalt-toned chunks that settle, not hanging in the air"): static (non-physics)
	// pieces placed ON the traced ground around the scorched core, tilted and half sunk; they pop in with the shock and stay.
	if (!Cube) return;
	const int32 N = 12 + int32(5 * Sev);
	const double R0 = (220.0 + 260.0 * Sev) * 0.50;
	for (int32 K = 0; K < N; ++K)
	{
		const double A = 2.0 * PI * (K + Rng.FRand() * 0.7) / N;
		const double R = R0 * Rng.FRandRange(0.8f, 1.25f);
		const FVector XY = PCm + FVector(FMath::Cos(A) * R, FMath::Sin(A) * R, 0.0);
		double Gz = TraceGroundZ(XY, nullptr);
		if (FMath::Abs(Gz - PCm.Z) > 80.0) Gz = PCm.Z;
		const double L = Rng.FRand() < 0.2f ? Rng.FRandRange(32.f, 50.f) : Rng.FRandRange(12.f, 30.f);
		const FVector Dim(L, L * Rng.FRandRange(0.55f, 1.f), L * Rng.FRandRange(0.25f, 0.55f));   // slabs
		const double Pitch = Rng.FRandRange(-26.f, 26.f), Roll = Rng.FRandRange(-26.f, 26.f);
		const double Tilt = FMath::DegreesToRadians(FMath::Max(FMath::Abs(Pitch), FMath::Abs(Roll)));
		const double Drop = 0.5 * Dim.X * FMath::Sin(Tilt) + 0.5 * Dim.Z * FMath::Cos(Tilt);
		FRubble* Rb = nullptr;
		if (Rubble.Num() < MaxRubble)
		{
			FRubble NR;
			NR.Comp = MakeComp(Cube, MChunk ? MChunk.Get() : MSolid.Get(), NR.Mid, true);
			KeepAlive.Add(NR.Comp);
			Rubble.Add(NR);
			Rb = &Rubble.Last();
		}
		else { Rb = &Rubble[NextRubble % Rubble.Num()]; ++NextRubble; }
		Rb->Pos = FVector(XY.X, XY.Y, Gz + Drop * 0.8);
		Rb->Q = FRotator(Pitch, Rng.FRandRange(0.f, 360.f), Roll).Quaternion();
		Rb->Scale = Dim / 100.0;
		Rb->T = 0.0; Rb->Delay = Rng.FRandRange(0.03f, 0.16f); Rb->Life = 25.0; Rb->bLive = true;
		Rb->Comp->SetVisibility(false);
		Rb->Comp->SetWorldLocationAndRotation(Rb->Pos, Rb->Q);
		Rb->Comp->SetWorldScale3D(FVector(0.01));
		if (GroundMat && Rng.FRand() < 0.4f) Rb->Comp->SetMaterial(0, GroundMat);   // the street's own look
		else if (Rb->Mid)
		{
			Rb->Comp->SetMaterial(0, Rb->Mid);
			const float Pk = Rng.FRand();
			const bool bBrick = Pk > 0.82f;
			const FLinearColor Base = bBrick ? BdBrick : Pk < 0.5f ? BdAsphalt * 2.5f : BdConcrete;   // asphalt / concrete / a little brick
			const float Vv = Rng.FRandRange(0.5f, 1.0f);
			Rb->Mid->SetVectorParameterValue(TEXT("Color"), FLinearColor(Base.R * Vv, Base.G * Vv, Base.B * Vv, 1.f));
			Rb->Mid->SetScalarParameterValue(TEXT("Rough"), 0.92f);
			Rb->Mid->SetScalarParameterValue(TEXT("Brick"), bBrick ? 1.f : 0.f);
			Rb->Mid->SetScalarParameterValue(TEXT("Seed"), Rng.FRandRange(0.f, 20.f));
		}
	}
}

void AWHBreachDirector::PlaceScar(const FVector& PosCm, const FQuat& Q, const FVector& ScaleM, const FLinearColor& Color)
{
	if (!Cyl) return;
	FScar* Sc = nullptr;
	if (Scars.Num() < MaxScars)
	{
		FScar New; New.Comp = MakeComp(Cyl, MSolid, New.Mid, false); KeepAlive.Add(New.Comp); Scars.Add(New); Sc = &Scars.Last();
	}
	else { Sc = &Scars[NextScar % Scars.Num()]; ++NextScar; }
	Sc->Comp->SetWorldLocationAndRotation(PosCm, Q);
	Sc->Comp->SetWorldScale3D(ScaleM);
	if (Sc->Mid) { Sc->Mid->SetVectorParameterValue(TEXT("Color"), Color); Sc->Mid->SetScalarParameterValue(TEXT("Rough"), 1.f); }
	Sc->Comp->SetVisibility(true);
}

void AWHBreachDirector::SpawnGc(const FVector& PosCm, const FVector& DirN)
{
	UGeometryCollection* GC = Cast<UGeometryCollection>(GcAsset.Get());
	if (!GC || MaxGcActors <= 0) return;
	if (GcActors.Num() >= MaxGcActors)
	{
		const int32 I = NextGc % GcActors.Num(); ++NextGc;
		if (GcActors[I]) GcActors[I]->Destroy();
		GcActors.RemoveAt(I);
	}
	FActorSpawnParameters SP; SP.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	AGeometryCollectionActor* A = GetWorld()->SpawnActor<AGeometryCollectionActor>(PosCm, FRotationMatrix::MakeFromX(-DirN).Rotator(), SP);
	if (!A) return;
	if (UGeometryCollectionComponent* C = A->GetGeometryCollectionComponent())
	{
		C->SetRestCollection(GC);
		C->SetSimulatePhysics(true);
		C->CrumbleActiveClusters();
	}
	A->SetLifeSpan(8.f);
	GcActors.Add(A);
}

void AWHBreachDirector::StartSlowMo()
{
	UGameplayStatics::SetGlobalTimeDilation(this, FMath::Clamp(SlowMoScale, 0.05f, 1.f));
	const double Now = FPlatformTime::Seconds();
	SlowMoUntil = Now + SlowMoReal; SlowMoEaseEnd = SlowMoUntil + 0.2;
	bSlowMo = true;
}

USoundBase* AWHBreachDirector::Authored(int32 Kind) const
{
	const TCHAR* Path = Kind == 0 ? TEXT("/Game/Invincible/Audio/S_SonicBoom.S_SonicBoom") : Kind == 1 ? TEXT("/Game/Invincible/Audio/S_Breach.S_Breach") : TEXT("/Game/Invincible/Audio/S_HeroLand.S_HeroLand");
	return LoadObject<USoundBase>(nullptr, Path);
}

void AWHBreachDirector::PlaySynth(int32 Kind, const FVector& PosCm, float Volume)
{
	if (bNoAudio) return;
	if (USoundBase* A = Authored(Kind)) { UGameplayStatics::PlaySoundAtLocation(this, A, PosCm, Volume); return; }
	// synthesized one-shot (mono 48 kHz int16): boom = N-wave crack + 38 Hz thump; crash = noise burst + debris crackle; thud = 55 Hz thump + noise
	const int32 Rate = 48000;
	const double Dur = Kind == 0 ? 1.6 : Kind == 1 ? 1.4 : 1.0;
	const int32 N = int32(Dur * Rate);
	TArray<uint8> Bytes; Bytes.SetNumUninitialized(N * 2);
	int16* Pcm = reinterpret_cast<int16*>(Bytes.GetData());
	FRandomStream R(1234 + Kind);
	double Lp = 0.0;
	for (int32 I = 0; I < N; ++I)
	{
		const double T = double(I) / Rate;
		const double Noise = R.FRandRange(-1.f, 1.f);
		Lp += (Noise - Lp) * (Kind == 1 ? 0.35 : 0.08);
		double V = 0.0;
		if (Kind == 0)
		{
			const double Crack = T < 0.012 ? (1.0 - 2.0 * T / 0.012) : 0.0;           // N-wave
			const double Thump = FMath::Sin(2.0 * PI * 38.0 * T) * FMath::Exp(-T * 3.2);
			V = 0.9 * Crack + 0.8 * Thump + 0.35 * Lp * FMath::Exp(-T * 2.0);
		}
		else if (Kind == 1)
		{
			const double Burst = Lp * FMath::Exp(-T * 3.5);
			const double Crackle = (R.FRand() < 0.004 * FMath::Exp(-T * 2.0)) ? R.FRandRange(-1.f, 1.f) : 0.0;
			V = 0.85 * Burst + 0.6 * Crackle + 0.5 * FMath::Sin(2.0 * PI * 48.0 * T) * FMath::Exp(-T * 5.0);
		}
		else
		{
			V = 0.9 * FMath::Sin(2.0 * PI * 55.0 * T) * FMath::Exp(-T * 4.5) + 0.4 * Lp * FMath::Exp(-T * 6.0);
		}
		const double Fade = FMath::Clamp((Dur - T) / 0.05, 0.0, 1.0);
		Pcm[I] = int16(FMath::Clamp(V * Fade, -1.0, 1.0) * 30000.0);
	}
	USoundWaveProcedural* W = NewObject<USoundWaveProcedural>(this);
	W->SetSampleRate(Rate);
	W->NumChannels = 1;
	W->Duration = float(Dur);
	W->SoundGroup = SOUNDGROUP_Default;
	W->bLooping = false;
	W->QueueAudio(Bytes.GetData(), Bytes.Num());
	AudioKeep.Add(W);
	if (AudioKeep.Num() > 900) AudioKeep.RemoveAt(0, 100); // old procedural waves are released (r3: the pooled components / MIDs live in KeepAlive, never trimmed)
	UGameplayStatics::PlaySoundAtLocation(this, W, PosCm, Volume);
}

void AWHBreachDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const double Dt = DeltaSeconds;
	Fx.Update(Dt, Dt);
	// slow-mo (real time)
	if (bSlowMo)
	{
		const double Now = FPlatformTime::Seconds();
		if (Now >= SlowMoEaseEnd) { UGameplayStatics::SetGlobalTimeDilation(this, 1.f); bSlowMo = false; }
		else if (Now >= SlowMoUntil)
		{
			const double K = (Now - SlowMoUntil) / FMath::Max(1e-3, SlowMoEaseEnd - SlowMoUntil);
			UGameplayStatics::SetGlobalTimeDilation(this, float(FMath::Lerp(double(SlowMoScale), 1.0, K * K * (3.0 - 2.0 * K))));
		}
	}
	// owner feedback 2026-10-15 #1: the charge slow-mo's safety end (real time), then the continuous flight FX
	if (bChargeSlow && FPlatformTime::Seconds() >= ChargeSlowEnd) EndChargeSlowMo();
	FlightFxTick(Dt);
	// chunks: retire after ChunkLife (or if they fell out of the world)
	const double Now = GetWorld()->GetTimeSeconds();
	for (FChunk& C : Chunks)
	{
		if (!C.bLive) continue;
		const double Age = Now - C.Born;
		const double Rem = double(ChunkLife) - Age;
		if (Rem <= 0.0 || C.Comp->GetComponentLocation().Z < -50000.0)
		{
			C.Comp->SetSimulatePhysics(false);
			C.Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			C.Comp->SetVisibility(false);
			C.bLive = false;
			continue;
		}
		if (Rem < 0.4)
		{ // r3: shrink out instead of popping out of existence (frozen where it lies)
			if (!C.bFrozen) { C.Comp->SetSimulatePhysics(false); C.Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision); C.bFrozen = true; }
			C.Comp->SetWorldScale3D(C.Scale * BdSmooth01(Rem / 0.4));
			continue;
		}
		if (Age > 1.2 && Now >= C.NextCheck)
		{
			// critic r2 (fl11 2.8-3.3 s: "a cube hanging in the air above the van hood"): a piece that has come to rest is checked for support below it;
			// one resting on nothing (or on an invisible moving proxy) is dissolved within 0.35 s instead of floating
			C.NextCheck = Now + 0.4;
			if (C.Comp->GetPhysicsLinearVelocity().SizeSquared() < 15.0 * 15.0)
			{
				const FVector L = C.Comp->GetComponentLocation();
				FHitResult H;
				FCollisionQueryParams Q(SCENE_QUERY_STAT(WHBreachHang), false);
				Q.AddIgnoredComponent(C.Comp);
				FCollisionObjectQueryParams Obj;
				Obj.AddObjectTypesToQuery(ECC_WorldStatic); Obj.AddObjectTypesToQuery(ECC_WorldDynamic); Obj.AddObjectTypesToQuery(ECC_PhysicsBody);
				bool bSupported = GetWorld()->LineTraceSingleByObjectType(H, L, L - FVector(0.0, 0.0, double(C.Comp->Bounds.SphereRadius) + 12.0), Obj, Q);
				if (bSupported && H.GetComponent() && H.GetComponent()->GetCollisionObjectType() == ECC_WorldDynamic && !H.GetComponent()->IsVisible()) bSupported = false;
				if (!bSupported) C.Born = Now - (double(ChunkLife) - 0.35);
			}
		}
	}
	// r3 puffs: dense dust (hidden until its delay, fades in over ~0.16 s, grows with an ease-out, lingers, fades over the last 60 %)
	for (FPuff& Pf : Puffs)
	{
		if (!Pf.bLive) continue;
		Pf.T += Dt;
		if (Pf.T < Pf.Delay) continue;
		const double Age = Pf.T - Pf.Delay;
		if (Age >= Pf.Life) { Pf.bLive = false; Pf.Comp->SetVisibility(false); continue; }
		if (!Pf.bShown) { Pf.bShown = true; Pf.Comp->SetVisibility(true); }
		const double K = Age / Pf.Life;
		Pf.Vel *= FMath::Exp(-Pf.Drag * Dt);
		Pf.Pos += Pf.Vel * Dt + FVector(0.0, 0.0, Pf.Rise * Dt * (1.0 - K));
		const double Sz = FMath::Lerp(Pf.S0, Pf.S1, BdEaseOut(K));
		const double Op = Pf.Peak * BdSmooth01(Age / 0.16) * (1.0 - BdSmooth01((K - 0.40) / 0.60));
		Pf.Comp->SetWorldLocation(Pf.Pos);
		Pf.Comp->SetWorldScale3D(FVector(Sz / 100.0));
		if (Pf.Mid) Pf.Mid->SetScalarParameterValue(TEXT("Opacity"), float(Op));
	}
	// r3 vapour: the sonic-boom cone / rings follow the hero for Follow s (HeroPosCm is written by the pawn every frame), grow with an ease-out
	// and fade; the ground shock ring is a vapour pancake that does not follow
	{
		const UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this);
		for (FVapour& Vp : Vapours)
		{
			if (!Vp.bLive) continue;
			Vp.T += Dt;
			if (Vp.T >= Vp.Life) { Vp.bLive = false; Vp.Comp->SetVisibility(false); continue; }
			const double K = Vp.T / Vp.Life;
			// (owner feedback 2026-10-15: + SideCm for the glued contrails; a piece that does not follow drifts at VelCm)
			if (Vp.T < Vp.Follow && FW && FW->bHeroValid) Vp.Anchor = FW->HeroPosCm + Vp.Dir * Vp.OffsetCm + Vp.SideCm;
			else Vp.Anchor += Vp.VelCm * Dt;
			const double E = BdEaseOut(K);
			const double Rad = FMath::Lerp(Vp.Rad0, Vp.Rad1, E);
			if (Vp.Shape == 2)
			{ // owner feedback 2026-10-15 #1: a sphere shell (the boom's shock shell, the charge's gathering vapour)
				Vp.Comp->SetWorldLocationAndRotation(Vp.Anchor, FRotationMatrix::MakeFromZ(Vp.Dir).ToQuat());
				Vp.Comp->SetWorldScale3D(FVector(2.0 * Rad / 100.0));
			}
			else if (Vp.Shape == 3)
			{ // owner feedback 2026-10-15 #1 / #3: a speed line -- an ellipsoid Len long along Dir, centred on Anchor
				const double Len = FMath::Lerp(Vp.Len0, Vp.Len1, E);
				Vp.Comp->SetWorldLocationAndRotation(Vp.Anchor, FRotationMatrix::MakeFromZ(Vp.Dir).ToQuat());
				Vp.Comp->SetWorldScale3D(FVector(2.0 * Rad / 100.0, 2.0 * Rad / 100.0, FMath::Max(1.0, Len) / 100.0));
				if (Vp.Mid && FMath::Abs(Vp.Len1 - Vp.Len0) > 1.0) Vp.Mid->SetScalarParameterValue(TEXT("HalfLen"), float(FMath::Max(1.0, Len * 0.5)));
			}
			else if (Vp.bCone)
			{
				// apex at Anchor, opening backwards along -Dir; the mesh's own pivot / apex end come from ProbeCone()
				const double Len = FMath::Lerp(Vp.Len0, Vp.Len1, E);
				const double Sx = 2.0 * Rad / FMath::Max(1.0, ConeWCm), Sz = Len / FMath::Max(1.0, ConeHCm);
				const FQuat Q = FRotationMatrix::MakeFromZ(bConeApexUp ? Vp.Dir : -Vp.Dir).ToQuat();
				const FVector CenterW = Vp.Anchor - Vp.Dir * (Len * 0.5);
				Vp.Comp->SetWorldLocationAndRotation(CenterW - Q.RotateVector(FVector(0.0, 0.0, ConeMidZCm * Sz)), Q);
				Vp.Comp->SetWorldScale3D(FVector(Sx, Sx, Sz));
			}
			else
			{
				const double Thick = FMath::Max(40.0, Rad * 0.18);
				Vp.Comp->SetWorldLocationAndRotation(Vp.Anchor, FRotationMatrix::MakeFromZ(Vp.Dir).ToQuat());
				Vp.Comp->SetWorldScale3D(FVector(2.0 * Rad / 100.0, 2.0 * Rad / 100.0, Thick / 100.0));
			}
			if (Vp.Mid)
			{ // envelopes (owner feedback 2026-10-15): 0 the r3 fade-out after 40 %, 1 gather (ramps up to the launch), 2 speed line (quick in, fades over the second half)
				double Op = Vp.Peak * BdSmooth01(Vp.T / 0.05) * (1.0 - BdSmooth01((K - 0.40) / 0.60));
				if (Vp.Env == 1) Op = Vp.Peak * BdSmooth01(K / 0.8) * (1.0 - BdSmooth01((K - 0.92) / 0.08));
				else if (Vp.Env == 2) Op = Vp.Peak * BdSmooth01(Vp.T / 0.04) * (1.0 - BdSmooth01((K - 0.5) / 0.5));
				Vp.Mid->SetScalarParameterValue(TEXT("Opacity"), float(Op));
			}
		}
	}
	// r3 decals: the opening / crater grows open (the material's Open parameter, ease-out) over Grow s
	for (TArray<FDecalItem>* Pool : { &HoleDecals, &CraterDecals })
		for (FDecalItem& Dc : *Pool)
		{
			if (!Dc.bGrowing) continue;
			Dc.T += Dt;
			const double K = FMath::Clamp(Dc.T / FMath::Max(1e-3, Dc.Grow), 0.0, 1.0);
			if (Dc.Mid) Dc.Mid->SetScalarParameterValue(TEXT("Open"), float(K));
			if (K >= 1.0) Dc.bGrowing = false;
		}
	// r3 crater rim rubble: pops in with a small overshoot after its delay, stays, shrinks out over its last 0.6 s
	for (FRubble& Rb : Rubble)
	{
		if (!Rb.bLive) continue;
		Rb.T += Dt;
		if (Rb.T < Rb.Delay) continue;
		const double Age = Rb.T - Rb.Delay;
		if (Age >= Rb.Life) { Rb.bLive = false; Rb.Comp->SetVisibility(false); continue; }
		if (!Rb.Comp->IsVisible()) Rb.Comp->SetVisibility(true);
		double S = 1.0;
		if (Age < 0.22) { const double K = Age / 0.22; S = 0.15 + 0.85 * K + 0.14 * FMath::Sin(K * PI); }
		else if (Age > Rb.Life - 0.6) S = BdSmooth01((Rb.Life - Age) / 0.6);
		const FVector Target = Rb.Scale * S;
		if (!Rb.Comp->GetComponentScale().Equals(Target, 1e-3)) Rb.Comp->SetWorldScale3D(Target);
	}
	// glass: ballistic, spinning, fading
	for (FShard& S : Shards)
	{
		if (!S.bLive) continue;
		S.T += Dt;
		if (S.T >= S.Life) { S.bLive = false; S.Comp->SetVisibility(false); continue; }
		S.Vel += FVector(0, 0, -980.0) * Dt;
		S.Vel *= FMath::Exp(-0.8 * Dt);
		S.Pos += S.Vel * Dt;
		if (S.Spin.SizeSquared() > 0) S.Q = (FQuat(S.Spin.GetSafeNormal(), S.Spin.Size() * Dt) * S.Q).GetNormalized();
		S.Comp->SetWorldLocationAndRotation(S.Pos, S.Q);
		if (S.Mid) S.Mid->SetScalarParameterValue(TEXT("Opacity"), float(0.7 * (1.0 - S.T / S.Life)));
	}
	// shock rings (r2 fallback only): flattened sphere expanding square-on to the flight line
	for (FRing& Rg : Rings)
	{
		if (!Rg.bLive) continue;
		Rg.T += Dt;
		const double K = FMath::Clamp(Rg.T / Rg.Life, 0.0, 1.0);
		if (K >= 1.0) { Rg.bLive = false; Rg.Comp->SetVisibility(false); continue; }
		const double R = 0.5 + Rg.R1 * (1.0 - (1.0 - K) * (1.0 - K));
		Rg.Comp->SetWorldLocationAndRotation(Rg.Pos, Rg.Q);
		Rg.Comp->SetWorldScale3D(FVector(R, R, 0.04 + 0.3 * K));
		if (Rg.Mid)
		{
			Rg.Mid->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.85f, 0.9f, 1.0f, 1.f));
			Rg.Mid->SetScalarParameterValue(TEXT("Opacity"), float(0.45 * (1.0 - K)));
		}
	}
}
