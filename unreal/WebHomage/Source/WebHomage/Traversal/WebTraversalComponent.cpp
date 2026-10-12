// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// Port of src/player/traversal/traversal.js (browser build). Function order and comments follow the browser file so the
// two can be diffed by eye; owner feel notes (user rN / feedback #N) are kept where they shaped the code.
#include "Traversal/WebTraversalComponent.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Traversal/Anim/WebTravAnimInstance.h"
#include "Traversal/WebTravFlips.h"
#include "Traversal/WebTravCamera.h"
#include "WebHomage.h"
#include "Engine/World.h"
#include "Engine/Level.h"

namespace
{
#define WT_NAME(x) const FName N_##x(TEXT(#x));
	WT_NAME(idle) WT_NAME(walk) WT_NAME(run) WT_NAME(sprint) WT_NAME(jumpCharge) WT_NAME(vault)
	WT_NAME(landLight) WT_NAME(landMedium) WT_NAME(landHard) WT_NAME(landRoll)
	WT_NAME(jumpLaunch) WT_NAME(rise) WT_NAME(apex) WT_NAME(fall) WT_NAME(dive) WT_NAME(release) WT_NAME(trick)
	WT_NAME(pointLaunch) WT_NAME(wallJump) WT_NAME(zipPull)
	WT_NAME(swingLow) WT_NAME(swingBottom) WT_NAME(swingHigh) WT_NAME(wallKick)
	WT_NAME(zipFire) WT_NAME(zipFlight) WT_NAME(zipCatch) WT_NAME(perchLand) WT_NAME(perchIdle)
	WT_NAME(crawl) WT_NAME(wallRun) WT_NAME(wallRunSide) WT_NAME(cornerWrap) WT_NAME(wallZip) WT_NAME(topOut) WT_NAME(landTopOut)
	WT_NAME(tuckFlip) WT_NAME(layout) WT_NAME(corkscrew) WT_NAME(scissor)
	WT_NAME(low) WT_NAME(fire) WT_NAME(flight) WT_NAME(catch)
	// events
	WT_NAME(jump) WT_NAME(land) WT_NAME(airTrick) WT_NAME(swingWallKick) WT_NAME(noAnchor) WT_NAME(swingChain) WT_NAME(swingStart)
	WT_NAME(swingJump) WT_NAME(skyLaunch) WT_NAME(swingToWall) WT_NAME(anchorLost) WT_NAME(ropeReanchor) WT_NAME(ropeWrap) WT_NAME(trickBoost) WT_NAME(wall) WT_NAME(cornerWrapEv)
	WT_NAME(wallLaunch) WT_NAME(wallHop) WT_NAME(zip) WT_NAME(zipLaunch) WT_NAME(zipCancel) WT_NAME(zipWebRelease) WT_NAME(perch)
	WT_NAME(webDash) WT_NAME(quickZip) WT_NAME(quickBoost)
#undef WT_NAME

	const FVector ZUP(0, 0, 1);
	double Damp(double A, double B, double Rate, double Dt) { return A + (B - A) * (1.0 - FMath::Exp(-Rate * Dt)); }
	double AngWrap(double A) { return FMath::Atan2(FMath::Sin(A), FMath::Cos(A)); }
	double Yaw(const FVector& V) { return FMath::Atan2(V.Y, V.X); }
	FVector YawDir(double A) { return FVector(FMath::Cos(A), FMath::Sin(A), 0.0); }
	FVector RotZ(const FVector& V, double A) { const double C = FMath::Cos(A), S = FMath::Sin(A); return FVector(V.X * C - V.Y * S, V.X * S + V.Y * C, V.Z); }
	double HLen(const FVector& V) { return FMath::Sqrt(V.X * V.X + V.Y * V.Y); }
	FVector Flat(const FVector& V) { return FVector(V.X, V.Y, 0.0); }
	double Sgn(double V) { return V > 0 ? 1.0 : V < 0 ? -1.0 : 0.0; }
	// v <- v - (v . R^) R^ ; returns the removed radial speed (webtension.js)
	double ProjectPerpendicular(FVector& V, const FVector& RHat) { const double VR = FVector::DotProduct(V, RHat); V -= RHat * VR; return VR; }

	struct FTrickDef { FName Name; double Dur, Snap, Boost, Up, Steer, Side; };
	// Swing-release / air tricks (user r10): the boost lands at the trick's snap moment (snap * dur s in), not at release.
	const FTrickDef TRICKS[] = {
		{ N_tuckFlip, 0.9, 0.35, 5.5, 0.8, 0, 0 },          // tucked front somersault (user r10c)
		{ N_layout, 1.3, 0.35, 4.0, 2.5, 0, 0 },            // loose layout flip: speed + a bit of height
		{ N_corkscrew, 0.78, 0.35, 5.0, 0.6, 0.35, 2.5 },   // barrel roll: speed + steering / drift toward the stick
		{ N_scissor, 0.7, 0.32, 3.5, 1.4, 0, 0 },           // running-in-air stride
	};
	const FTrickDef* TrickDef(FName N) { for (const FTrickDef& D : TRICKS) { if (D.Name == N) return &D; } return nullptr; }

	// user r9w/r9z: E on a wall = web-zip straight up the facade, two webs ~42 m up, pull 46 -> 16 m/s over 0.95 s
	struct { double Dur = 0.95, V0 = 46, V1 = 16, Reach = 42, Snap = 0.75, Cd = 1.2; } WZIP;
	// user r10: web-zip is INSTANT: zipFire (~0.05 s) -> zipFlight (burst to a 40-72 m/s peak) -> braking -> zipCatch -> perch
	const double ZIP_BRAKE = 200, ZIP_VEND = 5, ZIP_RAMP = 0.07, ZIP_SPEED = 0.83;
	// Q / L1: a camera-directed air impulse, independent of zip/swing anchors.
	struct { double Dv = 12, Cd = 0.55, Dur = 0.62; } QUICK;

	FVector ForwardBoostDirection(const FVector& ViewForward, double FallbackYaw)
	{
		FVector Horizontal = Flat(ViewForward).GetSafeNormal();
		if (Horizontal.IsNearlyZero()) Horizontal = YawDir(FallbackYaw);
		// Keep looking up/down useful without turning a forward boost into a vertical launch/dive.
		const double Elevation = FMath::Clamp(FMath::Atan2(ViewForward.Z, HLen(ViewForward)),
			-FMath::DegreesToRadians(45.0), FMath::DegreesToRadians(45.0));
		return Horizontal * FMath::Cos(Elevation) + ZUP * FMath::Sin(Elevation);
	}

	FVector ForwardBoostVelocity(const FVector& Velocity, const FVector& Direction, double DeltaSpeed, double SpeedLimit)
	{
		// Limit only the added impulse. Scaling the whole velocity would erase sideways/falling momentum,
		// especially during flips, and could turn a boost into a brake when already above the usual cap.
		const double SpeedSq = Velocity.SizeSquared();
		const double Limit = FMath::Max(SpeedLimit, FMath::Sqrt(SpeedSq));
		const double Along = FVector::DotProduct(Velocity, Direction);
		const double Room = FMath::Max(0.0, FMath::Sqrt(FMath::Max(0.0, Along * Along + Limit * Limit - SpeedSq)) - Along);
		return Velocity + Direction * FMath::Min(FMath::Max(0.0, DeltaSpeed), Room);
	}

	bool IsLand(FName S) { return S == N_landLight || S == N_landMedium || S == N_landHard || S == N_landRoll || S == N_landTopOut; }
}

UWebTraversalComponent::UWebTraversalComponent()
{
	PrimaryComponentTick.bCanEverTick = false; // driven by AWebTravCharacter::Tick
	S.Sub = N_fall;
}

void UWebTraversalComponent::InitWorld(UWorld* World, const AActor* InOwner)
{
	TravWorld.Init(World, InOwner);
	StreamWorld = World;
	if (!LevelAddedHandle.IsValid())
	{
		LevelAddedHandle = FWorldDelegates::LevelAddedToWorld.AddUObject(this, &UWebTraversalComponent::OnLevelAddedToWorld);
		LevelRemovedHandle = FWorldDelegates::LevelRemovedFromWorld.AddUObject(this, &UWebTraversalComponent::OnLevelRemovedFromWorld);
	}
	Anchors = MakeUnique<FWebTravAnchors>(TravWorld);
	Rng.Initialize(RandomSeed);
	FlipRng.Initialize(RandomSeed * 31 + 7);
	{ int32 V = 1; if (FParse::Value(FCommandLine::Get(), TEXT("-WHFlipVar="), V)) WebFlips::bVariants = V != 0; } // round 19 A/B
	{ int32 V = 1; if (FParse::Value(FCommandLine::Get(), TEXT("-WHTravHighFix="), V)) FWebTravAnchors::bHighFix = V != 0; } // round 19 A/B
	{ int32 V = 1; if (FParse::Value(FCommandLine::Get(), TEXT("-WHTrickCancel="), V)) bTrickCancel = V != 0; } // round 20 A/B
	{ int32 V = 1; if (FParse::Value(FCommandLine::Get(), TEXT("-WHFacadeWeb="), V)) bFacadeWeb = V != 0; } // round 20 A/B
	{ int32 V = 1; if (FParse::Value(FCommandLine::Get(), TEXT("-WHPerchTopFix="), V)) bPerchTopFix = V != 0; } // round 20 A/B
	{ int32 V = 1; if (FParse::Value(FCommandLine::Get(), TEXT("-WHRopeGuard="), V)) bRopeGuard = V != 0; } // round 20 A/B
	bWorldReady = true;
}

int32 UWebTraversalComponent::ZipKindCode() const
{
	return HasZipTarget() ? 1 : 0;
}

void UWebTraversalComponent::Emit(FName Type, float Sev, float Dist, float K, bool bRun)
{
	FWebTravEvent E;
	E.Type = Type; E.Severity = Sev; E.Dist = Dist; E.K = K; E.bRun = bRun;
	Events.Add(E);
}

// ------------------------------------------------------------------ web strands (web.js attach / release)
void UWebTraversalComponent::WebAttach(bool bRight, const FVector& Anchor, double ShootDur, bool bSecond)
{
	FWebTravStrand& St = Strands[bSecond ? 1 : 0];
	St.bActive = true; St.bRightHand = bRight; St.Anchor = Anchor; St.Age = 0.f; St.ShootDur = float(ShootDur);
	St.Taut = 0.f; St.ReleaseT = -1.f; St.bSnap = false; St.BlendT = 1.f; St.AnchorFrom = Anchor;
	if (ShootDur >= 0.08 && !bSecond) St.Age = -ShootAnticip;   // round 04: the arm leads the strand by 2 frames (the strand is not drawn while Age < 0)
}

void UWebTraversalComponent::OnLevelAddedToWorld(ULevel* Level, UWorld* InWorld)
{
	if (InWorld == StreamWorld.Get() && Level && !Level->IsPersistentLevel()) TravWorld.AddLevel(Level);
}

void UWebTraversalComponent::OnLevelRemovedFromWorld(ULevel* Level, UWorld* InWorld)
{
	FBox B(ForceInit);
	if (InWorld != StreamWorld.Get() || !Level || !TravWorld.RemoveLevel(Level, B)) return;
	// an anchor held on a removed solid is released: a swing falls (as when its anchor is lost), strands let go
	const FBox Pad = B.ExpandBy(1.0);
	if (S.Mode == EWebTravMode::Swing && Pad.IsInside(S.Sw.Anchor))
	{
		Emit(N_anchorLost, 0.f);
		bLeaveSwingOK = true;
		WebRelease(); SetMode(EWebTravMode::Air, N_fall); S.AirT = 0; S.ApexZ = FeetZ(); S.SwingCooldown = 0.3;
		bLeaveSwingOK = false;
		UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV stream: swing anchor released (its level was removed)"));
	}
	for (FWebTravStrand& St : Strands) if (St.bActive && St.ReleaseT < 0.f && Pad.IsInside(St.Anchor)) { St.ReleaseT = 0.f; }
}

void UWebTraversalComponent::EndPlay(const EEndPlayReason::Type Reason)
{
	if (LevelAddedHandle.IsValid()) { FWorldDelegates::LevelAddedToWorld.Remove(LevelAddedHandle); LevelAddedHandle.Reset(); }
	if (LevelRemovedHandle.IsValid()) { FWorldDelegates::LevelRemovedFromWorld.Remove(LevelRemovedHandle); LevelRemovedHandle.Reset(); }
	Super::EndPlay(Reason);
}

void UWebTraversalComponent::WebRelease(bool bSnap)
{
	for (FWebTravStrand& St : Strands)
	{
		if (St.bActive && St.ReleaseT < 0.f) { St.ReleaseT = 0.f; St.bSnap = bSnap; }
	}
}

void UWebTraversalComponent::WebReleaseSecond()
{
	if (Strands[1].bActive && Strands[1].ReleaseT < 0.f) Strands[1].ReleaseT = 0.f;
}

// ------------------------------------------------------------------ helpers
// standable floor: thin pinnacles are NOT floors — if the surface drops away on all four sides within 0.22 m, use the
// level around it
double UWebTraversalComponent::StandAt(double X, double Y, double Z) const
{
	const double G0 = FloorAt(X, Y, Z), RR = 0.22;
	const double A = FloorAt(X + RR, Y, Z), B = FloorAt(X - RR, Y, Z), C = FloorAt(X, Y + RR, Z), D = FloorAt(X, Y - RR, Z);
	if (A < G0 - 0.25 && B < G0 - 0.25 && C < G0 - 0.25 && D < G0 - 0.25) return FMath::Max(FMath::Max(A, B), FMath::Max(C, D));
	return G0;
}

FVector UWebTraversalComponent::InputDir(const FWebTravInput& I) const
{
	if (!Cam) return FVector(I.Move.Y, I.Move.X, 0.0);
	return Cam->ForwardFlat() * I.Move.Y + Cam->RightFlat() * I.Move.X;
}

// INVARIANT (user feedback #4): the web is released ONLY by (a) letting go of the swing button, (b) a zip / web-dash /
// quick boost (explicit button press), or (c) teleport. Anything else that leaves 'swing' while the button is held is a bug.
void UWebTraversalComponent::SetMode(EWebTravMode M, FName Sub)
{
	if (S.Mode == EWebTravMode::Swing && M != EWebTravMode::Swing && LastInput.bSwing && !bLeaveSwingOK)
	{
		UE_LOG(LogWebHomage, Error, TEXT("[traversal] BUG: left 'swing' -> '%d/%s' while the swing button is held (web must stay attached)"), int32(M), *Sub.ToString());
	}
	if (S.Mode != M) { S.ModeT = 0; S.PrevMode = S.Mode; }
	if (M != EWebTravMode::Air) S.bTopOut = false;
	if (M != EWebTravMode::Air && M != EWebTravMode::Swing) S.bWebPending = false;
	S.Mode = M;
	SetSub(Sub);
}

void UWebTraversalComponent::SetSub(FName Sub)
{
	if (S.Sub != Sub) { S.Sub = Sub; S.SubT = 0; }
}

bool UWebTraversalComponent::Collide(double StepH, double Rad, FTravContact& C)
{
	FVector Feet(S.Pos.X, S.Pos.Y, S.Pos.Z - H);
	const bool bHit = TravWorld.PushOutCapsule(Feet, Rad, HEIGHT, StepH, C);
	S.Pos.X = Feet.X; S.Pos.Y = Feet.Y;
	return bHit;
}

bool UWebTraversalComponent::HDir(const FVector& V, FVector& Out)
{
	Out = FVector(V.X, V.Y, 0.0);
	const double L = Out.Size();
	if (L > 1e-4) { Out /= L; return true; }
	return false;
}

void UWebTraversalComponent::CapSpeed(double M)
{
	const double L = S.Vel.Size();
	if (L > M) S.Vel *= M / L;
}

// ------------------------------------------------------------------ ground
void UWebTraversalComponent::EnterGround(FName Sub)
{
	SetMode(EWebTravMode::Ground, Sub);
	S.bGrounded = true; S.Vel.Z = 0; S.DashCount = 0; S.bDive = false; S.Trick = NAME_None; S.Q.N = 0;
	const double HS = HLen(S.Vel);
	S.Speed = HS;
	if (HS > 3) S.Facing = Yaw(S.Vel); // (tiny residual velocity never flips facing)
}

void UWebTraversalComponent::StepGround(double Hs, FWebTravInput& I)
{
	FVector InD = InputDir(I);
	const double Mag = FMath::Min(1.0, InD.Size());
	if (Mag > 1e-3) InD /= Mag;
	// user r12 Shift-walk is disabled in the browser (user r-nowalk): Shift = ground parkour / wall run
	const bool bParkour = I.bSwing || I.bSprint;
	const bool bLanding = IsLand(S.Sub);
	// landing recovery: hard landings lock movement briefly, rolls carry momentum
	if (bLanding)
	{
		S.LandLock -= Hs;
		if (S.Sub == N_landRoll) S.Speed = FMath::Max(S.Speed - 6 * Hs, FMath::Min(S.Speed, 6.0));
		else if (S.LandLock > 0) S.Speed = FMath::Max(0.0, S.Speed - 40 * Hs);
		const bool bCancel = S.LandLock <= 0 && (Mag > 0.2 || I.bJumpPressed || I.bJump);
		const double Lim = S.Sub == N_landHard ? 0.75 : S.Sub == N_landRoll ? 0.6 : S.Sub == N_landTopOut ? 0.62 : S.Sub == N_landMedium ? 0.35 : 0.18;
		if (S.SubT > Lim || bCancel) SetSub(N_idle);
	}
	const bool bLocked = bLanding && S.LandLock > 0;
	// --- jump (hold to charge, release to launch)
	if (!bLocked)
	{
		// jump buffer: Space pressed shortly before touching down still starts the charge
		if ((I.bJumpPressed || (S.JumpBuf > 0 && I.bJump)) && !S.bCharging) { S.bCharging = true; S.ChargeT = 0; S.JumpBuf = 0; }
		if (S.bCharging)
		{
			S.ChargeT += Hs;
			S.JumpCharge = FMath::Clamp((S.ChargeT - 0.1) / 0.55, 0.0, 1.0);
			// tap = short anticipation crouch (never a 1-frame pop into the air)
			if (!I.bJump && S.ChargeT >= (S.Speed > RUN ? 0.06 : 0.1)) { LaunchJump(bParkour); return; }
		}
	}
	// --- RMB pressed on the ground: if there is anything to swing from, hop up and swing
	if (!bLocked && I.bSwingPressed && !S.bCharging && S.SwingCooldown <= 0)
	{
		const FVector Fwd = TravelDir(I);
		const FVector Probe = S.Pos + FVector(0, 0, 3);
		FTravAnchor A;
		if (Anchors->Find(Probe, Fwd, nullptr, FMath::Max(S.Speed, 10.0), S.FloorZ, A) && A.Point.Z > S.Pos.Z + 6)
		{
			S.JumpCharge = 0.35; LaunchJump(true); S.bGroundSwing = true; S.SwingCooldown = 0.1;
			return;
		}
	}
	// --- locomotion: facing-driven (no side slip), accel / decel curves
	double Target = 0;
	if (!bLocked && Mag > 0.08)
	{
		Target = Mag < 0.55 ? WALK * Mag / 0.55 + 0.4 : WALK + (RUN - WALK) * (Mag - 0.55) / 0.45;
		if (S.bCharging) Target *= 1 - 0.75 * S.JumpCharge;
		const double Want = Yaw(InD), D = AngWrap(Want - S.Facing);
		if (S.Sub != N_landRoll)
		{
			if (FMath::Abs(D) > 2.4 && S.Speed > 6) { S.Speed *= FMath::Exp(-14 * Hs); S.Facing += Sgn(D) * 9 * Hs; } // skid-turn
			else
			{
				const double Rate = S.Speed < 2 ? 18 : S.Speed < 9 ? 11 : 7;
				S.Facing += FMath::Clamp(D, -Rate * Hs, Rate * Hs);
			}
		}
		Target *= FMath::Clamp(1 - FMath::Max(0.0, FMath::Abs(D) - 0.9) * 0.5, 0.35, 1.0); // slow into sharp turns
	}
	if (S.Sub != N_landRoll || S.Speed < 6)
	{
		const double Acc = (bParkour ? 24 : 30) * (S.Speed < 3 ? 1.6 : 1), Dec = Target < 0.1 ? 28 : 22; // ~0.3 s planted stop
		if (Target > S.Speed) S.Speed = FMath::Min(Target, S.Speed + Acc * Hs);
		else S.Speed = FMath::Max(Target, S.Speed - Dec * Hs);
		if (Target < 0.1 && S.Speed < 0.35) S.Speed = 0;
	}
	const double FX = FMath::Cos(S.Facing), FY = FMath::Sin(S.Facing);
	S.Carry *= FMath::Exp(-7 * Hs);
	S.Vel = FVector(FX * S.Speed + S.Carry.X, FY * S.Speed + S.Carry.Y, 0);
	S.Pos.X += S.Vel.X * Hs; S.Pos.Y += S.Vel.Y * Hs;
	FTravContact C;
	const bool bC = Collide(C);
	const bool bWide = bC ? WideWall(C.Normal, C.Point) : false;
	if (bC && !bWide)
	{
		// narrow obstacle (lamp post, pole, hydrant): parkour AROUND it — keep speed, steer onto the tangent
		const double TX = -C.Normal.Y, TY = C.Normal.X;
		double SD = Sgn(FX * TX + FY * TY); if (SD == 0) SD = 1;
		const double Want = FMath::Atan2(TY * SD + C.Normal.Y * 0.35, TX * SD + C.Normal.X * 0.35);
		S.Facing += FMath::Clamp(AngWrap(Want - S.Facing), -10 * Hs, 10 * Hs);
	}
	else if (bC)
	{
		const double Into = -(FX * C.Normal.X + FY * C.Normal.Y);
		if (Into > 0.25) S.Speed *= FMath::Max(0.0, 1 - Into * 0.9 * FMath::Min(1.0, Hs * 30)); // don't run in place against walls
		if (Into > 0.8 && C.Top - FeetZ() > 2.1 && !bParkour) S.Speed = 0;
		const double Obstacle = C.Top - FeetZ();
		if (!bLocked && Into > 0.55 && Mag > 0.3)
		{
			if (Obstacle > STEP && Obstacle < 2.1)
			{
				const double Behind = FloorAt(S.Pos.X - C.Normal.X * (R + 1.2), S.Pos.Y - C.Normal.Y * (R + 1.2), C.Top + 0.05);
				if (bParkour || (Obstacle < 1.2 && Behind > C.Top - 1.5)) { StartVault(C, bParkour); return; }
				if (Obstacle <= 1.45 && StartMantleOnto(C)) return; // parapet with a drop behind: step up and stand ON it
			}
			if (bParkour && Obstacle >= 2.1 && S.WallCooldown <= 0) { EnterWall(C.Normal, C.Point, true, FMath::Max(12.0, S.Speed)); return; }
			if (!bParkour && Obstacle > STEP && Obstacle <= 1.45 && StartMantleOnto(C)) return;
		}
	}
	// --- ground snap (smooth curb step-ups, walk off edges)
	const double FZ = FeetZ();
	const double G0 = StandAt(S.Pos.X, S.Pos.Y, FZ + STEP);
	if (G0 < FZ - 0.65)
	{ // walked off a ledge
		SetMode(EWebTravMode::Air, N_fall); S.bGrounded = false; S.AirT = 0; S.ApexZ = FZ; S.Coyote = 0.12; S.Vel.Z = 0;
		return;
	}
	if (FMath::Abs(G0 - FZ) > 1e-4) S.StepOff = FMath::Clamp(S.StepOff + FZ - G0, -0.6, 0.6);
	S.Pos.Z = G0 + H; S.FloorZ = G0;
	if (!IsLand(S.Sub) && S.Sub != N_vault)
	{
		if (S.bCharging) SetSub(N_jumpCharge);
		else if (S.Speed < 0.2) SetSub(N_idle);
		else if (S.Speed < WALK + 0.8) SetSub(N_walk);
		else if (S.Speed > RUN + 1.5) SetSub(N_sprint);
		else SetSub(N_run);
	}
}

// walking into a parapet / low wall (<= 1.45 m) with a drop behind it: mantle up and stand ON its top
bool UWebTraversalComponent::StartMantleOnto(const FTravContact& C)
{
	const FVector Inward = -C.Normal;
	double Thick = 0;
	for (; Thick < 0.9; Thick += 0.05)
	{
		const double F = FloorAt(C.Point.X + Inward.X * (Thick + 0.03), C.Point.Y + Inward.Y * (Thick + 0.03), C.Top + 0.05);
		if (FMath::Abs(F - C.Top) > 0.06) break;
	}
	if (Thick < 0.15) return false;
	const FVector Land(C.Point.X + Inward.X * (Thick / 2 + 0.02), C.Point.Y + Inward.Y * (Thick / 2 + 0.02), C.Top + H);
	if (TravWorld.Inside(Land + FVector(0, 0, 0.3))) return false;
	FVector Ctrl = FMath::Lerp(S.Pos, Land, 0.3); Ctrl.Z = Land.Z + 0.35;
	const double Sp = HLen(S.Vel); // user r9: hopping up onto a railing keeps the run
	S.Kin = FKin();
	S.Kin.Type = EKin::Vault; S.Kin.Dur = FMath::Clamp(1.2 / FMath::Max(Sp, 3.0), 0.22, 0.42);
	S.Kin.P0 = S.Pos; S.Kin.P1 = Ctrl; S.Kin.P2 = Land; S.Kin.ExitVel = Inward * Sp; S.Kin.Floor = C.Top;
	S.Facing = Yaw(Inward);
	SetMode(EWebTravMode::Ground, N_vault); Emit(N_vault);
	return true;
}

void UWebTraversalComponent::LaunchJump(bool bParkour)
{
	const double K = FMath::Pow(S.JumpCharge, 0.85);
	S.Vel.Z = JUMP + (JUMP_MAX - JUMP) * K + (bParkour && S.Speed > 10 ? 1.2 : 0);
	if (S.Speed > 1)
	{
		const double F = FMath::Min(S.Speed + 1.2, VMAX);
		S.Vel.X = FMath::Cos(S.Facing) * F; S.Vel.Y = FMath::Sin(S.Facing) * F;
	}
	S.bCharging = false; S.ChargeT = 0; S.bGrounded = false;
	const double Charge = S.JumpCharge;
	SetMode(EWebTravMode::Air, N_jumpLaunch); S.AirT = 0; S.ApexZ = FeetZ(); S.JumpCharge = Charge; S.SwingCooldown = 0.04;   // round 01 (W10): a swing pressed right after the jump answers within 0.05 s (was 0.12 s)
	Emit(N_jump, float(Charge));
}

void UWebTraversalComponent::StartVault(const FTravContact& C, bool bFast)
{ // ground mantle over a low obstacle / parapet
	const FVector N = C.Normal;
	const double Top = C.Top;
	const FVector Inward = -N;
	const double OnTop = FloorAt(S.Pos.X - N.X * 1.3, S.Pos.Y - N.Y * 1.3, Top + 0.05);
	FVector Land = S.Pos + Inward * (1.3 + R);
	const double Beyond = FloorAt(Land.X, Land.Y, Top + 0.05);
	if (FMath::Abs(OnTop - Top) > 0.1 && Beyond < Top - 2.2)
	{ // roof edge / parapet with a drop behind it: parkour leap over it
		const double Sp = FMath::Max(HLen(S.Vel), 8.0);
		S.Pos.Z = FMath::Max(S.Pos.Z, Top + 0.15 + H);
		S.Vel = Inward * Sp + ZUP * 6.5;
		S.Facing = Yaw(Inward);
		SetMode(EWebTravMode::Air, N_vault); S.AirT = 0; S.ApexZ = FeetZ(); S.SwingCooldown = 0.1; Emit(N_vault);
		return;
	}
	Land.Z = (FMath::Abs(OnTop - Top) < 0.1 ? Top : Beyond) + H;
	FVector Ctrl = FMath::Lerp(S.Pos, Land, 0.5); Ctrl.Z = Top + H + 0.5;
	const double Sp = FMath::Max(HLen(S.Vel), bFast ? 10.0 : 4.0);
	S.Kin = FKin();
	S.Kin.Type = EKin::Vault; S.Kin.Dur = FMath::Clamp(1.6 / Sp, 0.22, 0.42);
	S.Kin.P0 = S.Pos; S.Kin.P1 = Ctrl; S.Kin.P2 = Land; S.Kin.ExitVel = Inward * Sp * 0.9; S.Kin.Floor = Land.Z - H;
	S.Facing = Yaw(-N);
	SetMode(EWebTravMode::Ground, N_vault); Emit(N_vault);
}

