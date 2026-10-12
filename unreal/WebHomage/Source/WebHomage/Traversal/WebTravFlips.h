// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// Piece P3 round 11 (owner brief FLIPS_BRIEF.md, spec docs/night1/traversal/FLIPS_SPEC.md): gymnast flip programs.
// A flip program is a timeline of held gymnastic SHAPES (tuck, pike, layout, swan, pencil, straddle, throne, twist, reach,
// keyed in Blender on the hero rig: /Game/Traversal/HeroDev/flip<Shape>). The body rotation is not keyed: it follows one
// angular momentum through the whole program, rate = L * env(t) / I(shape(t)), so the flip spins fast through a tuck and
// slows almost to a hold in an open shape (pencil / swan / throne) -- the ease comes from the shapes, as in real tumbling.
// L is solved so the program ends exactly at its total angle (upright). Twists (corkscrews) turn about the body's long axis
// inside their own segments. Limbs overlap: the upper body samples the timeline FlipLead s ahead, the legs FlipLag s behind.
// Pure functions: the traversal (durations, telemetry), the character (root rotation) and the anim instance (shapes) all
// sample the same program at the same time.
#pragma once

#include "CoreMinimal.h"

// round 13: Kickout = the double's open finish (critic r12: "backDouble uses 5 shapes", "rigid identical plank"): a layout whose arms
// sweep wide while the legs scissor a little behind them, ending with the web arm up (the catch reach) -- keyed motion, not a held plank
enum class EWebFlipShape : uint8 { Tuck, Pike, Layout, Swan, Pencil, Straddle, Throne, Twist, Reach, Kickout, Num };

struct FWebFlipSeg
{
	EWebFlipShape Shape = EWebFlipShape::Tuck;
	float Dur = 0.3f;     // s
	float TwistDeg = 0.f; // twist about the long axis inside this segment (deg, eased in/out)
	// round 14 (critic r13: "the tuck spins at a constant 678 deg/s -- ease the ends >= 30 % slower than mid-flip"): the effective
	// inertia rises toward the segment's ends by these factors (1 + EaseIn at its start, 1 + EaseOut at its end, smooth over
	// WebFlips::EaseW of the segment) -- the gymnast grabs the knees tighter mid-tuck and opens a little going in / coming out
	float EaseIn = 0.f, EaseOut = 0.f;
};

struct FWebFlipProgram
{
	FName Name;
	float PitchDeg = 360.f;   // total rotation about the lateral axis; + = front flip (head goes forward), - = back flip
	TArray<FWebFlipSeg> Segs;
	float Boost = 3.5f, Up = 1.5f; // traversal release boost (m/s) at 0.3 x the first segment
	// round 13 (critic r12: "attach a web within 0.3 s of Reach"): the next web may attach from CatchOpen s before the program's end
	// (inside its final reach, once that pose reads) -- the catch cuts the last few degrees and springs them back in ~0.07 s
	float CatchOpen = 0.16f;
	// Terminal silhouette, using an existing authored clip. The Reach segment still owns its inertia and catch timing.
	EWebFlipShape CatchShape = EWebFlipShape::Reach;
	// round 19 (critic r18 "every trick is a canned playback"): per-instance variant data -- Lead / Lag override WebFlips::FlipLead /
	// FlipLag (arm / leg timing) when >= 0; Ver changes with every variant (rate-table cache key); Scale = duration factor vs the base
	float Lead = -1.f, Lag = -1.f;
	int32 Ver = 0;
	float Scale = 1.f;
	float CatchT() const { return FMath::Max(0.f, Dur() - CatchOpen); }
	float Dur() const { float D = 0.f; for (const FWebFlipSeg& S : Segs) D += S.Dur; return D; }
};

