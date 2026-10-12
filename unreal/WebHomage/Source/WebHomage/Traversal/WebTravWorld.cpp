// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Traversal/WebTravWorld.h"
#include "WebHomage.h"

#include "Components/PrimitiveComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/OverlapResult.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Pawn.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "PhysicsEngine/BodyInstance.h"
#include "PhysicsEngine/BodySetup.h"

static const FName NAME_WHGround(TEXT("WHGround"));

bool FWebTravWorld::IsExcludedName(const FString& L) const
{
	// round 20: what is visible but is NOT a traversal solid (a floor / wall / web target): signs, screens, billboard frames, neon, props,
	// street furniture, foliage, traffic, crowds, glass / glow overlays. Everything else that renders (facades, roofs, detail, ground,
	// podiums, landmarks, seawalls, bridges) is a solid with its real triangles.
	static const TCHAR* Ex[] = { TEXT("sign"), TEXT("screen"), TEXT("tsframes"), TEXT("tsticker"), TEXT("tsneon"), TEXT("tslights"), TEXT("tsvinyl"),
		TEXT("tshalo"), TEXT("tsbands"), TEXT("tstkts"), TEXT("billboard"), TEXT("neon"), TEXT("glow"), TEXT("streetkit"), TEXT("streetprop"), TEXT("_prop"),
		TEXT("prop_"), TEXT("trees"), TEXT("tree_"), TEXT("_tree"), TEXT("crown"), TEXT("clump"), TEXT("leaf"), TEXT("leaves"), TEXT("foliage"), TEXT("canopy"),
		TEXT("bush"), TEXT("traffic"), TEXT("crowd"), TEXT("vehicle"), TEXT("hydrant"), TEXT("lamp"), TEXT("tslights"), TEXT("decal"), TEXT("halo"),
		TEXT("spill"), TEXT("grime"), TEXT("wear"), TEXT("dust"), TEXT("markings") };
	for (const TCHAR* K : Ex) { if (L.Contains(K)) return true; }
	return false;
}


static bool IsTravCube(const UPrimitiveComponent* P)
{
	const UStaticMeshComponent* C = Cast<UStaticMeshComponent>(P);
	const UStaticMesh* M = C ? C->GetStaticMesh() : nullptr;
	return M && !C->IsVisible() && M->GetName() == TEXT("Cube") && M->GetPathName().StartsWith(TEXT("/Engine/BasicShapes/"));
}

int32 FWebTravWorld::AddBoxOwned(const FBox& B)
{
	FTravBox TB{ B.Min / 100.0, B.Max / 100.0 };
	const FVector S = TB.Max - TB.Min;
	if (S.Z < 1.0 || (S.X < 0.8 && S.Y < 0.8))
	{
		return -1;
	}
	const int32 Idx = Boxes.Add(TB);
	const int32 X0 = FMath::FloorToInt(TB.Min.X / Cell), X1 = FMath::FloorToInt(TB.Max.X / Cell);
	const int32 Y0 = FMath::FloorToInt(TB.Min.Y / Cell), Y1 = FMath::FloorToInt(TB.Max.Y / Cell);
	for (int32 X = X0; X <= X1; ++X)
	{
		for (int32 Y = Y0; Y <= Y1; ++Y)
		{
			Grid.FindOrAdd(Key(X, Y)).Add(Idx);
		}
	}
	if (CurOwn) CurOwn->BoxIdx.Add(Idx);
	return Idx;
}

void FWebTravWorld::AddGroundOwned(const FTravBox& G)
{
	const int32 Idx = GroundBoxes.Add(G);
	if (CurOwn) CurOwn->GroundIdx.Add(Idx);
}

void FWebTravWorld::AllowOwned(const UPrimitiveComponent* P) { AllowedComps.Add(P); if (CurOwn) CurOwn->Allowed.Add(P); }
void FWebTravWorld::ExcludeOwned(UPrimitiveComponent* P) { ExcludedComps.Add(P); if (CurOwn) CurOwn->Excluded.Add(P); }
void FWebTravWorld::CompToBoxOwned(const UPrimitiveComponent* P, int32 Idx) { CompToBox.Add(P, Idx); if (CurOwn) CurOwn->CompBox.Add(P); }
TArray<int32>& FWebTravWorld::InstOwned(const UPrimitiveComponent* P) { if (CurOwn) CurOwn->Inst.Add(P); return InstToBox.FindOrAdd(P); }

void FWebTravWorld::AddLevelInternal(ULevel* L, bool bLog)
{
	if (!L || LevelOwn.Contains(L)) return;
	FLevelOwn& Own = LevelOwn.Add(L);
	CurOwn = &Own;
	const int32 Before = Boxes.Num();
	IndexLevelActors(L);
	CurOwn = nullptr;
	Own.Bounds = FBox(ForceInit);
	for (int32 I : Own.BoxIdx) { Own.Bounds += Boxes[I].Min; Own.Bounds += Boxes[I].Max; }
	for (int32 I : Own.GroundIdx) { Own.Bounds += GroundBoxes[I].Min; Own.Bounds += GroundBoxes[I].Max; }
	if (bLog)
		UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV stream +level %s %d solids (%d boxes, %d ground boxes, %d solid comps)"), *L->GetOuter()->GetName(), Own.BoxIdx.Num() + Own.GroundIdx.Num(), Own.BoxIdx.Num(), Own.GroundIdx.Num(), Own.Allowed.Num());
	(void)Before;
}

