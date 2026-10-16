// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
// Hero v2 (owner-approved model, 2026-10-15): clip-driven anim instance. See WHHeroV2AnimInstance.h and
// docs/invincible/loop/heroV2_integration_NOTES.md (state -> clip table, tunables, capture checks).
#include "Traversal/Anim/WHHeroV2AnimInstance.h"
#include "Traversal/WebTravCharacter.h"
#include "Traversal/WebTraversalComponent.h"
#include "WebHomage.h"
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
	{ // -WHHeroV2Tune=Name=Value,... (float UPROPERTYs above)
		FString Tune;
		if (FParse::Value(FCommandLine::Get(), TEXT("-WHHeroV2Tune="), Tune, false) && !Tune.IsEmpty()) ApplyTune(Tune);
	}
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
	Tracks.Reset();
	UE_LOG(LogWebHomage, Display, TEXT("WH_HEROV2 anim init: %d/%d clips from %s (missing: %s; skeleton mismatch: %s), ref %s up %s fwd %s footUp %.2f height %.2f units"),
		NLoaded, int32(EWHHeroV2Clip::Num), ClipRoot, Missing.IsEmpty() ? TEXT("none") : *Missing, Mismatch.IsEmpty() ? TEXT("none") : *Mismatch,
		bRefOk ? TEXT("ok") : TEXT("MISSING BONES (no ground lock)"), *Ref.Up.ToString(), *Ref.Fwd.ToString(), Ref.RefFootUp, Ref.HeightUnits);
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
	if (To == S::Dash || From == S::Dash) return BlendDash;
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
	case EWHHeroV2State::Takeoff: Want = C::Takeoff; break;
	case EWHHeroV2State::Hover: Want = C::Hover; break;
	case EWHHeroV2State::LaunchUp: Want = C::LaunchUp; break;
	case EWHHeroV2State::Fly: Want = C::Fly; break;
	case EWHHeroV2State::Dash: Want = C::Fly; Tr.Rate = DashRate; break;               // dash: a fast AS_Fly (accepted by the owner brief)
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
	return float(FMath::Max(0.0, FeetZ - G) / Vz);
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
		else if (Want == S::LandHero)
		{
			bDive = A.Mode == EWebTravMode::Air;   // slam / double-tap dive: the clip starts with the dive
			bLandImpact = !bDive;
			if (!bDive) StartT = FMath::Max(0.f, LandImpactT - 0.08f);   // a hard landing without the dive: just before the impact frame
		}
		else if (Want == S::BoostLaunch && A.Flight.ChargeK <= 0.f) StartT = BoostBurstT;   // a boom without a seen charge
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
			{ // the landing event: the impact frame must be on it -- an early impact jumps to it with a short blend
				Tr.bDive = false; bLandImpact = true;
				bImpactJump = Tr.T < LandImpactT - 0.06f;
			}
			else
			{ // dive: play to the hold frame, then keep it until the floor is close enough that the remaining clip time to the impact frame
			  // equals the time to impact (catch-up at most 3x)
				const float Free = Tr.T < LandDiveHoldT ? FMath::Min(Tr.T + Dt, LandDiveHoldT) : Tr.T;
				const float Sync = LandImpactT - TimeToImpact(A);
				Tr.T = FMath::Max(Free, FMath::Min(Sync, Tr.T + 3.f * Dt));
				Tr.T = FMath::Min(Tr.T, LandImpactT - 0.01f);
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

	// ---- ground lock (grounded clips: feet on the floor) and the pitch freedom for the character
	{
		float Target = 0.f;
		const S Now = CurrentState();
		if (Now == S::GroundIdle) Target = 1.f;
		else if (Now == S::LandHero && bLandImpact) Target = 1.f;
		else if (Now == S::Takeoff) Target = 1.f - HV2Smooth(StateT, 0.f, FMath::Max(0.01f, TakeoffUnlockT));
		Frame.GroundW = bRefOk ? Frame.GroundW + (Target - Frame.GroundW) * (1.f - FMath::Exp(-Dt / FMath::Max(0.005f, GroundLockTau))) : 0.f;
		float PF = 0.f;
		for (const FTrack& Tr : Tracks)
		{
			float K = 0.f;
			if (HV2IsFlyType(Tr.State)) K = 1.f - Tr.UpW;
			else if (Tr.State == S::BoostLaunch) K = 1.f;
			else if (Tr.State == S::LandHero && Tr.bDive) K = 1.f;
			PF += Tr.W * K;
		}
		PitchFreedomV = FMath::Clamp(PF, 0.f, 1.f);
	}

	// ---- layers for the proxy (each track: its clip, plus the AS_LaunchUp blend of fly-type tracks)
	Frame.Layers.Reset();
	for (const FTrack& Tr : Tracks)
	{
		UAnimSequence* Seq = ClipSeq(Tr.Clip);
		if (!Seq || Tr.W <= 0.001f) continue;
		const float Wu = Tr.UpClip >= 0 ? FMath::Clamp(Tr.UpW, 0.f, 1.f) : 0.f;
		if (1.f - Wu > 0.001f) Frame.Layers.Add({ Seq, Tr.T, Tr.W * (1.f - Wu), Tr.bLoop });
		if (Wu > 0.001f) Frame.Layers.Add({ ClipSeq(Tr.UpClip), Tr.UpT, Tr.W * Wu, true });
	}
	// straight into the proxy (UAnimInstance::PreUpdateAnimation copies before NativeUpdateAnimation runs: this avoids a one-frame lag)
	GetProxyOnGameThread<FWHHeroV2AnimProxy>().Frame = Frame;
	LogState(A);
}

