// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
// Hero v2 (owner-approved model, 2026-10-15): clip-driven anim instance. See WHHeroV2AnimInstance.h and
// docs/invincible/loop/heroV2_integration_NOTES.md (state -> clip table, tunables, capture checks).
#include "Traversal/Anim/WHHeroV2AnimInstance.h"
#include "Traversal/WebTravCharacter.h"
#include "Traversal/WebTraversalComponent.h"
#include "Flight/WHRescueDirector.h"
#include "Flight/WHFlightComponent.h"
#include "WebHomage.h"
#include "Animation/Skeleton.h"
#include "Math/RotationMatrix.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimNodeBase.h"
#include "AnimationRuntime.h"
#include "BonePose.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "ReferenceSkeleton.h"
#include "HAL/PlatformTime.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "UObject/UnrealType.h"

// (unity build: every helper lives in a named namespace so it cannot collide with the other traversal files' anonymous helpers)
namespace WHHeroV2Detail
{
	const FName HV2NTakeoff(TEXT("takeoff")), HV2NHover(TEXT("hover")), HV2NFly(TEXT("fly")), HV2NBoost(TEXT("boost")), HV2NBrake(TEXT("brake")),
		HV2NDash(TEXT("dash")), HV2NSlam(TEXT("slam")), HV2NBreach(TEXT("breach")), HV2NLandHero(TEXT("landHero"));
	float HV2Smooth(float X, float A, float B) { const float T = FMath::Clamp((X - A) / FMath::Max(B - A, 1e-6f), 0.f, 1.f); return T * T * (3.f - 2.f * T); }
	/** Inverse of smoothstep on [0, 1] (the flight's ChargeK = smoothstep(SuperT / SuperChargeTime)): x = 1/2 - sin(asin(1 - 2y) / 3). */
	float HV2InvSmooth(float Y) { Y = FMath::Clamp(Y, 0.f, 1.f); return 0.5f - FMath::Sin(FMath::Asin(1.f - 2.f * Y) / 3.f); }
	bool HV2IsFlyType(EWHHeroV2State S) { return S == EWHHeroV2State::Fly || S == EWHHeroV2State::BoostHold || S == EWHHeroV2State::Dash || S == EWHHeroV2State::Breach; }
	/** component-space transform of a reference-skeleton bone (ref pose) */
	FTransform HV2RefCS(const FReferenceSkeleton& RS, int32 I)
	{
		FTransform T = FTransform::Identity;
		while (I != INDEX_NONE) { T = T * RS.GetRefBonePose()[I]; I = RS.GetParentIndex(I); }
		return T;
	}
	/** support distance of a box (half extents along the rotation's axes) along a unit direction */
	double HV2BoxSupport(const FQuat& Q, const FVector& Half, const FVector& D)
	{
		return Half.X * FMath::Abs(FVector::DotProduct(Q.GetAxisX(), D)) + Half.Y * FMath::Abs(FVector::DotProduct(Q.GetAxisY(), D))
			+ Half.Z * FMath::Abs(FVector::DotProduct(Q.GetAxisZ(), D));
	}
	/** r7: component-space transform of a skeleton bone in a clip at time T (a bone without a track keeps its reference transform) */
	FTransform HV2ClipCS(const UAnimSequence* S, const FReferenceSkeleton& RS, int32 I, double T)
	{
		FTransform X = FTransform::Identity;
		const FAnimExtractContext Ctx(T, false, {}, false);
		while (I != INDEX_NONE)
		{
			FTransform L = RS.GetRefBonePose()[I];
			S->GetBoneTransform(L, FSkeletonPoseBoneIndex(I), Ctx, false);
			X = X * L;
			I = RS.GetParentIndex(I);
		}
		return X;
	}
	/** r7: feet midpoint -> head joint of a clip pose (component space) */
	FVector HV2ClipBodyAxis(const UAnimSequence* S, const FReferenceSkeleton& RS, int32 Ih, int32 Il, int32 Ir, double T)
	{
		return HV2ClipCS(S, RS, Ih, T).GetLocation() - (HV2ClipCS(S, RS, Il, T).GetLocation() + HV2ClipCS(S, RS, Ir, T).GetLocation()) * 0.5;
	}
}

// r5 (critic r4 #5 / #6): the arm chains of the CustomUse rig (left_ / right_ collar, shoulder, elbow, wrist, fingers)
bool FWHHeroV2AnimProxy::IsArmBone(const FName& Bone)
{
	// (called on the evaluation worker: a function-local static is initialised once, thread-safely)
	static const TSet<FName> Arm = []()
	{
		TSet<FName> S;
		const TCHAR* Sides[] = { TEXT("left_"), TEXT("right_") };
		const TCHAR* Parts[] = { TEXT("collar"), TEXT("shoulder"), TEXT("elbow"), TEXT("wrist") };
		const TCHAR* Fingers[] = { TEXT("index"), TEXT("middle"), TEXT("pinky"), TEXT("ring"), TEXT("thumb") };
		for (const TCHAR* Sd : Sides)
		{
			for (const TCHAR* P : Parts) S.Add(FName(*FString::Printf(TEXT("%s%s"), Sd, P)));
			for (const TCHAR* F : Fingers) for (int32 K = 1; K <= 3; ++K) S.Add(FName(*FString::Printf(TEXT("%s%s%d"), Sd, F, K)));
		}
		return S;
	}();
	return Arm.Contains(Bone);
}

const TCHAR* UWHHeroV2AnimInstance::ClipRoot = TEXT("/Game/Invincible/HeroV2/Anims");

const TCHAR* UWHHeroV2AnimInstance::ClipAsset(EWHHeroV2Clip C)
{
	switch (C)
	{
	case EWHHeroV2Clip::Hover: return TEXT("AS_Hover");
	case EWHHeroV2Clip::Fly: return TEXT("AS_Fly");
	case EWHHeroV2Clip::LaunchUp: return TEXT("AS_LaunchUp");
	case EWHHeroV2Clip::BoostLaunch: return TEXT("AS_BoostLaunch");
	case EWHHeroV2Clip::BoostHold: return TEXT("AS_BoostHold");
	case EWHHeroV2Clip::Brake: return TEXT("AS_Brake");
	case EWHHeroV2Clip::LandHero: return TEXT("AS_LandHero");
	case EWHHeroV2Clip::Takeoff: return TEXT("AS_Takeoff");
	case EWHHeroV2Clip::GroundIdle: return TEXT("AS_GroundIdle");
	case EWHHeroV2Clip::PunchCombo: return TEXT("AS_PunchCombo");
	case EWHHeroV2Clip::Jab: return TEXT("AS_Jab");
	case EWHHeroV2Clip::FlyingFistKick: return TEXT("AS_FlyingFistKick");
	default: return TEXT("none");
	}
}

const TCHAR* UWHHeroV2AnimInstance::StateName(EWHHeroV2State S)
{
	switch (S)
	{
	case EWHHeroV2State::GroundIdle: return TEXT("groundIdle");
	case EWHHeroV2State::Takeoff: return TEXT("takeoff");
	case EWHHeroV2State::Hover: return TEXT("hover");
	case EWHHeroV2State::LaunchUp: return TEXT("launchUp");
	case EWHHeroV2State::Fly: return TEXT("fly");
	case EWHHeroV2State::Dash: return TEXT("dash");
	case EWHHeroV2State::BoostLaunch: return TEXT("boostLaunch");
	case EWHHeroV2State::BoostHold: return TEXT("boostHold");
	case EWHHeroV2State::Brake: return TEXT("brake");
	case EWHHeroV2State::LandHero: return TEXT("landHero");
	case EWHHeroV2State::Breach: return TEXT("breach");
	default: return TEXT("none");
	}
}

bool UWHHeroV2AnimInstance::IsLoopClip(int32 C)
{
	const EWHHeroV2Clip E = EWHHeroV2Clip(C);
	return E == EWHHeroV2Clip::Hover || E == EWHHeroV2Clip::Fly || E == EWHHeroV2Clip::LaunchUp || E == EWHHeroV2Clip::BoostHold || E == EWHHeroV2Clip::GroundIdle;
}

const TCHAR* UWHHeroV2AnimInstance::CurrentClipName() const
{
	return Tracks.Num() && Tracks.Last().Clip >= 0 ? ClipAsset(EWHHeroV2Clip(Tracks.Last().Clip)) : TEXT("none");
}

// Hero v2 mesh frame (owner request: ~1.85 m, feet on the capsule bottom, facing the actor's forward; glTF unit scale checked at runtime):
// up = feet -> head, forward = ankle -> foot (the same rule the clip tools use, tools/invincible/post_take.py), height from the imported
// vertex bounds along up (the ref pose is an arms-down A pose, so up is also the largest extent).
bool UWHHeroV2AnimInstance::ComputeRefFrame(const USkeletalMesh* Mesh, FWHHeroV2RefFrame& Out)
{
	if (!Mesh) return false;
	const FReferenceSkeleton& RS = Mesh->GetRefSkeleton();
	bool bOk = true;
	auto RefCS = [&RS, &bOk](const TCHAR* Name) -> FVector
	{
		int32 I = RS.FindBoneIndex(FName(Name));
		if (I == INDEX_NONE) { bOk = false; return FVector::ZeroVector; }
		FTransform T = FTransform::Identity;
		while (I != INDEX_NONE) { T = T * RS.GetRefBonePose()[I]; I = RS.GetParentIndex(I); }
		return T.GetLocation();
	};
	const FVector Head = RefCS(TEXT("head")), Pelvis = RefCS(TEXT("pelvis"));
	const FVector FootL = RefCS(TEXT("left_foot")), FootR = RefCS(TEXT("right_foot"));
	const FVector AnkL = RefCS(TEXT("left_ankle")), AnkR = RefCS(TEXT("right_ankle"));
	if (!bOk) return false;
	const FVector Up = (Head - (FootL + FootR) * 0.5).GetSafeNormal();
	if (Up.IsNearlyZero()) return false;
	FVector Fwd = (FootL - AnkL) + (FootR - AnkR);
	Fwd -= Up * FVector::DotProduct(Fwd, Up);
	if (Fwd.SizeSquared() < 1e-8)
	{ // fallback: right x up (UE axes: Y x Z = X), right = left foot -> right foot
		Fwd = FVector::CrossProduct(FootR - FootL, Up);
		Fwd -= Up * FVector::DotProduct(Fwd, Up);
	}
	Fwd = Fwd.GetSafeNormal();
	if (Fwd.IsNearlyZero()) return false;
	Out.Up = Up; Out.Fwd = Fwd; Out.Pelvis = Pelvis;
	Out.RefFootUp = FMath::Min(FVector::DotProduct(FootL, Up), FVector::DotProduct(FootR, Up));
	const FBoxSphereBounds B = Mesh->GetImportedBounds();
	const double Half = FMath::Abs(B.BoxExtent.X * Up.X) + FMath::Abs(B.BoxExtent.Y * Up.Y) + FMath::Abs(B.BoxExtent.Z * Up.Z);
	if (Half > 1e-4)
	{
		Out.HeightUnits = 2.0 * Half;
		Out.BottomUp = FVector::DotProduct(B.Origin, Up) - Half;
	}
	else
	{ // no usable bounds: head joint -> foot joints x 1.25 (head top / soles), soles at the foot joints
		Out.HeightUnits = (FVector::DotProduct(Head, Up) - Out.RefFootUp) * 1.25;
		Out.BottomUp = Out.RefFootUp;
	}
	return Out.HeightUnits > 1e-4;
}

void UWHHeroV2AnimInstance::ApplyTune(const FString& Tune)
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
			UE_LOG(LogWebHomage, Display, TEXT("WH_HEROV2 tune %s = %s"), *K, *V);
		}
		else UE_LOG(LogWebHomage, Warning, TEXT("WH_HEROV2 tune: no float property %s"), *K);
	}
}

