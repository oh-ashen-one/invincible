// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// Piece P3: port of src/player/traversal/anchors.js (analytic web-swing anchor search on building faces) and
// src/player/traversal/zippoints.js (roof-edge / corner / water-tower perch points + screen-centre zip targeting).
// Metres, UE axes (Z up). Tree canopies (browser near-LOD instances) are not ported: no trees in the test world yet.
#pragma once

#include "CoreMinimal.h"

class FWebTravWorld;

struct FTravAnchor
{
	FVector Point = FVector::ZeroVector;
	FVector Normal = FVector::ForwardVector;
	double L = 0.0;
	double Lat = 0.0;
	FName Kind;   // wall | low
};

struct FTravZipPoint
{
	FVector Pos = FVector::ZeroVector;
	FVector Normal = FVector::ForwardVector;
	FName Kind;   // roofEdge | roofCorner | waterTower | ledge
	int32 Box = -1;
};

/** Camera view used by zip targeting (screen projection). */
struct FTravView
{
	FVector Pos = FVector::ZeroVector;
	FVector Fwd = FVector::ForwardVector;
	FVector Right = FVector::RightVector;
	FVector Up = FVector::UpVector;
	double TanHalfH = 1.0;
	double TanHalfV = 0.55;
};

class WEBHOMAGE_API FWebTravAnchors
{
public:
	explicit FWebTravAnchors(const FWebTravWorld& InWorld) : World(InWorld) {}

	/** pos: body centre; fwd: horizontal travel dir (unit); turn: horizontal steer dir or null. */
	bool Find(const FVector& Pos, const FVector& Fwd, const FVector* Turn, double Speed, double FloorZ, FTravAnchor& Out) const;
	/** round 01 (W7): optional candidate filter (hand -> anchor line free of geometry and tree crowns); a rejected candidate is skipped, the next one is tried */
	TFunction<bool(const FTravAnchor&)> Filter;
	/** Is the anchor still attached to a 3D model? */
	bool Attached(const FVector& Point, const FVector& Normal) const;

	/** Zip / perch points derived from the building boxes. */
	void QueryZipPoints(const FVector& Center, double Radius, TArray<FTravZipPoint>& Out) const;

	/** Zip targeting (reticle): picks the best point near the screen centre. Returns true when a target exists. */
	bool UpdateTargeting(double Dt, const FTravView& View, const FVector& Eye, bool bEnabled, const FVector* Exclude, bool bAir,
		const FVector* PerchOut);
	bool HasTarget() const { return bHasBest; }
	const FTravZipPoint& Best() const { return BestPt; }

private:
	struct FCand { FVector Point; FVector Normal; double L; double Score; double Lat; FName Kind; };
	struct FPass { double Ahead, Up, Radius, MinAbove, MinL, MaxL, MinAhead, MaxLat, ElevLo, ElevHi; };
public:
	/** Round 19: high-band search aims >= 4 m over the body (-WHTravHighFix=0 = the round-18 1.5 m, A/B). */
	static bool bHighFix;
private:

	void FaceCandidates(const FVector& Pos, const FVector& D, const FVector& Fwd, const FVector& Right, const FPass& P, const FVector* Turn, TArray<FCand>& Out) const;
	bool Confirm(const FVector& Pos, const FCand& C, bool bStrict, FTravAnchor& Out) const;
	bool ArcClear(const FVector& Pos, double PivotZ, const FVector& Pivot, double Rope) const;
	bool Probe(const FVector& Point, const FVector& Dir) const;
	bool OnModel(const FVector& Point, const FVector& Normal) const;
	bool ConeRays(const FVector& Pos, const FVector& Fwd, FTravAnchor& Out) const;
	const TArray<FTravZipPoint>& BoxPoints(int32 I) const;

	struct FMeta { double H; bool bOk; };
	const FMeta& PointMeta(const FTravZipPoint& P);
	bool Visible(const FTravZipPoint& P, const FVector& Eye);
	static FString PKey(const FVector& P) { return FString::Printf(TEXT("%.1f,%.1f,%.1f"), P.X, P.Y, P.Z); }

	const FWebTravWorld& World;
	mutable TMap<int32, TArray<FTravZipPoint>> BoxCache;

	// targeting state
	TArray<FTravZipPoint> Pool;
	double PoolT = 99.0, Time = 0.0;
	TMap<FString, FMeta> Meta;
	TMap<FString, TPair<double, bool>> Vis;
	bool bHasBest = false;
	FTravZipPoint BestPt;
	FString BestKey;
};
