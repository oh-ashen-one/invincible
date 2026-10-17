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
#include "Camera/PlayerCameraManager.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundWaveProcedural.h"
#include "GeometryCollection/GeometryCollectionActor.h"
#include "GeometryCollection/GeometryCollectionComponent.h"
#include "GeometryCollection/GeometryCollectionObject.h"
#include "HAL/PlatformTime.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "MaterialShared.h"
#include "RHIShaderPlatform.h"
#include "CoreGlobals.h"

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
	/** critic r4: distance from P to the segment A-B (and the segment parameter 0..1 of the closest point) */
	double BdSegDist(const FVector& P, const FVector& A, const FVector& B, double* OutT = nullptr)
	{
		const FVector AB = B - A;
		const double L2 = AB.SizeSquared();
		const double T = L2 > 1e-6 ? FMath::Clamp(FVector::DotProduct(P - A, AB) / L2, 0.0, 1.0) : 0.0;
		if (OutT) *OutT = T;
		return FVector::Dist(P, A + AB * T);
	}
	/** critic r4: approximate distance from a point to an ellipsoid surface (centre C, rotation Q, semi-axes Semi; 0 inside), along the ray
	 *  from its centre */
	double BdEllipsoidDist(const FVector& P, const FVector& C, const FQuat& Q, const FVector& Semi)
	{
		const FVector L = Q.UnrotateVector(P - C);
		const FVector Qn(L.X / FMath::Max(1.0, Semi.X), L.Y / FMath::Max(1.0, Semi.Y), L.Z / FMath::Max(1.0, Semi.Z));
		const double Qs = Qn.Size();
		return Qs <= 1.0 ? 0.0 : L.Size() * (1.0 - 1.0 / Qs);
	}
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
	// critic r6 #8: glass-tower dust is a cool pale grey
	const FLinearColor BdGlassDust(0.30f, 0.33f, 0.36f);
	/** critic r6 #8: the breach opening's outline radius (box units: the decal edge = 1) at angle Th around its centre, Grow 0..1 -- the SAME ragged-star
	 *  formula as hole_field in Scripts/build_invincible_fx.py (without that shader's +-0.035 noise warp), so the rim chunks sit on the drawn edge */
	double BdHoleRadius(double Th, double Seed, double Grow)
	{
		auto Tri = [](double X) { return FMath::Abs(FMath::Frac(X) - 0.5) * 2.0; };
		const double Pf = 0.58 + 0.17 * Tri(Th * 1.11408 + Seed * 0.713) + 0.10 * Tri(Th * 1.75070 + Seed * 0.377 + 0.31) + 0.07 * Tri(Th * 3.02394 + Seed * 0.911 + 0.57)
			+ 0.09 * FMath::Sin(Th * 2.0 + Seed * 9.1) + 0.06 * FMath::Sin(Th * 3.0 + Seed * 4.3);
		return Pf * 0.58 * (0.12 + 0.88 * Grow);
	}
	/** critic r6 #8: the facade "style" of the triangle a complex trace hit in a merged city facade mesh. build_city's Facade.ush reads
	 *  style = UV channel 4 .y + 0.01 (1 masonry, 2 curtain-wall glass, 3 ribbon windows, 4 deco, 5 party wall, 6 stainless crown). FaceIndex counts the
	 *  triangles of the sections that have collision, in order (the way UStaticMeshComponent::GetMaterialFromCollisionFaceIndex walks them).
	 *  -1 when the mesh keeps no CPU copy (cooked builds without bAllowCPUAccess) or has fewer than 5 UV channels. */
	int32 BdFacadeStyle(const UStaticMeshComponent* SMC, int32 FaceIndex)
	{
		if (!SMC || FaceIndex < 0) return -1;
		const UStaticMesh* Mesh = SMC->GetStaticMesh();
		const FStaticMeshRenderData* RD = Mesh ? Mesh->GetRenderData() : nullptr;
		if (!RD) return -1;
		const int32 LodI = Mesh->LODForCollision;
		if (!RD->LODResources.IsValidIndex(LodI)) return -1;
		const FStaticMeshLODResources& L = RD->LODResources[LodI];
		const FStaticMeshVertexBuffer& VB = L.VertexBuffers.StaticMeshVertexBuffer;
		if (VB.GetNumTexCoords() <= 4 || !VB.GetAllowCPUAccess() || !L.IndexBuffer.GetAllowCPUAccess()) return -1;
		int32 Total = 0, Tri = -1;
		for (const FStaticMeshSection& Sec : L.Sections)
		{
			if (!Sec.bEnableCollision) continue;
			if (FaceIndex < Total + int32(Sec.NumTriangles)) { Tri = int32(Sec.FirstIndex / 3) + (FaceIndex - Total); break; }
			Total += int32(Sec.NumTriangles);
		}
		if (Tri < 0 || Tri * 3 + 2 >= L.IndexBuffer.GetNumIndices()) return -1;
		int32 Votes[8] = {};
		for (int32 K = 0; K < 3; ++K)
		{
			const uint32 Vi = L.IndexBuffer.GetIndex(uint32(Tri * 3 + K));
			if (Vi >= VB.GetNumVertices()) return -1;
			const int32 St = FMath::FloorToInt(VB.GetVertexUV(Vi, 4).Y + 0.01f);
			if (St >= 0 && St < 8) ++Votes[St];
		}
		int32 Best = 0;
		for (int32 I = 1; I < 8; ++I) if (Votes[I] > Votes[Best]) Best = I;
		return Votes[Best] > 0 ? Best : -1;
	}
	/** critic r6 #8: is this a city facade material (M_CityFacade, or an instance of it) */
	bool BdIsFacadeMat(const UMaterialInterface* M)
	{
		if (!M) return false;
		if (M->GetName().Contains(TEXT("CityFacade"))) return true;
		const UMaterial* B = M->GetMaterial();
		return B && B->GetName().Contains(TEXT("CityFacade"));
	}
	bool BdTagHasAny(const FString& Tag, const TCHAR* const* Keys, int32 N)
	{
		for (int32 I = 0; I < N; ++I) if (Tag.Contains(Keys[I])) return true;
		return false;
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
	// critic r5 #8: one continuous shock-ring annulus (optional; the segmented tubes stay the fallback)
	MRing = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Invincible/FX/M_InvShockRing.M_InvShockRing"));
	// critic r6 #8: glass-tower pane shards (optional; M_CmbTrans stands in)
	MGlassShard = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Invincible/FX/M_InvGlassShard.M_InvGlassShard"));
	Cone = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cone.Cone"));
	ProbeCone();
	GcAsset = LoadObject<UGeometryCollection>(nullptr, TEXT("/Game/Invincible/Destruction/GC_FacadeChunk.GC_FacadeChunk"));
	bNoSlowMo = FParse::Param(FCommandLine::Get(), TEXT("WHNoSlowMo"));
	bNoAudio = FParse::Param(FCommandLine::Get(), TEXT("WHNoFlightAudio"));
	{ float Fc = FacadeChunkFraction; if (FParse::Value(FCommandLine::Get(), TEXT("-WHFacadeChunks="), Fc)) FacadeChunkFraction = FMath::Clamp(Fc, 0.f, 1.f); }
	Fx.Init(this);
	ExcludeHeroFromDecals();   // r3: the opening / crater decals must not paint the hero when he flies through them
	PrewarmPools();            // critic r5 #3 / #8
	UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT breach director ready: materials %s, authored fracture %s, crater decal %s, slow-mo %s"),
		MSolid && MTrans ? TEXT("ok") : TEXT("FALLBACK"), GcAsset ? TEXT("yes") : TEXT("no (proxy chunks only)"), MDecal ? TEXT("yes") : TEXT("no (disc)"),
		bNoSlowMo ? TEXT("off") : TEXT("on"));
	UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT breach fx r3: hole decal %s, vapour %s (cone mesh %s, apex %s, %.0f x %.0f cm), dust %s, chunk material %s, facade chunk share %.2f"),
		MHole ? TEXT("yes") : TEXT("no"), MVapour ? TEXT("yes") : TEXT("no (r2 rings)"), Cone ? TEXT("yes") : TEXT("no"), bConeApexUp ? TEXT("+Z") : TEXT("-Z"), ConeWCm, ConeHCm,
		MDust ? TEXT("yes") : TEXT("no (combat puffs)"), MChunk ? TEXT("yes") : TEXT("no (flat tints)"), FacadeChunkFraction);
	UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT flight fx (owner feedback 2026-10-15): streak material %s, vapour pool cap %d"),
		MStreak ? TEXT("M_InvStreak") : (MVapour ? TEXT("M_InvVapour (fallback)") : TEXT("none (no streaks)")), MaxVapours);
	UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT breach fx r6: shock ring %s, prewarmed %d hole / %d crater decals, %d debris pieces"),
		MRing ? TEXT("M_InvShockRing (one annulus)") : TEXT("segmented tubes (fallback)"), HoleDecals.Num(), CraterDecals.Num(), Chunks.Num());
	UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT breach fx r7: glass shard material %s, %d hole-rim / %d pane pieces prewarmed, hole rim %d per breach"),
		MGlassShard ? TEXT("M_InvGlassShard") : TEXT("M_CmbTrans (fallback)"), HoleRim.Num(), Panes.Num(), RimPerHole);
}

