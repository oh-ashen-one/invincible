// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Traversal/WebTravCamera.h"
#include "Traversal/WebTravWorld.h"
#include "WebHomage.h"
#include "Components/PrimitiveComponent.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace
{
	double Damp(double A, double B, double Rate, double Dt) { return A + (B - A) * (1.0 - FMath::Exp(-Rate * Dt)); }
	double WrapA(double A) { return FMath::Atan2(FMath::Sin(A), FMath::Cos(A)); }
	double AngDamp(double A, double B, double Rate, double Dt) { return A + WrapA(B - A) * (1.0 - FMath::Exp(-Rate * Dt)); }
	double Smooth(double X, double E0, double E1) { const double T = FMath::Clamp((X - E0) / (E1 - E0), 0.0, 1.0); return T * T * (3.0 - 2.0 * T); }
	// Critically damped spring (SmoothDamp): frame-rate independent, continuous position AND velocity.
	double SD(double& V, double& Vel, double Target, double St, double Dt)
	{
		const double W = 2.0 / FMath::Max(1e-4, St), X = W * Dt, E = 1.0 / (1.0 + X + 0.48 * X * X + 0.235 * X * X * X);
		const double Ch = V - Target, Tmp = (Vel + W * Ch) * Dt;
		Vel = (Vel - W * Tmp) * E;
		V = Target + (Ch + Tmp) * E;
		return V;
	}
	double SDA(double& V, double& Vel, double Target, double St, double Dt) { return SD(V, Vel, V + WrapA(Target - V), St, Dt); }
	void SDV(FVector& V, FVector& Vel, const FVector& Target, double St, double Dt)
	{
		for (int32 A = 0; A < 3; ++A) { SD(V[A], Vel[A], Target[A], St, Dt); }
	}
	double Noise(double T, double S) { return FMath::Sin(T * 1.7 + S) * 0.5 + FMath::Sin(T * 3.1 + S * 2.3) * 0.3 + FMath::Sin(T * 5.3 + S * 4.1) * 0.2; }
	FName N_vault(TEXT("vault")), N_wallRun(TEXT("wallRun")), N_topOut(TEXT("topOut"));
	bool CameraProbeOn(const FTravCamInput& P)
	{
		static const bool bEnabled = FParse::Param(FCommandLine::Get(), TEXT("WHCamProbe"));
		return bEnabled && P.Pos.X > 290.0 && P.Pos.X < 310.0 && P.Pos.Y > 175.0 && P.Pos.Y < 195.0 && P.Pos.Z > 90.0 && P.Pos.Z < 102.0;
	}
	FBox BodyEnvelope(const FTravCamInput& P)
	{
		FBox B = P.BodyBounds.IsValid ? P.BodyBounds : FBox(FVector(-0.65, -0.65, -1.05), FVector(0.65, 0.65, 1.15));
		// FlipExtent also contains the next open shape: the preceding frame's compact skeleton alone cannot protect its limbs.
		if (P.FlipExtent > 0.f)
		{
			const double Half = double(P.FlipExtent) * 0.5;
			B.Min.Z = FMath::Min(B.Min.Z, -Half); B.Max.Z = FMath::Max(B.Max.Z, Half);
		}
		return B.ShiftBy(P.Pos);
	}
	// Largest per-axis angle of the FULL body, normalized by the rectangular frustum's half angles.
	// A chest can be inside the frame while a foot is already past its edge, especially after a collision pull-in.
	double BodyFrameEdge(const FBox& B, const FVector& C, const FRotator& R, double HalfV, double HalfH)
	{
		const FRotationMatrix M(R);
		double Edge = 0.0;
		for (int32 I = 0; I < 8; ++I)
		{
			const FVector Q(I & 1 ? B.Max.X : B.Min.X, I & 2 ? B.Max.Y : B.Min.Y, I & 4 ? B.Max.Z : B.Min.Z);
			const FVector D = Q - C;
			const double Depth = FVector::DotProduct(D, M.GetUnitAxis(EAxis::X));
			if (Depth <= 0.25) return 2.0;
			Edge = FMath::Max(Edge, FMath::Max(FMath::Abs(FMath::Atan2(FVector::DotProduct(D, M.GetUnitAxis(EAxis::Y)), Depth)) / HalfH,
				FMath::Abs(FMath::Atan2(FVector::DotProduct(D, M.GetUnitAxis(EAxis::Z)), Depth)) / HalfV));
		}
		return Edge;
	}
	// Bounded read-only forecast: current velocity / measured gravity, slide against the SAME traversal solids, then
	// stop at the standing feet clearance. It predicts no future input, trick impulse, wall-run or anchor attachment.
	FVector ForecastHero(const FTravCamInput& P, const FWebTravWorld& World, double T, double Gravity)
	{
		FVector At = P.Pos, Move = P.Vel * T + FVector(0, 0, -0.5 * Gravity * T * T);
		for (int32 I = 0; I < 3 && Move.SizeSquared() > 1e-6; ++I)
		{
			double HitD = 0.0; FVector Normal;
			if (!World.SweepSolid(At, At + Move, 0.36, HitD, Normal)) { At += Move; break; }
			const FVector End = At + Move;
			At += Move.GetSafeNormal() * FMath::Max(0.0, HitD - 0.05);
			Move = End - At;
			Move -= Normal * FMath::Min(0.0, FVector::DotProduct(Move, Normal));
		}
		At.Z = FMath::Max(At.Z, World.GroundHeight(At.X, At.Y, At.Z + 1.0) + 0.95);
		return At;
	}
	FVector FloorSafeSpot(FVector Spot, const FVector& Hero, const FWebTravWorld& World, double Lift)
	{
		Spot.Z = FMath::Max(Spot.Z + FMath::Max(0.0, Lift), World.GroundHeight(Spot.X, Spot.Y, Hero.Z + 4.0) + 0.4);
		return Spot;
	}
}

void FWebTravCamera::Reset(const FVector& Pos, double InYaw)
{
	Target = Pos + FVector(0, 0, 0.55);
	Yaw = InYaw; Pitch = 0.14; CollDist = Dist;
	bAutoInit = false;
	LagOff = LagOffV = JumpOff = JumpOffV = FVector::ZeroVector;
	bHasLastGoal = false; AnchorLean = 0.0; AnchorLeanV = 0.0;
	bChaseInit = false; UserPitch = 0.0; OccYawGoal = OccUpGoal = 0.0;
	GndCrane = GndCraneV = GndCraneGoal = GndClearT = 0.0; bGndLensHold = false; GndStopped = 0; // round 24
	bOutInit = false; // round 13: a teleport / reset is allowed to move the view at once
	bHaveComposeHero = false;
	RoofLift = RoofLiftV = 0.0;
	OcclBoostK = 0.0;
	bFlipObstacleOut = bHaveFlipVelocity = false; ForecastGravity = 10.8;
	FlipFrameTail = 0.0;
}

void FWebTravCamera::ApplyLook(const FVector2D& Look)
{
	if (FMath::Abs(Look.X) + FMath::Abs(Look.Y) > 0.001) LastLook = 0.0;
	if (FMath::Abs(Look.X) > 0.0005) LookYawDir = Look.X > 0.0 ? 1 : -1; // round 24
	Yaw += Look.X * Sens;
	Pitch = FMath::Clamp(Pitch + Look.Y * Sens, -0.9, 1.25);
	UserPitch = FMath::Clamp(UserPitch + Look.Y * Sens, -0.6, 0.6);
}