// ------------------------------------------------------------------ air
void UWebTraversalComponent::StepAir(double Hs, FWebTravInput& I)
{
	S.AirT += Hs; S.Coyote -= Hs;
	if (S.bWebPending)
	{ // round 07: web stuck on the rise; the swing starts at the top of the hop (see TryStartSwing)
		S.PendingT += Hs;
		if (!I.bSwing) { S.bWebPending = false; WebRelease(); }
		else if (S.PendingT >= S.PendingShoot + ShootAnticip && (S.Vel.Z <= PendingVz || S.PendingT >= PendingMax))   // round 01: never before the tip has landed
		{
			StartSwing(S.PendingA, S.PendingFwd, S.bPendingTurn ? &S.PendingTurn : nullptr, HLen(S.Vel));
			S.bGroundSwing = false;
			return;
		}
	}
	if (S.Coyote > 0 && I.bJumpPressed) { S.JumpCharge = 0; LaunchJump(I.bSprint || I.bSwing); return; }
	// user r4 #12: double-tap Space in the air = an air flip / corkscrew (once per airtime)
	if (I.bJumpPressed)
	{
		const double DTap = S.AirT - S.AirTapT;
		if (DTap >= 0 && DTap < 0.4 && !S.bAirTrickUsed && HeightAboveFloor() > 2.5 && S.Sub != N_trick)
		{
			StartTrick(ChooseTrick(I)); S.bAirTrickUsed = true; S.AirTapT = -9;
			Emit(N_airTrick);
		}
		else S.AirTapT = S.AirT;
	}
	if (!S.ArmedFlip.IsNone() && (S.Vel.Z <= double(SkyTrickVz) || !S.bSky))
	{ // round 12: the sky launch's flip program starts as the climb slows (apex hang)
		const FName N = S.ArmedFlip;
		S.ArmedFlip = NAME_None;
		StartTrick(N);
		Emit(N_airTrick);
	}
	if (S.TrickBuf > 0 && S.ArmedFlip.IsNone() && S.Sub != N_trick && S.Trick.IsNone() && S.AirT > 0.05)
	{ // round 04: trick on input during the air phase (owner live fix: always a flip when FlipFloorClear m over the floor, the refusal is logged)
		S.TrickBuf = 0;
		if (bLegacyTricks) { if (HeightAboveFloor() > 4.0) { StartTrick(ChooseTrick(I)); S.bAirTrickUsed = true; Emit(N_airTrick); } }
		else AirFlipPress(I);
	}
	if (S.Sub == N_trick && !S.Trick.IsNone() && !S.bTrickBoosted && S.SubT >= S.TrickSnapT) TrickBoost(I);
	// user r10m: holding forward (W) while falling tips into the head-first dive; letting go returns to the flat fall
	const double HAF = HeightAboveFloor();
	const bool bWDive = I.Move.Y > 0.5 && S.AirT > 0.3 && (S.Vel.Z < -7 || (S.bDive && S.Vel.Z < 0)) && S.Sub != N_trick && S.Sub != N_zipPull && HAF > 6;
	S.bDive = (I.bDrop || bWDive) && S.AirT > 0.08 && HAF > 3;
	double Gr = G;
	if (S.bSky && !S.bDive && S.Sub == N_trick && WebFlips::Find(S.Trick)) Gr *= SkyFlipGK; // round 12: the apex flip floats (stays over the roofs)
	else if (S.bFlowFlip && !S.bDive && S.Sub == N_trick && WebFlips::Find(S.Trick)) Gr *= FlowFlipGK; // round 13: the release flip floats (solved in ReleaseSwing)
	else if (!S.bDive && FMath::Abs(S.Vel.Z) < 3.5 && S.Sub != N_zipPull) Gr *= 0.55; // apex hang time
	else if (S.bSky && !S.bDive && FMath::Abs(S.Vel.Z) < SkyHangVz) Gr *= SkyHangK; // round 10: sky-launch hang time
	else if (S.bSky && !S.bDive && S.Vel.Z >= SkyHangVz) Gr *= SkyRiseK;              // round 10: sky-launch climb
	if (S.bDive) Gr *= 1.55;
	// open areas with the swing button held and nothing to attach to: never a dead free-fall — web-assisted glide-dive
	const bool bGlide = I.bSwing && !S.bDive && S.NoAnchorT > 0.15 && S.Vel.Z < -4 && S.AirT > 0.3 && HAF > 3.5;
	S.bGliding = bGlide;
	if (bGlide)
	{
		Gr *= 0.5;
		const double HS0 = HLen(S.Vel);
		FVector HV0;
		if (!HDir(S.Vel, HV0)) HV0 = Cam ? Cam->ForwardFlat() : FVector::ForwardVector;
		const double Excess = FMath::Max(0.0, -S.Vel.Z - 13); // descent beyond ~13 m/s becomes forward speed
		const double Conv = FMath::Min(Excess, 18 * Hs);
		S.Vel.Z += Conv;
		const double Add = FMath::Min(Conv * 0.9 + 3 * Hs, FMath::Max(0.0, 34 - HS0));
		S.Vel.X += HV0.X * Add; S.Vel.Y += HV0.Y * Add;
	}
	S.Vel.Z = FMath::Max(S.Vel.Z - Gr * Hs, S.bDive ? -72.0 : -56.0);
	if (bGlide && S.NoAnchorT < 4 && HAF < 12) S.Vel.Z = Damp(S.Vel.Z, -2.5, 3, Hs);
	// air control — after a web release the release velocity owns the trajectory (user feedback #4b): control fades in over ~0.9 s
	FVector InD = InputDir(I);
	S.RelT += Hs;
	const double RelK = FMath::Clamp((S.RelT - 0.35) / 0.55, 0.0, 1.0);
	const double RawMag = FMath::Min(1.0, InD.Size()), Mag = RawMag * RelK;
	const double HS = HLen(S.Vel);
	if (Mag > 0.05)
	{
		InD /= FMath::Max(InD.Size(), 1e-3);
		if (HS < 9)
		{
			S.Vel.X += InD.X * 16 * Mag * Hs; S.Vel.Y += InD.Y * 16 * Mag * Hs;
			const double N = HLen(S.Vel), Cap = FMath::Max(9.0, HS);
			if (N > Cap) { S.Vel.X *= Cap / N; S.Vel.Y *= Cap / N; }
		}
		else
		{
			const double Cur = Yaw(S.Vel), Want = Yaw(InD), D = AngWrap(Want - Cur);
			const double Turn = FMath::Clamp(D, -1.9 * Mag * Hs, 1.9 * Mag * Hs), NA = Cur + Turn;
			double Sp = HS;
			if (FMath::Abs(D) > 2.2) Sp = FMath::Max(6.0, HS - 8 * Hs); // pulling back = air brake
			S.Vel.X = FMath::Cos(NA) * Sp; S.Vel.Y = FMath::Sin(NA) * Sp;
		}
	}
	if (S.bDive)
	{ // dive: tuck and gain speed, keep heading
		const double N = HLen(S.Vel);
		if (N > 2) { const double K = FMath::Min(N + 3 * Hs, 30.0) / N; S.Vel.X *= K; S.Vel.Y *= K; }
	}
	if (HS > 32 + 3 * S.Chain) { S.Vel.X *= 1 - 0.12 * Hs; S.Vel.Y *= 1 - 0.12 * Hs; }
	// round 08: canyon keeping from the moment of release (was only 0.9 s after it: releases carried 20+ m/s sideways into facades)
	if (HS > 8 && (S.Sub == N_release || S.Sub == N_trick || S.Sub == N_rise || S.Sub == N_apex || S.Sub == N_fall || I.bSwing)) Corridor(Hs, InD);
	const double PrevFeet = FeetZ();
	S.Pos += S.Vel * Hs;
	FTravContact C;
	if (Collide(0.35, R, C))
	{
		FVector HV;
		const double Into = HDir(S.Vel, HV) ? -FVector::DotProduct(HV, C.Normal) : 0;
		// round 10: a push toward an open cross street past a corner is not a push into the wall
		FTravHit HStick;
		const FVector InN = InD.SizeSquared() > 0.1 ? InD.GetSafeNormal() : FVector::ZeroVector;
		const bool bPushIn = FVector::DotProduct(InD, C.Normal) < -0.4
			&& !(InN.SizeSquared() > 0.5 && !(TravWorld.Raycast(S.Pos, InN, 12.0, HStick) && FMath::Abs(HStick.Normal.Z) < 0.5));
		// chaining (RMB held, or just released a swing) and not deliberately steering into the wall: skip off it
		const bool bChaining = (I.bSwing || S.RelT < 0.7) && !bPushIn && HLen(S.Vel) > 9;
		if ((Into > 0.3 || bPushIn) && S.WallCooldown <= 0 && C.Top - FeetZ() > 1.2 && WideWall(C.Normal, C.Point) && !bChaining)
		{
			if (C.Top - FeetZ() < 1.9 && S.Vel.Z > -6) { StartVault(C, true); return; } // chest-height ledge: mantle
			const double Sp = S.Vel.Size();
			EnterWall(C.Normal, C.Point, ((I.bSwing || I.bSprint) && Sp > 7) || Sp > 18, Sp);
			return;
		}
		const double VN = FVector::DotProduct(S.Vel, C.Normal);
		if (VN < 0)
		{
			S.Vel -= C.Normal * VN;
			// chaining through a facade graze: skip off it along the street (keeps flow, never a wall-run up the tower)
			if (bChaining && -VN > 3)
			{
				S.Vel += C.Normal * FMath::Clamp(-VN * 0.25, 1.5, 4.0); S.WallCooldown = 0.25;
				Emit(N_swingWallKick, float(FMath::Clamp(-VN / 30, 0.1, 0.5)));
			}
		}
	}
	// swing attach (RMB held): search throttled; after a release wait for the apex / trick to play out
	if (S.bJumpRelHold && (S.Vel.Z <= 0 || S.Mode != EWebTravMode::Air)) S.bJumpRelHold = false;
	if (I.bSwing && !S.bWebPending && S.SwingCooldown <= 0 && (!S.bJumpRelHold || I.bSwingPressed)) // a fresh RMB press still grabs at once
	{
		// round 11: a flip program only lets the next web in during its final reach (catch continuity); old tricks: last 0.35 s
		const FWebFlipProgram* FP = S.Sub == N_trick ? WebFlips::Find(S.Trick) : nullptr;
		// round 13: from CatchOpen s before the end (inside the final reach) -- critic r12 "attach a web within 0.3 s of Reach"
		const double BusyUntil = FP ? double(FP->CatchT()) - 0.02 : FMath::Max(0.62, S.TrickDur - 0.35);
		// round 20 (critic r19 owner bug 1: "a held RMB during a trick waits 0.47-1.08 s"): a FRESH press always cancels the trick / top-out
		// flip / armed flip into a swing at once (the program's rotation springs back to the body frame in 0.07 s, PoseFigure); only a
		// button that was already held lets the flip finish into its catch window
		const bool bCancelTrick = I.bSwingPressed && bTrickCancel && ((S.Sub == N_trick && S.SubT < BusyUntil) || S.Sub == N_topOut || !S.ArmedFlip.IsNone());
		const bool bTrickBusy = S.Sub == N_trick && S.SubT < BusyUntil && !bCancelTrick; // let the flip finish
		if (bCancelTrick)
		{
			FlipCancels++;
			S.ArmedFlip = NAME_None;
			UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV trick cancel: RMB pressed in %s at %.2f s of it -> swing search now"), *S.Sub.ToString(), S.SubT);
		}
		// round 07 (critic r06, swing cadence): after a web release a held button searches again from 0.22 s on, even while
		// still rising (was: only once vz < 5.5 m/s -> 1-1.7 s web-less falls); a fresh press always searches at once (the
		// throttle left over from the previous search used to swallow the press)
		const bool bReady = I.bSwingPressed || (S.bGroundSwing && S.AirT > (bTrickCancel && S.Sub == N_wallJump ? 0.0 : 0.14)) || (S.AirT > 0.1 && S.Vel.Z < 5.5 && !bTrickBusy) || S.Vel.Z < -6
			|| (S.RelT > ReattachAfter && !bTrickBusy);
		if (I.bSwingPressed) S.SearchT = 0;
		S.SearchT -= Hs;
		if (bReady && S.SearchT <= 0 && !bTrickBusy)
		{
			S.SearchT = 0.06;
			if (TryStartSwing(I)) return;
		}
	}
	// landing
	const double F = StandAt(S.Pos.X, S.Pos.Y, PrevFeet + 0.05);
	if (FeetZ() <= F && S.Vel.Z <= 0) { Land(F, I); return; }
	if (S.Sub == N_vault && S.SubT < 0.3) S.Facing = Yaw(S.Vel);
	S.ApexZ = FMath::Max(S.ApexZ, FeetZ());
	// sub-state
	double Timed = -1;
	if (S.Sub == N_jumpLaunch) Timed = 0.16; else if (S.Sub == N_release) Timed = 0.4; else if (S.Sub == N_trick) Timed = S.TrickDur > 0 ? S.TrickDur : 0.85;
	// round 11: a flip program keeps its final reach while the web button is held and no web has caught yet (<= FlipReachHold s):
	// the catch comes out of the reach instead of a fall / dive pose in between
	// round 05 (critic r04 gap 1 / F8: "catch <= 0.25 s after the last shape"; s3b showed a 0.7-1.2 s dead glide between the
	// program's end and the scripted press): the reach also holds WITHOUT the button (up to FlipReachIdle s) -- the trick's last
	// shape runs (its scissor / free-arm pong) until the catch, so the web arrives out of the reach with no frozen glide
	if (S.Sub == N_trick && WebFlips::Find(S.Trick)) Timed += FMath::Max(I.bSwing ? double(FlipReachHold) : 0.0, double(FlipReachIdle));
	else if (S.Sub == N_pointLaunch) Timed = 0.45; else if (S.Sub == N_topOut) Timed = 1.6; else if (S.Sub == N_wallJump) Timed = 0.3; else if (S.Sub == N_zipPull) Timed = 0.28; else if (S.Sub == N_vault) Timed = 0.3;
	if (Timed < 0 || S.SubT > Timed)
	{
		if (S.Sub == N_trick) S.Trick = NAME_None;
		if (S.bDive || S.bGliding) SetSub(N_dive);
		else if (S.Vel.Z > 3) SetSub(N_rise);
		else if (S.Vel.Z > -4) SetSub(N_apex);
		else SetSub(S.Vel.Z < -24 && !I.bSwing ? N_dive : N_fall);
	}
}

void UWebTraversalComponent::Land(double F, const FWebTravInput& I)
{
	S.bWallCancel = false;
	S.bAirTrickUsed = false; S.AirTapT = -9;
	S.NoAnchorT = 0; S.bGliding = false; S.bGroundSwing = false;
	const double Impact = -S.Vel.Z, Drop = S.ApexZ - F;
	const bool bFromTopOut = S.bTopOut; // EnterGround clears it
	S.Pos.Z = F + H; S.FloorZ = F;
	FVector InD = InputDir(I);
	FVector HV;
	const bool bHV = HDir(S.Vel, HV);
	const double HS = HLen(S.Vel);
	const bool bHolding = InD.SizeSquared() > 0.09 && bHV && FVector::DotProduct(InD.GetSafeNormal(), HV) > 0.3;
	const double Sev = FMath::Clamp((FMath::Max(Impact, FMath::Sqrt(FMath::Max(0.0, Drop) * 2 * G) * 0.8) - 9) / 28, 0.0, 1.0);
	EnterGround(N_idle);
	S.LandSeverity = Sev;
	if (Impact < 7) { S.LandLock = 0; if (Impact > 4) SetSub(N_landLight); S.Speed = HS; }
	else if (bHolding && HS > 8.5 && (Impact > 13 || Drop > 4)) { SetSub(N_landRoll); S.LandLock = 0.35; S.Speed = FMath::Min(HS * 0.85, 16.0); S.Facing = Yaw(HV); }
	else if (Impact < 13 && Drop < 6) { SetSub(N_landLight); S.LandLock = 0; S.Speed = bHolding ? HS : HS * 0.8; }
	else if (Impact < 23 && Drop < 16) { SetSub(N_landMedium); S.LandLock = bHolding ? 0.06 : 0.14; S.Speed = HS * (bHolding ? 0.7 : 0.45); }
	else { SetSub(N_landHard); S.LandLock = 0.42; S.Speed = 0; }
	if (bFromTopOut)
	{ // round 06: wall-run top-out lands in a planted crouch (hand down), holds, then settles up into the stand
		SetSub(N_landTopOut); S.LandLock = 0.34; S.Speed = FMath::Min(HS * 0.3, 2.0); S.LandSeverity = FMath::Max(Sev, 0.3);
		if (bHV) S.Facing = Yaw(HV);
	}
	S.bCharging = false; S.JumpCharge = 0;
	S.Carry = FVector::ZeroVector;
	Emit(N_land, S.Sub == N_idle ? 0.f : float(S.LandSeverity));
	{ // round 19 (owner: "landing in mid-air"): log every landing whose floor is not a building box / the ground mesh
		(void)TravWorld.GroundHeight(S.Pos.X, S.Pos.Y, F + 0.3);
		LastLandSrc = TravWorld.LastGroundSrc;
		// round 20: in the visual-triangle mode every floor a ray can find is a visible solid (src 4 = a visible mesh outside any building box)
		if (TravWorld.SolidMode != 2 && LastLandSrc != 2 && LastLandSrc != 3)
		{
			UE_LOG(LogWebHomage, Warning, TEXT("WH_TRAV landing on a non-traversal floor: (%.1f, %.1f) z %.2f src %d %s"), S.Pos.X, S.Pos.Y, F, LastLandSrc,
				LastLandSrc == 4 ? *TravWorld.LastGroundComp : TEXT(""));
		}
		else
		{
			UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV landing: (%.1f, %.1f) z %.2f src %d %s"), S.Pos.X, S.Pos.Y, F, LastLandSrc, LastLandSrc == 4 ? *TravWorld.LastGroundComp : TEXT(""));
		}
	}
}

// ------------------------------------------------------------------ corridor keeping (swing / air chains stay in the street canyon)
void UWebTraversalComponent::Corridor(double Hs, const FVector& InD)
{
	// round 08 (critic r07: swings carried him into the facades): canyon keeping in the WALLS' frame. 8 horizontal rays find
	// the facades around the body; along each wall's normal the approach speed is limited (>= WallClearance at the arc bottom)
	// and, between two opposite walls, a damped spring steers toward the canyon centre line. The r02-r07 version measured
	// "sideways" in the velocity's own frame (a drift that had already turned the heading read as zero) and pushed with no
	// damping, so chains zig-zagged into the facades and out through intersections.
	CorrT -= Hs;
	if (CorrT <= 0)
	{
		CorrT = 0.05; CorrN = 0;
		for (int32 K = 0; K < 8; ++K)
		{
			const double A = K * PI / 4.0;
			const FVector D(FMath::Cos(A), FMath::Sin(A), 0.0);
			FTravHit Hit;
			if (!TravWorld.Raycast(S.Pos, D, 40, Hit) || FMath::Abs(Hit.Normal.Z) > 0.5) continue;
			const FVector N = Flat(Hit.Normal).GetSafeNormal();
			// only facades BESIDE the travel direction (a block face ahead is FacadeAvoid's job; braking into it is not)
			FVector HV0;
			if (HDir(S.Vel, HV0) && FMath::Abs(FVector::DotProduct(N, HV0)) > 0.5) continue;
			const double Dist = FVector::DotProduct(S.Pos - Hit.Point, N);
			if (Dist < 0 || Dist > 40) continue;
			bool bMerged = false; // one entry per wall plane (nearest)
			for (int32 W = 0; W < CorrN; ++W)
			{
				if (FVector::DotProduct(CorrWallN[W], N) > 0.95) { if (Dist < CorrWallD[W]) CorrWallD[W] = Dist; bMerged = true; break; }
			}
			if (!bMerged && CorrN < 8) { CorrWallN[CorrN] = N; CorrWallD[CorrN] = Dist; ++CorrN; }
		}
	}
	if (CorrN == 0) return;
	const FVector InN = InD.SizeSquared() > 0.1 ? InD.GetSafeNormal() : FVector::ZeroVector;
	// centring between the nearest wall and an opposite one (the player steering sideways turns it off)
	int32 W1 = 0;
	for (int32 W = 1; W < CorrN; ++W) { if (CorrWallD[W] < CorrWallD[W1]) W1 = W; }
	const FVector N1 = CorrWallN[W1];
	const bool bSteerSide = FMath::Abs(FVector::DotProduct(InN, N1)) > 0.5;
	for (int32 W = 0; W < CorrN; ++W)
	{
		if (W == W1 || FVector::DotProduct(CorrWallN[W], N1) > -0.9 || bSteerSide) continue;
		const double Off = 0.5 * (CorrWallD[W] - CorrWallD[W1]);           // + = the centre is further out along N1
		// round 09 (critic r08: rail-straight centred chain): a bounded weave inside the corridor. While swinging, the target
		// line sits toward the ACTIVE anchor's side (WeaveK x the anchor's offset from the centre, <= WeaveAmp m); in the air the
		// release carries him across freely until he leaves the WeaveAmp + 2 m band. The hard clearance below still holds.
		double Target = 0.0; // offset from the centre line along N1
		bool bFree = false;
		if (S.Mode == EWebTravMode::Swing)
		{
			const double AOff = CorrWallD[W1] + FVector::DotProduct(S.Sw.Anchor - S.Pos, N1) - 0.5 * (CorrWallD[W] + CorrWallD[W1]);
			Target = FMath::Clamp(AOff * double(WeaveK), -double(WeaveAmp), double(WeaveAmp));
			if (bAltSwing) Target *= double(AltWeaveK); // round 24 (T7 "low point over the street centre", clear of the sidewalk trees)
		}
		else bFree = FMath::Abs(Off) < double(WeaveAmp) + 2.0;
		if (!bFree)
		{
			const double Want = FMath::Clamp((Off + Target) * 1.2, -8.0, 8.0), V = FVector::DotProduct(S.Vel, N1);
			S.Vel += N1 * ((Want - V) * (1 - FMath::Exp(-WallKeepRate * Hs)));
		}
		break;
	}
	// hard clearance per wall: approach speed <= 2.5 m/s per metre above WallClearance (a stick INTO the wall = wall-run wanted)
	for (int32 W = 0; W < CorrN; ++W)
	{
		const FVector& N = CorrWallN[W];
		if (CorrWallD[W] > 14 || FVector::DotProduct(InN, -N) > 0.6) continue;
		const double MaxIn = FMath::Max(0.0, (CorrWallD[W] - WallClearance) * 2.5), VIn = -FVector::DotProduct(S.Vel, N);
		if (VIn > MaxIn) S.Vel += N * (VIn - MaxIn);
	}
}

// ------------------------------------------------------------------ swing
// desired travel heading while airborne / swinging: camera forward turned by the stick
bool UWebTraversalComponent::SteerHeading(const FVector& InD, FVector& Out) const
{
	if (InD.SizeSquared() < 0.02) return false;
	Out = Flat(InD).GetSafeNormal();
	return true;
}

// look-ahead along the swing: a facade within ~0.9 s of travel bends the heading toward the canyon (rad this step)
double UWebTraversalComponent::FacadeAvoid(double Hs)
{
	AvoidT -= Hs;
	if (AvoidT <= 0)
	{
		AvoidT = 0.06; AvoidRate = 0;
		FVector HV;
		const double HS = HLen(S.Vel);
		if (HDir(S.Vel, HV) && HS > 6)
		{
			const double Look = FMath::Clamp(HS * 0.9, 8.0, 34.0);
			FTravHit Hit;
			if (TravWorld.Raycast(S.Pos, HV, Look, Hit) && FMath::Abs(Hit.Normal.Z) < 0.5)
			{
				const FVector& N = Hit.Normal;
				const double Into = -(HV.X * N.X + HV.Y * N.Y);
				if (Into > 0.25)
				{ // turn toward the wall tangent that is closer to the current heading
					const double TX = -N.Y, TY = N.X;
					double SD = Sgn(HV.X * TX + HV.Y * TY); if (SD == 0) SD = 1;
					const double Urgency = FMath::Clamp(1 - Hit.Distance / Look, 0.0, 1.0);
					const double Cur = Yaw(HV), Tgt = FMath::Atan2(TY * SD + N.Y * 0.3, TX * SD + N.X * 0.3);
					AvoidRate = FMath::Clamp(AngWrap(Tgt - Cur), -1.0, 1.0) * (0.6 + 2.2 * Urgency) * Into;
				}
			}
		}
	}
	return AvoidRate * Hs;
}

FVector UWebTraversalComponent::TravelDir(const FWebTravInput& I) const
{
	FVector HV;
	const bool bHV = HDir(S.Vel, HV);
	const FVector InD = InputDir(I);
	if (bHV && HLen(S.Vel) > 4) return HV;
	if (InD.SizeSquared() > 0.05) return InD.GetSafeNormal();
	if (bHV) return HV;
	return Cam ? Cam->ForwardFlat() : YawDir(S.Facing);
}

bool UWebTraversalComponent::TryStartSwing(const FWebTravInput& I)
{
	FVector Fwd = TravelDir(I);
	{ // the NEXT anchor follows the player's chosen heading
		FVector Want;
		if (SteerHeading(InputDir(I), Want) && FVector::DotProduct(Want, Fwd) > -0.5) Fwd = FMath::Lerp(Fwd, Want, 0.6).GetSafeNormal();
	}
	// round 09 (critic r08: rail-straight chain): anchors alternate sides — the search heading leans AnchorAltDeg toward the
	// side opposite the previous web (the weave then carries him across the corridor and the camera framing swaps)
	// (the search only — the swing plane keeps the travel heading Fwd)
	FVector FwdSearch = Fwd;
	if (S.LastAnchorSide != 0 && S.Mode == EWebTravMode::Air) FwdSearch = RotZ(Fwd, -S.LastAnchorSide * FMath::DegreesToRadians(double(AnchorAltDeg)));
	FVector InD = InputDir(I);
	FVector TurnV;
	const FVector* Turn = nullptr;
	if (InD.SizeSquared() > 0.1)
	{
		InD.Normalize();
		if (FVector::DotProduct(InD, Fwd) < 0.85) { TurnV = InD; Turn = &TurnV; }
	}
	const double HS = HLen(S.Vel);
	const double Fl = FloorAt(S.Pos.X, S.Pos.Y, FeetZ() + 0.1);
	FTravAnchor A;
	Anchors->Filter = [this](const FTravAnchor& C) { return AnchorStrandClear(C); };   // round 01 (W7)
	bool bFound = Anchors->Find(S.Pos, FwdSearch, Turn, S.Vel.Size(), Fl, A);
	Anchors->Filter = nullptr;
	// round 10 (critic r09 b 2.0 s: rope anchored below and behind the hero): a web never pulls from below / behind the body
	// round 19 (owner: "swing eventually breaks"): the behind-the-body rule only applies at speed (a slow fall / a hop off a wall or perch
	// has no meaningful travel direction; it refused every web behind the drift)
	if (bFound)
	{
		FVector HVg;
		if (!HDir(S.Vel, HVg)) HVg = Fwd;
		const bool bBehind = HLen(S.Vel) > 6.0 && FVector::DotProduct(Flat(A.Point - S.Pos), HVg) < 2.0;
		if (A.Point.Z < S.Pos.Z + AnchorMinAbove || bBehind) bFound = false;
	}
	// round 20 (probe x2 / s1: RMB on a wall kicked off but the street search found nothing for 0.5-1 s, so he re-stuck to the wall):
	// right after a wall cancel the web goes up the facade ahead of the kick
	bool bFacade = false;
	if (!bFound && bFacadeWeb && S.bWallCancel && S.Mode == EWebTravMode::Air && S.AirT < 0.8)
		bFound = bFacade = FacadeAnchor(A) && Anchors->Attached(A.Point, A.Normal);   // round 02: an unsupported facade anchor was dropped at the swing start and re-shot (the tip jumped)
	if (!bFound)
	{
		if (S.NoAnchorReach < 0 && (S.NoAnchorT < 0.07 || I.bSwingPressed))
		{ // round 01 (W10): a readable reach-and-miss -- the arm thrusts up and forward along the camera aim for ~0.25 s, no strand
			S.NoAnchorReach = 0; S.bNoAnchorRight = !S.bNoAnchorRight;
			const FVector CF = Cam ? Cam->Forward() : Flat(Fwd);
			S.NoAnchorAim = (CF + FVector(0, 0, 0.35)).GetSafeNormal();
		}
		Emit(N_noAnchor); S.NoAnchorT += 0.06;
		Anchors->Filter = nullptr;
		return false;
	}
	S.NoAnchorT = 0;
	{
		FVector HVx;
		if (!HDir(S.Vel, HVx)) HVx = Fwd;
		const double LatA = FVector::DotProduct(A.Point - S.Pos, FVector(-HVx.Y, HVx.X, 0));
		S.LastAnchorSide = FMath::Abs(LatA) > 2.0 ? (LatA > 0 ? 1 : -1) : S.LastAnchorSide;
	}
	// round 07 (critic r06 cadence): fired on the rise after a release, the web shoots and sticks at once, but the pendulum
	// starts at the top of the hop (vz <= PendingVz or PendingMax s later) so every swing still swoops down from its entry;
	// a taut rope at once flung him up the back of the new arc and stalled him ~1.3 s at its top
	if (S.Mode == EWebTravMode::Air && S.Vel.Z > PendingVz && !S.bGroundSwing)
	{
		S.bWebPending = true; S.PendingT = 0; S.PendingA = A; S.PendingFwd = Fwd; S.bPendingTurn = Turn != nullptr;
		if (Turn) S.PendingTurn = *Turn;
		S.bPendingRight = PickHandRight(A.Point, Fwd);
		S.PendingShoot = ShootDurFor(FVector::Dist(S.Pos, A.Point));
		WebAttach(S.bPendingRight, A.Point, S.PendingShoot);
		return true;
	}
	if (bFacade)
	{ // swing along the facade in the kick direction
		Fwd = FVector::DotProduct(Flat(A.Point - S.Pos), S.WallCancelDir) >= -1.0 ? S.WallCancelDir : -S.WallCancelDir; Turn = nullptr;
		UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV wall cancel: facade web at (%.1f, %.1f, %.1f), %.1f m up, %.1f m ahead"), A.Point.X, A.Point.Y, A.Point.Z,
			A.Point.Z - S.Pos.Z, FVector::DotProduct(Flat(A.Point - S.Pos), S.WallCancelDir));
	}
	S.bWallCancel = false;
	if (S.Mode == EWebTravMode::Air)
	{ // round 01 (W3): the body stays ballistic while the strand is in flight; the pendulum starts when the tip lands (StepAir resolves the pending web)
		S.bWebPending = true; S.PendingT = 0; S.PendingA = A; S.PendingFwd = Fwd; S.bPendingTurn = Turn != nullptr;
		if (Turn) S.PendingTurn = *Turn;
		S.bPendingRight = PickHandRight(A.Point, Fwd);
		S.PendingShoot = ShootDurFor(FVector::Dist(S.Pos, A.Point));
		WebAttach(S.bPendingRight, A.Point, S.PendingShoot);
		return true;
	}
	StartSwing(A, Fwd, Turn, HS);
	S.bGroundSwing = false;
	return true;
}