// critic r5 #3 (a first-use decal rendered its whole box as a flat dark panel for one frame: fl15 3.85 s, fl11 2.28 s, fl17 20.68 s) / #8:
// the FX materials' shader maps are finished now, the decal pools exist from the start (registered, hidden, parameters at rest) and so does
// part of the debris pool, so no FX component is created (or first drawn with a new material) on the impact frame
void AWHBreachDirector::PrewarmPools()
{
	for (UMaterialInterface* M : { MHole.Get(), MDecal.Get(), MChunk.Get(), MDust.Get(), MVapour.Get(), MStreak.Get(), MRing.Get(), MSolid.Get(), MTrans.Get(), MGlassShard.Get() })
		if (M) if (FMaterialResource* R = M->GetMaterialResource(GMaxRHIShaderPlatform)) R->FinishCompilation();
	if (MHole) while (HoleDecals.Num() < MaxHoleDecals) { if (!AcquireDecal(HoleDecals, NextHole, MaxHoleDecals, MHole)) break; }
	if (MDecal) while (CraterDecals.Num() < MaxCraterDecals) { if (!AcquireDecal(CraterDecals, NextCrater, MaxCraterDecals, MDecal)) break; }
	NextHole = 0; NextCrater = 0;
	if (Cube) { const int32 N = FMath::Min(MaxChunks, ChunksPerBreach * 2); while (Chunks.Num() < N) { if (!NewChunk()) break; } }
	// critic r6 #8: a first set of hole-rim pieces (static, hidden) and glass panes, so neither is first created on an impact frame
	if (Cube)
	{
		const int32 NR = FMath::Min(MaxHoleRim, RimPerHole * 2);
		while (HoleRim.Num() < NR)
		{
			FRubble NRb; NRb.Comp = MakeComp(Cube, MChunk ? MChunk.Get() : MSolid.Get(), NRb.Mid, true); KeepAlive.Add(NRb.Comp);
			if (MGlassShard) { NRb.GlassMid = UMaterialInstanceDynamic::Create(MGlassShard, this); KeepAlive.Add(NRb.GlassMid); }
			HoleRim.Add(NRb);
		}
		const int32 NP = FMath::Min(MaxPanes, ShardsPerBreach);
		UMaterialInterface* PaneBase = MGlassShard ? MGlassShard.Get() : (MTrans ? MTrans.Get() : MSolid.Get());
		while (Panes.Num() < NP)
		{
			FShard NSh; NSh.Comp = MakeComp(Cube, PaneBase, NSh.Mid, false); NSh.bPane = true; KeepAlive.Add(NSh.Comp);
			if (NSh.Mid) NSh.Mid->SetScalarParameterValue(TEXT("Opacity"), 0.f);
			Panes.Add(NSh);
		}
	}
	// the boom's pieces: 2 cones, 6 rings, 16 streaks (more are still made on demand up to MaxVapours)
	if (MVapour && Sphere)
	{
		const int32 Want[6] = { Cone ? 2 : 0, 0, 0, 16, MRing ? 0 : 24, MRing ? 6 : 0 };
		for (int32 Sh = 0; Sh < 6; ++Sh)
			for (int32 K = 0; K < Want[Sh] && Vapours.Num() < FMath::Max(24, MaxVapours); ++K)
			{
				FVapour N; N.bCone = Sh == 0; N.Shape = Sh;
				UMaterialInterface* Base = (Sh == 3 && MStreak) ? MStreak.Get() : (Sh == 5 && MRing) ? MRing.Get() : MVapour.Get();
				N.Comp = MakeComp(Sh == 0 ? Cone.Get() : Sphere.Get(), Base, N.Mid, false);
				if (N.Mid) N.Mid->SetScalarParameterValue(TEXT("Opacity"), 0.f);
				KeepAlive.Add(N.Comp);
				Vapours.Add(N);
			}
	}
}

AWHBreachDirector::FChunk* AWHBreachDirector::NewChunk()
{
	if (!Cube || Chunks.Num() >= MaxChunks) return nullptr;
	FChunk New;
	New.Comp = MakeComp(Cube, MChunk ? MChunk.Get() : MSolid.Get(), New.Mid, true);
	New.Comp->SetCollisionProfileName(TEXT("PhysicsActor"));
	New.Comp->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
	New.Comp->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
	New.Comp->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
	New.Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	KeepAlive.Add(New.Comp);
	Chunks.Add(New);
	return &Chunks.Last();
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
	TraceFacade(bEntry ? P - D * 200.0 : P + D * 300.0, bEntry ? P + D * 200.0 : P - D * 200.0, Hit, /*bDescribe*/ true);
	FVector Pt = P, OutN = bEntry ? -D : D;   // outward facade normal (fallbacks: the flight line is ~ square-on)
	const bool bOnWall = Hit.bHit && FVector::Dist(Hit.Point, P) < 260.0 && FMath::Abs(Hit.Normal.Z) < 0.8;
	if (bOnWall)
	{
		Pt = Hit.Point; OutN = Hit.Normal;
		if (FVector::DotProduct(OutN, D) * (bEntry ? 1.0 : -1.0) > 0.0) OutN = -OutN;   // entry: faces against the flight; exit: along it
	}
	if (Hit.Mat) LastFacadeMat = Hit.Mat;
	// critic r6 #8: what was hit decides everything below. The facade plane around the hit is measured once (FitHoleHalf: the decal box that stays on
	// the wall, and the narrower in-plane span that tells a girder or a fire escape from a building wall).
	const double Half0 = HoleHalfCm * (1.0 + 0.18 * Sev);
	FVector Shift = FVector::ZeroVector;
	double Half = Half0, Span = -1.0;
	if (bOnWall && (MHole || !Hit.bFacadeSeen)) Half = FitHoleHalf(Pt, OutN, Half0, Shift, &Span);
	const EBdSurf Kind = ClassifyHit(Hit, bOnWall, Pt, Span);
	if (Kind == EBdSurf::Thin)
	{
		// critic r6 #8 (fl15 10.15 s: the clip ended on "a small hole in a bridge girder"): a thin / non-building solid -- no hole, no big debris
		ThinStrike(Pt, bOnWall ? OutN : (bEntry ? -D : D), D, Sev, bEntry);
		UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT breach %s fx at %s: thin / non-building solid (sparks + dust only; tag '%s', facade material %s, span %.0f cm)"),
			bEntry ? TEXT("in") : TEXT("out"), *PosM.ToString(), *Hit.Tag.Left(120), Hit.bFacadeSeen ? TEXT("yes") : TEXT("no"), Span);
		return;
	}
	UMaterialInterface* Look = (Kind == EBdSurf::Masonry) ? (Hit.Mat ? Hit.Mat : LastFacadeMat.Get()) : nullptr;   // (a glass / steel facade never wears the masonry look)
	// debris: >= 20 pieces (ChunksPerBreach = 44) of mixed size, many small 8-25 cm and a few to 50 cm, scattered over the opening on the outside
	// of the wall. Entry: they spray sideways / up / out of the hole (the wall is solid, the camera is outside); exit: they are blown out ahead.
	// critic r6 #8 (fl17 12.9 s: "a glass tower threw bricks"): by facade type -- curtain-wall glass: thin translucent glassy panes + a few steel bits;
	// a steel crown tier: steel plates / bars; masonry: concrete / brick chunks as before, with only a few window glints.
	const double Sp = 700.0 + 1300.0 * Sev;   // (r2: 18-44 m/s, the pieces left the frame within 0.2 s)
	if (Cube)
	{
		const FVector Org = Pt + OutN * 18.0;
		if (Kind == EBdSurf::Glass)
		{
			SpawnPanes(Org, bEntry ? OutN : D, ShardsPerBreach, Sp * 1.15);
			SpawnDebris(Org, OutN, HoleHalfCm * 0.40, Sp, bEntry ? 0.35 : 0.8, FMath::Max(4, ChunksPerBreach / 3), nullptr, BdSteel, 0.f, 1);
			SpawnShards(Org, bEntry ? OutN : D, 8, Sp * 1.2);
		}
		else if (Kind == EBdSurf::Steel)
		{
			SpawnDebris(Org, OutN, HoleHalfCm * 0.40, Sp, bEntry ? 0.35 : 0.8, FMath::Max(6, ChunksPerBreach * 2 / 3), nullptr, BdSteel, 0.f, 1);
			SpawnShards(Org, bEntry ? OutN : D, 6, Sp * 1.2);
		}
		else
		{
			SpawnDebris(Org, OutN, HoleHalfCm * 0.40, Sp, bEntry ? 0.35 : 0.8, ChunksPerBreach, Look, bEntry ? BdConcrete : BdBrick, bEntry ? 0.25f : 0.6f);
			SpawnShards(Org, bEntry ? OutN : D, 10, Sp * 1.2);
		}
	}
	// dust: dense, larger, longer-lived puffs around the opening (critic r2: "see-through bubble smoke")
	if (MDust && Sphere) BreachDust(Pt, OutN, D, Sev, bEntry, Kind);
	else
	{
		Fx.Dust(PosM, 2.5 + 2.5 * Sev);
		Fx.Dust(PosM + D * 3.0, 2.0 + 2.0 * Sev);
	}
	{ FLinearColor Spark(3.0f, 2.2f, 1.4f); Fx.Hit(Pt / 100.0, bEntry ? OutN : D, 1.0, &Spark); }
	// the hole: a deferred decal on the facade at the entry and the exit (M_BreachHole r7: jagged opening with a recessed interior, a lit reveal,
	// a broken rim, cracks); facing the facade normal (~ -D at the entry), it grows open over 0.18 s. The decal's frame goes to the material and
	// RimPerHole lit rim chunks are seated on its edge (PlaceHole).
	// (critic r1 + r2 capture fl14: the scorched plate -- a flat 3-5 m cylinder disc flush with the facade -- read as a black ellipse
	//  stamped on an intact wall and filled the frame when the camera was close; no plate when the decal asset is missing)
	if (MHole) PlaceHole(Pt, -OutN, Sev, Half, Shift, Kind, bOnWall);
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
	UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT breach %s fx at %s sev %.2f (chunks live %d; facade trace %s%s, facade material %s, surface %s, style %d, hole decal %s, dust %s)"), bEntry ? TEXT("in") : TEXT("out"), *PosM.ToString(), Sev,
		Chunks.FilterByPredicate([](const FChunk& C) { return C.bLive; }).Num(), Hit.bHit ? TEXT("hit") : TEXT("miss"), Hit.bHit ? *FString::Printf(TEXT(" n (%.2f, %.2f, %.2f)"), OutN.X, OutN.Y, OutN.Z) : TEXT(""),
		Look ? *Look->GetName() : TEXT("none"), Kind == EBdSurf::Glass ? TEXT("glass tower") : Kind == EBdSurf::Steel ? TEXT("steel") : TEXT("masonry"), Hit.Style,
		MHole ? TEXT("yes") : TEXT("no"), MDust ? TEXT("dense") : TEXT("combat puffs"));
}

