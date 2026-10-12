// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Combat/WHCombatSpidey.h"
#include "Combat/WHCombatDirector.h"
#include "Combat/WHCombatHero.h"
#include "Combat/WHCombatAnim.h"
#include "Combat/WHEnemy.h"
#include "Combat/WHCombatUtil.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Traversal/WebTraversalComponent.h"

using namespace WHCmb;

// Ground combo (spidey.js MOVES). Side: where the blow lands on the enemy (+1 his left, -1 his right) -> his stumble direction
static const TMap<FName, FWHMoveSpec>& Moves()
{
	static const TMap<FName, FWHMoveSpec> MV = {
		{ "jab",        { "punch1",    0.0,  0.20, 1.3,  0.95, 9,  "light",  0 } },
		{ "cross",      { "punch2",    0.0,  0.23, 1.3,  0.95, 10, "light",  1 } },
		{ "hook",       { "punch3",    0.0,  0.30, 1.35, 1.0,  11, "light", -1 } },
		{ "kick",       { "kick",      0.0,  0.30, 1.4,  1.1,  11, "light",  1 } },
		{ "roundhouse", { "kick",      0.0,  0.30, 1.15, 1.1,  16, "ender",  1 } },
		{ "riser",      { "uppercut",  0.0,  0.33, 1.2,  1.0,  17, "ender",  0 } },   // rising uppercut
		{ "flyKick",    { "webStrike", 0.36, 0.57, 1.15, 1.05, 18, "ender",  0 } },   // leaping kick, lands
	};
	return MV;
}
static const TArray<TArray<FName>>& Pools()
{
	static const TArray<TArray<FName>> P = { { "jab", "cross" }, { "cross", "hook" }, { "hook", "kick", "jab" }, { "roundhouse", "riser", "flyKick" } };
	return P;
}
struct FAirSeg { double From, Until, Hit, Dmg; FName Kind; };
static const FAirSeg AIR[3] = { { 0.0, 0.22, 0.13, 9, "air" }, { 0.2, 0.42, 0.27, 9, "air" }, { 0.42, 0.8, 0.60, 14, "slam" } };
static const double DASH_MAX = 5.2;   // gaps up to this run in (dash), beyond it a flying kick
static const double LUNGE = 0.3;      // the last bit of a gap is a step into the blow, taken during the wind-up
static const double NEAR = 9;         // enemies this close: fight-ready stance on the ground, C / Ctrl = dodge
static const double KIN_MAX = 1.2;    // a scripted segment moves at most this far per frame (never a teleport)

FWHSpidey::FWHSpidey(AWHCombatDirector* InC, AWHCombatHero* InHero) : C(InC), Hero(InHero)
{
	if (Hero && Hero->GetTraversal()) { Pos = Hero->GetTraversal()->PosM(); VisYaw = YawGoal = Hero->GetTraversal()->Facing(); }
}

UWHCombatHeroAnim* FWHSpidey::Anim() const
{
	return Hero && Hero->GetMesh() ? Cast<UWHCombatHeroAnim>(Hero->GetMesh()->GetAnimInstance()) : nullptr;
}

int32 FWHSpidey::PlayClip(FName Name, const FWHClipOpts& O)
{
	UWHCombatHeroAnim* A = Anim();
	UAnimSequence* S = A ? A->CombatClip(Name) : nullptr;
	if (!S) { C->LogEvent(FString::Printf(TEXT("missing hero clip %s"), *Name.ToString())); return 0; }
	return Layer.Play(Name, S, O);
}

double FWHSpidey::GroundZ(double X, double Y, double FromZ) const { return C->GroundHeight(X, Y, FromZ); }

bool FWHSpidey::Invuln() const
{
	return C->Time < InvulnUntil || (M.Name == "dodge" && M.T < 0.5) || M.Name == "finisher" || M.Name == "down";
}

bool FWHSpidey::OnGround() const
{
	return !bKin && Hero->GetTraversal()->Mode() == EWebTravMode::Ground;
}

double FWHSpidey::Nearest(double MaxD) const
{
	double D = 1e9;
	for (AWHEnemy* E : C->Enemies) if (E && E->Alive() && E->State != EWHEnemyState::Out) D = FMath::Min(D, HDist(E->Pos, Pos));
	return D <= MaxD ? D : -1;
}

FVector FWHSpidey::InputDir() const { return C->StickDir; }

void FWHSpidey::Turn(double Dt, double Rate, double MaxW)
{
	if (!bYawGoal) return;
	const double D = AngWrap(YawGoal - VisYaw), Step = D * (1.0 - FMath::Exp(-Rate * Dt));
	VisYaw = AngWrap(VisYaw + FMath::Clamp(Step, -MaxW * Dt, MaxW * Dt));
}

void FWHSpidey::KinTo(const FVector& In)
{
	FVector P = In;
	const double D = FVector::Dist(P, Pos);
	if (D > KIN_MAX) P = Pos + (P - Pos) * (KIN_MAX / D);
	Pos = P; bKin = true;
}

void FWHSpidey::GroundXY(double X, double Y)
{
	Pos.X = X; Pos.Y = Y;
	Pos.Z = GroundZ(X, Y, Pos.Z - H + 0.6) + H;
	bKin = false;
}

void FWHSpidey::Start(FName Name)
{
	const bool bHadGoal = bYawGoal; const double G = YawGoal;
	const int32 Tr = M.Track;
	M = FWHMove(); M.Name = Name; M.T = 0; M.bHitDone = false;
	(void)Tr; bYawGoal = bHadGoal; YawGoal = G;
	bOwned = true;
}

void FWHSpidey::Free(double Fade, const FVector* V)
{
	const double Fz = GroundZ(Pos.X, Pos.Y, Pos.Z);
	const bool bAir = bKin || Hero->GetTraversal()->Mode() != EWebTravMode::Ground || (Pos.Z - H) - Fz > 0.35;
	M = FWHMove(); M.Name = "free";
	Layer.Stop(Fade);
	StanceUid = 0;
	if (bAir)
	{
		bAirEnd = true;
		AirEndV = V ? *V : FVector(Vel.X * 0.35, Vel.Y * 0.35, FMath::Min(Vel.Z * 0.35, 1.0));
	}
	bKin = false;
}

