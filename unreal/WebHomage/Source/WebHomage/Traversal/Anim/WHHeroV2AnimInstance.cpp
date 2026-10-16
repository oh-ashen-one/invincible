// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
// Hero v2 (owner-approved model, 2026-10-15): clip-driven anim instance. See WHHeroV2AnimInstance.h and
// docs/invincible/loop/heroV2_integration_NOTES.md (state -> clip table, tunables, capture checks).
#include "Traversal/Anim/WHHeroV2AnimInstance.h"
#include "Traversal/WebTravCharacter.h"
#include "Traversal/WebTraversalComponent.h"
#include "Flight/WHRescueDirector.h"
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
	if (bRefOk) AnalyzeLandClip();
	{ // -WHHeroV2Tune=Name=Value,... (float UPROPERTYs above; after the clip analysis, so a tune overrides the measured land frames)
		FString Tune;
		if (FParse::Value(FCommandLine::Get(), TEXT("-WHHeroV2Tune="), Tune, false) && !Tune.IsEmpty()) ApplyTune(Tune);
	}
	Tracks.Reset();
	DipT = 99.f; CarryW = 0.f; bCarry = false;
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
}

float UWHHeroV2AnimInstance::TakeoffPlantK(float T) const
{
	if (T < 0.f) return 0.f;
	if (T < TakeoffPlantT) return 1.f;
	return 1.f - WHHeroV2Detail::HV2Smooth(T, TakeoffPlantT, TakeoffPlantT + FMath::Max(0.01f, TakeoffCatchT));
}