// critic r6 #8: what the trace's first surface is called (lower-case component / owner / mesh / material names in Tag)
void AWHBreachDirector::DescribeSurface(UPrimitiveComponent* C, UMaterialInterface* M, int32 FaceIndex, FFacadeHit& Out) const
{
	(void)FaceIndex;
	if (!C) return;
	FString Tag = C->GetName();
	if (const AActor* Ow = C->GetOwner()) Tag += TEXT(" ") + Ow->GetName();
	if (const UStaticMeshComponent* SMC = Cast<UStaticMeshComponent>(C))
		if (const UStaticMesh* Mesh = SMC->GetStaticMesh()) Tag += TEXT(" ") + Mesh->GetName();
	if (M) Tag += TEXT(" ") + M->GetName();
	Out.Tag = Tag.ToLower();
}

// critic r6 #8: the type of what the breach went through.
//  1. a city facade material anywhere along the trace = a building wall; its merged-mesh style picks glass (2 curtain wall, 3 ribbon) / steel (6 crown) /
//     masonry (everything else). Without CPU vertex data (cooked build) the style is unknown: a name containing glass / curtain says glass, else
//     a hit above TowerHeightCm is taken for a curtain-wall tower and anything lower for masonry.
//  2. no facade material: thin / non-building solids by name (bridge, girder, truss, cable, deck, fire escape, kit pieces, asphalt, sidewalk ...) or by
//     the narrow in-plane span of the surface (< 2.2 m: a beam, a rail) are Thin; a horizontal surface other than a roof is Thin; the rest (roofs, a
//     landmark / podium wall) is masonry, glass when its name says so.
AWHBreachDirector::EBdSurf AWHBreachDirector::ClassifyHit(const FFacadeHit& H, bool bOnWall, const FVector& PointCm, double SpanCm) const
{
	(void)bOnWall;
	static const TCHAR* const GlassKeys[] = { TEXT("glass"), TEXT("curtain"), TEXT("mirror") };
	static const TCHAR* const ThinKeys[] = { TEXT("bridge"), TEXT("girder"), TEXT("truss"), TEXT("cable"), TEXT("railing"), TEXT("pylon"), TEXT("beam"), TEXT("deck"),
		TEXT("fireescape"), TEXT("scaffold"), TEXT("crane"), TEXT("antenna"), TEXT("streetkit"), TEXT("awning"), TEXT("citykit"), TEXT("citydetail"), TEXT("cityframe"),
		TEXT("citysignage"), TEXT("citycar"), TEXT("cityprop"), TEXT("asphalt"), TEXT("sidewalk"), TEXT("cityland"), TEXT("coast"), TEXT("water"), TEXT("terrain") };
	if (H.bFacadeSeen)
	{
		if (BdTagHasAny(H.Tag, GlassKeys, UE_ARRAY_COUNT(GlassKeys))) return EBdSurf::Glass;
		if (H.Style == 2 || H.Style == 3) return EBdSurf::Glass;
		if (H.Style == 6) return EBdSurf::Steel;
		if (H.Style >= 0) return EBdSurf::Masonry;
		return PointCm.Z > double(TowerHeightCm) ? EBdSurf::Glass : EBdSurf::Masonry;   // style unreadable: height fallback
	}
	if (!H.bHit) return EBdSurf::Masonry;   // nothing traced: the old behaviour (a building hole at the flight line)
	if (BdTagHasAny(H.Tag, ThinKeys, UE_ARRAY_COUNT(ThinKeys))) return EBdSurf::Thin;
	if (FMath::Abs(H.Normal.Z) >= 0.8) return H.Tag.Contains(TEXT("roof")) ? EBdSurf::Masonry : EBdSurf::Thin;
	if (SpanCm >= 0.0 && SpanCm < 220.0) return EBdSurf::Thin;
	if (BdTagHasAny(H.Tag, GlassKeys, UE_ARRAY_COUNT(GlassKeys))) return EBdSurf::Glass;
	return EBdSurf::Masonry;
}