// ------------------------------------------------------------------------------------------------ strike (dash in, then strike)
FName FWHSpidey::ChooseMove(int32 Step, AWHEnemy* T)
{
	const double D = HDist(Feet(), T->Pos);
	TArray<FName> Pool;
	for (const FName& K : Pools()[Step])
	{
		if (K == LastMove) continue;
		if (K == "flyKick" && D < 1.6) continue;
		if (D > 2.2 && Step < 3 && Moves()[K].Clip == "kick") continue;
		Pool.Add(K);
	}
	return Pool.Num() ? Pool[Rng.RandRange(0, Pool.Num() - 1)] : Pools()[Step][0];
}

double FWHSpidey::DashDist(double U, double D, double T, double V0, double V1)
{
	const double U2 = U * U, U3 = U2 * U;
	return (U3 - 2 * U2 + U) * V0 * T + (-2 * U3 + 3 * U2) * D + (U3 - U2) * V1 * T;
}

void FWHSpidey::StrikeWith(AWHEnemy* T, const FWHMoveSpec& S0, bool bEnder, bool bNoLong, FName Name, bool bNoMove)
{
	const FVector P0 = Feet();
	const double Gap = FMath::Max(0.0, HDist(P0, T->Pos) - S0.Reach);
	const FVector Dir0 = FlatNorm(P0 - T->Pos);
	FWHMoveSpec S = S0;
	if (bEnder) S.Kind = "ender";
	const bool bCounter = C->Time < CounterUntil;
	if (bCounter) { S.Dmg *= 1.6; if (S.Kind == "light") S.Kind = "ender"; CounterUntil = 0; }
	if (Gap > DASH_MAX && !bNoLong)
	{ // too far to run in: leaping flying kick (airborne the whole way, no foot skate)
		Start(Name);
		M.Target = T; M.Clip = "webStrike"; M.From = 0.32; M.Hit = 0.57; M.Until = -1;
		M.Fly = Clamp(Gap / 17, 0.24, 0.5); M.Ts = (M.Hit - M.From) / M.Fly;
		M.Kind = S.Kind; M.Dmg = S.Dmg; M.Side = S.Side; M.P0 = P0; M.Dir0 = Dir0; M.Reach = S.Reach; M.bLong = true;
		M.ClipAt = 0; M.bClipOn = true; M.DashDur = M.Fly; M.PressT = C->Time;
		FWHClipOpts O; O.From = M.From; O.Ts = M.Ts; O.Fade = 0.08;
		M.Track = PlayClip(M.Clip, O);
		LastResult = FString::Printf(TEXT("%s flyingKick->%s gap %.1f"), *Name.ToString(), *T->Tag(), Gap);
	}
	else
	{ // run in on the loco cycle until LUNGE short of contact, THEN the blow (its wind-up plays while he steps into it)
		const double Windup = (S.Hit - S.From) / S.Ts;
		const FVector TV = Hero->GetTraversal()->VelM();
		const FVector HV = (TV.X * TV.X + TV.Y * TV.Y > Vel.X * Vel.X + Vel.Y * Vel.Y) ? TV : Vel;
		const double V0 = FMath::Max(0.0, FMath::Sqrt(HV.X * HV.X + HV.Y * HV.Y) * FMath::Cos(AngWrap(FMath::Atan2(HV.Y, HV.X) - YawTo(P0, T->Pos))));
		const double RunD = FMath::Max(0.0, Gap - LUNGE);
		const double RunT = RunD > 0.05 ? Clamp(0.06 + RunD / 12.5 - FMath::Min(0.1, V0 * 0.01), 0.1, 0.44) : 0.0;
		Start(Name);
		M.Target = T; M.Clip = S.Clip; M.From = S.From; M.Until = S.Until; M.Hit = S.Hit; M.Ts = S.Ts; M.Kind = S.Kind; M.Dmg = S.Dmg; M.Side = S.Side;
		M.P0 = P0; M.Dir0 = Dir0; M.Reach = S.Reach; M.bLong = false;
		M.DashDur = RunT + Windup; M.RunT = RunT; M.RunD = RunD; M.Windup = Windup; M.ClipAt = FMath::Max(0.0, RunT - 0.05);
		M.bClipOn = false; M.V0 = V0; M.D0 = FMath::Max(0.01, Gap); M.PressT = C->Time; M.bNoMove = bNoMove;
		if (M.ClipAt <= 0) PlayStrikeClip();
		LastResult = FString::Printf(TEXT("%s %s->%s gap %.1f run %.2fs"), *Name.ToString(), *S.Clip.ToString(), *T->Tag(), Gap, RunT);
	}
	if (bCounter) LastResult += TEXT(" COUNTER");
	Face(YawTo(P0, T->Pos));
	Target = T; LastAttackT = C->Time;
}

void FWHSpidey::PlayStrikeClip()
{
	M.bClipOn = true;
	const double Windup = (M.Hit - M.From) / M.Ts;
	FWHClipOpts O; O.From = M.From; O.Until = M.Until; O.Ts = M.Ts; O.Fade = Clamp(Windup * 0.7, 0.07, 0.12);
	M.Track = PlayClip(M.Clip, O);
}

void FWHSpidey::Strike(AWHEnemy* T, int32 Step)
{
	const FName K = ChooseMove(Step, T); LastMove = K;
	StrikeWith(T, Moves()[K]);
	LastResult = K.ToString() + TEXT(": ") + LastResult;
}

void FWHSpidey::Launcher(AWHEnemy* T)
{
	FWHMoveSpec S; S.Clip = "uppercut"; S.Hit = 0.33; S.Ts = 1.25; S.Reach = 1.0; S.Dmg = 10; S.Kind = "launch"; S.Side = 0;
	StrikeWith(T, S, false, true, "launch");
	M.bRise = false;
}