void FWebTravWorld::AddCrownOwned(const FVector& C, double R)
{
	const FVector4 Sp(C.X, C.Y, C.Z, R);
	const int32 X0 = FMath::FloorToInt((C.X - R) / 16.0), X1 = FMath::FloorToInt((C.X + R) / 16.0), Y0 = FMath::FloorToInt((C.Y - R) / 16.0), Y1 = FMath::FloorToInt((C.Y + R) / 16.0);
	for (int32 X = X0; X <= X1; ++X)
		for (int32 Y = Y0; Y <= Y1; ++Y)
		{
			const int64 K = CrownKey(X, Y);
			CrownGrid.FindOrAdd(K).Add(Sp);
			if (CurOwn) CurOwn->Crowns.Add(TPair<int64, FVector4>(K, Sp));
		}
}

bool FWebTravWorld::SegmentHitsCrown(const FVector& A, const FVector& B) const
{
	const FVector D = B - A; const double L = D.Size();
	if (L < 6.0 || CrownGrid.Num() == 0) return false;
	const FVector N = D / L;
	const int32 X0 = FMath::FloorToInt(FMath::Min(A.X, B.X) / 16.0) - 0, X1 = FMath::FloorToInt(FMath::Max(A.X, B.X) / 16.0);
	const int32 Y0 = FMath::FloorToInt(FMath::Min(A.Y, B.Y) / 16.0), Y1 = FMath::FloorToInt(FMath::Max(A.Y, B.Y) / 16.0);
	for (int32 X = X0; X <= X1; ++X)
		for (int32 Y = Y0; Y <= Y1; ++Y)
			if (const TArray<FVector4>* Cl = CrownGrid.Find(CrownKey(X, Y)))
				for (const FVector4& Sp : *Cl)
				{
					const FVector C(Sp.X, Sp.Y, Sp.Z);
					const double T = FMath::Clamp(FVector::DotProduct(C - A, N), 0.0, L);
					if (T < 2.5 || T > L - 2.5) continue;
					if (FVector::DistSquared(A + N * T, C) < double(Sp.W) * double(Sp.W)) return true;
				}
	return false;
}

double FWebTravWorld::CrownTopAt(double X, double Y, double R) const
{
	double Top = -1e9;
	if (CrownGrid.Num() == 0) return Top;
	for (int32 CX = FMath::FloorToInt((X - R) / 16.0); CX <= FMath::FloorToInt((X + R) / 16.0); ++CX)
		for (int32 CY = FMath::FloorToInt((Y - R) / 16.0); CY <= FMath::FloorToInt((Y + R) / 16.0); ++CY)
			if (const TArray<FVector4>* Cl = CrownGrid.Find(CrownKey(CX, CY)))
				for (const FVector4& Sp : *Cl)
					if (FMath::Square(Sp.X - X) + FMath::Square(Sp.Y - Y) <= FMath::Square(R + Sp.W)) Top = FMath::Max(Top, double(Sp.Z) + double(Sp.W));
	return Top;
}

bool FWebTravWorld::PushOutOfCrowns(FVector& P, double Margin) const
{
	if (CrownGrid.Num() == 0) return false;
	bool bMoved = false;
	for (int32 Pass = 0; Pass < 2; ++Pass)
	{
		const TArray<FVector4>* Cl = CrownGrid.Find(CrownKey(FMath::FloorToInt(P.X / 16.0), FMath::FloorToInt(P.Y / 16.0)));
		if (!Cl) break;
		bool bAny = false;
		for (const FVector4& Sp : *Cl)
		{
			const FVector C(Sp.X, Sp.Y, Sp.Z); const double R = double(Sp.W) + Margin;
			FVector D = P - C; const double Dd = D.Size();
			if (Dd < R) { D = Dd > 1e-3 ? D / Dd : FVector(0, 0, 1); P = C + D * R; bAny = bMoved = true; }
		}
		if (!bAny) break;
	}
	return bMoved;
}

void FWebTravWorld::AddLevel(ULevel* L) { AddLevelInternal(L, true); }