void UWHHeroV2AnimInstance::NativeInitializeAnimation()
{
	Super::NativeInitializeAnimation();
	Clips.SetNum(int32(EWHHeroV2Clip::Num));
	const USkeletalMeshComponent* SMC = GetSkelMeshComponent();
	const USkeletalMesh* Mesh = SMC ? SMC->GetSkeletalMeshAsset() : nullptr;
	FString Missing, Mismatch;
	int32 NLoaded = 0;
	for (int32 C = 0; C < int32(EWHHeroV2Clip::Num); ++C)
	{
		const TCHAR* Nm = ClipAsset(EWHHeroV2Clip(C));
		UAnimSequence* S = LoadObject<UAnimSequence>(nullptr, *FString::Printf(TEXT("%s/%s.%s"), ClipRoot, Nm, Nm));
		Clips[C] = S;
		if (!S) { Missing += FString(Missing.IsEmpty() ? TEXT("") : TEXT(" ")) + Nm; continue; }
		++NLoaded;
		if (Mesh && S->GetSkeleton() != Mesh->GetSkeleton()) Mismatch += FString(Mismatch.IsEmpty() ? TEXT("") : TEXT(" ")) + Nm;
	}
	bRefOk = Mesh && ComputeRefFrame(Mesh, Ref);
	Frame.bRefOk = bRefOk;
	Frame.UpCS = Ref.Up;
	Frame.RefFootUp = float(Ref.RefFootUp);
	Frame.MaxShift = float(Ref.HeightUnits * 0.45);
	InitArmFix(bRefOk ? Mesh : nullptr);
	if (bRefOk) { AnalyzeLandClip(); AnalyzeBoostClip(); AnalyzeHoverClip(); }   // r7: + boost burst span, hover phase / breathing
	{ // -WHHeroV2Tune=Name=Value,... (float UPROPERTYs above; after the clip analysis, so a tune overrides the measured land frames)
		FString Tune;
		if (FParse::Value(FCommandLine::Get(), TEXT("-WHHeroV2Tune="), Tune, false) && !Tune.IsEmpty()) ApplyTune(Tune);
	}
	Tracks.Reset();
	DipT = 99.f; CarryW = 0.f; bCarry = false;
	BurstS = -1.f; BobW = 0.f; StandWant = StandNudge = FVector::ZeroVector;
	UE_LOG(LogWebHomage, Display, TEXT("WH_HEROV2 anim init: %d/%d clips from %s (missing: %s; skeleton mismatch: %s), ref %s up %s fwd %s footUp %.2f height %.2f units"),
		NLoaded, int32(EWHHeroV2Clip::Num), ClipRoot, Missing.IsEmpty() ? TEXT("none") : *Missing, Mismatch.IsEmpty() ? TEXT("none") : *Mismatch,
		bRefOk ? TEXT("ok") : TEXT("MISSING BONES (no ground lock)"), *Ref.Up.ToString(), *Ref.Fwd.ToString(), Ref.RefFootUp, Ref.HeightUnits);
}

// r5 (critic r4 #1): constants of the arm swing fix -- the upper arm's bone axis (shoulder -> elbow, shoulder local) and the body's forward
// in the collar parent's (chest's) frame, both from the reference pose. Also the chest bone + forward used by the carry anchor.
void UWHHeroV2AnimInstance::InitArmFix(const USkeletalMesh* Mesh)
{
	Frame.bArmFix = false;
	ChestBone = NAME_None;
	if (!Mesh) return;
	const FReferenceSkeleton& RS = Mesh->GetRefSkeleton();
	const TCHAR* Sd[2] = { TEXT("left_"), TEXT("right_") };
	for (int32 S = 0; S < 2; ++S)
	{
		const int32 Ic = RS.FindBoneIndex(FName(*FString::Printf(TEXT("%scollar"), Sd[S])));
		const int32 Is = RS.FindBoneIndex(FName(*FString::Printf(TEXT("%sshoulder"), Sd[S])));
		const int32 Ie = RS.FindBoneIndex(FName(*FString::Printf(TEXT("%selbow"), Sd[S])));
		if (Ic == INDEX_NONE || Is == INDEX_NONE || Ie == INDEX_NONE || RS.GetParentIndex(Is) != Ic || RS.GetParentIndex(Ie) != Is) return;
		const int32 Ip = RS.GetParentIndex(Ic);
		const FVector Ax = RS.GetRefBonePose()[Ie].GetTranslation();
		if (Ip == INDEX_NONE || Ax.IsNearlyZero()) return;
		Frame.ArmAxis[S] = Ax.GetSafeNormal();
		Frame.ChestFwd[S] = WHHeroV2Detail::HV2RefCS(RS, Ip).GetRotation().UnrotateVector(Ref.Fwd).GetSafeNormal();
		if (S == 0) { ChestBone = RS.GetBoneName(Ip); ChestFwdLocal = Frame.ChestFwd[0]; }
	}
	Frame.bArmFix = true;
}

// r5 (critic r4 #3, fl11 "head-first dive then a 180 deg flip in ~2 frames"): the land clip is read at init. h(t) = pelvis height over the
// lower foot along the mesh up: negative in the head-first dive, growing as the legs swing under, a plateau in the kneel. LandFeetT = first
// frame at half the plateau (feet under the body), LandImpactT = first frame at 92 % (the kneel contact). Out-of-range results keep the
// tunables (offline FK of hero_land.glb: 0.43 / 0.49 s).
void UWHHeroV2AnimInstance::AnalyzeLandClip()
{
	const UAnimSequence* S = ClipSeq(int32(EWHHeroV2Clip::LandHero));
	const USkeleton* Sk = S ? S->GetSkeleton() : nullptr;
	if (!Sk) return;
	const FReferenceSkeleton& RS = Sk->GetReferenceSkeleton();
	const int32 Ip = RS.FindBoneIndex(FName(TEXT("pelvis"))), Il = RS.FindBoneIndex(FName(TEXT("left_foot"))), Ir = RS.FindBoneIndex(FName(TEXT("right_foot")));
	if (Ip == INDEX_NONE || Il == INDEX_NONE || Ir == INDEX_NONE) return;
	auto CS = [S, &RS](int32 I, double T) -> FVector
	{
		FTransform X = FTransform::Identity;
		const FAnimExtractContext Ctx(T, false, {}, false);
		while (I != INDEX_NONE)
		{
			FTransform L = RS.GetRefBonePose()[I];   // (a bone without a track keeps its reference transform)
			S->GetBoneTransform(L, FSkeletonPoseBoneIndex(I), Ctx, false);
			X = X * L;
			I = RS.GetParentIndex(I);
		}
		return X.GetLocation();
	};
	const double Len = FMath::Min(double(S->GetPlayLength()), 1.2);
	TArray<double> H;
	for (double T = 0.0; T <= Len + 1e-6; T += 1.0 / 60.0)
		H.Add(FVector::DotProduct(CS(Ip, T) - (FVector::DotProduct(CS(Il, T), Ref.Up) < FVector::DotProduct(CS(Ir, T), Ref.Up) ? CS(Il, T) : CS(Ir, T)), Ref.Up));
	double Plateau = 0.0; int32 NP = 0;
	for (int32 K = 0; K < H.Num(); ++K) { const double T = K / 60.0; if (T >= 0.7 && T <= 0.9) { Plateau += H[K]; ++NP; } }
	Plateau = NP ? Plateau / NP : 0.0;
	double FeetT = -1.0, ImpT = -1.0;
	for (int32 K = 0; K < H.Num(); ++K)
	{
		const double T = K / 60.0;
		if (T < LandDiveHoldT) continue;
		if (FeetT < 0.0 && H[K] >= 0.5 * Plateau) FeetT = T;
		if (FeetT >= 0.0 && ImpT < 0.0 && H[K] >= 0.92 * Plateau) { ImpT = T; break; }
	}
	const bool bOk = Plateau > 0.12 * Ref.HeightUnits && FeetT > LandDiveHoldT + 0.05 && ImpT > FeetT && ImpT <= 0.8;
	if (bOk) { LandFeetT = float(FeetT); LandImpactT = float(ImpT); }
	UE_LOG(LogWebHomage, Display, TEXT("WH_HEROV2 land clip: kneel plateau %.1f units, feet-first t=%.3f impact t=%.3f -> %s (LandFeetT %.3f LandImpactT %.3f)"),
		Plateau, FeetT, ImpT, bOk ? TEXT("used") : TEXT("out of range, tunables kept"), LandFeetT, LandImpactT);

	// r7 (critic r6 #6): (a) the kneel's end -- the last frame before the stand-up (pelvis over the lower foot > 1.1 x the plateau); the
	// airborne landing hold keeps the clip there. Offline FK of hero_land.glb: kneel + fist down 0.53 - 2.13 s, stand-up from 2.2 s.
	if (bOk)
	{
		const double Full = double(S->GetPlayLength());
		double EndT = -1.0;
		for (double T = 0.9; T <= Full + 1e-6; T += 1.0 / 30.0)
		{
			const FVector P = CS(Ip, T), L = CS(Il, T), R = CS(Ir, T);
			const double Hk = FVector::DotProduct(P - (FVector::DotProduct(L, Ref.Up) < FVector::DotProduct(R, Ref.Up) ? L : R), Ref.Up);
			if (Hk > 1.1 * Plateau) { EndT = T - 1.0 / 30.0; break; }
		}
		if (EndT > double(LandImpactT) + 0.4) LandKneelEndT = float(EndT);
		else if (EndT < 0.0) LandKneelEndT = FMath::Max(LandKneelEndT, float(Full) - 0.05f);   // (no stand-up in the clip)
	}
	// (b) the dive's head line: elevation of feet -> head over the mesh's forward (deg; head-down -90, head-forward 0, head-up +90) from the
	// held dive frame to feet-first. Offline: -79 deg at 0.20 s, -35 at 0.367, -13 at 0.40, +8 at 0.433 -- the flip turns the head forward
	// through the horizon, so a fly line diving gamma deg is matched by the first frame at -gamma (FastLinePredict / LineDiveStartT).
	LineDiveT.Reset(); LineDiveElev.Reset();
	const int32 Ih = RS.FindBoneIndex(FName(TEXT("head")));
	if (Ih != INDEX_NONE)
	{
		for (double T = double(LandDiveHoldT); T <= double(LandFeetT) + 1e-6; T += 1.0 / 60.0)
		{
			const FVector Ax = WHHeroV2Detail::HV2ClipBodyAxis(S, RS, Ih, Il, Ir, T);
			const float E = FMath::RadiansToDegrees(float(FMath::Atan2(FVector::DotProduct(Ax, Ref.Up), FVector::DotProduct(Ax, Ref.Fwd))));
			if (LineDiveElev.Num() && E < LineDiveElev.Last()) break;   // (monotonic part only)
			LineDiveT.Add(float(T)); LineDiveElev.Add(E);
		}
	}
	UE_LOG(LogWebHomage, Display, TEXT("WH_HEROV2 land clip r7: kneel held to t=%.2f, dive head line %.0f deg (t=%.2f) .. %.0f deg (t=%.2f), %d samples"),
		LandKneelEndT, LineDiveElev.Num() ? LineDiveElev[0] : 0.f, LineDiveT.Num() ? LineDiveT[0] : 0.f,
		LineDiveElev.Num() ? LineDiveElev.Last() : 0.f, LineDiveT.Num() ? LineDiveT.Last() : 0.f, LineDiveT.Num());
}

