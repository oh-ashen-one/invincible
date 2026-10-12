// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Characters/WHCharAnimInstance.h"
#include "Animation/AnimSequence.h"
#include "AnimationRuntime.h"
#include "Animation/AnimationPoseData.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Characters/WHCharLoopWalker.h"
#include "Characters/WHCharStage.h"

void UWHCharAnimInstance::NativeInitializeAnimation()
{
	Super::NativeInitializeAnimation();
	Loco.RemoveAll([](const FWHLocoSample& S) { return S.Clip == nullptr || S.Speed <= 0.f; });
	Loco.Sort([](const FWHLocoSample& A, const FWHLocoSample& B) { return A.Speed < B.Speed; });
	bHasLast = false;
	// round 05: a walker's AnimOffset also seeds the locomotion phase (in cycles), so identical clips at identical speeds are not in lockstep (CH19)
	if (const AWHCharLoopWalker* W = Cast<AWHCharLoopWalker>(GetOwningActor()))
	{ IdleOffset = W->AnimOffset; Phase = FMath::Frac(W->AnimOffset); }
}

void UWHCharAnimInstance::NativeUpdateAnimation(float Dt)
{
	Super::NativeUpdateAnimation(Dt);
	if (Dt <= 0.f) return;
	USkeletalMeshComponent* Comp = GetSkelMeshComponent();
	AActor* Owner = GetOwningActor();
	FVector Vel = FVector::ZeroVector;
	bool bAir = bForceAir;
	float Vz = ForcedVerticalSpeed;
	if (const ACharacter* C = Cast<ACharacter>(Owner))
	{
		if (const UCharacterMovementComponent* M = C->GetCharacterMovement())
		{
			Vel = M->Velocity; bAir = bAir || M->IsFalling(); if (!bForceAir) Vz = Vel.Z;
		}
	}
	else if (Comp)
	{
		const FVector P = Comp->GetComponentLocation();
		if (bHasLast) Vel = (P - LastPos) / Dt;
		LastPos = P; bHasLast = true;
	}
	const float Measured = ForcedSpeed >= 0.f ? ForcedSpeed : FVector(Vel.X, Vel.Y, 0.f).Size();
	SmoothedSpeed = FMath::FInterpTo(SmoothedSpeed, Measured, Dt, 8.f);
	Speed = SmoothedSpeed; VerticalSpeed = Vz; bInAir = bAir;

	// ---- locomotion 1D blend with a shared phase
	GameLayers.Reset();
	float LocoRate = 0.f;
	int32 I0 = -1, I1 = -1; float A = 0.f;
	if (Loco.Num() > 0)
	{
		if (Speed <= Loco[0].Speed) { I0 = I1 = 0; }
		else if (Speed >= Loco.Last().Speed) { I0 = I1 = Loco.Num() - 1; }
		else
		{
			for (int32 i = 0; i + 1 < Loco.Num(); ++i)
				if (Speed >= Loco[i].Speed && Speed <= Loco[i + 1].Speed)
				{ I0 = i; I1 = i + 1; A = (Speed - Loco[i].Speed) / FMath::Max(1.f, Loco[i + 1].Speed - Loco[i].Speed); break; }
		}
		const float L0 = Loco[I0].Clip->GetPlayLength(), L1 = Loco[I1].Clip->GetPlayLength();
		const float NatV = FMath::Lerp(Loco[I0].Speed, Loco[I1].Speed, A);
		const float NatRate = FMath::Lerp(1.f / FMath::Max(0.05f, L0), 1.f / FMath::Max(0.05f, L1), A);
		const float Ratio = FMath::Clamp(FMath::Max(Speed, Loco[0].Speed * 0.5f) / NatV, 0.3f, 2.5f);
		LocoRate = NatRate * FMath::Pow(Ratio, CadenceExp);
		Phase = FMath::Fmod(Phase + Dt * LocoRate, 1.f);
	}
	IdleTime += Dt;
	const float MoveW = (Idle || Sequence.Num() > 0) ? FMath::Clamp((Speed - IdleSpeed) / FMath::Max(1.f, (Loco.Num() ? Loco[0].Speed : 150.f) * 0.5f - IdleSpeed), 0.f, 1.f) : 1.f;

	// ---- air / land
	if (bAir && !bWasInAir) { AirTime = 0.f; if (Vz >= 50.f) ++JumpCount; if ((JumpUp || JumpVariants.Num() > 0) && Vz >= 50.f) FallAlpha = 0.f; }   // a jump starts on JumpUp, not on a stale fall weight
	UAnimSequence* JumpClip = JumpVariants.Num() > 0 ? JumpVariants[FMath::Max(0, JumpCount - 1) % JumpVariants.Num()].Get() : JumpUp.Get();
	if (!bAir && bWasInAir) LandTime = 0.f;
	bWasInAir = bAir;
	AirTime += Dt; LandTime += Dt;
	AirAlpha = FMath::FInterpTo(AirAlpha, bAir ? 1.f : 0.f, Dt, bAir ? AirBlendIn : 10.f);
	FallAlpha = FMath::FInterpTo(FallAlpha, ((Vz < 50.f && !bJumpHoldsThroughDescent) || !JumpClip) ? 1.f : 0.f, Dt, 6.f);
	float LandW = 0.f;
	if (Land && !bAir)
	{
		const float LL = Land->GetPlayLength();
		if (LandTime < LL) LandW = FMath::Clamp(1.f - LandTime / (0.8f * LL), 0.f, 1.f) * FMath::Clamp(1.f - Speed / 600.f, 0.25f, 1.f);
	}
	// takeoff anticipation: weight ramps in over TakeoffBlendIn while grounded; after lift-off the clip's last sampled pose is held
	// under the air blend so the crouch hands over to JumpUp (whose first frame is the same crouch) without a pop
	float TakeW = 0.f;
	if (Takeoff)
	{
		if (TakeoffTime >= 0.f) { LastTakeoff = TakeoffTime; TakeoffHold = 1.f; TakeW = FMath::Clamp(TakeoffTime / FMath::Max(0.01f, TakeoffBlendIn), 0.f, 1.f); }
		else if (bAir && TakeoffHold > 0.f) { TakeoffHold = FMath::Max(0.f, TakeoffHold - Dt / FMath::Max(0.02f, TakeoffHoldTime)); TakeW = TakeoffHold; }
		else TakeoffHold = 0.f;
	}
	float GroundW = (1.f - AirAlpha) * (1.f - LandW) * (1.f - TakeW);

	// ---- round 09: scripted beats (a choreographed fight): timed one-shot clips over the base (guard idle / locomotion); the base gets what is left
	struct FBeatW { UAnimSequence* Seq; float T_; float W; };
	TArray<FBeatW, TInlineAllocator<4>> Beats;
	float BeatSum = 0.f;
	if (Script.Num() > 0)
	{
		const float Ts = WHStage::Now(GetWorld());
		for (const FWHScriptBeat& B : Script)
		{
			if (!B.Clip || Ts < B.Start) continue;
			const float Len = B.Clip->GetPlayLength(), Rate = FMath::Max(0.05f, B.Rate);
			const float PlayEnd = B.Start + FMath::Max(0.f, Len - B.ClipStart) / Rate;
			const float HoldEnd = B.Hold < 0.f ? 1e9f : PlayEnd + B.Hold;
			const float Win = B.BlendIn > 1e-3f ? FMath::Clamp((Ts - B.Start) / B.BlendIn, 0.f, 1.f) : 1.f;
			const float Wout = Ts <= HoldEnd ? 1.f : (B.BlendOut > 1e-3f ? FMath::Clamp(1.f - (Ts - HoldEnd) / B.BlendOut, 0.f, 1.f) : 0.f);
			const float W = B.Weight * WHStage::Smooth(Win) * WHStage::Smooth(Wout);
			if (W <= 1e-3f) continue;
			Beats.Add({B.Clip.Get(), FMath::Clamp(B.ClipStart + (Ts - B.Start) * Rate, 0.f, Len), W});
			BeatSum += W;
		}
		if (BeatSum > 1.f) { for (FBeatW& B : Beats) B.W /= BeatSum; BeatSum = 1.f; }
	}
	const float ScriptW = BeatSum;
	const float BaseW = GroundW * (1.f - ScriptW);   // idle / sequence / locomotion share what the beats leave

	auto Push = [this](UAnimSequence* S, float T, float W, bool bLoop)
	{
		if (!S || W <= 1e-3f) return;
		FWHAnimLayer L; L.Seq = S; L.Time = bLoop ? FMath::Fmod(T, S->GetPlayLength()) : FMath::Clamp(T, 0.f, S->GetPlayLength()); L.Weight = W; L.bLoop = bLoop;
		GameLayers.Add(L);
	};
	if (Sequence.Num() > 0)
	{
		// staged idle: clips back to back, each cross-faded into the next over SequenceBlend (segment k lasts len_k - Blend)
		const int32 N = Sequence.Num();
		float Total = 0.f;
		TArray<float, TInlineAllocator<16>> Seg;
		for (int32 i = 0; i < N; ++i) { const float L = Sequence[i] ? Sequence[i]->GetPlayLength() : 0.5f; const float B = FMath::Min(SequenceBlend, 0.45f * L); Seg.Add(FMath::Max(0.05f, L - B)); Total += Seg.Last(); }
		float P = FMath::Fmod(FMath::Max(0.f, IdleTime + IdleOffset), Total), Start = 0.f;
		int32 K = 0;
		for (; K < N - 1 && P >= Start + Seg[K]; ++K) Start += Seg[K];
		const float Tk = P - Start;
		const int32 Prev = (K + N - 1) % N;
		const float LenK = Sequence[K] ? Sequence[K]->GetPlayLength() : 0.5f;
		const float Bk = FMath::Min(SequenceBlend, 0.45f * (Sequence[Prev] ? Sequence[Prev]->GetPlayLength() : 0.5f));
		const float W = Bk > 1e-3f ? FMath::Clamp(Tk / Bk, 0.f, 1.f) : 1.f;
		const float Ws = W * W * (3.f - 2.f * W);
		Push(Sequence[K], FMath::Min(Tk, LenK), BaseW * (1.f - MoveW) * Ws, false);
		if (Ws < 1.f) Push(Sequence[Prev], Seg[Prev] + Tk, BaseW * (1.f - MoveW) * (1.f - Ws), false);
	}
	else if (Idle) Push(Idle, IdleTime, BaseW * (1.f - MoveW), true);
	if (I0 >= 0)
	{
		Push(Loco[I0].Clip, Phase * Loco[I0].Clip->GetPlayLength(), BaseW * MoveW * (I0 == I1 ? 1.f : 1.f - A), true);
		if (I1 != I0) Push(Loco[I1].Clip, Phase * Loco[I1].Clip->GetPlayLength(), BaseW * MoveW * A, true);
	}
	for (const FBeatW& B : Beats) Push(B.Seq, B.T_, GroundW * B.W, false);
	Push(Land, LandTime, (1.f - AirAlpha) * LandW, false);
	Push(Takeoff, FMath::Max(0.f, LastTakeoff), TakeW * (bAir ? 1.f : (1.f - AirAlpha)), false);
	Push(JumpClip, AirTime, AirAlpha * (1.f - FallAlpha) * (1.f - (bAir ? TakeW : 0.f)), false);
	Push(Fall, AirTime, AirAlpha * FallAlpha, true);
}

