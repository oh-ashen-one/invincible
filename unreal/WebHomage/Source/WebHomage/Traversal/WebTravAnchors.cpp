// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Traversal/WebTravAnchors.h"
#include "Traversal/WebTravWorld.h"

namespace
{
	const FVector DOWN(0, 0, -1);
	FName N_wall(TEXT("wall")), N_low(TEXT("low")), N_roofEdge(TEXT("roofEdge")), N_roofCorner(TEXT("roofCorner")),
		N_waterTower(TEXT("waterTower")), N_ledge(TEXT("ledge"));
}

// ---------------------------------------------------------------- anchors
void FWebTravAnchors::FaceCandidates(const FVector& Pos, const FVector& D, const FVector& Fwd, const FVector& Right, const FPass& P,
	const FVector* Turn, TArray<FCand>& Out) const
{
	Out.Reset();
	TArray<int32> Near;
	World.Near(Pos.X, Pos.Y, P.Radius, Near);
	for (int32 I : Near)
	{
		const FTravBox& B = World.Boxes[I];
		const double Top = B.Max.Z;
		if (Top < Pos.Z + P.MinAbove) continue;
		if (B.Max.X - B.Min.X < 2.5 && B.Max.Y - B.Min.Y < 2.5) continue;
		const double ZLo = FMath::Max(B.Min.Z + 0.8, Pos.Z + P.MinAbove), ZHi = Top - 0.45;
		if (ZHi < ZLo) continue;
		const double AZ = FMath::Clamp(D.Z, ZLo, ZHi);
		// 4 vertical faces: axis (0 = X, 1 = Y), plane value, normal sign
		for (int32 F = 0; F < 4; ++F)
		{
			const int32 Ax = F < 2 ? 0 : 1;
			const double Sgn = (F % 2 == 0) ? -1.0 : 1.0;
			const double Plane = Sgn < 0 ? B.Min[Ax] : B.Max[Ax];
			const double PC = Pos[Ax];
			if ((PC - Plane) * Sgn < 4.0) continue; // must be well in front of the face (never a scrape swing along the wall he is on)
			const int32 Tax = Ax == 0 ? 1 : 0;
			const double T0 = B.Min[Tax] + 0.35, T1 = B.Max[Tax] - 0.35;
			if (T1 < T0) continue;
			const double TV = FMath::Clamp(D[Tax], T0, T1);
			FVector A;
			A[Ax] = Plane; A[Tax] = TV; A.Z = AZ;
			const FVector Rel = A - Pos;
			const double L = Rel.Size();
			if (L < P.MinL || L > P.MaxL) continue;
			const double Ahead = Rel.X * Fwd.X + Rel.Y * Fwd.Y;
			if (Ahead < P.MinAhead) continue;
			const double Lat = Rel.X * Right.X + Rel.Y * Right.Y, HL = FMath::Sqrt(Rel.X * Rel.X + Rel.Y * Rel.Y);
			const double Elev = FMath::Atan2(Rel.Z, HL);
			double Score = FVector::Dist(A, D) / 10.0 + FMath::Max(0.0, A.Z - D.Z) * 0.08;
			Score += FMath::Max(0.0, FMath::Abs(Lat) - P.MaxLat) * 0.25;
			Score += FMath::Max(0.0, P.ElevLo - Elev) * 4.0 + FMath::Max(0.0, Elev - P.ElevHi) * 3.0;
			Score -= FMath::Min(Ahead, 40.0) * 0.02;
			if (Turn)
			{ // corner swing: faces lining the new street, never walls blocking it
				const double Nd = Sgn * (*Turn)[Ax];
				if (Nd < -0.5) Score += 4.0; else if (FMath::Abs(Nd) < 0.5) Score -= 0.5;
			}
			FVector N = FVector::ZeroVector;
			N[Ax] = Sgn;
			Out.Add({ A, N, L, Score, Lat, N_wall });
		}
	}
	Out.Sort([](const FCand& A, const FCand& B) { return A.Score < B.Score; });
}

bool FWebTravAnchors::Confirm(const FVector& Pos, const FCand& C, bool bStrict, FTravAnchor& Out) const
{
	FVector D = C.Point - Pos;
	const double Len = D.Size();
	D /= Len;
	FTravHit H;
	if (!World.Raycast(Pos, D, Len + 1.5, H)) return false;
	if (FVector::Dist(H.Point, C.Point) > 1.2)
	{
		if (bStrict) return false;
		// the ray hit something else first: accept it if it's a solid wall that is itself a good anchor
		if (FMath::Abs(H.Normal.Z) > 0.5 || H.Distance < Len * 0.6 || H.Point.Z < Pos.Z + 4.0) return false;
		Out = { H.Point, H.Normal, H.Distance, C.Lat, N_wall };
		return true;
	}
	Out = { H.Point, H.Normal, H.Distance, C.Lat, C.Kind };
	return true;
}