bool UWebTraversalComponent::FacadeAnchor(FTravAnchor& A) const
{
	const FVector N = S.WallCancelN, D = S.WallCancelDir;
	if (N.SizeSquared() < 0.5 || D.SizeSquared() < 0.5) return false;
	// (probe s1: a vertical run 4-14 m from the tower's corner found nothing ahead -- closer points, straight up, then back along the facade)
	for (double Ahead : { 12.0, 9.0, 16.0, 6.0, 3.0, 0.0, -6.0, -10.0 })
		for (double Up : { 11.0, 8.0, 15.0, 6.0 })
		{
			const FVector Q = S.Pos + D * Ahead + FVector(0, 0, Up) + N * 2.5;
			FTravHit FH;
			if (!TravWorld.Raycast(Q, -N, 6.0, FH) || FH.bGround || FVector::DotProduct(FH.Normal, N) < 0.7) continue;
			if (FH.Point.Z < S.Pos.Z + AnchorMinAbove) continue;
			const FVector From = S.Pos + N * 1.0, To = FH.Point + N * 0.3, Dd = To - From;
			FTravHit FH2;
			if (TravWorld.Raycast(From, Dd.GetSafeNormal(), FMath::Max(0.1, Dd.Size() - 0.8), FH2)) continue; // the strand must reach it
			A.Point = FH.Point; A.Normal = FH.Normal; A.Kind = FName(TEXT("wall")); A.L = FVector::Dist(S.Pos, FH.Point); A.Lat = 0.0;
			return true;
		}
	return false;
}

void UWebTraversalComponent::StartSwing(const FTravAnchor& A, const FVector& Fwd, const FVector* Turn, double HS)
{
	FSwing& Sw = S.Sw;
	struct FAltArcClear { bool& B; ~FAltArcClear() { B = false; } } AltArcClear{ bAltArcNext }; // round 24: one swing per altitude release
	bAltSwing = AltChain > 0.f && bAltArcNext;
	S.Chain = S.SinceSwing <= CHAIN_BUF ? FMath::Min(CHAIN_MAX, S.Chain + 1) : 0; // user r10g momentum chain
	Emit(N_swingChain, 0.f, 0.f, float(S.Chain));
	Sw.Anchor = A.Point; Sw.Normal = A.Normal; Sw.Kind = A.Kind; Sw.ModelT = 0.1;
	Sw.Dir = Turn ? FMath::Lerp(Fwd, *Turn, 0.6).GetSafeNormal() : Fwd;
	const double DX = A.Point.X - S.Pos.X, DY = A.Point.Y - S.Pos.Y;
	if (PivotLateralKeep < 1.f)
	{
		// Round 02 deep pendulum: build the virtual pivot so the arc through the body bottoms out low over the street
		// (per-swing random depth) — the web still draws to the real anchor A.Point.
		const FVector Fl = Flat(Sw.Dir).GetSafeNormal(), Rt(-Fl.Y, Fl.X, 0);
		const double Lat = FVector::DotProduct(A.Point - S.Pos, Rt);
		const double AheadA = FMath::Max(FVector::DotProduct(A.Point - S.Pos, Fl), 10.0);
		double FMaxD = -1e9;
		for (double K : { 0.0, 0.5, 1.0, 1.4 })
		{
			const FVector Q = S.Pos + Fl * (AheadA * K);
			FMaxD = FMath::Max(FMaxD, TravWorld.StreetHeight(Q.X, Q.Y, S.Pos.Z - 0.5)); // round 10: the street, not tree canopies / awnings
		}
		const double HEntry = S.Pos.Z - H - FMaxD;
		double BottomFeet = FMath::Lerp(double(ArcBottomMin), double(ArcBottomMax), double(Rng.FRand()));
		// round 07: + 0..ArcDropJitter m per swing so consecutive short arcs never repeat
		BottomFeet = FMath::Max(3.0, FMath::Min(BottomFeet, HEntry - MinArcDrop - double(ArcDropJitter) * Rng.FRand()));
		// round 09 (critic r08: identical swings): alternate a shallow and a deep arc — the low point moves >= 1 storey
		// between consecutive swings (ArcDropShallow / ArcDropDeep below the entry, 0-1.5 m jitter)
		++S.SwingIdx;
		{
			double Drop = (S.SwingIdx % 2 ? double(ArcDropShallow) : double(ArcDropDeep)) + 1.5 * Rng.FRand();
			BottomFeet = FMath::Max(double(ArcLowMin), HEntry - Drop); // round 10: 3 -> ArcLowMin (5 m)
			// round 24 (T7 altitude chain): a swing entered from the roofline altitude dives to AltLowLo..AltLowHi m over the street,
			// alternating the low / high half of the band (consecutive arcs differ by >= 1 m)
			// (hold B r24: only after an altitude release -- the opening swing of c / x2 / r1 from a 22 m spawn changed their r23 paths)
			if (AltChain > 0.f && bAltArcNext && !S.bSky && HEntry >= double(AltEntryMin))
			{
				const double Mid = 0.5 * double(AltLowLo + AltLowHi), Rj = double(Rng.FRand());
				BottomFeet = FMath::Max(double(ArcLowMin), S.SwingIdx % 2 ? FMath::Lerp(double(AltLowLo), Mid - 0.5, Rj) : FMath::Lerp(Mid + 0.5, double(AltLowHi), Rj));
			}
			// round 10: the first web after a sky launch dives back into the canyon: low point 1-3 storeys over the street
			if (S.bSky) BottomFeet = double(ArcLowMin) + double(SkyArcExtra) * Rng.FRand();
			// round 01 (Gap 2): the arc bottom clears the tree crowns on the way (the lowest point lies 0.4-1.4 x the anchor distance ahead): feet >= crown top + 1.5 m over the street
			for (double K : { 0.35, 0.7, 1.0, 1.4 })
			{
				const FVector Q = S.Pos + Fl * (AheadA * K);
				const double CT = TravWorld.CrownTopAt(Q.X, Q.Y, 5.0);
				if (CT > -1e8) BottomFeet = FMath::Max(BottomFeet, CT + 1.5 - FMaxD);
			}
		}
		double DZ = FMath::Max(A.Point.Z - S.Pos.Z, double(MinPivotRise));
		const double BottomZ = FMaxD + BottomFeet + H;
		// round 07: the rope cap varies per swing (up to RopeCapJitter shorter) so a long chain never repeats one arc / tempo
		// round 10: the web after a sky launch is a long rope (<= SkyRopeMax) that carries him from the fall back to the street
		const double RopeCap = S.bSky ? double(SkyRopeMax) : double(MaxArcRope) * (1.0 - double(RopeCapJitter) * Rng.FRand());
		// round 09: a high anchor would need a rope over the cap for the designed low point — lower the (virtual) pivot
		// instead, so the deep / shallow alternation survives (the web still draws to the real anchor)
		if (S.Pos.Z - BottomZ + DZ > RopeCap) DZ = FMath::Max(double(MinPivotRise), RopeCap - (S.Pos.Z - BottomZ));
		double L = FMath::Clamp(S.Pos.Z + DZ - BottomZ, DZ + 3.0, FMath::Max(RopeCap, DZ + 3.0));
		double DH = FMath::Sqrt(FMath::Max(L * L - DZ * DZ, 16.0));
		DH = FMath::Min(DH, S.bSky ? double(SkyRopeMax) : double(MaxPivotAhead));
		Sw.Pivot = S.Pos + Fl * DH + Rt * (Lat * PivotLateralKeep) + ZUP * DZ;
		const double LN = FVector::Dist(S.Pos, Sw.Pivot);
		Sw.Rope = LN; Sw.RopeTarget = LN;
	}
	else
	{
		// browser r13 flight dynamics: the physics pivot IS the web's anchor on the model
		Sw.Pivot = A.Point;
		const double L = FVector::Dist(S.Pos, Sw.Pivot);
		double FMax = -1e9;
		for (double K : { 0.0, 0.5, 1.0, 1.4 })
		{
			const double X = S.Pos.X + (Sw.Pivot.X - S.Pos.X) * K, Y = S.Pos.Y + (Sw.Pivot.Y - S.Pos.Y) * K;
			FMax = FMath::Max(FMax, FloorAt(X, Y, Sw.Pivot.Z - 2));
		}
		const double HEntry = S.Pos.Z - H - FMax;
		double BottomFeet = A.Kind == N_low ? 3.0 : FMath::Max(FMax < 1 ? 4.2 : 2.6, FMath::Clamp(8 + HEntry * 0.3, 11.0, 18.0));
		if (A.Kind != N_low) BottomFeet = FMath::Max(BottomFeet, HEntry - SWING_DIP); // user r10f
		Sw.RopeTarget = FMath::Max(4.0, FMath::Min(L, Sw.Pivot.Z - FMax - H - BottomFeet));
	}
	Sw.Rope = FVector::Dist(S.Pos, Sw.Pivot); Sw.T = 0; Sw.Tension = 0; Sw.TautT = 0; Sw.Y0 = S.Pos.Z;
	Sw.Kick = 0; Sw.KickCd = 0; Sw.bApexed = false; Sw.AngMax = -9; Sw.StallT = 0;
	// incoming velocity projection: perpendicular to the web at once (taut from the first frame), momentum conserved
	const FVector RD = (Sw.Pivot - S.Pos).GetSafeNormal();
	const double Sp = S.Vel.Size();
	{
		FVector Tan = S.Vel;
		const double VR = ProjectPerpendicular(Tan, RD);
		if (Tan.SizeSquared() > 0.01) S.Vel = Tan.GetSafeNormal() * (Sp * (VR < 0 ? 0.96 : 1.0));
		else if (Sp > 0.5) S.Vel = Sw.Dir * Sp;
	}
	if (HS < 11)
	{ // web yank when starting slow — along the arc tangent
		FVector YD = Sw.Dir - RD * FVector::DotProduct(Sw.Dir, RD);
		if (YD.SizeSquared() > 1e-3) S.Vel += YD.GetSafeNormal() * ((11 - HS) * 0.7);
	}
	CapSpeed();
	const FVector Right(-Sw.Dir.Y, Sw.Dir.X, 0);
	const double Lat = DX * Right.X + DY * Right.Y;
	if (S.bWebPending) Sw.bRightHand = S.bPendingRight; // the strand already shot on the rise (round 07)
	else
	{
		Sw.bRightHand = PickHandRight(A.Point, Fwd);
		WebAttach(Sw.bRightHand, Sw.Anchor, ShootDurFor(FVector::Dist(S.Pos, A.Point)));
	}
	S.bWebPending = false;
	SetMode(EWebTravMode::Swing, N_swingLow); S.Trick = NAME_None; S.bDive = false; S.bAirTrickUsed = false; S.AirTapT = -9;
	Emit(N_swingStart);
}

FVector UWebTraversalComponent::PivotFor(const FVector& AnchorPoint) const
{
	if (PivotLateralKeep >= 1.f) return AnchorPoint;
	const FVector Right(-S.Sw.Dir.Y, S.Sw.Dir.X, 0);
	const double Lat = FVector::DotProduct(AnchorPoint - S.Pos, Right);
	FVector P = AnchorPoint - Right * (Lat * (1.0 - PivotLateralKeep));
	if (PivotLateralKeep <= 0.f && MinPivotElevDeg > 0.f)
	{ // keep the virtual pivot ahead-and-above at a real swing angle (see MinPivotRise / MinPivotElevDeg)
		const FVector Fl = Flat(S.Sw.Dir).GetSafeNormal();
		// canyon keeping: above the anchor band the pivot sits higher so the (deeper) arc can dip back toward the band
		const double HAbove = FeetZ() - FloorAt(S.Pos.X, S.Pos.Y, FeetZ() + 0.1);
		const double Excess = FMath::Max(0.0, HAbove - FMath::Clamp(30.0 + HLen(S.Vel) * 0.25, 30.0, 40.0));
		double DZ = FMath::Max(P.Z - S.Pos.Z, double(MinPivotRise) + Excess * CanyonDipK);
		const double MaxDH = DZ / FMath::Tan(FMath::DegreesToRadians(double(MinPivotElevDeg)));
		const double DH = FMath::Clamp(FVector::DotProduct(P - S.Pos, Fl), -MaxDH, MaxDH);
		P = S.Pos + Fl * DH + ZUP * DZ;
	}
	return P;
}

double UWebTraversalComponent::SwingPhase() const
{
	const FSwing& Sw = S.Sw;
	const double Along = (S.Pos.X - Sw.Pivot.X) * Sw.Dir.X + (S.Pos.Y - Sw.Pivot.Y) * Sw.Dir.Y;
	const double Below = Sw.Pivot.Z - S.Pos.Z;
	return FMath::Clamp(FMath::Atan2(Along, FMath::Max(Below, 0.01)) / 1.25, -1.0, 1.0);
}

// signed rope angle from straight down, in the swing plane: 0 bottom, +pi/2 level in front, -pi/2 level behind
double UWebTraversalComponent::SwingAngle() const
{
	const FSwing& Sw = S.Sw;
	const double Along = (S.Pos.X - Sw.Pivot.X) * Sw.Dir.X + (S.Pos.Y - Sw.Pivot.Y) * Sw.Dir.Y;
	return FMath::Atan2(Along, Sw.Pivot.Z - S.Pos.Z);
}

void UWebTraversalComponent::StepSwing(double Hs, FWebTravInput& I)
{
	FSwing& Sw = S.Sw;
	Sw.T += Hs;
	// the web is released ONLY by letting go of the swing button (user feedback #4)
	if (!I.bSwing) { ReleaseSwing(false, I); return; }
	if (I.bJumpPressed)
	{ // user r4 #10 / r11: Space = let go AND launch along the current velocity with extra force + a pop up
		bLeaveSwingOK = true; ReleaseSwing(true, I); bLeaveSwingOK = false;
		S.SwingCooldown = 0.35; Emit(N_swingJump);
		return;
	}
	if (!AnchorCheck(Hs)) return;
	// ---- flight dynamics (webtension.js): project v perpendicular to R, then gravity + tension F_T = m g cos(theta) + m v^2/|R|
	{
		FVector RH = Sw.Pivot - S.Pos;
		const double RLen = RH.Size();
		RH = RLen > 1e-6 ? RH / RLen : ZUP;
		ProjectPerpendicular(S.Vel, RH);
		const double CosT = RH.Z;
		const double T = WEB_MASS * GS * CosT + WEB_MASS * S.Vel.SizeSquared() / FMath::Max(RLen, 1e-3);
		S.Vel.Z -= GS * Hs;
		S.Vel += RH * (T / WEB_MASS * Hs);
		Sw.FdTension = T;
	}
	const FVector RD = (Sw.Pivot - S.Pos).GetSafeNormal(); // R^ (body -> anchor)
	const FVector InD = InputDir(I);
	// STEERING (Insomniac): heading and velocity turn together about the vertical, velocity put back perpendicular to R at
	// the same speed (a conical turn around the anchor, no speed loss). Facades on the predicted arc bend the heading.
	FVector SideA(-Sw.Dir.Y, Sw.Dir.X, 0);
	{
		FVector Want;
		double DYaw = 0;
		if (SteerHeading(InD, Want))
		{
			const double Cur = Yaw(Sw.Dir), Tgt = Yaw(Want), D = AngWrap(Tgt - Cur);
			if (FMath::Abs(D) < 2.6) DYaw = FMath::Clamp(D, -1.7 * Hs, 1.7 * Hs) * FMath::Clamp(FMath::Abs(D) / 0.25, 0.0, 1.0);
		}
		DYaw += FacadeAvoid(Hs);
		if (FMath::Abs(DYaw) > 1e-6)
		{
			Sw.Dir = RotZ(Sw.Dir, DYaw).GetSafeNormal();
			if (PivotLateralKeep < 1.f) Sw.Pivot = S.Pos + RotZ(Sw.Pivot - S.Pos, DYaw); // the whole arc turns about the body
			const double Sp0 = S.Vel.Size();
			S.Vel = RotZ(S.Vel, DYaw);
			ProjectPerpendicular(S.Vel, RD);
			const double Sp1 = S.Vel.Size();
			if (Sp1 > 1e-3) S.Vel *= Sp0 / Sp1;
			SideA = FVector(-Sw.Dir.Y, Sw.Dir.X, 0);
		}
	}
	// never grind along a facade: a wall within ~2.5 m at the side pushes the body out toward the street
	{
		Sw.SideT -= Hs;
		if (Sw.SideT <= 0)
		{
			Sw.SideT = 0.05; Sw.bSideN = false;
			for (double SG : { 1.0, -1.0 })
			{
				FTravHit HH;
				if (TravWorld.Raycast(S.Pos, SideA * SG, 2.5, HH) && FMath::Abs(HH.Normal.Z) < 0.5)
				{
					Sw.SideN = Flat(HH.Normal).GetSafeNormal(); Sw.SideK = 1 - HH.Distance / 2.5; Sw.bSideN = true;
				}
			}
		}
		if (Sw.bSideN) S.Vel += Sw.SideN * (10 * Sw.SideK * Hs);
	}
	Corridor(Hs, InD);
	const double Spd = S.Vel.Size();
	// Insomniac "pump": ONLY with stick input along the swing while moving forward along the arc, strongest at the bottom,
	// never beyond the energy that reaches PUMP_MAX_ANG (a held swing without input is a pendulum)
	FVector Tan = S.Vel - RD * FVector::DotProduct(S.Vel, RD);
	const double Push = InD.SizeSquared() > 0.01 ? FMath::Clamp(FVector::DotProduct(InD, Sw.Dir) / FMath::Max(InD.Size(), 1e-3), 0.0, 1.0) : 0.0;
	if (Push > 0 && Tan.SizeSquared() > 0.01 && FVector::DotProduct(Tan, Sw.Dir) > 0 && Sw.TautT > 0)
	{
		const double E = 0.5 * Spd * Spd + GS * (S.Pos.Z - Sw.Pivot.Z);
		const double ECap = -GS * Sw.Rope * FMath::Cos(PUMP_MAX_ANG);
		const double Room = FMath::Clamp((ECap - E) / (GS * 1.5), 0.0, 1.0);
		const double Bottom = FMath::Max(0.0, RD.Z);
		S.Vel += Tan.GetSafeNormal() * (9 * Bottom * Bottom * Push * Room * Hs);
	}
	// climb assist (user r10f "web swings are supposed to give height each time")
	if (Push > 0 && Tan.SizeSquared() > 0.01 && S.Vel.Z > 0 && FVector::DotProduct(Tan, Sw.Dir) > 0 && Sw.TautT > 0.1)
	{
		const double Short = Sw.Y0 + SWING_GAIN - S.Pos.Z;
		if (Short > 0) S.Vel += Tan.GetSafeNormal() * (FMath::Min(Short, 3.0) * 4.5 * Push * Hs);
	}
	// first-arc carry: before the FIRST apex a web "motor" guarantees a minimum speed along the arc
	if (!Sw.bApexed)
	{
		const double Ang = SwingAngle();
		if (Ang > 0.15 && Ang < 1.0 && Sw.TautT > 0.05 && Sw.Tension > 0.05)
		{
			FVector TG = Sw.Dir * FMath::Cos(Ang) + ZUP * FMath::Sin(Ang);
			ProjectPerpendicular(TG, RD);
			if (TG.SizeSquared() > 1e-4) TG.Normalize();
			const double VT = FVector::DotProduct(S.Vel, TG);
			if (VT > -1.5)
			{
				const double U = FMath::Clamp((Ang - 0.15) / 0.85, 0.0, 1.0);
				const double VMin = FMath::Clamp(0.65 * FMath::Sqrt(GS * Sw.Rope), 10.0, 18.0) * U * U * (3 - 2 * U);
				if (VT < VMin) S.Vel += TG * FMath::Min(VMin - VT, 30 * Hs);
			}
		}
	}
	// aerodynamic drag (quadratic); a momentum chain slips through the air (r10g)
	S.Vel *= FMath::Max(0.0, 1 - SWING_DRAG * (1 - 0.08 * S.Chain) * Spd * Hs);
	if (Spd > 37 + 3 * S.Chain) S.Vel *= 1 - 0.3 * Hs; // soft top speed; a swing chain lifts it (r10g)
	// reel toward target length (lifts off the street), faster if the feet approach the floor
	const double Fl = FloorAt(S.Pos.X, S.Pos.Y, FeetZ() + 0.2);
	const double Clearance = FeetZ() - Fl;
	if (Clearance < 2.2 && S.Vel.Z < 0) Sw.RopeTarget = FMath::Min(Sw.RopeTarget, FMath::Max(3.0, Sw.Pivot.Z - (Fl + 2.4 + H)));
	{
		const double Want = Damp(Sw.Rope, Sw.RopeTarget, Clearance < 1.5 ? 10 : (Sw.Kind == N_low || Clearance < 4) ? 6 : 3.2, Hs);
		Sw.Rope = FMath::Max(Want, Sw.Rope - (Clearance < 3 ? 22 : 14) * Hs); // reel-in speed limit
	}
	// soft facade deflect: a facade within ~0.35 s of travel gradually turns the velocity along the wall (speed kept)
	{
		const double Sp = S.Vel.Size();
		if (Sp > 4)
		{
			const double Look = FMath::Min(12.0, Sp * 0.35 + 1);
			FTravHit Hit;
			if (TravWorld.Raycast(S.Pos, S.Vel / Sp, Look, Hit) && FMath::Abs(Hit.Normal.Z) < 0.5)
			{
				const double VN = FVector::DotProduct(S.Vel, Hit.Normal);
				if (VN < 0)
				{
					const double K = FMath::Clamp(1 - Hit.Distance / Look, 0.0, 1.0) * (1 - FMath::Exp(-10 * Hs));
					S.Vel += Hit.Normal * (-VN * K);
					const double L = S.Vel.Size();
					if (L > 1e-3) S.Vel *= Sp / L;
				}
			}
		}
	}
	CapSpeed();
	S.Pos += S.Vel * Hs;
	// rigid web constraint: back on |R| = rope, velocity perpendicular to the new R (the web both pulls and pushes)
	{
		FVector RR = S.Pos - Sw.Pivot;
		const double L = RR.Size();
		RR = L > 1e-6 ? RR / L : FVector(0, 0, -1);
		S.Pos = Sw.Pivot + RR * Sw.Rope;
		ProjectPerpendicular(S.Vel, RR);
	}
	// tension 0..1 for the web / pose / camera (F_T relative to 2.6 g of pull)
	const double Tension = FMath::Clamp(Sw.FdTension / (WEB_MASS * GS * 2.6), 0.0, 1.0);
	Sw.Tension = Damp(Sw.Tension, Tension, 12, Hs);
	if (Tension > 0.05) Sw.TautT += Hs;
	// wall contact: the web stays attached. A real impact becomes a "wall-skip" (velocity redirected along the facade)
	Sw.KickCd -= Hs; Sw.Kick = FMath::Max(0.0, Sw.Kick - Hs / 0.4);
	bool bMoved = false;
	FTravContact C;
	if (Collide(0.3, R + 0.22, C))
	{
		// round 10 (Manhattan integration: steering off the avenue into a block pinned him swinging against the facade for 10+ s):
		// the stick held INTO a wide facade he touches = the player wants onto that wall: let go of the web and wall-run up it
		// (roof top-out -> back into the chain). Grazes without that intent keep the wall-skip below.
		const FVector InN = InD.SizeSquared() > 0.1 ? InD.GetSafeNormal() : FVector::ZeroVector;
		// (a corner grazed while turning into a cross street is not that: the stick direction itself must be blocked within 12 m)
		FTravHit HStick;
		const bool bStickBlocked = InN.SizeSquared() > 0.5 && TravWorld.Raycast(S.Pos, InN, 12.0, HStick) && FMath::Abs(HStick.Normal.Z) < 0.5;
		if (bStickBlocked && FVector::DotProduct(InN, C.Normal) < -0.5 && S.WallCooldown <= 0 && C.Top - FeetZ() > 3.0 && WideWall(C.Normal, C.Point))
		{
			const double Sp = FMath::Max(12.0, S.Vel.Size());
			bLeaveSwingOK = true; WebRelease(); EnterWall(C.Normal, C.Point, true, Sp); bLeaveSwingOK = false;
			Emit(N_swingToWall);
			return;
		}
		bMoved = true;
		const double VN = FVector::DotProduct(S.Vel, C.Normal);
		if (VN < 0)
		{
			const double Sp0 = S.Vel.Size();
			S.Vel -= C.Normal * VN; // slide component
			if (-VN > 3.5 && Sw.KickCd <= 0 && Sp0 > 6)
			{
				FVector Slide = S.Vel.GetSafeNormal();
				FVector Along = Sw.Dir - C.Normal * FVector::DotProduct(Sw.Dir, C.Normal); Along.Z = 0;
				if (Along.SizeSquared() > 1e-4) Slide += Along.GetSafeNormal() * 0.45;
				Slide += ZUP * 0.35;
				Slide -= C.Normal * FVector::DotProduct(Slide, C.Normal);
				if (Slide.SizeSquared() < 1e-4) Slide = ZUP;
				Slide.Normalize();
				S.Vel = Slide * (Sp0 * 0.88) + C.Normal * FMath::Clamp(-VN * 0.12, 1.5, 3.0);
				Sw.KickCd = 0.35; Sw.Kick = 1;
				Emit(N_swingWallKick, float(FMath::Clamp(-VN / 30, 0.1, 0.6)));
			}
		}
	}
	// floor contact: never scrape — lift and keep going
	const double F2 = FloorAt(S.Pos.X, S.Pos.Y, FeetZ() + 0.4);
	if (FeetZ() < F2 + 0.3) { S.Pos.Z = F2 + 0.3 + H; if (S.Vel.Z < 0) S.Vel.Z = 0; bMoved = true; }
	if (bMoved)
	{ // the model's surface wins: the web takes the new length, velocity back perpendicular to R
		FVector RN = Sw.Pivot - S.Pos;
		const double LN = RN.Size();
		if (LN > 1e-3) { Sw.Rope = LN; Sw.RopeTarget = FMath::Min(Sw.RopeTarget, LN); ProjectPerpendicular(S.Vel, RN / LN); }
	}
	Sw.Phase = SwingPhase(); Sw.Angle = SwingAngle();
	Sw.AngMax = FMath::Max(Sw.AngMax, Sw.Angle);
	if (!Sw.bApexed && ((Sw.Angle < Sw.AngMax - 0.06 && Sw.AngMax > 0.2) || Sw.T > 4)) Sw.bApexed = true;
	// round 05 (critic r04 gap 3: a stalled swing micro-rocked for 4 s; "cap hangs at ~1.5 s, auto-continue the chain"): a swing that
	// sits near the bottom at walking speed with a taut web for HangCapS s is let go; the still-held button re-fires a fresh web
	// ~0.1 s later (StepAir's held-button search), so a dead hang never reads
	// round 06 (critic r05: s2 t=10.4-12.8 dangled plumb-static > 2 s and the cap never fired -- the swing re-walled before
	// Sw.T > 0.8 and the tension ramp sat under 0.1): earlier detection (T > 0.35, tension > 0.04), and a stall PUMP: while the
	// hang is detected the pendulum is pushed along its swing direction, so a valid slow hang rebuilds the arc instead of
	// sitting dead; the release + refire remains as the backstop
	if (HangCapS > 0.f)
	{
		const bool bStall = Sw.T > 0.35 && Sw.Tension > 0.04 && S.Vel.Size() < double(HangStallSpd) && FMath::Abs(Sw.Angle) < 0.45
			&& Sw.Kick <= 0.0 && HeightAboveFloor() > 6.0;
		Sw.StallT = bStall ? Sw.StallT + Hs : 0.0;
		if (bStall && Sw.TautT > 0.15)
		{
			FVector TDir = Sw.Dir - RD * FVector::DotProduct(Sw.Dir, RD);
			if (TDir.SizeSquared() > 1e-4)
			{
				TDir.Normalize();
				// pump past the bottom, whichever side he hangs on; stop adding energy once the arc is alive again
				const double Sign = Sw.Angle < -0.03 ? -1.0 : 1.0;
				S.Vel += TDir * (Sign * 14.0 * Hs);
			}
		}
		if (Sw.StallT > double(HangCapS))
		{
			UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV hang cap: swing stalled %.2f s at %.1f m/s -> release + refire"), Sw.StallT, S.Vel.Size());
			bLeaveSwingOK = true; ReleaseSwing(false, I); bLeaveSwingOK = false;
			S.SwingCooldown = 0.0; // the held button searches again at once (StepAir: AirT > 0.1 && vz < 5.5)
			return;
		}
	}
	if (Sw.Kick > 0.3) SetSub(N_wallKick);
	else SetSub(Sw.Phase < -0.28 ? N_swingLow : Sw.Phase < 0.28 ? N_swingBottom : N_swingHigh);
	Strands[0].Taut = float(Sw.Tension);
	// NO auto-release: while the button is held he keeps swinging — up past the anchor, over and around
	RopeWrap(Hs);
}

// the anchor must stay connected to a 3D model (re-checked every 0.1 s); if gone, re-shoot ahead, else let go
bool UWebTraversalComponent::AnchorCheck(double Hs)
{
	FSwing& Sw = S.Sw;
	Sw.ModelT -= Hs;
	if (Sw.ModelT > 0) return true;
	Sw.ModelT = 0.1;
	if (Anchors->Attached(Sw.Anchor, Sw.Normal)) return true;
	const double Fl = FloorAt(S.Pos.X, S.Pos.Y, FeetZ() + 0.1);
	FTravAnchor A;
	if (Anchors->Find(S.Pos, Flat(Sw.Dir).GetSafeNormal(), nullptr, S.Vel.Size(), Fl, A) && A.Point.Z > S.Pos.Z + 3)
	{
		UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV reanchor (anchor off the model) %.1f %.1f %.1f -> %.1f %.1f %.1f"), Sw.Anchor.X, Sw.Anchor.Y, Sw.Anchor.Z, A.Point.X, A.Point.Y, A.Point.Z);
		Reanchor(A);
		Emit(N_anchorLost, 1.f);
		return true;
	}
	Emit(N_anchorLost, 0.f);
	bLeaveSwingOK = true;
	WebRelease(); SetMode(EWebTravMode::Air, N_fall); S.AirT = 0; S.ApexZ = FeetZ(); S.SwingCooldown = 0.3;
	bLeaveSwingOK = false;
	return false;
}