void FWHSpidey::AirStrike(AWHEnemy* T, int32 Seg, bool bForceSlam)
{
	const int32 Sg = bForceSlam ? 2 : Seg;
	const FAirSeg& A = AIR[Sg];
	Start("airStrike");
	M.Target = T; M.Seg = Sg; M.AFrom = A.From; M.AUntil = A.Until; M.AHit = A.Hit; M.ADmg = A.Dmg; M.AKind = A.Kind; M.Hit = A.Hit; M.Ts = 1.2;
	FWHClipOpts O; O.From = A.From; O.Until = A.Until; O.Ts = 1.2; O.Fade = 0.08;
	M.Track = PlayClip("airCombo", O);
	Target = T; LastAttackT = C->Time;
	LastResult = FString::Printf(TEXT("airStrike seg %d -> %s"), Sg, *T->Tag());
}

double FWHSpidey::ArcOver(const FVector& P0, const FVector& To, double Base) const
{
	double Top = 0;
	for (int32 i = 1; i < 8; ++i)
	{
		const double K = i / 8.0, X = Lerp(P0.X, To.X, K), Y = Lerp(P0.Y, To.Y, K), Z = Lerp(P0.Z - H, To.Z, K);
		const double G = GroundZ(X, Y, Z + 2.2) - Z; if (G > 0.25 && G < 2.3) Top = FMath::Max(Top, G + 0.5);
	}
	return FMath::Max(Base, Top);
}

void FWHSpidey::DiveStrike(AWHEnemy* T)
{
	const FVector P0 = Pos;
	Start("dive");
	M.Target = T; M.P0 = P0; M.Hit = 0.57; M.From = 0.3; M.Arrive = Clamp(FVector::Dist(P0, T->Pos) / 22, 0.2, 0.6); M.Arc = ArcOver(P0, T->Pos, 0.4);
	M.Ts = (0.57 - 0.3) / M.Arrive;
	FWHClipOpts O; O.From = 0.3; O.Ts = M.Ts; O.Fade = 0.1;
	M.Track = PlayClip("webStrike", O);
	Face(YawTo(P0, T->Pos)); Target = T;
	LastResult = TEXT("dive -> ") + T->Tag();
}

void FWHSpidey::WebStrike(AWHEnemy* T)
{
	const FVector P0 = Pos;
	const double D = HDist(P0, T->Pos);
	Start("webStrike");
	M.Target = T; M.P0 = P0; M.Hit = 0.57; M.Fly = Clamp(D / 24, 0.2, 0.55); M.bPulled = false;
	M.Ts2 = (0.57 - 0.3) / M.Fly;
	FWHClipOpts O; O.From = 0.05; O.Until = 0.3; O.Ts = 1.4; O.Fade = 0.09;
	M.Track = PlayClip("webStrike", O);
	Face(YawTo(P0, T->Pos)); Target = T;
	TWeakObjectPtr<AWHCombatHero> WH = Hero; TWeakObjectPtr<AWHEnemy> WT = T;
	C->Fx.Strand([WH]() { return WH.IsValid() ? WH->HandM(true) : FVector::ZeroVector; },
		[WT, WH]() { return WT.IsValid() ? WT->Chest() : (WH.IsValid() ? WH->HandM(true) : FVector::ZeroVector); }, 0.18 + M.Fly, 0.05, 0.1);
	LastResult = FString::Printf(TEXT("webStrike -> %s %.1f m"), *T->Tag(), D);
}

void FWHSpidey::YankStrike(AWHEnemy* T)
{
	TWeakObjectPtr<AWHCombatHero> WH = Hero; TWeakObjectPtr<AWHEnemy> WT = T;
	C->Fx.Strand([WH]() { return WH.IsValid() ? WH->HandM(true) : FVector::ZeroVector; },
		[WT, WH]() { return WT.IsValid() ? WT->Chest() : (WH.IsValid() ? WH->HandM(true) : FVector::ZeroVector); }, 0.3, 0.02, 0.08);
	LastMove = "roundhouse";
	const FWHMoveSpec& S = Moves()["roundhouse"];
	if (T->Type == EWHEnemyType::Brute && !(T->Stun > 0)) { StrikeWith(T, S, true); LastResult = TEXT("yank(brute: steps in) ") + LastResult; return; }
	const FVector P0 = Feet();
	const FVector D = FlatNorm(T->Pos - P0, YawDir(VisYaw));
	const double Windup = S.Hit / S.Ts, Pull = FMath::Max(0.24, Windup + 0.02);
	T->Yank(P0 + D * S.Reach, Pull);
	StrikeWith(T, S, true, false, "strike", true);
	M.DashDur = Pull; M.ClipAt = FMath::Max(0.0, Pull - Windup); M.RunT = 0;
	if (M.ClipAt > 0) Layer.Stop(0.1); else if (!M.bClipOn) PlayStrikeClip();
	LastResult = TEXT("yank ") + LastResult;
}

// dodge: back flip (face away from the move) or side flip (the move on his left), whichever needs the smaller turn
void FWHSpidey::Dodge(const FVector& ThreatDir, bool bPerfect, const FVector& InDir)
{
	FVector Mv;
	if (InDir.SizeSquared() > 0.1) Mv = FlatNorm(InDir);
	else Mv = ThreatDir.SizeSquared() > 0 ? -ThreatDir : -YawDir(VisYaw);
	const double YawBack = FMath::Atan2(-Mv.Y, -Mv.X);
	const double YawSide = FMath::Atan2(Mv.X, -Mv.Y);   // UE: his left = (sin y, -cos y)
	const double Tb = FMath::Abs(AngWrap(YawBack - VisYaw)), Tsd = FMath::Abs(AngWrap(YawSide - VisYaw));
	const bool bSide = InDir.SizeSquared() > 0.1 ? Tsd + 0.25 < Tb : false;
	const FVector F = Feet();
	Start("dodge");
	M.Move = Mv; M.bSide = bSide; M.Dist = bSide ? 3.2 : 3.4; M.P0 = F; M.bPerfect = bPerfect; M.Go = bSide ? 0.05 : 0.1;
	FWHClipOpts O; O.Ts = bSide ? 1.35 : 1.45; O.Fade = 0.07;
	M.Track = PlayClip(bSide ? "dodgeSide" : "dodge", O);
	Face(bSide ? YawSide : YawBack);
	InvulnUntil = C->Time + 0.55;
	if (bPerfect) CounterUntil = C->Time + 1.4;
	LastResult = FString::Printf(TEXT("dodge %s%s"), bSide ? TEXT("side") : TEXT("back"), bPerfect ? TEXT(" PERFECT") : TEXT(""));
}