// critic r6 #8 (fl15: "a small hole in a bridge girder"): a thin / non-building solid gets a spark flash, three to five small dust puffs, a few small
// steel bits and a quiet impact -- no hole decal, no rim, no pane or brick debris, no building-breach tally (a small collateral cost only)
void AWHBreachDirector::ThinStrike(const FVector& PtCm, const FVector& N, const FVector& D, float Sev, bool bEntry)
{
	FVector Nn = N.GetSafeNormal();
	if (Nn.IsNearlyZero()) Nn = -D;
	{ FLinearColor Spark(3.0f, 2.4f, 1.6f); Fx.Hit(PtCm / 100.0, Nn, 0.8, &Spark); }
	if (MDust && Sphere)
	{
		FVector U, V; BdPlaneBasis(Nn, U, V);
		const int32 NP = 3 + int32(2 * Sev);
		for (int32 K = 0; K < NP; ++K)
		{
			const FVector Rad = U * Rng.FRandRange(-1.f, 1.f) + V * Rng.FRandRange(-1.f, 1.f);
			const double S0 = Rng.FRandRange(40.f, 70.f);
			SpawnPuff(PtCm + Nn * Rng.FRandRange(15.f, 40.f) + Rad * 30.0, Nn * Rng.FRandRange(60.f, 160.f) + Rad * Rng.FRandRange(60.f, 180.f) + (bEntry ? FVector::ZeroVector : D * 120.0),
				S0, S0 * Rng.FRandRange(2.2f, 3.0f), Rng.FRandRange(0.7f, 1.0f), Rng.FRandRange(0.32f, 0.45f), Rng.FRandRange(0.f, 0.06f), BdDust * Rng.FRandRange(0.7f, 0.95f));
		}
	}
	else Fx.Dust(PtCm / 100.0, 0.6 + 0.6 * Sev);
	if (Cube) SpawnDebris(PtCm + Nn * 10.0, Nn, 25.0, 420.0 + 380.0 * Sev, 0.6, 3 + int32(3 * Sev), nullptr, BdSteel, 0.f, 1, 0.5f);
	PlaySynth(1, PtCm, 0.30f + 0.15f * Sev);
	if (UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this)) FW->AddCollateral(3000.f + 9000.f * Sev, TEXT("structure hit"));
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
		// (critic r5 #8: "untextured grey cubes" in fl11 / fl12 -- the street's own material does not map onto a cube; every crater piece wears
		//  the M_InvChunk concrete / asphalt look now)
		SpawnDebris(P + FVector(0, 0, 18.0), FVector::UpVector, 90.0, 520.0 + 700.0 * Sev, 0.7, ChunksPerCrater, nullptr, BdConcrete, 0.1f);
		SpawnRim(P, Sev, nullptr);
	}
	if (MDust && Sphere) CraterDust(P, Sev);
	else Fx.Dust(P / 100.0, 3.0 + 4.0 * Sev);
	// critic r4 fl11 / fl12 / fl17 (a flat WHITE disc of up to 273k px at the slam landing): the ground shock ring was a thin vapour pancake
	// 0.25 m over the street -- seen from the chase lens at a grazing angle its whole top face is fresnel-opaque, and since the vapour went
	// exposure-independent it rendered as a white ellipse. Removed: the shock reads through the low dust ring thrown outward (CraterDust),
	// the ejecta, the rim and the camera impact.
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
	// critic r4 fl04 / fl12 ("the boom is a set of concentric flat screen-facing discs"; the r3 9 m cone and the pancake rings sat around / on
	// the lens axis, so they read face-on, and the lens flew through them): everything is built AROUND the hero, sized so the 3/4 chase lens
	// (~2.8-4 m back, ~1.6-2 m off the travel axis) stays outside, and glued to him while he ramps up (the launch now accelerates over ~0.16 s):
	//  - a vapour cone wrapped round his body: apex BoomConeLeadM ahead of his chest, base just past his hips, BoomConeRadM -> 1.7x (the
	//    lens sees its flank and its open base in perspective: a cone opening along the travel axis);
	//  - two shock rings of vapour tubes around him (around the chest and the hips, the second drifting back slowly), radius 0.7 -> 2.3 m /
	//    1.2 -> 3.2 m: seen off-axis they read as ellipses around the body for 0.5-0.7 s;
	//  - speed lines bursting back along the cone flank (never on the lens side).
	bool bVapour = false;
	FVector CamSide = FVector::ZeroVector;   // unit, perpendicular to D, toward the lens
	{
		FVector Cv;
		if (ViewPos(Cv)) { const FVector Rel = Cv - PCm; CamSide = (Rel - D * FVector::DotProduct(Rel, D)).GetSafeNormal(); }
	}
	if (MVapour)
	{
		if (Cone)
		{
			const double Lead = double(BoomConeLeadM) * 100.0;
			// critic r6 #4 (fl04 1.517: the frame centre was a lifted haze): the cone keeps BoomConeOpacityK of its old opacity and a shorter life,
			// so the ring's leading edge is the read, not a veil around the hero
			if (FVapour* Vp = SpawnShape(0, PCm + D * Lead, D, BoomFollow, Lead, BoomConeLenM * 100.0, BoomConeLenM * 145.0, BoomConeRadM * 100.0, BoomConeRadM * 170.0, double(BoomOpacity) * double(BoomConeOpacityK), double(BoomLife) * 0.7, 1.5f, 0))
			{
				if (Vp->Mid) { Vp->Mid->SetScalarParameterValue(TEXT("Gain"), BoomGain); Vp->Mid->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.86f, 0.89f, 0.95f, 1.f)); }
			}
			bVapour = true;
		}
		if (Sphere)
		{
			const int32 NS = FMath::Clamp(BoomRingSegs, 8, 32);
			// critic r6 #4: the MAIN ring leads the hero (0.6 m ahead of his chest, glued for 0.3 s) and expands fast (ease-out) from 0.5 m to
			// BoomRingMaxM around the flight line: from the 3/4 chase lens it reads as an ellipse in perspective around him; its HARD hot leading edge
			// is the read (M_InvShockRing r7). A weaker echo ring follows just behind his chest. Both snap in, hold, and are gone within ~0.4 s.
			SpawnRing(PCm + D * 60.0, D, NS, 0.30, 60.0, 0.0, 50.0, double(BoomRingMaxM) * 100.0, 0.045, BoomRingOpacity, BoomRingLife, 3, 1.0);
			SpawnRing(PCm - D * 40.0, D, NS, 0.24, -40.0, 120.0, 40.0, double(BoomRingMaxM) * 100.0 * 0.65, 0.05, double(BoomRingOpacity) * 0.6, double(BoomRingLife) * 0.85, 3, 0.7);
			// speed lines back along the cone flank, glued for 0.12 s, then left behind (lens side skipped)
			const double Half = FMath::Atan2(double(BoomConeRadM) * 1.3, double(BoomConeLenM) * 1.2);
			for (int32 K = 0; K < 12; ++K)
			{
				const FVector Rad = BdRingDir(D, 2.0 * PI * (K + 0.3) / 12.0);
				if (!CamSide.IsNearlyZero() && FVector::DotProduct(Rad, CamSide) > 0.55) continue;
				const FVector Ax = (-D * FMath::Cos(Half) + Rad * FMath::Sin(Half)).GetSafeNormal();
				const double Len = Rng.FRandRange(220.f, 380.f);
				const FVector Off = D * 60.0 + Rad * 70.0 + Ax * (Len * 0.5);
				if (FVapour* Vp = SpawnShape(3, PCm + Off, Ax, 0.12, 0.0, Len, Len * 1.3, Rng.FRandRange(5.f, 8.f), 4.0, double(StreakOpacity) * 1.3, 0.35, 1.0f, 2))
					Vp->SideCm = Off;
			}
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
	{ // the flash at the body (additive sparks, small; r3: no opaque / lit flash disc)
		// (critic r4 fl04 washed frames: one flash at the body, 4.0 -- the r4 second 7.0 flash and the one on the lens line are gone)
		const FLinearColor Flash(4.f, 4.f, 4.2f);
		Fx.Hit(PosM, D, 1.0, &Flash);
	}
	// owner feedback 2026-10-15 #1 ("big expanding vapour ring / cone + flash + shock ring ... dust / glass shake on nearby facades"): the super
	// launch leaves a shock ring square-on to the launch line where it fired (BoomRingRadM) -- critic r4: a ring of vapour tubes now, not
	// a 24 m pancake (the lens passes through its hole as it follows him), no engulfing shock shell -- glass / dust shaken off facades within
	// BoomShakeRadM and a dust ring on a street below
	if (MVapour && Sphere)
		SpawnRing(PCm, D, FMath::Clamp(BoomRingSegs + BoomRingSegs / 4, 8, 40), 0.0, 0.0, 0.0, 100.0, double(BoomRingRadM) * 100.0, 0.035, double(BoomRingOpacity) * 0.55, BoomRingLife, 3, 0.8);
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
			// critic r4 fl04 / fl15 (white slabs across the frame): a streak the lens would fly past closer than StreakCamClearM is placed
			// again (3 tries, then skipped) -- the lens path is its position along the travel, the streak is fixed in the world
			FVector At = FVector::ZeroVector;
			bool bPlaced = false;
			for (int32 Try = 0; Try < 3 && !bPlaced; ++Try)
			{
				const double R = Rng.FRandRange(250.f, 1100.f);
				At = FxPosCm + Vd * Ahead + BdRingDir(Vd, Rng.FRandRange(0.f, 2.f * PI)) * R;
				if (!bCamOk) { bPlaced = true; break; }
				const FVector Rel = At - CamCm;
				bPlaced = (Rel - Vd * FVector::DotProduct(Rel, Vd)).Size() >= double(StreakCamClearM) * 100.0;
			}
			if (!bPlaced) continue;
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
			// critic r4 fl04 ("a hard-edged white slab running to the bottom-left corner"): the r4 trail was 9-15 m long and 0.6-1.1 m thick,
			// glued behind him -- straight through the 3/4 chase lens 2.8-4 m back. It is now TrailLenM long, starting at his feet, thin
			// (12-20 cm), the contrails 5-9 cm; the near-lens fade covers the rest
			const double Len = FMath::Max(30.0, double(TrailLenM) * 100.0 * (0.8 + 0.4 * FxSuperK));
			const double Peak = double(TrailOpacity) * FxSuperK;
			const double Life = 0.16;
			const double Back = Len * 0.5 + 90.0;
			// the body trail: from the feet back, glued to him
			SpawnShape(3, FxPosCm - Vd * Back, Vd, Life, -Back, Len, Len * 1.1, 12.0, 20.0, Peak, Life, 1.0f, 2);
			FVector Side = FVector::CrossProduct(Vd, FVector::UpVector);
			if (Side.IsNearlyZero()) Side = BdAnyPerp(Vd);
			Side = Side.GetSafeNormal();
			for (const double S : { -1.0, 1.0 })
				if (FVapour* Vp = SpawnShape(3, FxPosCm - Vd * (Back + 10.0) + Side * (45.0 * S), Vd, Life, -(Back + 10.0), Len * 1.1, Len * 1.2, 5.0, 9.0, Peak * 0.8, Life, 1.0f, 2))
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

void AWHBreachDirector::SpawnDebris(const FVector& OriginCm, const FVector& Axis, double SpawnRadiusCm, double SpeedCms, double AxisBias, int32 N, UMaterialInterface* Look, const FLinearColor& Tint, float Brick, int32 Set, float SizeScale)
{
	if (!Cube) return;
	const bool bSteel = Set == 1;   // critic r6 #8: steel bits (glass towers, steel crowns, thin solids): thin bars and plates in steel tints, never the facade look
	FVector Ax = Axis.GetSafeNormal();
	if (Ax.IsNearlyZero()) Ax = FVector::UpVector;
	FVector U, V; BdPlaneBasis(Ax, U, V);
	const double Now = GetWorld()->GetTimeSeconds();
	for (int32 K = 0; K < N; ++K)
	{
		FChunk* Ch = nullptr;
		for (FChunk& X : Chunks) if (!X.bLive) { Ch = &X; break; }   // critic r5: an idle (prewarmed / retired) piece first
		if (!Ch) Ch = NewChunk();
		if (!Ch) { if (Chunks.Num() == 0) return; Ch = &Chunks[NextChunk % Chunks.Num()]; ++NextChunk; } // recycle the oldest
		UStaticMeshComponent* C = Ch->Comp;
		C->SetSimulatePhysics(false);
		// critic r2 (breach: "no single piece or flat shape covers > 5 % of the frame at ~4 m"; r2 pieces were one size band of 9-47 cm cubes):
		// 66 % small 8-25 cm, 26 % medium 20-34 cm, 8 % large 34-50 cm (longest side); blocks, slabs and bars so the pile does not read as dice
		const float Pick = Rng.FRand();
		const double L = (Pick < 0.66f ? Rng.FRandRange(8.f, 25.f) : Pick < 0.92f ? Rng.FRandRange(20.f, 34.f) : Rng.FRandRange(34.f, 50.f)) * double(SizeScale);
		const float Shape = Rng.FRand();
		FVector Dim = Shape < 0.45f ? FVector(L, L * Rng.FRandRange(0.55f, 1.f), L * Rng.FRandRange(0.45f, 0.9f))          // block
			: Shape < 0.8f ? FVector(L, L * Rng.FRandRange(0.5f, 0.95f), L * Rng.FRandRange(0.14f, 0.3f))                            // slab
			: FVector(L, L * Rng.FRandRange(0.2f, 0.4f), L * Rng.FRandRange(0.2f, 0.4f));                                           // bar
		if (bSteel) Dim = Shape < 0.55f ? FVector(L * 1.5, L * 0.14, L * 0.14) : FVector(L, L * Rng.FRandRange(0.4f, 0.8f), L * 0.07);   // a bar or a thin plate
		Dim = FVector(FMath::Max(Dim.X, 3.0), FMath::Max(Dim.Y, 3.0), FMath::Max(Dim.Z, 3.0));   // (critic r6 #8: never thinner than 3 cm: the solver would tunnel through the street)
		const double Ang = Rng.FRand() * 2.0 * PI;
		const FVector Rad = U * FMath::Cos(Ang) + V * FMath::Sin(Ang);
		const FVector Pos = OriginCm + Rad * SpawnRadiusCm * FMath::Sqrt(double(Rng.FRand())) + Ax * Rng.FRandRange(0.f, 20.f);
		C->SetWorldLocationAndRotation(Pos, FRotator(Rng.FRandRange(0.f, 360.f), Rng.FRandRange(0.f, 360.f), Rng.FRandRange(0.f, 360.f)));
		Ch->Scale = Dim / 100.0;
		C->SetWorldScale3D(Ch->Scale);
		// look: part of the pieces wear the material of the facade (or ground) the line trace hit; the rest the M_InvChunk concrete / brick speckle
		// (or, without that asset, the r2 flat tints: darker mixed rubble, suite r1 sheet review)
		if (!bSteel && Look && Rng.FRand() < FacadeChunkFraction) C->SetMaterial(0, Look);
		else if (Ch->Mid)
		{
			C->SetMaterial(0, Ch->Mid);
			const bool bBrick = !bSteel && Rng.FRand() < Brick;
			const float Pick2 = Rng.FRand();
			const FLinearColor Base = bSteel ? (Pick2 < 0.8f ? Tint : BdScorch * 4.f) : bBrick ? BdBrick : Pick2 < 0.6f ? Tint : Pick2 < 0.8f ? BdConcrete : Pick2 < 0.92f ? BdSteel : BdScorch * 4.f;
			const float Vv = Rng.FRandRange(0.35f, 0.75f);
			Ch->Mid->SetVectorParameterValue(TEXT("Color"), FLinearColor(Base.R * Vv, Base.G * Vv, Base.B * Vv, 1.f));
			Ch->Mid->SetScalarParameterValue(TEXT("Rough"), 0.9f);
			Ch->Mid->SetScalarParameterValue(TEXT("Brick"), bBrick ? 1.f : 0.f);
			Ch->Mid->SetScalarParameterValue(TEXT("Seed"), Rng.FRandRange(0.f, 20.f));
			// critic r5 #8 ("untextured grey cubes"): M_InvChunk r6 textures the piece in its own frame; Size = the piece's dimensions (cm)
			Ch->Mid->SetVectorParameterValue(TEXT("Size"), FLinearColor(float(Dim.X), float(Dim.Y), float(Dim.Z), 0.f));
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

// critic r6 #8 (fl17 12.9 s: "a glass tower spawns bricks"): a curtain-wall breach throws PANES -- 18-55 cm flat boxes 1.6 cm thick wearing the glassy
// translucent M_InvGlassShard (mostly clear face-on, bright at grazing angles, a glint flashing as each one tumbles), flung out of the opening, tumbling,
// falling and fading over their last 45 %. Kinematic like the small glints (no physics cost), Panes pool of MaxPanes (oldest recycled).
void AWHBreachDirector::SpawnPanes(const FVector& PosCm, const FVector& DirN, int32 N, double SpeedCms)
{
	if (!Cube) return;
	UMaterialInterface* PaneBase = MGlassShard ? MGlassShard.Get() : (MTrans ? MTrans.Get() : MSolid.Get());
	const FVector Side = BdAnyPerp(DirN), Up = FVector::CrossProduct(DirN, Side);
	for (int32 K = 0; K < N; ++K)
	{
		FShard* Sh = nullptr;
		for (FShard& X : Panes) if (!X.bLive) { Sh = &X; break; }   // an idle (prewarmed / retired) pane first
		if (!Sh && Panes.Num() < MaxPanes)
		{
			FShard New;
			New.Comp = MakeComp(Cube, PaneBase, New.Mid, false);
			New.bPane = true;
			KeepAlive.Add(New.Comp);
			Panes.Add(New);
			Sh = &Panes.Last();
		}
		if (!Sh && Panes.Num() > 0) { Sh = &Panes[NextPane % Panes.Num()]; ++NextPane; }
		if (!Sh || !Sh->Comp) return;
		Sh->bLive = true; Sh->bPane = true; Sh->T = 0; Sh->Life = Rng.FRandRange(1.2f, 2.3f); Sh->Peak = Rng.FRandRange(0.65f, 0.9f);
		Sh->Pos = PosCm + Side * Rng.FRandRange(-170.f, 170.f) + Up * Rng.FRandRange(-140.f, 170.f);
		Sh->Vel = (DirN + Side * Rng.FRandRange(-0.9f, 0.9f) + Up * Rng.FRandRange(-0.3f, 0.9f)).GetSafeNormal() * SpeedCms * Rng.FRandRange(0.25f, 0.9f);
		Sh->Q = FRotator(Rng.FRandRange(0.f, 360.f), Rng.FRandRange(0.f, 360.f), Rng.FRandRange(0.f, 360.f)).Quaternion();
		Sh->Spin = FVector(Rng.FRandRange(-9.f, 9.f), Rng.FRandRange(-9.f, 9.f), Rng.FRandRange(-9.f, 9.f));
		const double W = Rng.FRandRange(18.f, 55.f);
		Sh->Comp->SetWorldScale3D(FVector(W / 100.0, W * Rng.FRandRange(0.45f, 1.0f) / 100.0, 0.016));
		if (Sh->Mid)
		{
			const float Tn = Rng.FRandRange(0.85f, 1.1f);
			Sh->Mid->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.62f * Tn, 0.78f * Tn, 0.86f * Tn, 1.f));
			Sh->Mid->SetScalarParameterValue(TEXT("Opacity"), 0.f);
			Sh->Mid->SetScalarParameterValue(TEXT("Gain"), 1.0f);
			Sh->Mid->SetScalarParameterValue(TEXT("Emissive"), 0.9f);   // (the M_CmbTrans fallback's own parameter)
		}
		Sh->Comp->SetWorldLocationAndRotation(Sh->Pos, Sh->Q);
		Sh->Comp->SetVisibility(true);
	}
}

// ---------------------------------------------------------------------------------------------------------------- round 3 helpers
bool AWHBreachDirector::TraceFacade(const FVector& StartCm, const FVector& EndCm, FFacadeHit& Out, bool bDescribe) const
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
		const bool bFirst = !Out.bHit && !H.bStartPenetrating;
		if (bFirst) { Out.bHit = true; Out.Point = H.ImpactPoint; Out.Normal = H.ImpactNormal.GetSafeNormal(); }
		if (C)
		{
			UMaterialInterface* M = nullptr;
			if (C->IsVisible() && !C->bHiddenInGame)
			{
				int32 Sec = 0;
				M = H.FaceIndex >= 0 ? C->GetMaterialFromCollisionFaceIndex(H.FaceIndex, Sec) : nullptr;
				if (!M) M = C->GetMaterial(int32(H.ElementIndex));
				if (!M) M = C->GetMaterial(0);
			}
			if (bDescribe)
			{
				// critic r6 #8: name the first surface; the first city-facade material along the line marks a building wall and gives its style
				if (bFirst) DescribeSurface(C, M, H.FaceIndex, Out);
				if (!Out.bFacadeSeen && BdIsFacadeMat(M))
				{
					Out.bFacadeSeen = true;
					if (const UStaticMeshComponent* SMC = Cast<UStaticMeshComponent>(C)) Out.Style = BdFacadeStyle(SMC, H.FaceIndex);
				}
			}
			if (!Out.Mat && M && BdDebrisMaterialOk(M)) Out.Mat = M;
			Q.AddIgnoredComponent(C);
		}
		if (Out.bHit && Out.Mat && (!bDescribe || Out.bFacadeSeen)) break;
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
		if (N.Mid) N.Mid->SetScalarParameterValue(TEXT("Open"), 0.f);
		N.Comp->SetVisibility(false);   // critic r5 #3: pooled from BeginPlay, shown only by a placement (one frame after it)
		KeepAlive.Add(N.Comp);
		if (N.Mid) KeepAlive.Add(N.Mid);
		Pool.Add(N);
		return &Pool.Last();
	}
	FDecalItem* It = &Pool[Next % Pool.Num()];
	++Next;
	return It;   // recycle the oldest
}