void FWebTravCamera::Update(double Dt, const FTravCamInput& P, const FWebTravWorld& World)
{
	Dt = FMath::Min(Dt, 0.1);
	FlipFrameTail = P.bFlip ? 0.5 : FMath::Max(0.0, FlipFrameTail - Dt);
	if (P.bFlip && bHaveFlipVelocity && Dt > 1e-5)
		ForecastGravity = FMath::Clamp((LastFlipVz - P.Vel.Z) / Dt, 0.0, 24.0);
	LastFlipVz = P.Vel.Z; bHaveFlipVelocity = P.bFlip;
	Time += Dt; LastLook += Dt;
	const FVector& Vel = P.Vel;
	const double Speed = Vel.Size(), HS = FVector2D(Vel.X, Vel.Y).Size();
	const EWebTravMode M = P.Mode;
	const bool bSwinging = M == EWebTravMode::Swing, bAir = M == EWebTravMode::Air || M == EWebTravMode::Zip, bDive = P.bDive;
	const FString SubS = P.Sub.ToString();
	const bool bLandSub = SubS.StartsWith(TEXT("land")), bLedgeSub = SubS.StartsWith(TEXT("ledge"));

	// ---- auto recenter behind the direction of travel
	const double Blend = FMath::Clamp((LastLook - 0.9) * 1.5, 0.0, 1.0);
	if (LastLook < 0.05 || !bAutoInit) { AutoYaw = Yaw; AutoYawV = 0; AutoPitch = Pitch; AutoPitchV = 0; bAutoInit = true; }
	{
		bool bWY = false, bWP = false;
		const double HeightPitch = FMath::Clamp((P.HAbove - HeightPitchRef) * HeightPitchK, -0.1, 0.55);
		double WantYaw = 0, WantPitch = 0, Rate = 0;
		if (M == EWebTravMode::Wall)
		{
			if (P.ModeT > 0.3) { WantYaw = FMath::Atan2(-P.WallNormal.Y, -P.WallNormal.X); Rate = 1.6; bWY = true; }
			WantPitch = P.Sub == N_wallRun ? -0.08 : -0.05; bWP = true;
		}
		else if (M == EWebTravMode::Perch) { WantYaw = P.Facing; Rate = 1.4; WantPitch = 0.3; bWY = bWP = true; }
		else if (bDive && HS <= 2.5) { WantPitch = 0.75 + 0.4 * Smooth(-Vel.Z, 18, 45); bWP = true; }
		else if (bSwinging && P.bHasSwingDir)
		{ // frame the ARC: recenter behind the swing plane direction, not the instantaneous velocity
			WantYaw = FMath::Atan2(P.SwingDir.Y, P.SwingDir.X); Rate = 2.2; bWY = true;
			// round 02: height term (browser: 0.1 - vz*0.006) so the horizon travels with the pendulum
			WantPitch = FMath::Clamp(0.04 + HeightPitch - Vel.Z * 0.0015, -0.15, 0.6); bWP = true;
		}
		else if (HS > 2.5)
		{
			WantYaw = FMath::Atan2(Vel.Y, Vel.X); bWY = true;
			Rate = FMath::Clamp((HS - 2.0) / 10.0, 0.0, 1.0) * (bAir ? 1.8 : 1.3);
			WantPitch = bDive ? 0.24 + 0.1 * Smooth(-Vel.Z, 18, 45) : bAir ? FMath::Clamp(0.08 + HeightPitch - Vel.Z * 0.003, -0.1, AirPitchDownMax) : 0.14; bWP = true;   // round 03: free flight after a release looks down at most ~10 deg
		}
		OccHold -= Dt;
		if (OccHold > 0) { bWY = false; bWP = false; }
		if (bWY) SDA(AutoYaw, AutoYawV, WantYaw, 0.5, Dt);
		else if (AutoRate < 0.05) { AutoYaw = Yaw; AutoYawV = 0; }
		if (bWP) SD(AutoPitch, AutoPitchV, WantPitch, (bSwinging || bAir) && !bDive ? 0.18 : 0.5, Dt); // round 02: pitch tracks height closer
		else if (AutoPRate < 0.05) { AutoPitch = Pitch; AutoPitchV = 0; }
		SD(AutoRate, AutoRateV, bWY ? Rate : 0.0, 0.35, Dt);
		SD(AutoPRate, AutoPRateV, bWP ? (bDive ? 2.4 : (bSwinging || bAir) ? 7.0 : 1.1) : 0.0, 0.35, Dt);
		const double YawPre = Yaw;
		if (Blend > 0)
		{
			Yaw = AngDamp(Yaw, AutoYaw, FMath::Max(0.0, AutoRate) * Blend, Dt);
			Pitch = Damp(Pitch, AutoPitch, FMath::Max(0.0, AutoPRate) * Blend, Dt);
		}
		// round 25 (c 9.85 s, see PerchHold in the header): perched, the recenter never turns the view onto a lifted / blocked chase spot
		PerchYawHeld = 0;
		if (PerchHold > 0.0 && M == EWebTravMode::Perch && FMath::Abs(WrapA(Yaw - YawPre)) > 1e-7 && PerchSpotBad(Yaw, P, World) && !PerchSpotBad(YawPre, P, World))
		{
			Yaw = YawPre; AutoYaw = Yaw; AutoYawV = 0.0; PerchYawHeld = 1;
		}
	}
	// ---- follow pivot: soft-clamped velocity lag + unexplained-displacement absorber
	const FVector Goal = P.Pos + FVector(0, 0, 0.55);
	SD(LagK, LagKV, bSwinging || bAir ? 0.03 : M == EWebTravMode::Wall ? 0.02 : 0.012, 0.4, Dt);
	SD(LagMax, LagMaxV, bSwinging || bAir ? 0.8 : 0.5, 0.4, Dt);
	FVector WantLag = Vel * -LagK;
	{ const double L = WantLag.Size(); if (L > 1e-4) WantLag *= LagMax * FMath::Tanh(L / LagMax) / L; }
	SDV(LagOff, LagOffV, WantLag, 0.3, Dt);
	if (bHasLastGoal)
	{
		const FVector Mv = Goal - LastGoal;
		FVector Jump = Mv - Vel * Dt;
		const FVector J2 = Mv - LastVel * Dt;
		if (J2.SizeSquared() < Jump.SizeSquared()) Jump = J2;
		const double JL = Jump.Size();
		if (JL > 0.06 && JL < 3.0) JumpOff -= Jump;
		else if (JL >= 3.0) { JumpOff = FVector::ZeroVector; JumpOffV = FVector::ZeroVector; }
	}
	bHasLastGoal = true; LastGoal = Goal; LastVel = Vel;
	if (JumpOff.Size() > 1.2) JumpOff = JumpOff.GetSafeNormal() * 1.2;
	SDV(JumpOff, JumpOffV, FVector::ZeroVector, 0.3, Dt);
	Target = Goal + LagOff + JumpOff;
	// velocity look-ahead: vertical damped hard while swinging / airborne, capped at 2 m
	{
		const double LW = bSwinging || bAir ? 0.06 : 0.04;
		FVector LeadW(Vel.X * LW, Vel.Y * LW, Vel.Z * (bSwinging || bAir ? 0.015 : LW));
		if (LeadW.Size() > 2.0) LeadW = LeadW.GetSafeNormal() * 2.0;
		SDV(Lead, LeadV, LeadW, 0.45, Dt);
	}
	// ---- distance / height / FOV by context
	double WantDist = 4.0, WantH = 0.0, WantSide = 0.32;
	if (M == EWebTravMode::Ground || M == EWebTravMode::Land) { WantDist = 3.9 + FMath::Clamp((Speed - 8.0) * 0.07, 0.0, 0.7); WantSide = 0.35; }
	else if (bSwinging) { WantDist = 3.6 + FMath::Clamp((Speed - 12.0) * 0.025, 0.0, 0.7); WantH = 0.35 + P.Tension * 0.25; WantSide = 0.15; }
	else if (bAir) { WantDist = bDive ? 3.9 : 3.8 + FMath::Clamp((Speed - 12.0) * 0.025, 0.0, 0.7); WantH = bDive ? 0.9 : 0.15; WantSide = 0.2; }
	else if (M == EWebTravMode::Wall) { WantDist = 4.8; WantH = P.Sub == N_wallRun ? 0.2 : 0.0; WantSide = 0.0; }
	else if (M == EWebTravMode::Perch) { WantDist = 4.3; WantH = 0.25; WantSide = 0.4; }
	if (M == EWebTravMode::Land || bLandSub) WantDist = 4.2;
	if (bLedgeSub) { WantH = 1.4; Pitch = Damp(Pitch, 0.42, 4, Dt); }
	// round 07 (critic r06 axis 6: "no FOV kick ... momentum reads flat"): the speed term grows over 14-40 m/s and
	// fades out while the trick camera is in (TRICK_CAMERA_SPEC TC4/TC12 pin the trick FOV; T14's hFOV 100-110 band = vFOV
	// 68-76 at 16:9). The chase closed loop is FOV-normalized against exactly this term
	// (see ComposeChase), so it holds the hero's size as if the kick never happened instead of fighting its transient (the
	// r07-first-pass 9 deg unnormalized kick pushed the s4 swing p90 over the P1 band top; a saturated 8 deg kick on the
	// fast chains shrank the s1 hero to the band floor -- 5 deg normalized keeps the cue inside the band)
	// round 11 (critic r10 gap 3: "no FOV kick / radial speed cue at peak velocity"; the r07 5 deg kick reads as nothing):
	// 5 -> 10 deg at 40+ m/s (base ~50 + 10 + the 5 deg dive = ~65 vFOV peak, still under T14's 68-76 band; OutVFov is
	// hard-capped at 75 below). The Fov spring quickens 0.7 -> 0.4 s so the kick actually arrives inside the ~0.4 s the
	// bottom of the arc lasts (the closed loop is normalized against the CURRENT Fov, so the faster spring does not fight it).
	const double WantFov = BaseVFov + 10.0 * Smooth(Speed, 14, 40) * (1.0 - Smooth(FlipK, 0.0, 1.0)) + (bDive ? 5.0 : 0.0) + WallFovAdd * WallK;
	SD(Dist, DistV, WantDist, 0.55, Dt);
	SD(HeightOff, HeightOffV, WantH, 0.5, Dt);
	SD(SideOff, SideOffV, WantSide, 0.6, Dt);
	// FOV punch / dip springs
	PunchV += (-Punch * 140.0 - PunchV * 16.0) * Dt; Punch += PunchV * Dt;
	DipV += (-Dip * 90.0 - DipV * 13.0) * Dt; Dip += DipV * Dt;
	SD(Fov, FovV, WantFov, 0.4, Dt);   // round 11: 0.7 -> 0.4 s (see above)
	// launch kick spring
	KickV += (-KickK * 55.0 - KickV * 11.0) * Dt; KickK += KickV * Dt;
	// ---- roll: velocity yaw-rate + swing bank
	const double VelYaw = FMath::Atan2(Vel.Y, Vel.X);
	const double DY = bHasLastVelYaw ? WrapA(VelYaw - LastVelYaw) : 0.0;
	LastVelYaw = VelYaw; bHasLastVelYaw = true;
	SD(YawRate, YawRateV, HS > 3 ? FMath::Clamp(DY / FMath::Max(Dt, 1e-3), -3.0, 3.0) * FMath::Min(1.0, (HS - 3.0) / 17.0) : 0.0, 0.3, Dt);
	SD(BankS, BankSV, bSwinging ? P.Bank : 0.0, 0.35, Dt);
	// round 09 (TRAVERSAL-SPEC T13: roll allowed, |roll| median <= 1.5 deg, p90 <= 10): a lean toward the anchor side only
	// toward the arc ends
	const double ArcRoll = SideK * FMath::DegreesToRadians(AnchorRollMax) * Smooth(FMath::Abs(P.SwingAngle), 0.55, 1.0);
	double WantRoll = FMath::Clamp(-YawRate * 0.03, -0.07, 0.07) - BankS * 0.04 + ArcRoll;
	// round 10 (critic r09 T13 |roll| median 1.6 > 1.5 deg): small leans (< RollDeadDeg) are dropped, larger ones keep their size
	{
		const double Dz = FMath::DegreesToRadians(RollDeadDeg);
		WantRoll *= FMath::Clamp((FMath::Abs(WantRoll) - Dz) / FMath::Max(Dz, 1e-6), 0.0, 1.0); // 0 below Dz, full from 2 Dz
	}
	WantRoll *= 1.0 - Smooth(FlipK, 0.0, 1.0); // round 16 (TC12): no roll with the body while the trick camera is in
	Roll = Damp(Roll, WantRoll, 3, Dt);
	// ---- compose (round 03): lagged chase camera with explicit framing and collision
	const FVector Fwd = Forward();
	ComposeChase(Dt, P, World, Fwd);
	const FVector LookAt = CamPos + CamRot.Vector() * 10.0;
	// shake
	Trauma = FMath::Max(0.0, Trauma - Dt * 1.5);
	const double Sh = Trauma * Trauma;
	FRotator R = CamRot;
	R.Roll = FMath::RadiansToDegrees(Roll + Sh * 0.045 * Noise(Time * 22.0, 3.0));
	R.Pitch += FMath::RadiansToDegrees(Sh * 0.035 * Noise(Time * 25.0, 1.0));
	R.Yaw += FMath::RadiansToDegrees(Sh * 0.035 * Noise(Time * 24.0, 7.0));
	CamRot = R;
	OutVFov = FMath::Min(Fov + Punch + 9.0 * FMath::Max(0.0, KickK) + FMath::RadiansToDegrees(AttachFov), 75.0);   // round 11: T14 caps the swing lens at hFOV 110 = vFOV 76; stay 1 deg under
	(void)LookAt;
	// ---- round 13: output slew limit (see the header): never a cut
	SlewFlags = 0;
	if (bOutInit && Dt > 0.0)
	{
		const double K = Dt * 60.0;
		// round 05: while the hero is out of view (watchdog below) the caps relax -- a fast pan that finds him beats a hidden hero
		// round 09: the relaxation now also applies in trick mode while the watchdog fires (critic r08: the trick camera held its
		// slew caps through a 1.6 s hero-loss in s3); TC-B's 150 deg/s cap still binds whenever the hero is seen
		// round 12: EdgeK (hero at/over the frame edge, see the watchdog block) relaxes the same caps -- an edge exit is a
		// partially lost hero; the recovery pan beats the held view there too
		const double Boost = 1.0 + FMath::Max(VisBoostK, EdgeK) * (VisWhipMul - 1.0);
		const FVector D = CamPos - LastOutPos;
		const double Lm = MaxStepPosM * K * Boost;
		// round 20: the position slew never leaves the lens behind a wall (T19 beats "never a cut")
		const bool bSlewHidden = D.Size() > Lm && World.LineBlocked(P.Pos + FVector(0, 0, 0.3), LastOutPos + D.GetSafeNormal() * Lm);
		if (bSlewHidden) SlewFlags |= 8;
		else if (D.Size() > Lm)
		{
			const FVector NewPos = LastOutPos + D.GetSafeNormal() * Lm;
			const FRotator A0 = (P.Pos - CamPos).Rotation(), A1 = (P.Pos - NewPos).Rotation();
			CamRot.Yaw += FRotator::NormalizeAxis(A1.Yaw - A0.Yaw);
			CamRot.Pitch += A1.Pitch - A0.Pitch;
			CamPos = NewPos;
			SlewFlags |= 1;
		}
		const double SlP = CamRot.Pitch - LastOutRot.Pitch, SlY = FRotator::NormalizeAxis(CamRot.Yaw - LastOutRot.Yaw);
		const double MP = MaxStepPitchDeg * K * Boost, MY = (FlipK > 1e-3 && VisBoostK <= 0.01 && EdgeK <= 0.01 ? FlipMaxStepYawDeg : MaxStepYawDeg * Boost) * K; // round 16 (TC-B): <= 150 deg/s while the trick camera is in (blend in / hold / blend out) and the hero is seen; round 09: the watchdog relaxes it when he is not; round 12: EdgeK relaxes it at the frame edge
		if (FMath::Abs(SlP) > MP) { CamRot.Pitch = LastOutRot.Pitch + FMath::Sign(SlP) * MP; SlewFlags |= 2; }
		if (FMath::Abs(SlY) > MY) { CamRot.Yaw = LastOutRot.Yaw + FMath::Sign(SlY) * MY; SlewFlags |= 4; }
		if (SlewFlags) { HeroDist = FVector::Dist(CamPos, P.Pos); bCamInGeometry = World.SphereOverlaps(CamPos, 0.15); }
		// round 14: the position re-aim above may add pitch -- keep the look-up cap (wall-run camera excepted)
		// (round 15: CapUpDeg = the cap ComposeChase applied this frame -- flip 8, chase 10, wall 30)
		if (CamRot.Pitch > CapUpDeg + 0.5) CamRot.Pitch = CapUpDeg + 0.5;
		// round 13 (critic r12 gap 3: hero fully lost ~0.3 s in the s3b trick blend-out at t=11.62-11.94; the r12 EdgeK only
		// RELAXED the slew caps -- the composed target itself kept turning away (the chase yaw outruns the boosted cap at
		// ~37 m/s tangential), so the recovery crawled): while the hero sits past the edge band, the OUTPUT also steers
		// straight toward his bearing, rate-capped at the same boosted caps. Inside the band the composed target rules
		// (TC-B); the steering fades out with EdgeK (slow release), so it never fights the deliberate off-centre framing.
		if (EdgeK > 0.30 && !(SlewFlags & 8))
		{
			const FRotator ToH = (P.Pos + FVector(0, 0, 0.4) - CamPos).Rotation();
			const double StDY = FRotator::NormalizeAxis(ToH.Yaw - CamRot.Yaw), StDP = ToH.Pitch - CamRot.Pitch;
			const double CapY = MaxStepYawDeg * K * Boost * EdgeK, CapP = MaxStepPitchDeg * K * Boost * EdgeK;
			CamRot.Yaw += FMath::Clamp(StDY, -CapY, CapY);
			CamRot.Pitch += FMath::Clamp(StDP, -CapP, CapP);
			if (CamRot.Pitch > CapUpDeg + 0.5) CamRot.Pitch = CapUpDeg + 0.5;
			SlewFlags |= 16;
		}
	}
	bLensTouch = World.SphereOverlaps(CamPos, 0.25);
	bCamEnclosed = World.Enclosed(CamPos);
	// ---- round 05: visibility watchdog (critic r04: hero fully hidden ~0.8 s in s1/s5; never > 0.25 s unseen during swings).
	// Seen = the full body sits inside the trick frustum with margin AND the lens->chest line is clear.
	// round 09 (critic r08: the trick camera lost the hero ~1.6 s in s3 -- this watchdog explicitly did NOT run while the trick
	// camera was in): the watchdog runs in trick mode too now; the trick camera's own response lives in ComposeChase (dolly in
	// along the held axis, lift, abort to the boosted chase past the unseen grace -- TC11's constraints, TC-G beats the held
	// view). UnseenT decays at 1.5 x so the recovery eases off instead of snapping.
	{
		const bool bBodySafety = FlipK > 1e-3 || FlipFrameTail > 0.0;
		const bool bChaseModes = M == EWebTravMode::Swing || M == EWebTravMode::Air || M == EWebTravMode::Zip || M == EWebTravMode::Wall   // round 09: wall too (the s3 20.0 blend-out onto the wall-run camera left him out of frame 0.4 s)
			|| ((M == EWebTravMode::Ground || M == EWebTravMode::Land) && bBodySafety);
		const FVector ChestW = P.Pos + FVector(0, 0, 0.4);
		const FVector ToH = ChestW - CamPos;
		const double Dh = ToH.Size();
		bool bSeen = true;
		bool bSightBlocked = false;
		const double HalfV = FMath::DegreesToRadians(FMath::Max(20.0, OutVFov)) * 0.5;
		const double HalfH = FMath::Atan(FMath::Tan(HalfV) * 16.0 / 9.0);
		const FRotationMatrix ERM(CamRot);
		const double Zf = FVector::DotProduct(ToH, ERM.GetUnitAxis(EAxis::X));
		if (bChaseModes && Dh > 0.3)
		{
			// While the trick view is in, test every body-box corner against the rectangular frustum. A chest-only check
			// missed clipped limbs after a cancel / landing. Ordinary chase retains its existing cone test.
			const bool bInView = bBodySafety
				? BodyFrameEdge(BodyEnvelope(P), CamPos, CamRot, HalfV, HalfH) <= 0.96
				: Zf / Dh >= FMath::Cos(FMath::Max(HalfV, HalfH) * 0.80);
			if (!bInView) bSeen = false;
			bSightBlocked = World.LineBlocked(CamPos, ChestW);
			if (bSightBlocked) bSeen = false; // a roof edge / facade between the lens and him
		}
		if (bSeen || !bChaseModes) UnseenT = FMath::Max(0.0, UnseenT - Dt * 1.5);
		else UnseenT += Dt;
		VisBoostK = FMath::Clamp(UnseenT / FMath::Max(0.05, VisBoostT), 0.0, 1.0);
		OcclBoostK = bSightBlocked ? VisBoostK : 0.0;
		// round 12 (critic r11 gap 3 / F9: the hero exits the right frame edge ~0.6 s on s3b t=7.4-7.8; TC wants him inside the
		// central 60 %): the watchdog fires only ~20 % PAST the frustum cone, so a hero crossing the edge inside a slew-capped
		// turn crawls back for half a second. Edge containment: measure the chest's angle off the view axis per axis; past
		// ~2/3 of the half-angle EdgeK snaps in (release slow), and the output slew caps relax exactly like the watchdog's
		// boost -- a hero at/over the edge recovers in ~0.1 s. TC-B's 150 deg/s still binds while he is inside the band
		// (TC-G in-frame beats the held view, the round-09 precedence).
		double EdgeGoal = 0.0;
		if (bChaseModes && Dh > 0.3)
		{
			if (Zf > 0.3 * Dh)
			{
				const double OffH = FMath::Atan2(FVector::DotProduct(ToH, ERM.GetUnitAxis(EAxis::Y)), Zf);
				const double OffV = FMath::Atan2(FVector::DotProduct(ToH, ERM.GetUnitAxis(EAxis::Z)), Zf);
				// An obstruction fallback may already be at K=0 while the trick is still playing or its wall catch begins.
				// Keep the body margin until the measured window ends, rather than reverting to the chest cone mid-transition.
				const double Edge = bBodySafety ? BodyFrameEdge(BodyEnvelope(P), CamPos, CamRot, HalfV, HalfH)
					: FMath::Max(FMath::Abs(OffH) / FMath::Max(1e-3, HalfH), FMath::Abs(OffV) / FMath::Max(1e-3, HalfV));
				EdgeGoal = Smooth(Edge, 0.68, 0.98);
			}
			else EdgeGoal = 1.0; // beside / behind the lens: full boost (the watchdog's frustum test covers the same case)
		}
		EdgeK = EdgeGoal > EdgeK ? Damp(EdgeK, EdgeGoal, 25.0, Dt) : Damp(EdgeK, EdgeGoal, 2.5, Dt);
	}
	LastOutPos = CamPos; LastOutRot = CamRot; bOutInit = true;
	if (CameraProbeOn(P))
		UE_LOG(LogWebHomage, Display, TEXT("WH_CAM_PROBE output time=%.4f hero=%s camera=%s pitch=%.3f yaw=%.3f vfov=%.3f slew=%d edge=%.3f vis=%.3f occl=%.3f"),
			Time, *P.Pos.ToString(), *CamPos.ToString(), CamRot.Pitch, CamRot.Yaw, OutVFov, SlewFlags, EdgeK, VisBoostK, OcclBoostK);
	// speed motion blur: none on foot / walls, ramps in over fast swings / dives / zips
	const bool bGroundish = M == EWebTravMode::Ground || M == EWebTravMode::Land || M == EWebTravMode::Wall;
	// round 08: blur only at genuinely high speed (0 below 28 m/s, full at 50), none on foot / walls
	const double MbTarget = (bGroundish ? 0.0 : bDive ? 1.3 : 1.0) * Smooth(Speed, 28, 50);
	MotionBlur = FMath::Max(0.0, SD(MbK, MbKV, MbTarget, MbTarget > MbK ? 0.35 : 0.2, Dt));
}