bool FWebTravAnchors::ArcClear(const FVector& Pos, double PivotZ, const FVector& Pivot, double Rope) const
{
	const FVector Bottom(Pivot.X, Pivot.Y, PivotZ - Rope);
	FVector D = Bottom - Pos;
	const double Len = D.Size();
	if (Len < 1.0) return true;
	FTravHit H;
	return !World.Raycast(Pos, D / Len, Len, H) || H.Normal.Z > 0.7;
}

bool FWebTravAnchors::Probe(const FVector& Point, const FVector& Dir) const
{
	const FVector O = Point - Dir * 0.6;
	FTravHit H;
	if (!World.Raycast(O, Dir, 1.4, H) || H.bGround) return false;
	return FVector::Dist(H.Point, Point) < 0.4;
}

bool FWebTravAnchors::OnModel(const FVector& Point, const FVector& Normal) const
{
	if (Normal.SizeSquared() > 0.5 && !(Normal.Z > 0.7) && Probe(Point, -Normal.GetSafeNormal())) return true;
	return Probe(Point, DOWN); // tops (roofs, water towers) and roof-edge points: straight down
}

bool FWebTravAnchors::Attached(const FVector& Point, const FVector& Normal) const
{
	return OnModel(Point, Normal);
}

bool FWebTravAnchors::ConeRays(const FVector& Pos, const FVector& Fwd, FTravAnchor& Out) const
{
	bool bFound = false;
	double BestScore = TNumericLimits<double>::Max();
	for (double E : { 0.95, 1.15, 0.75, 1.3 })
	{
		for (double Y : { 0.0, 0.35, -0.35, 0.7, -0.7, 1.05, -1.05 })
		{
			const double CY = FMath::Cos(Y), SY = FMath::Sin(Y);
			const double FX = Fwd.X * CY - Fwd.Y * SY, FY = Fwd.X * SY + Fwd.Y * CY;
			const FVector Dir = FVector(FX * FMath::Cos(E), FY * FMath::Cos(E), FMath::Sin(E)).GetSafeNormal();
			FTravHit H;
			if (!World.Raycast(Pos, Dir, 90.0, H) || H.bGround || H.Point.Z < Pos.Z + 5.0 || H.Distance < 9.0 || H.Normal.Z > 0.7) continue;
			const double Score = FMath::Abs(E - 0.95) * 2.0 + FMath::Abs(Y) * 1.2 + FMath::Abs(H.Distance - 30.0) / 20.0;
			if (Score < BestScore)
			{
				BestScore = Score;
				Out = { H.Point, H.Normal, H.Distance, 0.0, N_wall };
				bFound = true;
			}
		}
	}
	return bFound;
}

bool FWebTravAnchors::bHighFix = true;