// move the web to a new verified anchor mid-swing: velocity back onto the new arc at the same speed, web re-shot
void UWebTraversalComponent::Reanchor(const FTravAnchor& A)
{
	FSwing& Sw = S.Sw;
	Sw.Anchor = A.Point; Sw.Normal = A.Normal; Sw.Kind = A.Kind; Sw.ModelT = 0.1;
	Sw.Pivot = PivotFor(A.Point);
	const double LN = FVector::Dist(S.Pos, Sw.Pivot);
	Sw.Rope = LN; Sw.RopeTarget = FMath::Max(4.0, LN - 6);
	const double Sp = S.Vel.Size();
	ProjectPerpendicular(S.Vel, (Sw.Pivot - S.Pos) / FMath::Max(LN, 1e-3));
	const double Sp1 = S.Vel.Size();
	if (Sp1 > 1e-3) S.Vel *= Sp / Sp1;
	FWebTravStrand& St = Strands[0];
	if (St.bActive && St.ReleaseT < 0.f && St.Age >= St.ShootDur)
	{ // round 02: the landed strand slides to the new anchor over 0.15 s (it was re-shot: a full-length strand popping in a new direction)
		St.AnchorFrom = St.AnchorNow(); St.Anchor = Sw.Anchor; St.BlendT = 0.f;
	}
	else WebAttach(Sw.bRightHand, Sw.Anchor, FMath::Max(0.08, St.ShootDur));
}

// Rope wrap: a building now between body and anchor -> re-anchor ahead if possible, else wrap on that edge
void UWebTraversalComponent::RopeWrap(double Hs)
{
	FSwing& Sw = S.Sw;
	Sw.WrapT -= Hs;
	if (Sw.WrapT > 0) return;
	Sw.WrapT = 0.05;
	if (S.ModeT < 0.4) return;   // round 04: right after the attach the body may still sit beside the wall the (facade) anchor is on: not a wrap (it re-shot the web across the avenue)
	FVector D = Sw.Anchor - S.Pos;
	const double L = D.Size();
	if (L < 4) return;
	D /= L;
	FTravHit Hit;
	if (!TravWorld.Raycast(S.Pos, D, L - 1.5, Hit) || Hit.Distance < 1.5) return;
	// round 20 (probe f4 8.0 s: with visual-triangle solids a cornice / balcony 3-5 m below the anchor on its own facade "blocked" the strand ->
	// re-anchor onto a low point that turned a 37 m/s eastward swing 70 deg north, out of the city): the strand grazing the anchor's own facade
	// within RopeGuardNear m of the anchor is not a wrap, and a re-anchor may not turn the travel more than RopeGuardDeg
	if (bRopeGuard && Hit.Distance > L - double(RopeGuardNear)) return;
	{
		const double Fl = FloorAt(S.Pos.X, S.Pos.Y, FeetZ() + 0.1);
		FTravAnchor A;
		if (Anchors->Find(S.Pos, Flat(Sw.Dir).GetSafeNormal(), nullptr, S.Vel.Size(), Fl, A) && A.Point.Z > S.Pos.Z + 3)
		{
			bool bOk = true;
			if (bRopeGuard && S.Vel.SizeSquared() > 25.0)
			{ // predicted velocity on the new arc (same projection as Reanchor)
				const FVector Pv = PivotFor(A.Point);
				FVector V2 = S.Vel;
				ProjectPerpendicular(V2, (Pv - S.Pos).GetSafeNormal());
				const double Cos = FVector::DotProduct(V2.GetSafeNormal(), S.Vel.GetSafeNormal());
				bOk = Cos >= FMath::Cos(FMath::DegreesToRadians(double(RopeGuardDeg)));
				if (!bOk) UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV rope guard: re-anchor refused (would turn the travel %.0f deg)"), FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(Cos, -1.0, 1.0))));
			}
			if (bOk)
			{
				UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV reanchor (rope wrap, blocked at %.1f m) %.1f %.1f %.1f -> %.1f %.1f %.1f"), Hit.Distance, Sw.Anchor.X, Sw.Anchor.Y, Sw.Anchor.Z, A.Point.X, A.Point.Y, A.Point.Z);
				Reanchor(A); Emit(N_ropeReanchor);
				return;
			}
		}
	}
	if (Hit.bGround) return; // the strand may only wrap on a model, never on bare terrain
	const FVector P = Hit.Point + Hit.Normal * 0.06;
	Sw.Anchor = P; Sw.Normal = Hit.Normal; Sw.ModelT = 0.1;
	Sw.Pivot = PivotFor(P);
	const double LN = FVector::Dist(S.Pos, Sw.Pivot);
	Sw.Rope = LN; Sw.RopeTarget = FMath::Min(Sw.RopeTarget, LN);
	Strands[0].Anchor = P; // retarget, not re-shot
	Emit(N_ropeWrap);
}

// ---- release / air tricks. Selection follows the release trajectory; never the same trick twice in a row.
bool UWebTraversalComponent::AnchorStrandClear(const FTravAnchor& A) const
{ // the strand runs from the firing hand (shoulder height, to the anchor's side) to the anchor
	FVector HV;
	if (!HDir(S.Vel, HV)) HV = YawDir(S.Facing);
	const FVector Right(-HV.Y, HV.X, 0.0);
	const double Lat = FVector::DotProduct(A.Point - S.Pos, Right);
	const FVector Hand = S.Pos + FVector(0, 0, 0.5) + Right * (Lat > 0 ? 0.3 : -0.3);
	const FVector D = A.Point - Hand; const double L = D.Size();
	if (L < 1.0) return true;
	if (FVector::DotProduct((Hand - A.Point).GetSafeNormal(), A.Normal) < 0.3 && A.Normal.Z < 0.7) return false;   // a strand that skims the facade grazes its cornices / fire escapes
	{ // round 04: anchors above and ahead -- no level anchors, no side anchors (> ~75 deg off the travel heading at speed)
		const double Hz = FMath::Sqrt(D.X * D.X + D.Y * D.Y);
		if (D.Z < double(AnchorElevMin) * Hz) return false;
		if (HLen(S.Vel) > 8.0 && Hz > 1.0 && (D.X * HV.X + D.Y * HV.Y) / Hz < double(AnchorAheadMin)) return false;   // behind the travel line (side anchors up to 90 deg stay)
	}
	FTravHit Hit;
	if (TravWorld.Raycast(Hand, D / L, L - 1.0, Hit) && !Hit.bGround) return false;
	return !TravWorld.SegmentHitsCrown(Hand, A.Point);
}

bool UWebTraversalComponent::PickHandRight(const FVector& AnchorPt, const FVector& Fwd) const
{ // round 01 (W9): the anchor's side relative to the body's travel line (velocity heading; the steering blend of the anchor search is not the travel frame)
	FVector HV;
	if (!HDir(S.Vel, HV) || HLen(S.Vel) < 3.0) HV = Fwd;
	const double Lat = (AnchorPt.X - S.Pos.X) * -HV.Y + (AnchorPt.Y - S.Pos.Y) * HV.X;
	return FMath::Abs(Lat) > 0.2 ? Lat > 0 : !S.Sw.bRightHand;
}

double UWebTraversalComponent::StrandClearFraction(const FVector& A, const FVector& B) const
{ // the last 2.5 m before the anchor are not counted: the anchor sits ON the facade, its cornices / fire escapes are right there
	const FVector D = B - A; const double L = D.Size();
	if (L < 3.0) return 1.0;
	FTravHit Hit;
	return TravWorld.Raycast(A, D / L, L - 2.5, Hit) ? Hit.Distance / L : 1.0;
}

FName UWebTraversalComponent::ChooseTrick(const FWebTravInput& I)
{
	// round 11 (owner brief FLIPS_BRIEF.md): gymnast flip programs; a script / caller may request programs (comma list, cycled); owner r27: F picks from the 12-program cycle by stick direction via ChooseForInput
	if (!bLegacyTricks)
	{
		FVector HV0;
		if (!HDir(S.Vel, HV0)) HV0 = YawDir(S.Facing);
		const FVector InD0 = InputDir(I);
		S.TrickLat = -InD0.X * HV0.Y + InD0.Y * HV0.X;
		S.TrickSteep = S.Vel.Size() > 1 ? S.Vel.Z / S.Vel.Size() : 0;
		if (!I.FlipReq.IsEmpty())
		{
			TArray<FString> L;
			I.FlipReq.ParseIntoArray(L, TEXT(","), true);
			if (L.Num())
			{
				const FName N(*L[S.FlipCycle % L.Num()].TrimStartAndEnd());
				++S.FlipCycle;
				if (WebFlips::Find(N)) return FitFlip(N);
			}
		}
		const int32 K = S.AutoFlipK++ + int32(FlipKStart);
		const double StickFwd = InD0.X * HV0.X + InD0.Y * HV0.Y, StickLat = S.TrickLat;   // stick relative to travel (2D)
		float AirS;
		if (S.bSky) AirS = 0.f;   // sky launches are solved for their own air
		else if (bFlowChoose) { if (HeightAboveFloor() < FlipFloorClear) return NAME_None; AirS = 0.f; }
		else { AirS = float(AirTimeToClear() - double(FlipCatchRoom)); if (AirS <= 0.05f) return NAME_None; }
		const FName Pick = WebFlips::ChooseForInput(float(StickFwd), float(StickLat), K, AirS, S.LastTrickName);
		UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV flip choice: stick fwd %.2f lat %.2f (in %.2f %.2f, travel %.2f %.2f), air %.2f s, K %d -> %s"), StickFwd, StickLat, InD0.X, InD0.Y, HV0.X, HV0.Y, AirS, K, *Pick.ToString());
		return Pick;
	}
	const double Sp = S.Vel.Size(), HS = HLen(S.Vel), VY = S.Vel.Z, Steep = Sp > 1 ? VY / Sp : 0;
	FVector HV;
	if (!HDir(S.Vel, HV)) HV = YawDir(S.Facing);
	const FVector InD = InputDir(I);
	const double Lat = -InD.X * HV.Y + InD.Y * HV.X; // stick component to the RIGHT of travel (+) / left (-)
	double W[4] = { 1, 1, 1, 0.7 }; // tuckFlip, layout, corkscrew, scissor
	if (Steep < 0.3) { W[0] += 2.2; W[2] += 1.4; W[1] = 0.6; }
	else if (Steep > 0.55) { W[1] += 2.4; W[0] = 0.25; W[3] = 0.4; }
	if (HS > 22) { W[0] += 1; W[2] += 0.6; }
	if (VY < -2) W[1] = 0.3;
	if (VY < -5) { W[1] = 0.1; W[0] += 1; }
	if (FMath::Abs(Lat) > 0.35) W[2] += 2;
	for (int32 K = 0; K < 4; ++K) { if (TRICKS[K].Name == S.LastTrickName) W[K] = 0; }
	double Tot = 0;
	for (double V : W) Tot += V;
	double RR = Rng.FRand() * Tot;
	FName Name = TRICKS[0].Name;
	for (int32 K = 0; K < 4; ++K) { RR -= W[K]; if (RR <= 0) { Name = TRICKS[K].Name; break; } }
	S.TrickLat = Lat; S.TrickSteep = Steep;
	return Name;
}

// round 11 (f4 capture: a 2 s program from a low plain release landed him on the street mid-flip): a program only starts when
// the predicted fall to FlipFloorClear m over the floor (ballistic, G) leaves room for it up to its reach + FlipCatchRoom s;
// otherwise the longest program that fits (backSingle, then nothing: NAME_None = plain release)
double UWebTraversalComponent::AirTimeToClear() const
{
	const double H0 = HeightAboveFloor() - double(FlipFloorClear), Vz = S.Vel.Z;
	if (H0 <= 0.0) return 0.0;
	return (Vz + FMath::Sqrt(FMath::Max(0.0, Vz * Vz + 2.0 * G * H0))) / G;
}

FName UWebTraversalComponent::FitFlip(FName Want) const
{
	if (S.bSky) return Want; // sky launches are solved for their own long air (roofline apex, hang)
	// round 13: a flow flip's climb is solved so the catch window opens FlowCatchRise m ABOVE the release (the lowest point of the
	// program is the release itself): it only needs the release to be FlipFloorClear m over the floor (r13 probe: the ballistic test
	// swapped every program for backSingle at the 9-14 m releases of the chain)
	if (bFlowChoose) return HeightAboveFloor() >= double(FlipFloorClear) ? Want : NAME_None;
	const double Air = AirTimeToClear();
	auto Need = [](const FWebFlipProgram* P) { return P ? double(P->CatchT()) : 1e9; };
	const FWebFlipProgram* P = WebFlips::FindBase(Want);
	if (P && Need(P) * 1.18 + double(FlipCatchRoom) <= Air) return Want; // round 19: room for the longest variant
	const FName Short(TEXT("backSingle"));
	if (Need(WebFlips::FindBase(Short)) * 1.18 + double(FlipCatchRoom) <= Air) return Short;
	return NAME_None;
}

void UWebTraversalComponent::StartTrick(FName Name)
{
	if (Name.IsNone()) return;
	if (const FWebFlipProgram* FP0 = WebFlips::FindBase(Name))
	{ // round 11: flip program — its length is the trick; boost at 30 % of the first shape
		// round 19 (critic r18 "every program is a replay"): this instance's variant -- a fast release spins quicker (shorter), a high apex
		// has time for a slower, more extended program; + / - 5 % jitter; segments and arm / leg timing vary inside it (WebFlips::MakeVariant)
		const double Sp = S.Vel.Size(), ApexH = HeightAboveFloor() + FMath::Max(0.0, S.Vel.Z) * FMath::Max(0.0, S.Vel.Z) / (2.0 * G);
		const double Sc = 1.0 - 0.10 * FMath::Clamp((Sp - 24.0) / 12.0, -1.0, 1.0) + 0.08 * FMath::Clamp((ApexH - 18.0) / 15.0, -1.0, 1.0) + 0.05 * (2.0 * FlipRng.FRand() - 1.0);
		const FWebFlipProgram* FP = WebFlips::MakeVariant(Name, float(Sc), uint32(++FlipVarCount * 7919 + FlipRng.RandHelper(100000)));
		if (!FP) FP = FP0;
		UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV flip variant %s #%d: release %.1f m/s, apex ~%.1f m -> x%.3f (%.2f s, lead %.3f lag %.3f)"),
			*Name.ToString(), FlipVarCount, Sp, ApexH, FP->Scale, FP->Dur(), FP->Lead, FP->Lag);
		S.Trick = Name; S.LastTrickName = Name;
		S.TrickSide = FMath::Abs(S.TrickLat) > 0.35 ? Sgn(S.TrickLat) : 1.0; // corkscrew twist direction toward the stick
		S.TrickDur = FP->Dur(); S.TrickSnapT = 0.3 * FP->Segs[0].Dur; S.bTrickBoosted = false; S.bTrickNoUp = false;
		SetSub(N_trick);
		return;
	}
	const FTrickDef* D = TrickDef(Name);
	if (!D) return;
	const double Lat = S.TrickLat;
	S.Trick = Name; S.LastTrickName = Name;
	// side: layout +1 front flip / -1 back flip; corkscrew rolls / drifts toward the stick
	if (Name == N_layout) S.TrickSide = (S.TrickSteep > 0.45 ? -1 : 1) * (Rng.FRand() < 0.2 ? -1 : 1);
	else S.TrickSide = FMath::Abs(Lat) > 0.35 ? Sgn(Lat) : (Rng.FRand() < 0.5 ? 1 : -1);
	S.TrickDur = D->Dur; S.TrickSnapT = D->Dur * D->Snap; S.bTrickBoosted = false; S.bTrickNoUp = false;
	SetSub(N_trick);
}

void UWebTraversalComponent::TrickBoost(const FWebTravInput& I)
{
	const FTrickDef* D = TrickDef(S.Trick);
	S.bTrickBoosted = true;
	if (const FWebFlipProgram* FP = WebFlips::Find(S.Trick))
	{ // round 11: flip programs give a small forward push + hang (no steering)
		const double Sp0 = S.Vel.Size();
		FVector HV;
		if (!HDir(S.Vel, HV)) HV = YawDir(S.Facing);
		S.Vel.X += HV.X * FP->Boost * ReleaseBoostMul; S.Vel.Y += HV.Y * FP->Boost * ReleaseBoostMul;
		if (!S.bTrickNoUp) S.Vel.Z += FP->Up * ReleaseBoostMul;
		const double Lim = FMath::Max(VmaxC(), Sp0), Sp = S.Vel.Size();
		if (Sp > Lim) S.Vel *= Lim / Sp;
		Emit(N_trickBoost, 0.f, float(S.Vel.Size() - Sp0));
		return;
	}
	if (!D) return;
	const double K = ReleaseBoostMul;
	const double Sp0 = S.Vel.Size();
	FVector HV;
	if (!HDir(S.Vel, HV)) HV = YawDir(S.Facing);
	if (D->Steer > 0)
	{ // corkscrew: the roll turns the heading toward the stick (up to D.steer rad)
		const FVector InD = InputDir(I);
		if (InD.SizeSquared() > 0.09)
		{
			const double Dd = AngWrap(Yaw(InD) - Yaw(HV)), A = FMath::Clamp(Dd, -D->Steer, D->Steer);
			const double HS = HLen(S.Vel), NA = Yaw(HV) + A;
			S.Vel.X = FMath::Cos(NA) * HS; S.Vel.Y = FMath::Sin(NA) * HS; HV = YawDir(NA);
		}
	}
	S.Vel.X += HV.X * D->Boost * K; S.Vel.Y += HV.Y * D->Boost * K;
	if (!S.bTrickNoUp) S.Vel.Z += D->Up * K;
	if (D->Side > 0 && FMath::Abs(S.TrickLat) > 0.35)
	{
		const double SD = S.TrickSide;
		S.Vel.X += -HV.Y * D->Side * SD * K; S.Vel.Y += HV.X * D->Side * SD * K;
	}
	const double Lim = FMath::Max(VmaxC(), Sp0), Sp = S.Vel.Size();
	if (Sp > Lim) S.Vel *= Lim / Sp;
	Emit(N_trickBoost, 0.f, float(S.Vel.Size() - Sp0));
}

double UWebTraversalComponent::SkyRoofOverStreet() const
{
	FVector HV;
	if (!HDir(S.Vel, HV)) return -1.0;
	const double Roof = RoofBesideAhead(HV);
	return Roof < -0.5 ? -1.0 : Roof - TravWorld.StreetHeight(S.Pos.X, S.Pos.Y, FeetZ() + 0.1);
}

double UWebTraversalComponent::RoofBesideAhead(const FVector& Dir, double Ahead) const
{
	// Per side and per sample 10, 20 .. Ahead m along the path: a horizontal ray finds the street wall (<= 40 m out), a ray
	// straight down from 250 m above, 2.5 m inside that facade, finds the roof there (a tower set back further than 2.5 m reads
	// as its podium roof: the street wall's roofline). Side roofline = the LOWEST sample (the part of the block he can top);
	// cross streets (no wall hit) are skipped. Result = the lower side. (Box AABBs were tried first: rotated / merged boxes
	// reported 225 m towers for a 45 m street wall.)
	FVector F = Flat(Dir);
	if (F.SizeSquared() < 1e-4) return -1.0;
	F.Normalize();
	const FVector Rt(-F.Y, F.X, 0);
	double Top[2] = { -1.0, -1.0 };
	for (double D = 10.0; D <= Ahead + 1e-3; D += 10.0)
	{
		const FVector P = S.Pos + F * D;
		for (int32 Side = 0; Side < 2; ++Side)
		{
			const FVector SD = Rt * (Side ? 1.0 : -1.0);
			FTravHit Hw;
			if (!TravWorld.Raycast(P, SD, 40.0, Hw) || FMath::Abs(Hw.Normal.Z) > 0.5 || Hw.bGround) continue;
			const FVector Q = Hw.Point + SD * 2.5;
			FTravHit Hr;
			if (!TravWorld.Raycast(FVector(Q.X, Q.Y, S.Pos.Z + 250.0), FVector(0, 0, -1), 500.0, Hr) || Hr.bGround) continue;
			const double Roof = Hr.Point.Z;
			if (Roof < S.Pos.Z - 30.0) continue;
			Top[Side] = Top[Side] < 0.0 ? Roof : FMath::Min(Top[Side], Roof);
			if (bRoofDebug) UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV roof sample %.0f m side %d wall %.1f m roof %.1f"), D, Side, Hw.Distance, Roof);
		}
	}
	if (Top[0] < 0.0) return Top[1];
	if (Top[1] < 0.0) return Top[0];
	return FMath::Min(Top[0], Top[1]);
}

double UWebTraversalComponent::FlowRoofTarget(const FVector& Dir, double* OutRoofOverStreet) const
{
	// round 17 (TC8): per street side, the HIGHEST roof inside the FlowRoofR m half-disc on that side of the travel direction (down-rays on
	// a 5 m grid, the same measure as roof_check.py on the engine heightmap); tops under FlowRoofMinH m over the street are street trees /
	// awnings (r15 probe) and count as low. A side with nothing taller is "low" = FlowRoofMinH. The LOWER side is the roofline the apex
	// must clear. (A first version sampled the street wall with horizontal rays: at 8 m they hit the tree canopy, found no roof on the
	// low side and used the 90 m side.)
	FVector F = Flat(Dir);
	if (F.SizeSquared() < 1e-4) return -1.0;
	F.Normalize();
	const FVector Rt(-F.Y, F.X, 0);
	const double Street = TravWorld.StreetHeight(S.Pos.X, S.Pos.Y, FeetZ() + 0.1);
	const double Low = Street + double(FlowRoofMinH);
	double Top[2] = { Low, Low };
	const double RR = double(FlowRoofR);
	// the flip travels ~1 s of horizontal speed before its apex: the region is the capsule of radius RR around that stretch
	const double Dap = FMath::Min(40.0, HLen(S.Vel) * 1.0);
	for (double A = -RR; A <= Dap + RR + 1e-3; A += 5.0)
	{
		const double Ac = FMath::Clamp(A, 0.0, Dap);
		for (double L = -RR; L <= RR + 1e-3; L += 5.0)
		{
			if ((A - Ac) * (A - Ac) + L * L > RR * RR || FMath::Abs(L) < 2.0) continue;
			const FVector Q = S.Pos + F * A + Rt * L;
			FTravHit Hr;
			if (!TravWorld.Raycast(FVector(Q.X, Q.Y, S.Pos.Z + 250.0), FVector(0, 0, -1), 500.0, Hr) || Hr.bGround) continue;
			const int32 Side = L > 0.0 ? 1 : 0;
			Top[Side] = FMath::Max(Top[Side], Hr.Point.Z);
		}
	}
	const double Roof = FMath::Min(Top[0], Top[1]);
	if (OutRoofOverStreet) *OutRoofOverStreet = Roof - Street;
	return Roof + double(FlowRoofOver) + double(FlowApexMargin);
}

double UWebTraversalComponent::FlowApexGap() const
{
	if (S.Clock - GapCacheT < 0.1) return GapCacheV;
	GapCacheT = S.Clock;
	// the route direction (facing), not the instantaneous velocity: on the rising front of a swing / a wall kick the velocity can point
	// across the street and the capsule then lay over the tall blocks (r17 probe s2: "roofline 94 m" over a 20 m street side)
	const double T = FlowRoofTarget(RouteDir.IsNearlyZero() ? YawDir(S.Facing) : RouteDir);
	GapCacheV = T < 0.0 ? -1e9 : T - S.Pos.Z;
	return GapCacheV;
}

bool UWebTraversalComponent::CatchReachable(double Dur) const
{
	if (!Anchors) return true;
	if (S.Clock - CatchCacheT < 0.1) return bCatchCacheV;
	CatchCacheT = S.Clock;
	const FVector Vh(S.Vel.X, S.Vel.Y, 0.0);
	if (Vh.Size() < 2.0) { bCatchCacheV = true; return true; }
	// the catch is searched the way TryStartSwing will search it: from the predicted body position (the release turns the swing's climb into
	// forward speed: the flight runs at ~ the FULL speed, r18 probe f4 4th flip: vx 34 / vz 31 before the release, vx 50 after) in the program's final reach (the search opens
	// at CatchT; a catch within ~0.3 s of it reads as continuous), ~2 m under the release height (the flow apex climb and the fall after it), along
	// the travel heading leaned AnchorAltDeg away from the previous web's side, and the anchor must be AnchorMinAbove over the body and ahead.
	// Any of the three points attaching counts. (A single point at the program end, along the plain heading, blocked a flip that caught in r17 f1
	// and passed the f4 4th flip that did not.)
	bCatchCacheV = false;
	const FVector Fwd = Vh.GetSafeNormal();
	const FVector FwdSearch = S.LastAnchorSide != 0 ? RotZ(Fwd, -S.LastAnchorSide * FMath::DegreesToRadians(double(AnchorAltDeg))) : Fwd;
	for (const double Tq : { Dur - 0.1, Dur + 0.05, Dur + 0.2 })
	{
		const FVector P = S.Pos + Fwd * (S.Vel.Size() * Tq * double(CatchSpeedK)) - FVector(0, 0, 2.0);
		const double Fl = FloorAt(P.X, P.Y, P.Z - H + 0.1);
		FTravAnchor A;
		if (Anchors->Find(P, FwdSearch, nullptr, S.Vel.Size(), Fl, A) && A.Point.Z >= P.Z + AnchorMinAbove
			&& FVector::DotProduct(Flat(A.Point - P), Fwd) >= 2.0) { bCatchCacheV = true; break; }
	}
	return bCatchCacheV;
}

double UWebTraversalComponent::AltVzFor(double D)
{ // round 24: G until |vz| < 3.5 m/s, then the 0.55 x G apex hang (StepAir)
	const double Vh = 3.5, HangH = Vh * Vh / (2.0 * G * 0.55);
	return FMath::Sqrt(2.0 * G * FMath::Max(0.0, D - HangH) + Vh * Vh);
}

double UWebTraversalComponent::FlowApexGain(double Vz0, const FWebFlipProgram* FP) const
{
	// under FlowFlipGK x G; the program's Up boost lands at 0.3 x its first segment
	const double GF = G * double(FlowFlipGK);
	const double Tb = FP && FP->Segs.Num() > 0 ? 0.3 * double(FP->Segs[0].Dur) : 0.0;
	const double Up = FP ? double(FP->Up) * ReleaseBoostMul : 0.0;
	const double Zb = Vz0 * Tb - 0.5 * GF * Tb * Tb, V1 = Vz0 - GF * Tb;
	if (V1 <= 0.0) return FMath::Max(Vz0 * Vz0 / (2.0 * GF), Zb + FMath::Square(FMath::Max(0.0, V1 + Up)) / (2.0 * GF));
	return Zb + FMath::Square(V1 + Up) / (2.0 * GF);
}

double UWebTraversalComponent::TallestRoofAlong(const FVector& From, const FVector& Dir, double D0, double D1, double Rad) const
{
	// round 12: down-ray grid (5 m) over every point within R m of the horizontal segment D0..D1 m along Dir; building hits only
	FVector F = Flat(Dir);
	if (F.SizeSquared() < 1e-4) return -1.0;
	F.Normalize();
	const FVector Rt(-F.Y, F.X, 0);
	double Top = -1.0;
	const double Step = 5.0;
	for (double A = D0 - Rad; A <= D1 + Rad + 1e-3; A += Step)
	{
		const double Ac = FMath::Clamp(A, D0, D1);
		for (double L = -Rad; L <= Rad + 1e-3; L += Step)
		{
			if ((A - Ac) * (A - Ac) + L * L > Rad * Rad) continue;
			const FVector Q = From + F * A + Rt * L;
			FTravHit Hr;
			if (!TravWorld.Raycast(FVector(Q.X, Q.Y, From.Z + 350.0), FVector(0, 0, -1), 700.0, Hr) || Hr.bGround) continue;
			Top = FMath::Max(Top, Hr.Point.Z);
		}
	}
	return Top;
}

double UWebTraversalComponent::SkyV0For(double PeakOver, double Street, double FeetZNow) const
{
	const double Dh = FMath::Max(2.0, Street + PeakOver - FeetZNow);
	const double Vh = double(SkyHangVz), GRise = G * double(SkyRiseK), GHang = G * double(SkyHangK);
	const double HangH = Vh * Vh / (2.0 * GHang);
	const double V0 = FMath::Sqrt(FMath::Max(0.0, 2.0 * GRise * FMath::Max(0.0, Dh - HangH)) + Vh * Vh);
	return FMath::Clamp(V0, double(SkyLaunchVz), double(SkyLaunchVzMax));
}

double UWebTraversalComponent::SolveSkyPeak(const FVector& Pos, const FVector& HV, double HS, double Street, double RoofRule, double& TallOut, bool& bOk) const
{
	// round 12: the flip program is armed on the climb and plays from vz <= SkyTrickVz through the apex hang; the tallest roof
	// within SkyTallR of that stretch of the path (predicted from the climb time, horizontal speed <= 32 m/s: the air drag cap)
	// must sit SkyApexOver m under the apex. Two passes: the apex distance depends on the peak.
	const double GRise = G * double(SkyRiseK);
	const double HSe = FMath::Min(HS, 32.0);
	double Peak = FMath::Max(RoofRule, double(SkyPeakMin));
	TallOut = -1.0;
	const double FeetNow = Pos.Z - H;
	for (int32 Pass = 0; Pass < 2; ++Pass)
	{
		const double V0 = SkyV0For(Peak, Street, FeetNow);
		const double TStart = FMath::Max(0.0, V0 - double(SkyTrickVz)) / GRise;            // program start (vz = SkyTrickVz)
		const double D0 = HSe * TStart, D1 = D0 + HSe * 2.4;                                  // the longest program (backDouble 2.35 s)
		const double Tall = TallestRoofAlong(Pos, HV, D0, D1, double(SkyTallR));
		TallOut = Tall > -0.5 ? Tall - Street : -1.0;
		Peak = FMath::Max(FMath::Max(RoofRule, double(SkyPeakMin)), TallOut > -0.5 ? TallOut + double(SkyApexOver) : 0.0);
	}
	bOk = Peak <= double(SkyPeakMax) + 1e-3;
	return FMath::Clamp(Peak, double(SkyPeakMin), double(SkyPeakMax));
}