// r7 (critic r6 #4, fl04 one-frame pop at the boom): AS_BoostLaunch's burst span from its own bones -- body extension (feet -> head) is the
// coil's minimum before BoostBurstT and the stretched maximum after it. BoostCoilEndT = last frame <= BoostBurstT + 0.02 within 10 % of the
// coil, BoostBurstEndT = first frame after it at 95 % of the stretch; BurstCurve = cumulative joint travel over that span (120 Hz).
void UWHHeroV2AnimInstance::AnalyzeBoostClip()
{
	BurstCurveT.Reset(); BurstCurveF.Reset();
	const UAnimSequence* S = ClipSeq(int32(EWHHeroV2Clip::BoostLaunch));
	if (!S || ResolveClip(EWHHeroV2Clip::BoostLaunch) != int32(EWHHeroV2Clip::BoostLaunch)) return;
	const USkeleton* Sk = S->GetSkeleton();
	if (!Sk) return;
	const FReferenceSkeleton& RS = Sk->GetReferenceSkeleton();
	const int32 Ih = RS.FindBoneIndex(FName(TEXT("head"))), Il = RS.FindBoneIndex(FName(TEXT("left_foot"))), Ir = RS.FindBoneIndex(FName(TEXT("right_foot")));
	if (Ih == INDEX_NONE || Il == INDEX_NONE || Ir == INDEX_NONE) return;
	auto Ext = [S, &RS, Ih, Il, Ir](double T) { return WHHeroV2Detail::HV2ClipBodyAxis(S, RS, Ih, Il, Ir, T).Size(); };
	const double Len = double(S->GetPlayLength()), B = double(BoostBurstT), End = FMath::Min(Len, B + 0.4);
	double Coil = TNumericLimits<double>::Max(), Str = 0.0;
	for (double T = 0.1; T <= End + 1e-6; T += 1.0 / 120.0)
	{
		const double E = Ext(T);
		if (T <= B) Coil = FMath::Min(Coil, E); else Str = FMath::Max(Str, E);
	}
	double CoilEnd = -1.0, BurstEnd = -1.0;
	const bool bRange = Coil < TNumericLimits<double>::Max() && Str - Coil > 0.15 * Ref.HeightUnits;
	if (bRange)
	{
		for (double T = 0.1; T <= B + 0.02 + 1e-6; T += 1.0 / 120.0) if (Ext(T) <= Coil + 0.1 * (Str - Coil)) CoilEnd = T;
		for (double T = FMath::Max(CoilEnd, 0.1); CoilEnd > 0.0 && T <= End + 1e-6; T += 1.0 / 120.0) if (Ext(T) >= Coil + 0.95 * (Str - Coil)) { BurstEnd = T; break; }
	}
	const bool bOk = bRange && CoilEnd > 0.1 && BurstEnd > CoilEnd + 0.01 && BurstEnd <= B + 0.25;
	if (bOk)
	{ // the spread is uniform in joint travel (arc length of head, pelvis, feet, knees, elbows, knuckles): offline, 6 steps change a chase
	  // view's bbox aspect by <= 18 % per frame (r6: one 30 fps key, upper arms ~105 deg in one frame); uniform body extension left 51 % in
	  // the last step (the arms swing forward last)
		BoostCoilEndT = float(CoilEnd); BoostBurstEndT = float(BurstEnd);
		static const TCHAR* JN[] = { TEXT("head"), TEXT("pelvis"), TEXT("left_foot"), TEXT("right_foot"), TEXT("left_knee"), TEXT("right_knee"),
			TEXT("left_elbow"), TEXT("right_elbow"), TEXT("left_middle1"), TEXT("right_middle1") };
		TArray<int32> Ji;
		for (const TCHAR* N : JN) { const int32 I = RS.FindBoneIndex(FName(N)); if (I != INDEX_NONE) Ji.Add(I); }
		auto Joints = [S, &RS, &Ji](double T, TArray<FVector>& Out) { Out.Reset(); for (const int32 I : Ji) Out.Add(WHHeroV2Detail::HV2ClipCS(S, RS, I, T).GetLocation()); };
		TArray<FVector> Prev, Cur;
		double Acc = 0.0;
		TArray<double> Cum;
		for (double T = CoilEnd; ; T = FMath::Min(T + 1.0 / 120.0, BurstEnd))
		{
			Joints(T, Cur);
			if (Prev.Num() == Cur.Num()) for (int32 J = 0; J < Cur.Num(); ++J) Acc += (Cur[J] - Prev[J]).Size();
			BurstCurveT.Add(float(T)); Cum.Add(Acc);
			Prev = Cur;
			if (T >= BurstEnd - 1e-9) break;
		}
		if (Acc > 1e-6) { for (const double C : Cum) BurstCurveF.Add(float(C / Acc)); }
		else { BurstCurveT.Reset(); }   // (no joint motion: plain time lerp)
	}
	UE_LOG(LogWebHomage, Display, TEXT("WH_HEROV2 boost clip: extension coil %.1f stretched %.1f units, coil end t=%.3f burst end t=%.3f -> %s (BoostCoilEndT %.3f BoostBurstEndT %.3f, spread over %.2f s)"),
		bRange ? Coil : 0.0, Str, CoilEnd, BurstEnd, bOk ? TEXT("used") : TEXT("out of range, tunables kept"), BoostCoilEndT, BoostBurstEndT, BoostBurstBlendS);
}

// r7 (critic r6 #3): AS_Hover's own motion for the procedural layer -- the phase of the head's rise at HoverBobCycles per loop (DFT bin), so
// the added root bob peaks with the clip's lagging limbs; the clip-mean local rotation of spine2 / spine3 / the collars (the breathing is
// the clip's deviation from it, extrapolated by HoverBreathGain in the proxy).
void UWHHeroV2AnimInstance::AnalyzeHoverClip()
{
	static const TCHAR* Names[FWHHeroV2Frame::NumBreath] = { TEXT("spine2"), TEXT("spine3"), TEXT("left_collar"), TEXT("right_collar") };
	for (int32 K = 0; K < FWHHeroV2Frame::NumBreath; ++K) { Frame.BreathBone[K] = NAME_None; Frame.BreathAvg[K] = FQuat::Identity; }
	HoverBobPhase = 0.f;
	const UAnimSequence* S = ClipSeq(int32(EWHHeroV2Clip::Hover));
	const USkeleton* Sk = S ? S->GetSkeleton() : nullptr;
	if (!Sk) return;
	const FReferenceSkeleton& RS = Sk->GetReferenceSkeleton();
	const double Len = FMath::Max(double(S->GetPlayLength()), 0.1);
	const int32 N = FMath::Clamp(int32(Len * 30.0), 8, 600);
	const int32 Ih = RS.FindBoneIndex(FName(TEXT("head")));
	if (Ih != INDEX_NONE)
	{
		double Re = 0.0, Im = 0.0;
		const double W = 2.0 * UE_DOUBLE_PI * double(HoverBobCycles) / Len;
		for (int32 I = 0; I < N; ++I)
		{
			const double T = Len * I / N;
			const double H = FVector::DotProduct(WHHeroV2Detail::HV2ClipCS(S, RS, Ih, T).GetLocation(), Ref.Up);
			Re += H * FMath::Cos(W * T); Im += H * FMath::Sin(W * T);
		}
		HoverBobPhase = float(FMath::Atan2(Im, Re));   // head height ~ cos(W t - phase)
	}
	int32 NB = 0;
	for (int32 K = 0; K < FWHHeroV2Frame::NumBreath; ++K)
	{
		const int32 Ib = RS.FindBoneIndex(FName(Names[K]));
		if (Ib == INDEX_NONE) continue;
		FVector4 Sum(0.0, 0.0, 0.0, 0.0);
		FQuat First = FQuat::Identity;
		for (int32 I = 0; I < N; ++I)
		{
			FTransform L = RS.GetRefBonePose()[Ib];
			S->GetBoneTransform(L, FSkeletonPoseBoneIndex(Ib), FAnimExtractContext(Len * I / N, false, {}, true), false);
			FQuat Q = L.GetRotation().GetNormalized();
			if (I == 0) First = Q;
			if ((Q | First) < 0.f) Q = -Q;   // one hemisphere
			Sum += FVector4(Q.X, Q.Y, Q.Z, Q.W);
		}
		FQuat Avg(Sum.X, Sum.Y, Sum.Z, Sum.W);
		if (Avg.SizeSquared() < 1e-8) continue;
		Frame.BreathBone[K] = FName(Names[K]);
		Frame.BreathAvg[K] = Avg.GetNormalized();
		++NB;
	}
	UE_LOG(LogWebHomage, Display, TEXT("WH_HEROV2 hover clip: bob phase %.2f rad at %.1f cycles / %.2f s, %d breathing bones (bob %.1f cm, breathing x%.2f)"),
		HoverBobPhase, HoverBobCycles, Len, NB, HoverBobCm, HoverBreathGain);
}

// r7: AS_BoostLaunch time at burst progress U -- uniform steps of joint travel (BurstCurve) between the coil end and the stretch
float UWHHeroV2AnimInstance::BurstClipT(float U) const
{
	U = FMath::Clamp(U, 0.f, 1.f);
	const bool bCurve = BurstCurveT.Num() > 1 && FMath::IsNearlyEqual(BurstCurveT[0], BoostCoilEndT, 1e-3f) && FMath::IsNearlyEqual(BurstCurveT.Last(), BoostBurstEndT, 1e-3f);
	if (!bCurve) return FMath::Lerp(BoostCoilEndT, BoostBurstEndT, U);   // (no curve, or the span was tuned)
	for (int32 I = 1; I < BurstCurveF.Num(); ++I)
	{
		if (BurstCurveF[I] < U) continue;
		const float D = BurstCurveF[I] - BurstCurveF[I - 1];
		const float K = D > 1e-5f ? (U - BurstCurveF[I - 1]) / D : 1.f;
		return FMath::Lerp(BurstCurveT[I - 1], BurstCurveT[I], FMath::Clamp(K, 0.f, 1.f));
	}
	return BoostBurstEndT;
}

// r7: first AS_LandHero frame (held dive .. feet-first) whose head line is at or above GammaDeg below the horizon
float UWHHeroV2AnimInstance::LineDiveStartT(float GammaDeg) const
{
	const float Lo = LandDiveHoldT, Hi = FMath::Max(LandDiveHoldT, LandFeetT - 0.03f);
	if (LineDiveT.Num() < 2) return Lo;
	const float Want = -FMath::Clamp(GammaDeg, 0.f, 90.f);
	if (LineDiveElev[0] >= Want) return Lo;
	for (int32 I = 1; I < LineDiveT.Num(); ++I)
	{
		if (LineDiveElev[I] < Want) continue;
		const float D = LineDiveElev[I] - LineDiveElev[I - 1];
		const float K = D > 1e-4f ? (Want - LineDiveElev[I - 1]) / D : 1.f;
		return FMath::Clamp(FMath::Lerp(LineDiveT[I - 1], LineDiveT[I], FMath::Clamp(K, 0.f, 1.f)), Lo, Hi);
	}
	return Hi;
}

// r7 (critic r6 #6): a fly / boost / dash line that will meet the floor at the hero-landing descent speed -- the flight lands it as a hero
// landing when the descent at contact >= HeroLandMinSpeed (WHFlightComponent MoveAndCollide / FloorSkim). Entered FastLandLeadT before the
// predicted contact, kept (hysteresis) while still descending at 0.85 x and within FastLandLeadT + 0.25 s.
bool UWHHeroV2AnimInstance::FastLinePredict(const FWebTravAnim& A, float Vz, bool bStay, float& OutGammaDeg) const
{
	if (A.Mode != EWebTravMode::Air || !A.Flight.bActive || FastLandLeadT <= 0.f) return false;
	const float Need = HeroLandMinV * (bStay ? 0.85f : FMath::Max(1.f, FastLandVzK));
	if (-Vz < Need) return false;
	const float Tti = TimeToImpact(A);
	if (Tti > (bStay ? FastLandLeadT + 0.25f : FastLandLeadT)) return false;
	const float Vh = float(FVector2D(A.Velocity.X, A.Velocity.Y).Size() / 100.0);
	OutGammaDeg = FMath::RadiansToDegrees(FMath::Atan2(-Vz, FMath::Max(Vh, 1e-3f)));
	return true;
}

float UWHHeroV2AnimInstance::TakeoffPlantK(float T) const
{
	if (T < 0.f) return 0.f;
	if (T < TakeoffPlantT) return 1.f;
	return 1.f - WHHeroV2Detail::HV2Smooth(T, TakeoffPlantT, TakeoffPlantT + FMath::Max(0.01f, TakeoffCatchT));
}

float UWHHeroV2AnimInstance::DiveFlipK(float T, float T0) const
{
	// r7: a dive entered past the held frame (fast fly line, critic r6 #6) ramps from its own entry frame
	const float A = FMath::Min(FMath::Max(LandDiveHoldT, T0), LandFeetT - 0.01f);
	return WHHeroV2Detail::HV2Smooth(T, A, FMath::Max(A + 0.01f, LandFeetT));
}

