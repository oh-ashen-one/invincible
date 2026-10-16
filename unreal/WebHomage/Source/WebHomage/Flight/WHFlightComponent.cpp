// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
// Invincible flight conversion (owner request 2026-10-15). See WHFlightComponent.h for the control map and the design.
#include "Flight/WHFlightComponent.h"
#include "Flight/WHFlightWorld.h"
#include "Traversal/WebTraversalComponent.h"
#include "Traversal/WebTravCamera.h"
#include "WebHomage.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "UObject/UnrealType.h"
#include "Engine/World.h"
#include "GameFramework/WorldSettings.h"

namespace
{
#define WF_NAME(x) const FName NF_##x(TEXT(#x));
	// flight subs (FWebTravAnimFlight contract in WebTravTypes.h)
	WF_NAME(takeoff) WF_NAME(hover) WF_NAME(fly) WF_NAME(boost) WF_NAME(brake) WF_NAME(dash) WF_NAME(slam) WF_NAME(breach) WF_NAME(landHero)
	// ground / events
	WF_NAME(idle) WF_NAME(landLight)
	WF_NAME(sonicBoom) WF_NAME(breachIn) WF_NAME(breachOut) WF_NAME(heroLand) WF_NAME(flyStop) WF_NAME(flyDash) WF_NAME(flyBump) WF_NAME(land)
	// owner feedback 2026-10-15: super-boost charge start (Severity = charge slow-mo dilation, K = real charge s), double-tap dive start
	WF_NAME(superCharge) WF_NAME(heroDive)
#undef WF_NAME
	const FVector FlUp(0, 0, 1);
	double FlDamp(double A, double B, double Rate, double Dt) { return A + (B - A) * (1.0 - FMath::Exp(-Rate * Dt)); }
	FVector FlDampV(const FVector& A, const FVector& B, double Rate, double Dt) { return A + (B - A) * (1.0 - FMath::Exp(-Rate * Dt)); }
	double FlSmooth(double X, double A, double B) { const double T = FMath::Clamp((X - A) / FMath::Max(B - A, 1e-6), 0.0, 1.0); return T * T * (3.0 - 2.0 * T); }
	double FlAngWrap(double A) { return FMath::Atan2(FMath::Sin(A), FMath::Cos(A)); }
	FVector FlYawDir(double A) { return FVector(FMath::Cos(A), FMath::Sin(A), 0.0); }
	double FlHLen(const FVector& V) { return FMath::Sqrt(V.X * V.X + V.Y * V.Y); }
	/** Rotate unit vector V toward unit vector W by at most MaxAng rad (great circle). */
	FVector FlTurnToward(const FVector& V, const FVector& W, double MaxAng)
	{
		const double Ang = FMath::Acos(FMath::Clamp(FVector::DotProduct(V, W), -1.0, 1.0));
		if (Ang <= MaxAng || Ang < 1e-5) return W;
		FVector Ax = FVector::CrossProduct(V, W);
		if (Ax.SizeSquared() < 1e-10) Ax = FVector::CrossProduct(V, FMath::Abs(V.Z) < 0.9 ? FlUp : FVector(1, 0, 0)); // opposite: any perpendicular
		return FQuat(Ax.GetSafeNormal(), MaxAng).RotateVector(V).GetSafeNormal();
	}
	bool FlIsFlightSub(FName N) { return N == NF_takeoff || N == NF_hover || N == NF_fly || N == NF_boost || N == NF_brake || N == NF_dash || N == NF_slam || N == NF_breach; }
}

UWHFlightComponent::UWHFlightComponent()
{
	PrimaryComponentTick.bCanEverTick = false; // driven by UWebTraversalComponent::UpdateTraversal
	Sub = NF_hover;
}

void UWHFlightComponent::ApplyTune(const FString& Tune)
{
	TArray<FString> Parts;
	Tune.ParseIntoArray(Parts, TEXT(","));
	for (const FString& Pr : Parts)
	{
		FString K, V;
		if (!Pr.Split(TEXT("="), &K, &V)) continue;
		if (FFloatProperty* FP = FindFProperty<FFloatProperty>(GetClass(), FName(*K)))
		{
			FP->SetPropertyValue_InContainer(this, FCString::Atof(*V));
			UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT tune %s = %s"), *K, *V);
		}
		else UE_LOG(LogWebHomage, Warning, TEXT("WH_FLIGHT tune: no float property %s"), *K);
	}
}

void UWHFlightComponent::Event(UWebTraversalComponent& T, FName Type, float Sev, const FVector& Pos, const FVector& Dir, float K)
{
	FWebTravEvent E;
	E.Type = Type; E.Severity = Sev; E.K = K; E.Pos = Pos; E.Dir = Dir;
	T.Events.Add(E);
}

void UWHFlightComponent::SetFlySub(UWebTraversalComponent& T, FName NewSub)
{
	if (Sub != NewSub) { Sub = NewSub; SubT = 0.0; }
	T.SetSub(NewSub);
}

void UWHFlightComponent::Takeoff(UWebTraversalComponent& T)
{
	auto& S = T.S;
	const FVector Feet(S.Pos.X, S.Pos.Y, S.Pos.Z - UWebTraversalComponent::H);
	T.SetMode(EWebTravMode::Air, NF_takeoff);
	Sub = NF_takeoff; SubT = 0.0;
	S.bGrounded = false; S.bCharging = false; S.JumpCharge = 0; S.AirT = 0; S.ApexZ = Feet.Z;
	S.Vel = FVector(S.Vel.X * 0.5, S.Vel.Y * 0.5, TakeoffVz);
	S.Pos.Z += 0.05;
	bSlam = false;
	Event(T, TEXT("takeoff"), 0.3f, Feet, FlUp);
	if (UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(GetOwner()))
		FW->PushStimulus(EWHCrowdStimulus::Landing, Feet * 100.0, 900.f, 0.35f, 2.5f);
}

void UWHFlightComponent::HeroLand(UWebTraversalComponent& T, double Floor, double ImpactSpeed, bool bWasSlam)
{
	auto& S = T.S;
	S.Pos.Z = Floor + UWebTraversalComponent::H; S.FloorZ = Floor;
	const bool bHero = bWasSlam || ImpactSpeed >= HeroLandMinSpeed;
	const double Sev = FMath::Clamp((ImpactSpeed - SoftLandSpeed) / FMath::Max(1.0, 90.0 - SoftLandSpeed), 0.0, 1.0);
	const FVector Feet(S.Pos.X, S.Pos.Y, Floor);
	T.EnterGround(bHero ? NF_landHero : (ImpactSpeed > 6.0 ? NF_landLight : NF_idle));
	S.Vel = FVector::ZeroVector; S.Speed = 0; S.Carry = FVector::ZeroVector;
	S.LandSeverity = bHero ? FMath::Max(Sev, 0.35) : Sev;
	S.LandLock = bHero ? HeroLandLock : 0.0;
	bSlam = false; bBreach = false;
	bDiveDrop = false;                                 // owner feedback #2: the double-tap dive ends here (superhero landing)
	if (SuperState != ESuper::None) EndSuper(true);    // owner feedback #1: a super line into the street ends in a crater landing
	Sub = NAME_None; SubT = 0.0;
	if (bHero)
	{
		++HeroLandCount;
		Event(T, NF_heroLand, float(S.LandSeverity), Feet, -FlUp, float(ImpactSpeed));
		if (UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(GetOwner()))
			FW->PushStimulus(EWHCrowdStimulus::Landing, Feet * 100.0, float(1500.0 + 3500.0 * S.LandSeverity), 0.6f + 0.4f * float(S.LandSeverity), 5.f);
		UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT heroLand at (%.1f, %.1f, %.1f) impact %.1f m/s sev %.2f"), Feet.X, Feet.Y, Feet.Z, ImpactSpeed, S.LandSeverity);
	}
	else Event(T, NF_land, float(S.LandSeverity), Feet, -FlUp);
}