void FWHSpidey::WebShoot(AWHEnemy* T)
{
	FWHClipOpts O; O.Ts = 1.5; O.Fade = 0.08; O.bUpper = true; O.Id = "shoot"; O.bHold = false;
	PlayClip("webShootR", O);
	C->FireWebLater(T, 0.09);
	LastResult = TEXT("webShoot -> ") + T->Tag();
}

void FWHSpidey::Finisher(AWHEnemy* T)
{
	const FVector P0 = Feet();
	Start("finisher");
	M.Target = T; M.P0 = P0; M.Dir0 = FlatNorm(P0 - T->Pos); M.Hit = 0.57; M.Reach = 1.15; M.Arrive = 0.4;
	FWHClipOpts O; O.Ts = 1; O.Fade = 0.1;
	M.Track = PlayClip("finisher", O);
	Face(YawTo(P0, T->Pos)); Target = T;
	T->Set(EWHEnemyState::Stagger); T->StagT = 2; T->Play("thugStumbleBack", 0.1, 0.35, 1);
	C->ReleaseToken(T); C->ClearThreats(T);
	C->Cine(T, 1.45, "finisher");
	LastResult = TEXT("finisher -> ") + T->Tag();
}

void FWHSpidey::TakeHit(AWHEnemy* E, double Dmg, bool bHeavy)
{
	if (M.Name == "free") { Pos = Hero->GetTraversal()->PosM(); VisYaw = Hero->GetTraversal()->Facing(); }
	Hp = FMath::Max(0.0, Hp - Dmg);
	if (!OnGround() && Hp > 0) return;
	// scripted capture ("hero_armor"): a committed launcher is not knocked out of its rise, and heavy blows stagger instead of knocking down
	if (C->bHeroArmor && Hp > 0 && M.Name == "launch") return;
	if (C->bHeroArmor && Hp > 0) bHeavy = false;
	const FVector D = FlatNorm(Pos - E->Pos);
	bKin = false; ComboStep = 0;
	const FVector F = Feet();
	if (bHeavy || Hp <= 0)
	{
		Start("down"); M.HDir = D; M.Dist = 2.2; M.P0 = F; M.bDead = Hp <= 0;
		FWHClipOpts O; O.Ts = 1.15; O.Fade = 0.07; M.Track = PlayClip("knockdown", O);
		InvulnUntil = C->Time + 2.4;
	}
	else
	{
		Start("hit"); M.HDir = D; M.Dist = 0.35; M.P0 = F;
		FWHClipOpts O; O.Ts = 1.25; O.Fade = 0.06; M.Track = PlayClip("hitReact", O);
		InvulnUntil = C->Time + 0.45;
	}
	Face(FMath::Atan2(-D.Y, -D.X));
}