bool FWebTravWorld::RemoveLevel(ULevel* L, FBox& OutBoundsM)
{
	FLevelOwn* Own = LevelOwn.Find(L);
	if (!Own) return false;
	OutBoundsM = Own->Bounds;
	for (int32 Idx : Own->BoxIdx)
	{
		const FTravBox TB = Boxes[Idx];
		const int32 X0 = FMath::FloorToInt(TB.Min.X / Cell), X1 = FMath::FloorToInt(TB.Max.X / Cell);
		const int32 Y0 = FMath::FloorToInt(TB.Min.Y / Cell), Y1 = FMath::FloorToInt(TB.Max.Y / Cell);
		for (int32 X = X0; X <= X1; ++X)
			for (int32 Y = Y0; Y <= Y1; ++Y)
				if (TArray<int32>* Cl = Grid.Find(Key(X, Y))) { Cl->RemoveSingleSwap(Idx); if (Cl->Num() == 0) Grid.Remove(Key(X, Y)); }
		Boxes[Idx] = FTravBox{ FVector(1e7), FVector(1e7) };   // tombstone: the index stays valid (anchors / hits holding it) but matches nothing
	}
	for (int32 Idx : Own->GroundIdx) GroundBoxes[Idx] = FTravBox{ FVector(1e7), FVector(1e7) };
	for (const TPair<int64, FVector4>& Cr : Own->Crowns) if (TArray<FVector4>* Cl = CrownGrid.Find(Cr.Key)) { Cl->RemoveSingleSwap(Cr.Value); if (Cl->Num() == 0) CrownGrid.Remove(Cr.Key); }
	for (const UPrimitiveComponent* P : Own->Allowed) AllowedComps.Remove(P);
	for (const UPrimitiveComponent* P : Own->CompBox) CompToBox.Remove(P);
	for (const UPrimitiveComponent* P : Own->Inst) InstToBox.Remove(P);
	ExcludedComps.RemoveAll([&](const TWeakObjectPtr<UPrimitiveComponent>& W) { return !W.IsValid() || Own->Excluded.Contains(W.Get()); });
	const int32 N = Own->BoxIdx.Num() + Own->GroundIdx.Num();
	LevelOwn.Remove(L);
	++RemovedSerial;
	UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV stream -level %s %d solids"), L && L->GetOuter() ? *L->GetOuter()->GetName() : TEXT("?"), N);
	return true;
}

