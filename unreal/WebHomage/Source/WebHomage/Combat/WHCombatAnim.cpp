// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Combat/WHCombatAnim.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimationPoseData.h"
#include "AnimationRuntime.h"
#include "BonePose.h"

namespace
{
	FCompactPoseBoneIndex BoneIdx(const FBoneContainer& BC, const TCHAR* Name)
	{
		const int32 MI = BC.GetPoseBoneIndexForBoneName(FName(Name));
		return MI == INDEX_NONE ? FCompactPoseBoneIndex(INDEX_NONE) : BC.MakeCompactPoseIndex(FMeshPoseBoneIndex(MI));
	}
	FTransform RefCS(const FBoneContainer& BC, FCompactPoseBoneIndex B)
	{
		FTransform T = BC.GetRefPoseTransform(B);
		FCompactPoseBoneIndex P = BC.GetParentBoneIndex(B);
		while (P.IsValid()) { T = T * BC.GetRefPoseTransform(P); P = BC.GetParentBoneIndex(P); }
		return T;
	}
	FTransform PoseCS(const FCompactPose& Pose, FCompactPoseBoneIndex B)
	{
		const FBoneContainer& BC = Pose.GetBoneContainer();
		FTransform T = Pose[B];
		FCompactPoseBoneIndex P = BC.GetParentBoneIndex(B);
		while (P.IsValid()) { T = T * Pose[P]; P = BC.GetParentBoneIndex(P); }
		return T;
	}
	struct FBasis { FVector Up = FVector::UpVector, Fwd = FVector::ForwardVector, Right = FVector::RightVector, RefHipsH = FVector::ZeroVector; bool bOk = false; };
	FBasis RefBasis(const FBoneContainer& BC)
	{
		FBasis B;
		const FCompactPoseBoneIndex Hips = BoneIdx(BC, TEXT("hips")), Head = BoneIdx(BC, TEXT("head"));
		const FCompactPoseBoneIndex FL = BoneIdx(BC, TEXT("foot_L")), TL = BoneIdx(BC, TEXT("toe_L"));
		if (!Hips.IsValid() || !Head.IsValid()) return B;
		const FVector HipP = RefCS(BC, Hips).GetLocation();
		B.Up = (RefCS(BC, Head).GetLocation() - HipP).GetSafeNormal();
		if (FL.IsValid() && TL.IsValid())
		{
			FVector F = RefCS(BC, TL).GetLocation() - RefCS(BC, FL).GetLocation();
			F -= B.Up * FVector::DotProduct(F, B.Up);
			B.Fwd = F.GetSafeNormal();
		}
		B.Right = FVector::CrossProduct(B.Up, B.Fwd).GetSafeNormal();
		B.RefHipsH = HipP - B.Up * FVector::DotProduct(HipP, B.Up);
		B.bOk = true;
		return B;
	}
	void RotateBoneCS(FCompactPose& Pose, FCompactPoseBoneIndex B, const FQuat& Q)
	{
		if (!B.IsValid()) return;
		const FBoneContainer& BC = Pose.GetBoneContainer();
		const FCompactPoseBoneIndex P = BC.GetParentBoneIndex(B);
		const FTransform ParentCS = P.IsValid() ? PoseCS(Pose, P) : FTransform::Identity;
		FTransform CS = Pose[B] * ParentCS;
		CS.SetRotation((Q * CS.GetRotation()).GetNormalized());
		Pose[B] = CS.GetRelativeTransform(ParentCS);
	}
}