// critic r5 #8: how far the facade plane through PointCm (outward normal OutN) runs on each in-plane side, by line traces into it every 40 cm
// (a hit counts when its normal is within ~37 deg of OutN and it lies within 35 cm of the plane: a window recess counts, the street behind a
// corner or a perpendicular wall does not). The box is centred up to 30 % of Half away from the nearer edge and then sized so 0.92 of it
// (the decal's visible circle) stays on the facade; never under 110 cm.
double AWHBreachDirector::FitHoleHalf(const FVector& PointCm, const FVector& OutN, double Half, FVector& OutShift, double* OutSpanCm) const
{
	OutShift = FVector::ZeroVector;
	if (OutSpanCm) *OutSpanCm = -1.0;
	UWorld* W = GetWorld();
	if (!W || Half <= 0.0) return Half;
	FVector N = OutN.GetSafeNormal();
	if (N.IsNearlyZero()) return Half;
	FVector U, V; BdPlaneBasis(N, U, V);
	FCollisionQueryParams Q(SCENE_QUERY_STAT(WHBreachHoleFit), /*bTraceComplex*/ true);
	if (APawn* Hero = UGameplayStatics::GetPlayerPawn(this, 0)) Q.AddIgnoredActor(Hero);
	FCollisionObjectQueryParams Obj;
	Obj.AddObjectTypesToQuery(ECC_WorldStatic);
	Obj.AddObjectTypesToQuery(ECC_WorldDynamic);
	auto OnPlane = [&](const FVector& At) -> bool
	{
		FHitResult H;
		if (!W->LineTraceSingleByObjectType(H, At + N * 80.0, At - N * 80.0, Obj, Q) || H.bStartPenetrating) return false;
		return FVector::DotProduct(H.ImpactNormal.GetSafeNormal(), N) > 0.8 && FMath::Abs(FVector::DotProduct(H.ImpactPoint - PointCm, N)) < 35.0;
	};
	const double Reach = Half * 1.3, Step = 40.0;
	auto Extent = [&](const FVector& D) -> double
	{
		double Ok = 0.0;
		for (double S = Step; S <= Reach + 1.0; S += Step) { if (!OnPlane(PointCm + D * S)) break; Ok = S; }
		return Ok;
	};
	const double EUp = Extent(U), EUm = Extent(-U), EVp = Extent(V), EVm = Extent(-V);
	if (OutSpanCm) *OutSpanCm = FMath::Min(EUp + EUm, EVp + EVm);   // critic r6 #8: the narrower in-plane run of the surface (a girder / rail is < 2.2 m)
	const double Need = 0.92 * Half;
	auto Centre = [&](double Ep, double Em) -> double
	{
		if (FMath::Min(Ep, Em) >= Need) return 0.0;
		return FMath::Clamp(0.5 * (Ep - Em), -0.3 * Half, 0.3 * Half);   // + = toward the +axis side
	};
	const double Su = Centre(EUp, EUm), Sv = Centre(EVp, EVm);
	OutShift = U * Su + V * Sv;
	const double Room = FMath::Min(FMath::Min(EUp - Su, EUm + Su), FMath::Min(EVp - Sv, EVm + Sv));
	return FMath::Clamp(Room / 0.92, FMath::Min(170.0, Half), Half);   // critic r6 #8: never a hole narrower than ~1.5 m on a building wall (was 110 cm half -> ~1 m)
}