// ------------------------------------------------------------------------------------------------ per-frame motion
void FWHSpidey::Motion(double Dt)
{
	M.T += Dt;
	FWHClipTrack* Tr = Track(); if (!Tr) Tr = Layer.Top();
	AWHEnemy* T = M.Target.Get();
	auto Contact = [](AWHEnemy* E, const FVector& Dir0, double Reach) { return E->Pos + Dir0 * Reach; };
	const FName N = M.Name;
	if (N == "strike" || N == "launch")
	{
		if (!T || (!T->Alive() && !M.bHitDone)) { Free(0.2); return; }
		if (M.bLong)
		{ // flying kick: airborne arc onto the contact point
			const double U = Clamp(M.T / M.Fly, 0, 1), E = 1 - (1 - U) * (1 - U);
			if (!M.bHitDone)
			{
				const FVector Cp = Contact(T, M.Dir0, M.Reach);
				const double X = Lerp(M.P0.X, Cp.X, E), Y = Lerp(M.P0.Y, Cp.Y, E);
				const double Z = Lerp(M.P0.Z, T->Pos.Z, E) + H + FMath::Sin(PI * U) * 0.55;
				if (U < 1) KinTo(FVector(X, Y, Z)); else GroundXY(X, Y);
				YawGoal = YawTo(Feet(), T->Pos); bYawGoal = true;
			}
		}
		else if (!M.bHitDone && T->Alive() && !M.bNoMove && M.T <= M.DashDur + 0.02)
		{ // run in, then step into the blow
			const FVector Cp = Contact(T, M.Dir0, M.Reach);
			double D;
			if (M.T < M.RunT) D = DashDist(Clamp(M.T / M.RunT, 0, 1), M.RunD, M.RunT, M.V0, 2.2);
			else { const double U = Clamp((M.T - M.RunT) / FMath::Max(1e-3, M.Windup), 0, 1); D = M.RunD + (M.D0 - M.RunD) * (1 - (1 - U) * (1 - U)); }
			const double K = Clamp(D / M.D0, 0, 1.02);
			GroundXY(Lerp(M.P0.X, Cp.X, K), Lerp(M.P0.Y, Cp.Y, K));
			YawGoal = YawTo(Feet(), T->Pos); bYawGoal = true;
		}
		else if (M.bNoMove && !M.bHitDone && T->Alive()) { YawGoal = YawTo(Feet(), T->Pos); bYawGoal = true; }
		if (!M.bClipOn && M.T >= M.ClipAt) PlayStrikeClip();
		FWHClipTrack* Trk = M.bClipOn ? Track() : nullptr;
		const double ClipT = Trk ? Trk->T : -1;
		if (!M.bHitDone && M.bClipOn && ClipT >= M.Hit - 0.001 && M.T >= M.DashDur - 0.03)
		{
			M.bHitDone = true;
			FWHPlayerHit PH; PH.Kind = M.Kind; PH.Dmg = M.Dmg; PH.Heavy = M.Kind != "light" ? 0.6 : 0.15; PH.Side = M.Side;
			C->PlayerHit(T, PH);
			if (N == "launch" && T->State == EWHEnemyState::Air) { M.bRise = true; M.RiseT = 0; M.RiseFrom = Pos; }
			if (M.bLong) bKin = false;
		}
		if (N == "launch" && M.bRise)
		{
			M.RiseT += Dt;
			const double K = Smooth(M.RiseT / 0.38);
			FVector Want = T->Pos + M.Dir0 * 1.0; Want.Z = T->Pos.Z + H + 0.1;
			KinTo(M.RiseFrom + (Want - M.RiseFrom) * K);
			if (M.RiseT > 0.38)
			{
				Start("air"); M.Target = T; M.IdleT = 0;
				FWHClipOpts O; O.From = 0; O.Until = 0.02; O.Ts = 0.2; O.Fade = 0.2; M.Track = PlayClip("airCombo", O);
				bKin = true;
			}
			return;
		}
		if (Trk && (ClipT >= Trk->Until - 0.02 || (M.bHitDone && N == "strike" && ClipT >= M.Hit + 0.3))) Free(M.bLong ? 0.3 : 0.25);
		return;
	}
	if (N == "finisher")
	{
		const double U = Clamp(M.T / M.Arrive, 0, 1), E = 1 - (1 - U) * (1 - U);
		if (T && T->Alive() && M.T <= M.Arrive + 0.02)
		{
			const FVector Cp = Contact(T, M.Dir0, M.Reach);
			GroundXY(Lerp(M.P0.X, Cp.X, E), Lerp(M.P0.Y, Cp.Y, E));
			YawGoal = YawTo(Feet(), T->Pos); bYawGoal = true;
		}
		const double ClipT = Tr ? Tr->T : 0;
		if (!M.bHitDone && ClipT >= M.Hit - 0.001 && M.T > 0.2 && T) { M.bHitDone = true; FWHPlayerHit PH; PH.Kind = "finisher"; PH.Dmg = 999; C->PlayerHit(T, PH); }
		if (!Tr || ClipT >= Tr->Until - 0.02) Free(0.25);
		return;
	}
	if (N == "air" || N == "airStrike")
	{
		if (!T || !T->Alive() || T->State != EWHEnemyState::Air) { const FVector V(0, 0, -1); Free(0.3, &V); return; }
		const FVector Dd = FlatNorm(Pos - T->Pos, -YawDir(VisYaw));
		FVector Want = T->Pos + Dd * 0.95; Want.Z = T->Pos.Z + H + 0.05;
		KinTo(Pos + (Want - Pos) * (1 - FMath::Exp(-14 * Dt)));
		YawGoal = YawTo(Feet(), T->Pos); bYawGoal = true;
		if (N == "air")
		{
			M.IdleT += Dt;
			if (M.IdleT > 0.9) { T->Juggle = FMath::Min(T->Juggle, 0.0); const FVector V(0, 0, -1); Free(0.3, &V); }
			return;
		}
		const double ClipT = Tr ? Tr->T : 0;
		if (!M.bHitDone && ClipT >= M.AHit)
		{
			M.bHitDone = true;
			const bool bSlam = M.AKind == "slam";
			FWHPlayerHit PH; PH.Kind = bSlam ? FName("slam") : FName("air"); PH.Dmg = M.ADmg; PH.Heavy = bSlam ? 0.9 : 0.25;
			C->PlayerHit(T, PH);
			if (bSlam) { const FVector From = Pos; Start("slamDown"); M.SlamFrom = From; return; }
		}
		if (M.bHitDone && ClipT >= M.AUntil - 0.01)
		{
			const int32 Tk = M.Track, Sg = M.Seg;
			Start("air"); M.Target = T; M.IdleT = 0; M.Seg = Sg; M.Track = Tk;
		}
		return;
	}
	if (N == "slamDown")
	{ // dives after the slammed enemy, lands in a superhero landing (finisher clip's landing)
		const double G = GroundZ(Pos.X, Pos.Y, Pos.Z);
		const double K = M.T / 0.22, E = K * K;
		KinTo(M.SlamFrom + (FVector(M.SlamFrom.X, M.SlamFrom.Y, G + H) - M.SlamFrom) * FMath::Min(1.0, E));
		if (M.T >= 0.22)
		{
			Pos.Z = G + H; bKin = false;
			C->GroundPound(FVector(Pos.X, Pos.Y, G));
			Start("landing");
			FWHClipOpts O; O.From = 1.0; O.Ts = 1.3; O.Fade = 0.06; M.Track = PlayClip("finisher", O);
		}
		return;
	}
	if (N == "landing") { if (M.T > 0.4 / 1.3 + 0.1) Free(0.25); return; }
	if (N == "dive")
	{
		const double U = Clamp(M.T / M.Arrive, 0, 1), E = U * U * (3 - 2 * U);
		if (T && T->Alive() && !M.bHitDone)
		{
			const FVector D0 = FlatNorm(M.P0 - T->Pos);
			FVector Cp = T->Pos + D0 * 1.05; Cp.Z = T->Pos.Z + H;
			FVector P = M.P0 + (Cp - M.P0) * E; P.Z = Lerp(M.P0.Z, Cp.Z, E) + FMath::Sin(PI * U) * M.Arc;
			KinTo(P);
			YawGoal = YawTo(Feet(), T->Pos); bYawGoal = true;
		}
		if (!M.bHitDone && U >= 1 && T)
		{
			M.bHitDone = true; bKin = false;
			FWHPlayerHit PH; PH.Kind = "strike"; PH.Dmg = 16; PH.Heavy = 0.7; PH.Reach = 1.6; C->PlayerHit(T, PH);
			FVector B = -YawDir(VisYaw) * 2.5; B.Z = 3.2;
			Free(0.3, &B); return;
		}
		if (M.T > M.Arrive + 0.3) Free(0.3);
		return;
	}
	if (N == "webStrike")
	{
		if (!T) { Free(0.3); return; }
		if (!M.bPulled && M.T >= 0.18)
		{
			M.bPulled = true; M.FlyT0 = M.T; M.P0 = Pos; M.Arc = ArcOver(M.P0, T->Pos, 0.9);
			FWHClipOpts O; O.From = 0.3; O.Ts = M.Ts2; O.Fade = 0.08; M.Track = PlayClip("webStrike", O);
		}
		if (M.bPulled && T->Alive() && !M.bHitDone)
		{
			const double U = Clamp((M.T - M.FlyT0) / M.Fly, 0, 1), E = U * U * (3 - 2 * U);
			const FVector D0 = FlatNorm(M.P0 - T->Pos);
			FVector Cp = T->Pos + D0 * 1.0; Cp.Z = T->Pos.Z + H + 0.1;
			FVector P = M.P0 + (Cp - M.P0) * E; P.Z = Lerp(M.P0.Z, Cp.Z, E) + FMath::Sin(PI * U) * M.Arc;
			KinTo(P);
			YawGoal = YawTo(Feet(), T->Pos); bYawGoal = true;
			if (U >= 1)
			{
				M.bHitDone = true;
				FWHPlayerHit PH; PH.Kind = "strike"; PH.Dmg = 20; PH.Heavy = 0.8; PH.bStunBrute = true; PH.Reach = 1.6; C->PlayerHit(T, PH);
				// recovery: the clip's own landing (0.57 -> 0.93 s) while he rebounds ~0.8 m off the chest and drops onto his feet
				M.bRecover = true; M.Recover = M.T; M.R0 = Pos; M.RDir = D0;
				const double G = GroundZ(Pos.X + D0.X * 0.8, Pos.Y + D0.Y * 0.8, Pos.Z - H + 0.3);
				M.Ry = FMath::Min(G + H, Pos.Z); M.RDur = (0.93 - 0.57) / 1.45;
				if (FWHClipTrack* K = Track()) K->Ts = 1.45;
			}
		}
		if (M.bHitDone && M.bRecover)
		{
			const double U = Clamp((M.T - M.Recover) / M.RDur, 0, 1), E = 1 - (1 - U) * (1 - U);
			FVector P = M.R0 + M.RDir * 0.8 * E; P.Z = Lerp(M.R0.Z, M.Ry, U * U);
			if (M.Ry > M.R0.Z - 2) { if (U < 1) KinTo(P); else GroundXY(P.X, P.Y); }
			else if (U > 0.2) { const FVector V(M.RDir.X * 2, M.RDir.Y * 2, 1); Free(0.3, &V); return; }
			if (U >= 1 && M.Name == "webStrike") { Free(0.22); return; }
		}
		if (!T->Alive() && !M.bHitDone && M.T > 0.2) Free(0.3);
		return;
	}
	if (N == "whiff") { if (M.T > 0.3) Free(0.25); return; }
	if (N == "dodge")
	{
		const double U = Clamp((M.T - M.Go) / 0.48, 0, 1), E = 1 - FMath::Pow(1 - U, 2.2);
		GroundXY(M.P0.X + M.Move.X * M.Dist * E, M.P0.Y + M.Move.Y * M.Dist * E);
		if (M.T > (M.bSide ? 0.6 : 0.7)) Free(0.28);
		return;
	}
	if (N == "hit" || N == "down")
	{
		const double Dur = N == "hit" ? 0.3 : 0.5;
		const double U = Clamp(M.T / Dur, 0, 1), E = 1 - (1 - U) * (1 - U);
		GroundXY(M.P0.X + M.HDir.X * M.Dist * E, M.P0.Y + M.HDir.Y * M.Dist * E);
		if (N == "hit" && M.T > 0.38) { Free(0.22); return; }
		if (N == "down")
		{
			const double Up = M.bDead ? 2.2 : 1.0;
			if (!M.bUp && M.T > Up)
			{
				M.bUp = true; FWHClipOpts O; O.Ts = 1.2; O.Fade = 0.12; M.Track = PlayClip("getUp", O);
				if (M.bDead || Hp <= 0) { Hp = MaxHp; C->Banner(TEXT("DEFEATED")); }
			}
			if (M.bUp && M.T > Up + 0.8) Free(0.25);
		}
		return;
	}
	Free(0.25); // unknown / not ported (throw)
}