bool UWHFlightComponent::StartBreach(UWebTraversalComponent& T, const FVector& HitPos, const FVector& HitN, const FVector& Dir)
{
	const FWebTravWorld& W = T.TravWorld;
	auto& S = T.S;
	// suite round 1 (sim fl01 / fl14): floors and roofs are landed on, never breached (a 10 m/s hover descent was carried straight down
	// through the street), and the exit must leave the body above the street (fl14 exited 1.8 m under it and flew on underground)
	if (FMath::Abs(Dir.Z) > 0.75 || S.Vel.Size() < double(BreachSpeed) * 0.95) return false;
	// march through the solid along the flight line until the body fits outside it again (building boxes and visual solids)
	auto FreeAt = [&W](const FVector& P) { return !W.Inside(P, 0.1) && !W.SphereOverlaps(P, 0.5); };
	auto ExitAboveStreet = [&W, &HitPos, &Dir](double D)
	{
		const FVector Exit = HitPos + Dir * (D + 0.6);
		const double Street = W.GroundHeight(Exit.X, Exit.Y, Exit.Z + 0.5);
		return !(Street > -999.0 && Exit.Z - UWebTraversalComponent::H < Street - 0.05);
	};
	double Sx = -1.0;
	for (double D = 0.6; D <= double(BreachMaxDepth); D += 0.5)
	{
		if (FreeAt(HitPos + Dir * D)) { Sx = D; break; }
	}
	if (Sx < 0.0) return false;
	if (!ExitAboveStreet(Sx)) return false;
	// critic r2 fl14 (after the exit he was at 0.000 m/s for 5.4 s, pinned against the next tower of a courtyard): the exit kept 0.8 x a
	// cruise entry = 44 m/s, under BreachSpeed, and the 0.25 s cooldown blocked a second breach anyway, so the next facade a few metres on
	// stopped him dead. The exit now keeps at least 1.05 x BreachSpeed, and a solid met within the run the exit speed covers in the
	// cooldown (+ 4 m) is carried through in the same breach (same time bound), up to BreachMaxDepth in total. A next solid too deep to
	// pass (or an exit under the street) keeps the first exit; the contact slide then steers along the free direction (DeflectFree).
	const double ExitV = FMath::Max(double(BreachSpeed) * 1.05, S.Vel.Size() * double(BreachKeep));
	{
		const double Run = FMath::Max(6.0, ExitV * double(BreachCooldown) + 4.0);
		for (int32 Chain = 0; Chain < 4; ++Chain)
		{
			double Block = -1.0;
			for (double D = Sx + 0.5; D <= Sx + Run; D += 0.5)
			{
				if (!FreeAt(HitPos + Dir * D)) { Block = D; break; }
			}
			if (Block < 0.0) break;   // clear run ahead of this exit
			double Sx2 = -1.0;
			for (double D = Block + 0.5; D <= double(BreachMaxDepth); D += 0.5)
			{
				if (FreeAt(HitPos + Dir * D)) { Sx2 = D; break; }
			}
			if (Sx2 < 0.0 || !ExitAboveStreet(Sx2)) break;
			Sx = Sx2;
		}
	}
	bBreach = true;
	BreachA = HitPos - Dir * 0.05; BreachDir = Dir; BreachLen = Sx + 0.6; BreachS = 0.0;
	BreachB = BreachA + Dir * BreachLen;
	BreachExitV = ExitV;
	// the body is out of sight inside the solid: the pass is time-bounded (fl14: 124 m at 44 m/s hid the hero for 2.8 s), the exit keeps
	// the kept speed
	BreachV = FMath::Max(BreachExitV, BreachLen / FMath::Max(0.1, double(BreachMaxTime)));
	BreachExitN = Dir;
	++BreachCount;
	SetFlySub(T, NF_breach);
	Event(T, NF_breachIn, FMath::Clamp(float(S.Vel.Size() / BoostSpeed), 0.f, 1.f), HitPos, Dir, float(S.Vel.Size()));
	if (UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(GetOwner()))
		FW->PushStimulus(EWHCrowdStimulus::Impact, HitPos * 100.0, 4000.f, 1.f, 6.f, S.Vel * 100.0);
	UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT breach in at (%.1f, %.1f, %.1f) n (%.2f, %.2f, %.2f) speed %.1f depth %.1f m"),
		HitPos.X, HitPos.Y, HitPos.Z, HitN.X, HitN.Y, HitN.Z, S.Vel.Size(), BreachLen);
	return true;
}

void UWHFlightComponent::StepBreach(UWebTraversalComponent& T, double H)
{
	auto& S = T.S;
	BreachS += BreachV * H;
	S.Pos = BreachA + BreachDir * FMath::Min(BreachS, BreachLen);
	S.Vel = BreachDir * BreachV;
	if (BreachS >= BreachLen)
	{
		bBreach = false; BreachCd = BreachCooldown;
		S.Vel = BreachDir * BreachExitV;
		Event(T, NF_breachOut, FMath::Clamp(float(BreachV / BoostSpeed), 0.f, 1.f), BreachB, BreachDir, float(BreachV));
		if (UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(GetOwner()))
			FW->PushStimulus(EWHCrowdStimulus::Impact, BreachB * 100.0, 4000.f, 1.f, 6.f, S.Vel * 100.0);
		SetFlySub(T, NF_fly);
	}
}

// critic r2 fl14 (pinned at 0.000 m/s against a glass tower after a breach exit): a contact that cannot be breached keeps its speed, turned
// along the facade toward the free direction -- the tangential part of the travel when there is a real one, else up / along the wall to
// either side, whichever has the longest clear run (ties: up, over the building)
void UWHFlightComponent::DeflectFree(UWebTraversalComponent& T, const FVector& HitN, double Speed)
{
	auto& S = T.S;
	if (Speed < 1.0) return;
	const FVector D = FreeAlong(T, HitN, Speed, 0.5);
	if (!D.IsNearlyZero()) S.Vel = D * Speed;
}

FVector UWHFlightComponent::FreeAlong(UWebTraversalComponent& T, const FVector& HitN, double Speed, double TanShare) const
{
	const auto& S = T.S;
	const FWebTravWorld& W = T.TravWorld;
	const FVector Tan = S.Vel - HitN * FVector::DotProduct(S.Vel, HitN);
	if (Tan.Size() >= TanShare * FMath::Max(Speed, 1e-3) && Tan.Size() > 0.5) return Tan.GetSafeNormal();
	const FVector Nh = FVector(HitN.X, HitN.Y, 0.0).GetSafeNormal();
	if (Nh.IsNearlyZero()) return FVector::ZeroVector;
	const FVector Along = FVector::CrossProduct(FlUp, Nh);
	const FVector From = S.Pos + Nh * 0.6;
	FVector Cands[3] = { FlUp, Along, -Along };
	if (FVector::DotProduct(Tan, Along) < 0.0) Swap(Cands[1], Cands[2]);   // a little tangential travel picks its side first
	FVector Best = FlUp;
	double BestFree = -1.0;
	for (const FVector& C : Cands)
	{
		double D = 0.0; FVector N = FVector::ZeroVector;
		const double Free = W.SweepSolid(From, From + C * 15.0, 0.45, D, N) ? D : 15.0;
		if (Free > BestFree + 0.5) { BestFree = Free; Best = C; }
	}
	return Best;
}