double UWebTraversalComponent::SkyPeakNeeded(bool& bReachable) const
{
	if (S.Clock - NeedCacheT < 0.1) { bReachable = bNeedCacheOk; return NeedCacheV; }
	NeedCacheT = S.Clock;
	FVector HV;
	if (!HDir(S.Vel, HV)) HV = YawDir(S.Facing);
	const double Street = TravWorld.StreetHeight(S.Pos.X, S.Pos.Y, FeetZ() + 0.1);
	const double Roof = RoofBesideAhead(HV);
	const double Rule = Roof > -0.5 ? Roof - Street + double(SkyRoofOver) : double(SkyPeakMin);
	double Tall = -1.0;
	NeedCacheV = SolveSkyPeak(S.Pos, HV, HLen(S.Vel) + SWING_JUMP, Street, Rule, Tall, bNeedCacheOk);
	bNeedCacheOk = NeedCacheV <= double(SkyPeakMax) - 4.0 && bNeedCacheOk; // margin: the release velocity differs a little
	bReachable = bNeedCacheOk;
	return NeedCacheV;
}

// round 13 / owner live fix: the flow flip's solved climb (the catch window opens FlowCatchRise m over the current height, or the lower roofline / apex rule); shared by the release flip (ReleaseSwing)
// and the mid-air F press (AirFlipPress). Requires S.Trick = a flip program (StartTrick) and bFlowTricks.
void UWebTraversalComponent::SolveFlowClimb(FName TrickN, const FVector& HV, bool bAltRel)
{
	const FWebFlipProgram* FP = WebFlips::Find(TrickN);
	if (!FP) return;
	const double Tc = FMath::Max(0.5, double(FP->CatchT()));
	const double GF = G * double(FlowFlipGK);
	const double Up = FP->Up * ReleaseBoostMul; // TrickBoost adds this at 0.3 x the first segment
	// round 15: rise to FlowRoofOver m over the lower street wall's roofline when that is within FlowRiseMax (sky behind by height)
	double Rise = double(FlowCatchRise);
	FlowRoofUsed = -1.0;
	if (FlowRoofOver > 0.f)
	{
		const double Street = TravWorld.StreetHeight(S.Pos.X, S.Pos.Y, FeetZ() + 0.1);
		const double Roof = RoofBesideAhead(HV, double(FlowRoofAhead));
		// (probe r15: street-tree canopies 9-15 m read as a "roofline" -- a roof counts only FlowRoofMinH m or more over the street)
		if (Roof > -0.5 && Roof - Street >= double(FlowRoofMinH))
		{
			FlowRoofUsed = Roof - Street;
			const double Need = Roof + double(FlowRoofOver) - FeetZ();
			if (Need > Rise && Need <= double(FlowRiseMax)) Rise = Need;
		}
	}
	FlowRiseUsed = Rise;
	double Vz0 = FMath::Clamp((Rise + 0.5 * GF * Tc * Tc) / Tc - Up * (Tc - 0.3 * FP->Segs[0].Dur) / Tc,
		double(FlowVzMin), double(FlowVzMax));
	FlowApexWant = 0.0;
	if (bFlowApexSolve)
	{ // round 17 (TC8): solve the climb for the program's APEX: hips at the lower roofline within FlowRoofR + FlowRoofOver (+ margin);
	  // no roofline here -> the r13 rule above. Gain at least FlowApexMin (the shape reads at the top of a rise, not on a fall).
		double RoofOver = -1.0;
		const double Target = FlowRoofTarget(RouteDir.IsNearlyZero() ? YawDir(S.Facing) : RouteDir, &RoofOver);
		const double WantRaw = FMath::Max(double(FlowApexMin), Target - S.Pos.Z);
		// round 24 (T7): the altitude chain's apex (hips at AltApexNow m over the floor) is a floor under the roofline rule
		// (hold C probe a: the flip cycle solved for the jittered 38 m apex ran 4.1 s release -> release; a flip takes the base apex)
		const double WantAlt = bAltRel ? FloorAt(S.Pos.X, S.Pos.Y, FeetZ() + 0.1) + double(AltApexH) + H - S.Pos.Z : -1e9;
		const bool bRoofOut = Target > 0.0 && WantRaw > FlowApexGain(double(FlowApexVzMax), FP) + 0.5;
		// TC8 "else it fires anyway": a roofline the capped climb cannot clear (Midtown canyons, 45-300 m walls) keeps the r13/r15 rule
		// (the r17 probe of a / b solved for 72-100 m rooflines and rocketed 20 m up for 2 s)
		if (bRoofOut && !bAltRel)
		{
			UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV flow apex: roofline %.1f m over the street out of reach (need %.1f m) -> r13 climb"), RoofOver, WantRaw);
		}
		else if (Target > 0.0 || bAltRel)
		{
			if (Target > 0.0 && !bRoofOut) FlowRoofUsed = RoofOver;
			const double Want = bAltRel ? FMath::Max(bRoofOut || Target <= 0.0 ? double(FlowApexMin) : WantRaw, WantAlt) : WantRaw;
			if (bAltRel) { AltApexWant = double(AltApexH); ++AltRelIdx; bAltArcNext = true; }
			double Lo = 0.0, Hi = bAltRel ? double(FMath::Max(FlowApexVzMax, AltFlowVzMax)) : double(FlowApexVzMax);
			if (FlowApexGain(Hi, FP) <= Want) Lo = Hi;
			else for (int32 It = 0; It < 30; ++It) { const double Md = 0.5 * (Lo + Hi); (FlowApexGain(Md, FP) < Want ? Lo : Hi) = Md; }
			Vz0 = FMath::Max(double(FlowVzMin), Hi);
			FlowApexWant = S.Pos.Z + FlowApexGain(Vz0, FP);
			FlowRiseUsed = Vz0 * Tc - 0.5 * GF * Tc * Tc + Up * FMath::Max(0.0, Tc - 0.3 * FP->Segs[0].Dur); // height at the catch window
		}
	}
	if (S.Vel.Z > Vz0)
	{ // the rest of the swing's climb goes forward (as the plain-release cap does)
		FVector HV0;
		if (!HDir(S.Vel, HV0)) HV0 = YawDir(S.Facing);
		const double Extra = S.Vel.Z - Vz0;
		S.Vel.X += HV0.X * Extra * 0.6; S.Vel.Y += HV0.Y * Extra * 0.6;
	}
	S.Vel.Z = Vz0;
	S.bFlowFlip = true;
	UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV flow flip %s at (%.1f, %.1f, %.1f) %.1f m over the floor: lower roofline %.1f m over the street, rise %.1f m, vz %.1f m/s, catch window at %.2f s"),
		*TrickN.ToString(), S.Pos.X, S.Pos.Y, FeetZ(), HeightAboveFloor(), FlowRoofUsed, FlowRiseUsed, Vz0, Tc);
	if (FlowApexWant > 0.0) UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV flow apex: hips %.1f -> apex %.1f (roofline %.1f m over the street)"), S.Pos.Z, FlowApexWant, FlowRoofUsed);
}

// owner live fix: F pressed in the air (not at a release) always plays a flip when the hero is FlipFloorClear m over the floor: the stick family picks the program (ChooseForInput, AirS 0),
// the same solved climb as the release flow flip opens the catch window above the current height. Below FlipFloorClear the refusal is logged.
bool UWebTraversalComponent::AirFlipPress(const FWebTravInput& I)
{
	const double HAF = HeightAboveFloor();
	if (HAF < double(FlipFloorClear))
	{
		UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV flip refused: low (h=%.1f m, needs %.1f)"), HAF, double(FlipFloorClear));
		return false;
	}
	const bool bFlow = bFlowTricks && !S.bSky && !bLegacyTricks;
	bFlowChoose = bFlow; const FName N = ChooseTrick(I); bFlowChoose = false;
	if (N.IsNone())
	{
		UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV flip refused: no program (h=%.1f m)"), HAF);
		return false;
	}
	StartTrick(N); S.bAirTrickUsed = true; S.bLastTrick = true;
	if (bFlow && WebFlips::Find(N))
	{
		FVector HV;
		if (!HDir(S.Vel, HV)) HV = YawDir(S.Facing);
		SolveFlowClimb(N, HV, false);
	}
	UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV air flip start %s at h=%.1f m, vz %.1f m/s"), *N.ToString(), HAF, S.Vel.Z);
	Emit(N_airTrick);
	return true;
}

void UWebTraversalComponent::ReleaseSwing(bool bJump, const FWebTravInput& I)
{
	// round 12 (critic r11): a trick pressed at a web release is a sky launch — the flip plays at an apex above the rooftops
	if (!bJump && bTrickLaunch && !bLegacyTricks && S.TrickBuf > 0) bJump = true;
	S.bFlowFlip = false;
	WebRelease();
	// release inertia (user feedback #4b): the velocity at release carries over 1:1, plus a small boost along it
	const double Sp = S.Vel.Size();
	if (Sp > 0.5) S.Vel *= (Sp + ReleaseBoost() + CHAIN_REL * S.Chain) / Sp; // + momentum chain (r10g)
	const double K = ReleaseBoost() / RELEASE_BOOST;
	FVector HV;
	if (!HDir(S.Vel, HV)) HV = YawDir(S.Facing);
	if (!bJump) S.Vel.Z = FMath::Min(FMath::Max(S.Vel.Z, REL_UP_VY), FMath::Max(S.Vel.Z + REL_UP * K, REL_UP * 0.75 * K));
	// near the street a release may still climb (16 m/s at <= 12 m, easing to ReleaseVzMax at 24 m): the chain gains the height
	// its next drop needs
	const double VzCap = FMath::Lerp(16.0, double(ReleaseVzMax), FMath::Clamp((HeightAboveFloor() - 12.0) / 12.0, 0.0, 1.0));
	auto PopForward = [&]()
	{ // round 07 (critic r06 cadence): a release is a forward pop, not a climb — the climb above ReleaseVzMax goes into forward
	  // speed (60 %), so the hop tops out ~0.4 s later and the next web's swing starts there (was 1-2 s ballistic arcs)
		if (S.Vel.Z <= VzCap) return;
		FVector HV0;
		if (!HDir(S.Vel, HV0)) HV0 = YawDir(S.Facing);
		const double Extra = S.Vel.Z - VzCap;
		S.Vel.Z = VzCap; S.Vel.X += HV0.X * Extra * 0.6; S.Vel.Y += HV0.Y * Extra * 0.6;
	};
	// round 24 (T7): the altitude chain solves a plain / flow release for a roofline apex instead (below, once the trick is known)
	// (probe r24 c / x2 / r1: a release TOWARD a nearby facade -- the player turned into the block to wall-run -- climbed 20 m up the wall
	//  instead of the r23 hop onto it; x2's wall kick then hid the hero behind the facade for 0.8 s): the roofline climb only applies when
	//  the street ahead is open for AltOpenAhead m at body height and AltOpenUp m above it)
	bool bAltRel = AltChain > 0.f && !bJump && !bLegacyTricks;
	if (bAltRel && AltOpenAhead > 0.f)
	{
		FVector HVo;
		if (!HDir(S.Vel, HVo)) HVo = YawDir(S.Facing);
		FTravHit OH;
		for (double Up : { 0.0, double(AltOpenUp) })
			if (TravWorld.Raycast(S.Pos + ZUP * Up, HVo, double(AltOpenAhead), OH) && FMath::Abs(OH.Normal.Z) < 0.5) { bAltRel = false; break; }
		if (!bAltRel) UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV alt release skipped: facade %.1f m ahead"), OH.Distance);
	}
	if (!bJump && !bAltRel) PopForward();
	const double AltApexNow = double(AltApexH) + double(AltApexJit) * double((AltRelIdx * 37) % 5) / 4.0; // m over the floor (feet)
	if (bJump)
	{ // user r11: Space-release = stronger forward push + a jump-off-the-web pop up
		S.Vel.X += HV.X * SWING_JUMP * K; S.Vel.Y += HV.Y * SWING_JUMP * K;
		S.Vel.Z = FMath::Min(SWING_JUMP_VY, FMath::Max(S.Vel.Z + SWING_JUMP_UP, SWING_JUMP_UP * 0.85));
		S.bJumpRelHold = true; // user r10c: no new web until the apex
		// round 10: jump-release with a trick pressed = sky launch (climb to the roofline, hang, chained tricks, dive back in)
		if (S.TrickBuf > 0)
		{
			S.bSky = true;
			// round 10 (T7): solve the launch for an apex just over the lower street wall's roofline beside the path ahead
			const double Street = TravWorld.StreetHeight(S.Pos.X, S.Pos.Y, FeetZ() + 0.1);
			bRoofDebug = true;
			const double Roof = RoofBesideAhead(HV);
			bRoofDebug = false;
			SkyRoofUsed = Roof > -0.5 ? Roof - Street : -1.0;
			// round 12: and SkyApexOver m over the tallest roof within SkyTallR m of the flip's stretch of the path
			const double Rule = Roof > -0.5 ? Roof - Street + double(SkyRoofOver) : double(SkyPeakMin);
			bool bReach = false;
			const double PeakOver = SolveSkyPeak(S.Pos, HV, HLen(S.Vel), Street, Rule, SkyTallUsed, bReach);
			SkyPeakWant = PeakOver;
			S.Vel.Z = SkyV0For(PeakOver, Street, FeetZ());
			Emit(N_skyLaunch, float(PeakOver), float(SkyRoofUsed));
			UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV sky launch at (%.1f, %.1f, %.1f): street %.1f, lower roofline %.1f m over it, tallest roof near the flip %.1f m, peak want %.1f m (%s), vz %.1f m/s"),
				S.Pos.X, S.Pos.Y, FeetZ(), Street, SkyRoofUsed, SkyTallUsed, PeakOver, bReach ? TEXT("clears") : TEXT("CAPPED"), S.Vel.Z);
		}
	}
	SetMode(EWebTravMode::Air, N_release); S.AirT = 0; S.ApexZ = FeetZ();
	S.SwingCooldown = 0.05; S.RelT = 0;
	// release trick (user r10): the common case (~80 %); a plain release never twice in a row. Needs room to play out.
	const double HF = HeightAboveFloor();
	const bool bRoom = S.bSky || (HF > 5 && S.Vel.Size() > 9 && (S.Vel.Z > -5 || HF > 14)); // round 12: a sky launch always has room (f4 probe: a launch off a roof skipped the arming and the buffered trick started on the climb)
	// round 04: tricks only on input (trick pressed up to 0.4 s before the release, or during the air phase below)
	FName TrickN = NAME_None; // round 11: FitFlip may answer "no room for any flip" -> plain release
	if (bRoom && S.TrickBuf > 0) { bFlowChoose = bFlowTricks && !bJump && !S.bSky && !bLegacyTricks; TrickN = ChooseTrick(I); bFlowChoose = false; S.TrickBuf = 0; }
	S.ArmedFlip = NAME_None;
	if (!TrickN.IsNone() && S.bSky && WebFlips::Find(TrickN))
	{ // round 12: armed on the climb, started at vz <= SkyTrickVz (StepAir) so the whole program plays in the apex hang
		S.ArmedFlip = TrickN; S.Trick = NAME_None; S.bLastTrick = true; // (no plain-release push: the program boosts at its snap)
	}
	else if (!TrickN.IsNone())
	{
		StartTrick(TrickN); S.bLastTrick = true;
		const FWebFlipProgram* FP = WebFlips::Find(TrickN);
		if (FP && bFlowTricks && !bJump && !S.bSky)
		{ // round 13: the program starts now; solve the climb so the catch window opens FlowCatchRise m over the release height
			SolveFlowClimb(TrickN, HV, bAltRel);
		}
	}
	else
	{
		S.Trick = NAME_None; S.bLastTrick = false; S.Vel.X += HV.X * REL_NOTRICK * K; S.Vel.Y += HV.Y * REL_NOTRICK * K;
		if (bAltRel)
		{ // round 24 (T7 altitude chain): solve the release for an apex AltApexNow m over the floor -- the velocity turns up toward it
		  // (speed kept, <= AltTurnDeg, horizontal >= AltHMin, vz <= AltVzMax); more climb than needed goes forward as the r07 pop
			const double D = AltApexNow - HeightAboveFloor();
			AltApexWant = AltApexNow; ++AltRelIdx; bAltArcNext = true;
			if (D <= 1.0) PopForward();
			else
			{
				const double VzW = FMath::Min(AltVzFor(D), double(AltVzMax));
				FVector HVa;
				if (!HDir(S.Vel, HVa)) HVa = YawDir(S.Facing);
				double Hh = HLen(S.Vel), Vz = S.Vel.Z;
				if (Vz > VzW) { Hh += (Vz - VzW) * 0.6; Vz = VzW; }
				else
				{
					const double Sp2 = Hh * Hh + Vz * Vz, Sp1 = FMath::Sqrt(Sp2);
					const double A0 = FMath::Atan2(Vz, FMath::Max(Hh, 1e-3));
					const double A1 = FMath::Min(A0 + FMath::DegreesToRadians(double(AltTurnDeg)), FMath::DegreesToRadians(80.0));
					Vz = FMath::Max(Vz, FMath::Min(VzW, Sp1 * FMath::Sin(A1)));
					Hh = FMath::Sqrt(FMath::Max(0.0, Sp2 - Vz * Vz));
					if (Hh < double(AltHMin) && Sp1 > double(AltHMin))
					{
						Hh = double(AltHMin); Vz = FMath::Max(S.Vel.Z, FMath::Sqrt(FMath::Max(0.0, Sp2 - Hh * Hh)));
					}
				}
				S.Vel = HVa * Hh + ZUP * Vz;
				UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV alt release at (%.1f, %.1f) %.1f m over the floor: apex want %.1f m, vz %.1f (need %.1f), hs %.1f m/s"),
					S.Pos.X, S.Pos.Y, HeightAboveFloor(), AltApexNow, Vz, AltVzFor(D), Hh);
			}
		}
	}
	if (bAltRel && !TrickN.IsNone() && !S.bFlowFlip) PopForward(); // (a non-flow trick keeps the r07 pop)
	S.bTrickNoUp = false; // user r10f: every release gains height again
	const double HS = HLen(S.Vel), HL = FMath::Max(VmaxC(), Sp);
	if (HS > HL) { S.Vel.X *= HL / HS; S.Vel.Y *= HL / HS; }
	Emit(N_release, bJump ? 1.f : 0.f);
}

// ------------------------------------------------------------------ wall
// is the contact a real facade (>= ~1 m wide, coplanar both sides)? Poles / posts are not wall-runnable.
bool UWebTraversalComponent::WideWall(const FVector& N, const FVector& Point) const
{
	const double TX = -N.Y, TY = N.X;
	int32 Ok = 0;
	for (double SD : { -1.0, 1.0 })
	{
		const FVector O(Point.X + N.X * 0.5 + TX * SD * 0.5, Point.Y + N.Y * 0.5 + TY * SD * 0.5, S.Pos.Z);
		FTravHit Hit;
		if (TravWorld.Raycast(O, FVector(-N.X, -N.Y, 0), 1.1, Hit) && FMath::Abs(Hit.Normal.Z) < 0.5 && Hit.Normal.X * N.X + Hit.Normal.Y * N.Y > 0.8) ++Ok;
	}
	return Ok == 2;
}

FVector UWebTraversalComponent::CleanWallNormal(const FVector& Pt, const FVector& RawN) const
{
	const FVector N = Flat(RawN).GetSafeNormal();
	if (TravWorld.SolidMode != 2 || N.IsNearlyZero()) return N;
	TArray<int32> L;
	TravWorld.Near(Pt.X, Pt.Y, 2.0, L);
	double Best = 1.5; FVector BN = N;
	for (int32 I : L)
	{
		const FTravBox& B = TravWorld.Boxes[I];
		if (Pt.Z < B.Min.Z - 1.0 || Pt.Z > B.Max.Z + 1.0) continue;
		const struct { FVector Nf; double D; bool bIn; } Faces[4] = {
			{ FVector(1, 0, 0), FMath::Abs(Pt.X - B.Max.X), Pt.Y >= B.Min.Y - 0.5 && Pt.Y <= B.Max.Y + 0.5 },
			{ FVector(-1, 0, 0), FMath::Abs(Pt.X - B.Min.X), Pt.Y >= B.Min.Y - 0.5 && Pt.Y <= B.Max.Y + 0.5 },
			{ FVector(0, 1, 0), FMath::Abs(Pt.Y - B.Max.Y), Pt.X >= B.Min.X - 0.5 && Pt.X <= B.Max.X + 0.5 },
			{ FVector(0, -1, 0), FMath::Abs(Pt.Y - B.Min.Y), Pt.X >= B.Min.X - 0.5 && Pt.X <= B.Max.X + 0.5 } };
		for (const auto& F : Faces)
		{
			if (F.bIn && F.D < Best && FVector::DotProduct(F.Nf, N) > 0.5) { Best = F.D; BN = F.Nf; }
		}
	}
	return BN;
}

bool UWebTraversalComponent::WallPlane(const FVector& N, FVector& OutN, FVector& OutPoint) const
{
	const FVector Lat(-N.Y, N.X, 0.0);
	int32 Nv = 0; double BestD = -1e9; FVector Sum = FVector::ZeroVector; FVector BestP = FVector::ZeroVector;
	for (double OZ : { 0.35, -0.5 })
		for (double OL : { -0.45, 0.0, 0.45 })
		{
			FTravHit Hit;
			const FVector O = S.Pos + Lat * OL + FVector(0, 0, OZ);
			if (!TravWorld.Raycast(O, -N, R + 0.9, Hit) || FMath::Abs(Hit.Normal.Z) > 0.5 || FVector::DotProduct(Flat(Hit.Normal).GetSafeNormal(), N) < 0.3) continue;
			++Nv; Sum += Flat(Hit.Normal).GetSafeNormal();
			const double D = FVector::DotProduct(Hit.Point - S.Pos, N); // most protruding = largest (least negative)
			if (D > BestD) { BestD = D; BestP = Hit.Point - Lat * OL; }
		}
	if (Nv < 2) return false;
	OutN = CleanWallNormal(BestP, Sum.GetSafeNormal());
	OutPoint = S.Pos + N * BestD; OutPoint.Z = S.Pos.Z;
	return true;
}

void UWebTraversalComponent::EnterWall(const FVector& N, const FVector& Point, bool bRun, double Speed)
{
	FWall& W = S.W;
	W.Normal = CleanWallNormal(Point, N); // round 20
	S.Pos.X = Point.X + W.Normal.X * (R + 0.02); S.Pos.Y = Point.Y + W.Normal.Y * (R + 0.02);
	W.RunV = bRun ? FMath::Clamp(FMath::Max(Speed * 0.8, S.Vel.Z), WALLRUN * 0.9, WALLRUN * 1.15) : FMath::Max(0.0, FMath::Min(8.0, S.Vel.Z)); // r9q
	W.bFast = bRun; S.Vel = FVector::ZeroVector; S.bDive = false; S.Trick = NAME_None;
	W.Up = ZUP; W.Off = 0; W.RunK = 0; W.SideUpK = 0; W.Dist = R + 0.02; W.Point = FVector(Point.X, Point.Y, S.Pos.Z);
	SetMode(EWebTravMode::Wall, bRun ? N_wallRun : N_crawl); S.bGrounded = false; S.DashCount = 0;
	Emit(N_wall, 0.f, 0.f, 1.f, bRun);
}

FVector UWebTraversalComponent::WallBasis(const FVector& N) const
{
	FVector Right = Cam ? Cam->RightFlat() : FVector(-N.Y, N.X, 0);
	Right -= N * FVector::DotProduct(Right, N);
	if (Right.SizeSquared() < 0.09) Right = FVector(N.Y, -N.X, 0); // camera looks along the wall: wall-right as seen from outside
	return Right.GetSafeNormal();
}