UAnimSequence* UWHHeroV2AnimInstance::ClipSeq(int32 C) const
{
	return Clips.IsValidIndex(C) ? Clips[C].Get() : nullptr;
}

float UWHHeroV2AnimInstance::ClipLen(int32 C) const
{
	const UAnimSequence* S = ClipSeq(C);
	return S ? FMath::Max(S->GetPlayLength(), 1e-3f) : 1.f;
}

// a missing clip falls back to the nearest one that exists (the hover is the last resort; none = reference pose)
int32 UWHHeroV2AnimInstance::ResolveClip(EWHHeroV2Clip Want) const
{
	EWHHeroV2Clip C = Want;
	for (int32 Guard = 0; Guard < 6; ++Guard)
	{
		if (ClipSeq(int32(C))) return int32(C);
		switch (C)
		{
		case EWHHeroV2Clip::BoostHold: case EWHHeroV2Clip::BoostLaunch: case EWHHeroV2Clip::FlyingFistKick: C = EWHHeroV2Clip::Fly; break;
		case EWHHeroV2Clip::Takeoff: C = EWHHeroV2Clip::LaunchUp; break;
		case EWHHeroV2Clip::Hover: return -1;
		default: C = EWHHeroV2Clip::Hover; break;
		}
	}
	return -1;
}

// per-transition crossfade times (owner request: 0.15-0.3 s, tunable)
float UWHHeroV2AnimInstance::BlendTime(EWHHeroV2State From, EWHHeroV2State To) const
{
	using S = EWHHeroV2State;
	if (From == S::None) return 0.f;
	if (To == S::Takeoff) return BlendToTakeoff;
	if (From == S::Takeoff) return BlendTakeoffOut;
	if (To == S::BoostLaunch) return BlendToBoostLaunch;
	if (From == S::BoostLaunch) return BlendBoostLaunchOut;
	if (To == S::Brake) return BlendToBrake;
	if (From == S::Brake && (To == S::Hover || To == S::LaunchUp)) return BlendBrakeToHover;
	if (To == S::LandHero) return BlendToLandDive;
	if (From == S::LandHero && To == S::GroundIdle) return BlendLandToIdle;
	if (From == S::LandHero && (To == S::Hover || To == S::LaunchUp)) return BlendLandToHover;   // owner request 2026-10-16: hold -> float
	// r5 (critic r4 fl09: dash -> hover swung the body ~90 deg in 0.15 s): the dash <-> an upright clip blends over BlendDashUpright
	if (To == S::Dash || From == S::Dash)
		return WHHeroV2Detail::HV2IsFlyType(To == S::Dash ? From : To) ? BlendDash : BlendDashUpright;
	if ((From == S::Hover && To == S::LaunchUp) || (From == S::LaunchUp && To == S::Hover)) return BlendHoverLaunchUp;
	if (WHHeroV2Detail::HV2IsFlyType(From) != WHHeroV2Detail::HV2IsFlyType(To)) return BlendFlyHover;
	return BlendDefault;
}

void UWHHeroV2AnimInstance::StartTrack(EWHHeroV2State S, float StartT, float Blend)
{
	using C = EWHHeroV2Clip;
	FTrack Tr;
	Tr.State = S;
	C Want = C::Hover;
	switch (S)
	{
	case EWHHeroV2State::GroundIdle: Want = C::GroundIdle; break;
	case EWHHeroV2State::Takeoff: Want = C::Takeoff; Tr.Rate = TakeoffRate; break;     // r5: crouch -> push-off compressed (critic r4 #5)
	case EWHHeroV2State::Hover: Want = C::Hover; break;
	case EWHHeroV2State::LaunchUp: Want = C::LaunchUp; break;
	case EWHHeroV2State::Fly: Want = C::Fly; break;
	// r5 (critic r4 #1, fl09 1.55 s spread-eagled dash): the dash is AS_BoostHold (the boost's parallel fists on the x1.6 flight loop)
	case EWHHeroV2State::Dash: Want = C::BoostHold; Tr.Rate = DashRate; break;
	case EWHHeroV2State::BoostLaunch: Want = C::BoostLaunch; BurstS = -1.f; break;   // r7: a fresh burst
	case EWHHeroV2State::BoostHold: Want = C::BoostHold; break;
	case EWHHeroV2State::Brake: Want = C::Brake; Tr.Rate = BrakeClipRate; break;
	case EWHHeroV2State::LandHero: Want = C::LandHero; break;
	case EWHHeroV2State::Breach: Want = C::BoostHold; break;                           // through a building: the super line (he is hidden inside)
	default: break;
	}
	Tr.Clip = ResolveClip(Want);
	Tr.bLoop = Tr.Clip >= 0 && IsLoopClip(Tr.Clip);
	if (WHHeroV2Detail::HV2IsFlyType(S)) { Tr.UpClip = ClipSeq(int32(C::LaunchUp)) ? int32(C::LaunchUp) : -1; Tr.UpW = UpWNow; }
	Tr.T = Tr.Clip >= 0 ? FMath::Clamp(StartT, 0.f, ClipLen(Tr.Clip)) : 0.f;
	Tr.W = Tracks.Num() == 0 || Blend <= 1e-3f ? 1.f : 0.f;
	if (Tr.W >= 1.f) Tracks.Reset();
	BlendDur = FMath::Max(Blend, 1e-3f);
	Tracks.Add(Tr);
	// at most four tracks: the oldest fading ones go first (weights renormalised in AdvanceTracks)
	while (Tracks.Num() > 4) Tracks.RemoveAt(0);
	StateT = 0.f;
}

void UWHHeroV2AnimInstance::AdvanceTracks(float Dt)
{
	if (Tracks.Num() == 0) return;
	// clocks: loops wrap, one-shots clamp and report completion (the newest track's special timing is applied by the caller first)
	for (int32 I = 0; I < Tracks.Num(); ++I)
	{
		FTrack& Tr = Tracks[I];
		if (Tr.Clip < 0) continue;
		const float Len = ClipLen(Tr.Clip);
		if (!(I == Tracks.Num() - 1 && (Tr.State == EWHHeroV2State::LandHero && Tr.bDive))) Tr.T += Dt * Tr.Rate;
		if (Tr.bLoop) { Tr.T = FMath::Fmod(Tr.T, Len); if (Tr.T < 0.f) Tr.T += Len; }
		else if (Tr.T >= Len - 1e-3f) { Tr.T = Len; Tr.bDone = true; }
		if (Tr.UpClip >= 0) { const float UL = ClipLen(Tr.UpClip); Tr.UpT = FMath::Fmod(Tr.UpT + Dt, UL); }
	}
	// weights: the newest fades in over BlendDur, the older ones share the rest in proportion
	FTrack& New = Tracks.Last();
	New.W = FMath::Min(1.f, New.W + Dt / BlendDur);
	float OldSum = 0.f;
	for (int32 I = 0; I + 1 < Tracks.Num(); ++I) OldSum += Tracks[I].W;
	const float Rest = 1.f - New.W;
	for (int32 I = 0; I + 1 < Tracks.Num(); ++I) Tracks[I].W = OldSum > 1e-6f ? Tracks[I].W * Rest / OldSum : 0.f;
	for (int32 I = Tracks.Num() - 2; I >= 0; --I) if (Tracks[I].W < 0.005f) Tracks.RemoveAt(I);
	if (Tracks.Num() == 1) Tracks[0].W = 1.f;
}

// seconds until the dive meets the floor under the hero (the traversal ground index the flight lands on); 9 = unknown / not falling
float UWHHeroV2AnimInstance::TimeToImpact(const FWebTravAnim& A) const
{
	const AWebTravCharacter* Ch = Cast<AWebTravCharacter>(GetOwningActor());
	const UWebTraversalComponent* Tr = Ch ? Ch->GetTraversal() : nullptr;
	if (!Tr) return 9.f;
	const FVector P = Tr->PosM();
	const double FeetZ = P.Z - UWebTraversalComponent::H;
	double G = Tr->TravWorld.GroundHeight(P.X, P.Y, FeetZ + 0.05);
	// owner request 2026-10-16 (roof the ground index did not know): with the flight float, also the surface the flight sweep lands on
	if (bFloat && FlightSurfZ > -999.0 && FlightSurfZ <= FeetZ + 0.05) G = FMath::Max(G, FlightSurfZ);
	const double Vz = -double(A.Velocity.Z) / 100.0;
	if (G <= -999.0 || Vz < 3.0) return 9.f;
	const double D = FMath::Max(0.0, FeetZ - G);
	// r5 (critic r4 #3): the slam / double-tap dive still accelerates -- d = v t + a t^2 / 2 with the eased fall acceleration
	const double Acc = FMath::Clamp(double(FallAccel), 0.0, 400.0);
	if (Acc > 0.5) return float((FMath::Sqrt(Vz * Vz + 2.0 * Acc * D) - Vz) / Acc);
	return float(D / Vz);
}

// owner brief state -> clip map (see the notes for the table); sticky one-shots finish unless a new action takes over
EWHHeroV2State UWHHeroV2AnimInstance::PickState(const FWebTravAnim& A, float Vz, float& OutUpTarget)
{
	using namespace WHHeroV2Detail;
	using S = EWHHeroV2State;
	const S Cur = CurrentState();
	const FTrack* CurTr = Tracks.Num() ? &Tracks.Last() : nullptr;
	const bool bCurDone = !CurTr || CurTr->bDone;
	const FWebTravAnimFlight& F = A.Flight;
	OutUpTarget = 0.f;
	bLineWant = false;   // r7 (set below for a predicted fly-line hero landing)
	{ // fly-type line pitched up past LaunchUpPitchDeg blends toward AS_LaunchUp (owner brief: "e.g. > 60 deg")
		const float Vh = float(FVector2D(A.Velocity.X, A.Velocity.Y).Size() / 100.0);
		if (FMath::Sqrt(Vh * Vh + Vz * Vz) > 3.f)
		{
			const float GammaDeg = FMath::RadiansToDegrees(FMath::Atan2(Vz, Vh));
			OutUpTarget = HV2Smooth(GammaDeg, LaunchUpPitchDeg - LaunchUpBandDeg, LaunchUpPitchDeg + LaunchUpBandDeg);
		}
	}
	if (A.Mode != EWebTravMode::Air && bFloat)
	{ // owner request 2026-10-16 ("always floating"): never AS_GroundIdle in flight float mode (the flight turns any ground state into the
	  // float before the anim reads it; this only covers a stray frame)
		return (Cur == S::LandHero && !bCurDone) ? S::LandHero : S::Hover;
	}
	if (A.Mode != EWebTravMode::Air)
	{
		// the hero landing plays out (stand-up) while he stays put; walking or the clip's end hands over to the idle, once per landing
		// (bLandSpent: the traversal sub may stay "landHero" after the clip has finished)
		if (A.Sub != HV2NLandHero && Cur != S::LandHero) bLandSpent = false;
		if (Cur == S::LandHero && (bCurDone || (bLandImpact && StateT > 0.3f && A.Speed > 0.5f))) bLandSpent = true;
		if (!bLandSpent && (A.Sub == HV2NLandHero || Cur == S::LandHero)) return S::LandHero;
		return S::GroundIdle;
	}
	bLandSpent = false;
	// owner request 2026-10-16: the hero landing is an airborne hold (Air + sub landHero, velocity zero) -> AS_LandHero's impact part until
	// the flight releases the hold into the hover float
	if (A.Sub == HV2NLandHero) return S::LandHero;
	S Want = S::Hover;
	if (A.Sub == HV2NTakeoff) Want = S::Takeoff;
	else if (A.Sub == HV2NSlam) Want = S::LandHero;
	else if (A.Sub == HV2NBreach) Want = S::Breach;
	else if (A.Sub == HV2NDash) Want = S::Dash;
	else if (A.Sub == HV2NFly) Want = S::Fly;
	else if (A.Sub == HV2NBoost) Want = ((Cur == S::BoostLaunch && !bCurDone) || (Cur != S::BoostLaunch && F.LaunchK > 0.9f)) ? S::BoostLaunch : S::BoostHold;
	else if (A.Sub == HV2NBrake)
	{
		if (F.ChargeK > 0.f) Want = S::BoostLaunch;   // owner feedback #1: the super charge runs under sub "brake"
		else if (Cur == S::Brake) Want = S::Brake;
		else if ((Cur == S::Hover || Cur == S::LaunchUp || Cur == S::Takeoff || Cur == S::GroundIdle || Cur == S::None) && PrevSpeed < BrakeMinSpeed) Want = S::Hover;
		else Want = S::Brake;
	}
	// r6 (critic r5 #1, fl17 "he lies prone on top of the load like a surfboard in the carry-dive"): while a load is held overhead the body
	// stays upright -- the path-aligned / dive clips (fly, boost, dash, breach, boost launch, slam dive) give way to the hover (feet down, no
	// path pitch: PitchFreedom 0); the arms keep AS_LaunchUp's fists overhead (UpdateCarry runs before this pick)
	if (bCarry && (HV2IsFlyType(Want) || Want == S::BoostLaunch || Want == S::LandHero)) Want = S::Hover;
	// r7 (critic r6 #6, fl12 2.75-2.80 "spread-eagle splat"): a fly / boost / dash line about to meet the floor at the hero-landing descent
	// speed turns into AS_LandHero's dive before the contact (the flight lands it as a hero landing; r6 crossfaded the 36 deg-pitched boost
	// line into the kneel over 0.15 s at the contact frame)
	if (!bCarry && (Want == S::Fly || Want == S::BoostHold || Want == S::Dash))
	{
		const bool bStay = Cur == S::LandHero && CurTr && CurTr->bDive && CurTr->bLine;
		float Gamma = 0.f;
		if (FastLinePredict(A, Vz, bStay, Gamma)) { Want = S::LandHero; bLineWant = true; LineGammaDeg = Gamma; }
	}
	if (Want == S::Hover)
	{ // hover climbing (Space held) = the launch-straight-up clip, with hysteresis
		const float On = HoverClimbVz, Off = HoverClimbVz * 0.5f;
		if (F.Climb > 0.5f && (Vz > On || (Cur == S::LaunchUp && Vz > Off))) Want = S::LaunchUp;
	}
	// sticky one-shots: the takeoff and the brake finish into the hover / launch-up they hand off to
	if ((Want == S::Hover || Want == S::LaunchUp) && !bCurDone && (Cur == S::Takeoff || Cur == S::Brake)) return Cur;
	if ((Want == S::Hover || Want == S::LaunchUp) && Cur == S::Takeoff && bCurDone)
		return Vz > HoverClimbVz ? S::LaunchUp : S::Hover;
	// the boost launch plays through the burst into the super line
	// (r7: from the coil end -- the burst is spread from there, critic r6 #4)
	if (Want == S::Fly && Cur == S::BoostLaunch && !bCurDone && F.ChargeK <= 0.f && CurTr && CurTr->T >= BoostCoilEndT - 0.03f) return S::BoostLaunch;
	return Want;
}