// critic r4 fl16 (stick-back slow flight head-on into a facade: position locked within 4 cm for 5.5 s, head and arm inside the fire-escape
// grate): a slow fly line keeps its body centre WallStandoffM off the facade (+ WallHeadReachM x how square he heads into it, so the leading
// head / fists stay clear), the speed component into the wall is bled off smoothly (it may close at no more than WallApproachRate x the
// remaining gap; inside the standoff he eases back out at <= 3 m/s), and the bled speed is turned along the wall toward the free side
// (FreeAlong: the tangential travel, else up / left / right), never under SlideMinSpeed while fly is held. Rays (visual collision, so
// fire escapes / balconies count) along the horizontal travel and back toward the last wall normal; the swept contact stays the backstop.
bool UWHFlightComponent::WallStandoff(UWebTraversalComponent& T, double H, const FWebTravInput& I)
{
	auto& S = T.S;
	const FWebTravWorld& W = T.TravWorld;
	SlideDirT = FMath::Max(0.0, SlideDirT - H);
	const double Rs = FMath::Max(0.5, double(WallStandoffM));
	const double Sp0 = S.Vel.Size();
	const FVector Vh(S.Vel.X, S.Vel.Y, 0.0);
	const double Reach = Rs + double(WallHeadReachM) + FMath::Max(0.0, Vh.Size()) / FMath::Max(1.0, double(WallApproachRate)) + 0.5;
	FTravHit Best; bool bHit = false;
	auto Probe = [&](const FVector& D)
	{
		if (D.IsNearlyZero()) return;
		FTravHit Hh;
		if (W.Raycast(S.Pos, D, Reach, Hh) && FMath::Abs(Hh.Normal.Z) < 0.5 && !Hh.bGround && (!bHit || Hh.Distance < Best.Distance)) { Best = Hh; bHit = true; }
	};
	if (Vh.Size() > 0.5) Probe(Vh.GetSafeNormal());
	if (!WallNLast.IsNearlyZero()) Probe(-WallNLast);
	if (!bHit) { if (SlideDirT <= 0.0) WallNLast = FVector::ZeroVector; return false; }
	FVector N = FVector(Best.Normal.X, Best.Normal.Y, 0.0).GetSafeNormal();
	if (N.IsNearlyZero()) return false;
	if (FVector::DotProduct(S.Pos - Best.Point, N) < 0.0) N = -N;   // out of the wall, toward the body
	WallNLast = N;
	const double Into = Sp0 > 0.5 ? FMath::Max(0.0, FVector::DotProduct(S.Vel / Sp0, -N)) : 0.0;
	const double Want = Rs + double(WallHeadReachM) * Into;
	const double Dd = FMath::Max(0.0, FVector::DotProduct(S.Pos - Best.Point, N));   // square distance to the facade plane (not the ray length)
	const double VN = FVector::DotProduct(S.Vel, N);
	// the slowest the gap may close (negative) / the speed it must open at (positive, capped 3 m/s)
	const double Allowed = FMath::Min(3.0, double(WallApproachRate) * (Want - Dd));
	if (VN < Allowed)
	{
		const double Bled = FMath::Max(0.0, -VN) - FMath::Max(0.0, -Allowed);
		S.Vel += N * (Allowed - VN);
		if (I.bSwing && Bled > 0.0)
		{ // the bled speed goes along the wall (held direction for a head-on contact)
			FVector Tan = S.Vel - N * FVector::DotProduct(S.Vel, N);
			if (SlideDirT <= 0.0 || SlideDir.IsNearlyZero() || FMath::Abs(FVector::DotProduct(SlideDir, N)) > 0.2)
			{
				SlideDir = FreeAlong(T, N, Sp0, 0.3);
				SlideDirT = 0.6;
			}
			const FVector Dir = Tan.Size() > 0.3 * Sp0 && Tan.Size() > 0.5 ? Tan.GetSafeNormal() : SlideDir;
			const double TanNew = FMath::Min(Sp0, Tan.Size() + Bled);
			S.Vel = N * FVector::DotProduct(S.Vel, N) + Dir * TanNew;
		}
	}
	if (I.bSwing && Dd < Want + 0.3)
	{ // never a freeze along the wall while fly is held
		const FVector Tan = S.Vel - N * FVector::DotProduct(S.Vel, N);
		if (Tan.Size() < double(SlideMinSpeed))
		{
			if (SlideDirT <= 0.0 || SlideDir.IsNearlyZero()) { SlideDir = FreeAlong(T, N, FMath::Max(Sp0, 1.0), 0.3); SlideDirT = 0.6; }
			const FVector Dir = Tan.Size() > 0.5 ? Tan.GetSafeNormal() : SlideDir;
			S.Vel = N * FVector::DotProduct(S.Vel, N) + Dir * double(SlideMinSpeed);
		}
	}
	// r3 hero request (wall-side tuck): facade side in the body frame and the distance to it (only near the standoff)
	if (Dd < Want + 0.5)
	{
		WallSideV = FMath::Clamp(FVector::DotProduct(-N, S.BodyQ.GetRightVector()), -1.0, 1.0);
		WallDistV = Dd; WallT = 0.25;
	}
	return true;
}