bool FWebTravAnchors::Find(const FVector& Pos, const FVector& Fwd, const FVector* Turn, double Speed, double FloorZ, FTravAnchor& Out) const
{
	const FVector Want = Turn ? (Fwd * 0.55 + *Turn * 0.9).GetSafeNormal() : Fwd;
	const FVector Right(-Want.Y, Want.X, 0.0); // right-hand side of travel
	auto Verify = [this](FTravAnchor& A) { return OnModel(A.Point, A.Normal); };
	if (!World.Ok())
	{
		return ConeRays(Pos, Want, Out) && Verify(Out);
	}
	const double HAbove = Pos.Z - FloorZ;
	// Altitude band (Insomniac keeps chains in the street canyon): the desired anchor sits ~30-42 m over the STREET.
	const double StreetZ = FMath::Min(FloorZ, World.GroundHeight(Pos.X, Pos.Y, 0.6));
	const double Band = StreetZ + FMath::Clamp(30.0 + Speed * 0.25, 30.0, 40.0);
	const bool bHigh = Pos.Z > Band - 4.0;
	FPass Passes[2] = {
		{ FMath::Clamp(12.0 + Speed * 0.75, 18.0, 40.0) * FMath::Clamp(HAbove / 20.0, 0.55, 1.0),
		  FMath::Clamp(15.0 + Speed * 0.25, 15.0, 26.0) * FMath::Clamp(1.25 - (HAbove - 18.0) / 40.0, 0.4, 1.0),
		  70, 5, 9, 72, 2, 22, 0.5, 1.3 },
		{ FMath::Clamp(16.0 + Speed * 0.7, 22.0, 46.0), 26, 95, 4, 8, 95, 4, 40, 0.3, 1.4 },
	};
	// round 19 (owner playtest: "eventually your right-click swing breaks" -- it broke once he was high, e.g. after a wall run up a tower):
	// above the band the search aimed 1.5-2.5 m over the body, and TryStartSwing refuses any web under AnchorMinAbove (3 m) -> every
	// candidate rejected, a dead button over the roofs. High now aims >= 4 m (+4 m target) above the body.
	if (bHigh)
	{
		for (FPass& P : Passes) { P.MinAbove = bHighFix ? 4.0 : 1.5; P.ElevLo = 0.12; }
	}
	TArray<FCand> List;
	for (const FPass& P : Passes)
	{
		const FVector D(Pos.X + Want.X * P.Ahead, Pos.Y + Want.Y * P.Ahead, FMath::Max(Pos.Z + P.MinAbove + (bHigh && bHighFix ? 4.0 : 1.0), FMath::Min(Pos.Z + P.Up, Band)));
		FaceCandidates(Pos, D, Want, Right, P, Turn, List);
		int32 Tries = 0;
		for (const FCand& C : List)
		{
			if (++Tries > 7) break;
			FTravAnchor A;
			if (!Confirm(Pos, C, Turn != nullptr, A) || !Verify(A)) continue;
			if (Filter && !Filter(A)) continue;
			const double PivotZ = A.Point.Z, Rope = FMath::Max(5.0, FMath::Min(A.L, PivotZ - FloorZ - 3.2));
			if (!ArcClear(Pos, PivotZ, A.Point, Rope) && Tries < 6) continue;
			Out = A;
			return true;
		}
	}
	// low swings off street furniture / water towers (parks, waterfront, wide avenues)
	TArray<FTravZipPoint> Pts;
	QueryZipPoints(Pos, 40.0, Pts);
	const FTravZipPoint* Best = nullptr;
	double BS = TNumericLimits<double>::Max();
	for (const FTravZipPoint& P : Pts)
	{
		const FVector Rel = P.Pos - Pos;
		if (Rel.Z < (bHighFix ? 3.0 : 1.0) || P.Pos.Z - FloorZ < 6.0) continue; // round 19: >= TryStartSwing's 3 m
		const double Ahead = Rel.X * Want.X + Rel.Y * Want.Y;
		if (Ahead < 1.0) continue;
		const double L = Rel.Size();
		if (L < 5.0 || L > 40.0) continue;
		const double S = FMath::Abs(Ahead - 12.0) / 8.0 + FMath::Abs(Rel.X * Right.X + Rel.Y * Right.Y) / 10.0 - FMath::Min(Rel.Z, 20.0) / 20.0;
		if (S < BS)
		{
			FTravHit H;
			if (World.Raycast(Pos, Rel / L, L - 0.5, H)) continue;
			if (!OnModel(P.Pos + FVector(0, 0, 0.1), P.Normal)) continue;
			BS = S;
			Best = &P;
		}
	}
	if (Best)
	{
		Out = { Best->Pos + FVector(0, 0, 0.1), Best->Normal, FVector::Dist(Best->Pos, Pos), 0.0, N_low };
		if (Verify(Out) && (!Filter || Filter(Out))) return true;
	}
	if (HAbove > 3.0)
	{
		return ConeRays(Pos, Want, Out) && Verify(Out) && (!Filter || Filter(Out));
	}
	return false;
}

