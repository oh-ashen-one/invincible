// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Combat/WHClipStack.h"
#include "Combat/WHCombatUtil.h"
#include "Animation/AnimSequence.h"

int32 FWHClipStack::Play(FName Name, UAnimSequence* Seq, const FWHClipOpts& O)
{
	if (!Seq) return 0;
	FWHClipTrack Tr;
	Tr.Name = Name; Tr.Id = O.Id.IsNone() ? Name : O.Id; Tr.Seq = Seq;
	Tr.Len = FMath::Max(0.01, double(Seq->GetPlayLength()));
	Tr.T = FMath::Clamp(O.From, 0.0, Tr.Len);
	Tr.Ts = O.Ts;
	Tr.Until = O.Until < 0.0 ? Tr.Len : FMath::Min(O.Until, Tr.Len);
	Tr.Fade = O.Fade; Tr.W = O.Fade <= 0.0 ? 1.0 : 0.0;
	Tr.bUpper = O.bUpper; Tr.bHold = O.bHold; Tr.bLoop = O.bLoop; Tr.bLockHips = O.bLockHips;
	Tr.Uid = NextUid++;
	// masked tracks replace older tracks with the same id
	if (O.bUpper)
	{
		for (FWHClipTrack& T : Tracks) if (T.Id == Tr.Id && T.Out <= 0.0) { T.Out = 1e-6; T.FadeOut = FMath::Max(O.Fade, 0.05); }
	}
	Tracks.Add(Tr);
	return Tr.Uid;
}

void FWHClipStack::Stop(double FadeOut)
{
	for (FWHClipTrack& T : Tracks) if (T.Out <= 0.0) { T.Out = 1e-6; T.FadeOut = FadeOut; }
}

void FWHClipStack::StopId(FName Id, double FadeOut)
{
	for (FWHClipTrack& T : Tracks) if (T.Id == Id && T.Out <= 0.0) { T.Out = 1e-6; T.FadeOut = FadeOut; }
}

FWHClipTrack* FWHClipStack::Find(int32 Uid)
{
	if (!Uid) return nullptr;
	for (FWHClipTrack& T : Tracks) if (T.Uid == Uid) return &T;
	return nullptr;
}

const FWHClipTrack* FWHClipStack::Find(int32 Uid) const
{
	if (!Uid) return nullptr;
	for (const FWHClipTrack& T : Tracks) if (T.Uid == Uid) return &T;
	return nullptr;
}

void FWHClipStack::Advance(double Dt)
{
	if (!Tracks.Num()) return;
	for (FWHClipTrack& T : Tracks)
	{
		if (T.bLoop) { T.T = FMath::Fmod(T.T + Dt * T.Ts, T.Len); if (T.T < 0) T.T += T.Len; }
		else T.T = FMath::Min(T.Until, T.T + Dt * T.Ts);
		T.W = FMath::Min(1.0, T.W + Dt / FMath::Max(1e-3, T.Fade));
		if (T.Out > 0.0) T.Out += Dt / FMath::Max(1e-3, T.FadeOut);
		if (!T.bHold && !T.bLoop && T.T >= T.Until && T.Out <= 0.0) T.Out = 1e-6;
		if (T.Out >= 1.0) T.bDead = true;
	}
	int32 Cover = -1;
	for (int32 i = Tracks.Num() - 1; i >= 0; --i)
	{
		const FWHClipTrack& T = Tracks[i];
		if (!T.bUpper && T.W >= 1.0 && T.Out <= 0.0) { Cover = i; break; }
	}
	TArray<FWHClipTrack> Keep;
	for (int32 i = 0; i < Tracks.Num(); ++i)
	{
		const FWHClipTrack& T = Tracks[i];
		if (T.bDead) continue;
		if (Cover >= 0 && i < Cover && !T.bUpper) continue;
		Keep.Add(T);
	}
	Tracks = MoveTemp(Keep);
}

double FWHClipStack::Coverage() const
{
	double Rest = 1.0;
	for (const FWHClipTrack& T : Tracks)
	{
		if (T.bUpper) continue;
		const double Env = WHCmb::Smooth(T.W) * (1.0 - WHCmb::Smooth(T.Out));
		Rest *= (1.0 - Env);
	}
	return 1.0 - Rest;
}

void FWHClipStack::Snapshot(TArray<FWHClipSample>& Out) const
{
	Out.Reset();
	for (const FWHClipTrack& T : Tracks)
	{
		const double Env = WHCmb::Smooth(T.W) * (1.0 - WHCmb::Smooth(T.Out));
		if (Env < 0.001 || !T.Seq) continue;
		FWHClipSample S;
		S.Seq = T.Seq; S.Time = float(T.T); S.Env = float(Env); S.bUpper = T.bUpper; S.bLoop = T.bLoop; S.bLockHips = T.bLockHips;
		Out.Add(S);
	}
}