void FWebTravWorld::IndexLevelActors(ULevel* L)
{
	const AActor* IgnoreActor = IgnoreActorPtr;
	const AActor* const IgnoreActorPtr_ = IgnoreActor; (void)IgnoreActorPtr_;
	auto& DumpTextRef = DumpText; (void)DumpTextRef;
	for (AActor* A : L->Actors)
	{
		if (!A || A == IgnoreActorPtr || A->IsA<APawn>())
		{
			continue;
		}
#if WITH_EDITOR
		{ // round 01 (W7): tree crowns (leaf instanced meshes of the street / park trees)
			FString Lb = A->GetActorLabel().ToLower(); Lb.ReplaceInline(TEXT("-"), TEXT("_"));
			if (Lb.StartsWith(TEXT("ism_ez_")) && Lb.Contains(TEXT("leaves")))
			{
				TInlineComponentArray<UInstancedStaticMeshComponent*> Is(A);
				for (UInstancedStaticMeshComponent* IC : Is)
				{
					const UStaticMesh* SM = IC ? IC->GetStaticMesh() : nullptr;
					if (!SM) continue;
					const FBoxSphereBounds MB = SM->GetBounds();
					TSet<int64> Seen;
					for (int32 K = 0; K < IC->GetInstanceCount(); ++K)
					{
						FTransform T;
						if (!IC->GetInstanceTransform(K, T, true)) continue;
						const FVector C = T.TransformPosition(MB.Origin) / 100.0;
						const int64 Q = (int64(FMath::RoundToInt(C.X)) << 40) ^ (int64(FMath::RoundToInt(C.Y)) << 16) ^ int64(FMath::RoundToInt(C.Z));
						if (Seen.Contains(Q)) continue;
						Seen.Add(Q);
						AddCrownOwned(C, 0.6 * MB.SphereRadius * T.GetScale3D().GetMax() / 100.0);
					}
				}
			}
		}
#endif
		if (A->ActorHasTag(NAME_WHGround))
		{
			FVector Origin, Extent;
			A->GetActorBounds(false, Origin, Extent);
			// round 19: in the boxes-only city a ground actor is a floor box only when it is a thin slab (a tile whose bounds span a
			// ramp / curb stack / anything taller would put an invisible floor over its whole footprint); its mesh is still hit by rays
			if (!bBoxesOnly || Extent.Z * 2.0 <= 100.0) AddGroundOwned({ (Origin - Extent) / 100.0, (Origin + Extent) / 100.0 });
			TInlineComponentArray<UPrimitiveComponent*> GPs(A);
			for (UPrimitiveComponent* GP : GPs)
			{
				if (!GP) continue;
				AllowOwned(GP);
				if (SolidMode == 2 && GP->IsVisible() && !GP->IsCollisionEnabled() && Cast<UStaticMeshComponent>(GP)) { GP->SetCollisionEnabled(ECollisionEnabled::QueryOnly); ++Stats.NReEnabled; }
				if (bDumpPrims) { const FBox B = GP->Bounds.GetBox(); const UStaticMeshComponent* SC = Cast<UStaticMeshComponent>(GP);
					DumpText += FString::Printf(TEXT("%s,%s,%s,%s,%d,%d,%d,%d,-,%.0f,%.0f,%.0f,%.0f,%.0f,%.0f,ground\n"), *A->GetName(), *GP->GetName(), SC && SC->GetStaticMesh() ? *SC->GetStaticMesh()->GetName() : TEXT("-"),
						*GP->GetClass()->GetName(), GP->IsVisible() ? 1 : 0, -1, int32(GP->GetCollisionEnabled()), int32(GP->GetCollisionObjectType()), B.Min.X / 100, B.Min.Y / 100, B.Min.Z / 100, B.Max.X / 100, B.Max.Y / 100, B.Max.Z / 100); }
			}
			continue;
		}
		TInlineComponentArray<UPrimitiveComponent*> Prims(A);
		for (UPrimitiveComponent* P : Prims)
		{
			if (!P) continue;
			const int32 CollBefore = int32(P->GetCollisionEnabled());
			FString Role = TEXT("-");
			const UStaticMeshComponent* SMC = Cast<UStaticMeshComponent>(P);
			const UStaticMesh* SMesh = SMC ? SMC->GetStaticMesh() : nullptr;
			const FString MeshName = SMesh ? SMesh->GetName() : FString();
			#if WITH_EDITOR
			const FString LName = (A->GetName() + TEXT("/") + A->GetActorLabel() + TEXT("/") + P->GetName() + TEXT("/") + MeshName).ToLower();
#else
			const FString LName = (A->GetName() + TEXT("/") + P->GetName() + TEXT("/") + MeshName).ToLower();
#endif
			const FBox PB = P->Bounds.GetBox();
			if (SolidMode == 2)
			{
				if (IsTravCube(P))
				{ // the browser's per-building box: indexed for the canyon / anchor / zip-point logic, never a collider (invisible)
					const int32 Idx = AddBoxOwned(PB);
					if (Idx >= 0) CompToBoxOwned(P, Idx);
					if (P->IsCollisionEnabled()) { P->SetCollisionEnabled(ECollisionEnabled::NoCollision); ++Stats.NCubesOff; }
					Role = TEXT("box-index");
				}
				else if (!SMC || !SMesh || !P->IsVisible() || A->IsHidden())
				{
					if (P->IsCollisionEnabled() && P->GetCollisionObjectType() == ECC_WorldStatic && !Cast<UInstancedStaticMeshComponent>(P) && SMesh && !P->IsVisible())
					{ // an invisible static mesh is never a floor ("nothing invisible is a floor"): hidden helper planes etc.
						P->SetCollisionEnabled(ECollisionEnabled::NoCollision); ++Stats.NVisualOnly; Role = TEXT("hidden-off");
					}
					else Role = TEXT("other");
				}
				else if (!bIsmSolid && Cast<UInstancedStaticMeshComponent>(P) && !(MeshName == TEXT("SM_shed") || MeshName == TEXT("SM_shedtop") || MeshName == TEXT("SM_subway")))
				{ // instanced street / roof props and trees (benches, carts, posts, hvac, antennas, trunks, hedges): visible, not solids.
				  // Sidewalk sheds and subway entrances are structures and stay solid.
					++Stats.NExcluded; Role = TEXT("excluded-ism"); ExcludeOwned(P);
				}
				else if (MeshName.StartsWith(TEXT("SM_far")) || (FMath::Max(PB.GetSize().X, PB.GetSize().Y) > 40000.0 && PB.Max.Z > 2000.0))
				{ // far skyline (2 km tiles beyond the playable city): scenery only
					P->SetCollisionEnabled(ECollisionEnabled::NoCollision); ++Stats.NFarSkipped; Role = TEXT("far-off"); ExcludeOwned(P);
				}
				else if (IsExcludedName(LName))
				{
					++Stats.NExcluded; Role = TEXT("excluded"); ExcludeOwned(P);
				}
				else
				{ // a visible building / roof / ground / landmark surface: a traversal solid with its own triangles
					if (!P->IsCollisionEnabled()) { P->SetCollisionEnabled(ECollisionEnabled::QueryOnly); ++Stats.NReEnabled; }
					if (P->GetCollisionObjectType() != ECC_WorldStatic && P->GetCollisionObjectType() != ECC_WorldDynamic) P->SetCollisionObjectType(ECC_WorldStatic);
					AllowOwned(P); ++Stats.NVisSolid; Role = TEXT("solid");
				}
				if (bDumpPrims) DumpText += FString::Printf(TEXT("%s,%s,%s,%s,%d,%d,%d,%d,%d,%.0f,%.0f,%.0f,%.0f,%.0f,%.0f,%s\n"), *A->GetName(), *P->GetName(), MeshName.IsEmpty() ? TEXT("-") : *MeshName,
					*P->GetClass()->GetName(), P->IsVisible() ? 1 : 0, CollBefore, int32(P->GetCollisionEnabled()), int32(P->GetCollisionObjectType()),
					SMesh && SMesh->GetBodySetup() ? int32(SMesh->GetBodySetup()->CollisionTraceFlag.GetValue()) : -1,
					PB.Min.X / 100, PB.Min.Y / 100, PB.Min.Z / 100, PB.Max.X / 100, PB.Max.Y / 100, PB.Max.Z / 100, *Role);
				continue;
			}
			if (bBoxesOnly && IsTravCube(P)) AllowOwned(P);
			if (bBoxesOnly && P->IsCollisionEnabled() && !IsTravCube(P))
			{
				const FBox VB = P->Bounds.GetBox();
				if (FMath::Max(VB.GetSize().X, VB.GetSize().Y) > 6000.0)
				{
					P->SetCollisionEnabled(ECollisionEnabled::NoCollision);
					++Stats.NVisualOnly;
				}
				continue;   // only the per-building boxes are traversal boxes
			}
			if (!P->IsCollisionEnabled() || P->GetCollisionObjectType() != ECC_WorldStatic)
			{
				continue;
			}
			{
				// owner playtest 2026-10-01 ("landed in mid-air", "ran up the air"): the far-skyline LOD meshes (SM_farCityMass / SM_farCity /
				// SM_farCityRoofs, one merged mesh per 2 km tile) carried collision, so each became one 2 km x 2 km, 80-290 m tall invisible block.
				// They are scenery only: switch their collision off (also for web traces) and never index anything wider than 400 m above street level.
				const bool bFarMesh = SMesh && SMesh->GetName().StartsWith(TEXT("SM_far"));
				const bool bGiant = FMath::Max(PB.GetSize().X, PB.GetSize().Y) > 40000.0 && PB.Max.Z > 2000.0;
				if (bFarMesh || bGiant)
				{
					P->SetCollisionEnabled(ECollisionEnabled::NoCollision);
					++Stats.NFarSkipped;
					continue;
				}
			}
			if (const UInstancedStaticMeshComponent* ISM = Cast<UInstancedStaticMeshComponent>(P))
			{
				// per-instance boxes; foliage / tree / moving-traffic instances are not perchable building boxes
				const UStaticMesh* SM = ISM->GetStaticMesh();
				const FString IMeshName = SM ? SM->GetName().ToLower() : FString();
				const FString CompName = (A->GetName() + TEXT("/") + ISM->GetName()).ToLower();
				static const TCHAR* Skip[] = { TEXT("tree"), TEXT("crown"), TEXT("clump"), TEXT("leaf"), TEXT("leaves"), TEXT("foliage"), TEXT("canopy"), TEXT("bush"), TEXT("traffic") };
				bool bSkip = !SM;
				for (const TCHAR* K : Skip) { if (IMeshName.Contains(K) || CompName.Contains(K)) { bSkip = true; break; } }
				++Stats.NInstComps;
				TArray<int32>& Map = InstOwned(P);
				const int32 N = ISM->GetInstanceCount();
				Map.Init(-1, N);
				if (bSkip) { Stats.NInstSkipped += N; continue; }
				const FBox MB = SM->GetBoundingBox();
				for (int32 I = 0; I < N; ++I)
				{
					FTransform T;
					if (!ISM->GetInstanceTransform(I, T, /*bWorldSpace*/ true)) continue;
					const int32 Idx = AddBoxOwned(MB.TransformBy(T));
					Map[I] = Idx;
					if (Idx >= 0) ++Stats.NInstBoxes;
				}
				continue;
			}
			const int32 Idx = AddBoxOwned(PB);
			if (Idx >= 0)
			{
				CompToBoxOwned(P, Idx);
			}
		}
	}
}