void UWHHeroV2AnimInstance::LogState(const FWebTravAnim& A)
{
	const EWHHeroV2State Cur = CurrentState();
	if (Cur == LastLogged && LogPending == EWHHeroV2State::None) return;
	const double Now = FPlatformTime::Seconds();
	if (LastLogReal >= 0.0 && Now - LastLogReal < double(LogMinInterval))
	{ // rate limit: remember it and print the latest state when the interval allows
		if (Cur != LastLogged) { LogPending = Cur; ++LogSuppressed; }
		return;
	}
	LogPending = EWHHeroV2State::None;
	if (Cur == LastLogged) return;
	const UWorld* W = GetWorld();
	UE_LOG(LogWebHomage, Display, TEXT("WH_HEROV2 state %s clip %s t=%.3f clipT=%.2f blend=%.2f from=%s mode=%d sub=%s speed=%.1f%s"),
		StateName(Cur), CurrentClipName(), W ? W->GetTimeSeconds() : 0.0, CurrentClipTime(), BlendDur, StateName(LastLogged),
		int32(A.Mode), *A.Sub.ToString(), A.Speed, LogSuppressed ? *FString::Printf(TEXT(" (+%d suppressed)"), LogSuppressed) : TEXT(""));
	LastLogged = Cur; LastLogReal = Now; LogSuppressed = 0;
}