// ------------------------------------------------------------------------------------------------ input -> moves
bool FWHSpidey::AttackInput(bool bHold)
{
	const FVector D = InputDir();
	const FVector* DP = D.SizeSquared() > 0.04 ? &D : nullptr;
	const EWebTravMode Md = Hero->GetTraversal()->Mode();
	bAirborne = !OnGround() && Md != EWebTravMode::Ground;
	if (M.Name == "air" || M.Name == "airStrike")
	{
		AWHEnemy* T = M.Target.Get();
		if (T && T->Alive()) AirStrike(T, bHold ? 2 : ((M.Seg < 0 ? -1 : M.Seg) + 1) % 3, bHold);
		return true;
	}
	if (Md == EWebTravMode::Air || (Md == EWebTravMode::Ground && bKin))
	{
		AWHEnemy* T = C->PickTarget(DP, 14, Feet());
		if (T && Md == EWebTravMode::Air) { DiveStrike(T); return true; }
		return false;
	}
	if (Md != EWebTravMode::Ground) return false;
	AWHEnemy* T = C->PickTarget(DP, 8.5, Feet());
	if (!T)
	{ // whiff in place (still readable)
		const FWHMoveSpec& S = Moves()[Pools()[ComboStep % 3][0]]; ComboStep = (ComboStep + 1) % 4; LastAttackT = C->Time;
		Start("whiff"); FWHClipOpts O; O.Ts = S.Ts; O.Fade = 0.1; M.Track = PlayClip(S.Clip, O);
		LastResult = TEXT("whiff (no target)");
		return true;
	}
	if (bHold && (T->Type != EWHEnemyType::Brute || T->Stun > 0) && HDist(Feet(), T->Pos) < 4.5) { Launcher(T); ComboStep = 0; return true; }
	if (C->Time - LastAttackT > 0.95) ComboStep = 0;
	Strike(T, ComboStep % 4);
	ComboStep = (ComboStep + 1) % 4;
	return true;
}