// ------------------------------------------------------------------ proxy (worker thread)
bool FWHHeroV2AnimProxy::Evaluate(FPoseContext& Output)
{
	bool bFirst = true;
	float Acc = 0.f;
	FAnimationPoseData OutData(Output);
	for (const FWHHeroV2Layer& L : Frame.Layers)
	{
		if (!L.Seq || L.Weight <= 0.001f) continue;
		if (bFirst)
		{
			L.Seq->GetAnimationPose(OutData, FAnimExtractContext(double(L.Time), false, {}, L.bLoop));
			Acc = L.Weight; bFirst = false;
			continue;
		}
		FPoseContext Tmp(this);
		FAnimationPoseData TmpData(Tmp);
		L.Seq->GetAnimationPose(TmpData, FAnimExtractContext(double(L.Time), false, {}, L.bLoop));
		FAnimationRuntime::BlendTwoPosesTogetherInPlace(OutData, TmpData, Acc / (Acc + L.Weight));
		Acc += L.Weight;
	}
	if (bFirst) { Output.ResetToRefPose(); return true; }
	if (Frame.bRefOk && Frame.GroundW > 0.001f)
	{ // ground lock: shift the root bone along the mesh up axis so the lowest foot joint sits at its reference-pose height
		FCompactPose& Pose = Output.Pose;
		const FBoneContainer& BC = Pose.GetBoneContainer();
		auto Idx = [&BC](const TCHAR* Name) -> FCompactPoseBoneIndex
		{
			const int32 MI = BC.GetPoseBoneIndexForBoneName(FName(Name));
			return MI == INDEX_NONE ? FCompactPoseBoneIndex(INDEX_NONE) : BC.MakeCompactPoseIndex(FMeshPoseBoneIndex(MI));
		};
		auto CS = [&Pose, &BC](FCompactPoseBoneIndex B) -> FTransform
		{
			FTransform T = Pose[B];
			FCompactPoseBoneIndex P = BC.GetParentBoneIndex(B);
			while (P.IsValid()) { T = T * Pose[P]; P = BC.GetParentBoneIndex(P); }
			return T;
		};
		const FCompactPoseBoneIndex FL = Idx(TEXT("left_foot")), FR = Idx(TEXT("right_foot"));
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