void UWHHeroV2AnimInstance::NativeUpdateAnimation(float DeltaSeconds)
{
	Super::NativeUpdateAnimation(DeltaSeconds);
	using namespace WHHeroV2Detail;
	using S = EWHHeroV2State;
	const float Dt = FMath::Clamp(DeltaSeconds, 0.f, 0.1f);
	const AWebTravCharacter* Ch = Cast<AWebTravCharacter>(GetOwningActor());
	const UWebTraversalComponent* Trav = Ch ? Ch->GetTraversal() : nullptr;
	const FWebTravAnim A = Trav ? Trav->Anim : FWebTravAnim();
	const float Vz = float(A.Velocity.Z / 100.0);
	// owner request 2026-10-16 ("always floating"): the flight's float mode / surface under him / touch counter
	const UWHFlightComponent* FlC = Trav ? Trav->Flight.Get() : nullptr;
	bFloat = FlC && FlC->IsFloatOn() && A.Flight.bActive;
	FlightSurfZ = bFloat ? FlC->SurfaceBelowZ() : -1000.0;
	HeroLandMinV = FlC ? FMath::Max(1.f, FlC->HeroLandMinSpeed) : 30.f;   // r7: the flight's hero-landing descent speed

	// r5: eased downward acceleration of the fall (time to impact of an accelerating dive)
	if (A.Mode == EWebTravMode::Air && Dt > 1e-4f)
		FallAccel += (FMath::Clamp((PrevVz - Vz) / Dt, 0.f, 400.f) - FallAccel) * (1.f - FMath::Exp(-8.f * Dt));
	else FallAccel = 0.f;

	// ---- r5 rescue carry (critic r4 #6): AS_LaunchUp's arms overhead while the director reports a carried load
	// (r6, critic r5 #1: updated before the state pick, which keeps a carrying body upright)
	UpdateCarry(A, Dt);

	float UpTarget = 0.f;
	const S Cur = CurrentState();
	S Want = PickState(A, Vz, UpTarget);
	StateT += Dt;

	// ---- transitions
	if (Want == S::BoostLaunch && Cur == S::BoostLaunch && A.Flight.ChargeK > 0.f && Tracks.Last().T > BoostBurstEndT)
		StartTrack(S::BoostLaunch, 0.f, BlendToBoostLaunch);   // a fresh charge while the last launch is still showing
	else if (Want != Cur)
	{
		float StartT = 0.f;
		bool bDive = false, bLine = false;
		float Blend = BlendTime(Cur, Want);
		if (Want == S::Takeoff) StartT = TakeoffClipStart;
		else if (Want == S::Brake) StartT = BrakeEnterT;   // r5 (critic r4 #2): upright brake entry, never the clip's side-roll part
		else if (Want == S::LandHero)
		{
			// slam / double-tap dive: the clip starts with the dive (owner request 2026-10-16: the airborne landing hold is the impact)
			bDive = A.Mode == EWebTravMode::Air && A.Sub != HV2NLandHero;
			bLandImpact = !bDive;
			// a hard landing without the dive: just before the contact frame, legs already under him (r5)
			if (!bDive) StartT = FMath::Max(LandFeetT, LandImpactT - 0.04f);
			// r7 (critic r6 #6): a fast fly line -- the dive frame whose head line matches the path (36 deg down: t ~0.37, head forward-down)
			else if (bLineWant)
			{
				bLine = true;
				StartT = LineDiveStartT(LineGammaDeg);
				Blend = BlendToLineDive;
				UE_LOG(LogWebHomage, Display, TEXT("WH_HEROV2 fast line landing: path %.0f deg down at %.0f m/s descent %.0f m/s, %.2f s to the floor -> AS_LandHero dive from t=%.2f"),
					LineGammaDeg, A.Speed, -Vz, TimeToImpact(A), StartT);
			}
		}
		else if (Want == S::BoostLaunch && A.Flight.ChargeK <= 0.f) StartT = BoostCoilEndT;   // a boom without a seen charge (r7: the burst is spread from the coil end)
		// r5 (critic r4 #5 / #8, touchdown "stops in one frame, no knee compression"): a soft landing dips into a knee bend
		if (Want == S::GroundIdle && Cur != S::GroundIdle && Cur != S::LandHero && Cur != S::None)
		{
			DipT = 0.f;
			DipPeakNow = FMath::Clamp(DipPeak + DipPeakPerMps * FMath::Max(0.f, -PrevVz), 0.f, DipMax);
		}
		StartTrack(Want, StartT, Blend);
		Tracks.Last().bDive = bDive;
		Tracks.Last().bLine = bLine;
		Tracks.Last().DiveT0 = bDive ? StartT : 0.f;
		if (!HV2IsFlyType(Want)) UpWNow = 0.f;
	}

	// ---- special timing of the current track
	if (Tracks.Num())
	{
		FTrack& Tr = Tracks.Last();
		if (Tr.State == S::BoostLaunch && A.Flight.ChargeK > 0.f && Tr.Clip == int32(EWHHeroV2Clip::BoostLaunch))
		{ // owner brief: the 0.42 s burst coincides with the boom -- the clip time follows the flight's own charge progress (real-time,
		  // slow-mo proof): ChargeK = smoothstep(SuperT / SuperChargeTime) -> T = BoostBurstT x invsmooth(ChargeK); AdvanceTracks adds Dt
		  // r7 (critic r6 #4): the charge ends on the last coil frame (BoostCoilEndT), not mid-burst (0.42 was 60 % into the 0.400 -> 0.433 jump)
			BurstS = -1.f; Tr.Rate = 1.f;
			Tr.T = FMath::Max(Tr.T, BoostCoilEndT * HV2InvSmooth(A.Flight.ChargeK) - Dt * Tr.Rate);
			Tr.T = FMath::Min(Tr.T, BoostCoilEndT - Dt * Tr.Rate);
		}
		else if (Tr.State == S::BoostLaunch && Tr.Clip == int32(EWHHeroV2Clip::BoostLaunch) && BurstS < 100.f)
		{ // r7 (critic r6 #4, fl04 "upright charge pose at 1.450, full horizontal flight at 1.467"): on the boom the coil -> stretch span is
		  // spread over BoostBurstBlendS in uniform steps of joint travel (>= 4 in-between frames), then the clip runs on at 1x
			if (BurstS < 0.f && Tr.T >= BoostCoilEndT - 0.03f && Tr.T < BoostBurstEndT) BurstS = 0.f;
			if (BurstS >= 0.f)
			{
				BurstS += Dt;
				const float U = FMath::Clamp(BurstS / FMath::Max(0.02f, BoostBurstBlendS), 0.f, 1.f);
				Tr.T = FMath::Max(Tr.T, BurstClipT(U));
				Tr.Rate = U < 1.f ? 0.f : 1.f;
				if (U >= 1.f) BurstS = 1000.f;   // (done: the clip plays on)
			}
		}
		// r7 (critic r6 #6): the airborne hero-landing hold keeps AS_LandHero's knee + fist contact pose (no stand-up before the release)
		if (Tr.State == S::LandHero && !Tr.bDive && bLandImpact && A.Mode == EWebTravMode::Air && A.Sub == HV2NLandHero && Tr.T < LandKneelEndT)
			Tr.T = FMath::Min(Tr.T, LandKneelEndT - Dt * Tr.Rate);
		bool bImpactJump = false;
		if (Tr.State == S::LandHero && Tr.bDive)
		{
			if (A.Mode != EWebTravMode::Air || A.Sub == HV2NLandHero)   // (owner request 2026-10-16: or the airborne landing hold)
			{ // the landing event: the contact frame must be on it -- an impact before the feet-first turn jumps to it with a short blend
				Tr.bDive = false; bLandImpact = true;
				bImpactJump = Tr.T < LandFeetT - 0.05f;
			}
			else
			{ // r5 (critic r4 #3, fl11 head-first until ~3 m then a 180 deg snap in ~2 frames): play into the held dive pose (LandDiveHoldT)
			  // while far; from LandFlipLeadT s before the impact the flip (hold -> LandFeetT) is spread so that he is feet-first
			  // LandFeetLeadT s (>= 8 frames) before the contact; feet-first he creeps on toward the contact frame, reached on the impact
				const float Tti = TimeToImpact(A);
				float T = Tr.T;
				if (Tr.bLine && Tti > LandFlipLeadT && T < LandFeetT)
				{ // r7 (critic r6 #6): a fast fly line's dive frame follows the path angle while far (never backwards)
					const float Vh = float(FVector2D(A.Velocity.X, A.Velocity.Y).Size() / 100.0);
					T = FMath::Max(T, LineDiveStartT(FMath::RadiansToDegrees(FMath::Atan2(-Vz, FMath::Max(Vh, 1e-3f)))));
				}
				// (r7, critic r6 #6: a dive already inside LandFlipLeadT before reaching the held frame goes straight into the timed flip, so a
				// slam / double-tap close to the floor is still feet-first on the contact instead of jumping there)
				else if (T < LandDiveHoldT && Tti > LandFlipLeadT) T = FMath::Min(T + Dt, LandDiveHoldT);
				else if (T < LandFeetT)
				{
					if (Tti <= LandFlipLeadT)
					{
						const float Rate = (LandFeetT - T) / FMath::Max(Tti - LandFeetLeadT, Dt);
						T = FMath::Min(LandFeetT, T + FMath::Clamp(Rate, 1.f, LandFlipMaxRate) * Dt);
					}
				}
				else
				{
					const float Rate = (LandImpactT - 0.02f - T) / FMath::Max(Tti, Dt);
					T = FMath::Min(LandImpactT - 0.02f, T + FMath::Clamp(Rate, 0.f, 1.f) * Dt);
				}
				Tr.T = FMath::Max(Tr.T, T);
			}
		}
		if (bImpactJump)
		{ // (Tr is not used past this point: StartTrack may reallocate Tracks)
			StartTrack(S::LandHero, LandImpactT - 0.02f, BlendLandImpact);
			Tracks.Last().bDive = false;
		}
		FTrack& Top = Tracks.Last();
		if (HV2IsFlyType(Top.State))
		{
			UpWNow = UpWNow + (UpTarget - UpWNow) * (1.f - FMath::Exp(-UpBlendRate * Dt));
			Top.UpW = Top.UpClip >= 0 ? UpWNow : 0.f;
		}
	}
	AdvanceTracks(Dt);
	PrevSpeed = A.Speed;
	PrevVz = Vz;

	// ---- ground lock (grounded clips: feet on the floor) and the pitch freedom for the character
	{
		float Target = 0.f;
		const S Now = CurrentState();
		const FTrack* Top = Tracks.Num() ? &Tracks.Last() : nullptr;
		if (Now == S::GroundIdle) Target = 1.f;
		else if (Now == S::LandHero && bLandImpact) Target = 1.f;
		// r5 (critic r4 #5): planted while the crouch plays, released with the character's catch-up (AWebTravCharacter::HeroV2Frame)
		else if (Now == S::Takeoff) Target = TakeoffPlantK(StateT);
		// r5 (critic r4 #3): through the feet-first turn the feet are brought onto the capsule bottom, so the contact frame meets the floor
		else if (Now == S::LandHero && Top && Top->bDive) Target = FMath::Square(DiveFlipK(Top->T, Top->DiveT0));   // (r7: from the entry frame)
		else if (bFloat && (Now == S::Hover || Now == S::LaunchUp))
		{ // owner request 2026-10-16: the rise out of the airborne landing hold lets the planted feet go with the AS_LandHero track's fade
			for (const FTrack& Tr : Tracks) { if (Tr.State == S::LandHero && !Tr.bDive) Target += Tr.W; }
			Target = FMath::Min(Target, 1.f);
		}
		Frame.GroundW = bRefOk ? Frame.GroundW + (Target - Frame.GroundW) * (1.f - FMath::Exp(-Dt / FMath::Max(0.005f, GroundLockTau))) : 0.f;
		float PF = 0.f;
		for (const FTrack& Tr : Tracks)
		{
			float K = 0.f;
			if (HV2IsFlyType(Tr.State)) K = 1.f - Tr.UpW;
			else if (Tr.State == S::BoostLaunch) K = 1.f;
			// r5: upright once feet-first (critic r4 #3); r7 (critic r6 #6): a fast fly line's dive frame already lies on the path -- no mesh pitch
			else if (Tr.State == S::LandHero && Tr.bDive) K = Tr.bLine ? 0.f : 1.f - DiveFlipK(Tr.T, Tr.DiveT0);
			PF += Tr.W * K;
		}
		PitchFreedomV = FMath::Clamp(PF, 0.f, 1.f);
	}

	// ---- r5 touchdown dip (critic r4 #5): AS_Takeoff's crouch on the non-arm bones, in over DipInT, out over DipOutT
	// owner request 2026-10-16 ("always floating"): a floor touch into the float (WH_FLIGHT float touch) dips the knees the same way; the dip
	// plays in the hover float and fades out fast (never cut) if a fly-type state takes over
	if (bFloat && FlC && FlC->FloatTouchCount() != LastTouchCount)
	{
		LastTouchCount = FlC->FloatTouchCount();
		DipT = 0.f;
		DipPeakNow = FMath::Clamp(DipPeak + DipPeakPerMps * float(FlC->FloatTouchSpeed()), 0.f, DipMax);
	}
	if (CurrentState() == S::GroundIdle) DipT = FMath::Min(DipT + Dt, 99.f);
	else if (bFloat && DipT < 50.f) DipT = FMath::Min(DipT + Dt * ((CurrentState() == S::Hover || CurrentState() == S::LaunchUp) ? 1.f : 4.f), 99.f);
	else DipT = 99.f;
	{
		const float Up = HV2Smooth(DipT, 0.f, FMath::Max(0.01f, DipInT));
		const float Dn = 1.f - HV2Smooth(DipT, DipInT, DipInT + FMath::Max(0.01f, DipOutT));
		Frame.DipW = DipT < 50.f ? DipPeakNow * FMath::Min(Up, Dn) : 0.f;
		Frame.DipSeq = ClipSeq(int32(EWHHeroV2Clip::Takeoff));
		Frame.DipTime = DipPoseT;
		if (!Frame.DipSeq) Frame.DipW = 0.f;
	}

	// ---- r7 (critic r6 #3, fl08 "torso centroid moves 2.0 px over 2.6 s, no bob, no breathing"): procedural hover layer on top of the
	// approved AS_Hover -- a vertical root bob (HoverBobCm at HoverBobCycles per clip loop, phase-locked to the clip's own head rise) and
	// the clip's spine2 / spine3 / collar breathing x HoverBreathGain; weight = the AS_Hover tracks' share, faded out with speed (1 -> 5 m/s),
	// the ground lock (landing hold) and eased (HoverBobTau), so transitions never pop. Visual only: the capsule / camera target stay calm.
	{
		const USkeletalMeshComponent* SMC = GetSkelMeshComponent();
		const double Sc = SMC ? FMath::Max(1e-4, double(SMC->GetComponentScale().X)) : 1.0;   // mesh units -> cm
		float HoverW = 0.f; const FTrack* HT = nullptr;
		for (const FTrack& Tr : Tracks) { if (Tr.State == S::Hover && Tr.Clip == int32(EWHHeroV2Clip::Hover)) { HoverW += Tr.W; HT = &Tr; } }
		const float Target = (A.Mode == EWebTravMode::Air && A.Flight.bActive) ? FMath::Clamp(HoverW, 0.f, 1.f) * (1.f - HV2Smooth(A.Speed, HoverBobSpeedLo, FMath::Max(HoverBobSpeedLo + 0.1f, HoverBobSpeedHi)))
			* (1.f - FMath::Clamp(Frame.GroundW, 0.f, 1.f)) : 0.f;
		BobW += (Target - BobW) * (1.f - FMath::Exp(-Dt / FMath::Max(0.02f, HoverBobTau)));
		Frame.BobShift = 0.f; Frame.BreathK = 0.f; Frame.BreathArmK = 0.f;
		if (BobW > 0.002f && HT && bRefOk)
		{
			const float Ph = 2.f * UE_PI * HoverBobCycles * HT->T / ClipLen(int32(EWHHeroV2Clip::Hover)) - HoverBobPhase;
			Frame.BobShift = float(double(BobW * HoverBobCm * FMath::Cos(Ph)) / Sc);
			Frame.BreathK = BobW * FMath::Max(0.f, HoverBreathGain - 1.f);
			Frame.BreathArmK = Frame.BreathK * (1.f - CarryW);
		}
	}

	// ---- r7 (critic r6 #2, fl17 32.9 s -> "his side merges into the taxi door"): floating still by a street vehicle, the mesh steps clear
	UpdateStandClear(A, FlC, Dt);

	// ---- layers for the proxy (each track: its clip, plus the AS_LaunchUp blend of fly-type tracks)
	Frame.Layers.Reset();
	UAnimSequence* IdleSeq = ClipSeq(int32(EWHHeroV2Clip::GroundIdle));
	UAnimSequence* UpSeq = ClipSeq(int32(EWHHeroV2Clip::LaunchUp));
	for (const FTrack& Tr : Tracks)
	{
		UAnimSequence* Seq = ClipSeq(Tr.Clip);
		if (!Seq || Tr.W <= 0.001f) continue;
		const float Wu = Tr.UpClip >= 0 ? FMath::Clamp(Tr.UpW, 0.f, 1.f) : 0.f;
		// arm overrides: r5 (critic r4 #1 / #5) AS_Takeoff's crouch has the arms straight out sideways -- the idle arms until TakeoffArmsT0,
		// its own arms (swinging up into the leap) from TakeoffArmsT1; r5 (critic r4 #6) the carry's arms overhead on every layer
		UAnimSequence* ArmSeq = nullptr; float ArmT = 0.f, ArmW = 0.f; bool bArmLoop = true, bArmSwing = false;
		if (Tr.State == S::Takeoff && Tr.Clip == int32(EWHHeroV2Clip::Takeoff) && IdleSeq)
		{
			ArmSeq = IdleSeq; ArmT = 0.5f; ArmW = 1.f - HV2Smooth(Tr.T, TakeoffArmsT0, TakeoffArmsT1);
		}
		if (CarryW > 0.001f && UpSeq)
		{
			ArmW = FMath::Max(ArmW, CarryW); ArmSeq = UpSeq; ArmT = FMath::Fmod(CarryArmT, ClipLen(int32(EWHHeroV2Clip::LaunchUp)));
			bArmSwing = true;   // r7 (critic r6 #2): arms up in front, not through a T
		}
		if (ArmW <= 0.001f) ArmSeq = nullptr;
		const bool bBreathL = Tr.State == S::Hover && Tr.Clip == int32(EWHHeroV2Clip::Hover);   // r7: AS_Hover drives the extra breathing
		if (1.f - Wu > 0.001f) Frame.Layers.Add({ Seq, Tr.T, Tr.W * (1.f - Wu), Tr.bLoop, ArmSeq, ArmT, ArmW, bArmLoop, bBreathL, bArmSwing });
		if (Wu > 0.001f) Frame.Layers.Add({ ClipSeq(Tr.UpClip), Tr.UpT, Tr.W * Wu, true, ArmSeq, ArmT, ArmW, bArmLoop, false, bArmSwing });
	}
	Frame.ArmFixStrength = ArmFixStrength; Frame.ArmFixLo = ArmFixLo; Frame.ArmFixHi = ArmFixHi;
	// straight into the proxy (UAnimInstance::PreUpdateAnimation copies before NativeUpdateAnimation runs: this avoids a one-frame lag)
	GetProxyOnGameThread<FWHHeroV2AnimProxy>().Frame = Frame;
	LogState(A);
}