bool UWHFlightComponent::MoveAndCollide(UWebTraversalComponent& T, double H, const FWebTravInput& I)
{
	auto& S = T.S;
	const FWebTravWorld& W = T.TravWorld;
	// critic r4 fl16: slow fly lines (under breach speed) hold a standoff from facades and slide along them (WallStandoff). Not while fly is
	// held with the stick forward square into a wall: that keeps the round-1 pin-and-punch-through (PunchPinTime) below.
	if (WallStandoffM > 0.f && (Sub == NF_fly || Sub == NF_dash) && S.Vel.Size() < double(BreachSpeed) * 0.95)
	{
		bool bPunchWanted = false;
		if (I.bSwing && I.Move.Y > -0.3 && !WallNLast.IsNearlyZero() && S.Vel.Size() > 1.0)
			bPunchWanted = FVector::DotProduct(S.Vel.GetSafeNormal(), -WallNLast) > 0.6;
		if (!bPunchWanted) WallStandoff(T, H, I);
	}
	else if (SlideDirT <= 0.0) WallNLast = FVector::ZeroVector;
	const FVector P0 = S.Pos;
	const FVector P1 = P0 + S.Vel * H;
	const double Sp = S.Vel.Size();
	double HitD = 0.0; FVector HitN = FVector::ZeroVector;
	const FVector Step = P1 - P0;
	const double L = Step.Size();
	bool bPinned = false;
	if (L > 1e-5 && W.SweepSolid(P0, P1, 0.45, HitD, HitN))
	{
		const FVector Dir = Step / L;
		const FVector HitPos = P0 + Dir * HitD;
		// critic r2 fl14: inside the post-exit cooldown a NEW facade ahead (its inward normal along the last breach direction -- the face
		// just left can only be met moving back into it) is breached as well instead of stopping him against it
		const bool bNewFace = BreachCd > 0.0 && FVector::DotProduct(-HitN, BreachExitN) > 0.3;
		// (a grazing contact -- under ~20 deg to the facade, e.g. the fast slide DeflectFree leaves him in -- slides: marching a breach
		//  along the wall face found "free" space 0.6 m on and staged a 1 m breach with its camera hold / cut)
		const bool bHeadOn = FVector::DotProduct(Dir, -HitN) > 0.34;
		bool bBreachFailed = false;
		if (FMath::Abs(HitN.Z) < 0.6 && Sp >= BreachSpeed && bHeadOn && (BreachCd <= 0.0 || bNewFace) && Sub != NF_slam)
		{
			if (StartBreach(T, HitPos, HitN, Dir))
			{
				StepBreach(T, FMath::Max(0.0, H - HitD / FMath::Max(Sp, 1.0)));
				return true;
			}
			bBreachFailed = true;
		}
		S.Pos = P0 + Dir * FMath::Max(0.0, HitD - 0.02);
		if (HitN.Z >= 0.6)
		{ // floor / roof under the flight line
			// (suite r2 sim fl11: the 0.45 m sweep sphere touches the floor with its centre 0.45 m up, so "centre - H" put the feet 0.5 m
			//  into the street and the hero then dropped through it into a hover; the floor is the sphere's contact height)
			const double FloorZ = S.Pos.Z - 0.47;
			const double Impact = FMath::Max(0.0, -S.Vel.Z);
			if (Sub == NF_slam || Impact > SoftLandSpeed || (I.bDrop && Sub == NF_hover)) { HeroLand(T, FloorZ, FMath::Max(Impact, Sub == NF_slam ? Sp : 0.0), Sub == NF_slam); return true; }
			S.Pos.Z = FMath::Max(S.Pos.Z, FloorZ + UWebTraversalComponent::H);
			if (S.Vel.Z < 0) S.Vel.Z = 0;
		}
		else
		{ // slide along the facade (slow, or a deep solid that cannot be breached)
			// critic r1 (fl10 / fl16 frozen 4.7 s at 19 m/s): resting 2 cm off the wall, the next tangential sweep grazed the same face at
			// distance 0 (normal square to the motion, so nothing was removed) every step -- stand a few cm clear of it
			S.Pos += FVector(HitN.X, HitN.Y, 0.0) * 0.05;
			{ // r3 hero request: the wall-side arm / leg tuck needs the facade side in the body frame and the distance to it
				WallSideV = FMath::Clamp(FVector::DotProduct(-HitN, S.BodyQ.GetRightVector()), -1.0, 1.0);
				WallDistV = 0.47; WallT = 0.25;
			}
			const double VN = FVector::DotProduct(S.Vel, HitN);
			if (VN < 0)
			{
				S.Vel -= HitN * VN;
				if (-VN > 15.0) { Event(T, NF_flyBump, FMath::Clamp(float(-VN / 60.0), 0.f, 1.f), HitPos, HitN); }
			}
			// critic r2 fl14 (0.000 m/s pinned against a tower after a breach exit): a fast fly-held contact that could not breach (solid
			// deeper than BreachMaxDepth, exit under the street) keeps its speed and turns along the free direction instead of stopping dead
			if (bBreachFailed && I.bSwing) DeflectFree(T, HitN, Sp);
			// suite round 1 (sim fl14: pinned motionless for 1.1 s): fly held head-on into a facade under BreachSpeed accelerated, slid to
			// zero and repeated every step. After PunchPinTime of pushing he punches through instead; slow flight (stick back) keeps sliding.
			if (I.bSwing && I.Move.Y > -0.3 && Sub != NF_slam && BreachCd <= 0.0 && FMath::Abs(HitN.Z) < 0.6 && FVector::DotProduct(Dir, -HitN) > 0.6)
			{
				bPinned = true; PinT += H;
				if (PinT >= double(PunchPinTime))
				{
					const FVector PD = FVector(-HitN.X, -HitN.Y, 0.0).GetSafeNormal();
					const FVector V0 = S.Vel;
					S.Vel = PD * FMath::Max(double(BreachSpeed), V0.Size());
					if (StartBreach(T, HitPos, HitN, PD)) { PinT = 0.0; return true; }
					S.Vel = V0;
					// critic r2 fl14: a punch that cannot get through (too deep) no longer leaves him pinned at 0 m/s for good -- he is turned
					// along / up the facade at no less than half the cruise speed
					DeflectFree(T, HitN, FMath::Max3(Sp, V0.Size(), 0.5 * double(CruiseSpeed)));
					PinT = 0.0;
				}
			}
		}
	}
	else S.Pos = P1;
	// the floor below (street, roofs): land or skim
	const double Feet = S.Pos.Z - UWebTraversalComponent::H;
	// (suite r2 sim fl11: a 95 m/s slam step sank the feet 0.8 m under the street before this probe, which then started under it and
	//  landed him at -0.5 m; probe from the higher of the old and new feet)
	const double Floor = W.GroundHeight(S.Pos.X, S.Pos.Y, FMath::Max(Feet, P0.Z - UWebTraversalComponent::H) + 0.6);
	if (Floor > -999.0 && Feet < Floor)
	{
		const double Impact = FMath::Max(0.0, -S.Vel.Z);
		if (Sub == NF_slam || Impact > SoftLandSpeed || (I.bDrop && Sub == NF_hover)) { HeroLand(T, Floor, FMath::Max(Impact, Sub == NF_slam ? Sp : 0.0), Sub == NF_slam); return true; }
		S.Pos.Z = Floor + UWebTraversalComponent::H;
		if (S.Vel.Z < 0) S.Vel.Z = 0;
	}
	// critic r2 (fl13 touchdown): the snap-down band 0.35 -> 0.05 m (at the capped descent a 0.35 m snap started from ~3.2 m/s and moved the
	// body 0.35 m in one step; the feet-under-floor branch above now makes the contact at ~TouchdownV)
	else if (Floor > -999.0 && Sub == NF_hover && I.bDrop && Feet - Floor < 0.05 && S.Vel.Z <= 0.5)
	{ // hover + descend held right over the floor: a gentle touchdown
		HeroLand(T, Floor, FMath::Max(0.0, -S.Vel.Z), false);
		return true;
	}
	// slow flight: the capsule push-out keeps the body off poles / facades (fast flight is swept above)
	if (Sp < 25.0)
	{
		FTravContact C;
		const FVector PreP = S.Pos;
		if (T.Collide(UWebTraversalComponent::STEP, UWebTraversalComponent::R, C))
		{
			const double VN = S.Vel.X * C.Normal.X + S.Vel.Y * C.Normal.Y;
			if (VN < 0) { S.Vel.X -= C.Normal.X * VN; S.Vel.Y -= C.Normal.Y * VN; }
			// critic r1 (fl10 / fl16: frozen 4.7 s while speed read 19 m/s, body rocking): the push-out can also undo the step along the
			// wall (an indexed solid the swept collision does not see); whatever it pushes against is taken out of the velocity as well
			const FVector Corr(S.Pos.X - PreP.X, S.Pos.Y - PreP.Y, 0.0);
			if (Corr.SizeSquared() > 1e-8)
			{
				const FVector Nc = Corr.GetSafeNormal();
				const double VC = S.Vel.X * Nc.X + S.Vel.Y * Nc.Y;
				if (VC < 0) { S.Vel.X -= Nc.X * VC; S.Vel.Y -= Nc.Y * VC; }
			}
		}
	}
	if (!bPinned) PinT = 0.0;
	return false;
}

