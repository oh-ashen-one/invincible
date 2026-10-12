// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// Piece P3: world queries for traversal in METRES (port of the browser's world.raycast / world.groundHeight /
// collide.js BoxIndex + pushOutCapsule), implemented with Unreal line traces and capsule penetration tests.
#pragma once

#include "CoreMinimal.h"
#include "CollisionQueryParams.h"

class UWorld;
class ULevel;
class AActor;
class UPrimitiveComponent;

struct FTravHit
{
	double Distance = 0.0;
	FVector Point = FVector::ZeroVector;   // m
	FVector Normal = FVector::UpVector;
	bool bGround = false;                  // hit the bare ground plane (actor tagged WHGround): never holds a web
	int32 Box = -1;                        // building box index, -1 if not a box
	TWeakObjectPtr<UPrimitiveComponent> Comp;
};

struct FTravContact
{
	FVector Normal = FVector::ForwardVector; // horizontal
	FVector Point = FVector::ZeroVector;
	double Depth = 0.0;
	double Top = 0.0;                         // top of the obstacle stack in front (m)
};

struct FTravBox
{
	FVector Min = FVector::ZeroVector; // m
	FVector Max = FVector::ZeroVector;
};

class WEBHOMAGE_API FWebTravWorld
{
public:
	/** Gathers building boxes (blocking static geometry, not tagged WHGround) and sets up query params. */
	void Init(UWorld* InWorld, const AActor* IgnoreActor);

	/** Ray from O along unit D up to MaxDist (m). */
	bool Raycast(const FVector& O, const FVector& D, double MaxDist, FTravHit& Out) const;
	/** round 01: does the segment A->B (m) pass through a tree crown sphere (the 2.5 m at each end are ignored: the hand stands under trees, the anchor sits behind leaves)? */
	bool SegmentHitsCrown(const FVector& A, const FVector& B) const;
	/** round 01: highest crown top (m) of any tree crown whose centre is within RadiusM horizontally of (X, Y); -1e9 when none */
	double CrownTopAt(double X, double Y, double RadiusM) const;
	/** round 01: moves P (m) out of every crown sphere it lies in (+ MarginM); true when it moved */
	bool PushOutOfCrowns(FVector& P, double MarginM) const;
	/** Sphere sweep from A to B (m); returns true on a blocking hit (OutDist = distance travelled before the hit). */
	bool SphereSweep(const FVector& A, const FVector& B, double Radius, double& OutDist) const;
	/** Does a sphere at P (m) overlap solid geometry (ground included)? */
	bool SphereOverlaps(const FVector& P, double Radius) const;
	/** Highest surface at (X,Y) at or below FromZ (m). -1000 if nothing. */
	double GroundHeight(double X, double Y, double FromZ) const;
	/** Round 10 (lit city): like GroundHeight but passes through props / trees / street-kit meshes (only ground-tagged actors
	 *  and indexed building boxes count), so a swing's designed low point is measured from the street, not a tree canopy. */
	double StreetHeight(double X, double Y, double FromZ) const;
	/** Pushes a vertical capsule (feet, radius R, height H) horizontally out of solids; only the part above StepH collides. */
	bool PushOutCapsule(FVector& Feet, double R, double H, double StepH, FTravContact& Out) const;
	/** Is the point inside a building box (margin m)? */
	bool Inside(const FVector& P, double Margin = 0.05) const;
	/** Box indices whose XY footprint intersects the square around (X,Y) with half-size R. */
	void Near(double X, double Y, double R, TArray<int32>& Out) const;

	/** Incremental indexing (World Partition cells / streamed levels): AddLevel indexes the solids, boxes and ground of one level exactly as Init does for the levels loaded at BeginPlay;
	 *  RemoveLevel removes exactly what that level added (entries are owned per level; box indices stay valid as tombstones so a held index never dangles) and returns the level's
	 *  bounds (m) so the caller can release anchors inside it. */
	void AddLevel(ULevel* L);
	bool RemoveLevel(ULevel* L, FBox& OutBoundsM);
	/** Is the box index a live solid (not a tombstone of a removed level)? */
	bool BoxLive(int32 I) const { return Boxes.IsValidIndex(I) && Boxes[I].Min.X < 1e6; }
	int32 RemovedSerial = 0;