void FWHCharAnimProxy::PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds)
{
	FAnimInstanceProxy::PreUpdate(InAnimInstance, DeltaSeconds);
	if (UWHCharAnimInstance* I = Cast<UWHCharAnimInstance>(InAnimInstance)) Layers = I->GameLayers;
}

bool FWHCharAnimProxy::Evaluate(FPoseContext& Output)
{
	float Acc = 0.f;
	bool bFirst = true;
	for (const FWHAnimLayer& L : Layers)
	{
		if (!L.Seq || L.Weight <= 0.f) continue;
		if (bFirst)
		{
			FAnimationPoseData Out(Output);
			L.Seq->GetAnimationPose(Out, FAnimExtractContext(double(L.Time), false, FDeltaTimeRecord(), L.bLoop));
			Acc = L.Weight; bFirst = false;
			continue;
		}
		FPoseContext Tmp(Output), Res(Output);
		FAnimationPoseData TmpData(Tmp);
		L.Seq->GetAnimationPose(TmpData, FAnimExtractContext(double(L.Time), false, FDeltaTimeRecord(), L.bLoop));
		FAnimationPoseData OutData(Output), ResData(Res);
		FAnimationRuntime::BlendTwoPosesTogether(OutData, TmpData, Acc / (Acc + L.Weight), ResData);
		Acc += L.Weight;
		Output = Res;
	}
	if (bFirst) Output.ResetToRefPose();
	return true;
}