void UWHFlightComponent::StepAirSub(UWebTraversalComponent& T, double H, const FWebTravInput& I)
{
	auto& S = T.S;
	FVector& V = S.Vel;
	const FWebTravCamera* Cam = T.Cam;
	// hover / takeoff frame: the camera's ground plane (hover stays the precise, camera-relative mode)
	const FVector FwdF = Cam ? Cam->ForwardFlat() : FlYawDir(S.Facing);
	const FVector RightF = Cam ? Cam->RightFlat() : FVector(-FMath::Sin(S.Facing), FMath::Cos(S.Facing), 0.0);
	// owner feedback #3 (flight-sim feel): in the fly / super line the hero steers by his own nose (AimYaw, moved by look input and stick X
	// in StepFlight) -- the camera chases him instead of leading him
	const FVector FwdN = bAttitude ? FlYawDir(AimYaw) : FwdF;
	const FVector RightN = bAttitude ? FVector(-FMath::Sin(AimYaw), FMath::Cos(AimYaw), 0.0) : RightF;
	// aim = nose yaw + the flight's own held pitch (see AimPitch in the header), never the camera's hero-framing look-down
	const FVector Aim = (FwdN * FMath::Cos(AimPitch) - FlUp * FMath::Sin(AimPitch)).GetSafeNormal();
	const bool bFly = I.bSwing;
	Climb = (I.bJump ? 1.0 : 0.0) - (I.bDrop ? 1.0 : 0.0);
	StickBody = I.Move;
	if (!FlIsFlightSub(S.Sub)) SetFlySub(T, NF_hover); // walked off a ledge / any legacy air sub: hover
	if (Sub != S.Sub) Sub = S.Sub;

	// ---- presses (cleared by the caller after the first substep)
	if (I.bZipPressed && Sub != NF_slam)
	{ // instant stop (also ends a super boost)
		if (SuperState != ESuper::None) EndSuper(true);
		SetFlySub(T, NF_brake); ++BrakeCount;
		Event(T, NF_flyStop, FMath::Clamp(float(V.Size() / CruiseSpeed), 0.f, 1.5f), S.Pos, V.GetSafeNormal());
	}
	if (I.bQuickPressed && DashCd <= 0.0 && Sub != NF_slam && SuperState == ESuper::None)
	{
		FVector D = (bAttitude ? FwdN : FwdF) * I.Move.Y + (bAttitude ? RightN : RightF) * I.Move.X;
		DashDir = D.SizeSquared() > 0.09 ? D.GetSafeNormal() : Aim;
		V += DashDir * double(DashDv);
		DashCd = DashCooldown; ++DashCount;
		SetFlySub(T, NF_dash);
		Event(T, NF_flyDash, 0.5f, S.Pos, DashDir);
	}
	if (I.bTrickPressed && Sub != NF_slam)
	{ // dive straight down for a superhero landing
		if (SuperState != ESuper::None) EndSuper(true);
		SetFlySub(T, NF_slam); bSlam = true; bDiveDrop = false;
	}
	// owner feedback #2: a second airborne Space press within DoubleTapTime = the accelerating superhero-landing dive; the first press keeps
	// its single-press meaning (climb). The takeoff press is handled on the ground and never opens the window.
	if (I.bJumpPressed)
	{
		if (JumpTapT <= double(DoubleTapTime) && Sub != NF_slam) { StartDive(T); JumpTapT = 99.0; }
		else JumpTapT = 0.0;
	}
	// owner feedback #1: Shift / L3 from fly or hover (any airborne flight sub but the slam) = the sonic-boom super boost: charge first
	if (I.bSprintPressed && SuperState == ESuper::None && SuperCd <= 0.0 && Sub != NF_slam)
	{
		SuperState = ESuper::Charge; SuperT = 0.0; ++SuperCount;
		SetFlySub(T, NF_brake);   // the snap stop / hang reads through the brake flare; FWebTravAnimFlight::ChargeK carries the coil
		Event(T, NF_superCharge, FMath::Clamp(SuperChargeSlowMo, 0.05f, 1.f), S.Pos, Aim, SuperChargeTime);
		UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT super charge at (%.1f, %.1f, %.1f) from %s %.1f m/s"), S.Pos.X, S.Pos.Y, S.Pos.Z, *Sub.ToString(), V.Size());
	}

	const double Sp = V.Size();
	// owner feedback #1 / #3: one fly-line step for cruise and super speed -- the travel turns toward the nose at no more than LatAccel of
	// lateral acceleration (turn radius v^2 / LatAccel: momentum, wide turns at speed), climbing costs speed / diving gains a little
	// (ClimbEnergyK x g x sin(climb)), then the acceleration curve toward Vt (or the decay above it at DecelRate)
	auto StepLine = [&](double Vt, double LatAccel, double AccelUp, double DecelRate) -> double
	{
		FVector D = Aim;
		if (FMath::Abs(Climb) > 0.01)
		{
			const FVector Rt = FVector::CrossProduct(FlUp, D).GetSafeNormal();
			if (!Rt.IsNearlyZero()) D = FQuat(Rt, -FMath::DegreesToRadians(ClimbPitchDeg) * Climb).RotateVector(D); // +Climb pitches up
		}
		D = D.GetSafeNormal();
		FVector Dir = Sp > 1.0 ? V / Sp : D;
		const double MaxW = FMath::Min(FMath::DegreesToRadians(double(TurnRateSlow)), FMath::Max(1.0, LatAccel) / FMath::Max(Sp, 1.0));
		Dir = FlTurnToward(Dir, D, MaxW * H);
		double V1 = Sp - 9.81 * double(ClimbEnergyK) * Dir.Z * H;
		if (V1 < Vt)
		{
			const double A = AccelUp * FMath::Max(0.06, 1.0 - FMath::Pow(FMath::Max(0.0, V1) / FMath::Max(Vt, 1.0), double(AccelExp)));
			V1 = FMath::Min(Vt, V1 + A * H);
		}
		else V1 -= (V1 - Vt) * (1.0 - FMath::Exp(-DecelRate * H));
		V1 = FMath::Max(0.0, V1);
		V = Dir * V1;
		return V1;
	};
	if (SuperState == ESuper::Charge)
	{ // snap to a hang (SuperT runs in real seconds in StepFlight, so the slow-mo does not stretch the charge)
		V *= FMath::Exp(-double(SuperChargeStopRate) * H);
		SetFlySub(T, NF_brake);
		if (SuperT >= double(SuperChargeTime)) SuperLaunch(T, Aim, RightN, I);
	}
	else if (SuperState == ESuper::Run)
	{ // held Shift: the super-speed line (steerable, wide turns)
		if (LaunchRampS >= 0.0)
		{ // critic r4 fl04 (0 -> 243 m/s in one telemetry step): the launch ramp -- SuperLaunchV0 at the boom frame, then an explosive
		  // (ease-out / smoothstep mix: ~1300 m/s^2 at the start, none at the end) climb to LaunchVEnd over SuperLaunchRampT s along the travel
			LaunchRampS += H;
			const double Rt = FMath::Max(0.02, double(SuperLaunchRampT));
			const double K = FMath::Clamp(LaunchRampS / Rt, 0.0, 1.0);
			const double E = 0.5 * K * K * (3.0 - 2.0 * K) + 0.5 * (1.0 - (1.0 - K) * (1.0 - K));
			const FVector Dir = Sp > 1.0 ? V / Sp : LaunchDir;
			V = Dir * FMath::Lerp(FMath::Min(double(SuperLaunchV0), LaunchVEnd), LaunchVEnd, E);
			if (K >= 1.0) LaunchRampS = -1.0;
		}
		else StepLine(double(SuperSpeed), double(SuperLatAccel), double(SuperAccel), double(Decel));
		SetFlySub(T, NF_boost);
		// (a tap of Shift still gets the whole launch: the release only counts once the ramp is done)
		if (!I.bSprint && LaunchRampS < 0.0) { SuperState = ESuper::Decel; SuperT = 0.0; }
	}
	else if (SuperState == ESuper::Decel)
	{ // released: back to cruise over SuperDecelTime, then the ordinary fly / hover rules
		const double V1 = StepLine(double(CruiseSpeed), double(SuperLatAccel), double(Accel), double(SuperDecelRate));
		SetFlySub(T, V1 > SonicSpeed * 0.8 ? NF_boost : NF_fly);
		if (SuperT >= double(SuperDecelTime) || V1 <= CruiseSpeed * 1.05) EndSuper(true);
	}
	else if (Sub == NF_takeoff)
	{
		const double K = FMath::Clamp(SubT / FMath::Max(0.05, double(TakeoffDur)), 0.0, 1.0);
		V.Z = FMath::Max(V.Z, double(TakeoffVz) * FMath::Pow(1.0 - K, 1.5) + Climb * VertSpeed * K);
		const FVector Want = (FwdF * I.Move.Y + RightF * I.Move.X) * double(HoverSpeed);
		V.X = FlDamp(V.X, Want.X, HoverRate, H); V.Y = FlDamp(V.Y, Want.Y, HoverRate, H);
		if (K >= 1.0) SetFlySub(T, bFly ? NF_fly : NF_hover);
		else if (bFly && SubT > 0.15) SetFlySub(T, NF_fly);
	}
	else if (Sub == NF_brake)
	{
		V *= FMath::Exp(-double(BrakeRate) * H);
		if (SubT >= BrakeDur) SetFlySub(T, NF_hover);
	}
	else if (Sub == NF_slam)
	{
		if (bDiveDrop)
		{ // owner feedback #2 (double-tap Space): straight down, accelerating hard (DiveAccelNow grows with the height, see StartDive)
			V.X = FlDamp(V.X, 0.0, 6.0, H); V.Y = FlDamp(V.Y, 0.0, 6.0, H);
			V.Z = FMath::Max(-double(DiveMaxSpeed), V.Z - DiveAccelNow * H);
		}
		else
		{
			const FVector Want(V.X * 0.15, V.Y * 0.15, -double(SlamSpeed));
			V = FlDampV(V, Want, 7.0, H);
		}
	}
	else if (Sub == NF_dash && SubT < DashDur)
	{
		// the burst carries; a light drag back toward the fly / hover speed band afterwards
		V *= FMath::Exp(-0.6 * H);
	}
	else if (bFly)
	{ // owner feedback #3: cruise line steered by the nose with momentum (StepLine); owner feedback #1: Shift no longer ramps a boost here
		// (the old TurnRateSlow..TurnRateFast blend and StickYawDeg aim offset are replaced by FlyLatAccel and the stick turn in StepFlight)
		double Vt = CruiseSpeed;
		if (I.Move.Y < -0.3) Vt *= FMath::Lerp(1.0, 0.35, FMath::Clamp((-I.Move.Y - 0.3) / 0.7, 0.0, 1.0)); // stick back = slow flight
		const double V1 = StepLine(Vt, double(FlyLatAccel), double(Accel), double(Decel));
		SetFlySub(T, V1 > SonicSpeed * 0.8 ? NF_boost : NF_fly);
	}
	else
	{ // hover: stick strafes on the camera's ground plane, Space / C climb; a fast arrival glides down instead of stopping dead
		double ClimbV = Climb * double(VertSpeed);
		double DescCap = -1.0;   // m/s: fastest descent allowed at this height (-1 = no floor found)
		if (Climb < 0.0)
		{ // critic r2 (fl01 / fl13: "gentle" touchdowns stopped from 10 m/s in one frame): the descent eases out over the last 4 m
			// critic r2 / r3 replay (fl13: the linear ease still met the floor at ~5 m/s -- the 4/s velocity damp lagged its target): the
			// descent follows a constant-deceleration profile to TouchdownV at the floor, and the damped velocity is capped by it below
			const double FeetZ = S.Pos.Z - UWebTraversalComponent::H;
			const double Fl = T.TravWorld.GroundHeight(S.Pos.X, S.Pos.Y, FeetZ + 0.6);
			if (Fl > -999.0)
			{
				const double Tv = double(TouchdownV);
				DescCap = FMath::Sqrt(Tv * Tv + 2.0 * FMath::Max(0.1, double(TouchdownDecel)) * FMath::Max(0.0, FeetZ - Fl - double(TouchdownSlowH)));
				ClimbV = -FMath::Min(-ClimbV, DescCap);
			}
		}
		const FVector Want = (FwdF * I.Move.Y + RightF * I.Move.X) * double(HoverSpeed) + FlUp * ClimbV;
		const double Rate = Sp > HoverSpeed * 1.5 ? HoverGlideRate : HoverRate;
		V = FlDampV(V, Want, Rate, H);
		if (DescCap >= 0.0 && V.Z < -DescCap) V.Z = -DescCap;
		SetFlySub(T, NF_hover);
	}
	// (owner feedback #1: the speed-crossing sonic boom is gone -- the boom fires only at a super launch, SuperLaunch)
}