// r5 (critic r4 #6, fl17 "he stands on the load and dives with empty hands while it falls separately"): the director's carried load is held
// overhead in both fists. Game thread, before the evaluation: is a load carried (catch / set-down edges), the arms-overhead weight.
void UWHHeroV2AnimInstance::UpdateCarry(const FWebTravAnim& A, float Dt)
{
	AWHRescueDirector* Dir = RescueDir.Get();
	if (!Dir && A.Flight.bActive)
	{ // (looked up once a second until found; the director is spawned by the flight game mode)
		RescueFindT -= Dt;
		if (RescueFindT <= 0.f) { RescueFindT = 1.f; Dir = AWHRescueDirector::Find(GetWorld()); RescueDir = Dir; }
	}
	if (Dir) Dir->SetOverheadCarryHero(true);   // catch from above only at close reach; lives count on the set-down (see the director)
	FTransform LoadW = FTransform::Identity;
	FVector HalfCm = FVector::ZeroVector;
	const bool bNow = Dir && A.Flight.bActive && Dir->GetCarriedLoad(LoadW, HalfCm);
	if (bNow && !bCarry) { bCarryCatch = true; CarryT = 0.f; }
	bCarry = bNow;
	if (bCarry) { CarryT += Dt; CarryHalfCm = HalfCm; }
	CarryArmT += Dt;
	CarryW = bCarry ? FMath::Min(1.f, CarryW + Dt / FMath::Max(0.01f, CarryInT)) : FMath::Max(0.f, CarryW - Dt / FMath::Max(0.01f, CarryOutT));
}

// r7 (critic r6 #2, fl17 32.9 - 36.2 s "the hero's side merges into the taxi door"): street vehicles are collision-free ISM instances, so
// the float settles wherever the player stops -- here inside a parked taxi's side. Floating (nearly) still within 1.5 m of the floor (hover /
// launch-up / the landing hold), the director's vehicle boxes (AWHRescueDirector::GatherVehicles, 10 Hz) give the smallest sideways push
// that puts StandClearCm between the body (StandRadiusCm) and every box; the mesh root eases there (<= StandClearMaxCm, tau 0.2 s) and
// back when he moves on. Visual only (capsule, camera target and flight body untouched); the director's set-down reads the same offset.
void UWHHeroV2AnimInstance::UpdateStandClear(const FWebTravAnim& A, const UWHFlightComponent* FlC, float Dt)
{
	using S = EWHHeroV2State;
	const S Now = CurrentState();
	const AWebTravCharacter* Ch = Cast<AWebTravCharacter>(GetOwningActor());
	const UWebTraversalComponent* Trav = Ch ? Ch->GetTraversal() : nullptr;
	const bool bOn = StandClearCm > 0.f && bFloat && FlC && Trav && A.Mode == EWebTravMode::Air && A.Speed < StandClearMaxSpeed
		&& FlC->FloatGapM() < 1.5 && (Now == S::Hover || Now == S::LaunchUp || (Now == S::LandHero && bLandImpact));
	if (bOn)
	{
		StandQueryT -= Dt;
		if (StandQueryT <= 0.f)
		{
			StandQueryT = 0.1f;
			const FVector Feet = Trav->PosM() * 100.0 - FVector(0, 0, UWebTraversalComponent::H * 100.0);
			TArray<FWHVehicleBox> Boxes;
			FVector Push = FVector::ZeroVector;
			if (AWHRescueDirector::GatherVehicles(GetWorld(), Feet, 900.0, Boxes) > 0
				&& AWHRescueDirector::VehicleClearPush(Boxes, Feet, 185.0, double(StandRadiusCm), double(StandClearCm), Push))
			{
				Push = Push.GetClampedToMaxSize(double(StandClearMaxCm));
				if (!bStandLogged)
				{
					UE_LOG(LogWebHomage, Display, TEXT("WH_HEROV2 stand clear: %d vehicle box(es) within %.0f cm of the body at (%.0f, %.0f, %.0f) -> mesh steps %.0f cm (%.0f, %.0f)"),
						Boxes.Num(), StandClearCm, Feet.X, Feet.Y, Feet.Z, Push.Size(), Push.X, Push.Y);
					bStandLogged = true;
				}
			}
			StandWant = Push;
		}
	}
	else { StandWant = FVector::ZeroVector; StandQueryT = 0.f; if (StandNudge.SizeSquared() < 1.0) bStandLogged = false; }
	StandNudge += (StandWant - StandNudge) * (1.f - FMath::Exp(-Dt / 0.2f));
	const USkeletalMeshComponent* SMC = GetSkelMeshComponent();
	Frame.NudgeCS = (SMC && StandNudge.SizeSquared() > 0.01) ? SMC->GetComponentTransform().InverseTransformVector(StandNudge) : FVector::ZeroVector;
	if (AWHRescueDirector* Dir = RescueDir.Get()) Dir->SetHeroVisualOffset(StandNudge);
}

// r5 (critic r4 #6): the load's place, from THIS frame's evaluated pose (game thread, after the evaluation, before the director's
// TG_PostPhysics tick renders it at anchor x mesh transform): bottom face on top of both fists (the middle-finger knuckles + CarryFistCm),
// up = along the arms (overhead in a hover, ahead on a fly line), depth axis Y = the chest's forward (the director's set-down reads it),
// 4 m X across the shoulders. For CarrySwingT after the catch the load travels from where it was caught round the chest's front, never
// closer to the body capsule (feet -> head) than its separating distance + CarryClearCm.
void UWHHeroV2AnimInstance::NativePostEvaluateAnimation()
{
	Super::NativePostEvaluateAnimation();
	if (!bCarry || !bRefOk) return;
	AWHRescueDirector* Dir = RescueDir.Get();
	USkeletalMeshComponent* SMC = GetSkelMeshComponent();
	if (!Dir || !SMC) return;
	const TArray<FTransform>& CS = SMC->GetEditableComponentSpaceTransforms();   // (the buffer the evaluation just filled)
	auto Bone = [SMC, &CS](const TCHAR* Name, FTransform& Out) -> bool
	{
		const int32 I = SMC->GetBoneIndex(FName(Name));
		if (!CS.IsValidIndex(I)) return false;
		Out = CS[I];
		return true;
	};
	FTransform HL, HR, SL, SR, Head, FL, FR, Chest;
	if (!Bone(TEXT("left_middle1"), HL) || !Bone(TEXT("right_middle1"), HR) || !Bone(TEXT("left_shoulder"), SL) || !Bone(TEXT("right_shoulder"), SR)
		|| !Bone(TEXT("head"), Head) || !Bone(TEXT("left_foot"), FL) || !Bone(TEXT("right_foot"), FR)) return;
	const double Sc = FMath::Max(1e-4, double(SMC->GetComponentScale().X));   // mesh units -> cm
	const FVector Half = CarryHalfCm / Sc;
	const FVector HandM = (HL.GetLocation() + HR.GetLocation()) * 0.5;
	FVector Z = HandM - (SL.GetLocation() + SR.GetLocation()) * 0.5;
	Z = Z.IsNearlyZero() ? Ref.Up : Z.GetSafeNormal();
	FVector Y = (ChestBone != NAME_None && Bone(*ChestBone.ToString(), Chest)) ? Chest.GetRotation().RotateVector(ChestFwdLocal) : Ref.Fwd;
	Y -= Z * FVector::DotProduct(Y, Z);
	if (Y.SizeSquared() < 1e-6) { Y = Ref.Fwd - Z * FVector::DotProduct(Ref.Fwd, Z); }
	Y = Y.GetSafeNormal();
	const FQuat HoldQ = FRotationMatrix::MakeFromZY(Z, Y).ToQuat();
	const FVector HoldP = HandM + Z * (double(CarryFistCm) / Sc + Half.Z);
	const FTransform MeshXf = SMC->GetComponentTransform();
	if (bCarryCatch)
	{ // the catch: from where the load is now, relative to the hero mesh (it then moves with him)
		FTransform LoadW; FVector HalfCm;
		if (Dir->GetCarriedLoad(LoadW, HalfCm))
		{
			CarryCatchCS = FTransform(LoadW.GetRotation(), LoadW.GetLocation()).GetRelativeTransform(MeshXf);
			CarryCatchCS.SetScale3D(FVector::OneVector);
		}
		else CarryCatchCS = FTransform(HoldQ, HoldP);
		bCarryCatch = false;
	}
	FTransform LoadCS(HoldQ, HoldP);
	const float K = CarrySwingT > 0.01f ? FMath::Clamp(CarryT / CarrySwingT, 0.f, 1.f) : 1.f;
	if (K < 1.f)
	{
		// r7 (critic r6 #2, fl17 17.35 - 17.65 "legs inside the container"): r5/r6 swung the load from the catch through the chest's front,
		// i.e. down past his legs / waist. Now the path is split along the body axis: the height eases in first (Ev, done by 70 %), the
		// sideways offset last (Eh, from 25 %), and a keep-out guard holds the box horizontally clear of the body (box support + 30 cm body
		// radius + CarryClearCm) whenever its vertical extent overlaps the band feet - clear .. max(head top + clear, raised fists) -- soft over
		// CarryMarginCm, off at the hold. With the director's under-the-load catch (bottom face over his head) it never comes below his head.
		const double E = WHHeroV2Detail::HV2Smooth(K, 0.f, 1.f);
		const double Ev = WHHeroV2Detail::HV2Smooth(K, 0.f, 0.7f), Eh = WHHeroV2Detail::HV2Smooth(K, 0.25f, 1.f);
		const FVector A0 = (FL.GetLocation() + FR.GetLocation()) * 0.5, B0 = Head.GetLocation();
		const FVector BAx = (B0 - A0).IsNearlyZero() ? Ref.Up : (B0 - A0).GetSafeNormal();
		const double HeadTop = FVector::DotProduct(B0 - A0, BAx) + 12.0 / Sc, Rad = 30.0 / Sc, Clear = double(CarryClearCm) / Sc, Margin = double(CarryMarginCm) / Sc;
		const double HandTop = FMath::Max(FVector::DotProduct(HL.GetLocation() - A0, BAx), FVector::DotProduct(HR.GetLocation() - A0, BAx));
		auto Split = [&A0, &BAx](const FVector& P, double& H, FVector& R) { const FVector D = P - A0; H = FVector::DotProduct(D, BAx); R = D - BAx * H; };
		double H0 = 0.0, H1 = 0.0; FVector R0, R1;
		Split(CarryCatchCS.GetLocation(), H0, R0);
		Split(HoldP, H1, R1);
		const FQuat Q = FQuat::Slerp(CarryCatchCS.GetRotation(), HoldQ, float(E)).GetNormalized();
		const double H = FMath::Lerp(H0, H1, Ev);
		FVector R = FMath::Lerp(R0, R1, Eh);
		const double SupV = WHHeroV2Detail::HV2BoxSupport(Q, Half, BAx);
		const double Hi = FMath::Max(HeadTop + Clear, HandTop + double(CarryFistCm) / Sc - Margin - 1.0 / Sc), Lo = -Clear;
		const double Pen = FMath::Min((H + SupV) - Lo, Hi - (H - SupV));   // > 0: the box's vertical extent overlaps the body band
		const double G = double(WHHeroV2Detail::HV2Smooth(float(Pen), float(-Margin), 0.f)) * (1.0 - double(WHHeroV2Detail::HV2Smooth(float(E), 0.92f, 1.f)));
		if (G > 1e-4)
		{
			FVector Rd = R;
			if (Rd.SizeSquared() < 1e-6) Rd = R0;
			if (Rd.SizeSquared() < 1e-6) Rd = Y - BAx * FVector::DotProduct(Y, BAx);
			Rd = Rd.GetSafeNormal();
			const double Sep = WHHeroV2Detail::HV2BoxSupport(Q, Half, Rd) + Rad + Clear;
			if (R.Size() < Sep * G) R = Rd * (Sep * G);
		}
		LoadCS = FTransform(Q, A0 + BAx * H + R);
	}
	Dir->SetCarryAnchor(SMC, LoadCS);
}