bool FWebTravCamera::PerchSpotBad(double InYaw, const FTravCamInput& P, const FWebTravWorld& World) const
{
	const FVector Hero = P.Pos, Chest = Hero + FVector(0, 0, 0.4);
	const FVector B(-FMath::Cos(InYaw), -FMath::Sin(InYaw), 0.0), Rt(-FMath::Sin(InYaw), FMath::Cos(InYaw), 0.0);
	const double LensZ = Hero.Z + ChaseHeight;
	for (double R : { 3.3, 3.9, 4.5, 5.1 })
	{
		for (double Lat : { -0.2, 0.3, 0.8 })
		{
			const FVector S = Hero + B * R + Rt * Lat;
			// (the floor is traced from 4 m over the hero: a trace starting under a box top misses the box -- r24 build 8)
			if (World.GroundHeight(S.X, S.Y, Hero.Z + 4.0) + 0.4 > LensZ + 0.3) return true;
		}
	}
	double Hd = 0.0;
	return !World.SphereOverlaps(Chest, 0.22) && World.SphereSweep(Chest, Hero + B * 4.5 + Rt * 0.3 + FVector(0, 0, ChaseHeight), 0.3, Hd);
}

void FWebTravCamera::ComposeChase(double Dt, const FTravCamInput& P, const FWebTravWorld& World, const FVector& /*Fwd*/)
{
	const FVector Hero = P.Pos;                         // body centre (m)
	const FVector Chest = Hero + FVector(0, 0, 0.4);
	const bool bProbe = CameraProbeOn(P);
	const bool bSwinging = P.Mode == EWebTravMode::Swing, bAir = P.Mode == EWebTravMode::Air || P.Mode == EWebTravMode::Zip;
	const double VFov = FMath::DegreesToRadians(Fov + Punch + 9.0 * FMath::Max(0.0, KickK));
	const double TanHalfV = FMath::Tan(VFov * 0.5);
	// ---- framing target: hero low in frame at the bottom of an arc / near the street, upper centre up high; falling
	// fast pushes him lower (the camera trails above), rising pushes him higher
	double SWant = 0.58;
	if (bSwinging)
	{ // by arc angle: lower third at the bottom of the arc, upper centre at both ends (every swing travels the frame)
		SWant = FMath::Lerp(FrameLowS, FrameHighS, FMath::Clamp(FMath::Abs(P.SwingAngle) / 0.85, 0.0, 1.0));
	}
	else if (bAir)
	{ // round 06 (critic r05: the hero drifts toward the frame edge in a long float): a weaker fall-rate push and a tighter
	  // vertical band keep him near centred while floating / diving
		SWant = FMath::Clamp(FMath::Lerp(FrameLowS, FrameHighS, FMath::Clamp((P.HAbove - 8.0) / 32.0, 0.0, 1.0)) - P.Vel.Z * 0.0015, 0.36, 0.56);
	}
	if (P.Mode == EWebTravMode::Wall || P.Sub == N_topOut) SWant = WallFrameS;
	// round 10: sky launch — the camera sinks under the hero and looks up while he rises / hangs (released at a fast fall)
	// round 10 (final loop, critic r09 gap 1): long floats high over the street get the same from-below framing (see the header)
	const bool bSkyFloat = bAir && !P.bDive && !P.bFlip && !P.bFlipSoon && !P.bFlipPre && P.HAbove > SkyFloatH;
	SD(SkyK, SkyKV, ((P.bSky || bSkyFloat) && P.Vel.Z > -9.0) ? 1.0 : 0.0, (P.bSky || bSkyFloat) && P.Vel.Z > -9.0 ? 0.25 : 0.35, Dt);
	SkyK = FMath::Clamp(SkyK, 0.0, 1.0);
	SWant = FMath::Lerp(SWant, SkySFrame, SkyK);
	// round 16 (TRICK_CAMERA_SPEC): the trick camera is chosen ONCE at the release frame (ChooseFlipView) and held on its world
	// azimuth; an obstruction on the held axis dollies in (TC11), under FlipDistMin it blends to the plain chase
	// round 18: also BEFORE a predicted flow-flip release (bFlipPre): the view is chosen and blended in ahead of the release, so the trick window
	// (release .. catch + 0.5 s) opens on the held 3/4 view (critic r17 TC-A: the blend-in inside the window gave offset p5 20-29, range 34)
	const bool bFlipCam = P.bFlip || P.bFlipSoon || P.bFlipPre;
	// ---- round 24 (critic r23 c 7.7-8.5 s, probe v1: the orbit search + crane still swung the view back 47-105 deg): on foot / perched a user
	// camera turn STOPS where the chase spot behind the hero would enter geometry (the look yaw is held at the last clear yaw while the turn
	// pushes into the wall; turning back is free). Clear = a GndStopR m sphere swept from the chest to GndStopExtra m past the chase spot.
	{
		const bool bGndMode = P.Mode == EWebTravMode::Ground || P.Mode == EWebTravMode::Perch || P.Mode == EWebTravMode::Land;
		const bool bGnd = GndMinDist > 0.0 && GndStop > 0.0 && bGndMode && !bFlipCam;
		// (hold D probe c: the lens hold ended the frame the look input stopped, 8.30 s, and the drifted chase spot swung the view 42 deg back):
		// a lens held by a stop stays held while on foot / perched until the player has left the stick alone for GndLensRelease s, and
		// through the first 0.3 s of a zip fired from there (the zip camera then takes over under the output slew limit)
		if (bGndLensHold && !(bGnd && LastLook < GndLensRelease) && !(P.Mode == EWebTravMode::Zip && P.ModeT < 0.3)) bGndLensHold = false;
		if (bGnd)
		{
			const FVector B(-FMath::Cos(Yaw), -FMath::Sin(Yaw), 0.0);
			const FVector Spot = Hero + B * (ChaseDist + GndStopExtra) + FVector(0, 0, ChaseHeight);
			double Hd = 0.0;
			const bool bBlocked = World.SphereOverlaps(Chest, 0.22) ? false : World.SphereSweep(Chest, Spot, GndStopR, Hd);
			if (!bBlocked) { GndYawOk = Yaw; bGndYawOk = true; GndStopped = 0; }
			else if (bGndYawOk && LastLook < GndLookHold)
			{
				AutoYaw += WrapA(GndYawOk - Yaw); Yaw = GndYawOk;
				// (hold C probe, c on its r23 path: with the yaw held the chase spring / sweep still pulled the lens 1 m in and swung the view
				//  28 deg back) -- the lens itself is held where the stop began (it saw the whole hero there), looking at the hero
				if (!GndStopped && !bGndLensHold && bOutInit) { GndStopPos = LastOutPos; }
				GndStopped = 1; bGndLensHold = GndHoldLens > 0.0;
			}
		}
		else { bGndYawOk = false; GndStopped = 0; }
	}
	if (bFlipCam && !bFlipWas)
	{
		bFlipObstacleOut = false;
		const bool bStillIn = FlipK > 0.05 && !bFlipAbort; // the previous trick's view is still blended (a chain): keep its distance, move its azimuth
		ChooseFlipView(P, World);
		bFlipAbort = FlipTier >= 3;
		if (!bStillIn) { FlipAzNow = FlipAz; FlipDistNow = FlipDistSel; FlipDistV = 0.0; FlipExtS = P.FlipExtent > 0.f ? double(P.FlipExtent) : 1.0; FlipExtV = 0.0; }
		FlipCompactS = FMath::Clamp(double(P.FlipCompact), 0.0, 1.0); FlipCompactV = 0.0; FlipSinceObs = 9.0;
	}
	if (bFlipCam)
	{ // round 18: a re-chosen view moves its azimuth at <= FlipAzRate deg/s (a fresh one starts on it)
		const double DA = WrapA(FlipAz - FlipAzNow), MaxD = FMath::DegreesToRadians(FlipAzRate) * Dt;
		FlipAzNow = WrapA(FlipAzNow + FMath::Clamp(DA, -MaxD, MaxD));
	}
	if (!bFlipCam) { bFlipAbort = false; FlipTier = -1; FlipObsT = 0.0; }
	bFlipWas = bFlipCam;
	if (bFlipCam && !bFlipAbort && bChaseInit)
	{ // TC11: sweep hero chest -> the held spot; a hit dollies the camera in along the axis, never yaws / re-picks the side
		const double Ec = FMath::Asin(FMath::Clamp(FlipDrop / FMath::Max(1.0, FlipDist), 0.0, 0.6));
		const FVector Uc(FMath::Cos(FlipAzNow) * FMath::Cos(Ec), FMath::Sin(FlipAzNow) * FMath::Cos(Ec), -FMath::Sin(Ec));
		// the distance follows the pose: a compact shape (tuck / pike) is pulled in FlipTuckPull m so the tuck-dominated backDouble reads as big as
		// the open shapes (TC-C p50 >= .18 with p90 <= .36: one constant distance cannot do both -- a tuck is ~.15, a layout ~.30 at the same range)
		SD(FlipCompactS, FlipCompactV, FMath::Clamp(double(P.FlipCompact), 0.0, 1.0), FlipCompactT, Dt);
		// round 18: distance = FlipExtK x the hero's extent (spring 0.12 s), inside FlipDistCompact (4.5: a tuck, extent ~1 m, reads .15 of the frame at
		// 5.0 m -- r18 render f1 mask p50 .167 -- and ~.19 at 4.5) .. FlipDistMax. The pull-in is weighted by FlipCompact (tuck 1, pike .6, open 0, with its
		// 0.22 s anticipation): a flat 4.5 floor also pulled the open programs in (r18 render 2: corkscrew / pikeSwan bone-box h p90 .36-.37), open shapes stay >= 5.0
		if (P.FlipExtent > 0.f) SD(FlipExtS, FlipExtV, double(P.FlipExtent), 0.12, Dt);
		if (HeroProjH > 0.0 && FlipK > 0.3)
		{
			const double Ratio = HeroProjH / FlipFbTarget;
			// round 05 (critic r04 secondary: hero 0.11-0.15 of frame mid-flip in s3b): clamp 0.6-1.7 -> 0.5-1.9 (the pose-extent
			// anticipation undershoots on a layout seen end-on; the loop needs the range to pull in / back off further)
			// round 06 (critic r05: trick hero below the 0.18 floor on some frames): gain 2.5 -> 3.2, deadband 8 -> 6 %, pull-in to 0.46
			if (FMath::Abs(Ratio - 1.0) > 0.06) FlipFbK = FMath::Clamp(FlipFbK * (1.0 + (Ratio - 1.0) * FMath::Min(1.0, FlipFbGain * Dt)), 0.46, 1.35);
		}
		else FlipFbK = FMath::Lerp(FlipFbK, 1.0, FMath::Min(1.0, 2.0 * Dt));
		const double Want0 = P.FlipExtent > 0.f || FlipExtS > 0.0
			? FMath::Clamp(FlipExtK * FlipExtS, FMath::Min(FlipDistSel, FMath::Lerp(FlipDistSel, FlipDistCompact, FMath::Clamp(FlipCompactS, 0.0, 1.0))), FMath::Max(FlipDistSel, FlipDistMax))
			: FlipDistSel - FlipTuckPull * FMath::Clamp(FlipCompactS, 0.0, 1.0);
		// round 09 (critic r08: the trick camera lost the hero ~1.6 s in a dark alley, then buried itself in a facade; the round-05
		// chase watchdog was excluded in trick mode): the watchdog now runs through the trick, and the trick camera answers it
		// inside TC11's constraints -- dolly IN along the held axis (never a yaw / side re-pick), and past the grace of a fully
		// unseen hero the trick view falls back to the plain chase (the watchdog's distance / lift / slew boost then owns the
		// recovery; TC-G hero-visible beats the held view)
		double Want = FMath::Clamp(Want0 * FlipFbK * (1.0 - 0.45 * OcclBoostK), 2.8, FMath::Max(FlipDistSel, FlipDistMax) * 1.03);
		// An edge-clipped open pose needs a longer radius, not the old visibility pull-IN. Bound the held-axis goal by the
		// complete current / anticipated body at its intended framing, before the distance spring or obstruction probe.
		const double HalfV = FMath::DegreesToRadians(FMath::Max(20.0, FMath::Min(Fov + Punch + 9.0 * FMath::Max(0.0, KickK) + FMath::RadiansToDegrees(AttachFov), 75.0))) * 0.5;
		const double HalfH = FMath::Atan(FMath::Tan(HalfV) * 16.0 / 9.0);
		const FBox Bounds = BodyEnvelope(P);
		for (double Radius : { 4.0, 4.5, 5.0, 5.5, 6.0, 6.48 })
		{
			const FVector Spot = FloorSafeSpot(Hero + Uc * Radius, Hero, World, RoofLift);
			FRotator Aim = (Hero - Spot).Rotation();
			Aim.Pitch = FMath::Min(Aim.Pitch + FMath::RadiansToDegrees(FMath::Atan((FlipSFrame - 0.5) * 2.0 * FMath::Tan(HalfV))), FlipPitchUpMax);
			Aim.Yaw -= FlipSide * FlipLeadDeg;
			Want = FMath::Max(Want, Radius);
			if (BodyFrameEdge(Bounds, Spot, Aim, HalfV, HalfH) <= 0.92) break;
		}
		double HitD = 0.0, ObsGoal = 1e9;
		const FVector HeldSpot = FloorSafeSpot(Hero + Uc * Want, Hero, World, RoofLift);
		// Measure the same floor-safe spot that composition will use. Testing the old below-roof endpoint here still
		// shrank FlipDistNow even when the later sweep had been fixed, turning a landing into a pose-feedback close-up.
		// FloorSafeSpot includes the actual lift; probing the below-roof endpoint falsely shortened a clear composed ray.
		if (!World.SphereOverlaps(Chest, 0.22) && World.SphereSweep(Chest, HeldSpot, 0.3, HitD)) ObsGoal = HitD - 0.25;
		if (bProbe)
			UE_LOG(LogWebHomage, Display, TEXT("WH_CAM_PROBE held time=%.4f chest=%s spot=%s want=%.3f actual=%.3f hit=%.3f hitpoint=%s obs=%.3f bounds=%s"),
				Time, *Chest.ToString(), *HeldSpot.ToString(), Want, FlipDistNow, HitD, *(Chest + (HeldSpot - Chest).GetSafeNormal() * HitD).ToString(), ObsGoal, *Bounds.ToString());
		const double Goal = FMath::Min(Want, ObsGoal);
		// TC11's plain-chase fallback must BEGIN before a descending held ray loses its 4 m of room. Waiting for the
		// present hit plus grace left only 0.1 s before the c6 landing, while the post-catch hold delayed the turn again.
		// Lead time follows the existing blend / yaw budget; the forecast only tests this held axis, never selects a new side.
		if (P.Vel.Z < -3.0 && FlipK > 0.5)
		{
			const double TurnT = FMath::Abs(FMath::RadiansToDegrees(WrapA(Yaw + PI - FlipAzNow))) / FMath::Max(1.0, FlipMaxStepYawDeg * 60.0);
			const double AheadT = FMath::Min(1.25, FMath::Max(FlipOutT, TurnT) + 0.10);
			const FVector AheadHero = ForecastHero(P, World, AheadT, ForecastGravity), AheadChest = AheadHero + FVector(0, 0, 0.4);
			const FVector AheadSpot = FloorSafeSpot(AheadHero + Uc * Want, AheadHero, World, RoofLift);
			double AheadHit = 0.0;
			const bool bNoRoom = !World.SphereOverlaps(AheadChest, 0.22) && World.SphereSweep(AheadChest, AheadSpot, 0.3, AheadHit) && AheadHit - 0.25 < FlipDistMin;
			if (bNoRoom) { bFlipAbort = true; bFlipObstacleOut = true; }
			if (bProbe) UE_LOG(LogWebHomage, Display, TEXT("WH_CAM_PROBE forecast time=%.4f ahead=%.3f gravity=%.3f hero=%s spot=%s hit=%.3f fallback=%d"),
				Time, AheadT, ForecastGravity, *AheadHero.ToString(), *AheadSpot.ToString(), AheadHit, bNoRoom ? 1 : 0);
		}
		// TC11: no room to keep the trick view (under FlipDistMin for FlipAbortGrace s running -- a trunk or a canopy edge passing the
		// axis for a few frames is dollied through, r16 probe: one tree at a 13 m flip ended the whole trick camera) -> plain chase over FlipOutT
		// round 09: the same fallback when the hero has been fully out of view for the grace (the watchdog's UnseenT)
		FlipObsT = (ObsGoal < FlipDistMin || (UnseenT > 0.25 && OcclBoostK > 0.01)) ? FlipObsT + Dt : 0.0;
		if (FlipObsT > FlipAbortGrace) { bFlipAbort = true; bFlipObstacleOut = true; }
		else
		{ // obstruction: in fast, out slow (0.6 s, and for 0.6 s after the last hit); pose-driven distance changes: 0.12 s in / 0.2 s out on top of the 0.25 s compactness spring
			// round 09: while the watchdog fires the dolly-in is immediate (the 0.12 s ease is for pose-driven moves, not a lost hero)
			const bool bObs = ObsGoal < Want;
			FlipSinceObs = bObs ? 0.0 : FlipSinceObs + Dt;
			const double St = Goal < FlipDistNow ? (bObs || VisBoostK > 0.01 ? FlipDollyInT : 0.12) : (FlipSinceObs < 0.6 && VisBoostK <= 0.01 ? FlipDollyOutT : 0.2);
			SD(FlipDistNow, FlipDistV, FMath::Max(Goal, 2.8), St, Dt);
		}
	}
	{
		const bool bOn = bFlipCam && !bFlipAbort;
		if (bOn)
		{ // blend in: critically damped springs (smooth times FlipInT horizontal, FlipZInT height), continuous with a blend-out still running
			bFlipOutRun = false;
			// round 17 (critic r16: "flipcam_k >= 0.9 by flip_t 0.35", r16 spring reached it at ~0.65 s): a smoothstep over FlipInT from the
			// weight at its start (k .9 at 0.80 x FlipInT; the output yaw slew 2.4 deg/frame still caps the view's turn rate)
			// v2 (rendered f-series: the smoothstep was still turning ~130 deg/s when k passed .9 -> TC-B "held max <= 60 deg/s" failed): the blend
			// covers the azimuth change D0 (camera azimuth now -> held azimuth) with a minimum-time profile: accelerate at FlipInAcc deg/s^2 to
			// FlipInRate deg/s, decelerate at FlipInDec deg/s^2 (rate sqrt(2 a d) at d deg left), so k reaches .9 at ~0.30-0.35 s for D0 30-40 deg
			// with the turn at <= ~57 deg/s by then; k = covered / D0.
			if (!bFlipInRun)
			{
				bFlipInRun = true; FlipInClock = 0.0; FlipInK0 = FlipK; FlipInS = 0.0; FlipInR = 0.0;
				const double CurAz = bOutInit ? FMath::Atan2(LastOutPos.Y - Hero.Y, LastOutPos.X - Hero.X) : FlipAz;
				FlipInD0 = FMath::Max(2.0, FMath::Abs(FMath::RadiansToDegrees(WrapA(FlipAz - CurAz))) * (1.0 - FlipInK0));
			}
			FlipInClock += Dt;
			{
				const double Rem = FMath::Max(0.0, FlipInD0 - FlipInS);
				const double Want = FMath::Min(FlipInRate, FMath::Sqrt(2.0 * FlipInDec * Rem));
				FlipInR = FMath::Min(Want, FlipInR + FlipInAcc * Dt);
				FlipInS = FMath::Min(FlipInD0, FlipInS + FlipInR * Dt);
				const double X = FlipInS / FlipInD0;
				FlipK = FlipInClock >= FlipInT * 3.0 ? 1.0 : FlipInK0 + (1.0 - FlipInK0) * X; // (a safety end at 3 x FlipInT)
				FlipKV = (1.0 - FlipInK0) * FlipInR / FlipInD0;
			}
			SD(FlipZK, FlipZKV, 1.0, FlipZInT, Dt);
			FlipKr = FlipK; // round 07: radius follows the azimuth while blending in
		}
		else if (FlipK > 1e-4 || FlipZK > 1e-4)
		{ // blend out (TC10): a smoothstep over FlipOutT seconds from the weights at its start -- finite, so the next trick of a chain never
			// starts on the exponential tail of this one (a critically damped tail left 22 % of the old side in the next flip: a 19 deg jump)
			bFlipInRun = false;
			if (!bFlipOutRun) { bFlipOutRun = true; FlipOutClock = 0.0; FlipOutK0 = FlipK; FlipOutZ0 = FlipZK; }
			FlipOutClock += Dt;
			// round 18: the azimuth weight holds FlipAzHold s first (TC-A window = program + 0.5 s; the height / pitch settle below is unchanged)
			const double AzHold = bFlipObstacleOut ? 0.0 : FlipAzHold;
			const double X = FMath::Clamp((FlipOutClock - AzHold) / FMath::Max(0.05, FlipOutT), 0.0, 1.0), S = X * X * (3.0 - 2.0 * X), Dv = X > 0.0 && X < 1.0 ? 6.0 * X * (1.0 - X) / FMath::Max(0.05, FlipOutT) : 0.0;
			FlipK = FlipOutK0 * (1.0 - S); FlipKV = -FlipOutK0 * Dv;
			// round 07: the radius lets go at once (the azimuth keeps its FlipAzHold; TC10/TC-K measure the VIEW blend-out)
			// A landing retains its radius while azimuth / height are still held. Releasing only the radius here produced a
			// roof close-up during the ground transition, before the view could settle under its existing angular slew.
			const double RadiusHold = P.Mode == EWebTravMode::Ground || P.Mode == EWebTravMode::Land ? FlipAzHold : 0.0;
			const double Xr = FMath::Clamp((FlipOutClock - RadiusHold) / FMath::Max(0.05, FlipOutT * 0.6), 0.0, 1.0), Sr = Xr * Xr * (3.0 - 2.0 * Xr);
			FlipKr = FlipOutK0 * (1.0 - Sr);
			if (bFlipObstacleOut) FlipKr = FlipK; // preserve radius until the obstacle fallback has turned onto the chase path
			// the height weight holds FlipZHold s after the catch before it follows (TC6: the lens stays under the hips through the 0.5 s tail)
			const double ZHold = bFlipObstacleOut ? 0.0 : FlipZHold;
			const double Xz = FMath::Clamp((FlipOutClock - ZHold) / FMath::Max(0.05, FlipOutT), 0.0, 1.0), Sz = Xz * Xz * (3.0 - 2.0 * Xz);
			FlipZK = FlipOutZ0 * (1.0 - Sz); FlipZKV = Xz > 0.0 && Xz < 1.0 ? -FlipOutZ0 * 6.0 * Xz * (1.0 - Xz) / FMath::Max(0.05, FlipOutT) : 0.0;
		}
		else { bFlipOutRun = false; bFlipInRun = false; bFlipObstacleOut = false; FlipK = FlipZK = FlipKr = 0.0; FlipKV = FlipZKV = 0.0; }
		FlipK = FMath::Clamp(FlipK, 0.0, 1.0);
		FlipKr = FMath::Clamp(FlipKr, 0.0, 1.0);
		FlipZK = FMath::Clamp(FlipZK, 0.0, 1.0);
	}
	SWant = FMath::Lerp(SWant, FlipSFrame, FlipK);
	SWant = FMath::Clamp(SWant, 0.32, 0.72);
	// round 10 (critic r09: camera pop at b 0.000-0.017 s): the first composed frame starts AT its framing / attach targets
	// (FrameS was reset to 0.55 and sprang to ~0.40 over the first frames: 4 deg of pitch per frame)
	const bool bFirst = !bChaseInit;
	if (bFirst) { FrameS = SWant; FrameSV = 0.0; }
	SD(FrameS, FrameSV, SWant, 0.22, Dt);
	// ---- desired position: behind the (lagged) heading yaw, above the hero
	const FVector Back = -ForwardFlat(), Right = RightFlat();
	// round 07: 0.4 m closer while swinging / airborne (the higher round-07 camera left the hero < 160 px at the arc ends)
	const double AirClose = (bSwinging || bAir) ? SwingCloser : 0.0;
	// round 05 (P1): closed-loop chase distance from the projected hero bone-box height (the trick camera's signal), so the hero
	// pixel height holds its band while the pose / framing change; the watchdog adds VisBoostBack while he is out of view
	if ((bSwinging || bAir) && !bFlipCam && HeroProjH > 0.0)
	{
		// round 07 (s4 P1: the speed FOV kick / its decay made the loop pull in and then leave the hero over the band top at
		// the swing bottom / catch): normalize the measured projected height by the speed-kick fov part (Fov + Punch + Kick,
		// NOT the attach beat's AttachFov -- that beat deliberately shrinks him to fit the anchor and the r06 behaviour
		// passes P1) -- the loop holds the hero's size as if the kick never happened instead of chasing its transient
		const double Hn = HeroProjH * FMath::Tan(FMath::DegreesToRadians(FMath::Max(10.0, Fov + Punch + 9.0 * FMath::Max(0.0, KickK))) * 0.5) / FMath::Tan(FMath::DegreesToRadians(BaseVFov) * 0.5);
		const double Ratio = Hn / (bSwinging ? ChaseFbSwing : ChaseFbAir);
		if (FMath::Abs(Ratio - 1.0) > 0.03) ChaseFbK = FMath::Clamp(ChaseFbK * (1.0 + (Ratio - 1.0) * FMath::Min(1.0, ChaseFbGain * Dt)), ChaseFbMin, ChaseFbMax);
	}
	else ChaseFbK = FMath::Lerp(ChaseFbK, 1.0, FMath::Min(1.0, 2.0 * Dt));
	const double ChaseKNow = FMath::Clamp(ChaseFbK + VisBoostK * VisBoostBack, ChaseFbMin, ChaseFbMax + VisBoostBack);
	const double BackDist = ChaseDist * ChaseKNow - AirClose + 1.3 * FMath::Max(0.0, KickK);
	const double OY = OccYawOff, OU = OccUp; // round 12: the flip orbit is placed below (searched view), not a fixed 40 deg
	const FVector BackR(Back.X * FMath::Cos(OY) - Back.Y * FMath::Sin(OY), Back.X * FMath::Sin(OY) + Back.Y * FMath::Cos(OY), 0);
	// round 09 (TRAVERSAL-SPEC T12/T17/T18): the camera slides AnchorShift m toward the ACTIVE anchor's side (kept through the
	// swing chain's short air phases) while still looking at the hero: the view runs 2-25 deg off the avenue axis and the near
	// facade on that side fills a side third, the hero stays centred
	if (bSwinging && P.bHasAnchor)
	{
		const double Lat = FVector::DotProduct(P.Anchor - Hero, Right);
		if (FMath::Abs(Lat) > 2.0) SideGoal = Lat > 0 ? 1.0 : -1.0;
	}
	if (bSwinging) { bInChain = true; ChainAirT = 0.0; }
	else if (P.Mode != EWebTravMode::Air) bInChain = false; // ground / wall / perch / zip end the chain
	else ChainAirT += Dt;
	if (P.bDive || ChainAirT > 0.8) bInChain = false;       // a long fall / dive is not the chain rhythm: centred again (aiming)
	SD(SideK, SideKV, bInChain ? SideGoal : 0.0, 0.3, Dt);
	// round 10 (critic r09 gap 1: P1 air s1/s5 82 % -- the release-transient poses turn the hero end-on and the closed loop lags
	// ~0.2 s, so the 10 fps sampler catches him under the 0.18 floor): a small geometric pull-in right after each release,
	// decaying over the first 0.45 s of the chain gap (the closed loop owns the size again after that)
	const double RelPull = (bAir && bInChain && ChainAirT < 0.45) ? 1.0 - 0.12 * (1.0 - ChainAirT / 0.45) : 1.0;
	FVector Desired = Hero + BackR * (BackDist * RelPull) + Right * (0.3 + AnchorShift * SideK);
	double ZWant = Hero.Z + FMath::Lerp(ChaseHeight, -SkyCamBelow, SkyK) + OU;
	// round 07 (critic r06: steep top-down stretches on floats, s4 t=5.9): the 0.05 s CamZ spring lags a fast-falling hero by
	// ~vz * 0.05-0.07 m above him, which reads as a top-down float; feed the vertical velocity forward so the camera descends
	// with him (dives keep their deliberate high down-look)
	if ((bSwinging || bAir) && !P.bDive) ZWant += P.Vel.Z * 0.055;
	// round 24 (capture c 9.87 s: the perch recenter swung the chase spot over a 1.8 m rooftop box; the floor clamp popped the lens up 1 m per
	// frame and the slew-limited pitch left the hero under the bottom edge for 0.17 s): on foot / perched the spot is pulled in toward the
	// hero (down to GndFloorPullMin of the distance) until its floor is no higher than the camera height wants
	if (GndFloorPull > 0.0 && (P.Mode == EWebTravMode::Ground || P.Mode == EWebTravMode::Perch || P.Mode == EWebTravMode::Land) && !bFlipCam)
	{
		for (double K : { 1.0, 0.9, 0.8, 0.7, 0.6 })
		{
			if (K < GndFloorPullMin - 1e-3) break;
			const FVector Dk = Hero + BackR * (BackDist * K) + Right * (0.3 + AnchorShift * SideK);
			// (the floor is traced from 4 m over the hero: a trace starting under a box top misses the box)
			if (World.GroundHeight(Dk.X, Dk.Y, Hero.Z + 4.0) + 0.4 <= ZWant + 0.3) { Desired = Dk; break; }
		}
	}
	// round 16: trick camera spot = FlipDistNow m from the hero on the held world azimuth, FlipDrop m under his body centre
	// (the chase camera state -- Desired / CamXY / CamZ -- keeps running through the trick, so the blend-out has no jump; the trick spot is
	// blended onto its result in POLAR coordinates around the hero: azimuth, radius, height -- a Cartesian lerp of two spots 45 deg apart
	// swings the view ~2x faster than the spring asks for)
	const double FlipKs = Smooth(FlipK, 0.0, 1.0);
	FVector FlipSpot = Hero;
	{
		const double FlipElevNow = FMath::Asin(FMath::Clamp(FlipDrop / FMath::Max(1.0, FlipDist), 0.0, 0.6));
		FlipSpot = Hero + FVector(FMath::Cos(FlipAzNow) * FMath::Cos(FlipElevNow), FMath::Sin(FlipAzNow) * FMath::Cos(FlipElevNow), -FMath::Sin(FlipElevNow)) * FlipDistNow;
	}
	if (!bChaseInit)
	{
		bChaseInit = true;
		CamXY = FVector(Desired.X, Desired.Y, 0); CamXYV = FVector::ZeroVector; CamZ = ZWant; CamZV = 0;
	}
	// horizontal lag, then hold 4..6.5 m (plus kick) behind; vertical lag, then hold 0.8..4 m (+ occlusion lift) above
	SDV(CamXY, CamXYV, FVector(Desired.X, Desired.Y, 0), 0.07, Dt);
	FVector HD = FVector(CamXY.X - Hero.X, CamXY.Y - Hero.Y, 0);
	const double HL = HD.Size();
	const double MaxH = 5.0 * ChaseKNow - AirClose + 1.3 * FMath::Max(0.0, KickK), MinH = 3.5 * ChaseKNow - AirClose;
	if (HL < 1e-3) HD = BackR * MinH; else if (HL < MinH) HD *= MinH / HL; else if (HL > MaxH) HD *= MaxH / HL;
	CamXY = FVector(Hero.X + HD.X, Hero.Y + HD.Y, 0);
	SD(CamZ, CamZV, ZWant, 0.05, Dt);
	CamZ = FMath::Clamp(CamZ, Hero.Z + FMath::Lerp(CamZMin, -SkyCamBelow - 0.3, SkyK) + OU, Hero.Z + CamZMax + OU); // round 07: 0.7..1.8 -> 1.2..2.6
	FVector Cam(CamXY.X, CamXY.Y, CamZ);
	if (FlipK > 1e-4 || FlipZK > 1e-4)
	{ // the trick camera: polar blend (azimuth / radius about the hero by FlipK, height by FlipZK) of the chase camera onto the held spot
		const double DxC = Cam.X - Hero.X, DyC = Cam.Y - Hero.Y, DxF = FlipSpot.X - Hero.X, DyF = FlipSpot.Y - Hero.Y;
		const double AC = FMath::Atan2(DyC, DxC), AF = FMath::Atan2(DyF, DxF);
		const double RC = FMath::Sqrt(DxC * DxC + DyC * DyC), RF = FMath::Sqrt(DxF * DxF + DyF * DyF);
		// round 07 (s3/s3b P1 swing): while blending out the trick distance springs to the live chase radius (the chase
		// closed loop owns the hero's size again) and the radius weight FlipKr decays ahead of the azimuth's
		const bool bLandingRadiusHold = (P.Mode == EWebTravMode::Ground || P.Mode == EWebTravMode::Land) && FlipOutClock <= FlipAzHold;
		if (!bFlipCam && FlipKr > 1e-4 && !bLandingRadiusHold && !bFlipObstacleOut) SD(FlipDistNow, FlipDistV, RC, 0.18, Dt);
		const double AB = AC + WrapA(AF - AC) * FlipK, RB = FMath::Lerp(RC, RF, FlipKr);
		Cam = FVector(Hero.X + RB * FMath::Cos(AB), Hero.Y + RB * FMath::Sin(AB), Hero.Z + FMath::Lerp(Cam.Z - Hero.Z, FlipSpot.Z - Hero.Z, FlipZK));
	}
	const FVector ProbeRaw = Cam;
	// A descending trick lens can hit the roof BEFORE the body lands. Sweeping the below-roof spot first shortened the
	// c6 radius from 6.3 to 2.7 m; the later floor / minimum-distance lifts then overtook the slew-limited view angle.
	// Prepare floor clearance at the held XY spot before the sweep. Anticipate 0.2 s of travel and stop the predicted body
	// at its landing surface, rather than extrapolating it through the roof. The spring preserves position / velocity;
	// the output still obeys its existing slew and all collision queries remain active.
	{
		double WantLift = 0.0;
		if ((FlipK > 0.05 || FlipZK > 0.05) && !bFlipObstacleOut)
		{
			const double AheadT = 0.20;
			const FVector AheadHero = Hero + P.Vel * AheadT;
			const double AheadFloor = World.GroundHeight(AheadHero.X, AheadHero.Y, Hero.Z + 4.0);
			const double AheadZ = FMath::Max(AheadHero.Z, AheadFloor + 0.95);
			const FVector AheadCam = Cam + FVector(P.Vel.X * AheadT, P.Vel.Y * AheadT, AheadZ - Hero.Z);
			const double FloorNow = World.GroundHeight(Cam.X, Cam.Y, Hero.Z + 4.0) + 0.4;
			const double FloorAhead = World.GroundHeight(AheadCam.X, AheadCam.Y, FMath::Max(Hero.Z, AheadZ) + 4.0) + 0.4;
			WantLift = FMath::Max(0.0, FMath::Max(FloorNow - Cam.Z, FloorAhead - AheadCam.Z));
		}
		SD(RoofLift, RoofLiftV, WantLift, WantLift > RoofLift ? 0.12 : 0.4, Dt);
		if (FlipK > 0.05 || FlipZK > 0.05)
			Cam = FloorSafeSpot(Cam, Hero, World, RoofLift);
		else Cam.Z += FMath::Max(0.0, RoofLift);
	}
	const FVector ProbeFloor = Cam;
	// ---- collision: sphere-sweep from the chest; if the clear distance would drop under MinHeroDist, search raised /
	// rotated positions and move there smoothly (held ~1 s so the camera does not flicker)
	bool bNoSweep = false; // round 14: set below when the hero himself is inside geometry
	auto ClearFrom = [&](const FVector& From, const FVector& To, FVector& Out) -> double
	{
		const FVector D = To - From;
		const double L = D.Size();
		double HitD = 0;
		if (!bNoSweep && L > 1e-3 && World.SphereSweep(From, To, 0.22, HitD)) { Out = From + D / L * FMath::Max(0.0, HitD - 0.12); return FMath::Max(0.0, HitD - 0.12); }
		Out = To;
		return L;
	};
	// sweep origin: the chest, or (hero against / clipping a surface) the first clear point 1-2.5 m above it
	FVector From = Chest;
	bool bFromOk = false;
	for (double Lift : { 0.0, 1.0, 1.8, 2.6 })
	{
		From = Chest + FVector(0, 0, Lift);
		if (!World.SphereOverlaps(From, 0.22)) { bFromOk = true; break; }
	}
	// round 14 (probe f3 4.8-5.6 s: the hero swings through a street-tree canopy at a swing bottom; every sweep origin overlaps the
	// canopy): the r13 hold kept the camera's offset AND rotation for 0.8 s (hero slid to 0.90 of the frame, pitch 28 deg down, camera
	// 49 frames inside the foliage). Now the frame composes normally but WITHOUT the collision sweeps (the hero is inside geometry,
	// so a sweep from him cannot tell a clear spot): the chase spot behind him is taken as it is.
	bNoSweep = !bFromOk && bChaseInit && !CamPos.IsZero();
	if (bNoSweep) From = Chest;
	auto ClearTo = [&](const FVector& To, FVector& Out) -> double
	{
		ClearFrom(From, To, Out);
		return FVector::Dist(Out, Hero);
	};
	// orbit candidates relative to the current heading: yaw offset DYw (rad) and extra height Up (m)
	auto Candidate = [&](double DYw, double Up)
	{
		const FVector B2(Back.X * FMath::Cos(DYw) - Back.Y * FMath::Sin(DYw), Back.X * FMath::Sin(DYw) + Back.Y * FMath::Cos(DYw), 0);
		return Hero + B2 * ChaseDist + FVector(0, 0, ChaseHeight + Up);
	};
	FVector Tmp;
	// round 24: on foot / perched (see GndMinDist in the header)
	const bool bGndCam = GndMinDist > 0.0 && (P.Mode == EWebTravMode::Ground || P.Mode == EWebTravMode::Perch || P.Mode == EWebTravMode::Land) && !bFlipCam;
	const bool bGndTurn = bGndCam && LastLook < GndLookHold && LookYawDir != 0;
	const double DefClear = ClearTo(Candidate(0, 0), Tmp);
	const double DefLen = FVector::Dist(Candidate(0, 0), Hero); // unobstructed distance of the default spot
	// round 12 (critic r11: the s3 t=20.0 top-out read top-down): through a top-out the orbit never cranes UP onto the roof the
	// hero is climbing onto -- a horizontal re-seat keeps him in frame from the street side while the wall camera owns the view
	const bool bTopOutNow = P.Sub == N_topOut;
	if (DefClear >= DefLen - 0.3) { OccYawGoal = 0; OccUpGoal = 0; }
	else if ((OccYawGoal == 0 && OccUpGoal == 0) || (bTopOutNow && OccUpGoal > 0.0) || ClearTo(Candidate(OccYawGoal, OccUpGoal), Tmp) < DefLen - 0.8)
	{ // default spot blocked and no clear orbit held: search raised / rotated spots
		double BestC = -1e9, BY = 0, BU = 0;
		for (double Up : { 0.0, 2.0, 4.0, 6.0, 9.0 })
		{
			if (bTopOutNow && Up > 0.0) continue;
			for (double DYw : { 0.0, 0.6, -0.6, 1.1, -1.1, 1.6, -1.6, 2.2, -2.2 })
			{
				if (bGndTurn && DYw * double(LookYawDir) < -1e-3) continue; // round 24: never orbit back against the user's turn
				const double C2 = ClearTo(Candidate(DYw, Up), Tmp);
				const double Score = FMath::Min(C2, 6.0) - 0.8 * FMath::Abs(DYw) - 0.25 * Up - (FMath::Abs(DYw - OccYawGoal) + FMath::Abs(Up - OccUpGoal) * 0.2) * 0.3;
				if (C2 >= DefLen - 0.8 && Score > BestC) { BestC = Score; BY = DYw; BU = Up; }
			}
		}
		if (BestC > -1e8) { OccYawGoal = BY; OccUpGoal = BU; }
	}
	SD(OccYawOff, OccYawOffV, OccYawGoal, 0.3, Dt);
	SD(OccUp, OccUpV, OccUpGoal, 0.3, Dt);
	if (bGndCam && GndAbsorb > 0.0 && FMath::Abs(OccYawOff) > 1e-6)
	{ // round 24: the orbit offset becomes the look yaw (the spot stays where it is; the default is that spot from now on: no spring back)
		Yaw += OccYawOff; AutoYaw += OccYawOff; OccYawGoal -= OccYawOff; OccYawOff = 0.0;
	}
	FVector Got;
	ClearTo(Cam, Got);
	const FVector ProbeSwept = Got;
	// round 15 (r14 f3 4.6-5.5 s: 43 frames with the lens inside a street-tree canopy while the hero swung through it): with the hero
	// inside geometry the spot is not swept, so lift it (then pull it toward the hero) until the lens is out of the foliage
	if (bNoSweep && World.SphereOverlaps(Got, 0.25))
	{
		bool bOut = false;
		for (double Up : { 0.8, 1.6, 2.4, 3.2, 4.0, 5.0 })
		{
			const FVector C2 = Got + FVector(0, 0, Up);
			if (!World.SphereOverlaps(C2, 0.25)) { Got = C2; bOut = true; break; }
		}
		if (!bOut)
		{
			for (double K2 : { 0.8, 0.6, 1.3, 1.6 })
			{
				const FVector C2 = Hero + (Got - Hero) * K2;
				if (!World.SphereOverlaps(C2, 0.25)) { Got = C2; break; }
			}
		}
	}
	// (round 12: the flip spot sits FlipDist out by design — the 3 m cut fired every frame and snapped to the chase orbit)
	// round 13 (critic r12: this "too close: cut to the clear orbit" rule re-armed while the flip camera blended out -> one-frame 43 deg /
	// 60 deg / 3.1 m cuts at f1 6.30 s and f4 8.58 s, then oscillated for 15 frames): no cut. The orbit search above already springs the
	// camera to a clear spot (OccYawOff / OccUp, 0.3 s); until it gets there the swept position is used, and MinHeroDist below keeps it
	// off the hero. The output slew limit (Update) bounds every frame.
	Cam = Got;
	// never closer than MinHeroDist: if the geometry forces it, rise straight up over the hero instead
	if (FVector::Dist(Cam, Hero) < MinHeroDist)
	{
		FVector Up2 = Hero + FVector(0, 0, MinHeroDist + 0.5) + BackR * 1.0;
		FVector G3;
		ClearTo(Up2, G3);
		if (FVector::Dist(G3, Hero) > FVector::Dist(Cam, Hero)) Cam = G3;
	}
	// ---- round 08 (critic r07: camera hugging / entering facades): keep the camera off the walls sideways — a spring toward
	// CamWallSoft m of clearance (toward the canyon centre, not along the wall) and a hard CamWallHard m minimum
	{
		const FVector RtC = RightFlat();
		double DR = 1e9, DL = 1e9;
		FTravHit WH;
		if (World.Raycast(Cam, RtC, CamWallSoft + 1.0, WH) && FMath::Abs(WH.Normal.Z) < 0.5) DR = WH.Distance;
		if (World.Raycast(Cam, -RtC, CamWallSoft + 1.0, WH) && FMath::Abs(WH.Normal.Z) < 0.5) DL = WH.Distance;
		double Want = 0.0;
		if (DR < CamWallSoft) Want -= CamWallSoft - DR;
		if (DL < CamWallSoft) Want += CamWallSoft - DL;
		SD(WallPush, WallPushV, Want, 0.15, Dt);
		double Push = WallPush;
		if (GndStopped) Push = 0.0; // round 24: the stopped ground orbit is not slid along the wall (that read as a yaw reversal)
		if (DR < CamWallHard) Push = FMath::Min(Push, -(CamWallHard - DR));
		if (DL < CamWallHard) Push = FMath::Max(Push, CamWallHard - DL);
		Push *= 1.0 - FlipKs; // round 16 (TC11): the trick camera never yaws round the hero -- the dolly-in along the held axis replaces the push
		if (FMath::Abs(Push) > 1e-3)
		{
			FVector Moved;
			ClearFrom(Cam, Cam + RtC * Push, Moved);
			Cam = Moved;
			FVector Seen;
			if (ClearTo(Cam, Seen) < FVector::Dist(Cam, Hero) - 0.3) Cam = Seen; // keep the hero in sight
		}
	}
	const double GY = World.GroundHeight(Cam.X, Cam.Y, Cam.Z + 0.3) + 0.4;
	if (Cam.Z < GY) Cam.Z = GY;
	// ---- round 24 (critic r23 c 7.7-8.5 s): on foot / perched the lens never sits under GndMinDist m from the hero -- crane it up over him
	// (raised at once, lowered once the unraised spot has been clear for 0.5 s)
	{
		double Goal = 0.0;
		// A landing starts the ordinary ground crane only after the trick view has blended out.
		if (bGndCam && FlipK <= 0.05)
		{
			const double R = GndMinDist + 0.2, D0 = FVector::Dist(Cam, Hero);
			const double Hd = FVector2D(Cam.X - Hero.X, Cam.Y - Hero.Y).Size(), Dz = Cam.Z - Hero.Z;
			if (D0 < R) Goal = FMath::Clamp(FMath::Sqrt(FMath::Max(0.0, R * R - Hd * Hd)) - Dz, 0.0, GndCraneMax);
		}
		if (Goal >= GndCraneGoal) { GndCraneGoal = Goal; GndClearT = 0.0; }
		else { GndClearT += Dt; if (GndClearT > 0.5 || !bGndCam) GndCraneGoal = Goal; }
		SD(GndCrane, GndCraneV, GndCraneGoal, GndCraneGoal > GndCrane ? GndCraneT : 0.4, Dt);
		if (GndCrane > 0.01)
		{
			FVector C3 = Cam + FVector(0, 0, GndCrane);
			ClearFrom(From, C3, C3);
			if (FVector::Dist(C3, Hero) > FVector::Dist(Cam, Hero)) Cam = C3;
		}
	}
	// ---- round 06: wall-run camera, blended in / out with a spring (held through the rising half of the top-out, so the
	// hero clears the roof edge in frame, then handed back to the chase camera which comes up over the edge)
	{
		const bool bOnWall = P.Mode == EWebTravMode::Wall;
		const bool bWant = bOnWall || (P.Sub == N_topOut && P.Vel.Z > 0.0);
		SD(WallK, WallKV, bWant ? 1.0 : 0.0, bWant ? 0.16 : 0.22, Dt);
		WallK = FMath::Clamp(WallK, 0.0, 1.0);
		if (bOnWall) { WallHeroXY = FVector(Hero.X, Hero.Y, 0); bWallXY = true; }
		if (WallK > 0.001)
		{
			FVector N(P.WallNormal.X, P.WallNormal.Y, 0.0);
			N = N.SizeSquared() > 0.01 ? N.GetSafeNormal() : -ForwardFlat();
			const FVector Base = (bOnWall || !bWallXY) ? Hero : FVector(WallHeroXY.X, WallHeroXY.Y, Hero.Z);
			const double Floor = World.GroundHeight(Base.X + N.X * WallCamOut, Base.Y + N.Y * WallCamOut, Hero.Z + 0.5);
			double WZ = FMath::Max(Hero.Z - WallCamBelow, Floor + 0.6);
			// round 12 (critic r11 gap 3 / F9: s3 t=20.0 -- through the top-out the roof's floor clamp parks the lens ON the roof,
			// ~3 m over the rising hero, and the wallFront reads top-down at 0.14 of the frame height): while he tops out the lens
			// never sits above his eye line; the ClearFrom sweep keeps it out of the roof geometry (it stops at the facade face,
			// over the street), so the top-out reads level-or-below with the hero big in frame
			if (P.Sub == N_topOut) WZ = FMath::Min(WZ, Hero.Z + 0.2);
			const double Dz = Hero.Z - WZ;
			const double Out = FMath::Max(WallCamOut, FMath::Sqrt(FMath::Max(0.0, WallCamDist * WallCamDist - Dz * Dz)));
			FVector WallCam(Base.X + N.X * Out, Base.Y + N.Y * Out, WZ), WallClear;
			ClearFrom(From, WallCam, WallClear);
			const double K = Smooth(WallK, 0.0, 1.0);
			FVector Bl = FMath::Lerp(Cam, WallClear, K);
			// round 26 (director: w1 camera 4-7 m on the whole run): the chord of the position blend passed ~0.3-0.7 m closer to the hero
			// than either end (w1 3.96 m at the wall entry): the blended spot keeps the blended DISTANCE (pushed out along its own ray, swept clear)
			const double DB = FMath::Lerp(FVector::Dist(Cam, Hero), FVector::Dist(WallClear, Hero), K), DN = FVector::Dist(Bl, Hero);
			if (WallDistBlend > 0.0 && DN > 0.5 && DN < DB - 0.02)
			{
				FVector Far;
				ClearFrom(From, Hero + (Bl - Hero) * (DB / DN), Far);
				if (FVector::Dist(Far, Hero) > DN) Bl = Far;
			}
			Cam = Bl;
		}
	}
	// ---- round 20 (critic r19 camera 4: after a zip a parapet hides the perched hero for 1.3 s; frames inside facades): the camera must SEE the
	// body, not only clear a sphere from the chest. Four probe points (head .. knees) are line-traced from the lens against all visible
	// collision; under 3 visible -> lift the camera (then pull it in) to the first spot that sees >= 3, fast (0.08 s spring), held 0.8 s.
	{
		const FVector Pts[4] = { Hero + FVector(0, 0, 0.6), Hero + FVector(0, 0, 0.2), Hero - FVector(0, 0, 0.3), Hero - FVector(0, 0, 0.7) };
		auto Vis = [&](const FVector& C) { int32 Nv = 0; for (const FVector& Q : Pts) { if (!World.LineBlocked(C, Q)) ++Nv; } return Nv; };
		const FVector Base = Cam;
		FVector Lifted = Base + FVector(0, 0, VisUp);
		ClearFrom(From, Lifted, Lifted);
		const int32 V0 = Vis(Lifted);
		// round 20 (capture r1 8.1 s: perched, 3 of 4 probe points visible but the parapet hid his legs, occl .48): perched, every probe point counts
		const int32 NeedVis = P.Mode == EWebTravMode::Perch ? 4 : 3;
		// round 09: the lift runs in trick mode too (it raises the lens straight up along the held axis -- TC11's no-yaw
		// constraint is kept; a hero hidden by a roof edge during a trick gets the same recovery as the chase)
		if (V0 < NeedVis)
		{
			double Found = -1.0;
			for (double Up : { 0.0, 0.6, 1.2, 1.8, 2.6, 3.5, 4.5, 6.0 })
			{
				FVector C2 = Base + FVector(0, 0, Up);
				ClearFrom(From, C2, C2);
				if (Vis(C2) >= NeedVis) { Found = Up; break; }
			}
			if (Found >= 0.0) { VisUpGoal = Found; VisHold = 0.8; }
		}
		else if (V0 >= NeedVis)
		{
			VisHold -= Dt;
			if (VisHold <= 0.0)
			{ // relax only when the unlifted spot also sees the body
				FVector C0 = Base; ClearFrom(From, C0, C0);
				if (Vis(C0) >= NeedVis) VisUpGoal = 0.0;
			}
		}
		SD(VisUp, VisUpV, VisUpGoal, VisUpGoal > VisUp ? 0.07 : 0.4, Dt);
		if (VisUp > 0.01) { FVector C3 = Base + FVector(0, 0, VisUp); ClearFrom(From, C3, Cam); }
		VisPts = Vis(Cam);
	}
	// round 05: watchdog-driven lift while the hero is out of view (roof edges) -- the probe search above only covers BLOCKED lines,
	// not an off-frame hero; the distance gain and slew boost do the horizontal part
	// round 09: also in trick mode (the watchdog runs there now)
	if (OcclBoostK > 0.01)
	{
		VisUpGoal = FMath::Max(VisUpGoal, VisBoostUp * OcclBoostK);
		FVector C4 = Cam + FVector(0, 0, VisBoostUp * OcclBoostK * 0.5);
		ClearFrom(From, C4, C4);
		if (FVector::Dist(C4, Hero) >= FVector::Dist(Cam, Hero) - 0.2) Cam = C4;
	}
	if (bGndLensHold && !GndStopPos.IsZero() && !World.LineBlocked(GndStopPos, Hero + FVector(0, 0, 0.3)))
	{
		Cam = GndStopPos; // round 24
		// round 25 (c 8.65-8.85 s: 10.3 m, bbox .06): the held lens follows the hero along its line of sight beyond GndZipHoldMax m
		const double DH = FVector::Dist(Cam, Hero);
		if (GndZipHoldMax > 0.0 && DH > GndZipHoldMax) Cam = Hero + (Cam - Hero) / DH * GndZipHoldMax;
	}
	// round 26 (director: w1 camera 4-7 m on every wall-run frame; probe: 3.95 m for ~0.1 s at the air -> wall entry, the follow springs
	// carry the dive's momentum toward the facade): on the wall the lens is never nearer than WallMinDist m -- pushed out along its own ray,
	// swept clear (a blocked push keeps the nearer spot: T19 beats T15)
	if (WallMinDist > 0.0 && WallK > 0.05 && P.Mode == EWebTravMode::Wall)
	{
		const double D0 = FVector::Dist(Cam, Hero);
		const double Want = WallMinDist;
		if (D0 > 0.5 && D0 < Want - 0.01)
		{
			FVector Far;
			ClearFrom(From, Hero + (Cam - Hero) * (Want / D0), Far);
			if (FVector::Dist(Far, Hero) > D0 && !World.LineBlocked(Far, Hero + FVector(0, 0, 0.3))) Cam = Far;
		}
	}
	CamPos = Cam;
	if (bProbe)
	{
		UE_LOG(LogWebHomage, Display, TEXT("WH_CAM_PROBE compose time=%.4f mode=%d hero=%s from=%s raw=%s floorprep=%s swept=%s final=%s flipdist=%.3f k=%.3f kr=%.3f zk=%.3f rooflift=%.3f floor=%.3f frame=%.3f"),
			Time, int32(P.Mode), *Hero.ToString(), *From.ToString(), *ProbeRaw.ToString(), *ProbeFloor.ToString(), *ProbeSwept.ToString(), *Cam.ToString(),
			FlipDistNow, FlipK, FlipKr, FlipZK, RoofLift, GY, FrameS);
		const FVector Along(FMath::Cos(FlipAzNow), FMath::Sin(FlipAzNow), 0.0);
		for (double Radius : { 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 6.5 })
		{
			const FVector Q = Hero + Along * Radius;
			FTravHit Hit;
			const bool bHit = World.Raycast(FVector(Q.X, Q.Y, Hero.Z + 8.0), FVector(0, 0, -1), 30.0, Hit);
			UE_LOG(LogWebHomage, Display, TEXT("WH_CAM_PROBE floor time=%.4f r=%.1f xy=(%.3f,%.3f) height=%.3f hit=%d normal=%s box=%d component=%s"),
				Time, Radius, Q.X, Q.Y, World.GroundHeight(Q.X, Q.Y, Hero.Z + 8.0), bHit ? 1 : 0, *Hit.Normal.ToString(), Hit.Box,
				Hit.Comp.IsValid() ? *Hit.Comp->GetPathName() : TEXT("none"));
		}
		TArray<int32> NearBoxes;
		World.Near(Hero.X, Hero.Y, 8.0, NearBoxes);
		for (int32 I : NearBoxes)
		{
			const FTravBox& B = World.Boxes[I];
			if (B.Max.Z >= Hero.Z - 4.0 && B.Min.Z <= Hero.Z + 8.0)
				UE_LOG(LogWebHomage, Display, TEXT("WH_CAM_PROBE box time=%.4f id=%d min=%s max=%s"), Time, I, *B.Min.ToString(), *B.Max.ToString());
		}
	}
	LastComposeHero = Hero; bHaveComposeHero = true;
	HeroDist = FVector::Dist(CamPos, Hero);
	bCamInGeometry = World.SphereOverlaps(CamPos, 0.15);
	// ---- orientation: yaw toward the hero; pitch puts the hero's centre at FrameS on screen (user look adds an offset)
	const FVector ToHero = Hero - CamPos;
	const double HLen = FMath::Max(0.1, FVector2D(ToHero.X, ToHero.Y).Size());
	const double DownToHero = FMath::Atan2(-ToHero.Z, HLen);
	UserPitch = Damp(UserPitch, 0.0, LastLook > 1.5 ? 1.5 : 0.0, Dt);
	const double Delta = FMath::Atan((FrameS - 0.5) * 2.0 * TanHalfV);
	// (round 06: on the wall the lower clamp opens up to an 80 deg look UP the facade)
	// (round 12: during a flip the look-up limit follows the searched elevation: + 20 deg of framing, <= 75)
	// (round 14: capped at FlipPitchUpMax -- the r13 look-up reached 53 deg)
	// round 09: while the visibility watchdog fires the look-up caps relax by up to 14 deg (the s3 pre-release rise carried the
	// hero out of the TOP of the frame against the 7.5 deg trick cap; TC5's band applies only when he is seen)
	const double FlipUpDeg = FlipPitchUpMax + VisBoostK * 14.0;
	double PitchDown = FMath::Clamp(DownToHero - Delta + UserPitch, FMath::DegreesToRadians(FMath::Lerp(FMath::Lerp(FMath::Lerp(PitchDownMin, -SkyPitchUp, SkyK), -FlipUpDeg, FlipK), -WallMaxUpDeg, Smooth(WallK, 0.0, 1.0))),
		// round 06: when collision lifts the camera high over the hero (roof edges), look down far enough that his centre
		// stays at or above 0.62 of the frame height (the fixed 22 deg limit dropped him off the bottom edge)
		FMath::Max(FMath::DegreesToRadians(22.0), DownToHero - FMath::Atan((0.62 - 0.5) * 2.0 * TanHalfV)));
	// round 20 (capture c 9.0-10.0 s: after the perch landing a look-up held from the zip aim left the crouched hero cut by the bottom edge,
	// centre at 0.92 of the frame): perched / on foot, his centre stays at or above 0.66 of the frame height and the look offset recentres fast
	// (round 24, hold B c 8.50-8.57 s: the zip fired from the roof switched the framing to the air rule and the standing hero dipped out of
	//  the bottom edge for 4 frames -- the clamp also holds through the zip's first 0.25 s)
	if (P.Mode == EWebTravMode::Perch || P.Mode == EWebTravMode::Ground || (P.Mode == EWebTravMode::Zip && P.ModeT < 0.25))
	{
		PitchDown = FMath::Max(PitchDown, DownToHero - FMath::Atan((0.66 - 0.5) * 2.0 * TanHalfV));
		if (P.Mode == EWebTravMode::Perch && LastLook > 0.3) UserPitch = Damp(UserPitch, 0.0, 4.0, Dt);
	}
	// round 05: at each web attach, look up enough that the anchor on the facade (and a band of sky) is on screen for
	// ~0.7 s, then settle back (spring); the hero stays in frame below
	double LookWant = 0.0, FovWant = 0.0;
	if (bSwinging && P.bHasAnchor && P.SwingT < 0.5)
	{
		const FVector ToA = P.Anchor - CamPos;
		const double UpToAnchor = FMath::Atan2(ToA.Z, FMath::Max(0.1, FVector2D(ToA.X, ToA.Y).Size()));
		const double TopM = FMath::DegreesToRadians(4.0), BotM = FMath::DegreesToRadians(12.0); // round 07: 8 -> 12
		// if anchor (top) and hero (bottom) cannot both fit, widen the view for the attach beat (<= 20 deg)
		const double Span = UpToAnchor + DownToHero + TopM + BotM;
		FovWant = FMath::Clamp(Span - VFov, 0.0, FMath::DegreesToRadians(AttachFovMax)); // round 08: 26 -> 10 deg (92-95 deg fish-eye shrank the hero)
		const double Half = (VFov + FovWant) * 0.5;
		const double Need = UpToAnchor - (Half - TopM);             // pitch-up that puts it TopM inside the top
		// round 10 (TRAVERSAL-SPEC T5 voids anchor-in-frame; T10 hero centre y <= 0.70, critic r09 cy p95 .72): the look-up stops
		// where the hero centre reaches AttachMaxS of the frame height (was: hero 12 deg inside the bottom edge -> cy up to .87)
		(void)BotM;
		const double HeroLimit = FMath::Atan((AttachMaxS - 0.5) * 2.0 * FMath::Tan(Half)) - DownToHero;
		LookWant = FMath::Max(0.0, FMath::Min(Need + PitchDown, HeroLimit + PitchDown));
		// round 07: the new swings open with a steep swoop (up to 40 m/s down) — the look-up fades out as he falls faster so
		// the hero does not drop off the bottom edge
		LookWant *= FMath::Clamp(1.0 - (-P.Vel.Z - 8.0) / 14.0, 0.0, 1.0);
	}
	// horizontal: turn toward an anchor that is outside the sides (hero kept 10 deg inside the opposite edge)
	double YawWant = 0.0;
	const double ToHeroYaw = FMath::Atan2(ToHero.Y, ToHero.X);
	if (bSwinging && P.bHasAnchor && P.SwingT < 0.5)
	{
		const FVector ToA = P.Anchor - CamPos;
		const double HalfH = FMath::Atan(FMath::Tan((VFov + FovWant) * 0.5) * 16.0 / 9.0);
		const double DA = FMath::Atan2(FMath::Sin(FMath::Atan2(ToA.Y, ToA.X) - ToHeroYaw), FMath::Cos(FMath::Atan2(ToA.Y, ToA.X) - ToHeroYaw));
		const double Over = FMath::Abs(DA) - (HalfH - FMath::DegreesToRadians(5.0));
		if (Over > 0) YawWant = FMath::Sign(DA) * FMath::Min(Over, HalfH - FMath::DegreesToRadians(10.0));
	}
	// round 07: gentler, capped turn toward an off-screen anchor (the 0.035 s spring whipped the view ~45 deg in 0.1 s)
	// round 06 (critic r05: hero at the frame edge through the swing after the attach): cap 25 -> 16 deg so the attach beat
	// off-centres him less
	YawWant = FMath::Clamp(YawWant, -FMath::DegreesToRadians(16.0), FMath::DegreesToRadians(16.0));
	YawWant *= 1.0 - FlipKs; // round 16 (TC3): no attach yaw beat while the trick camera is in -- the view turns only with the blend-out
	if (bFirst) { AttachYaw = YawWant; AttachLook = LookWant; AttachFov = FovWant; AttachYawV = AttachLookV = AttachFovV = 0.0; }
	// round 13: a web caught out of a flip (flip camera still blending out) turns the view more gently (per-frame yaw budget)
	const double AttachSt = P.SwingT < 0.5 ? (FlipK > 0.05 ? 0.25 : 0.12) : 0.3;
	SD(AttachYaw, AttachYawV, YawWant, AttachSt, Dt);
	// round 10 (critic r09: camera pop at b 0.000-0.017 s, a web attached on the first frame): 0.035 s -> 0.12 s springs
	SD(AttachLook, AttachLookV, LookWant, AttachSt, Dt);
	SD(AttachFov, AttachFovV, FovWant, AttachSt, Dt);
	PitchDown -= AttachLook;
	// ---- round 14 (critic r13: "within 0.5 s of attach return the pitch to 4-12 deg down"; r13 f4 medians -1..+9 deg UP 0.5-1.0 s after
	// the attaches: the attach look-up beat + the arc-bottom framing looked up): from SettleT0 to SettleT1 s after a web attaches the
	// pitch is pulled into the settle band, as long as the hero stays inside 0.18..0.82 of the frame height
	{
		const double WallW = Smooth(WallK, 0.0, 1.0);
		if (bSwinging && P.SwingT < 90.0)
		{
			const double Sk = Smooth(P.SwingT, SettleT0, SettleT1) * (1.0 - WallW);
			if (Sk > 0.0)
			{
				const double Keep = FMath::Atan(0.64 * TanHalfV);
				const double Lo = FMath::Min(FMath::DegreesToRadians(SettleDownMin), DownToHero + Keep);
				const double Hi = FMath::Max(FMath::DegreesToRadians(SettleDownMax), DownToHero - Keep);
				PitchDown = FMath::Lerp(PitchDown, FMath::Clamp(PitchDown, Lo, Hi), Sk);
			}
		}
		// hard look-up cap for every view but the wall-run camera (critic r13 test: pitch never > 30 deg up)
		// (round 15: the flip view is capped at FlipPitchUpMax from FlipK 0.3 on -- also while it blends out -- the wall camera at WallMaxUpDeg)
		// (round 09: + the watchdog relief while the hero is unseen)
		CapUpDeg = FMath::Lerp(FMath::Lerp(MaxLookUpDeg, FlipUpDeg, Smooth(FlipK, 0.0, 0.3)), WallMaxUpDeg + VisBoostK * 14.0, WallW);
		PitchDown = FMath::Max(PitchDown, -FMath::DegreesToRadians(CapUpDeg));
	}
	Pitch = PitchDown; // keep the orbit state coherent for Forward()
	// (round 09: the hero stays centred horizontally — TRAVERSAL-SPEC T9; the off-axis look comes from the sideways slide)
	// (round 16, TC7: a small lead-room yaw bias toward the hero's travel -- the hero sits on the trailing side of the frame, x ~ .45-.55)
	CamRot = FRotator(FMath::RadiansToDegrees(-PitchDown), FMath::RadiansToDegrees(ToHeroYaw + AttachYaw - FlipSide * FMath::DegreesToRadians(FlipLeadDeg) * FlipKs), 0);
}