// owner feedback #1: the end of the charge -- sonic boom and launch toward the stick (camera-relative: in the line the nose and the camera
// heading agree within CamLeadK of the lead) or, hands off the stick, the nose / aim
void UWHFlightComponent::SuperLaunch(UWebTraversalComponent& T, const FVector& Aim, const FVector& RightN, const FWebTravInput& I)
{
	auto& S = T.S;
	FVector D = Aim;
	if (I.Move.SizeSquared() > 0.09)
	{
		const FVector St = Aim * I.Move.Y + RightN * I.Move.X;
		if (!St.IsNearlyZero()) D = St.GetSafeNormal();
	}
	if (FlHLen(D) > 1e-3) AimYaw = FMath::Atan2(D.Y, D.X);
	AimPitch = FMath::Clamp(-FMath::Asin(FMath::Clamp(D.Z, -1.0, 1.0)), -1.35, 1.35);
	// critic r4 fl04: the launch accelerates over SuperLaunchRampT (StepAirSub, Run) instead of setting the full speed in one frame
	LaunchVEnd = double(SuperSpeed) * FMath::Clamp(double(SuperLaunchK), 0.1, 1.0);
	LaunchDir = D;
	if (SuperLaunchRampT > 0.001f) { S.Vel = D * FMath::Min(double(SuperLaunchV0), LaunchVEnd); LaunchRampS = 0.0; }
	else { S.Vel = D * LaunchVEnd; LaunchRampS = -1.0; }
	SuperState = ESuper::Run; SuperT = 0.0; LaunchK = 1.0;
	SetFlySub(T, NF_boost);
	BoomK = 1.0; ++BoomCount;
	const double Sp = S.Vel.Size();
	Event(T, NF_sonicBoom, 1.f, S.Pos, D, float(LaunchVEnd));
	if (UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(GetOwner()))
		FW->PushStimulus(EWHCrowdStimulus::SonicBoom, S.Pos * 100.0, 15000.f, 1.f, 3.f, D * LaunchVEnd * 100.0);
	UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT sonic boom (super launch) at (%.1f, %.1f, %.1f) dir (%.2f, %.2f, %.2f) %.1f m/s -> %.1f m/s over %.2f s"),
		S.Pos.X, S.Pos.Y, S.Pos.Z, D.X, D.Y, D.Z, Sp, LaunchVEnd, double(SuperLaunchRampT));
}

void UWHFlightComponent::EndSuper(bool bCooldown)
{
	if (bCooldown && SuperState != ESuper::None) SuperCd = SuperCooldown;
	SuperState = ESuper::None; SuperT = 0.0; ChargeK = 0.0;
	LaunchRampS = -1.0;   // critic r4 fl04: a brake / slam / landing ends the launch ramp too
}

// owner feedback #2: double-tap Space -- straight down into the superhero landing. The downward acceleration is at least DiveAccel and
// grows with the height to the floor below so the dive lands in about DiveTime s from any height (h = a t^2 / 2), capped at DiveMaxSpeed.
void UWHFlightComponent::StartDive(UWebTraversalComponent& T)
{
	auto& S = T.S;
	if (SuperState != ESuper::None) EndSuper(true);
	const double FeetZ = S.Pos.Z - UWebTraversalComponent::H;
	const double Fl = T.TravWorld.GroundHeight(S.Pos.X, S.Pos.Y, FeetZ + 0.6);
	const double Hh = Fl > -999.0 ? FMath::Max(0.0, FeetZ - Fl) : 0.0;
	const double Td = FMath::Max(0.5, double(DiveTime));
	DiveAccelNow = FMath::Max(double(DiveAccel), 2.0 * Hh / (Td * Td));
	SetFlySub(T, NF_slam); bSlam = true; bDiveDrop = true; ++DiveCount;
	S.Vel.Z = FMath::Min(S.Vel.Z, -8.0);   // he tips over at once (head-first dive in the anim's slam roll)
	Event(T, NF_heroDive, float(FMath::Clamp(Hh / 200.0, 0.0, 1.0)), S.Pos, -FlUp, float(Hh));
	UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT double-tap dive at (%.1f, %.1f, %.1f) height %.1f m accel %.0f m/s^2"), S.Pos.X, S.Pos.Y, S.Pos.Z, Hh, DiveAccelNow);
}