void UWebTraversalComponent::StepWall(double Hs, FWebTravInput& I)
{
	FWall& W = S.W;
	FVector& N = W.Normal;
	FVector Right = WallBasis(N);
	// user r9: ANY movement on a wall is the wall run; with no input he just clings in place
	bool bFast = I.bSprint || I.bSwing || I.Move.Size() > 0.2;
	double MX = I.Move.X, MY = I.Move.Y;
	// user r9: running sideways round a building — the held key keeps meaning "carry on the same way round"
	if (W.bLockDir)
	{
		if (Sgn(MX) == W.LockMx && FMath::Abs(MX) > 0.2)
		{
			if (FVector::DotProduct(Right, W.LockDir) * W.LockMx > 0.8) W.bLockDir = false;
			else Right = W.LockDir * W.LockMx;
		}
		else W.bLockDir = false;
	}
	if (bFast && FMath::Sqrt(MX * MX + MY * MY) < 0.2) MY = 1; // parkour held with no direction: run up
	// user r9w/r9z: wall-zip burst straight up (input-proof for the whole pull)
	double ZV = 0;
	if (S.Sub == N_wallZip)
	{
		W.ZipT += Hs;
		const double U = FMath::Clamp(W.ZipT / WZIP.Dur, 0.0, 1.0);
		ZV = WZIP.V0 + (WZIP.V1 - WZIP.V0) * U * U * (3 - 2 * U); MX = 0; MY = 1;
		if (W.bZipWeb && U >= WZIP.Snap) { W.bZipWeb = false; WebRelease(true); }
		if (U >= 1) { const bool bGo = I.bSprint && I.Move.Y > 0.2; W.RunV = bGo ? WALLRUN * 1.1 : 3; SetSub(bGo ? N_wallRun : N_crawl); }
	}
	W.Move = FVector2D(MX, MY);
	const double Len = FMath::Sqrt(MX * MX + MY * MY);
	if (Len > 1) { MX /= Len; MY /= Len; }
	double VX = (bFast ? WALLRUN : 4.2) * MX;
	const double VYIn = (bFast ? WALLRUN : 4.2) * MY; // user r9r
	// round 22: an upright side run (stick sideways) sheds the climb speed fast (rate WallSideClimbDamp, r21 3/s) so the run line levels out
	// along the facade in ~0.15 s instead of a 45 deg diagonal for half a second (the torso is upright: "above the run line" needs a level run)
	const bool bSideLevel = WallSideUpright > 0.5f && UWebTravAnimInstance::bWallGait && FMath::Abs(MY) <= 0.2 && FMath::Abs(MX) > 0.2;
	W.RunV = Damp(W.RunV, 0, bFast && MY > 0.2 ? 0.4 : FMath::Sqrt(MX * MX + MY * MY) < 0.2 ? 9 : bSideLevel ? double(WallSideClimbDamp) : 3, Hs);
	if (S.Sub == N_wallZip) { W.RunV = ZV; bFast = true; }
	const double VY = ZV != 0 ? ZV : FMath::Max(VYIn, MY >= -0.1 ? W.RunV : -1e9);
	// round 23 (director r23: vertical sprint torso 5-20 deg off wall-up; c climbed a 33 deg diagonal -- torso 28-35 deg): a vertical-dominant
	// fast run keeps its run line within WallVertMaxDeg of the wall's up axis (the sideways share of the stick is shed; side runs untouched)
	if (WallVertMaxDeg > 0.f && UWebTravAnimInstance::bWallGait && bFast && S.Sub != N_wallZip && MY > 0.2 && FMath::Abs(MY) >= FMath::Abs(MX) && VY > 1.0)
	{
		const double MaxX = VY * FMath::Tan(FMath::DegreesToRadians(double(WallVertMaxDeg)));
		VX = FMath::Clamp(VX, -MaxX, MaxX);
	}
	S.Vel = Right * VX + ZUP * VY;
	W.bFast = bFast && (FMath::Abs(VX) + FMath::Abs(VY) > 5);
	W.Phase += S.Vel.Size() * Hs / (W.bFast ? 2.6 : 1.2);
	const FName Sub2 = W.bFast ? (FMath::Abs(VY) >= FMath::Abs(VX) ? N_wallRun : N_wallRunSide) : N_crawl;
	if (S.Sub != N_wallZip && (S.Sub != N_cornerWrap || S.SubT > 0.3)) SetSub(Sub2);
	// round 20 (critic r19 side-run: body within 20 deg of the run direction, head leading): the body axis follows the run direction 2x faster
	if (S.Vel.SizeSquared() > 0.04) W.Up = FMath::Lerp(W.Up, S.Vel.GetSafeNormal(), 1 - FMath::Exp(-(bTrickCancel ? 18 : 8) * Hs)).GetSafeNormal();
	else W.Up = FMath::Lerp(W.Up, ZUP, 1 - FMath::Exp(-4 * Hs)).GetSafeNormal();
	if (W.Up.Z < -0.2) W.Up = FMath::Lerp(W.Up, ZUP, 0.5).GetSafeNormal();
	if (I.bJumpPressed)
	{ // wall jump
		S.Vel = N * 8.5 + ZUP * (bFast ? 11 : 9.5) + Right * (MX * 4);
		SetMode(EWebTravMode::Air, N_wallJump); S.AirT = 0; S.ApexZ = FeetZ(); S.WallCooldown = 0.35; S.SwingCooldown = 0.18;
		S.Facing = Yaw(S.Vel); Emit(N_wallJump);
		return;
	}
	if (I.bSwingPressed)
	{ // RMB on a wall: kick off it and swing away
		FVector CF = Cam ? Cam->ForwardFlat() : -N;
		CF -= N * FVector::DotProduct(CF, N);
		if (bTrickCancel)
		{ // round 20 (critic r19: "a held RMB during a wall-run waits 0.47-1.08 s"): the kick and the web are one move -- the web is
		  // fired in this same step (ground-swing rule: no rise-pending), a wall-jump hop + 0.06 s re-search only when no anchor is in range
			// along the camera's view off the wall (the next anchor lies ahead of the velocity -- TryStartSwing refuses webs behind it), a small
			// push off the facade; a camera looking straight at the wall uses the run direction instead
			{ // round 20 (probe x2: a camera facing the wall left a tiny sideways residue that kicked him BACK along the run): a side run kicks
			  // along its run direction unless the camera clearly looks along the wall; a vertical run uses the camera's side, else Right
				// the DISPLAYED view (the wall camera faces the facade; the look yaw underneath can point anywhere)
				if (Cam) { CF = FRotator(0.0, Cam->CamRot.Yaw, 0.0).Vector(); CF -= N * FVector::DotProduct(CF, N); }
				const FVector RunD = Flat(S.W.Up);
				if (RunD.SizeSquared() >= 0.09 && (CF.SizeSquared() < 0.25 || FVector::DotProduct(CF, RunD) > 0.0)) CF = RunD;
				else if (CF.SizeSquared() < 0.09) CF = Right;
			}
			CF = CF.GetSafeNormal();
			S.Vel = N * 4 + ZUP * 3 + CF * 12;
			SetMode(EWebTravMode::Air, N_wallJump); S.AirT = 0; S.ApexZ = FeetZ(); S.WallCooldown = 0.5; S.SwingCooldown = 0; S.bGroundSwing = true;
			S.Facing = Yaw(S.Vel); Emit(N_wallJump);
			S.bWallCancel = true; S.WallCancelN = N; S.WallCancelDir = CF;
			UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV wall cancel: RMB pressed in %s -> swing search now (kick v %.1f %.1f %.1f, along %.2f %.2f)"), *S.Sub.ToString(),
				S.Vel.X, S.Vel.Y, S.Vel.Z, CF.X, CF.Y);
			FlipCancels++;
			if (!TryStartSwing(I)) { S.Vel.Z += 4; S.SwingCooldown = 0.06; }
			return;
		}
		S.Vel = N * 9 + ZUP * 7 + CF * 6;
		SetMode(EWebTravMode::Air, N_wallJump); S.AirT = 0; S.ApexZ = FeetZ(); S.WallCooldown = 0.5; S.SwingCooldown = 0.1; S.bGroundSwing = true;
		S.Facing = Yaw(S.Vel); Emit(N_wallJump);
		return;
	}
	if (I.bDropPressed) { S.Vel = N * 3; SetMode(EWebTravMode::Air, N_fall); S.AirT = 0; S.ApexZ = FeetZ(); S.WallCooldown = 0.5; return; }
	const FVector Prev = S.Pos;
	S.Pos += S.Vel * Hs;
	// inner corner: wall ahead in the sideways direction
	if (FMath::Abs(VX) > 0.5)
	{
		const FVector Side = Right * Sgn(VX);
		FTravHit Hit;
		FTravHit Hit2;
		if (TravWorld.Raycast(S.Pos, Side, R + 0.25, Hit) && FMath::Abs(Hit.Normal.Z) < 0.5 && FVector::DotProduct(Hit.Normal, Side) < -0.7
			// round 20: a real inner corner (the new face reaches >= 1.2 m out from this facade), not a pilaster / jamb
			&& (TravWorld.SolidMode != 2 || (TravWorld.Raycast(S.Pos + N * 1.2, Side, R + 0.7, Hit2) && FVector::DotProduct(Hit2.Normal, Side) < -0.7)))
		{
			Hit.Normal = CleanWallNormal(Hit.Point, Hit.Normal);
			const FVector N1 = Flat(Hit.Normal).GetSafeNormal();
			FVector P1 = Hit.Point + N1 * (R + 0.02); P1.Z = S.Pos.Z;
			StartCornerWrap(N1, P1, 0.22, N, Sgn(VX));
			return;
		}
	}
	// wall top ahead (user r6): the top of the wall at chest height -> pop up and hop forward onto the roof
	if (VYIn + W.RunV > 0.5 || VY > 0.5)
	{
		FVector O = S.Pos - N * (R + 0.25); O.Z = FeetZ() + 2.4;
		FTravHit Top;
		if (TravWorld.Raycast(O, FVector(0, 0, -1), 2.4, Top) && Top.Normal.Z > 0.5 && Top.Point.Z - FeetZ() < 1.35)
		{
			if (StartWallHop(N, bFast || W.bFast)) return;
		}
	}
	// stay attached: probe the wall at chest and knee height
	auto Probe = [&](double OZ, FTravHit& Out) { return TravWorld.Raycast(FVector(S.Pos.X, S.Pos.Y, S.Pos.Z + OZ), -N, R + 0.9, Out); };
	FTravHit Hit;
	bool bHit = false;
	FVector PlaneN, PlaneP;
	if (TravWorld.SolidMode == 2 && WallPlane(N, PlaneN, PlaneP))
	{ // round 20: the facade plane from a ray grid (real triangles: recesses / jambs / mullions must not steer the run)
		bHit = true; Hit.Point = PlaneP; Hit.Normal = PlaneN;
	}
	else
	{
		bHit = Probe(0.35, Hit);
		if (!bHit || FMath::Abs(Hit.Normal.Z) > 0.5) bHit = Probe(-0.5, Hit);
	}
	if (bHit && FMath::Abs(Hit.Normal.Z) < 0.5)
	{
		FVector NN = Flat(Hit.Normal).GetSafeNormal();
		if (TravWorld.SolidMode == 2)
		{ // a big turn on a facade is a corner (handled by the corner wraps), never a frame-to-frame normal swap; small drifts are eased in
			if (FVector::DotProduct(NN, N) < 0.85 && S.ModeT > 0.15) NN = N;
			else if (FVector::DotProduct(NN, N) < 0.999) NN = FMath::Lerp(N, NN, FMath::Min(1.0, 12.0 * Hs)).GetSafeNormal();
		}
		if (FVector::DotProduct(NN, N) < 0.98 || TravWorld.SolidMode == 2) N = NN;
		// effective wall plane = the most protruding surface over the body extent (user feedback #5)
		const double BX = Hit.Point.X, BY = Hit.Point.Y;
		const double Prot = FMath::Min(0.12, WallProtrusion(N, BX, BY));
		W.Off = Prot > W.Off ? Prot : Damp(W.Off, Prot, 10, Hs);
		const double Off = R + 0.02 + W.Off;
		S.Pos.X = BX + N.X * Off; S.Pos.Y = BY + N.Y * Off;
		W.Point = FVector(BX + N.X * W.Off, BY + N.Y * W.Off, S.Pos.Z); W.Dist = R + 0.02;
	}
	else
	{
		// outer corner: wrap around it (checked first when moving sideways — a side run must carry round the corner)
		if (FMath::Abs(VX) > 0.5 && FMath::Abs(VX) >= FMath::Abs(VY))
		{
			const FVector Side = Right * Sgn(VX);
			const FVector O = Prev + Side * (R + 0.8) - N * (R + 0.8);
			FTravHit H2;
			if (TravWorld.Raycast(O, -Side, 2, H2) && FVector::DotProduct(H2.Normal, Side) > 0.7)
			{
				const FVector N1 = CleanWallNormal(H2.Point, H2.Normal); // round 20
				FVector P1 = H2.Point + N1 * (R + 0.02); P1.Z = Prev.Z;
				StartCornerWrap(N1, P1, 0.3, -N, Sgn(VX));
				return;
			}
		}
		// top of the wall: hop onto the roof
		if (VY > -0.5)
		{
			FVector O = Prev - N * (R + 0.7); O.Z += 2.4;
			FTravHit Top;
			if (TravWorld.Raycast(O, FVector(0, 0, -1), 5.5, Top) && Top.Normal.Z > 0.5 && StartWallHop(N, bFast || W.bFast)) return;
		}
		if (S.Sub == N_wallZip && S.Z.Target.Z > S.Pos.Z + 0.5) return; // user r9z: a recess mid-pull never drops him off
		if (FMath::Abs(VX) > 0.5)
		{
			const FVector Side = Right * Sgn(VX);
			const FVector O = Prev + Side * (R + 0.8) - N * (R + 0.8);
			FTravHit H2;
			if (TravWorld.Raycast(O, -Side, 2, H2) && FVector::DotProduct(H2.Normal, Side) > 0.7)
			{
				FVector P1 = H2.Point + Side * (R + 0.02); P1.Z = Prev.Z;
				StartCornerWrap(Side, P1, 0.3, -N, Sgn(VX));
				return;
			}
		}
		S.Vel = N * 2 + ZUP * (FMath::Max(0.0, VY) * 0.5); SetMode(EWebTravMode::Air, N_fall); S.AirT = 0; S.ApexZ = FeetZ(); S.WallCooldown = 0.3;
		return;
	}
	// bottom: step off onto the street
	const double GF = FloorAt(S.Pos.X + N.X * 0.6, S.Pos.Y + N.Y * 0.6, FeetZ() + 0.3);
	if (FeetZ() <= GF + 0.02 && VY <= 0)
	{
		S.Pos.Z = GF + H; S.Pos.X += N.X * 0.15; S.Pos.Y += N.Y * 0.15; S.Vel = FVector::ZeroVector; S.Facing = Yaw(N);
		EnterGround(N_idle); S.WallCooldown = 0.5;
	}
}

// user r9w: E while running up / clinging to a wall: web-zip up the facade (burst in StepWall, sub 'wallZip')
void UWebTraversalComponent::WallZip()
{
	FWall& W = S.W;
	const FVector N = W.Normal;
	FVector Tgt = S.Pos - N * (R + 0.02 + W.Off); Tgt.Z += WZIP.Reach;
	// user r9z: highest facade point up to `reach` (stop 0.5 m under its top)
	double Top = -1;
	for (double DY = 2; DY <= WZIP.Reach; DY += 2)
	{
		FTravHit Hit;
		if (TravWorld.Raycast(FVector(S.Pos.X, S.Pos.Y, S.Pos.Z + DY), -N, R + 2.5, Hit) && FMath::Abs(Hit.Normal.Z) < 0.5) { Top = DY; Tgt = Hit.Point; }
		else if (Top > 0) break;
	}
	if (Top > 0 && Top < WZIP.Reach) Tgt.Z -= 0.5;
	S.Z.Target = Tgt; W.ZipT = 0; W.bZipWeb = true; W.bLockDir = false;
	const FVector Side = FVector(-N.Y, N.X, 0) * 0.35; // user r9z: two webs, one per hand
	WebAttach(true, Tgt - Side, 0.06);
	WebAttach(false, Tgt + Side, 0.07, true);
	SetSub(N_wallZip); S.Facing = Yaw(-N); S.ZipCooldown = WZIP.Cd;
	Emit(N_wallZip);
}

// how far (m, >= 0) any wall surface within the body's extent sticks out past the base wall point (bx, by)
double UWebTraversalComponent::WallProtrusion(const FVector& N, double BX, double BY) const
{
	double Best = 0;
	for (double OY : { -0.88, -0.45, 0.05, 0.5, 0.85 })
	{
		const FVector O(BX + N.X * 0.75, BY + N.Y * 0.75, S.Pos.Z + OY);
		FTravHit Hit;
		if (!TravWorld.Raycast(O, -N, 1.6, Hit) || FMath::Abs(Hit.Normal.Z) > 0.6) continue;
		const double D = (Hit.Point.X - BX) * N.X + (Hit.Point.Y - BY) * N.Y;
		if (D > Best && D < 0.7) Best = D;
	}
	return Best;
}

// dir1 = travel direction along the new face, mx = the lateral key held (direction lock). A fast side run wraps at speed.
void UWebTraversalComponent::StartCornerWrap(const FVector& N1, const FVector& P1, double Dur, const FVector& Dir1, double Mx)
{
	FWall& W = S.W;
	const bool bRun = W.bFast && S.Sub == N_wallRunSide;
	const FVector Mid = FMath::Lerp(S.Pos, P1, 0.5) + W.Normal * 0.35 + N1 * 0.35;
	const double Sp = S.Vel.Size();
	if (bRun) Dur = FMath::Clamp((FVector::Dist(S.Pos, Mid) + FVector::Dist(Mid, P1)) / FMath::Max(Sp, 6.0), 0.1, 0.3);
	S.Kin = FKin();
	S.Kin.Type = EKin::CornerWrap; S.Kin.Dur = Dur; S.Kin.P0 = S.Pos; S.Kin.P1 = Mid; S.Kin.P2 = P1;
	S.Kin.N0 = W.Normal; S.Kin.N1 = N1; S.Kin.bRun = bRun; S.Kin.Sp = Sp; S.Kin.Dir1 = Dir1; S.Kin.bHasDir1 = true;
	if (Mx != 0) { W.LockDir = Dir1; W.LockMx = Mx; W.bLockDir = true; }
	if (!bRun) SetSub(N_cornerWrap);
	Emit(N_cornerWrapEv, 0.f, 0.f, 1.f, bRun);
}

// Wall-top hop (user r6) / wall-run launch (user r9b)
bool UWebTraversalComponent::StartWallHop(const FVector& N, bool bFast)
{
	FWall& W = S.W;
	const FVector Inward = Flat(-N).GetSafeNormal();
	const bool bRun = S.Mode == EWebTravMode::Wall && ((S.Sub == N_wallRun && W.bFast) || S.Sub == N_wallZip);
	const double VY0 = bRun ? FMath::Max(0.0, S.Vel.Z) : 0;
	// user r9b: a vertical wall RUN reaching the top launches him into the air — ordinary air gameplay from there
	if (bRun && TryMantleSetback(N)) return true;
	if (bRun)
	{
		++TopOutCount;
		UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV wall top-out at z %.1f (feet), %d setbacks mantled before it"), FeetZ(), SetbackCount);
		// round 06: a lower, quicker top-out (the flip fills the air time) that carries a bit further onto the roof
		const double VUp = 11.5; (void)VY0;
		S.Vel = Inward * 3.0 + ZUP * VUp;
		S.Facing = Yaw(Inward);
		// round 06: the top-out is its own air sub (front flip over the roof edge, crouch landing) instead of a jump launch
		SetMode(EWebTravMode::Air, N_topOut); S.AirT = 0; S.ApexZ = FeetZ(); S.bGrounded = false; S.JumpCharge = 1; S.bTopOut = true;
		S.WallCooldown = 0.9; S.SwingCooldown = 0.15; S.Kin.Type = EKin::None;
		Emit(N_wallLaunch); Emit(N_jump, 1.f);
		return true;
	}
	const double WallDist = R + 0.02 + W.Off;
	const double F0 = FeetZ();
	static const double DS[] = { 0.08, 0.25, 0.45, 0.7, 1.0, 1.35, 1.75, 2.2, 2.7 };
	double Prof[9];
	for (int32 K = 0; K < 9; ++K)
	{
		FVector O = S.Pos + Inward * (WallDist + DS[K]); O.Z = F0 + 6;
		FTravHit Hit;
		Prof[K] = TravWorld.Raycast(O, FVector(0, 0, -1), 14, Hit) && Hit.Normal.Z > 0.3 ? Hit.Point.Z : -1e9;
	}
	double Floor = 1e9;
	bool bFar = false;
	for (int32 K = 3; K < 9; ++K) { if (Prof[K] > -1e8) { Floor = FMath::Min(Floor, Prof[K]); bFar = true; } }
	if (!bFar) return false;                      // nothing to land on
	if (Floor < F0 - 3) return false;             // not a roof, a drop
	double ObstD = -1, ObstTop = Floor;
	for (int32 K = 0; K < 9; ++K) { if (Prof[K] > Floor + 0.2 && DS[K] < 1.6) { ObstD = DS[K]; if (Prof[K] > ObstTop) ObstTop = Prof[K]; } }
	const double LandD = FMath::Max(1.25, ObstD + 0.95);
	const FVector LandP = S.Pos + Inward * (WallDist + LandD);
	const double LandTop = FloorAt(LandP.X, LandP.Y, FMath::Max(ObstTop, Floor) + 0.3);
	if (!(LandTop > F0 - 3)) return false;
	double Apex = FMath::Max(FMath::Max(ObstTop, LandTop) + 0.45, F0 + 0.35);
	const double DTot = WallDist + LandD;
	double TA = 0, TB = 0;
	for (int32 K = 0; K < 4; ++K)
	{
		TA = FMath::Sqrt(2 * (Apex - F0) / G);
		TB = FMath::Max(0.28, FMath::Sqrt(2 * FMath::Max(0.05, Apex - LandTop) / G));
		const double V = DTot / TB;
		if (ObstD < 0) break;
		const double TC = (WallDist + ObstD + R) / V, Drop = 0.5 * G * TC * TC;
		if (Apex - Drop >= ObstTop + 0.1) break;
		Apex = ObstTop + 0.1 + Drop + 0.05;
	}
	S.Kin = FKin();
	S.Kin.Type = EKin::WallHop; S.Kin.TA = TA; S.Kin.TB = TB; S.Kin.F0 = F0; S.Kin.Apex = Apex; S.Kin.LandTop = LandTop;
	S.Kin.P0 = S.Pos; S.Kin.Inward = Inward; S.Kin.DTot = DTot; S.Kin.bRun = bFast; S.Kin.ExitSpeed = bFast ? 5.5 : 1.8;
	S.Facing = Yaw(Inward);
	SetMode(EWebTravMode::Air, N_jumpLaunch); S.AirT = 0; S.ApexZ = Apex; S.bGrounded = false; S.WallCooldown = 0.6; S.SwingCooldown = 0.25;
	S.JumpCharge = bFast ? 0.35 : 0.1;
	Emit(N_wallHop);
	return true;
}

// round 20 (critic r19: "head-down mid-facade flips" -- per-mass boxes / real triangles expose setback tiers, c topped out at 35 m AND 45 m):
// a vertical wall run reaching a ledge tops out only when no solid continues above it within SetbackLook m inward; a setback is mantled
// (short kinematic hop over the ledge onto the next face) and the run continues up it
bool UWebTraversalComponent::TryMantleSetback(const FVector& N0)
{
	const FVector N = Flat(N0).GetSafeNormal();
	const double WallDist = R + 0.02 + S.W.Off;
	// ledge top just inside the edge
	FTravHit Top;
	const FVector In = S.Pos - N * (WallDist + 0.3);
	if (!TravWorld.Raycast(FVector(In.X, In.Y, FeetZ() + 3.2), FVector(0, 0, -1), 4.5, Top) || Top.Normal.Z < 0.5) return false;
	const double LedgeZ = Top.Point.Z;
	// a face continuing above the ledge, within SetbackLook m inward, facing the same way, at least 4 m tall
	for (double Hgt : { 1.3, 2.6 })
	{
		FTravHit Wf;
		const FVector O(S.Pos.X, S.Pos.Y, LedgeZ + Hgt);
		if (!TravWorld.Raycast(O, -N, WallDist + double(SetbackLook), Wf)) continue;
		if (FMath::Abs(Wf.Normal.Z) > 0.5 || FVector::DotProduct(Flat(Wf.Normal).GetSafeNormal(), N) < 0.7) continue;
		FTravHit Up4;
		const FVector N2 = Flat(Wf.Normal).GetSafeNormal();
		const FVector O4 = Wf.Point + N2 * 0.6 + FVector(0, 0, 4.0);
		if (!TravWorld.Raycast(O4, -N2, 1.5, Up4) || FMath::Abs(Up4.Normal.Z) > 0.5) continue; // a low parapet / rooftop box, not a tier
		const FVector P1 = FVector(Wf.Point.X + N2.X * (R + 0.02), Wf.Point.Y + N2.Y * (R + 0.02), LedgeZ + H + 0.9);
		const FVector Mid = FVector(S.Pos.X - N.X * (WallDist * 0.5), S.Pos.Y - N.Y * (WallDist * 0.5), LedgeZ + H + 0.7);
		const double Sp = FMath::Max(8.0, FMath::Max(S.Vel.Z, S.W.RunV));
		S.Kin = FKin();
		S.Kin.Type = EKin::Mantle; S.Kin.P0 = S.Pos; S.Kin.P1 = Mid; S.Kin.P2 = P1; S.Kin.N0 = N; S.Kin.N1 = N2; S.Kin.Sp = Sp; S.Kin.bRun = true;
		S.Kin.Dur = FMath::Clamp((FVector::Dist(S.Pos, Mid) + FVector::Dist(Mid, P1)) / Sp, 0.14, 0.38);
		S.Kin.Inward = Wf.Point;
		if (MantleStep > 0.5f)
		{ // round 21 (critic r20: "mid-facade hop at c 3.55 s", limbs 3 m off the wall): cross the setback ON its surfaces -- up the lip,
		  // round the edge, along the ledge top (normal up), cut the inner corner, onto the next face; the IK stride keeps running on
		  // whichever surface is under him, so every limb stays on it
			const double D = WallDist;
			const FVector InW = -N;
			const double Dn = FMath::Max(0.6, Wf.Distance - WallDist);
			const FVector C(S.Pos.X - N.X * WallDist, S.Pos.Y - N.Y * WallDist, 0.0); // old face plane at the hero
			double TopZ = LedgeZ;
			for (double Fr : { 0.25, 0.5, 0.8 })
			{
				FTravHit Tp; const FVector Q = C + InW * (Dn * Fr);
				if (TravWorld.Raycast(FVector(Q.X, Q.Y, LedgeZ + 3.2), FVector(0, 0, -1), 4.5, Tp) && Tp.Normal.Z > 0.5) TopZ = FMath::Max(TopZ, Tp.Point.Z);
			}
			const FVector Zu(0, 0, 1), NE = (N + Zu).GetSafeNormal();
			const double Cut = FMath::Min(0.5, FMath::Max(0.1, Dn - 2.0 * D) * 0.5);
			FKin& K = S.Kin;
			K.MNum = 0;
			auto AddQ = [&K](const FVector& Q, const FVector& Nq) { if (K.MNum < 6) { K.MQ[K.MNum] = Q; K.MN[K.MNum] = Nq; K.ML[K.MNum] = K.MNum ? K.ML[K.MNum - 1] + FVector::Dist(K.MQ[K.MNum - 1], Q) : 0.0; ++K.MNum; } };
			AddQ(S.Pos, N);
			if (S.Pos.Z < TopZ - 0.05) AddQ(FVector(S.Pos.X, S.Pos.Y, TopZ - 0.05), N);
			AddQ(FVector(C.X, C.Y, TopZ) + NE * D, NE);
			AddQ(FVector(C.X, C.Y, TopZ) + InW * 0.15 + Zu * D, Zu);
			AddQ(FVector(C.X, C.Y, TopZ) + InW * FMath::Max(0.3, Dn - D - Cut) + Zu * D, Zu);
			AddQ(FVector(C.X, C.Y, TopZ) + InW * (Dn - D) + Zu * (D + Cut + 0.25), N2);
			K.MS = 0; K.CurN = N; K.CurPt = S.Pos - N * D;
			K.Dur = FMath::Max(0.1, K.ML[K.MNum - 1] / Sp);
			K.P2 = K.MQ[K.MNum - 1];
			UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV setback step: ledge top z %.2f, depth %.2f m, path %.2f m, %.2f s"), TopZ, Dn, K.ML[K.MNum - 1], K.Dur);
		}
		++SetbackCount;
		UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV wall setback mantled at ledge z %.1f (next face %.1f m in): the run continues"), LedgeZ, Wf.Distance - WallDist);
		return true;
	}
	return false;
}

void UWebTraversalComponent::StepWallHop(double Hs)
{
	FKin& K = S.Kin;
	K.T += Hs;
	const FVector Prev = S.Pos;
	double FZ, D;
	if (K.T <= K.TA)
	{ // rising straight up along the wall (decelerating), no inward motion yet
		const double VY0 = G * K.TA, T = K.T;
		FZ = K.F0 + VY0 * T - 0.5 * G * T * T; D = 0;
		if (S.Sub != N_jumpLaunch && K.T < 0.12) SetSub(N_jumpLaunch); else if (K.T >= 0.12) SetSub(N_rise);
	}
	else
	{ // over the top and forward onto the roof
		const double T = FMath::Min(K.T - K.TA, K.TB);
		FZ = K.Apex - 0.5 * G * T * T; D = K.DTot * (T / K.TB);
		SetSub(T < 0.12 ? N_apex : N_fall);
		if (K.T - K.TA >= K.TB || FZ <= K.LandTop)
		{
			const FKin KK = K;
			S.Kin.Type = EKin::None;
			S.Pos = KK.P0 + KK.Inward * KK.DTot;
			S.FloorZ = FloorAt(S.Pos.X, S.Pos.Y, KK.LandTop + 0.3); S.Pos.Z = S.FloorZ + H;
			S.Vel = KK.Inward * KK.ExitSpeed; S.Facing = Yaw(KK.Inward);
			EnterGround(N_landLight); S.Speed = KK.ExitSpeed; S.LandSeverity = 0.15; S.LandLock = 0; S.WallCooldown = 0.4;
			Emit(N_land, 0.15f);
			return;
		}
	}
	S.Pos = FVector(K.P0.X + K.Inward.X * D, K.P0.Y + K.Inward.Y * D, FZ + H);
	S.Vel = (S.Pos - Prev) / FMath::Max(Hs, 1e-4);
}

void UWebTraversalComponent::StepKin(double Hs)
{
	FKin& K = S.Kin;
	if (K.Type == EKin::Mantle && K.MNum > 1)
	{ // round 21: surface-following setback step (distance along the centre polyline at the run speed)
		K.MS = FMath::Min(K.MS + K.Sp * Hs, K.ML[K.MNum - 1]);
		int32 Sg = 1;
		while (Sg < K.MNum - 1 && K.ML[Sg] < K.MS) ++Sg;
		const double L0 = K.ML[Sg - 1], L1 = K.ML[Sg];
		const double F = L1 > L0 + 1e-6 ? FMath::Clamp((K.MS - L0) / (L1 - L0), 0.0, 1.0) : 1.0;
		const FVector Prev = S.Pos;
		S.Pos = FMath::Lerp(K.MQ[Sg - 1], K.MQ[Sg], F);
		K.CurN = FMath::Lerp(K.MN[Sg - 1], K.MN[Sg], F).GetSafeNormal();
		const double Dd = S.W.Dist;
		K.CurPt = S.Pos - K.CurN * Dd;
		const FVector Tan = (K.MQ[Sg] - K.MQ[Sg - 1]).GetSafeNormal();
		S.Vel = Tan * K.Sp;
		S.W.Up = Tan; S.W.Point = K.CurPt;
		(void)Prev;
		if (K.MS >= K.ML[K.MNum - 1] - 1e-6)
		{
			const FKin KK = K;
			S.Kin.Type = EKin::None; S.Kin.MNum = 0;
			const FVector Pt = KK.Inward;
			const double RK = S.W.RunK;
			EnterWall(KK.N1, FVector(Pt.X, Pt.Y, S.Pos.Z), true, KK.Sp);
			S.W.RunV = FMath::Max(S.W.RunV, KK.Sp); S.WallCooldown = 0.0; S.W.Up = ZUP; S.W.RunK = RK;
		}
		return;
	}
	K.T += Hs / K.Dur;
	const double U = FMath::Min(1.0, K.T);
	const double E = U * U * (3 - 2 * U);
	const double A = 1 - E;
	S.Pos = K.P0 * (A * A) + K.P1 * (2 * A * E) + K.P2 * (E * E);
	if (K.Type == EKin::Mantle)
	{
		const FVector PV = K.P1 * (2 * A) - K.P0 * (2 * A) + K.P2 * (2 * E) - K.P1 * (2 * E);
		if (PV.SizeSquared() > 1e-6) S.Vel = PV.GetSafeNormal() * K.Sp;
	}
	if (K.Type == EKin::CornerWrap)
	{
		S.W.Normal = FMath::Lerp(K.N0, K.N1, E).GetSafeNormal();
		const FVector PV = K.P1 * (2 * A) - K.P0 * (2 * A) + K.P2 * (2 * E) - K.P1 * (2 * E);
		if (PV.SizeSquared() > 1e-6) S.Vel = PV.GetSafeNormal() * (K.bRun ? K.Sp : 2.0);
	}
	if (U >= 1)
	{
		const FKin KK = K;
		S.Kin.Type = EKin::None;
		if (KK.Type == EKin::CornerWrap)
		{
			S.W.Normal = KK.N1;
			if (KK.bRun && KK.bHasDir1) { S.Vel = KK.Dir1 * KK.Sp; SetSub(N_wallRunSide); } else SetSub(N_crawl);
		}
		else if (KK.Type == EKin::Mantle)
		{ // round 20: back on the next tier's face, still running up
			const FVector Pt = KK.Inward;
			EnterWall(KK.N1, FVector(Pt.X, Pt.Y, S.Pos.Z), true, KK.Sp);
			S.W.RunV = FMath::Max(S.W.RunV, KK.Sp); S.WallCooldown = 0.0;
		}
		else if (KK.Type == EKin::Vault)
		{
			S.FloorZ = FloorAt(S.Pos.X, S.Pos.Y, FeetZ() + 0.3); S.Pos.Z = S.FloorZ + H;
			S.Speed = KK.ExitVel.Size(); S.Vel = KK.ExitVel;
			if (S.Speed > 0.1) S.Facing = Yaw(KK.ExitVel);
			EnterGround(S.Speed > RUN + 1.5 ? N_sprint : S.Speed > 1 ? N_run : N_idle);
			S.Speed = KK.ExitVel.Size(); S.WallCooldown = 0.35;
		}
	}
}