	bool Ok() const { return Boxes.Num() > 0; }
	/** Round 20: is the hit point on / inside a building box (index, margin m)? -1 if none. Used to tag visual-mesh hits with their building. */
	int32 BoxAt(const FVector& P, double Margin = 1.0) const;
	/** Round 20: sphere sweep A -> B (m) against traversal solids only (props / signs / foliage passed through); false when the sweep starts
	 *  inside something. OutDist = distance before the hit, OutN = hit normal. */
	bool SweepSolid(const FVector& A, const FVector& B, double Radius, double& OutDist, FVector& OutN) const;
	/** Round 20: line A -> B (m) blocked by any visible collision (camera visibility; props included)? */
	bool LineBlocked(const FVector& A, const FVector& B) const;
	/** Round 20: is P (m) enclosed by geometry (the camera inside a building)? 4 horizontal rays all hit within 70 m and the up ray hits. */
	bool Enclosed(const FVector& P) const;
	/** Round 20 collision mode: 2 = visual triangles (merged visual meshes are traversal solids, traced complex; WHBox cubes only index
	 *  buildings for the canyon / anchor logic), 1 = round-19 boxes-only, 0 = every collision primitive (690dfa7). */
	int32 SolidMode = 0;
	bool bIsmSolid = false;
	/** Round 20: visible components excluded by name (signs / screens / props / foliage) -- the depth audit renders with and without them. */
	TArray<TWeakObjectPtr<UPrimitiveComponent>> ExcludedComps;
	/** Round 19 (owner playtest 2026-10-01, "landing in mid-air and being able to run is still around"): in a map with the browser's
	 *  per-building boxes (WHBox cubes) only those boxes and the WHGround floor are traversal solids; every other collision primitive
	 *  (props, trees, signage, street kit, landmark meshes with a simple-collision hull, traffic) is passed through by the traversal's
	 *  rays and capsule push-out. */
	bool BoxesOnly() const { return bBoxesOnly; }
	bool Allowed(const UPrimitiveComponent* C) const { return !bBoxesOnly || (C && AllowedComps.Contains(C)); }
	/** Last GroundHeight source (telemetry / landing log): 0 none, 1 ground box, 2 ground mesh hit, 3 building box hit, 4 other hit. */
	mutable int32 LastGroundSrc = 0;
	mutable FString LastGroundComp;
	mutable int32 SkippedHits = 0;

	TArray<FTravBox> Boxes;
	/** Terrain (actors tagged WHGround): always a floor, even when a body has sunk below its top (browser terrain). */
	TArray<FTravBox> GroundBoxes;
	mutable int32 TraceCount = 0;

private:
	struct FLevelOwn
	{
		TArray<int32> BoxIdx, GroundIdx;
		TArray<const UPrimitiveComponent*> Allowed, Excluded, CompBox, Inst;
		TArray<TPair<int64, FVector4>> Crowns;   // round 01: tree-crown spheres (x, y, z, radius in m) with their grid cell, removed with the level
		FBox Bounds = FBox(ForceInit);
	};
	struct FIndexStats { int32 NInstComps = 0, NInstBoxes = 0, NInstSkipped = 0, NFarSkipped = 0, NVisualOnly = 0, NVisSolid = 0, NExcluded = 0, NReEnabled = 0, NCubesOff = 0; };
	void AddLevelInternal(ULevel* L, bool bLog);
	void IndexLevelActors(ULevel* L);
	int32 AddBoxOwned(const FBox& B);
	void AddGroundOwned(const FTravBox& G);
	void AllowOwned(const UPrimitiveComponent* P);
	void ExcludeOwned(UPrimitiveComponent* P);
	void CompToBoxOwned(const UPrimitiveComponent* P, int32 Idx);
	TArray<int32>& InstOwned(const UPrimitiveComponent* P);
	TMap<const ULevel*, FLevelOwn> LevelOwn;
	// round 01 (W7): tree crowns have no collision -- spheres built from the leaf instanced meshes of the streamed tiles (ISM_ez_*leaves), 16 m grid
	TMap<int64, TArray<FVector4>> CrownGrid;
	int64 CrownKey(int32 CX, int32 CY) const { return (int64(CX) << 32) ^ int64(uint32(CY)); }
	void AddCrownOwned(const FVector& CenterM, double RadiusM);
	FLevelOwn* CurOwn = nullptr;
	FIndexStats Stats;
	const AActor* IgnoreActorPtr = nullptr;
	bool bDumpPrims = false;
	FString DumpPath, DumpText;
	int64 Key(int32 CX, int32 CY) const { return (int64(CX) << 32) ^ int64(uint32(CY)); }
	TMap<int64, TArray<int32>> Grid;
	TMap<const UPrimitiveComponent*, int32> CompToBox;
	// instanced meshes (ISM/HISM): one box per instance (index = instance index, -1 = skipped); a component-wide bounds box made
	// giant invisible walls/floors (owner playtest 2026-10-01: landing / running in mid-air)
	TMap<const UPrimitiveComponent*, TArray<int32>> InstToBox;
	double Cell = 24.0;
	bool bBoxesOnly = false;
	TSet<const UPrimitiveComponent*> AllowedComps;
	bool IsExcludedName(const FString& LowerName) const;
	TWeakObjectPtr<UWorld> World;
	FCollisionQueryParams Params;
	FCollisionObjectQueryParams ObjParams;
};