void FWebTravWorld::Init(UWorld* InWorld, const AActor* IgnoreActor)
{
	World = InWorld;
	// round 20: complex traces -- a mesh's own triangles, not a simple hull (a merged tile's convex hull was a 256 m invisible block)
	Params = FCollisionQueryParams(SCENE_QUERY_STAT(WebTrav), /*bTraceComplex*/ true);
	if (IgnoreActor)
	{
		Params.AddIgnoredActor(IgnoreActor);
	}
	ObjParams = FCollisionObjectQueryParams();
	ObjParams.AddObjectTypesToQuery(ECC_WorldStatic);
	ObjParams.AddObjectTypesToQuery(ECC_WorldDynamic);

	Boxes.Reset();
	GroundBoxes.Reset();
	Grid.Reset();
	CompToBox.Reset();
	InstToBox.Reset();
	AllowedComps.Reset();
	ExcludedComps.Reset();
	bBoxesOnly = false;
	LastGroundSrc = 0; SkippedHits = 0;
	Stats = FIndexStats(); LevelOwn.Reset(); RemovedSerial = 0; IgnoreActorPtr = IgnoreActor; CurOwn = nullptr;
	if (!InWorld)
	{
		return;
	}
	bool bHasBoxes = InWorld->IsPartitionedWorld();   // World Partition (island): the WHBox cubes stream in with their cells, none may be loaded yet
	for (TActorIterator<AActor> It(InWorld); It && !bHasBoxes; ++It)
	{
		TInlineComponentArray<UPrimitiveComponent*> Ps(*It);
		for (UPrimitiveComponent* P : Ps) { if (P && IsTravCube(P) && P->IsCollisionEnabled()) { bHasBoxes = true; break; } }
	}
	// round 20 (critic r19 camera 4 / swing 6, root cause: since 690dfa7 the wide merged visual meshes carried no collision and the r19 boxes-only
	// filter made every building without a WHBox cube pass-through for the hero, the web search and the camera): collision = visual triangles.
	//   -WHTravCollide=visual (default with WHBox boxes) | boxes (round 19) | all (every collision primitive, 690dfa7 floor-audit A/B)
	SolidMode = bHasBoxes ? 2 : 0;
	{ int32 V = 0; bIsmSolid = FParse::Value(FCommandLine::Get(), TEXT("-WHTravIsmSolid="), V) && V != 0; } // round 20 A/B: instanced props / trees solid again
	{
		FString CM;
		if (FParse::Value(FCommandLine::Get(), TEXT("-WHTravCollide="), CM)) SolidMode = CM == TEXT("boxes") ? (bHasBoxes ? 1 : 0) : CM == TEXT("all") ? 0 : (bHasBoxes ? 2 : 0);
		int32 V = 1;
		if (FParse::Value(FCommandLine::Get(), TEXT("-WHTravSolidFilter="), V) && V == 0) SolidMode = 0;
	}
	bBoxesOnly = SolidMode != 0;
	bDumpPrims = FParse::Value(FCommandLine::Get(), TEXT("-WHTravDumpPrims="), DumpPath);
	DumpText = TEXT("actor,comp,mesh,class,visible,coll_before,coll_after,objtype,ctf,minx,miny,minz,maxx,maxy,maxz,role\n");
	for (ULevel* L : InWorld->GetLevels()) { if (L) AddLevelInternal(L, /*bLog*/ false); }
	if (bDumpPrims) { FFileHelper::SaveStringToFile(DumpText, *DumpPath); UE_LOG(LogWebHomage, Display, TEXT("WebTravWorld: primitive dump written: %s"), *DumpPath); }
	UE_LOG(LogWebHomage, Display, TEXT("WebTravWorld: solid mode %d (%s; per-building boxes found %d)"), SolidMode,
		SolidMode == 2 ? TEXT("visual triangles: every visible building / roof / ground mesh, traced complex; WHBox cubes index only") : SolidMode == 1 ? TEXT("round-19 boxes-only") : TEXT("every collision primitive"), bHasBoxes ? 1 : 0);
	UE_LOG(LogWebHomage, Display, TEXT("WebTravWorld: %d building boxes indexed (%d instanced components -> %d instance boxes, %d foliage/traffic instances skipped, %d far-skyline/giant components de-collided; %d visible solids, %d with collision re-enabled (QueryOnly), %d excluded by name, %d hidden de-collided, %d WHBox cubes de-collided, %d traversal solids total, %d ground boxes)"),
		Boxes.Num(), Stats.NInstComps, Stats.NInstBoxes, Stats.NInstSkipped, Stats.NFarSkipped, Stats.NVisSolid, Stats.NReEnabled, Stats.NExcluded, Stats.NVisualOnly, Stats.NCubesOff, AllowedComps.Num(), GroundBoxes.Num());
}