// ------------------------------------------------------------------ zip / perch / point launch
// round 19: "the nearest place" when nothing is highlighted: on a wall the top edge of this facade (<= 58 m straight up), else the nearest
// visible roof edge / corner / water tower within 58 m, preferring what the camera faces and what is not far below the hero
bool UWebTraversalComponent::NearestZip(FTravZipPoint& Out, FName& Why) const
{
	const double ZipRange = 58.0;
	const FVector Eye = S.Pos + FVector(0, 0, 0.5);
	// round 23 (critic r22: "w2 zipFire 4.00 s, it never lands -- z 232 m at 6.97 s"; T4): a facade top more than WallZipFarUp above the hero
	// (a ~4 s flight up a 284 m tower) is only the fallback; the nearest roof edge / corner within reach is taken first
	FTravZipPoint FarTop; bool bFarTop = false;
	if (S.Mode == EWebTravMode::Wall)
	{
		// round 20 (critic r19: "E from a side-run ends clinging mid-facade at 61 m" -- the facade top was > 58 m up): on a wall the facade
		// top is searched up to WallZipRange (the zip's speed profile flies any length)
		const FVector N = S.W.Normal;
		double LastHit = -1.0;
		const double WallRange = FMath::Max(ZipRange, double(WallZipRange));
		for (double DY = 0.5; DY <= WallRange; DY += 1.0)
		{
			FTravHit Hit;
			const bool bWall = TravWorld.Raycast(FVector(S.Pos.X, S.Pos.Y, S.Pos.Z + DY), -N, R + 2.5, Hit) && FMath::Abs(Hit.Normal.Z) < 0.5;
			if (bWall) { LastHit = DY; continue; }
			if (LastHit < 0.0 && DY < 4.0) continue; // a recess right at the body
			// the facade ended: find its roof just inside the edge
			// round 20 (capture w1 5.0-6.1 s: the perch sat on the roof BEHIND a 1-2 m parapet -- the down ray 0.6 m inside missed the thin
			// parapet -- so the camera saw only his head over it): the edge is the HIGHEST walkable top within 0.15-0.6 m of the facade line
			FTravHit Top; double BestIn = -1.0;
			for (double Inset : { 0.15, 0.3, 0.45, 0.6 })
			{
				FTravHit T2;
				const FVector In = FVector(S.Pos.X, S.Pos.Y, 0.0) - Flat(N) * (R + 0.02 + S.W.Off + Inset);
				if (TravWorld.Raycast(FVector(In.X, In.Y, S.Pos.Z + DY + 3.0), FVector(0, 0, -1), 8.0, T2) && T2.Normal.Z > 0.5
					&& (BestIn < 0.0 || T2.Point.Z > Top.Point.Z + 0.05)) { Top = T2; BestIn = Inset; }
			}
			if (BestIn >= 0.0 && !bPerchTopFix) { const FVector In = FVector(S.Pos.X, S.Pos.Y, 0.0) - Flat(N) * (R + 0.02 + S.W.Off + 0.6);
				FTravHit T3; if (TravWorld.Raycast(FVector(In.X, In.Y, S.Pos.Z + DY + 3.0), FVector(0, 0, -1), 8.0, T3) && T3.Normal.Z > 0.5) { Top = T3; BestIn = 0.6; } else BestIn = -1.0; }
			if (BestIn >= 0.0)
			{
				const FVector Edge = FVector(S.Pos.X, S.Pos.Y, 0.0) - Flat(N) * (R + 0.02 + S.W.Off + (bPerchTopFix ? FMath::Max(0.2, BestIn) : 0.25));
				Out.Pos = FVector(Edge.X, Edge.Y, Top.Point.Z); Out.Normal = Flat(N).GetSafeNormal(); Out.Kind = FName(TEXT("roofEdge")); Out.Box = Top.Box;
				Why = TEXT("facadeTop");
				if (WallZipFarUp > 0.f && Top.Point.Z - S.Pos.Z > double(WallZipFarUp)) { FarTop = Out; bFarTop = true; break; }
				return true;
			}
			break;
		}
	}
	TArray<FTravZipPoint> Pts;
	Anchors->QueryZipPoints(Eye, ZipRange, Pts);
	const FVector CF = Cam ? Cam->ForwardFlat() : YawDir(S.Facing);
	const FVector Excl = S.Mode == EWebTravMode::Perch ? S.P.Pos : FVector(1e9);
	const FTravZipPoint* Best = nullptr;
	double BS = TNumericLimits<double>::Max();
	for (const FTravZipPoint& P : Pts)
	{
		const FVector Rel = P.Pos - Eye;
		const double Dist = Rel.Size();
		if (Dist < 3.0 || Dist > ZipRange || FVector::DistSquared(P.Pos, Excl) < 4.0) continue;
		const FVector RF = Flat(Rel).GetSafeNormal();
		const double Face = RF.IsNearlyZero() ? 1.0 : FVector::DotProduct(RF, CF);
		if (Face < -0.2) continue; // never behind the camera
		const double Sc = Dist / ZipRange + (1.0 - Face) * 0.6 + (P.Pos.Z < Eye.Z - 4.0 ? 0.5 : 0.0) - (P.Kind == FName(TEXT("roofCorner")) ? 0.05 : 0.0);
		if (Sc >= BS) continue;
		FVector Tgt = P.Pos + P.Normal * 0.35; Tgt.Z += 0.35;
		FVector D = Tgt - Eye;
		const double L = D.Size();
		FTravHit Hv;
		if (TravWorld.Raycast(Eye, D / L, L, Hv) && Hv.Distance < L - 0.7) continue;
		BS = Sc; Best = &P;
	}
	if (!Best && bFarTop && WallZipFarRange > 0.f)
	{ // round 23 (Z23, probe r23: w2 found nothing in front of the wall camera -- it faces the facade -- and flew 4 s up the 300 m tower):
	  // any visible roof edge / corner off the wall within WallZipFarRange, nearest first, along the run preferred, never through the wall
		const double FR = double(WallZipFarRange);
		TArray<FTravZipPoint> P2;
		Anchors->QueryZipPoints(Eye, FR, P2);
		const FVector Nf = Flat(S.W.Normal).GetSafeNormal();
		const FVector RunD = Flat(S.Vel).GetSafeNormal();
		FTravZipPoint Far2;
		double BS2 = TNumericLimits<double>::Max();
		bool bF2 = false;
		for (const FTravZipPoint& P : P2)
		{
			const FVector Rel = P.Pos - Eye;
			const double Dist = Rel.Size();
			if (Dist < 3.0 || Dist > FR) continue;
			const FVector RF = Flat(Rel).GetSafeNormal();
			if (!RF.IsNearlyZero() && FVector::DotProduct(RF, -Nf) > 0.5) continue; // behind the facade
			const double Run = RunD.IsNearlyZero() || RF.IsNearlyZero() ? 0.0 : FVector::DotProduct(RF, RunD);
			const double Sc = Dist / FR + (1.0 - Run) * 0.3 + (P.Pos.Z > Eye.Z + 25.0 ? 0.4 : 0.0) - (P.Kind == FName(TEXT("roofCorner")) ? 0.05 : 0.0);
			if (Sc >= BS2) continue;
			FVector Tgt = P.Pos + P.Normal * 0.35; Tgt.Z += 0.35;
			const FVector D = Tgt - Eye;
			const double L = D.Size();
			FTravHit Hv;
			if (TravWorld.Raycast(Eye, D / L, L, Hv) && Hv.Distance < L - 0.7) continue;
			BS2 = Sc; Far2 = P; bF2 = true;
		}
		if (bF2) { Out = Far2; Why = TEXT("nearFar2"); return true; }
	}
	if (!Best)
	{
		if (bFarTop) { Out = FarTop; Why = TEXT("facadeTop"); return true; }
		return false;
	}
	Out = *Best;
	Why = bFarTop ? TEXT("nearFar") : TEXT("nearest");
	return true;
}

// Insomniac web-zip (USER_FEEDBACK #8 / user r10: instant): zipFire -> zipFlight -> zipCatch -> perch
void UWebTraversalComponent::StartZip(const FTravZipPoint& T)
{
	FZip& Z = S.Z;
	Z.Target = T.Pos; Z.Normal = T.Normal; Z.Kind = T.Kind; Z.bLaunch = false; Z.bDash = false; Z.bWebs = true; Z.Taut = 0; Z.T = 0; Z.U = 0;
	const bool bHoriz = HLen(T.Normal) > 0.3;
	// perch stance: feet on the edge (slightly inboard), facing outward
	FVector End = T.Pos;
	if (bHoriz) End -= Flat(T.Normal).GetSafeNormal() * 0.12;
	End.Z += H;
	Z.P2 = End;
	const double Dist = FVector::Dist(S.Pos, End);
	// two anchors a hand-span apart across the line of fire, converging on the target
	const FVector LOS = (T.Pos - S.Pos).GetSafeNormal();
	FVector ZipOff = FVector::CrossProduct(LOS, ZUP);
	if (ZipOff.SizeSquared() < 1e-4) ZipOff = FVector(1, 0, 0);
	ZipOff = ZipOff.GetSafeNormal() * 0.09;
	const FVector AR = T.Pos + T.Normal * 0.05 - ZipOff, AL = T.Pos + T.Normal * 0.05 + ZipOff;
	const double Shoot = FMath::Clamp(Dist / 900, 0.03, 0.05); // near-instant lines (user r10)
	WebAttach(true, AR, Shoot);
	WebAttach(false, AL, Shoot + 0.015, true);
	Z.bFromGround = S.bGrounded;
	Z.FireDur = Shoot + 0.015;
	S.Facing = FMath::Atan2(End.Y - S.Pos.Y, End.X - S.Pos.X);
	SetMode(EWebTravMode::Zip, N_zipFire); S.bCharging = false; S.bDive = false; S.Trick = NAME_None; S.bGliding = false;
	if (Z.bFromGround) S.Vel *= 0.35;
	Emit(N_zip);
}

FVector UWebTraversalComponent::Bez(double E) const
{
	const double A = 1 - E;
	return S.Z.P0 * (A * A) + S.Z.P1 * (2 * A * E) + S.Z.P2 * (E * E);
}

void UWebTraversalComponent::ZipCurve(const FVector& Vel)
{ // arc from the launch point: final approach roughly LEVEL into the perch, from outside the edge
	FZip& Z = S.Z;
	const FVector P0 = Z.P0, End = Z.P2;
	const double Dist = FVector::Dist(P0, End);
	Z.P1 = FMath::Lerp(P0, End, 0.62);
	Z.P1.Z = End.Z + 0.4 + (P0.Z > End.Z ? 0 : Dist * 0.03);
	const FVector HN = Flat(Z.Normal);
	if (HN.SizeSquared() > 0.09) Z.P1 += HN.GetSafeNormal() * FMath::Min(3.0, Dist * 0.08);
	// air zip: the arc leaves along the current momentum (no kink / stop), bending onto the target
	const double Sp = Vel.Size();
	if (Sp > 4)
	{
		const FVector VD = Vel / Sp, ToT = (End - P0).GetSafeNormal();
		if (FVector::DotProduct(VD, ToT) > -0.2) Z.P1 = FMath::Lerp(Z.P1, P0 + VD * (Dist * 0.5), FMath::Clamp(Sp / 30, 0.0, 0.55));
	}
	// the whole flight curve must be clear of facades: raise the arc / move its control point out over the street
	for (int32 It = 0; It < 5 && !ZipClear(); ++It)
	{
		Z.P1.Z += 2.5 + Dist * 0.05;
		FVector Out = Flat(Z.Normal);
		if (Out.SizeSquared() < 0.09) Out = Flat(P0 - End);
		if (Out.SizeSquared() > 1e-4) Z.P1 += Out.GetSafeNormal() * 1.5;
	}
	// speed profile (user r10: release burst): arc-length LUT, burst ramp -> cruise at the peak -> constant braking
	Z.LUT[0] = 0;
	FVector Q = P0;
	for (int32 K = 1; K <= 32; ++K) { const FVector B = Bez(K / 32.0); Z.LUT[K] = Z.LUT[K - 1] + FVector::Dist(B, Q); Q = B; }
	const double L = Z.LUT[32];
	Z.Len = L;
	const double V0 = FMath::Clamp(FVector::DotProduct(Vel, (Z.P1 - P0).GetSafeNormal()), 0.0, 20.0);
	double VP = FMath::Clamp(22 + L * 2.4, 40.0, 72.0) * ZIP_SPEED;
	for (int32 It = 0; It < 12; ++It)
	{ // shrink the peak until ramp + braking fit inside the path
		const double DR = (V0 + VP) / 2 * ZIP_RAMP, DB = (VP * VP - ZIP_VEND * ZIP_VEND) / (2 * ZIP_BRAKE);
		if (DR + DB <= L * 0.92 || VP <= 12) break;
		VP *= 0.88;
	}
	const double DR = (V0 + VP) / 2 * ZIP_RAMP, DB = FMath::Max(0.0, (VP * VP - ZIP_VEND * ZIP_VEND) / (2 * ZIP_BRAKE));
	const double DC = FMath::Max(0.0, L - DR - DB);
	Z.V0 = V0; Z.VP = VP; Z.DR = DR; Z.DC = DC; Z.DB = L - DR - DC;
	Z.TC = ZIP_RAMP + DC / VP; Z.TBrake = Z.TC;
	const double VE = FMath::Sqrt(FMath::Max(0.0, VP * VP - 2 * ZIP_BRAKE * Z.DB));
	const double AB = Z.DB > 1e-3 ? (VP * VP - VE * VE) / (2 * Z.DB) : ZIP_BRAKE;
	Z.AB = AB; Z.Dur = Z.TC + (VP - VE) / FMath::Max(AB, 1e-3);
}

double UWebTraversalComponent::ZipDist(double Tau) const
{
	const FZip& Z = S.Z;
	if (Tau <= ZIP_RAMP) return Z.V0 * Tau + (Z.VP - Z.V0) / ZIP_RAMP * Tau * Tau / 2;
	if (Tau <= Z.TC) return Z.DR + Z.VP * (Tau - ZIP_RAMP);
	const double TB = FMath::Min(Tau, Z.Dur) - Z.TC;
	return FMath::Min(Z.Len, Z.DR + Z.DC + Z.VP * TB - Z.AB * TB * TB / 2);
}

double UWebTraversalComponent::ZipArcE(double D) const
{
	const double* T = S.Z.LUT;
	if (D >= T[32]) return 1;
	if (D <= 0) return 0;
	int32 K = 1;
	while (K < 32 && T[K] < D) ++K;
	return (K - 1 + (D - T[K - 1]) / FMath::Max(1e-6, T[K] - T[K - 1])) / 32.0;
}

bool UWebTraversalComponent::ZipClear() const
{
	FVector A = S.Z.P0;
	for (int32 K = 1; K <= 10; ++K)
	{
		const FVector B = Bez(K / 10.0);
		if (K == 10) break;
		FVector D = B - A;
		const double L = D.Size();
		if (L > 1e-3)
		{
			FTravHit HH;
			if (TravWorld.Raycast(A, D / L, L + 0.4, HH) && FVector::Dist(HH.Point, S.Z.P2) > 1.6) return false;
		}
		A = B;
	}
	return true;
}

void UWebTraversalComponent::StepZip(double Hs, FWebTravInput& I)
{
	FZip& Z = S.Z;
	// user r4 #11: Space in the last ~0.35 s before arrival (or during the catch) = don't perch, launch off the anchor
	if (I.bJumpPressed && (S.Sub == N_zipCatch || (S.Sub == N_zipFlight && (1 - Z.U) * Z.Dur < 0.35))) Z.bLaunch = true;
	// user r4 #13: RMB during the flight cancels the zip and swings at once, carrying the zip's velocity
	if (I.bSwingPressed && (S.Sub == N_zipFlight || S.Sub == N_zipCatch))
	{
		WebRelease(); Z.bWebs = false; SetMode(EWebTravMode::Air, N_fall); S.AirT = 0.2; S.ApexZ = FeetZ(); S.SwingCooldown = 0; S.RelT = 0.4;
		Emit(N_zipCancel);
		if (!TryStartSwing(I)) S.bGroundSwing = true;
		return;
	}
	if (S.Sub == N_zipFire)
	{ // the webs are shooting (a few frames): ground stays planted, air keeps its momentum; then LAUNCH at once
		if (Z.bFromGround) { S.Vel *= FMath::Exp(-7 * Hs); S.Vel.Z = 0; }
		else { S.Vel *= FMath::Exp(-0.8 * Hs); S.Vel.Z -= 6 * Hs; }
		S.Pos += S.Vel * Hs;
		if (!Z.bFromGround)
		{
			FTravContact C;
			if (Collide(0.3, R, C)) { const double VN = FVector::DotProduct(S.Vel, C.Normal); if (VN < 0) S.Vel -= C.Normal * VN; }
		}
		if (S.SubT >= Z.FireDur)
		{ // LAUNCH: the taut webs yank him off toward the target
			Z.Taut = 1; Strands[0].Taut = 1.f; Strands[1].Taut = 1.f;
			Z.P0 = S.Pos; ZipCurve(S.Vel); Z.U = 0; Z.Tau = 0;
			Z.LaunchDir = (Z.P1 - Z.P0).GetSafeNormal();
			SetSub(N_zipFlight); S.bGrounded = false;
			Emit(N_zipLaunch, 0.f, float(FVector::Dist(Z.P0, Z.P2)));
		}
		Z.T = 0;
		return;
	}
	const FVector Prev = S.Pos;
	Z.Tau += Hs; Z.U = FMath::Min(1.0, Z.Tau / Z.Dur);
	S.Pos = Bez(ZipArcE(ZipDist(Z.Tau)));
	S.Vel = (S.Pos - Prev) / FMath::Max(Hs, 1e-4);
	Z.T = Z.U;
	{
		const double Sp = S.Vel.Size();
		if (Sp > 0.5) { Z.Pitch = FMath::Asin(FMath::Clamp(S.Vel.Z / Sp, -1.0, 1.0)); Z.FlightDir = S.Vel / Sp; }
	}
	if (Z.bWebs && Z.U >= 0.25) { Z.bWebs = false; WebRelease(true); Emit(N_zipWebRelease); }
	if (S.Sub == N_zipFlight && Z.Tau >= Z.TBrake) SetSub(N_zipCatch);
	if (Z.U >= 1) ArriveZip();
}

void UWebTraversalComponent::ArriveZip()
{
	FZip& Z = S.Z;
	WebRelease();
	const FVector TravelV = S.Vel;
	if (Z.bLaunch) { AnchorLaunch(TravelV); return; }
	FPerch& P = S.P;
	P.Pos = Z.Target; P.Normal = Z.Normal; P.Kind = Z.Kind;
	FVector HN = Flat(Z.Normal);
	if (HN.SizeSquared() > 0.09) { HN.Normalize(); S.Facing = Yaw(HN); }
	else if (TravelV.SizeSquared() > 1) S.Facing = Yaw(TravelV);
	P.bRoof = FMath::Abs(FloorAt(Z.Target.X - HN.X, Z.Target.Y - HN.Y, Z.Target.Z + 0.2) - Z.Target.Z) < 0.25;
	P.Impact = TravelV; // arrival velocity: the animation layer absorbs it (perchLand)
	S.Pos = Z.P2; S.Vel = FVector::ZeroVector; S.FloorZ = Z.Target.Z;
	SetMode(EWebTravMode::Perch, N_perchLand); S.bGrounded = true; S.DashCount = 0;
	S.LandSeverity = FMath::Clamp(TravelV.Size() / 60, 0.1, 0.45);
	Emit(N_perch, float(S.LandSeverity));
}

// user r4 #11: Space at a zip arrival — no perch: vault off the anchor, jump up + forward keeping momentum
void UWebTraversalComponent::AnchorLaunch(const FVector& TravelV)
{
	FVector HV = Flat(TravelV);
	double HS = HV.Size();
	if (HS < 2) { HV = Cam ? Cam->ForwardFlat() : YawDir(S.Facing); HS = 0; }
	else HV /= HS;
	const FVector InD = InputDir(LastInput);
	if (InD.SizeSquared() > 0.09) HV = FMath::Lerp(HV, Flat(InD).GetSafeNormal(), 0.35).GetSafeNormal(); // a little stick steering
	const double Fwd = FMath::Min(VMAX - 6, FMath::Max(HS, 12.0) + 6);
	S.Vel = HV * Fwd + ZUP * (13 + FMath::Max(0.0, TravelV.Z) * 0.3);
	SetMode(EWebTravMode::Air, N_pointLaunch); S.AirT = 0; S.ApexZ = FeetZ(); S.SwingCooldown = 0.3; S.WallCooldown = 0.3; S.RelT = 0;
	S.Facing = Yaw(HV); S.Trick = NAME_None; S.bGrounded = false;
	Emit(N_pointLaunch, 1.f);
}

void UWebTraversalComponent::PointLaunch(const FVector& Normal, const FVector& TravelV)
{
	// direction: held stick > camera heading, nudged by the zip momentum / perch outward normal
	const FVector InD = InputDir(LastInput);
	FVector Dir = InD.SizeSquared() > 0.09 ? InD.GetSafeNormal() : (Cam ? Cam->ForwardFlat() : YawDir(S.Facing));
	FVector TV;
	if (HDir(TravelV, TV) && FVector::DotProduct(TV, Dir) > 0) Dir = FMath::Lerp(Dir, TV, 0.25).GetSafeNormal();
	FVector Out = Flat(Normal);
	if (Out.SizeSquared() > 0.09 && FVector::DotProduct(Out.GetSafeNormal(), Dir) > -0.3) Dir = FMath::Lerp(Dir, Out.GetSafeNormal(), 0.2).GetSafeNormal();
	// never launch into a facade: swing the heading toward the most open direction
	auto Blocked = [&](const FVector& D)
	{
		FTravHit HH;
		return TravWorld.Raycast(S.Pos + FVector(0, 0, 1.5), FVector(D.X, D.Y, 0.45).GetSafeNormal(), 14, HH) && FMath::Abs(HH.Normal.Z) < 0.6;
	};
	if (Blocked(Dir))
	{
		bool bBest = false;
		FVector BestD;
		double BestA = 9;
		const double A0 = Yaw(Dir);
		for (double DA : { 0.4, -0.4, 0.8, -0.8, 1.2, -1.2, 1.6, -1.6, 2.2, -2.2, UE_DOUBLE_PI })
		{
			const FVector D = YawDir(A0 + DA);
			if (!Blocked(D) && FMath::Abs(DA) < BestA) { BestA = FMath::Abs(DA); BestD = D; bBest = true; }
		}
		if (bBest) Dir = BestD; else if (Out.SizeSquared() > 0.09) Dir = Out.GetSafeNormal();
	}
	const double Carry = FMath::Min(12.0, HLen(TravelV) * 0.25);
	S.Vel = Dir * (15 + Carry) + ZUP * 20.5;
	SetMode(EWebTravMode::Air, N_pointLaunch); S.AirT = 0; S.ApexZ = FeetZ(); S.SwingCooldown = 0.35; S.WallCooldown = 0.3;
	S.Facing = Yaw(Dir); S.Trick = NAME_None;
	Emit(N_pointLaunch);
}

void UWebTraversalComponent::WebDash()
{ // Insomniac web-zip: forward air dash when no zip point is targeted
	const FVector F = Cam ? Cam->ForwardFlat() : YawDir(S.Facing);
	const double HS = HLen(S.Vel);
	const double Sp = FMath::Min(FMath::Max(HS + 8, 22.0), VMAX);
	S.Vel.X = F.X * Sp; S.Vel.Y = F.Y * Sp; S.Vel.Z = FMath::Max(S.Vel.Z, 3.5);
	FVector Tgt = S.Pos + F * 16; Tgt.Z += 3;
	S.Z.Target = Tgt; S.Z.T = 0; S.Z.bDash = true;
	WebAttach(true, Tgt, 0.05);
	S.DashWebT = 0.22;
	SetMode(EWebTravMode::Air, N_zipPull); S.AirT = 0.2; S.ZipCooldown = 0.45; S.DashCount++; S.Facing = Yaw(F); S.Trick = NAME_None;
	Emit(N_webDash);
}

// ------------------------------------------------------------------ forward boost (Q / L1, air or mid-swing)
void UWebTraversalComponent::QuickBoostStart()
{
	FQuick& Q = S.Q;
	const bool bFromSwing = S.Mode == EWebTravMode::Swing;
	if (bFromSwing)
	{ // Explicit boost releases the rope, retaining the exact carried swing velocity.
		bLeaveSwingOK = true; WebRelease(); SetMode(EWebTravMode::Air, S.Vel.Z > 3 ? N_rise : S.Vel.Z > -4 ? N_apex : N_fall); bLeaveSwingOK = false;
		S.AirT = 0; S.ApexZ = FeetZ();
	}
	// A pending swing catch must not take over a boost before its reattach cooldown expires.
	if (S.bWebPending) { S.bWebPending = false; WebRelease(); }
	const FVector ViewForward = Cam ? Cam->CamRot.Vector() : YawDir(S.Facing);
	const double ViewYaw = Cam ? FMath::DegreesToRadians(Cam->CamRot.Yaw) : S.Facing;
	Q.Dir = ForwardBoostDirection(ViewForward, ViewYaw); // latch the view the player actually sees at the press
	if (S.Clock - Q.Last > 1.6) Q.N = 0;
	if (bFromSwing) Q.bRightHand = !S.Sw.bRightHand;
	else Q.bRightHand = !Q.bRightHand;
	static const double KS[] = { 1, 0.8, 0.65, 0.55 };
	Q.K = KS[FMath::Min(Q.N, 3)];
	Q.N++; Q.Last = S.Clock; Q.Seq++;
	Q.T = 0; Q.bActive = true;
	S.DashWebT = 0;
	// Do not replace the air substate, trick identity, clock, held shape or armed flip.
	S.SwingCooldown = FMath::Max(S.SwingCooldown, 0.36); // a held swing button resumes after the impulse
	S.ZipCooldown = FMath::Max(S.ZipCooldown, 0.15);
	Emit(N_quickZip, 0.f, 0.f, float(Q.K));
	QuickImpulse();
}

void UWebTraversalComponent::QuickImpulse()
{
	const FQuick& Q = S.Q;
	S.Vel = ForwardBoostVelocity(S.Vel, Q.Dir, QUICK.Dv * Q.K, VmaxC());
	S.RelT = 0.15; // the boost owns the trajectory; ordinary air control fades back in
	Emit(N_quickBoost, 0.f, 0.f, float(Q.K));
}

void UWebTraversalComponent::StepQuickBoost(double Dt)
{
	FQuick& Q = S.Q;
	if (!Q.bActive) return;
	Q.T += Dt;
	if (Q.T > QUICK.Dur || S.Mode != EWebTravMode::Air) Q.bActive = false;
}

void UWebTraversalComponent::StepPerch(double Hs, FWebTravInput& I)
{
	FPerch& P = S.P;
	if (S.Sub == N_perchLand && S.SubT > 0.5) SetSub(N_perchIdle);
	FVector Out = Flat(P.Normal);
	if (Out.SizeSquared() < 0.09) Out = YawDir(S.Facing);
	Out.Normalize();
	if (I.bJumpPressed)
	{
		if (S.Sub == N_perchLand && S.SubT < 0.25) AnchorLaunch(P.Impact); else PointLaunch(P.Normal, FVector::ZeroVector);
		return;
	}
	if (I.bSwingPressed) { S.Vel = Out * 7 + ZUP * 5.5; SetMode(EWebTravMode::Air, N_jumpLaunch); S.AirT = 0; S.ApexZ = FeetZ(); S.SwingCooldown = 0.12; return; }
	if (I.bDropPressed) { S.Pos += Out * 0.55; S.Vel = Out * 2.5; SetMode(EWebTravMode::Air, N_fall); S.AirT = 0; S.ApexZ = FeetZ(); return; }
	FVector InD = InputDir(I);
	if (InD.SizeSquared() > 0.16 && S.ModeT > 0.25)
	{
		InD.Normalize();
		const bool bAlongEdge = FMath::Abs(FVector::DotProduct(InD, Out)) < 0.5;
		if (!bAlongEdge && (FVector::DotProduct(InD, Out) > 0.3 || !P.bRoof))
		{ // hop down / off
			if (FVector::DotProduct(InD, Out) > 0.3) S.Pos += Out * 0.3;
			S.Vel = InD * 5.5 + ZUP * 4.5; S.Facing = Yaw(InD);
			SetMode(EWebTravMode::Air, N_jumpLaunch); S.AirT = 0; S.ApexZ = FeetZ();
			return;
		}
		// stand up and walk: along the edge or back onto the roof
		S.Facing = Yaw(InD); S.Speed = 1.5;
		if (!bAlongEdge) S.Pos += InD * 0.2;
		EnterGround(N_walk); S.Speed = 1.5;
		return;
	}
	S.Vel = FVector::ZeroVector;
}