bool FWHSpidey::DoAction(FName K)
{
	const FVector D = InputDir();
	const FVector* DP = D.SizeSquared() > 0.04 ? &D : nullptr;
	const bool bAir = Hero->GetTraversal()->Mode() != EWebTravMode::Ground || M.Name == "air" || M.Name == "airStrike";
	if (K == "attack") return AttackInput(false);
	if (K == "web")
	{
		AWHEnemy* T = (M.Name == "air" || M.Name == "airStrike") ? M.Target.Get() : nullptr;
		if (!T) T = C->PickTarget(DP, 26, Feet(), 0, 1.25);
		if (!T) T = C->PickTarget(DP, 26, Feet());
		if (T) WebShoot(T); else { C->Deny(TEXT("No target")); LastResult = TEXT("web: no target"); }
		return true;
	}
	if (K == "strike")
	{
		AWHEnemy* Far = C->PickTarget(DP, 22, Feet(), 3.5, 1.95);
		if (Far) { WebStrike(Far); return true; }
		AWHEnemy* Nr = !bAir ? C->PickTarget(DP, 3.5, Feet()) : nullptr;
		if (Nr) { YankStrike(Nr); return true; }
		LastResult = TEXT("strike: nobody (E would stay the web-zip)");
		return false;
	}
	if (K == "finisher")
	{
		AWHEnemy* T = C->PickTarget(DP, 10, Feet());
		const double Cost = T && T->Type == EWHEnemyType::Brute ? 2 : 1;
		if (T && !bAir && Focus >= Cost) { Focus -= Cost; Finisher(T); return true; }
		if (bAir) { LastResult = TEXT("finisher: in the air (Q stays the quick boost)"); return false; }
		if (!T) C->Deny(TEXT("No target")); else C->Deny(Cost > 1 ? TEXT("Brutes need 2 focus") : TEXT("Need focus"));
		LastResult = FString::Printf(TEXT("finisher denied (focus %.2f)"), Focus);
		return true;
	}
	if (bAir) { C->Deny(TEXT("Not in the air")); LastResult = TEXT("denied: in the air"); return true; }
	if (K == "launcher")
	{ // scripted capture (the hold-attack launcher without the jab-then-hold timing): best eligible target within 4.5 m (a brute only while stunned)
		const FVector Fp = Feet(); AWHEnemy* Best = nullptr; double Bs = 1e9;
		for (AWHEnemy* E : C->Enemies)
		{
			if (!E || !E->Targetable() || (E->Type == EWHEnemyType::Brute && E->Stun <= 0)) continue;
			if (E->State == EWHEnemyState::Air || E->State == EWHEnemyState::Knock || E->State == EWHEnemyState::Down) continue;
			const double Dd = HDist(Fp, E->Pos); if (Dd > 4.5 || FMath::Abs(E->Pos.Z - Fp.Z) > 1.0) continue;
			double Sc = Dd - ((E->State == EWHEnemyState::Attack || E->State == EWHEnemyState::Approach) ? 0.6 : 0.0);
			if (DP) Sc += FMath::Acos(FMath::Clamp(FVector::DotProduct(FlatNorm(E->Pos - Fp), FlatNorm(*DP)), -1.0, 1.0)) * 1.2;
			if (Sc < Bs) { Bs = Sc; Best = E; }
		}
		if (Best) { Launcher(Best); ComboStep = 0; LastResult = TEXT("launcher -> ") + Best->Tag(); }
		else { C->Deny(TEXT("No launcher target")); LastResult = TEXT("launcher: no target"); }
		return true;
	}
	if (K == "heal")
	{
		if (Focus >= 1 && Hp < MaxHp) { Focus -= 1; C->Heal(35); LastResult = TEXT("heal +35"); }
		else { C->Deny(Focus < 1 ? TEXT("Need focus") : TEXT("Health full")); LastResult = TEXT("heal denied"); }
		return true;
	}
	if (K == "throw") { C->Deny(TEXT("Nothing to throw (props not ported)")); LastResult = TEXT("throw: not ported"); return true; }
	return true;
}

void FWHSpidey::Measure(double Dt)
{
	if (Dt < 1e-4) return;
	Vel = (Pos - PrevPos) / Dt;
	if (Vel.Size() > 40) Vel = Vel.GetSafeNormal() * 40;
}