// round 16 (TRICK_CAMERA_SPEC TC1 / TC2): choose the trick camera's view ONCE, at the release frame; it is never re-searched.
// Candidates: yaw offsets FlipYawMin..FlipYawMax deg from the travel-behind direction on both sides, FlipDist m out, FlipDrop m under the
// hero. Order: (1) obstruction -- the spot must be sweep-reachable from the hero with FlipWallMargin m free beyond it and a clear path
// FlipAheadT s along the travel; (2) sun -- the view at least SunMinDeg from the sun; (3) open space (lateral free distance, background
// sky share, a graded clear-path time, no glare facade). A side that passes (1) wins over one that fails it, even if it fails (2). If
// nothing passes at FlipDist the same yaws are tried pulled in (TC11) down to FlipDistMin, and if that fails too the plain chase is used
// (Tier 3) -- never a side-on orbit.
void FWebTravCamera::ChooseFlipView(const FTravCamInput& P, const FWebTravWorld& World)
{
	const FVector Hero = P.Pos;
	const FVector VF(P.Vel.X, P.Vel.Y, 0.0);
	const double HS = VF.Size();
	const double Head = HS > 1.5 ? FMath::Atan2(VF.Y, VF.X) : Yaw;   // travel heading (rad)
	const double BackAz = Head + PI;
	const bool bKeep = FlipK > 0.05 && !bFlipAbort;
	double CurOff = 0.0; // the side the chase camera is on at the release (a tie-break: the blend-in moves the least)
	{
		const FVector Off = CamPos - Hero;
		if (bChaseInit && FVector2D(Off.X, Off.Y).Size() > 0.2) CurOff = WrapA(FMath::Atan2(Off.Y, Off.X) - BackAz);
	}
	static const double RingDeg[][2] = { {0, 11}, {0, -11}, {8, 0}, {-8, 0}, {8, 11}, {-8, 11}, {8, -11}, {-8, -11},
		{8, 5}, {-8, 5}, {8, -5}, {-8, -5}, {4, 11}, {-4, 11}, {4, -11}, {-4, -11} };
	struct FCand { double Az = 0, Off = 0, Rad = 0, Open = 0, Sky = 0, Glare = 0, Sun = 180, ClearT = 0, Cost = 0; int32 Side = 1, Tier = 3, Why = 0; };
	auto Eval = [&](double OffDeg, int32 Side, double Rad, FCand& C) -> bool // true = passes (1) obstruction
	{
		C.Side = Side; C.Off = OffDeg; C.Rad = Rad;
		C.Az = BackAz + Side * FMath::DegreesToRadians(OffDeg);
		const double E = FMath::Asin(FMath::Clamp(FlipDrop / FMath::Max(1.0, FlipDist), 0.0, 0.6));
		const FVector ToCam(FMath::Cos(C.Az) * FMath::Cos(E), FMath::Sin(C.Az) * FMath::Cos(E), -FMath::Sin(E));
		const FVector CamP = Hero + ToCam * Rad;
		double HitD = 0.0;
		if (World.SphereSweep(Hero, CamP, 0.3, HitD)) { C.Why = 1; return false; }
		if (World.SphereSweep(CamP, CamP + ToCam * FlipWallMargin, 0.3, HitD)) { C.Why = 2; return false; }
		if (HS > 1.0 && World.SphereSweep(CamP, CamP + VF * FlipAheadT, 0.3, HitD)) { C.Why = 3; return false; }
		if (CamP.Z < World.GroundHeight(CamP.X, CamP.Y, CamP.Z + 0.5) + 0.5) { C.Why = 4; return false; }
		// graded clearance: how far along the predicted travel (ballistic, 0.25 s steps) the camera spot stays clear
		{
			FVector Prev = CamP;
			C.ClearT = 1.5;
			for (int32 K = 1; K <= 6; ++K)
			{
				const double Tt = 0.25 * K;
				const FVector Nx = CamP + VF * Tt + FVector(0, 0, P.Vel.Z * Tt - 3.0 * Tt * Tt);
				if (World.SphereSweep(Prev, Nx, 0.3, HitD) || World.SphereOverlaps(Nx, 0.3)) { C.ClearT = 0.25 * (K - 1); break; }
				Prev = Nx;
			}
		}
		// open space: lateral free distance from the hero toward the camera side, background sky share, glare facades
		{
			FTravHit H;
			const FVector HDir(ToCam.X, ToCam.Y, 0.0);
			C.Open = World.Raycast(Hero, HDir.GetSafeNormal(), 30.0, H) ? FMath::Min(30.0, H.Distance) / 30.0 : 1.0;
			const FVector D = -ToCam;
			const FVector Rt = FVector::CrossProduct(FVector::UpVector, D).GetSafeNormal();
			const FVector Up = FVector::CrossProduct(D, Rt).GetSafeNormal();
			int32 Free = 0, N = 0, Glr = 0;
			for (const auto& RD : RingDeg)
			{
				const FVector Dir = (D + Rt * FMath::Tan(FMath::DegreesToRadians(RD[0])) + Up * FMath::Tan(FMath::DegreesToRadians(RD[1]))).GetSafeNormal();
				FTravHit Hh;
				++N;
				if (!World.Raycast(CamP + Dir * (Rad + 0.6), Dir, 900.0, Hh)) ++Free;
				else if (bHaveSun && FMath::Abs(Hh.Normal.Z) < 0.5)
				{ // a background facade whose mirror direction lies within GlareDeg of the sun mirrors it into the lens (rendered r14 f4 9.85 s)
					const FVector Rf = Dir - 2.0 * FVector::DotProduct(Dir, Hh.Normal) * Hh.Normal;
					if (FVector::DotProduct(Rf.GetSafeNormal(), SunDir) > FMath::Cos(FMath::DegreesToRadians(GlareDeg))) ++Glr;
				}
			}
			C.Sky = double(Free) / double(FMath::Max(1, N));
			C.Glare = double(Glr) / double(FMath::Max(1, N));
			C.Sun = bHaveSun ? FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FVector::DotProduct(D, SunDir), -1.0, 1.0))) : 180.0;
		}
		C.Tier = C.Sun >= SunMinDeg ? 0 : 1;
		C.Cost = 2.0 * (1.0 - C.Open) + FlipSkyW * (1.0 - C.Sky) + 4.0 * (1.0 - C.ClearT / 1.5) + GlareW * C.Glare
			+ 2.0 * FMath::Max(0.0, SunPrefDeg - C.Sun) / 40.0
			+ 0.6 * FMath::Abs(OffDeg - FlipPrefYaw) / 5.0 + (FMath::Sign(CurOff) != double(Side) ? 0.25 : 0.0)
			// round 18: while the previous trick's view is still blended (a flip chain), stay near its azimuth (no swing across behind him)
			+ (bKeep ? 0.08 * FMath::Abs(FMath::RadiansToDegrees(WrapA(C.Az - FlipAzNow))) : 0.0);
		return true;
	};
	// round 18 (critic r17 TC-A p5 20-29): the look direction leads the held azimuth by ~5-7 deg, so a 35 deg azimuth read 28-29 on pcm_yaw -> 40-55
	static const double OffsDeg[] = { 40.0, 44.0, 48.0, 52.0, 55.0 }; // round 17: 35 added (TC1 35-55)
	FCand Best; bool bHave = false;
	FString Log;
	int32 BestTier = 99, BestRank = 99;
	// round 17 (critic r16 "at release pick the 35-55 deg side that already has view_sun >= 100"): rank 0 = clear at FlipDist + sun ok,
	// 1 = sun ok but pulled in (TC11), 2 = only a sun-facing side is clear (r16 took that before pulling in: n1 probe 53 deg from the sun)
	for (int32 Stage = 0; Stage < 4 && BestRank > 0; ++Stage)
	{
		const double Rd = Stage == 0 ? FlipDist : FMath::Lerp(FlipDist, FlipDistMin, double(Stage) / 3.0);
		for (double O : OffsDeg)
		{
			if (O < FlipYawMin - 1e-3 || O > FlipYawMax + 1e-3) continue;
			for (int32 Side : { 1, -1 })
			{
				FCand C;
				if (!Eval(O, Side, Rd, C)) { Log += FString::Printf(TEXT(" [%+.0f@%.1f fail%d]"), Side * O, Rd, C.Why); continue; }
				Log += FString::Printf(TEXT(" [%+.0f@%.1f sun%.0f open%.2f sky%.2f clr%.2f cost%.2f]"), Side * O, Rd, C.Sun, C.Open, C.Sky, C.ClearT, C.Cost);
				if (Stage > 0) { C.Cost += C.Sun >= SunMinDeg ? 0.0 : 100.0; C.Tier = C.Sun >= SunMinDeg ? 2 : 1; } // pulled in along the same yaw (TC11)
				const int32 Rank = C.Sun < SunMinDeg ? 2 : (Stage == 0 ? 0 : 1);
				if (!bHave || Rank < BestRank || (Rank == BestRank && C.Cost < Best.Cost)) { Best = C; BestTier = C.Tier; BestRank = Rank; bHave = true; }
			}
		}
	}
	(void)BestTier;
	UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV trick camera choice at hero (%.1f, %.1f, %.1f) heading %.0f:%s"), Hero.X, Hero.Y, Hero.Z, FMath::RadiansToDegrees(Head), *Log);
	if (!bHave) { FlipTier = 3; FlipDistSel = FlipDist; FlipSkyShare = -1.0; return; }
	FlipAz = Best.Az; FlipSide = double(Best.Side); FlipOffDeg = Best.Side * Best.Off; FlipDistSel = Best.Rad; FlipTier = Best.Tier;
	FlipSkyShare = Best.Sky; FlipSunDeg = Best.Sun; FlipGlare = Best.Glare;
}