// ---------------------------------------------------------------- zip points
const TArray<FTravZipPoint>& FWebTravAnchors::BoxPoints(int32 I) const
{
	if (const TArray<FTravZipPoint>* C = BoxCache.Find(I))
	{
		return *C;
	}
	TArray<FTravZipPoint>& Pts = BoxCache.Add(I);
	const FTravBox& B = World.Boxes[I];
	const double Top = B.Max.Z;
	if (Top < 3.0) return Pts;
	const double W = B.Max.X - B.Min.X, D = B.Max.Y - B.Min.Y;
	const bool bOnRoof = B.Min.Z > 3.0, bSmall = W < 8.0 && D < 8.0;
	const FName KindEdge = bOnRoof && bSmall ? (Top - B.Min.Z > 2.5 ? N_waterTower : N_ledge) : N_roofEdge;
	const FName KindCorner = bOnRoof && bSmall ? KindEdge : N_roofCorner;
	const double Ins = 0.3;
	auto Add = [&](double X, double Y, double NX, double NY, FName Kind)
	{
		if (World.GroundHeight(X, Y, 1500.0) > Top + 0.35) return;          // uncovered
		const double OX = X + NX * 1.6, OY = Y + NY * 1.6;
		if (World.GroundHeight(OX, OY, 1500.0) > Top - 1.8) return;         // real drop outward
		Pts.Add({ FVector(X, Y, Top), FVector(NX, NY, 0).GetSafeNormal(), Kind, I });
	};
	const double S2 = UE_INV_SQRT_2;
	Add(B.Min.X + Ins, B.Min.Y + Ins, -S2, -S2, KindCorner);
	Add(B.Max.X - Ins, B.Min.Y + Ins, S2, -S2, KindCorner);
	Add(B.Min.X + Ins, B.Max.Y - Ins, -S2, S2, KindCorner);
	Add(B.Max.X - Ins, B.Max.Y - Ins, S2, S2, KindCorner);
	auto Edge = [](double Len, TFunctionRef<void(double)> CB)
	{
		if (Len < 5.0) return;
		const int32 N = FMath::Max(1, FMath::RoundToInt(Len / 9.0));
		for (int32 K = 0; K < N; ++K) CB((K + 0.5) / N);
	};
	Edge(W, [&](double T) { const double X = B.Min.X + W * T; Add(X, B.Min.Y + Ins, 0, -1, KindEdge); Add(X, B.Max.Y - Ins, 0, 1, KindEdge); });
	Edge(D, [&](double T) { const double Y = B.Min.Y + D * T; Add(B.Min.X + Ins, Y, -1, 0, KindEdge); Add(B.Max.X - Ins, Y, 1, 0, KindEdge); });
	return Pts;
}

void FWebTravAnchors::QueryZipPoints(const FVector& Center, double Radius, TArray<FTravZipPoint>& Out) const
{
	Out.Reset();
	if (!World.Ok()) return;
	TArray<int32> Near;
	World.Near(Center.X, Center.Y, Radius, Near);
	for (int32 I : Near)
	{
		for (const FTravZipPoint& P : BoxPoints(I))
		{
			if (FVector::DistSquared(P.Pos, Center) < Radius * Radius) Out.Add(P);
		}
	}
}

// ---------------------------------------------------------------- targeting
const FWebTravAnchors::FMeta& FWebTravAnchors::PointMeta(const FTravZipPoint& P)
{
	const FString K = PKey(P.Pos);
	if (const FMeta* M = Meta.Find(K)) return *M;
	const double Below = World.GroundHeight(P.Pos.X + P.Normal.X * 0.02, P.Pos.Y + P.Normal.Y * 0.02, P.Pos.Z - 0.6);
	const double H = P.Pos.Z - FMath::Min(Below, World.GroundHeight(P.Pos.X + P.Normal.X * 1.2, P.Pos.Y + P.Normal.Y * 1.2, P.Pos.Z - 0.6));
	FTravHit Hit;
	const bool bHit = World.Raycast(FVector(P.Pos.X, P.Pos.Y, P.Pos.Z + 0.6), DOWN, 1.6, Hit);
	const double GH = World.GroundHeight(P.Pos.X, P.Pos.Y, P.Pos.Z + 0.3);
	const bool bSolid = bHit || FMath::Abs(GH - P.Pos.Z) < 0.3;
	const double MinH = P.Kind == N_ledge ? 8.0 : (P.Kind == N_roofEdge || P.Kind == N_roofCorner || P.Kind == N_waterTower) ? 6.0 : 4.5;
	if (Meta.Num() > 4000) Meta.Reset();
	return Meta.Add(K, { H, bSolid && H >= MinH });
}

bool FWebTravAnchors::Visible(const FTravZipPoint& P, const FVector& Eye)
{
	const FString K = PKey(P.Pos);
	if (const TPair<double, bool>* C = Vis.Find(K))
	{
		if (Time - C->Key < 0.25) return C->Value;
	}
	FVector Tgt = P.Pos + P.Normal * 0.35;
	Tgt.Z += 0.35;
	FVector Dir = Tgt - Eye;
	const double Len = Dir.Size();
	Dir /= Len;
	FTravHit H;
	const bool bOk = !World.Raycast(Eye, Dir, Len, H) || H.Distance > Len - 0.7;
	if (Vis.Num() > 600) Vis.Reset();
	Vis.Add(K, TPair<double, bool>(Time, bOk));
	return bOk;
}