void AWHBreachDirector::PlaceHole(const FVector& PointCm, const FVector& IntoWall, float Sev, double Half, const FVector& Shift, EBdSurf Kind, bool bOnWall)
{
	FDecalItem* It = AcquireDecal(HoleDecals, NextHole, MaxHoleDecals, MHole);
	if (!It || !It->Comp) return;
	FVector Into = IntoWall.GetSafeNormal();
	if (Into.IsNearlyZero()) Into = FVector::ForwardVector;
	// critic r5 #8 (fl14 5.35-5.40 s: the opening ran past the wall edge, over the background): the box is fitted to the facade plane around the
	// hit (Breach measured it with FitHoleHalf: shifted a little off a near edge, then shrunk to what is left), and it projects 0.5 m either side of
	// the surface (was 0.9 m, which also reached round a corner onto the perpendicular face)
	(void)Sev;
	It->Comp->DecalSize = FVector(50.0, Half, Half);
	const FRotator Rot = FMath::Abs(Into.Z) > 0.9 ? FRotationMatrix::MakeFromX(Into).Rotator() : FRotationMatrix::MakeFromXZ(Into, FVector::UpVector).Rotator();
	It->Comp->SetVisibility(false);
	const FVector Centre = PointCm + Shift;
	It->Comp->SetWorldLocationAndRotation(Centre, Rot);
	It->Comp->SetSortOrder(2);
	It->bPendingShow = true; It->PlacedFrame = GFrameCounter;   // critic r5 #3: shown from the next engine frame (Tick)
	// critic r6 #8: the decal's frame (the box axes: local Y / Z span the facade, local X is the projection = into the wall) goes to the material, so its
	// outline and its recessed interior share one coordinate system with the rim chunks below
	const FQuat Q = Rot.Quaternion();
	const FVector AxU = Q.GetAxisY(), AxV = Q.GetAxisZ(), AxN = -Q.GetAxisX();
	const float Seed = Rng.FRandRange(0.f, 9.f);
	const float GlassK = Kind == EBdSurf::Glass ? 1.f : Kind == EBdSurf::Steel ? 0.6f : 0.f;
	if (It->Mid)
	{
		const float T = Rng.FRandRange(0.8f, 1.15f);
		It->Mid->SetScalarParameterValue(TEXT("Seed"), Seed);
		It->Mid->SetScalarParameterValue(TEXT("Open"), 0.f);
		// concrete rim for masonry, a dark blue-grey steel / glass frame for a curtain wall
		It->Mid->SetVectorParameterValue(TEXT("RimCol"), GlassK > 0.5f ? FLinearColor(0.16f * T, 0.18f * T, 0.21f * T, 1.f) : FLinearColor(0.30f * T, 0.28f * T, 0.25f * T, 1.f));
		It->Mid->SetVectorParameterValue(TEXT("Centre"), FLinearColor(float(Centre.X), float(Centre.Y), float(Centre.Z), 0.f));
		It->Mid->SetVectorParameterValue(TEXT("AxU"), FLinearColor(float(AxU.X), float(AxU.Y), float(AxU.Z), 0.f));
		It->Mid->SetVectorParameterValue(TEXT("AxV"), FLinearColor(float(AxV.X), float(AxV.Y), float(AxV.Z), 0.f));
		It->Mid->SetVectorParameterValue(TEXT("AxN"), FLinearColor(float(AxN.X), float(AxN.Y), float(AxN.Z), 0.f));
		It->Mid->SetScalarParameterValue(TEXT("HalfCm"), float(Half));
		It->Mid->SetScalarParameterValue(TEXT("Glass"), GlassK);
	}
	It->T = 0.0; It->Grow = 0.18; It->bGrowing = true;
	if (bOnWall && Cube && RimPerHole > 0) SpawnHoleRim(Centre, AxU, AxV, AxN, Half, Seed, Kind);
}

// critic r6 #8 (breach holes "with no interior", no rim): RimPerHole static broken-edge pieces seated on the opening's analytic outline (BdHoleRadius is the
// shader's formula at full growth, so they sit on the drawn edge within ~14 cm), standing off the facade plane and lit by the scene. Concrete / brick
// slabs for masonry; for a curtain wall glass teeth (thin tilted panes) and dark steel plates. They pop in with the opening (Delay) like the crater rim
// and stay for Life s. Everything stays inside the fitted box, so it cannot hang past the wall edge FitHoleHalf found.
void AWHBreachDirector::SpawnHoleRim(const FVector& CentreCm, const FVector& U, const FVector& V, const FVector& N, double HalfCm, double Seed, EBdSurf Kind)
{
	if (!Cube) return;
	const bool bGlassWall = Kind != EBdSurf::Masonry;
	const int32 Count = FMath::Clamp(RimPerHole, 0, 24);
	const double Phase = Rng.FRandRange(0.f, 1.f);
	for (int32 K = 0; K < Count; ++K)
	{
		const double A = 2.0 * PI * (K + Phase * 0.6 + Rng.FRand() * 0.35) / Count - PI;
		const double R = BdHoleRadius(A, Seed, 1.0) * HalfCm * Rng.FRandRange(0.97f, 1.10f);
		if (R + 40.0 > 0.92 * HalfCm) continue;   // stays on the facade box
		const FVector Rad = U * FMath::Cos(A) + V * FMath::Sin(A);
		FVector Tg = FVector::CrossProduct(N, Rad);
		if (!Tg.Normalize()) continue;
		const bool bPane = bGlassWall && Rng.FRand() < 0.6f;
		FVector Dim;   // (X = along the wall normal, Y = along the edge, Z = radial), cm
		double Tilt = 0.0;
		if (bPane) { Dim = FVector(1.8, double(Rng.FRandRange(22.f, 55.f)), double(Rng.FRandRange(14.f, 34.f))); Tilt = Rng.FRandRange(-0.9f, 0.9f); }
		else if (bGlassWall) { Dim = FVector(double(Rng.FRandRange(4.f, 7.f)), double(Rng.FRandRange(30.f, 70.f)), double(Rng.FRandRange(8.f, 16.f))); Tilt = Rng.FRandRange(-0.3f, 0.3f); }
		else { Dim = FVector(double(Rng.FRandRange(10.f, 24.f)), double(Rng.FRandRange(24.f, 58.f)), double(Rng.FRandRange(14.f, 34.f))); Tilt = Rng.FRandRange(-0.35f, 0.35f); }
		FRubble* Rb = nullptr;
		if (HoleRim.Num() < MaxHoleRim)
		{
			FRubble NR;
			NR.Comp = MakeComp(Cube, MChunk ? MChunk.Get() : MSolid.Get(), NR.Mid, true);
			KeepAlive.Add(NR.Comp);
			if (MGlassShard) { NR.GlassMid = UMaterialInstanceDynamic::Create(MGlassShard, this); KeepAlive.Add(NR.GlassMid); }
			HoleRim.Add(NR);
			Rb = &HoleRim.Last();
		}
		else if (HoleRim.Num() > 0) { Rb = &HoleRim[NextHoleRim % HoleRim.Num()]; ++NextHoleRim; }
		if (!Rb || !Rb->Comp) continue;
		FQuat Q = FRotationMatrix::MakeFromXY(N, Tg).ToQuat();
		Q = FQuat(Tg, Tilt) * Q;                                        // lean the piece out of the wall plane
		Q = FQuat(N, Rng.FRandRange(-0.45f, 0.45f)) * Q;                // and turn it a little around the wall normal
		Rb->Pos = CentreCm + Rad * R + N * (0.35 * Dim.X + (bPane ? 6.0 : 1.0));
		Rb->Q = Q;
		Rb->Scale = Dim / 100.0;
		Rb->T = 0.0; Rb->Delay = Rng.FRandRange(0.04f, 0.20f); Rb->Life = 25.0; Rb->bLive = true;
		Rb->Comp->SetVisibility(false);
		Rb->Comp->SetWorldLocationAndRotation(Rb->Pos, Rb->Q);
		Rb->Comp->SetWorldScale3D(FVector(0.01));
		if (bPane && Rb->GlassMid)
		{
			Rb->Comp->SetMaterial(0, Rb->GlassMid);
			Rb->GlassMid->SetScalarParameterValue(TEXT("Opacity"), Rng.FRandRange(0.55f, 0.8f));
			Rb->GlassMid->SetScalarParameterValue(TEXT("Gain"), 1.0f);
		}
		else if (Rb->Mid)
		{
			Rb->Comp->SetMaterial(0, Rb->Mid);
			const float Pk = Rng.FRand();
			const bool bBrick = !bGlassWall && Pk > 0.78f;
			const FLinearColor Base = bGlassWall ? BdSteel * 1.4f : bBrick ? BdBrick : Pk < 0.6f ? BdConcrete : BdConcrete * 1.2f;
			const float Vv = Rng.FRandRange(0.55f, 1.0f);
			Rb->Mid->SetVectorParameterValue(TEXT("Color"), FLinearColor(Base.R * Vv, Base.G * Vv, Base.B * Vv, 1.f));
			Rb->Mid->SetScalarParameterValue(TEXT("Rough"), bGlassWall ? 0.55f : 0.92f);
			Rb->Mid->SetScalarParameterValue(TEXT("Brick"), bBrick ? 1.f : 0.f);
			Rb->Mid->SetScalarParameterValue(TEXT("Seed"), Rng.FRandRange(0.f, 20.f));
			Rb->Mid->SetVectorParameterValue(TEXT("Size"), FLinearColor(float(Dim.X), float(Dim.Y), float(Dim.Z), 0.f));
		}
	}
}

void AWHBreachDirector::PlaceCraterDecal(const FVector& PCm, float Sev)
{
	FDecalItem* It = AcquireDecal(CraterDecals, NextCrater, MaxCraterDecals, MDecal);
	if (!It || !It->Comp) return;
	const double R = 220.0 + 260.0 * Sev;
	// a shallow slab: the ground is flat, and the only other things in the volume are boots, wheels and rubble (the hero's meshes have decals off)
	It->Comp->DecalSize = FVector(28.0, R, R);
	It->Comp->SetVisibility(false);
	It->Comp->SetWorldLocationAndRotation(PCm + FVector(0.0, 0.0, 6.0), FRotator(-90.0, Rng.FRandRange(0.f, 360.f), 0.f));
	It->Comp->SetSortOrder(1);
	It->bPendingShow = true; It->PlacedFrame = GFrameCounter;   // critic r5 #3: shown from the next engine frame (Tick)
	if (It->Mid)
	{
		It->Mid->SetScalarParameterValue(TEXT("Seed"), Rng.FRandRange(0.f, 9.f));
		It->Mid->SetScalarParameterValue(TEXT("Open"), 0.f);
	}
	It->T = 0.0; It->Grow = 0.30; It->bGrowing = true;
}

void AWHBreachDirector::SpawnPuff(const FVector& PosCm, const FVector& VelCms, double S0, double S1, double Life, double Peak, double DelayS, const FLinearColor& Col, double FlatZ, double RiseCms)
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
	Pf->Drag = Rng.FRandRange(1.8f, 2.8f);
	Pf->Rise = RiseCms >= 0.0 ? RiseCms : double(Rng.FRandRange(40.f, 110.f));
	Pf->FlatZ = FMath::Clamp(FlatZ, 0.2, 1.0);   // critic r4 landings: low ground dust
	Pf->bLive = true; Pf->bShown = false;
	Pf->Comp->SetVisibility(false);
	if (Pf->Mid)
	{
		Pf->Mid->SetVectorParameterValue(TEXT("Color"), Col);
		Pf->Mid->SetScalarParameterValue(TEXT("Seed"), Rng.FRandRange(0.f, 20.f));
		Pf->Mid->SetScalarParameterValue(TEXT("Opacity"), 0.f);
	}
}