int32 FWebTravWorld::BoxAt(const FVector& P, double M) const
{
	TArray<int32> L;
	Near(P.X, P.Y, M, L);
	int32 Best = -1; double BestTop = -1e9;
	for (int32 I : L)
	{
		const FTravBox& B = Boxes[I];
		if (P.X >= B.Min.X - M && P.X <= B.Max.X + M && P.Y >= B.Min.Y - M && P.Y <= B.Max.Y + M && P.Z >= B.Min.Z - M && P.Z <= B.Max.Z + M && B.Max.Z > BestTop)
		{
			Best = I; BestTop = B.Max.Z;
		}
	}
	return Best;
}

void FWebTravWorld::Near(double X, double Y, double R, TArray<int32>& Out) const
{
	Out.Reset();
	const int32 X0 = FMath::FloorToInt((X - R) / Cell), X1 = FMath::FloorToInt((X + R) / Cell);
	const int32 Y0 = FMath::FloorToInt((Y - R) / Cell), Y1 = FMath::FloorToInt((Y + R) / Cell);
	for (int32 CX = X0; CX <= X1; ++CX)
	{
		for (int32 CY = Y0; CY <= Y1; ++CY)
		{
			if (const TArray<int32>* L = Grid.Find(Key(CX, CY)))
			{
				for (int32 I : *L)
				{
					const FTravBox& B = Boxes[I];
					if (B.Max.X < X - R || B.Min.X > X + R || B.Max.Y < Y - R || B.Min.Y > Y + R)
					{
						continue;
					}
					Out.AddUnique(I);
				}
			}
		}
	}
}

bool FWebTravWorld::Inside(const FVector& P, double M) const
{
	TArray<int32> L;
	Near(P.X, P.Y, 0.01, L);
	for (int32 I : L)
	{
		const FTravBox& B = Boxes[I];
		if (P.X > B.Min.X + M && P.X < B.Max.X - M && P.Y > B.Min.Y + M && P.Y < B.Max.Y - M && P.Z > B.Min.Z + M && P.Z < B.Max.Z - M)
		{
			return true;
		}
	}
	return false;
}