FQuat UWHFlightComponent::FlightOrient(UWebTraversalComponent& T, double Dt, const FWebTravInput& I)
{
	auto& S = T.S;
	const FVector V = S.Vel;
	const double Sp = V.Size(), HS = FlHLen(V);
	const bool bLine = (Sub == NF_fly || Sub == NF_boost || Sub == NF_dash || Sub == NF_breach) && Sp > 6.0;
	FlyK = FlDamp(FlyK, bLine ? FlSmooth(Sp, 6.0, 25.0) : 0.0, 6.0, Dt);
	// bank: centripetal lean from the yaw rate of travel (+ = right turn)
	const double VelYaw = FMath::Atan2(V.Y, V.X);
	double YR = 0.0;
	if (bHaveVelYaw && HS > 4.0) YR = FlAngWrap(VelYaw - LastVelYaw) / FMath::Max(Dt, 1e-3);
	LastVelYaw = VelYaw; bHaveVelYaw = HS > 4.0;
	// owner feedback #3: bank follows the turn (centripetal lean) plus an optional roll on stick X in the line
	const double BankMax = FMath::DegreesToRadians(double(BankMaxDeg));
	const double BankWant = FMath::Clamp(FMath::Clamp(YR * HS / 30.0, -1.0, 1.0) * BankMax + FMath::DegreesToRadians(double(StickRollDeg)) * StickBody.X, -BankMax, BankMax) * FlyK;
	Bank = FlDamp(Bank, BankWant, 5.0, Dt);
	// hover frame: faces the camera's look, leans with the stick
	const double CamYaw = T.Cam ? T.Cam->Yaw : S.Facing;
	const bool bCharge = SuperState == ESuper::Charge;
	if (!bHoverYawInit) { HoverYaw = S.Facing; bHoverYawInit = true; }
	if (bCharge) HoverYaw = HoverYaw + FlAngWrap(AimYaw - HoverYaw) * (1.0 - FMath::Exp(-10.0 * Dt)); // owner feedback #1: he turns to the launch line
	else if (FlyK > 0.5 && HS > 4.0) HoverYaw = VelYaw; // coming out of a fly line the hover keeps the travel heading
	else HoverYaw = HoverYaw + FlAngWrap(CamYaw - HoverYaw) * (1.0 - FMath::Exp(-6.0 * Dt));
	const double Lean = FMath::DegreesToRadians(double(HoverLeanDeg));
	double LeanP = I.Move.Y * Lean, LeanR = I.Move.X * Lean;
	if (Sub == NF_brake) LeanP = -0.6;                       // legs swing forward under the stop
	if (bCharge) { LeanP = -double(SuperChargeLean) * ChargeK; LeanR = 0.0; }   // owner feedback #1: the body coils back through the charge
	if (Sub == NF_slam) { LeanP = 0.18; LeanR = 0.0; }        // feet first, slight forward pitch
	if (Sub == NF_takeoff) { LeanP *= 0.4; LeanR *= 0.4; }
	Pitch = FlDamp(Pitch, LeanP, 8.0, Dt);
	RollS = FlDamp(RollS, LeanR, 8.0, Dt);
	const double RollH = RollS;
	FQuat QU = FQuat(FlUp, HoverYaw) * FQuat(FVector(0, 1, 0), Pitch) * FQuat(FVector(1, 0, 0), -RollH);
	// fly line: head leads along the velocity, chest toward the ground, rolled into the turn
	FQuat QL = QU;
	if (Sp > 1.0)
	{
		FVector Vd = V / Sp;
		// owner feedback #3 (angle of attack): the body points NoseBodyK of the way toward the nose while the travel catches up with it
		if (bAttitude && NoseBodyK > 0.f)
		{
			const FVector Nose = (FlYawDir(AimYaw) * FMath::Cos(AimPitch) - FlUp * FMath::Sin(AimPitch)).GetSafeNormal();
			if (FVector::DotProduct(Nose, Vd) > 0.2) Vd = (Vd + (Nose - Vd) * FMath::Clamp(double(NoseBodyK), 0.0, 0.6)).GetSafeNormal();
		}
		FVector X0 = -FlUp - Vd * FVector::DotProduct(-FlUp, Vd);
		if (X0.SizeSquared() < 0.04) { const FVector F = FlYawDir(HoverYaw); X0 = F - Vd * FVector::DotProduct(F, Vd); }
		QL = FRotationMatrix::MakeFromZX(Vd, X0.GetSafeNormal()).ToQuat() * FQuat(FVector(0, 0, 1), -Bank);
	}
	const FQuat Want = FQuat::Slerp(QU, QL, FlyK).GetNormalized();
	S.BodyQ = FQuat::Slerp(S.BodyQ, Want, 1.0 - FMath::Exp(-12.0 * Dt)).GetNormalized();
	S.Facing = FlyK > 0.5 && HS > 2.0 ? VelYaw : HoverYaw;
	S.Bank = Bank; S.Pitch = Pitch; S.Roll = RollH; S.RollA = RollH; S.PitchA = Pitch;
	T.RootPos = S.Pos - S.BodyQ.GetUpVector() * UWebTraversalComponent::H;
	return S.BodyQ;
}