void AWHBreachDirector::BreachDust(const FVector& PointCm, const FVector& OutN, const FVector& FlightDir, float Sev, bool bEntry, EBdSurf Kind)
{
	// critic r2 ("see-through bubble smoke"): fewer, larger, more opaque puffs that linger ~1.5 s. They start on a ring AROUND the opening (so the
	// dark hole stays readable 0.3 s after the impact) and billow outward along the wall; at the exit a share is blown out ahead of the hero.
	FVector U, V; BdPlaneBasis(OutN, U, V);
	// critic r6 #8: a glass tower raises a thinner, cooler grey dust (fewer puffs); steel a dark one; masonry the concrete / brick dust
	const bool bGlassy = Kind == EBdSurf::Glass || Kind == EBdSurf::Steel;
	const int32 N = FMath::Max(6, int32(double(PuffsPerBreach + int32(6 * Sev)) * (bGlassy ? 0.65 : 1.0)));
	const double HoleR = HoleHalfCm * 0.42;
	const FLinearColor Base = Kind == EBdSurf::Glass ? BdGlassDust : Kind == EBdSurf::Steel ? BdDust * 0.7f : (bEntry ? BdDust : BdBrickDust);
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
	// critic r4 (dust hid the hero for 55 / 26 / 15 frames at the fl11 / fl12 / fl17 landings; r3 puffs started 0.8-2.2 m from him, rose
	// 0.8-2.2 m/s and grew to 2.2-4.5 m round balls): a LOW ring thrown OUTWARD -- puffs start 1.8-3.0 m out, 10-35 cm over the street, fly
	// out at 5-13 m/s with little lift (0.2-0.9 m/s, slow rise), squashed to 0.55 of their width; the ones on the lens side of him start
	// smaller and thinner (and the Tick fades any puff on the lens -> hero line down to HeroClearMin)
	const int32 N = 16 + int32(8 * Sev);
	FVector ToCam = FVector::ZeroVector;
	{
		FVector Cv;
		if (ViewPos(Cv)) ToCam = FVector(Cv.X - PCm.X, Cv.Y - PCm.Y, 0.0).GetSafeNormal();
	}
	for (int32 K = 0; K < N; ++K)
	{
		const double A = 2.0 * PI * (K + Rng.FRand() * 0.8) / N;
		const FVector Rad(FMath::Cos(A), FMath::Sin(A), 0.0);
		const double Thin = ToCam.IsNearlyZero() ? 0.0 : BdSmooth01((FVector::DotProduct(Rad, ToCam) - 0.35) / 0.5);   // 1 = straight at the lens
		const double S0 = Rng.FRandRange(60.f, 100.f) * (0.9 + 0.3 * Sev) * (1.0 - 0.45 * Thin);
		SpawnPuff(PCm + Rad * Rng.FRandRange(180.f, 300.f) + FVector(0.0, 0.0, Rng.FRandRange(10.f, 35.f)),
			Rad * Rng.FRandRange(500.f, 1300.f) + FVector(0.0, 0.0, Rng.FRandRange(20.f, 90.f)),
			S0, S0 * Rng.FRandRange(2.6f, 3.4f), Rng.FRandRange(1.1f, 1.6f), Rng.FRandRange(0.5f, 0.66f) * (1.0 - 0.65 * Thin), Rng.FRandRange(0.f, 0.08f),
			BdDust * Rng.FRandRange(0.8f, 1.05f), 0.55, Rng.FRandRange(15.f, 35.f));
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
	UMaterialInterface* Base = (Shape == 3 && MStreak) ? MStreak.Get() : (Shape == 5 && MRing) ? MRing.Get() : MVapour.Get();   // (critic r5 #8: shape 5 = M_InvShockRing)
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
	Vp->RadialU = FVector::RightVector; Vp->SegLenK = 0.5; Vp->ThickK = 0.08; Vp->DriftCms = 0.0;   // (critic r4: shape-4 ring tube fields)
	if (Vp->Mid)
	{
		Vp->Mid->SetVectorParameterValue(TEXT("Color"), Shape == 0 ? FLinearColor(0.92f, 0.95f, 1.0f, 1.f) : FLinearColor(0.9f, 0.93f, 1.0f, 1.f));
		Vp->Mid->SetScalarParameterValue(TEXT("EdgePow"), EdgePow);
		Vp->Mid->SetScalarParameterValue(TEXT("Opacity"), 0.f);
		if (Shape != 3) Vp->Mid->SetScalarParameterValue(TEXT("Gain"), 1.4f);   // (the M_InvVapour default; the boom pieces lower it after the spawn)
		if (Shape == 3)
		{ // M_InvStreak: the axis and half length (cm) the speed line fades along (ignored by M_InvVapour)
			Vp->Mid->SetVectorParameterValue(TEXT("Dir"), FLinearColor(float(Dn.X), float(Dn.Y), float(Dn.Z), 0.f));
			Vp->Mid->SetScalarParameterValue(TEXT("HalfLen"), float(FMath::Max(1.0, Len0 * 0.5)));
		}
	}
	Vp->Comp->SetVisibility(true);
	return Vp;
}

// critic r4 fl04 / fl12 (flat discs): a shock ring made of NSeg short vapour tubes (stretched spheres along the ring tangent) on a circle
// square-on to Dir. A tube is fresnel-bright along its silhouette, so off-axis the ring reads as an ellipse of vapour around the body; the
// middle is empty (a lens passing through the ring plane goes through the hole). Shape 4 in the Tick; pool cap MaxVapours.
void AWHBreachDirector::SpawnRing(const FVector& CentreCm, const FVector& Dir, int32 NSeg, double FollowS, double OffsetCm, double DriftCms, double R0, double R1, double ThickK, double Peak, double Life, int32 Env, double RimScale)
{
	if (!Sphere || !MVapour || NSeg <= 0) return;
	FVector D = Dir.GetSafeNormal();
	if (D.IsNearlyZero()) D = FVector::ForwardVector;
	// critic r5 #8 (fl04 t=1.48 / fl12 t=1.0: "a chain of ~20 separate translucent bead blobs, a bubble necklace"): the ring is ONE annulus
	// (shape 5, M_InvShockRing) -- a continuous band with no gaps. The tube ring below is the fallback when the asset has not been built.
	// critic r6 #4 (fl04 1.517: "a soft filled disc ... luma lifted evenly 131-173, no edge peak"): M_InvShockRing r7 has a HARD, hot leading edge
	// (RimGain on top of Gain, exposure-independent), a short wake behind it and a clear interior; the envelope (Env 3) snaps in and fades fast.
	if (MRing)
	{
		if (FVapour* Vp = SpawnShape(5, CentreCm, D, FollowS, OffsetCm, 0.0, 0.0, R0, R1, Peak, Life, 1.3f, Env))
		{
			Vp->ThickK = ThickK; Vp->DriftCms = DriftCms;
			if (Vp->Mid)
			{
				Vp->Mid->SetScalarParameterValue(TEXT("Gain"), BoomGain);
				Vp->Mid->SetScalarParameterValue(TEXT("RimGain"), float(double(BoomRimGain) * RimScale));
				Vp->Mid->SetScalarParameterValue(TEXT("Soft"), 0.3f);
				Vp->Mid->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.88f, 0.91f, 0.97f, 1.f));
			}
			return;
		}
	}
	// fallback (critic r5 #8): denser, wider-overlapping tubes with one shared opacity / life, so the beads merge into a band
	// (critic r6 #4: the tubes are a soft haze by nature -- their peak stays at the old boom opacity, not the ring's leading-edge peak)
	const double TubePeak = FMath::Min(Peak, double(BoomOpacity)) * 0.7;
	const int32 NS = FMath::Clamp(NSeg * 3 / 2, 12, 48);
	const double Phase = Rng.FRandRange(0.f, 1.f);
	for (int32 K = 0; K < NS; ++K)
	{
		const FVector Rad = BdRingDir(D, 2.0 * PI * (K + Phase) / NS);
		FVapour* Vp = SpawnShape(4, CentreCm, D, FollowS, OffsetCm, 0.0, 0.0, R0, R1, TubePeak, Life, 1.3f, 0);
		if (!Vp) break;   // pool full
		Vp->RadialU = Rad;
		Vp->SegLenK = 2.0 * PI / NS * 2.2;   // each tube spans ~2.2 neighbours' spacing (was 1.35): no pinch between them
		Vp->ThickK = ThickK * 1.35 * 1.5;
		Vp->DriftCms = DriftCms;
		if (Vp->Mid) { Vp->Mid->SetScalarParameterValue(TEXT("Gain"), BoomGain); Vp->Mid->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.86f, 0.89f, 0.95f, 1.f)); }
	}
}

bool AWHBreachDirector::ViewPos(FVector& OutCm) const
{
	if (const APlayerCameraManager* PCM = UGameplayStatics::GetPlayerCameraManager(this, 0))
	{
		OutCm = PCM->GetCameraLocation();
		return true;
	}
	return false;
}