// ------------------------------------------------------------------ proxy (worker thread)
bool FWHHeroV2AnimProxy::Evaluate(FPoseContext& Output)
{
	FCompactPose& Pose = Output.Pose;
	const FBoneContainer& BC = Pose.GetBoneContainer();
	auto Idx = [&BC](const FName& Name) -> FCompactPoseBoneIndex
	{
		const int32 MI = BC.GetPoseBoneIndexForBoneName(Name);
		return MI == INDEX_NONE ? FCompactPoseBoneIndex(INDEX_NONE) : BC.MakeCompactPoseIndex(FMeshPoseBoneIndex(MI));
	};
	// r5: arm / non-arm bone mask (compact indices) for the per-layer arm overrides and the touchdown dip
	bool bNeedMask = Frame.DipSeq && Frame.DipW > 0.001f;
	for (const FWHHeroV2Layer& L : Frame.Layers) bNeedMask |= L.ArmSeq && L.ArmW > 0.001f;
	TArray<uint8, TInlineAllocator<96>> IsArm;
	if (bNeedMask)
	{
		IsArm.SetNumZeroed(Pose.GetNumBones());
		const FReferenceSkeleton& RS = BC.GetReferenceSkeleton();
		for (FCompactPoseBoneIndex B : Pose.ForEachBoneIndex())
			IsArm[B.GetInt()] = IsArmBone(RS.GetBoneName(BC.MakeMeshPoseIndex(B).GetInt())) ? 1 : 0;
	}
	// r5 arm fix (critic r4 #1): each layer's collar / shoulder local rotations, per side
	static const FName CollarN[2] = { FName(TEXT("left_collar")), FName(TEXT("right_collar")) };
	static const FName ShoulderN[2] = { FName(TEXT("left_shoulder")), FName(TEXT("right_shoulder")) };
	FCompactPoseBoneIndex Ic[2] = { FCompactPoseBoneIndex(INDEX_NONE), FCompactPoseBoneIndex(INDEX_NONE) }, Is[2] = { FCompactPoseBoneIndex(INDEX_NONE), FCompactPoseBoneIndex(INDEX_NONE) };
	bool bArmIdx = Frame.bArmFix;   // r7: the indices also serve the per-layer arm override's swing (ApplyArms)
	if (bArmIdx) for (int32 S = 0; S < 2; ++S) { Ic[S] = Idx(CollarN[S]); Is[S] = Idx(ShoulderN[S]); bArmIdx &= Ic[S].IsValid() && Is[S].IsValid(); }
	const bool bFix = bArmIdx && Frame.Layers.Num() > 1;
	struct FArmSample { float W; FQuat C[2]; FQuat S[2]; };
	TArray<FArmSample, TInlineAllocator<8>> ArmSamples;
	auto Sample = [&Ic, &Is](const FCompactPose& P, float W) -> FArmSample
	{
		FArmSample R; R.W = W;
		for (int32 S = 0; S < 2; ++S) { R.C[S] = P[Ic[S]].GetRotation(); R.S[S] = P[Is[S]].GetRotation(); }
		return R;
	};
	auto Record = [&](const FCompactPose& P, float W) { if (bFix) ArmSamples.Add(Sample(P, W)); };
	// r5 (critic r4 #1): where the inputs' upper-arm directions (chest frame) cancel -- arms down vs overhead -- the plain per-bone blend
	// passes the arm out sideways (the T-pose flash at every hover <-> fly); the blended upper arm is turned toward the mean direction plus
	// the chest's forward, i.e. the arm swings up in front of the body. No change where the inputs agree (one clip, similar arms).
	auto SwingFront = [this, &Ic, &Is](FCompactPose& P, const FArmSample* Smp, int32 N)
	{
		for (int32 S = 0; S < 2; ++S)
		{
			FVector Sum = FVector::ZeroVector; float WSum = 0.f;
			for (int32 J = 0; J < N; ++J) { Sum += (Smp[J].C[S] * Smp[J].S[S]).RotateVector(Frame.ArmAxis[S]) * Smp[J].W; WSum += Smp[J].W; }
			if (WSum <= 1e-4f) continue;
			Sum /= WSum;
			const float Cn = 1.f - float(Sum.Size());
			const float G = WHHeroV2Detail::HV2Smooth(Cn, Frame.ArmFixLo, Frame.ArmFixHi);
			if (G <= 0.001f) continue;
			const float Bias = Frame.ArmFixStrength * WHHeroV2Detail::HV2Smooth(Cn, Frame.ArmFixLo + 0.05f, Frame.ArmFixHi + 0.3f);
			const FVector Want = (Sum + Frame.ChestFwd[S] * Bias).GetSafeNormal();
			const FQuat Rc = P[Ic[S]].GetRotation(), Rs = P[Is[S]].GetRotation();
			const FVector Now = (Rc * Rs).RotateVector(Frame.ArmAxis[S]);
			if (Want.IsNearlyZero() || Now.IsNearlyZero()) continue;
			const FQuat Corr = FQuat::Slerp(FQuat::Identity, FQuat::FindBetweenNormals(Now, Want), G);
			P[Is[S]].SetRotation((Rc.Inverse() * Corr * Rc * Rs).GetNormalized());
		}
	};
	// r7 (critic r6 #2, fl17 catch "arms in a T"): the per-layer arm override (the carry's AS_LaunchUp fists overhead blending in over a hover
	// layer's arms-down) is the same cancelling pair -- the override blend now gets the same swing in front of the chest
	auto ApplyArms = [this, &IsArm, bArmIdx, &Sample, &SwingFront](FCompactPose& P, const FWHHeroV2Layer& L)
	{
		if (!L.ArmSeq || L.ArmW <= 0.001f || IsArm.Num() != P.GetNumBones()) return;
		FPoseContext ArmCtx(this);
		FAnimationPoseData ArmData(ArmCtx);
		L.ArmSeq->GetAnimationPose(ArmData, FAnimExtractContext(double(L.ArmTime), false, {}, L.bArmLoop));
		const bool bSwing = bArmIdx && L.bArmSwing && L.ArmW < 0.999f;
		FArmSample Pair[2];
		if (bSwing) { Pair[0] = Sample(P, 1.f - L.ArmW); Pair[1] = Sample(ArmCtx.Pose, L.ArmW); }
		for (FCompactPoseBoneIndex B : P.ForEachBoneIndex()) if (IsArm[B.GetInt()]) P[B].BlendWith(ArmCtx.Pose[B], L.ArmW);
		if (bSwing) SwingFront(P, Pair, 2);
	};
	// r7 (critic r6 #3): the AS_Hover layer's local rotations of the breathing bones (the heaviest such layer)
	FCompactPoseBoneIndex Ib[FWHHeroV2Frame::NumBreath];
	FQuat BreathQ[FWHHeroV2Frame::NumBreath];
	float BreathLayerW = 0.f;
	const bool bBreath = Frame.BreathK > 0.001f;
	for (int32 K = 0; K < FWHHeroV2Frame::NumBreath; ++K)
	{
		Ib[K] = (bBreath && Frame.BreathBone[K] != NAME_None) ? Idx(Frame.BreathBone[K]) : FCompactPoseBoneIndex(INDEX_NONE);
		BreathQ[K] = FQuat::Identity;
	}
	auto RecordBreath = [&](const FCompactPose& P, const FWHHeroV2Layer& L)
	{
		if (!bBreath || !L.bBreath || L.Weight <= BreathLayerW) return;
		BreathLayerW = L.Weight;
		for (int32 K = 0; K < FWHHeroV2Frame::NumBreath; ++K) if (Ib[K].IsValid()) BreathQ[K] = P[Ib[K]].GetRotation();
	};

	bool bFirst = true;
	float Acc = 0.f;
	FAnimationPoseData OutData(Output);
	for (const FWHHeroV2Layer& L : Frame.Layers)
	{
		if (!L.Seq || L.Weight <= 0.001f) continue;
		if (bFirst)
		{
			L.Seq->GetAnimationPose(OutData, FAnimExtractContext(double(L.Time), false, {}, L.bLoop));
			RecordBreath(Output.Pose, L);
			ApplyArms(Output.Pose, L);
			Record(Output.Pose, L.Weight);
			Acc = L.Weight; bFirst = false;
			continue;
		}
		FPoseContext Tmp(this);
		FAnimationPoseData TmpData(Tmp);
		L.Seq->GetAnimationPose(TmpData, FAnimExtractContext(double(L.Time), false, {}, L.bLoop));
		RecordBreath(Tmp.Pose, L);
		ApplyArms(Tmp.Pose, L);
		Record(Tmp.Pose, L.Weight);
		FAnimationRuntime::BlendTwoPosesTogetherInPlace(OutData, TmpData, Acc / (Acc + L.Weight));
		Acc += L.Weight;
	}
	if (bFirst) { Output.ResetToRefPose(); return true; }
	if (bFix && ArmSamples.Num() > 1) SwingFront(Pose, ArmSamples.GetData(), ArmSamples.Num());
	if (Frame.DipSeq && Frame.DipW > 0.001f && IsArm.Num() == Pose.GetNumBones())
	{ // r5 (critic r4 #5): touchdown knee bend -- the non-arm bones toward AS_Takeoff's crouch (the ground lock below keeps the feet down)
		FPoseContext DipCtx(this);
		FAnimationPoseData DipData(DipCtx);
		Frame.DipSeq->GetAnimationPose(DipData, FAnimExtractContext(double(Frame.DipTime), false, {}, false));
		for (FCompactPoseBoneIndex B : Pose.ForEachBoneIndex()) if (!IsArm[B.GetInt()]) Pose[B].BlendWith(DipCtx.Pose[B], Frame.DipW);
	}
	if (Frame.bRefOk && Frame.GroundW > 0.001f)
	{ // ground lock: shift the root bone along the mesh up axis so the lowest foot joint sits at its reference-pose height
		auto CS = [&Pose, &BC](FCompactPoseBoneIndex B) -> FTransform
		{
			FTransform T = Pose[B];
			FCompactPoseBoneIndex P = BC.GetParentBoneIndex(B);
			while (P.IsValid()) { T = T * Pose[P]; P = BC.GetParentBoneIndex(P); }
			return T;
		};
		static const FName FootLN(TEXT("left_foot")), FootRN(TEXT("right_foot"));
		const FCompactPoseBoneIndex FL = Idx(FootLN), FR = Idx(FootRN);
		if (FL.IsValid() && FR.IsValid())
		{
			const double MinUp = FMath::Min(FVector::DotProduct(CS(FL).GetLocation(), Frame.UpCS), FVector::DotProduct(CS(FR).GetLocation(), Frame.UpCS));
			const double D = FMath::Clamp((double(Frame.RefFootUp) - MinUp) * double(Frame.GroundW), -double(Frame.MaxShift), double(Frame.MaxShift));
			const FCompactPoseBoneIndex Root(0);   // compact index 0 = the root bone: its local space is component space
			Pose[Root].AddToTranslation(Frame.UpCS * D);
		}
	}
	// r7 (critic r6 #3): hover breathing -- the AS_Hover layer's deviation from its clip mean (Delta = Q x Avg^-1, local) is applied once more
	// by BreathK (spine2 / spine3) / BreathArmK (collars): Q' = Delta^k x Q, i.e. (1 + k) x the clip's own breathing on these bones
	if (bBreath && BreathLayerW > 0.f)
	{
		for (int32 K = 0; K < FWHHeroV2Frame::NumBreath; ++K)
		{
			if (!Ib[K].IsValid()) continue;
			const float Kk = K < 2 ? Frame.BreathK : Frame.BreathArmK;
			if (Kk <= 0.001f) continue;
			FQuat Delta = (BreathQ[K] * Frame.BreathAvg[K].Inverse()).GetNormalized();
			if (Delta.W < 0.f) Delta = -Delta;                               // shortest arc
			if (Delta.GetAngle() > FMath::DegreesToRadians(12.f)) continue;   // (not breathing: a transition pose)
			const FQuat Add = FQuat::Slerp(FQuat::Identity, Delta, Kk).GetNormalized();
			Pose[Ib[K]].SetRotation((Add * Pose[Ib[K]].GetRotation()).GetNormalized());
		}
	}
	// r7 (critic r6 #3 / #2): the hover bob along the mesh up and the stand-clear nudge, both on the root (component space)
	if (FMath::Abs(Frame.BobShift) > 1e-6f || !Frame.NudgeCS.IsNearlyZero(1e-6))
	{
		const FCompactPoseBoneIndex Root(0);
		Pose[Root].AddToTranslation(Frame.UpCS * double(Frame.BobShift) + Frame.NudgeCS);
	}
	return true;
}