bool FWebTravWorld::Raycast(const FVector& O, const FVector& D, double MaxDist, FTravHit& Out) const
{
	UWorld* W = World.Get();
	if (!W || MaxDist <= 0.0)
	{
		return false;
	}
	++TraceCount;
	FHitResult H;
	const FVector Start = O * 100.0, End = (O + D * MaxDist) * 100.0;
	if (!W->LineTraceSingleByObjectType(H, Start, End, ObjParams, Params) || H.bStartPenetrating)
	{
		return false;
	}
	if (bBoxesOnly && !Allowed(H.GetComponent()))
	{ // round 19: pass through every non-traversal solid (re-trace with the hit components ignored; <= 8 layers)
		FCollisionQueryParams P2 = Params;
		bool bFound = false;
		for (int32 K = 0; K < 8; ++K)
		{
			++SkippedHits;
			if (H.GetComponent()) P2.AddIgnoredComponent(H.GetComponent());
			++TraceCount;
			if (!W->LineTraceSingleByObjectType(H, Start, End, ObjParams, P2) || H.bStartPenetrating) break;
			if (Allowed(H.GetComponent())) { bFound = true; break; }
		}
		if (!bFound) return false;
	}
	Out.Distance = H.Distance / 100.0;
	Out.Point = H.ImpactPoint / 100.0;
	Out.Normal = H.ImpactNormal.GetSafeNormal();
	Out.Comp = H.GetComponent();
	const AActor* A = H.GetActor();
	Out.bGround = A && A->ActorHasTag(NAME_WHGround);
	const int32* Bi = H.GetComponent() ? CompToBox.Find(H.GetComponent()) : nullptr;
	Out.Box = Bi ? *Bi : -1;
	if (!Bi && H.GetComponent())
	{
		if (const TArray<int32>* M = InstToBox.Find(H.GetComponent()))
		{
			Out.Box = M->IsValidIndex(H.Item) ? (*M)[H.Item] : -1;
		}
	}
	if (SolidMode == 2 && Out.Box < 0 && !Out.bGround) Out.Box = BoxAt(Out.Point, 1.0); // round 20: the visual hit's building (index only)
	return true;
}

bool FWebTravWorld::SweepSolid(const FVector& A, const FVector& B, double Radius, double& OutDist, FVector& OutN) const
{
	UWorld* W = World.Get();
	if (!W) return false;
	FCollisionQueryParams P2 = Params;
	const FCollisionShape Sh = FCollisionShape::MakeSphere(float(Radius * 100.0));
	for (int32 K = 0; K < 6; ++K)
	{
		++TraceCount;
		FHitResult H;
		if (!W->SweepSingleByObjectType(H, A * 100.0, B * 100.0, FQuat::Identity, ObjParams, Sh, P2)) return false;
		if (!Allowed(H.GetComponent())) { if (H.GetComponent()) P2.AddIgnoredComponent(H.GetComponent()); continue; }
		if (H.bStartPenetrating) return false;
		OutDist = H.Distance / 100.0; OutN = H.ImpactNormal.GetSafeNormal();
		return true;
	}
	return false;
}

bool FWebTravWorld::LineBlocked(const FVector& A, const FVector& B) const
{
	UWorld* W = World.Get();
	if (!W) return false;
	++TraceCount;
	FHitResult H;
	return W->LineTraceSingleByObjectType(H, A * 100.0, B * 100.0, ObjParams, Params);
}

bool FWebTravWorld::Enclosed(const FVector& P) const
{
	UWorld* W = World.Get();
	if (!W) return false;
	auto Hit = [&](const FVector& D, double L)
	{
		++TraceCount;
		FHitResult H;
		return W->LineTraceSingleByObjectType(H, P * 100.0, (P + D * L) * 100.0, ObjParams, Params);
	};
	if (!Hit(FVector(0, 0, 1), 400.0)) return false;
	for (const FVector& D : { FVector(1, 0, 0), FVector(-1, 0, 0), FVector(0, 1, 0), FVector(0, -1, 0) }) { if (!Hit(D, 70.0)) return false; }
	return true;
}

bool FWebTravWorld::SphereSweep(const FVector& A, const FVector& B, double Radius, double& OutDist) const
{
	UWorld* W = World.Get();
	if (!W) return false;
	++TraceCount;
	FHitResult H;
	if (!W->SweepSingleByObjectType(H, A * 100.0, B * 100.0, FQuat::Identity, ObjParams, FCollisionShape::MakeSphere(float(Radius * 100.0)), Params))
	{
		return false;
	}
	OutDist = H.bStartPenetrating ? 0.0 : H.Distance / 100.0;
	return true;
}

bool FWebTravWorld::SphereOverlaps(const FVector& P, double Radius) const
{
	UWorld* W = World.Get();
	if (!W) return false;
	++TraceCount;
	return W->OverlapAnyTestByObjectType(P * 100.0, FQuat::Identity, ObjParams, FCollisionShape::MakeSphere(float(Radius * 100.0)), Params);
}

double FWebTravWorld::GroundHeight(double X, double Y, double FromZ) const
{
	double Best = -1000.0;
	LastGroundSrc = 0;
	for (const FTravBox& G : GroundBoxes)
	{
		if (X >= G.Min.X && X <= G.Max.X && Y >= G.Min.Y && Y <= G.Max.Y && G.Max.Z > Best) { Best = G.Max.Z; LastGroundSrc = 1; }
	}
	FTravHit H;
	if (Raycast(FVector(X, Y, FromZ), FVector(0, 0, -1), 2000.0, H))
	{
		// round 19 (boxes-only city): the surface the ray actually finds (box roof or ground mesh) is the floor; the ground-tile boxes
		// are only the fallback when the ray finds nothing (a body sunk below the ground top). max() put the 15 cm sidewalk tile top
		// under the whole road.
		if (bBoxesOnly || H.Point.Z >= Best)
		{
			Best = H.Point.Z;
			LastGroundSrc = H.bGround ? 2 : H.Box >= 0 ? 3 : 4;
			if (LastGroundSrc == 4 && H.Comp.IsValid()) LastGroundComp = H.Comp->GetOwner() ? H.Comp->GetOwner()->GetName() + TEXT("/") + H.Comp->GetName() : H.Comp->GetName();
		}
	}
	return Best;
}