float UWHHeroV2AnimInstance::DiveFlipK(float T) const
{
	return WHHeroV2Detail::HV2Smooth(T, LandDiveHoldT, FMath::Max(LandDiveHoldT + 0.01f, LandFeetT));
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
	case EWHHeroV2State::BoostLaunch: Want = C::BoostLaunch; break;
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
	const double G = Tr->TravWorld.GroundHeight(P.X, P.Y, FeetZ + 0.05);
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
	{ // fly-type line pitched up past LaunchUpPitchDeg blends toward AS_LaunchUp (owner brief: "e.g. > 60 deg")
		const float Vh = float(FVector2D(A.Velocity.X, A.Velocity.Y).Size() / 100.0);
		if (FMath::Sqrt(Vh * Vh + Vz * Vz) > 3.f)
		{
			const float GammaDeg = FMath::RadiansToDegrees(FMath::Atan2(Vz, Vh));
			OutUpTarget = HV2Smooth(GammaDeg, LaunchUpPitchDeg - LaunchUpBandDeg, LaunchUpPitchDeg + LaunchUpBandDeg);
		}
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
	if (Want == S::Fly && Cur == S::BoostLaunch && !bCurDone && F.ChargeK <= 0.f && CurTr && CurTr->T >= BoostBurstT) return S::BoostLaunch;
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
	if (Want == S::BoostLaunch && Cur == S::BoostLaunch && A.Flight.ChargeK > 0.f && Tracks.Last().T > BoostBurstT + 0.05f)
		StartTrack(S::BoostLaunch, 0.f, BlendToBoostLaunch);   // a fresh charge while the last launch is still showing
	else if (Want != Cur)
	{
		float StartT = 0.f;
		bool bDive = false;
		if (Want == S::Takeoff) StartT = TakeoffClipStart;
		else if (Want == S::Brake) StartT = BrakeEnterT;   // r5 (critic r4 #2): upright brake entry, never the clip's side-roll part
		else if (Want == S::LandHero)
		{
			bDive = A.Mode == EWebTravMode::Air;   // slam / double-tap dive: the clip starts with the dive
			bLandImpact = !bDive;
			// a hard landing without the dive: just before the contact frame, legs already under him (r5)
			if (!bDive) StartT = FMath::Max(LandFeetT, LandImpactT - 0.04f);
		}
		else if (Want == S::BoostLaunch && A.Flight.ChargeK <= 0.f) StartT = BoostBurstT;   // a boom without a seen charge
		// r5 (critic r4 #5 / #8, touchdown "stops in one frame, no knee compression"): a soft landing dips into a knee bend
		if (Want == S::GroundIdle && Cur != S::GroundIdle && Cur != S::LandHero && Cur != S::None)
		{
			DipT = 0.f;
			DipPeakNow = FMath::Clamp(DipPeak + DipPeakPerMps * FMath::Max(0.f, -PrevVz), 0.f, DipMax);
		}
		StartTrack(Want, StartT, BlendTime(Cur, Want));
		Tracks.Last().bDive = bDive;
		if (!HV2IsFlyType(Want)) UpWNow = 0.f;
	}

	// ---- special timing of the current track
	if (Tracks.Num())
	{
		FTrack& Tr = Tracks.Last();
		if (Tr.State == S::BoostLaunch && A.Flight.ChargeK > 0.f && Tr.Clip == int32(EWHHeroV2Clip::BoostLaunch))
		{ // owner brief: the 0.42 s burst coincides with the boom -- the clip time follows the flight's own charge progress (real-time,
		  // slow-mo proof): ChargeK = smoothstep(SuperT / SuperChargeTime) -> T = BoostBurstT x invsmooth(ChargeK); AdvanceTracks adds Dt
			Tr.T = FMath::Max(Tr.T, BoostBurstT * HV2InvSmooth(A.Flight.ChargeK) - Dt * Tr.Rate);
			Tr.T = FMath::Min(Tr.T, BoostBurstT - Dt * Tr.Rate);
		}
		bool bImpactJump = false;
		if (Tr.State == S::LandHero && Tr.bDive)
		{
			if (A.Mode != EWebTravMode::Air)
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
				if (T < LandDiveHoldT) T = FMath::Min(T + Dt, LandDiveHoldT);
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
		else if (Now == S::LandHero && Top && Top->bDive) Target = FMath::Square(DiveFlipK(Top->T));
		Frame.GroundW = bRefOk ? Frame.GroundW + (Target - Frame.GroundW) * (1.f - FMath::Exp(-Dt / FMath::Max(0.005f, GroundLockTau))) : 0.f;
		float PF = 0.f;
		for (const FTrack& Tr : Tracks)
		{
			float K = 0.f;
			if (HV2IsFlyType(Tr.State)) K = 1.f - Tr.UpW;
			else if (Tr.State == S::BoostLaunch) K = 1.f;
			else if (Tr.State == S::LandHero && Tr.bDive) K = 1.f - DiveFlipK(Tr.T);   // r5: upright once feet-first (critic r4 #3)
			PF += Tr.W * K;
		}
		PitchFreedomV = FMath::Clamp(PF, 0.f, 1.f);
	}

	// ---- r5 touchdown dip (critic r4 #5): AS_Takeoff's crouch on the non-arm bones, in over DipInT, out over DipOutT
	if (CurrentState() == S::GroundIdle) DipT = FMath::Min(DipT + Dt, 99.f);
	else DipT = 99.f;
	{
		const float Up = HV2Smooth(DipT, 0.f, FMath::Max(0.01f, DipInT));
		const float Dn = 1.f - HV2Smooth(DipT, DipInT, DipInT + FMath::Max(0.01f, DipOutT));
		Frame.DipW = DipT < 50.f ? DipPeakNow * FMath::Min(Up, Dn) : 0.f;
		Frame.DipSeq = ClipSeq(int32(EWHHeroV2Clip::Takeoff));
		Frame.DipTime = DipPoseT;
		if (!Frame.DipSeq) Frame.DipW = 0.f;
	}

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
		UAnimSequence* ArmSeq = nullptr; float ArmT = 0.f, ArmW = 0.f; bool bArmLoop = true;
		if (Tr.State == S::Takeoff && Tr.Clip == int32(EWHHeroV2Clip::Takeoff) && IdleSeq)
		{
			ArmSeq = IdleSeq; ArmT = 0.5f; ArmW = 1.f - HV2Smooth(Tr.T, TakeoffArmsT0, TakeoffArmsT1);
		}
		if (CarryW > 0.001f && UpSeq)
		{
			ArmW = FMath::Max(ArmW, CarryW); ArmSeq = UpSeq; ArmT = FMath::Fmod(CarryArmT, ClipLen(int32(EWHHeroV2Clip::LaunchUp)));
		}
		if (ArmW <= 0.001f) ArmSeq = nullptr;
		if (1.f - Wu > 0.001f) Frame.Layers.Add({ Seq, Tr.T, Tr.W * (1.f - Wu), Tr.bLoop, ArmSeq, ArmT, ArmW, bArmLoop });
		if (Wu > 0.001f) Frame.Layers.Add({ ClipSeq(Tr.UpClip), Tr.UpT, Tr.W * Wu, true, ArmSeq, ArmT, ArmW, bArmLoop });
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
		const double E = WHHeroV2Detail::HV2Smooth(K, 0.f, 1.f);
		// body capsule: feet midpoint -> head joint (+ ~12 cm skull), radius ~30 cm
		const FVector A0 = (FL.GetLocation() + FR.GetLocation()) * 0.5, B0 = Head.GetLocation();
		const FVector Cc = (A0 + B0) * 0.5;
		const FVector BAx = (B0 - A0).GetSafeNormal();
		const double HalfLen = (B0 - A0).Size() * 0.5 + 12.0 / Sc, Rad = 30.0 / Sc, Clear = double(CarryClearCm) / Sc;
		const FVector P0 = CarryCatchCS.GetLocation() - Cc, P1 = HoldP - Cc;
		const double R0 = P0.Size(), R1 = P1.Size();
		const FVector D0 = R0 > 1e-3 ? P0 / R0 : Y, D1 = R1 > 1e-3 ? P1 / R1 : Z;
		// direction: a quadratic arc on the sphere through the chest's front (never through the body)
		FVector D = D0 * ((1.0 - E) * (1.0 - E)) + Y * (2.0 * E * (1.0 - E)) + D1 * (E * E);
		D = D.IsNearlyZero() ? D1 : D.GetSafeNormal();
		const FQuat Q = FQuat::Slerp(CarryCatchCS.GetRotation(), HoldQ, float(E)).GetNormalized();
		const double Need = WHHeroV2Detail::HV2BoxSupport(Q, Half, D) + HalfLen * FMath::Abs(FVector::DotProduct(BAx, D)) + Rad + Clear;
		double R = FMath::Lerp(R0, R1, E);
		R += FMath::Max(0.0, Need - R) * (1.0 - WHHeroV2Detail::HV2Smooth(float(E), 0.85f, 1.f));
		LoadCS = FTransform(Q, Cc + D * R);
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
	auto ApplyArms = [this, &IsArm](FCompactPose& P, const FWHHeroV2Layer& L)
	{
		if (!L.ArmSeq || L.ArmW <= 0.001f || IsArm.Num() != P.GetNumBones()) return;
		FPoseContext ArmCtx(this);
		FAnimationPoseData ArmData(ArmCtx);
		L.ArmSeq->GetAnimationPose(ArmData, FAnimExtractContext(double(L.ArmTime), false, {}, L.bArmLoop));
		for (FCompactPoseBoneIndex B : P.ForEachBoneIndex()) if (IsArm[B.GetInt()]) P[B].BlendWith(ArmCtx.Pose[B], L.ArmW);
	};
	// r5 arm fix (critic r4 #1): each layer's collar / shoulder local rotations, per side
	static const FName CollarN[2] = { FName(TEXT("left_collar")), FName(TEXT("right_collar")) };
	static const FName ShoulderN[2] = { FName(TEXT("left_shoulder")), FName(TEXT("right_shoulder")) };
	FCompactPoseBoneIndex Ic[2] = { FCompactPoseBoneIndex(INDEX_NONE), FCompactPoseBoneIndex(INDEX_NONE) }, Is[2] = { FCompactPoseBoneIndex(INDEX_NONE), FCompactPoseBoneIndex(INDEX_NONE) };
	bool bFix = Frame.bArmFix && Frame.Layers.Num() > 1;
	if (bFix) for (int32 S = 0; S < 2; ++S) { Ic[S] = Idx(CollarN[S]); Is[S] = Idx(ShoulderN[S]); bFix &= Ic[S].IsValid() && Is[S].IsValid(); }
	struct FArmSample { float W; FQuat C[2]; FQuat S[2]; };
	TArray<FArmSample, TInlineAllocator<8>> ArmSamples;
	auto Record = [&](const FCompactPose& P, float W)
	{
		if (!bFix) return;
		FArmSample R; R.W = W;
		for (int32 S = 0; S < 2; ++S) { R.C[S] = P[Ic[S]].GetRotation(); R.S[S] = P[Is[S]].GetRotation(); }
		ArmSamples.Add(R);
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
			ApplyArms(Output.Pose, L);
			Record(Output.Pose, L.Weight);
			Acc = L.Weight; bFirst = false;
			continue;
		}
		FPoseContext Tmp(this);
		FAnimationPoseData TmpData(Tmp);
		L.Seq->GetAnimationPose(TmpData, FAnimExtractContext(double(L.Time), false, {}, L.bLoop));
		ApplyArms(Tmp.Pose, L);
		Record(Tmp.Pose, L.Weight);
		FAnimationRuntime::BlendTwoPosesTogetherInPlace(OutData, TmpData, Acc / (Acc + L.Weight));
		Acc += L.Weight;
	}
	if (bFirst) { Output.ResetToRefPose(); return true; }
	if (bFix && ArmSamples.Num() > 1)
	{ // r5 (critic r4 #1): where the layers' upper-arm directions (chest frame) cancel -- arms down vs overhead -- the plain per-bone blend
	  // passes the arm out sideways (the T-pose flash at every hover <-> fly); the blended upper arm is turned toward the mean direction plus
	  // the chest's forward, i.e. the arm swings up in front of the body. No change where the layers agree (one clip, similar arms).
		for (int32 S = 0; S < 2; ++S)
		{
			FVector Sum = FVector::ZeroVector; float WSum = 0.f;
			for (const FArmSample& R : ArmSamples) { Sum += (R.C[S] * R.S[S]).RotateVector(Frame.ArmAxis[S]) * R.W; WSum += R.W; }
			if (WSum <= 1e-4f) continue;
			Sum /= WSum;
			const float Cn = 1.f - float(Sum.Size());
			const float G = WHHeroV2Detail::HV2Smooth(Cn, Frame.ArmFixLo, Frame.ArmFixHi);
			if (G <= 0.001f) continue;
			const float Bias = Frame.ArmFixStrength * WHHeroV2Detail::HV2Smooth(Cn, Frame.ArmFixLo + 0.05f, Frame.ArmFixHi + 0.3f);
			const FVector Want = (Sum + Frame.ChestFwd[S] * Bias).GetSafeNormal();
			const FQuat Rc = Pose[Ic[S]].GetRotation(), Rs = Pose[Is[S]].GetRotation();
			const FVector Now = (Rc * Rs).RotateVector(Frame.ArmAxis[S]);
			if (Want.IsNearlyZero() || Now.IsNearlyZero()) continue;
			const FQuat Corr = FQuat::Slerp(FQuat::Identity, FQuat::FindBetweenNormals(Now, Want), G);
			Pose[Is[S]].SetRotation((Rc.Inverse() * Corr * Rc * Rs).GetNormalized());
		}
	}
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
	return true;
}