bool FWebTravCamera::SetTune(const FString& Name, double V)
{
	struct FT { const TCHAR* N; double* P; };
	const FT Tab[] = { {TEXT("SunMinDeg"), &SunMinDeg}, {TEXT("SunPrefDeg"), &SunPrefDeg}, {TEXT("FlipDist"), &FlipDist}, {TEXT("FlipDistMin"), &FlipDistMin},
		{TEXT("FlipDrop"), &FlipDrop}, {TEXT("FlipDistMax"), &FlipDistMax}, {TEXT("FlipDistCompact"), &FlipDistCompact}, {TEXT("FlipExtK"), &FlipExtK}, {TEXT("FlipAzHold"), &FlipAzHold}, {TEXT("FlipAzRate"), &FlipAzRate}, {TEXT("FlipTuckPull"), &FlipTuckPull}, {TEXT("FlipCompactT"), &FlipCompactT}, {TEXT("FlipYawMin"), &FlipYawMin}, {TEXT("FlipYawMax"), &FlipYawMax}, {TEXT("FlipPrefYaw"), &FlipPrefYaw},
		{TEXT("FlipLeadDeg"), &FlipLeadDeg}, {TEXT("FlipSFrame"), &FlipSFrame}, {TEXT("FlipPitchUpMax"), &FlipPitchUpMax}, {TEXT("MaxLookUpDeg"), &MaxLookUpDeg},
		{TEXT("FlipInT"), &FlipInT}, {TEXT("FlipOutT"), &FlipOutT}, {TEXT("FlipZInT"), &FlipZInT}, {TEXT("FlipDollyInT"), &FlipDollyInT}, {TEXT("FlipDollyOutT"), &FlipDollyOutT},
		{TEXT("FlipWallMargin"), &FlipWallMargin}, {TEXT("FlipAheadT"), &FlipAheadT},
		{TEXT("WallCamBelow"), &WallCamBelow}, {TEXT("WallCamOut"), &WallCamOut}, {TEXT("WallCamDist"), &WallCamDist}, {TEXT("WallDistBlend"), &WallDistBlend}, {TEXT("WallMinDist"), &WallMinDist},
		{TEXT("WallFrameS"), &WallFrameS}, {TEXT("FlipSkyW"), &FlipSkyW}, {TEXT("FlipInRate"), &FlipInRate}, {TEXT("FlipInAcc"), &FlipInAcc}, {TEXT("FlipInDec"), &FlipInDec}, {TEXT("WallMaxUpDeg"), &WallMaxUpDeg}, {TEXT("SettleDownMin"), &SettleDownMin},
		{TEXT("SettleDownMax"), &SettleDownMax}, {TEXT("GlareDeg"), &GlareDeg}, {TEXT("GlareW"), &GlareW},
		{TEXT("GndFloorPull"), &GndFloorPull}, {TEXT("GndFloorPullMin"), &GndFloorPullMin}, {TEXT("GndStop"), &GndStop}, {TEXT("GndHoldLens"), &GndHoldLens}, {TEXT("GndLensRelease"), &GndLensRelease}, {TEXT("GndStopExtra"), &GndStopExtra}, {TEXT("GndStopR"), &GndStopR}, {TEXT("GndMinDist"), &GndMinDist}, {TEXT("GndLookHold"), &GndLookHold}, {TEXT("GndAbsorb"), &GndAbsorb}, {TEXT("GndCraneT"), &GndCraneT}, {TEXT("GndCraneMax"), &GndCraneMax}, {TEXT("PerchHold"), &PerchHold}, {TEXT("GndZipHoldMax"), &GndZipHoldMax},
		{TEXT("ChaseFbSwing"), &ChaseFbSwing}, {TEXT("ChaseFbAir"), &ChaseFbAir}, {TEXT("ChaseFbGain"), &ChaseFbGain}, {TEXT("ChaseFbMin"), &ChaseFbMin}, {TEXT("ChaseFbMax"), &ChaseFbMax},
		{TEXT("VisWhipMul"), &VisWhipMul}, {TEXT("VisBoostT"), &VisBoostT}, {TEXT("VisBoostBack"), &VisBoostBack}, {TEXT("VisBoostUp"), &VisBoostUp} };
	for (const FT& T : Tab) if (Name == T.N) { *T.P = V; return true; }
	return false;
}
