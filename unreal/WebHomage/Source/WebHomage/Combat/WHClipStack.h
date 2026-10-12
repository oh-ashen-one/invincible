// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// Piece P5 (combat): clip stack — port of src/game/combat/poselayer.js (and of the crime actors' mixer.play cross-fades).
// A stack of clip tracks; each new full-body track cross-fades in over everything below it (buried tracks are dropped once
// covered), masked tracks (upper body) replace older tracks with the same id. Game thread only; the anim proxies read a
// snapshot (FWHClipSample) every frame.
#pragma once

#include "CoreMinimal.h"

class UAnimSequence;

struct FWHClipOpts
{
	double From = 0.0;
	double Until = -1.0;   // < 0: clip end
	double Ts = 1.0;
	double Fade = 0.08;
	bool bUpper = false;   // upper-body mask (spine and up)
	bool bHold = true;     // freeze at Until (false: fade out when reaching it)
	bool bLoop = false;    // loop the clip (enemy idles / locomotion)
	bool bLockHips = true; // hips horizontal pinned (root motion handled by the owner)
	FName Id;
};

struct FWHClipTrack
{
	FName Name, Id;
	UAnimSequence* Seq = nullptr;
	double T = 0.0, Ts = 1.0, Until = 0.0, Len = 0.0, Fade = 0.08, W = 0.0, Out = 0.0, FadeOut = 0.2;
	bool bUpper = false, bHold = true, bLoop = false, bLockHips = true, bDead = false;
	int32 Uid = 0;
};

/** What the anim proxy samples (one per live track, bottom to top). */
struct FWHClipSample
{
	UAnimSequence* Seq = nullptr;
	float Time = 0.f;
	float Env = 0.f;       // 0..1 blend weight over what is below
	bool bUpper = false;
	bool bLoop = false;
	bool bLockHips = true;
};

struct WEBHOMAGE_API FWHClipStack
{
	TArray<FWHClipTrack> Tracks;
	int32 NextUid = 1;

	/** Push a track. Returns its uid (0 if Seq is null). */
	int32 Play(FName Name, UAnimSequence* Seq, const FWHClipOpts& O);
	/** Fade every live track out. */
	void Stop(double FadeOut = 0.22);
	void StopId(FName Id, double FadeOut = 0.2);
	FWHClipTrack* Find(int32 Uid);
	const FWHClipTrack* Find(int32 Uid) const;
	FWHClipTrack* Top() { return Tracks.Num() ? &Tracks.Last() : nullptr; }
	bool Active() const { return Tracks.Num() > 0; }
	/** Advance times + envelopes, prune covered / dead tracks. */
	void Advance(double Dt);
	/** Overall weight of the stack over the base pose (1 - product of (1 - env)). */
	double Coverage() const;
	void Snapshot(TArray<FWHClipSample>& Out) const;
	void Clear() { Tracks.Reset(); }
};