bool FWebTravAnchors::UpdateTargeting(double Dt, const FTravView& View, const FVector& Eye, bool bEnabled, const FVector* Exclude, bool bAir,
	const FVector* PerchOut)
{
	static const double RANGE = 58.0;
	Time += Dt; PoolT += Dt;
	if (!bEnabled) { bHasBest = false; BestKey.Reset(); return false; }
	if (PoolT > 0.15) { PoolT = 0.0; QueryZipPoints(Eye, RANGE, Pool); }
	auto KindBonus = [](FName K) -> double
	{
		if (K == N_roofEdge) return -0.45;
		if (K == N_roofCorner) return -0.5;
		if (K == N_waterTower) return -0.35;
		if (K == N_ledge) return 0.15;
		return 0.0;
	};
	struct FScored { const FTravZipPoint* P; double Dist, Ang, Score; };
	TArray<FScored> Scored;
	for (const FTravZipPoint& P : Pool)
	{
		const double Dist = FVector::Dist(P.Pos, Eye);
		if (Dist < 3.0 || Dist > RANGE) continue;
		if (Exclude && FVector::DistSquared(P.Pos, *Exclude) < 4.0) continue;
		const FVector Rel = P.Pos - View.Pos;
		const double Z = FVector::DotProduct(Rel, View.Fwd);
		if (Z <= 0.1) continue;
		const double SX = FVector::DotProduct(Rel, View.Right) / Z / View.TanHalfH, SY = FVector::DotProduct(Rel, View.Up) / Z / View.TanHalfV;
		if (FMath::Abs(SX) > 0.92 || FMath::Abs(SY) > 0.9) continue;
		const double Ang = FMath::Acos(FMath::Clamp(FVector::DotProduct(Rel.GetSafeNormal(), View.Fwd), -1.0, 1.0));
		const FMeta& M = PointMeta(P);
		if (!M.bOk) continue;
		double Score = Ang / 0.3 + Dist / RANGE * 0.9 + KindBonus(P.Kind) - FMath::Min(M.H, 40.0) / 40.0 * 0.35;
		if (bAir) Score += FMath::Max(0.0, Eye.Z - P.Pos.Z - 3.0) * 0.07;
		if (P.Pos.Z < Eye.Z - 12.0) Score += 0.5;
		if (P.Pos.Z > Eye.Z + 30.0) Score += 0.35;
		Scored.Add({ &P, Dist, Ang, Score });
	}
	Scored.Sort([](const FScored& A, const FScored& B) { return A.Score < B.Score; });
	const FScored* NB = nullptr;
	const FScored* PrevEntry = nullptr;
	for (int32 I = 0; I < Scored.Num() && I < 16; ++I)
	{
		const FScored& E = Scored[I];
		if (!Visible(*E.P, Eye)) continue;
		if (!NB && E.Ang < 0.55) NB = &E;
		if (PKey(E.P->Pos) == BestKey) PrevEntry = &E;
	}
	FScored PerchPick{ nullptr, 0, 0, 0 };
	if (!NB && PerchOut)
	{ // perched with nothing in view: the best point out in front of the perch
		double BS = TNumericLimits<double>::Max();
		for (const FTravZipPoint& P : Pool)
		{
			FVector D = P.Pos - Eye;
			const double Dist = D.Size();
			if (Dist < 3.0 || Dist > RANGE) continue;
			if (Exclude && FVector::DistSquared(P.Pos, *Exclude) < 4.0) continue;
			D /= Dist;
			const double Out = D.X * PerchOut->X + D.Y * PerchOut->Y;
			if (Out < 0.2) continue;
			const FMeta& M = PointMeta(P);
			if (!M.bOk || !Visible(P, Eye)) continue;
			const double SC = Dist / RANGE - Out + KindBonus(P.Kind) - (P.Pos.Z > Eye.Z - 2.0 ? 0.3 : 0.0);
			if (SC < BS) { BS = SC; PerchPick = { &P, Dist, 0, SC }; }
		}
		if (PerchPick.P) NB = &PerchPick;
	}
	// hysteresis: keep the current target unless the new one is clearly better
	if (PrevEntry && PrevEntry->Ang < 0.6 && (!NB || PrevEntry->Score < NB->Score + 0.25)) NB = PrevEntry;
	bHasBest = NB != nullptr;
	if (NB) { BestPt = *NB->P; BestKey = PKey(NB->P->Pos); }
	else BestKey.Reset();
	return bHasBest;
}