void FWHSpidey::Override(double Dt)
{
	UWebTraversalComponent* Tv = Hero->GetTraversal();
	bOwned = false; bAirEnd = false;
	if (M.Name == "free") { Pos = Tv->PosM(); VisYaw = Tv->Facing(); bKin = false; }
	PrevPos = Pos;
	const EWebTravMode Md = Tv->Mode();
	bAirborne = Md == EWebTravMode::Air || Md == EWebTravMode::Swing || Md == EWebTravMode::Zip || M.Name == "air" || M.Name == "airStrike" || (M.Name == "launch" && M.bRise);
	FWHCombatInput& In = C->Input;
	const double Gt = C->Time;
	const bool bGround = Md == EWebTravMode::Ground;
	// --- held attack: cancel the jab that fired on press into the launcher (ground) / slam (air)
	if (In.HoldNow(C->RTime))
	{
		AWHEnemy* T = M.Target.Get();
		if (M.Name == "strike" && !M.bLong && T && T->Alive() && Gt - M.PressT < 0.45 && T->State != EWHEnemyState::Knock && (T->Type != EWHEnemyType::Brute || T->Stun > 0))
		{ Launcher(T); ComboStep = 0; LastResult = TEXT("hold -> launcher ") + T->Tag(); C->LogEvent(TEXT("action ") + LastResult); }
		else if ((M.Name == "air" || M.Name == "airStrike") && T && T->Alive()) { AirStrike(T, 2, true); C->LogEvent(TEXT("action hold -> air slam")); }
		else if (M.Name == "free" || M.Name == "whiff") { AttackInput(true); C->LogEvent(TEXT("action hold: ") + LastResult); }
	}
	// --- dodge: C / Ctrl on the ground (in the air the key stays traversal's drop / dive)
	const FWHThreat* Th = C->NearestThreat();
	if (In.Has("dodge", Gt) && !bGround && M.Name == "free") In.Take("dodge", Gt);
	if (In.Has("dodge", Gt) && bGround && M.Name != "down" && M.Name != "finisher" && M.Name != "landing" && !(M.Name == "dodge" && M.T < 0.4))
	{
		In.Take("dodge", Gt);
		FVector TD = FVector::ZeroVector;
		if (Th && Th->E.IsValid()) TD = FlatNorm(Th->E->Pos - Pos);
		const bool bPerfect = Th && Th->At - Gt <= 0.3 && Th->At - Gt > -0.05;
		bKin = false; Dodge(TD, bPerfect, FVector::ZeroVector);   // (scripted 'toward' aims attacks only; no stick for the dodge)
		C->OnDodge(Th, bPerfect);
		C->LogEvent(TEXT("action ") + LastResult);
		Motion(Dt); Turn(Dt, 16, 13); Measure(Dt); Commit();
		return;
	}
	// --- buffered actions: run when free or inside a cancel window
	FWHClipTrack* Tk = Track();
	const double ClipT = Tk ? Tk->T : 0;
	const bool bCancel = M.Name == "free" || (M.Name == "whiff" && M.T > 0.1)
		|| (M.Name == "strike" && M.bHitDone && ClipT >= M.Hit + 0.05)
		|| (M.Name == "dodge" && (M.bPerfect ? M.T > 0.08 : M.T > 0.38))
		|| (M.Name == "hit" && M.T > 0.3)
		|| (M.Name == "landing" && M.T > 0.15)
		|| M.Name == "air" || (M.Name == "airStrike" && M.bHitDone);
	if (bCancel)
	{
		static const FName Order[] = { "finisher", "throw", "strike", "heal", "launcher", "attack", "web" };
		for (const FName& K : Order)
		{
			if (!In.Has(K, Gt)) continue;
			In.Take(K, Gt);
			LastResult.Reset();
			DoAction(K);
			C->LogEvent(FString::Printf(TEXT("action %s: %s"), *K.ToString(), *LastResult));
			break;
		}
	}
	else if (In.Has("web", Gt) && M.Name != "dodge" && M.Name != "down" && M.Name != "finisher" && M.Name != "hit" && M.Name != "webStrike")
	{
		In.Take("web", Gt); LastResult.Reset(); DoAction("web"); C->LogEvent(TEXT("action web: ") + LastResult);
	}
	if (Hp <= 0 && M.Name != "down" && bGround)
	{
		for (AWHEnemy* E : C->Enemies) if (E && E->Alive()) { TakeHit(E, 0, true); break; }
	}
	if (M.Name != "free") { bOwned = true; Motion(Dt); Turn(Dt); Measure(Dt); }
	Commit();
}

void FWHSpidey::Commit()
{
	if (!bOwned) return;
	UWebTraversalComponent* Tv = Hero->GetTraversal();
	if (!bKin)
	{ // on the ground: feet exactly on the floor (Teleport enters ground mode)
		Pos.Z = GroundZ(Pos.X, Pos.Y, Pos.Z - H + 0.6) + H;
	}
	Tv->Teleport(Pos, VisYaw);
	if (bAirEnd) Tv->SetVelocityM(AirEndV);
	const FVector BodyCm = Tv->PosM() * 100.0;
	Hero->SetActorLocationAndRotation(BodyCm - FVector(0, 0, UWebTraversalComponent::H * 100.0) + FVector(0, 0, Hero->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()),
		FRotator(0, FMath::RadiansToDegrees(VisYaw), 0), false, nullptr, ETeleportType::TeleportPhysics);
	bAirEnd = false;
}

void FWHSpidey::Stance(double Dt)
{
	if (M.Name != "free") return;
	UWebTraversalComponent* Tv = Hero->GetTraversal();
	const FVector V = Tv->VelM();
	const bool bWant = C->bEngaged && Nearest(NEAR) >= 0 && Tv->Mode() == EWebTravMode::Ground && FMath::Sqrt(V.X * V.X + V.Y * V.Y) < 0.4;
	FWHClipTrack* S = Layer.Find(StanceUid);
	if (bWant && (!S || S->Out > 0))
	{
		FWHClipOpts O; O.bLoop = true; O.Fade = 0.25; O.Id = "stance";
		StanceUid = PlayClip("fightIdle", O);
	}
	else if (!bWant && S && S->Out <= 0) { Layer.Stop(0.3); StanceUid = 0; }
}

void FWHSpidey::Late(double Dt)
{
	Stance(Dt);
	Layer.Advance(Dt);
	TArray<FWHClipSample> Smp; Layer.Snapshot(Smp);
	if (UWHCombatHeroAnim* A = Anim()) A->SetCombatSamples(Smp);
}

void FWHSpidey::Reset()
{
	if (M.Name != "free") Free(0.3);
	ComboStep = 0;
}