struct FWebFlipPose
{
	bool bValid = false;
	float PitchDeg = 0.f, TwistDeg = 0.f, PitchRate = 0.f;  // deg, deg, deg/s
	// upper-body shape blend (sampled FlipLead ahead) and legs (FlipLag behind): A -> B by W; HoldA = 0..1 progress through A's hold
	EWebFlipShape A = EWebFlipShape::Tuck, B = EWebFlipShape::Tuck, LA = EWebFlipShape::Tuck, LB = EWebFlipShape::Tuck;
	float W = 0.f, LW = 0.f, HoldA = 0.f, HoldB = 0.f, LHoldA = 0.f, LHoldB = 0.f;
	// round 14: the upper-body shape's own hips->head lean off the body frame (deg, + = head forward), blended A -> B by W. The
	// character subtracts it from the root pitch so the VISIBLE body axis follows the momentum timeline (r13 rendered: a swan -> tuck
	// change curled the axis ~55 deg in 0.17 s on top of the program, so every tuck entered at ~460 deg/s and pikeSwan peaked 1045-1090)
	float AxisOffDeg = 0.f;
	int32 Seg = 0;
};

namespace WebFlips
{
	/** Blender clip name of a shape (flipTuck ...). */
	const TCHAR* ShapeClip(EWebFlipShape S);
	const TCHAR* ShapeName(EWebFlipShape S);
	/** Round 14: hips->head lean of a keyed shape off the body frame (deg, + = head forward), measured on the rendered r14 probe. */
	float ShapeAxisDeg(EWebFlipShape S);
	/** Round 18: vertical extent (m) a shape reaches during its hold (trick-camera distance anticipation). */
	float ShapeExtent(EWebFlipShape S);
	/** Program by name (backDouble, frontPikeSwan, corkscrew, backSingle, wallFront); nullptr if unknown. Round 19: the current
	 *  per-instance variant of that program once one was made (MakeVariant), else the base program. */
	const FWebFlipProgram* Find(FName Name);
	/** Round 19: the unvaried base program (planning / fit checks before a variant exists). */
	const FWebFlipProgram* FindBase(FName Name);
	/** Round 19: make this instance's variant of a program: total duration x Scale (0.8-1.2), each segment x its own 0.92-1.08 jitter
	 *  (the rate curve's shape changes, not only its speed), arm lead / leg lag per instance. Returns the variant (also what Find returns). */
	const FWebFlipProgram* MakeVariant(FName Name, float Scale, uint32 Seed);
	/** Round 19: -WHFlipVar=0 turns variants off (A/B against round 18). */
	extern bool bVariants;
	/** Tricks C r01: per-instance tempo (+10-16 % / -10-13 %) on top of half the caller's scale; -WHTrickTempo=0 = the r19-r23 scale. */
	extern bool bTempo;
	/** All program names (for cycling). */
	const TArray<FName>& Names();
	/** Tricks C r01: the programs a web release may play (every program but the wall top-out), in the reel's cycling order. */
	const TArray<FName>& ReleasePrograms();
	/** Tricks C r01 trick input mapping (for UWebTraversalComponent::ChooseTrick, see docs/night1/tricks/REQUEST-traversal.md):
	 *  StickFwd / StickLat = the move stick at the trick press (forward +, right +), K = a running counter (never the same program twice
	 *  in a row), AirS = seconds of air the release has before the catch window must open (<= 0: unknown, any program).
	 *  Stick forward -> front family (frontDouble, frontPikeSwan, barani, frontSingle, corkscrew, rudi); back -> back family (backDouble,
	 *  backTripleChain, backPike, backSingle, backLayout, fullTwist); sideways -> twisting family (barani, fullTwist, rudi, corkscrew);
	 *  neutral -> every release program in turn. The longest programs only play when AirS covers 1.15 x their catch time. Round 05 (critic
	 *  r04: "0-1 rotations per release"): the double / triple programs lead the front / back pools, so a long release opens with 2-3
	 *  rotations (F1); the fit test still falls back to the singles in short air. */
	FName ChooseForInput(float StickFwd, float StickLat, int32 K, float AirS, FName Last);
	/** Sample a program at T seconds (clamped to [0, Dur]). */
	FWebFlipPose Sample(const FWebFlipProgram& P, float T);
	/** Root offset using the evaluated pose axis in figure space, so keyed lean cannot add to the flip rate. */
	FQuat PoseRotation(const FWebFlipPose& Pose, const FVector& PoseAxis, float EntryW, float Side);
	extern float FlipLead, FlipLag;
}