void WHCmbAnim::ApplySamples(FAnimInstanceProxy& Proxy, FPoseContext& Output, const TArray<FWHClipSample>& Samples, bool bFirstFull)
{
	if (!Samples.Num()) return;
	FCompactPose& Pose = Output.Pose;
	const FBoneContainer& BC = Pose.GetBoneContainer();
	const FBasis Bs = RefBasis(BC);
	const FCompactPoseBoneIndex Hips = BoneIdx(BC, TEXT("hips"));
	// upper-body mask: spine1 and everything below it in the hierarchy
	TArray<uint8> Upper;
	bool bAnyUpper = false;
	for (const FWHClipSample& S : Samples) bAnyUpper |= S.bUpper;
	if (bAnyUpper)
	{
		const FCompactPoseBoneIndex Sp = BoneIdx(BC, TEXT("spine1"));
		Upper.SetNumZeroed(Pose.GetNumBones());
		for (FCompactPoseBoneIndex B : Pose.ForEachBoneIndex())
		{
			FCompactPoseBoneIndex C = B;
			while (C.IsValid()) { if (C == Sp) { Upper[B.GetInt()] = 1; break; } C = BC.GetParentBoneIndex(C); }
		}
	}
	bool bFirst = bFirstFull;
	for (const FWHClipSample& S : Samples)
	{
		if (!S.Seq) continue;
		FPoseContext Tmp(&Proxy);
		FAnimationPoseData TmpData(Tmp);
		S.Seq->GetAnimationPose(TmpData, FAnimExtractContext(double(S.Time), false, {}, S.bLoop));
		if (S.bLockHips && Hips.IsValid() && Bs.bOk)
		{
			FTransform& H = Tmp.Pose[Hips];
			const FVector T = H.GetTranslation();
			H.SetTranslation(Bs.RefHipsH + Bs.Up * FVector::DotProduct(T, Bs.Up));
		}
		const float W = bFirst ? 1.f : FMath::Clamp(S.Env, 0.f, 1.f);
		bFirst = false;
		for (FCompactPoseBoneIndex B : Pose.ForEachBoneIndex())
		{
			if (S.bUpper && !Upper[B.GetInt()]) continue;
			Pose[B].BlendWith(Tmp.Pose[B], W);
		}
	}
}

void WHCmbAnim::ApplyProc(FPoseContext& Output, const FWHProcLayer& P)
{
	if (FMath::Abs(P.Flinch) < 1e-3f && FMath::Abs(P.AimPitch) < 1e-3f) return;
	FCompactPose& Pose = Output.Pose;
	const FBoneContainer& BC = Pose.GetBoneContainer();
	const FBasis Bs = RefBasis(BC);
	if (!Bs.bOk) return;
	auto Lean = [&Bs](double A) // rotate "up" toward "back" by A rad (A < 0 leans forward)
	{
		return FQuat::FindBetweenNormals(Bs.Up, (Bs.Up * FMath::Cos(A) - Bs.Fwd * FMath::Sin(A)).GetSafeNormal());
	};
	const FCompactPoseBoneIndex Sp2 = BoneIdx(BC, TEXT("spine2")), Head = BoneIdx(BC, TEXT("head"));
	const double F = P.Flinch * P.Flinch * (3.0 - 2.0 * P.Flinch);
	double A = 0.35 * F + 0.8 * P.AimPitch;
	if (FMath::Abs(A) > 1e-4) RotateBoneCS(Pose, Sp2, Lean(A));
	if (F > 1e-3 && Head.IsValid())
		RotateBoneCS(Pose, Head, FQuat::FindBetweenNormals(Bs.Up, (Bs.Up * FMath::Cos(0.3 * F) + Bs.Right * P.FlinchDir * FMath::Sin(0.3 * F)).GetSafeNormal()));
}

// ------------------------------------------------------------------------------------------------ hero
UAnimSequence* UWHCombatHeroAnim::CombatClip(FName Name)
{
	if (TObjectPtr<UAnimSequence>* S = CClips.Find(Name)) return S->Get();
	const FString N = ClipPrefix + Name.ToString();   // r04: P2's hero clips are prefixed (-WHHeroClipPrefix=A_Hero_); empty for the HeroDev proxy
	UAnimSequence* Seq = LoadObject<UAnimSequence>(nullptr, *FString::Printf(TEXT("%s/%s.%s"), *ClipRoot, *N, *N));
	CClips.Add(Name, Seq);
	return Seq;
}

void FWHCombatHeroProxy::PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds)
{
	FWebTravAnimProxy::PreUpdate(InAnimInstance, DeltaSeconds);
	if (const UWHCombatHeroAnim* I = Cast<UWHCombatHeroAnim>(InAnimInstance)) Samples = I->Samples;
}

bool FWHCombatHeroProxy::Evaluate(FPoseContext& Output)
{
	FWebTravAnimProxy::Evaluate(Output);
	WHCmbAnim::ApplySamples(*this, Output, Samples, false);
	return true;
}

// ------------------------------------------------------------------------------------------------ enemy
void FWHEnemyProxy::PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds)
{
	FAnimInstanceProxy::PreUpdate(InAnimInstance, DeltaSeconds);
	if (const UWHEnemyAnim* I = Cast<UWHEnemyAnim>(InAnimInstance)) { Samples = I->Samples; Proc = I->Proc; }
}

bool FWHEnemyProxy::Evaluate(FPoseContext& Output)
{
	Output.ResetToRefPose();
	WHCmbAnim::ApplySamples(*this, Output, Samples, true);
	WHCmbAnim::ApplyProc(Output, Proc);
	return true;
}