void UWHFlightComponent::StepFlight(UWebTraversalComponent& T, double Dt, FWebTravInput I)
{
	auto& S = T.S;
	T.LastInput = I;
	S.SubT += Dt; S.ModeT += Dt; S.Clock += Dt;
	SubT += Dt; FlightT += Dt;
	DashCd -= Dt; BreachCd -= Dt;
	BoomK = FMath::Max(0.0, BoomK - Dt / 0.6);
	// owner feedback #1 / #2 clocks: super cooldown, the double-tap window, the launch impulse (anim LaunchK, 0.5 s)
	SuperCd -= Dt; JumpTapT += Dt;
	LaunchK = FMath::Max(0.0, LaunchK - Dt / 0.5);
	{ // owner feedback #1: the charge runs on REAL seconds (the breach director slows the world through it)
		double Dil = 1.0;
		if (const UWorld* W = GetWorld()) if (const AWorldSettings* WS = W->GetWorldSettings()) Dil = double(WS->GetEffectiveTimeDilation());
		if (SuperState == ESuper::Charge) SuperT += Dt / FMath::Max(0.05, Dil);
		else if (SuperState != ESuper::None) SuperT += Dt;
		if (S.Mode != EWebTravMode::Air && SuperState != ESuper::None) EndSuper(true);   // (landed / grounded by another path)
	}
	// flight aim (the NOSE): picked up from the camera (yaw) and the player's current look offset (pitch) when the fly / super line starts,
	// then moved only by look input -- held pitch = hands-off level flight holds its altitude (critic r1 fl03 fix kept).
	// owner feedback #3 (flight-sim feel): in the line the look input steers the hero's nose (AimYaw too) instead of orbiting the camera; the
	// camera chases his heading (CamYawGoal, FWebTravCamera::bFlightAttitude). Stick X turns the nose at StickTurnRate. The nose leads the
	// travel by at most NoseLeadMaxDeg, so a hard mouse flick asks for the tightest turn the speed allows instead of an instant reversal.
	{
		const bool bAtt = S.Mode == EWebTravMode::Air && (I.bSwing || SuperState != ESuper::None);
		if (bAtt && !bAttitude)
		{
			AimYaw = T.Cam ? T.Cam->Yaw : S.Facing;
			AimPitch = T.Cam ? T.Cam->LookPitchOffset() : 0.0;
		}
		if (bAtt)
		{
			AimPitch = FMath::Clamp(AimPitch + I.Look.Y * double(LookPitchK), -1.35, 1.35);
			AimYaw += I.Look.X * double(LookYawK);
			if (SuperState != ESuper::Charge) AimYaw += FMath::DegreesToRadians(double(StickTurnRate)) * I.Move.X * Dt;
			if (FlHLen(S.Vel) > 8.0 && SuperState != ESuper::Charge)
			{
				const double VY = FMath::Atan2(S.Vel.Y, S.Vel.X);
				const double MaxL = FMath::DegreesToRadians(FMath::Clamp(double(NoseLeadMaxDeg), 5.0, 170.0));
				const double Lead = FlAngWrap(AimYaw - VY);
				if (FMath::Abs(Lead) > MaxL) AimYaw = VY + FMath::Sign(Lead) * MaxL;
			}
			AimYaw = FlAngWrap(AimYaw);
		}
		else AimPitch = 0.0;
		bAttitude = bAtt;
		// the heading the camera chases: the travel heading plus CamLeadK of the nose lead (the nose itself at low speed / in the charge)
		const double HSp = FlHLen(S.Vel);
		const double Kv = SuperState == ESuper::Charge ? 0.0 : FlSmooth(HSp, 4.0, 15.0);
		CamYawGoal = AimYaw - Kv * (1.0 - FMath::Clamp(double(CamLeadK), 0.0, 1.0)) * FlAngWrap(AimYaw - FMath::Atan2(S.Vel.Y, S.Vel.X));
	}
	// legacy web state never survives into flight
	if (S.Mode == EWebTravMode::Swing || S.Mode == EWebTravMode::Zip || S.Mode == EWebTravMode::Perch || S.Mode == EWebTravMode::Wall)
	{
		T.bLeaveSwingOK = true;
		T.WebRelease();
		T.SetMode(EWebTravMode::Air, NF_hover);
		T.bLeaveSwingOK = false;
		S.Kin.Type = UWebTraversalComponent::EKin::None;
		Sub = NF_hover; SubT = 0.0;
	}
	const int32 NSteps = FMath::Max(1, FMath::CeilToInt(Dt / (1.0 / 120.0) - 1e-6));
	const double Hs = Dt / NSteps;
	for (int32 K = 0; K < NSteps; ++K)
	{
		if (bBreach) StepBreach(T, Hs);
		else if (S.Mode == EWebTravMode::Ground)
		{
			const bool bLocked = S.Sub == NF_landHero ? S.LandLock > 0.0 || S.SubT < 0.45 : S.LandLock > 0.0;
			if (S.Kin.Type != UWebTraversalComponent::EKin::None) T.StepKin(Hs);
			else if (!bLocked && (I.bJumpPressed || I.bSwingPressed)) Takeoff(T);
			else
			{ // walking: the traversal's own ground step without jump / parkour / swing / wall run
				FWebTravInput G = I;
				G.bJump = G.bJumpPressed = false; G.bSwing = G.bSwingPressed = false; G.bSprint = G.bSprintPressed = false;
				G.bZip = G.bZipPressed = false; G.bQuick = G.bQuickPressed = false; G.bTrick = G.bTrickPressed = false;
				T.StepGround(Hs, G);
				if (S.Mode == EWebTravMode::Wall) { T.SetMode(EWebTravMode::Ground, NF_idle); } // never a wall run in flight mode
			}
		}
		else
		{
			StepAirSub(T, Hs, I);
			if (!bBreach) MoveAndCollide(T, Hs, I);
		}
		// safety net: never resolved inside a solid outside a breach -- carry on through it along the travel (or straight up)
		// (suite round 1: only a fast flight line can tunnel; slow flight trusts the swept / capsule collision -- the box index has solids
		//  without render collision, e.g. over Times Square, and the old net turned a hover descent into a breach through the street)
		if (!bBreach && S.Mode == EWebTravMode::Air && S.Vel.Size() >= double(BreachSpeed) && T.TravWorld.Inside(S.Pos + FVector(0, 0, 0.3)))
		{
			const FVector D = S.Vel.GetSafeNormal();
			if (!StartBreach(T, S.Pos, -D, D)) { FTravContact C; T.Collide(UWebTraversalComponent::STEP, UWebTraversalComponent::R + 0.05, C); }
		}
		if (K == 0)
		{
			I.bJumpPressed = I.bSwingPressed = I.bDropPressed = I.bZipPressed = I.bQuickPressed = I.bTrickPressed = I.bSprintPressed = false;
		}
	}
	SpeedM = S.Vel.Size();
	S.bGrounded = S.Mode == EWebTravMode::Ground;
	S.bDive = false; S.bGliding = false; S.bSky = false; S.bFlowFlip = false; S.ArmedFlip = NAME_None; S.Trick = NAME_None;
	S.Q.bActive = false;
	// flyover: people below look up (only within FlyoverMaxH of the street, and only when moving)
	FlyoverT -= Dt;
	if (S.Mode == EWebTravMode::Air && SpeedM > 15.0 && FlyoverT <= 0.0)
	{
		FlyoverT = FlyoverEvery;
		const double Street = T.TravWorld.StreetHeight(S.Pos.X, S.Pos.Y, S.Pos.Z - UWebTraversalComponent::H + 0.1);
		const double Hh = S.Pos.Z - Street;
		if (Street > -999.0 && Hh < FlyoverMaxH)
			if (UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(GetOwner()))
				FW->PushStimulus(EWHCrowdStimulus::Flyover, FVector(S.Pos.X, S.Pos.Y, Street) * 100.0, float((25.0 + Hh) * 100.0), float(FMath::Clamp(SpeedM / 80.0, 0.3, 1.0)), 2.5f, S.Vel * 100.0);
	}
	// owner feedback #1: charge progress (coil / gather / camera pull-in) and the super-speed weight (streaks, shake, FOV, blur)
	// (> 0 on every charge frame, the first one included: the breach director ends the charge slow-mo when it reads 0)
	ChargeK = SuperState == ESuper::Charge ? FMath::Max(1e-3, FlSmooth(SuperT, 0.0, FMath::Max(0.05, double(SuperChargeTime)))) : 0.0;
	SuperK = (SuperState == ESuper::Run || SuperState == ESuper::Decel) ? FlSmooth(SpeedM, double(BoostSpeed) * 0.8, double(SuperSpeed) * 0.85) : 0.0;
	FQuat Q;
	if (S.Mode == EWebTravMode::Air) Q = FlightOrient(T, Dt, I);
	else { Q = T.Orient(Dt); bHaveVelYaw = false; FlyK = 0.0; Bank = 0.0; Pitch = 0.0; HoverYaw = S.Facing; }
	T.FinalQ = Q;
	T.WriteAnim(Q);
	FWebTravAnimFlight& F = T.Anim.Flight;
	F.bActive = true;
	F.SpeedK = float(FMath::Clamp(SpeedM / FMath::Max(1.0, double(CruiseSpeed)), 0.0, 2.0));
	F.Bank = float(Bank); F.Pitch = float(Pitch + FlyK * 0.5 * PI);
	F.Stick = StickBody; F.Climb = float(Climb); F.BoomK = float(BoomK); F.bRightFist = bRightFist;
	F.FlightT = float(S.Mode == EWebTravMode::Air ? FlightT : 0.0);
	WallT -= Dt;
	F.WallSide = WallT > 0.0 ? float(WallSideV) : 0.f;
	F.WallDist = WallT > 0.0 ? float(WallDistV) : 99.f;
	// owner feedback #1 / #2: the anim's coil / launch / super-stretch / dive inputs (see FWebTravAnimFlight and owner1_fx_NOTES.md)
	F.ChargeK = float(ChargeK); F.SuperK = float(SuperK); F.LaunchK = float(LaunchK);
	F.DiveK = (bDiveDrop && Sub == NF_slam) ? float(FMath::Clamp(-S.Vel.Z / 120.0, 0.0, 1.0)) : 0.f;
	if (S.Mode != EWebTravMode::Air) FlightT = 0.0;
	// strands (none are attached in flight; any legacy one fades out)
	for (FWebTravStrand& St : T.Strands)
	{
		if (!St.bActive) continue;
		if (St.ReleaseT < 0.f) St.ReleaseT = 0.f;
		St.ReleaseT += float(Dt); if (St.ReleaseT > 0.42f) St.bActive = false;
	}
}