// ------------------------------------------------------------------ orientation (root transform)
FQuat UWebTraversalComponent::Orient(double Dt)
{
	const double HV = HLen(S.Vel);
	double Rate = 12;
	FVector Up = ZUP, Fwd = YawDir(S.Facing);
	// bank from the yaw-rate of travel (centripetal lean); UE: + = turning right
	const double VelYaw = Yaw(S.Vel);
	const double YR = HV > 2 ? AngWrap(VelYaw - LastVelYaw) / FMath::Max(Dt, 1e-3) : 0;
	LastVelYaw = VelYaw;
	const double BankT = FMath::Clamp(YR * HV / 22, -1.0, 1.0);
	S.Bank = Damp(S.Bank, BankT, 5, Dt);
	S.Pitch = 0; S.Roll = 0; // Roll + = lean right, Pitch + = lean forward
	switch (S.Mode)
	{
	case EWebTravMode::Ground:
		Rate = S.Sub == N_landRoll ? 20 : 16;
		S.Roll = S.Bank * (S.Speed > RUN ? 0.28 : 0.15);
		if (S.Sub == N_sprint || S.Sub == N_run) S.Pitch = 0.06 * FMath::Min(1.0, S.Speed / SPRINT);
		break;
	case EWebTravMode::Air:
		if (HV > 1.5 && S.Sub != N_zipPull) S.Facing = VelYaw;
		Fwd = YawDir(S.Facing);
		S.Roll = S.Bank * 0.45;
		S.Pitch = S.bDive || S.bGliding ? 0.25 : FMath::Clamp(-S.Vel.Z * 0.008, -0.2, 0.25);
		// round 19 (owner: between-swing poses at speed): a fast descent tips the body toward the flight path -- a sky-dive lean
		// (0.85 rad) when falling fast, head-first (1.25 rad) in a dive / glide; rising, tricks, launches and zips keep the upright frame
		if (S.Sub != N_trick && S.Sub != N_topOut && S.Sub != N_zipPull && S.Sub != N_jumpLaunch && S.Sub != N_wallJump && S.Sub != N_pointLaunch && S.Sub != N_vault)
		{
			const double K = FMath::Clamp((-S.Vel.Z - 4.0) / 14.0, 0.0, 1.0) * FMath::Clamp((S.Vel.Size() - 14.0) / 16.0, 0.0, 1.0);
			S.Pitch = FMath::Lerp(S.Pitch, S.bDive || S.bGliding ? 1.25 : 0.85, K);
			// round 20 (critic r19 body 5: "fallCalm stands upright at 43-51 m/s"): at speed the body axis lies along the flight path --
			// head first, chest to the ground (streamlined), full from AirAlignV1 m/s; the pitch is the angle from world up to the velocity
			const double Sp = S.Vel.Size();
			const double KA = FMath::Clamp((Sp - double(AirAlignV0)) / FMath::Max(1.0, double(AirAlignV1 - AirAlignV0)), 0.0, 1.0);
			if (KA > 0.0 && HV > 1.5)
			{
				const double Ang = FMath::Acos(FMath::Clamp(S.Vel.Z / Sp, -1.0, 1.0));
				S.Pitch = FMath::Lerp(S.Pitch, FMath::Min(Ang, S.bDive || S.bGliding ? double(AirPitchMax) - 0.3 : double(AirPitchMax)), KA);   // round 02: a free fall never turns head-down (the 177 deg tumble of the s4 float)
			}
		}
		Rate = 8;
		if (S.bWebPending && S.PendingShoot > 0.0)
		{ // round 01 (W4): while the strand is in flight the body turns onto the rope frame (hips under the coming anchor), so the attach finds it already there
			// round 06 (F8: body 32-84 deg off upright at the catch): only ~55 % of the turn happens in flight now (and the
			// turn is rate-limited, see the BodyQ step below) -- the rest completes through the attach spring (W4's window);
			// and the pre-turn target never tips more than 20 deg off upright (a near-horizontal rope would otherwise have
			// the body fully tipped at the attach frame)
			const double Wp = 0.55 * FMath::SmoothStep(0.0, 1.0, S.PendingT / FMath::Max(S.PendingShoot, 0.05));
			FVector UpT = (FVector(S.PendingA.Point - S.Pos).GetSafeNormal() + ZUP * 0.12).GetSafeNormal();
			{
				const double Ang = FMath::Acos(FMath::Clamp(UpT.Z, -1.0, 1.0)), CapA = FMath::DegreesToRadians(20.0);
				if (Ang > CapA)
				{
					FVector Side = UpT - ZUP * UpT.Z;
					if (Side.SizeSquared() > 1e-6) UpT = (ZUP * FMath::Cos(CapA) + Side.GetSafeNormal() * FMath::Sin(CapA)).GetSafeNormal();
				}
			}
			Up = FMath::Lerp(Up, UpT, Wp).GetSafeNormal();
			if (S.Vel.SizeSquared() > 1) Fwd = FMath::Lerp(Fwd, S.Vel.GetSafeNormal(), Wp).GetSafeNormal();
			S.Pitch *= (1.0 - Wp);
			Rate = FMath::Lerp(8.0, 14.0, Wp);
		}
		break;
	case EWebTravMode::Swing:
	{
		FSwing& Sw = S.Sw;
		const FVector AD = (Sw.Anchor - S.Pos).GetSafeNormal();
		Up = (AD + ZUP * 0.12).GetSafeNormal();
		if (HV > 1) S.Facing = VelYaw;
		Fwd = S.Vel.SizeSquared() > 1 ? S.Vel : YawDir(S.Facing);
		const FVector RightD(-Sw.Dir.Y, Sw.Dir.X, 0);
		Sw.Bank = Damp(Sw.Bank, FMath::Clamp(BankT + FVector::DotProduct(S.Vel, RightD) * 0.02, -1.0, 1.0), 6, Dt);
		S.Roll = Sw.Bank * 0.5; Rate = 14;
		break;
	}
	case EWebTravMode::Zip:
	{
		// user r4 #15/#17: streamlined pointing AT the anchor for the whole flight, upright only in the last ~0.12 s
		const FZip& Z = S.Z;
		auto SM = [](double X) { X = FMath::Clamp(X, 0.0, 1.0); return X * X * (3 - 2 * X); };
		const bool bFlying = S.Sub == N_zipFlight || S.Sub == N_zipCatch;
		const double K = bFlying ? SM(Z.Tau / 0.08) * (1 - SM((0.12 - (1 - Z.T) * Z.Dur) / 0.12)) : 0;
		const FVector HF = YawDir(S.Facing);
		if (K > 0.01)
		{
			FVector ToT = Z.P2 - S.Pos;
			if (ToT.SizeSquared() < 0.25) ToT = Z.FlightDir;
			ToT.Normalize();
			Up = FMath::Lerp(ZUP, ToT, K).GetSafeNormal();
			const FVector XR = FVector::CrossProduct(ZUP, HF).GetSafeNormal();
			Fwd = FVector::CrossProduct(XR, Up);
			if (Fwd.SizeSquared() < 1e-4) Fwd = HF;
		}
		else Fwd = HF;
		Rate = 14;
		break;
	}
	case EWebTravMode::Perch:
		Fwd = YawDir(S.Facing); Rate = 10;
		break;
	case EWebTravMode::Wall:
	{
		// round 06 (critic r05, ref wall-run): head-up climb-run — body up = along the wall, chest to the wall, torso leaned
		// back off it while running (runK). The browser's "run cycle rotated onto the wall" frame (body up = normal) is gone.
		FWall& W = S.W;
		const bool bMStep = S.Kin.Type == EKin::Mantle && S.Kin.MNum > 0; // round 21: crossing a setback on its surfaces
		const FVector N = bMStep ? S.Kin.CurN : W.Normal;
		const bool bGait = UWebTravAnimInstance::bWallGait;
		const bool bRunning = (S.Sub == N_wallRun && W.bFast) || S.Sub == N_wallZip || (bGait && S.Sub == N_wallRunSide && W.bFast);
		W.RunK = Damp(W.RunK, bRunning ? 1 : 0, bRunning ? 9 : 7, Dt);
		FVector Along = W.Up - N * FVector::DotProduct(W.Up, N);
		if (Along.SizeSquared() < 1e-4) Along = ZUP;
		Along.Normalize();
		// round 21 (critic r20: "the side-run is a plank"; ref side run: raised torso, head leading): a side run raises the body axis
		// WallSideRaiseDeg above the run line toward the wall's up axis (the legs keep striding along the run line)
		if (bGait && S.Sub == N_wallRunSide && WallSideRaiseDeg > 0.f && S.Kin.Type != EKin::Mantle)
		{
			FVector WU = ZUP - N * FVector::DotProduct(ZUP, N);
			FVector Perp = WU - Along * FVector::DotProduct(WU, Along);
			if (Perp.SizeSquared() > 1e-4)
			{
				Perp.Normalize();
				const double Ar = FMath::DegreesToRadians(double(WallSideRaiseDeg)) * FMath::Clamp(W.RunK, 0.0, 1.0);
				Along = (Along * FMath::Cos(Ar) + Perp * FMath::Sin(Ar)).GetSafeNormal();
			}
		}
		Fwd = -N; Up = Along;
		S.Pitch = -(bGait ? double(WallGaitLeanR) : WallRunLean) * W.RunK; // round 19: the IK stride leans further off the wall (hands reach it)
		if (bTrickCancel && S.Sub == N_wallRunSide) S.Pitch *= 0.4; // round 20: a side run keeps the head on the run line (lean 40 %)
		// round 22 (critic r21: side run "a slither", box wider than tall in 29/44 frames): upright parkour runner side-on to the facade --
		// body up = the wall's up axis leaned WallSideLeanDeg forward along the run line and WallSideOutDeg out from the wall (feet reach it),
		// chest along the run line (head leading); SideUpK blends in / out so the swing -> wall and side -> vertical changes do not pop
		{
			const bool bSideUp = bGait && WallSideUpright > 0.5f && S.Sub == N_wallRunSide && W.bFast && !bMStep;
			W.SideUpK = Damp(W.SideUpK, bSideUp ? 1 : 0, bSideUp ? 12 : 8, Dt);
			if (W.SideUpK > 1e-3)
			{
				FVector Zw = ZUP - N * FVector::DotProduct(ZUP, N);
				if (Zw.SizeSquared() < 1e-4) Zw = ZUP;
				Zw.Normalize();
				FVector RunD = W.Up - N * FVector::DotProduct(W.Up, N);
				RunD -= Zw * FVector::DotProduct(RunD, Zw);
				if (RunD.SizeSquared() < 1e-3) RunD = S.Vel - N * FVector::DotProduct(S.Vel, N) - Zw * FVector::DotProduct(S.Vel, Zw);
				if (RunD.SizeSquared() > 1e-4)
				{
					RunD.Normalize();
					const double Ln = FMath::DegreesToRadians(double(WallSideLeanDeg)), Ou = FMath::DegreesToRadians(double(WallSideOutDeg));
					FVector UpU = Zw * FMath::Cos(Ln) + RunD * FMath::Sin(Ln);
					UpU = (UpU * FMath::Cos(Ou) + N * FMath::Sin(Ou)).GetSafeNormal();
					const double K = W.SideUpK;
					Up = FMath::Lerp(Up, UpU, K).GetSafeNormal();
					Fwd = FMath::Lerp(Fwd, RunD, K).GetSafeNormal();
					S.Pitch *= (1 - K);
					if (Up.IsNearlyZero()) Up = UpU;
					if (Fwd.IsNearlyZero()) Fwd = RunD;
				}
			}
		}
		Rate = bMStep ? 26 : 14; // round 21: the body follows the surface round the ledge lip / inner corner
		break;
	}
	default:
		break;
	}
	{
		FVector F2 = Fwd - Up * FVector::DotProduct(Fwd, Up);
		if (F2.SizeSquared() > 1e-6)
		{
			const FQuat Want = FRotationMatrix::MakeFromZX(Up, F2).ToQuat();
			FQuat Next = FQuat::Slerp(S.BodyQ, Want, 1 - FMath::Exp(-Rate * Dt)).GetNormalized();
			// round 06 (A5: the lead-in turn onto the rope between the press and the attach ran 400-700 deg/s on the chest,
			// median 520-623; F8: the body arrived at the catch 32-84 deg off upright): while a strand is in flight and
			// through the first 0.4 s of the swing the body-frame turn is rate-limited, so the turn onto the rope completes
			// inside W4's 0.15-0.35 s window instead of ahead of the attach; a wall entry right off a swing eases in too
			// (its snap landed inside the attach window of the W4/A5 probes: +27 deg in one frame)
			// round 10 (critic r09 gap 3: the one-frame s3 snap lands at Sw.T = 0.43, the first frame PAST this gate -- an attach
			// fresh off a wallJump still had ~20-50 deg of turn left when the limit fell away, and it landed at once): the gate
			// now holds until the frame has CONVERGED (residual <= 2 deg), capped at 0.9 s; identical when it converged on time.
			const bool bWebLead = (S.Mode == EWebTravMode::Air && S.bWebPending)
				|| (S.Mode == EWebTravMode::Swing && (S.Sw.T < 0.4 || (S.Sw.T < 0.9 && S.BodyQ.AngularDistance(Want) > FMath::DegreesToRadians(2.0))))
				|| (S.Mode == EWebTravMode::Wall && S.ModeT < 0.35 && S.PrevMode == EWebTravMode::Swing);
			if (bWebLead)
			{
				const double Step = S.BodyQ.AngularDistance(Next), MaxStep = FMath::DegreesToRadians(S.Mode == EWebTravMode::Wall ? 380.0 : 190.0) * Dt;
				if (Step > MaxStep) Next = FQuat::Slerp(S.BodyQ, Next, MaxStep / Step).GetNormalized();
			}
			S.BodyQ = Next;
		}
	}
	// round 06: roll / pitch leans are springs too — mode changes (swing -> air release) used to pop them in one frame
	S.RollA = Damp(S.RollA, S.Roll, 14, Dt); S.PitchA = Damp(S.PitchA, S.Pitch, 14, Dt);
	FQuat Q = S.BodyQ;
	if (S.RollA != 0) Q = Q * FQuat(FVector(1, 0, 0), -S.RollA);
	if (S.PitchA != 0) Q = Q * FQuat(FVector(0, 1, 0), S.PitchA);
	// root position = feet (along the body's up axis), with curb step smoothing
	S.StepOff = Damp(S.StepOff, 0, 16, Dt);
	const FVector BodyUp = S.BodyQ.GetUpVector();
	if (S.Mode == EWebTravMode::Wall)
	{
		const FWall& W = S.W;
		const double ToPlane = W.Dist;
		const FVector SurfN = (S.Kin.Type == EKin::Mantle && S.Kin.MNum > 0) ? S.Kin.CurN : W.Normal; // round 21
		// feet 0.30 m off the wall when crawling, WallRunFootOff when running (the striding foot reaches the wall)
		double FootOff = FMath::Lerp(0.30, UWebTravAnimInstance::bWallGait ? double(WallGaitFootOffR) : WallRunFootOff, W.RunK);
		FootOff = FMath::Lerp(FootOff, double(WallSideFootOff), W.SideUpK); // round 22: upright side run (feet ~.1 m off the facade after the out-tilt)
		RootPos = S.Pos + SurfN * (FootOff - ToPlane) - BodyUp * H;
	}
	else RootPos = S.Pos - BodyUp * H;
	if (S.Mode == EWebTravMode::Ground || S.Mode == EWebTravMode::Perch) RootPos.Z = S.Pos.Z - H + S.StepOff;
	return Q.GetNormalized();
}

void UWebTraversalComponent::WriteAnim(const FQuat& Q)
{
	FWebTravAnim& A = Anim;
	EWebTravMode M = S.Mode;
	if (M == EWebTravMode::Ground && IsLand(S.Sub)) M = EWebTravMode::Land;
	if (M != A.Mode) A.FromMode = A.Mode;
	A.Mode = M; A.Sub = S.Sub; A.T = float(S.SubT); A.ModeT = float(S.ModeT);
	A.Velocity = S.Vel * 100.0;
	A.Speed = float(M == EWebTravMode::Ground || M == EWebTravMode::Land ? S.Speed : S.Vel.Size());
	A.bGrounded = S.bGrounded;
	A.JumpCharge = float(S.bCharging || S.Sub == N_jumpLaunch ? S.JumpCharge : 0);
	const bool bSwing = S.Mode == EWebTravMode::Swing;
	A.Swing.Phase = float(S.Sw.Phase); A.Swing.Bank = float(S.Sw.Bank); A.Swing.Tension = bSwing ? float(S.Sw.Tension) : 0.f;
	A.Swing.Anchor = S.Sw.Anchor * 100.0; A.Swing.bRightHand = S.Sw.bRightHand; A.Swing.RopeLengthCm = float(S.Sw.Rope * 100.0);
	A.Swing.Angle = bSwing ? float(S.Sw.Angle) : 0.f; A.Swing.Kick = bSwing ? float(S.Sw.Kick) : 0.f; A.Swing.Chain = S.Chain;
	const bool bZip = S.Mode == EWebTravMode::Zip;
	A.Zip.Target = S.Z.Target * 100.0; A.Zip.T = bZip ? float(S.Z.T) : 0.f;
	A.Zip.Phase = !bZip ? NAME_None : S.Sub == N_zipFire ? N_fire : S.Sub == N_zipFlight ? N_flight : S.Sub == N_zipCatch ? N_catch : NAME_None;
	A.Zip.bWebs = bZip && S.Z.bWebs; A.Zip.Pitch = bZip ? float(S.Z.Pitch) : 0.f; A.Zip.Dir = S.Z.FlightDir;
	A.Zip.bDash = S.Z.bDash && S.Sub == N_zipPull && S.Mode == EWebTravMode::Air;
	A.Wall.Normal = S.W.Normal; A.Wall.Move = S.W.Move; A.Wall.bFast = S.W.bFast; A.Wall.Phase = float(S.W.Phase);
	A.Wall.RunK = S.Mode == EWebTravMode::Wall ? float(S.W.RunK) : 0.f;
	A.Wall.Point = S.W.Point * 100.0; A.Wall.Up = S.W.Up;
	A.Wall.SideUp = S.Mode == EWebTravMode::Wall ? float(S.W.SideUpK) : 0.f; // round 22
	if (S.Mode == EWebTravMode::Wall && S.Kin.Type == EKin::Mantle && S.Kin.MNum > 0) { A.Wall.Normal = S.Kin.CurN; A.Wall.Point = S.Kin.CurPt * 100.0; } // round 21: the support surface
	A.Perch.Point = S.P.Pos * 100.0; A.Perch.Normal = S.P.Normal; A.Perch.Kind = S.P.Kind; A.Perch.Impact = S.P.Impact * 100.0;
	A.LandingSeverity = float(S.LandSeverity); A.Trick = S.Trick; A.TrickSide = float(S.TrickSide); A.TrickDur = float(S.TrickDur);
	A.bDive = S.bDive || S.bGliding; A.bGlide = S.bGliding;
	A.FacingDeg = float(FMath::RadiansToDegrees(S.Facing));
	A.BodyQ = Q; A.RootPos = RootPos * 100.0; A.StepOffset = float(S.StepOff * 100.0);
	A.bQuickActive = S.Q.bActive; A.QuickT = float(S.Q.T); A.bQuickRightHand = S.Q.bRightHand;
	A.WebShotK = S.bWebPending && S.PendingShoot > 0.0 ? float(FMath::Clamp(S.PendingT / S.PendingShoot, 0.0, 1.0)) : -1.f;
	A.NoAnchorT = float(S.NoAnchorReach); A.bNoAnchorRight = S.bNoAnchorRight; A.NoAnchorAim = S.NoAnchorAim;
}

// ------------------------------------------------------------------ main update
void UWebTraversalComponent::UpdateTraversal(double Dt, FWebTravInput I)
{
	Events.Reset();
	if (!bWorldReady || !Anchors) return;
	LastInput = I;
	if (I.bZipPressed) LastZipFrom = FString::Printf(TEXT("%d/%s"), int32(S.Mode), *S.Sub.ToString());
	{ // round 17: route direction = horizontal velocity smoothed over ~1.5 s (the roofline capsule of FlowRoofTarget follows the route, not a
	  // swing's sideways / vertical moment)
		const FVector HVn(S.Vel.X, S.Vel.Y, 0.0);
		const double Hn = HVn.Size();
		if (RouteDir.IsNearlyZero()) RouteDir = Hn > 1.0 ? HVn / Hn : YawDir(S.Facing);
		else if (Hn > 4.0) RouteDir = FMath::Lerp(RouteDir, HVn / Hn, FMath::Clamp(Dt / 1.5, 0.0, 1.0)).GetSafeNormal();
	}
	S.JumpBuf = I.bJumpPressed ? 0.22 : FMath::Max(0.0, S.JumpBuf - Dt);
	S.TrickBuf = I.bTrickPressed ? 0.4 : FMath::Max(0.0, S.TrickBuf - Dt);
	S.SubT += Dt; S.ModeT += Dt;
	if (S.Mode == EWebTravMode::Swing) S.SinceSwing = 0;
	else
	{
		S.SinceSwing += Dt;
		if (S.SinceSwing > CHAIN_BUF && S.Chain) { S.Chain = 0; Emit(N_swingChain, 0.f, 0.f, 0.f); }
	}
	S.SwingCooldown -= Dt; S.WallCooldown -= Dt; S.ZipCooldown -= Dt; S.Clock += Dt;
	if (S.NoAnchorReach >= 0) { S.NoAnchorReach += Dt; if (S.NoAnchorReach > 0.30) S.NoAnchorReach = -1; }
	if (S.DashWebT > 0) { S.DashWebT -= Dt; if (S.DashWebT <= 0 && S.Mode == EWebTravMode::Air) WebRelease(); }
	// zip targeting (reticle) — suppressed while swinging fast / zipping
	if (Cam)
	{
		const FVector Eye = S.Pos + FVector(0, 0, 0.5);
		const bool bEnabled = S.Mode != EWebTravMode::Zip && !(S.Mode == EWebTravMode::Swing && S.Vel.Size() > 30);
		const bool bPerched = S.Mode == EWebTravMode::Perch;
		FTravView View;
		View.Pos = Cam->CamPos;
		const FRotationMatrix RM(Cam->CamRot);
		View.Fwd = RM.GetUnitAxis(EAxis::X); View.Right = RM.GetUnitAxis(EAxis::Y); View.Up = RM.GetUnitAxis(EAxis::Z);
		View.TanHalfV = FMath::Tan(FMath::DegreesToRadians(Cam->OutVFov * 0.5));
		View.TanHalfH = View.TanHalfV * 16.0 / 9.0;
		// round 15: while the side-on trick camera frames a flip (now on the sun-away side, often facing away from the route's zip
		// points) the reticle aims along the chase heading -- the player's aim, not the cinematic view (probe r15 b: the roof point
		// left the side view at 2.67 s and the 2.88 s zip found nothing)
		if (Cam->FlipK > 0.3)
		{
			const FVector F = Cam->ForwardFlat();
			const FRotator AimR(6.0, FMath::RadiansToDegrees(FMath::Atan2(F.Y, F.X)), 0.0);
			const FRotationMatrix AM(AimR);
			View.Pos = S.Pos - F * 3.8 + FVector(0, 0, 1.2);
			View.Fwd = AM.GetUnitAxis(EAxis::X); View.Right = AM.GetUnitAxis(EAxis::Y); View.Up = AM.GetUnitAxis(EAxis::Z);
		}
		FVector PerchOut = Flat(S.P.Normal);
		if (PerchOut.SizeSquared() > 0.09) PerchOut.Normalize(); else PerchOut = YawDir(S.Facing);
		Anchors->UpdateTargeting(Dt, View, Eye, bEnabled, bPerched ? &S.P.Pos : nullptr,
			S.Mode == EWebTravMode::Air || S.Mode == EWebTravMode::Swing, bPerched ? &PerchOut : nullptr);
	}
	// E / MMB: zip to the highlighted point, or air web-dash
	// round 19 (owner playtest 2026-10-01: "pressing E to go to the nearest place doesn't work when you're running on the side of the
	// buildings"): E works from EVERY mode -- a vault / corner wrap / wall hop in progress is cut; a wall run, crawl or side run zips to the
	// highlighted point, else to the nearest place (the top edge of this facade, else the nearest visible roof edge / corner), and only
	// then bursts up the facade (WallZip); a roof run / perch with nothing highlighted zips to the nearest place too
	if (I.bZipPressed && S.ZipCooldown <= 0 && S.Mode != EWebTravMode::Zip)
	{
		bLeaveSwingOK = true; // explicit button press: the only non-RMB way the held web is switched
		if (S.Kin.Type != EKin::None) { S.Kin.Type = EKin::None; S.Vel = FVector::ZeroVector; }
		FTravZipPoint T;
		bool bHas = Anchors->HasTarget();
		FName Why = TEXT("highlighted");
		if (bHas) T = Anchors->Best();
		else if (NearestZip(T, Why)) bHas = true;
		if (bHas)
		{
			if (S.Mode == EWebTravMode::Swing) WebRelease();
			if (S.Mode == EWebTravMode::Wall) { S.W.bZipWeb = false; S.W.bLockDir = false; }
			StartZip(T); S.ZipCooldown = 0.25;
			LastZipWhy = Why;
		}
		else if (S.Mode == EWebTravMode::Wall) { WallZip(); LastZipWhy = TEXT("wallZip"); } // user r9w: burst up a facade taller than the zip range
		else if (S.Mode == EWebTravMode::Perch) { PointLaunch(S.P.Normal, FVector::ZeroVector); S.ZipCooldown = 0.25; LastZipWhy = TEXT("pointLaunch"); } // never a dead button on a perch
		else if (S.Mode == EWebTravMode::Air || S.Mode == EWebTravMode::Swing) { if (S.Mode == EWebTravMode::Swing) WebRelease(); WebDash(); LastZipWhy = TEXT("webDash"); }
		else LastZipWhy = TEXT("none");
		UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV zip press: %s -> %s"), *LastZipFrom, *LastZipWhy.ToString());
		bLeaveSwingOK = false;
	}
	// Q / L1: quick web boost (air, or mid-swing); a press up to 0.25 s early is buffered until the cooldown ends
	S.QuickBuf = I.bQuickPressed ? 0.25 : FMath::Max(0.0, S.QuickBuf - Dt);
	if (S.QuickBuf > 0 && S.Kin.Type == EKin::None && (S.Mode == EWebTravMode::Air || S.Mode == EWebTravMode::Swing) && S.Clock - S.Q.Last >= QUICK.Cd)
	{
		S.QuickBuf = 0; QuickBoostStart();
	}
	StepQuickBoost(Dt);
	const int32 NSteps = FMath::Max(1, FMath::CeilToInt(Dt / (1.0 / 120.0) - 1e-6));
	const double Hs = Dt / NSteps;
	for (int32 K = 0; K < NSteps; ++K)
	{
		const EWebTravMode Pre = S.Mode;
		const FVector PrevPos = S.Pos;
		const bool bFreeFlight = S.Kin.Type == EKin::None && (S.Mode == EWebTravMode::Air || S.Mode == EWebTravMode::Swing);
		if (S.Kin.Type == EKin::WallHop) StepWallHop(Hs);
		else if (S.Kin.Type != EKin::None && S.Mode != EWebTravMode::Zip) StepKin(Hs);
		else if (S.Mode == EWebTravMode::Ground) StepGround(Hs, I);
		else if (S.Mode == EWebTravMode::Air) StepAir(Hs, I);
		else if (S.Mode == EWebTravMode::Swing) StepSwing(Hs, I);
		else if (S.Mode == EWebTravMode::Wall) StepWall(Hs, I);
		else if (S.Mode == EWebTravMode::Zip) StepZip(Hs, I);
		else if (S.Mode == EWebTravMode::Perch) StepPerch(Hs, I);
		if (K == 0 || S.Mode != Pre) { I.bJumpPressed = false; I.bSwingPressed = false; I.bDropPressed = false; }
		// round 20: the merged facades are thin triangle surfaces now (not boxes): a fast body could step through one between two
		// push-outs. Free flight (air / swing) sweeps its sub-step and stops short of a wall it would pass (the push-out then sees the contact).
		if (AntiTunnel > 0.f && bFreeFlight && S.Mode == Pre && S.Kin.Type == EKin::None && TravWorld.SolidMode == 2)
		{
			const FVector D = S.Pos - PrevPos;
			const double L = D.Size();
			double HitD = 0.0; FVector HitN;
			if (L > 0.04 && TravWorld.SweepSolid(PrevPos, S.Pos, 0.2, HitD, HitN) && FMath::Abs(HitN.Z) < 0.6)
			{
				S.Pos = PrevPos + D / L * FMath::Max(0.0, HitD - 0.02);
				const double VN = FVector::DotProduct(S.Vel, HitN);
				if (VN < 0) S.Vel -= HitN * VN;
				++TunnelStops;
			}
		}
	}
	// user r9w: wall zip cut short (wall jump / roof hop / fell off): its web drops
	if (S.W.bZipWeb && S.Sub != N_wallZip) { S.W.bZipWeb = false; if (S.Mode != EWebTravMode::Swing && S.Mode != EWebTravMode::Zip) WebRelease(true); }
	// safety net: never below the terrain / inside a building
	{
		const double G0 = TravWorld.GroundHeight(S.Pos.X, S.Pos.Y, S.Pos.Z - H + 0.3);
		if (S.Pos.Z - H < G0 - 0.05 && S.Mode != EWebTravMode::Wall)
		{
			S.Pos.Z = G0 + H;
			if (S.Vel.Z < 0) S.Vel.Z = 0;
			if (S.Mode == EWebTravMode::Air) Land(G0, I);
		}
		if (S.Mode != EWebTravMode::Zip && S.Mode != EWebTravMode::Wall && TravWorld.Inside(S.Pos + FVector(0, 0, 0.3)))
		{ // resolved inside a solid: pop ZUP only onto a surface within reach, else leave it to the horizontal push-out
			const double FY0 = S.Pos.Z - H, Top = TravWorld.GroundHeight(S.Pos.X, S.Pos.Y, FY0 + 1.2);
			const bool bOkUp = Top > FY0 - 0.3 && Top - FY0 < 1.2 && !TravWorld.Inside(FVector(S.Pos.X, S.Pos.Y, Top + 0.35));
			if (bOkUp) S.Pos.Z = Top + H;
			else { FTravContact C; Collide(STEP, R + 0.05, C); }
			if (bOkUp || !TravWorld.Inside(S.Pos + FVector(0, 0, 0.3)))
			{ // a held web is never dropped by the safety net
				if (S.Mode == EWebTravMode::Swing) { if (S.Vel.Z < 0) S.Vel.Z = 0; }
				else if (bOkUp) { S.Vel = FVector::ZeroVector; WebRelease(); EnterGround(N_idle); }
			}
		}
	}
	if (S.Mode != EWebTravMode::Air) { S.bSky = false; S.bFlowFlip = false; S.ArmedFlip = NAME_None; } // round 10: a sky launch ends at the next web / landing / wall / zip
	S.bGrounded = S.Mode == EWebTravMode::Ground || S.Mode == EWebTravMode::Perch;
	if (S.Mode == EWebTravMode::Ground) S.DashCount = 0;
	FinalQ = Orient(Dt);
	WriteAnim(FinalQ);
	for (FWebTravStrand& St : Strands)
	{
		if (!St.bActive) continue;
		St.Age += float(Dt); St.BlendT = FMath::Min(1.f, St.BlendT + float(Dt) / 0.15f);
		if (St.ReleaseT >= 0.f) { St.ReleaseT += float(Dt); if (St.ReleaseT > 0.42f) St.bActive = false; }   // round 09: the W8 retract now runs 0.36 s + fade to 0.38
	}
}

void UWebTraversalComponent::Teleport(const FVector& P, double YawRad)
{
	S.Pos = P;
	const double F = FloorAt(P.X, P.Y, P.Z);
	if (S.Pos.Z < F + H) S.Pos.Z = F + H;
	bLeaveSwingOK = true;
	S.Vel = FVector::ZeroVector; S.Kin.Type = EKin::None; WebRelease();
	S.Facing = YawRad; S.Speed = 0; S.StepOff = 0; S.Trick = NAME_None; S.bDive = false; S.bCharging = false;
	if (S.Pos.Z - H - F < 0.05) EnterGround(N_idle);
	else { SetMode(EWebTravMode::Air, N_fall); S.AirT = 0; S.ApexZ = FeetZ(); }
	bLeaveSwingOK = false;
	S.BodyQ = FQuat(ZUP, YawRad);
	LastVelYaw = YawRad;
}