double FWebTravWorld::StreetHeight(double X, double Y, double FromZ) const
{
	double Best = -1000.0;
	for (const FTravBox& G : GroundBoxes)
	{
		if (X >= G.Min.X && X <= G.Max.X && Y >= G.Min.Y && Y <= G.Max.Y) Best = FMath::Max(Best, G.Max.Z);
	}
	double Z = FromZ;
	for (int32 K = 0; K < 6; ++K)
	{
		FTravHit H;
		if (!Raycast(FVector(X, Y, Z), FVector(0, 0, -1), 2000.0, H)) break;
		// a building mass counts (a box > 4 m tall); awnings / canopies / fire escapes / ledges (thin boxes), props, trees and
		// street-kit meshes do not: keep looking below them
		const bool bMass = H.Box >= 0 && Boxes.IsValidIndex(H.Box) && Boxes[H.Box].Max.Z - Boxes[H.Box].Min.Z > 4.0;
		if (H.bGround || bMass) { Best = FMath::Max(Best, H.Point.Z); break; }
		Z = H.Point.Z - 0.05;
	}
	return Best;
}

bool FWebTravWorld::PushOutCapsule(FVector& Feet, double R, double H, double StepH, FTravContact& Out) const
{
	UWorld* W = World.Get();
	if (!W)
	{
		return false;
	}
	const double Lo = StepH, Hi = H;
	const double HalfH = FMath::Max((Hi - Lo) * 0.5, R + 0.01);
	const FCollisionShape Shape = FCollisionShape::MakeCapsule(float(R * 100.0), float(HalfH * 100.0));
	bool bAny = false;
	double BestDepth = -1.0;
	TWeakObjectPtr<UPrimitiveComponent> BestComp;
	for (int32 Iter = 0; Iter < 3; ++Iter)
	{
		const FVector Centre = FVector(Feet.X, Feet.Y, Feet.Z + Lo + HalfH) * 100.0;
		TArray<FOverlapResult> Overlaps;
		++TraceCount;
		if (!W->OverlapMultiByObjectType(Overlaps, Centre, FQuat::Identity, ObjParams, Shape, Params))
		{
			break;
		}
		bool bMoved = false;
		for (const FOverlapResult& O : Overlaps)
		{
			UPrimitiveComponent* C = O.GetComponent();
			if (!C || !Allowed(C))
			{
				continue;
			}
			FMTDResult MTD;
			const FVector CNow = FVector(Feet.X, Feet.Y, Feet.Z + Lo + HalfH) * 100.0;
			// round 20: penetration against the mesh's own triangles (complex), per instance for instanced meshes
			const FBodyInstance* BI = C->GetBodyInstance(NAME_None, true, O.ItemIndex);
			if (!BI || !BI->OverlapTest(CNow, FQuat::Identity, Shape, &MTD, /*bTraceComplex*/ true) || MTD.Distance <= KINDA_SMALL_NUMBER)
			{
				continue;
			}
			FVector N(MTD.Direction.X, MTD.Direction.Y, 0.0);
			const double HL = N.Size();
			if (HL < 0.3)
			{
				continue; // vertical push-out: floor / ceiling, handled by ground snapping
			}
			N /= HL;
			const double Depth = FMath::Min(double(MTD.Distance) / 100.0 / HL, 1.0);
			if (FMath::Abs(N.X) > 0.999) { N = FVector(FMath::Sign(N.X), 0, 0); }
			else if (FMath::Abs(N.Y) > 0.999) { N = FVector(0, FMath::Sign(N.Y), 0); }
			Feet.X += N.X * (Depth + 1e-4);
			Feet.Y += N.Y * (Depth + 1e-4);
			bMoved = true;
			if (Depth > BestDepth)
			{
				BestDepth = Depth;
				bAny = true;
				Out.Normal = N;
				Out.Point = FVector(Feet.X - N.X * R, Feet.Y - N.Y * R, Feet.Z + H * 0.5);
				Out.Depth = Depth;
				BestComp = C;
			}
		}
		if (!bMoved)
		{
			break;
		}
	}
	if (bAny)
	{
		// top of the obstacle stack in front of the contact (wall + parapet + coping): highest surface right behind the
		// contact point. A trace from high above finds the roof; the obstacle bounds are the fallback.
		const FVector P = Out.Point - Out.Normal * 0.05;
		FTravHit TH;
		double Top = BestComp.IsValid() ? BestComp->Bounds.GetBox().Max.Z / 100.0 : Feet.Z + H;
		const double From = Feet.Z + 400.0;
		if (Raycast(FVector(P.X, P.Y, From), FVector(0, 0, -1), 400.0 + 1.0, TH) && TH.Point.Z > Feet.Z + StepH)
		{
			Top = TH.Point.Z;
		}
		Out.Top = Top;
	}
	return bAny;
}