double AWHBreachDirector::CamFade(double DistCm) const
{
	const double C = FMath::Max(10.0, double(CamClearCm));
	return BdSmooth01((DistCm - 0.15 * C) / C);
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
			Rb->Mid->SetVectorParameterValue(TEXT("Size"), FLinearColor(float(Dim.X), float(Dim.Y), float(Dim.Z), 0.f));   // critic r5 #8
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
	bCamOk = ViewPos(CamCm);   // critic r4: lens position for the near-lens / hero-line fades and the streak placement
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
	// critic r4 (landings: the hero hidden 15-55 frames behind dust; whiteouts with sd ~20): a puff on the lens -> hero line keeps only
	// HeroClearMin..1 of its opacity (by how far its centre is from that line, in puff radii), and a puff near the lens fades out (CamFade)
	const UWHFlightWorldSubsystem* FWp = UWHFlightWorldSubsystem::Get(this);
	const bool bHeroLine = bCamOk && FWp && FWp->bHeroValid;
	const FVector HeroChest = bHeroLine ? FWp->HeroPosCm + FVector(0.0, 0.0, 30.0) : FVector::ZeroVector;
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
		double Op = Pf.Peak * BdSmooth01(Age / 0.16) * (1.0 - BdSmooth01((K - 0.40) / 0.60));
		// (a squashed ground puff sits on the street: its centre rides up with its height so it is not half buried)
		const FVector DrawPos = Pf.Pos + FVector(0.0, 0.0, Pf.FlatZ < 0.999 ? 0.3 * Sz * Pf.FlatZ : 0.0);
		if (bHeroLine)
		{
			const double Rp = FMath::Max(10.0, 0.5 * Sz);
			const double DL = BdSegDist(DrawPos, CamCm, HeroChest);
			Op *= FMath::Lerp(FMath::Clamp(double(HeroClearMin), 0.0, 1.0), 1.0, BdSmooth01((DL - 0.3 * Rp) / (0.9 * Rp)));
		}
		if (bCamOk) Op *= CamFade(FVector::Dist(DrawPos, CamCm) - 0.5 * Sz);
		Pf.Comp->SetWorldLocation(DrawPos);
		Pf.Comp->SetWorldScale3D(FVector(Sz / 100.0, Sz / 100.0, Sz * Pf.FlatZ / 100.0));
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
			// (critic r4: a shape-4 ring tube's anchor is its ring centre, which may drift back along the axis at DriftCms)
			if (Vp.T < Vp.Follow && FW && FW->bHeroValid)
				Vp.Anchor = (Vp.Shape == 4 || Vp.Shape == 5) ? FW->HeroPosCm + Vp.Dir * (Vp.OffsetCm - Vp.DriftCms * Vp.T) : FW->HeroPosCm + Vp.Dir * Vp.OffsetCm + Vp.SideCm;
			else Vp.Anchor += Vp.VelCm * Dt;
			const double E = BdEaseOut(K);
			const double Rad = FMath::Lerp(Vp.Rad0, Vp.Rad1, E);
			// critic r4 (washed frames / slabs through the lens): the distance from the lens to this piece's surface (cm) for CamFade
			double LensD = 1e6;
			if (Vp.Shape == 2)
			{ // owner feedback 2026-10-15 #1: a sphere shell (the boom's shock shell, the charge's gathering vapour)
				Vp.Comp->SetWorldLocationAndRotation(Vp.Anchor, FRotationMatrix::MakeFromZ(Vp.Dir).ToQuat());
				Vp.Comp->SetWorldScale3D(FVector(2.0 * Rad / 100.0));
				if (bCamOk) LensD = FMath::Abs(FVector::Dist(CamCm, Vp.Anchor) - Rad);   // a shell: inside or outside, its wall is what nears the lens
			}
			else if (Vp.Shape == 3)
			{ // owner feedback 2026-10-15 #1 / #3: a speed line -- an ellipsoid Len long along Dir, centred on Anchor
				const double Len = FMath::Lerp(Vp.Len0, Vp.Len1, E);
				const FQuat Q = FRotationMatrix::MakeFromZ(Vp.Dir).ToQuat();
				Vp.Comp->SetWorldLocationAndRotation(Vp.Anchor, Q);
				Vp.Comp->SetWorldScale3D(FVector(2.0 * Rad / 100.0, 2.0 * Rad / 100.0, FMath::Max(1.0, Len) / 100.0));
				if (Vp.Mid && FMath::Abs(Vp.Len1 - Vp.Len0) > 1.0) Vp.Mid->SetScalarParameterValue(TEXT("HalfLen"), float(FMath::Max(1.0, Len * 0.5)));
				if (bCamOk) LensD = BdEllipsoidDist(CamCm, Vp.Anchor, Q, FVector(Rad, Rad, FMath::Max(1.0, Len) * 0.5));
			}
			else if (Vp.Shape == 4)
			{ // critic r4 fl04: one tube of a segmented shock ring -- on the circle of radius Rad around the axis, along its tangent
				const FVector Tg = FVector::CrossProduct(Vp.Dir, Vp.RadialU).GetSafeNormal();
				const double SegL = FMath::Max(20.0, Vp.SegLenK * Rad);
				const double Th = FMath::Clamp(Vp.ThickK * Rad, 10.0, 60.0);
				const FVector C = Vp.Anchor + Vp.RadialU * Rad;
				const FQuat Q = FRotationMatrix::MakeFromZX(Tg.IsNearlyZero() ? BdAnyPerp(Vp.Dir) : Tg, Vp.RadialU).ToQuat();
				Vp.Comp->SetWorldLocationAndRotation(C, Q);
				Vp.Comp->SetWorldScale3D(FVector(2.0 * Th / 100.0, 2.0 * Th / 100.0, SegL / 100.0));
				if (bCamOk) LensD = BdEllipsoidDist(CamCm, C, Q, FVector(Th, Th, SegL * 0.5));
			}
			else if (Vp.Shape == 5)
			{ // critic r5 #8: the whole shock ring as one flattened sphere; M_InvShockRing draws only the annulus Band +- BandW of its radius
				const double Th = FMath::Clamp(Vp.ThickK * Rad, 12.0, 70.0);
				const double Ro = Rad + Th;   // the mesh's outer radius
				const FQuat Q = FRotationMatrix::MakeFromZ(Vp.Dir).ToQuat();
				Vp.Comp->SetWorldLocationAndRotation(Vp.Anchor, Q);
				Vp.Comp->SetWorldScale3D(FVector(2.0 * Ro / 100.0, 2.0 * Ro / 100.0, 2.0 * Th / 100.0));
				if (Vp.Mid)
				{
					Vp.Mid->SetScalarParameterValue(TEXT("Band"), float(Rad / Ro));
					Vp.Mid->SetScalarParameterValue(TEXT("BandW"), float(Th / Ro));
				}
				if (bCamOk)
				{ // the lens against the tube: torus distance (ring radius Rad, tube radius Th)
					const FVector L = Q.UnrotateVector(CamCm - Vp.Anchor);
					LensD = FMath::Max(0.0, FMath::Sqrt(FMath::Square(FVector2D(L.X, L.Y).Size() - Rad) + L.Z * L.Z) - Th);
				}
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
				if (bCamOk)
				{ // the lens against the cone's flank: (axial back from the apex, radial) vs the segment apex (0, 0) -> base rim (Len, Rad)
					const FVector Rel = CamCm - Vp.Anchor;
					const double Ax = FVector::DotProduct(Rel, -Vp.Dir);
					const double Rr = (Rel + Vp.Dir * Ax).Size();
					LensD = BdSegDist(FVector(Ax, Rr, 0.0), FVector::ZeroVector, FVector(Len, Rad, 0.0));
				}
			}
			else
			{
				const double Thick = FMath::Max(40.0, Rad * 0.18);
				const FQuat Q = FRotationMatrix::MakeFromZ(Vp.Dir).ToQuat();
				Vp.Comp->SetWorldLocationAndRotation(Vp.Anchor, Q);
				Vp.Comp->SetWorldScale3D(FVector(2.0 * Rad / 100.0, 2.0 * Rad / 100.0, Thick / 100.0));
				if (bCamOk) LensD = BdEllipsoidDist(CamCm, Vp.Anchor, Q, FVector(Rad, Rad, Thick * 0.5));
			}
			if (Vp.Mid)
			{ // envelopes (owner feedback 2026-10-15): 0 the r3 fade-out after 40 %, 1 gather (ramps up to the launch), 2 speed line (quick in, fades over the second half)
				double Op = Vp.Peak * BdSmooth01(Vp.T / 0.05) * (1.0 - BdSmooth01((K - 0.40) / 0.60));
				if (Vp.Env == 1) Op = Vp.Peak * BdSmooth01(K / 0.8) * (1.0 - BdSmooth01((K - 0.92) / 0.08));
				else if (Vp.Env == 2) Op = Vp.Peak * BdSmooth01(Vp.T / 0.04) * (1.0 - BdSmooth01((K - 0.5) / 0.5));
				else if (Vp.Env == 3) Op = Vp.Peak * BdSmooth01(Vp.T / 0.015) * (1.0 - BdSmooth01((K - 0.30) / 0.70));   // critic r6 #4: the shock ring snaps in, holds, then fades
				if (LensD < 1e5) Op *= CamFade(LensD);   // critic r4: nothing white right on the lens
				Vp.Mid->SetScalarParameterValue(TEXT("Opacity"), float(Op));
			}
		}
	}
	// r3 decals: the opening / crater grows open (the material's Open parameter, ease-out) over Grow s
	for (TArray<FDecalItem>* Pool : { &HoleDecals, &CraterDecals })
		for (FDecalItem& Dc : *Pool)
		{
			// critic r5 #3: a placed decal appears one engine frame after its placement, with its parameters (Open 0) already in place
			if (Dc.bPendingShow && GFrameCounter > Dc.PlacedFrame && Dc.Comp) { Dc.Comp->SetVisibility(true); Dc.bPendingShow = false; }
			if (!Dc.bGrowing) continue;
			Dc.T += Dt;
			const double K = FMath::Clamp(Dc.T / FMath::Max(1e-3, Dc.Grow), 0.0, 1.0);
			if (Dc.Mid) Dc.Mid->SetScalarParameterValue(TEXT("Open"), float(K));
			if (K >= 1.0) Dc.bGrowing = false;
		}
	// r3 crater rim rubble: pops in with a small overshoot after its delay, stays, shrinks out over its last 0.6 s
	// (critic r6 #8: the breach openings' rim pieces ride the same pop-in / stay / shrink-out)
	for (TArray<FRubble>* RbPool : { &Rubble, &HoleRim })
		for (FRubble& Rb : *RbPool)
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
	// glass: ballistic, spinning, fading (critic r6 #8: the glass-tower panes too -- they fade in over 50 ms and out over their last 45 %)
	for (TArray<FShard>* ShPool : { &Shards, &Panes })
		for (FShard& S : *ShPool)
		{
			if (!S.bLive) continue;
			S.T += Dt;
			if (S.T >= S.Life) { S.bLive = false; S.Comp->SetVisibility(false); continue; }
			S.Vel += FVector(0, 0, -980.0) * Dt;
			S.Vel *= FMath::Exp(-0.8 * Dt);
			S.Pos += S.Vel * Dt;
			if (S.Spin.SizeSquared() > 0) S.Q = (FQuat(S.Spin.GetSafeNormal(), S.Spin.Size() * Dt) * S.Q).GetNormalized();
			S.Comp->SetWorldLocationAndRotation(S.Pos, S.Q);
			if (S.Mid)
			{
				const double Kp = S.T / S.Life;
				const double Op = S.bPane ? S.Peak * BdSmooth01(S.T / 0.05) * (1.0 - BdSmooth01((Kp - 0.55) / 0.45)) : 0.7 * (1.0 - Kp);
				S.Mid->SetScalarParameterValue(TEXT("Opacity"), float(Op));
			}
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
