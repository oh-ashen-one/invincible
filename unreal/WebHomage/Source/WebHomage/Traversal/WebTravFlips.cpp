// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Traversal/WebTravFlips.h"
#include "Traversal/WebTraversalComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "Components/SkeletalMeshComponent.h"
#include "Misc/CoreDelegates.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"

namespace WebFlips
{
	float FlipLead = 0.02f, FlipLag = 0.055f; // round 06: 0.04 / 0.07 -> F11 leg lag (Lead + Lag) lands 0.05-0.12 s
	bool bVariants = true;
	bool bTempo = true;

	namespace
	{
		// effective "inertia" per shape, tuned to the owner clip (FLIPS_SPEC F3/F4): tuck spins ~600 deg/s, the open holds
		// turn 40-90 deg/s (pencil / swan / throne), pike and layout sit between
		float Inertia(EWebFlipShape S)
		{
			switch (S)
			{
			// final round 10 (critic r09 gap 2, 3rd round: "~1 rotation per release vs the owner's 1080 deg / 2.8 s"): the programs are
			// retimed tighter (doubles ~2.0-2.2 s so they complete inside s3b's 1.6-2.5 s windows; means 300-380 deg/s in F2's band);
			// tuck inertia 1.0 -> 1.22 keeps the base peaks ~600-650 (a fast tempo variant + the rendered lean stack stay <= ~800: F3)
			case EWebFlipShape::Tuck: return 1.22f;
			case EWebFlipShape::Pike: return 1.35f;
			case EWebFlipShape::Layout: return 3.2f;
			// final round 12 (critic r11 gap 2: the r11 alternating programs never HOLD -- the 0.32 s hold segments at inertia 9-10
			// dip under 150 deg/s (rendered) for only ~0.25 s once the shape-transition lean stacks at both ends; the r11 F4 passes
			// were the END reach/kickout, not a mid-chain open shape): hold shapes are slower (pencil/throne 9 -> 11, swan 10 -> 12,
			// straddle 7.5 -> 8.5) and the hold segments run 0.42-0.54 s (see the tables), so the rendered <= 150 deg/s window covers
			// >= 0.3 s mid-chain with the tuck bursts kept (owner clip: pencil 0.64 s, throne 0.48 s)
			// final round 13 (critic r12 gap 2: rendered vs program -- with the clip scrub frozen in the hold core
			// (WebTravAnimInstance HoldFreeze), the hold's program rate also slows (pencil/throne 11 -> 13, swan 12 -> 14,
			// straddle 8.5 -> 10): a held shape now turns ~55-75 deg/s instead of ~80-115, so it READS held; the table's
			// total-rotation normalization moves ~1-2 % onto the tuck peaks, inside F3's headroom)
			case EWebFlipShape::Swan: return 14.0f;
			case EWebFlipShape::Pencil: return 13.0f;
			case EWebFlipShape::Straddle: return 10.0f; // round 18: corkscrew's inverted shape (replaces its swan: same timeline)
			case EWebFlipShape::Throne: return 13.0f;
			case EWebFlipShape::Twist: return 3.5f;
			case EWebFlipShape::Reach: return 7.0f;
			// round 13: open finish; round 14 5.5 -> 10.5 (rendered r13 hold 0.21 s: the keyed arch adds ~40 deg/s to the program's 123)
			case EWebFlipShape::Kickout: return 10.5f;
			default: return 3.f;
			}
		}
		float Smooth(float X) { X = FMath::Clamp(X, 0.f, 1.f); return X * X * (3.f - 2.f * X); }
		constexpr float BPre = 0.06f, BPost = 0.11f; // shape transition window around a segment boundary (s)
		constexpr float EnvIn = 0.12f, EnvOut = 0.22f; // rotation set-in / settle at the program ends (s)
		constexpr int32 TableHz = 240;

		struct FTable { TArray<float> G; float L = 0.f; int32 Ver = -1; }; // cumulative rotation (deg) at 1/TableHz steps

		TArray<FWebFlipProgram>& Programs()
		{
			static TArray<FWebFlipProgram> P;
			if (P.Num()) return P;
			using S = EWebFlipShape;
			auto Add = [&](const TCHAR* Name, float Pitch, std::initializer_list<FWebFlipSeg> Segs, float Boost = 3.5f, float Up = 1.5f, float CatchOpen = 0.16f)
			{
				FWebFlipProgram F; F.Name = FName(Name); F.PitchDeg = Pitch; F.Segs = Segs; F.Boost = Boost; F.Up = Up; F.CatchOpen = CatchOpen; P.Add(F);
			};
			// ---- P3 rounds 11-19 (kept unchanged so traversal's merged r23 flips do not regress) --------------------------------------------
			// backDouble: a double tuck that kicks out into an open finish (Kickout: arms sweep wide, legs scissor behind them, the web arm
			// comes up for the catch). round 14: Tuck 1.20 s eased, Kickout 0.60 s at <= ~100 deg/s; catch 1.60 s after the release
			// round 05 (critic r04 gap 1: "0-1 rotations per release, no fast tuck or held pencil/throne"): the double now tucks fast
			// (450-750 deg/s, F3), holds an inverted pencil between the rotations (>= 0.3 s at <= 150 deg/s, F4) and opens out into the
			// reach (F8) -- the owner clip's S3 vocabulary.
			// round 06 (critic r05 gap 2: "~2.2 rotations on the best program; owner clip 1080 deg in 2.8 s; no hold > 0.5 s at <= 150
			// deg/s; rendered peaks > 800 on frontDouble/backLayout/frontPikeSwan"): every long-release program now turns >= 720 deg
			// with exactly one held open shape 0.3-0.5 s, base peaks 510-680 (flip_sim.py) so the fastest tempo variant stays under 800
			// rendered; the residual lean stack is removed by the closed-loop axis correction (WebTravCharacter.cpp). The 360s survive
			// only as the short-air fallback (backSingle) and the wall top-out (wallFront).
			// final round 11 (critic r10 gap 2, 4th round: checker measures ~2 rotations but the READ is "1 rotation + hold" -- the
			// long entry tuck spins the whole first rotation inside one ball, then the pencil stalls, then the second rotation is one
			// more ball): every multi-rotation program now alternates SHORT tuck bursts (<= 0.38 s, none holds a whole rotation) with
			// open shapes that KEEP ROTATING (layout / straddle at ~230-370 deg/s), one F4 hold mid-chain (pencil / swan / throne,
			// 0.32-0.34 s at <= 150 deg/s), no long hold after a rotation. Base peaks 617-714 (flip sim), means 303-365, 7-10 shapes
			// per program, every shape >= 0.22 s (A7: >= 3 frames at 25 fps).
			// final round 12 (critic r11 gap 2: the alternation reads as CONTINUOUS rotation -- the 0.32 s holds never reach a
			// rendered <= 150 deg/s window of >= 0.3 s; r09's held shapes passed at 0.54-0.87 s): the hold segment runs 0.42-0.44 s
			// (barani / corkscrew / fullTwist straddles 0.48-0.54) at the raised hold inertias, while the alternating tuck bursts and
			// rotating open shapes stay (flip sim on the committed tables: base peaks 611-741, means 306-358, program <= 115 deg/s
			// hold windows 0.35-0.50 s at the fastest variant).
			Add(TEXT("backDouble"), -720.f, { {S::Tuck, 0.38f, 0.f, 0.55f, 0.3f}, {S::Layout, 0.28f}, {S::Tuck, 0.35f}, {S::Pencil, 0.44f}, {S::Tuck, 0.35f, 0.f, 0.3f, 0.4f}, {S::Kickout, 0.20f}, {S::Reach, 0.22f} }, 3.5f, 1.5f, 0.2f);
			// front pike into a held inverted swan, a long fast tuck round again, kick out, reach (720 deg; the swan sits mid-rotation
			// so every 330 deg chunk of the render mixes a fast and a slow phase: flip_check F5)
			// round 09 (critic r08 F4: frontPikeSwan's longest <= 150 deg/s hold measured 0.27 s vs the 0.3 s line): the swan hold
			// 0.32 -> 0.38 s (mean rate 720 / 2.32 s = 310 deg/s stays inside F2's 300-500)
			// final round 10: 2.32 -> 2.15 s (entry / exit tightened, holds at the 0.30-0.32 s floor): a double now completes inside
			// the short scripted air windows instead of dying mid-second-rotation at the catch (mean 335 deg/s, base peak 617)
			// final round 12: the hold 0.32 -> 0.48 s (see backDouble), and it moves swan -> pencil: the flipSwan clip's arch
			// breathes +-2-3 deg/frame mid-hold (probe: rendered rate bursts to 170-200 deg/s over the program's 70), which kept
			// breaking F4's <= 150 deg/s windows (0.22-0.24 s measured); flipPencil reads steady (backSingle's pencil holds 0.54 s)
			Add(TEXT("frontPikeSwan"), 720.f, { {S::Pike, 0.38f, 0.f, 0.6f, 0.3f}, {S::Tuck, 0.32f}, {S::Pencil, 0.48f}, {S::Tuck, 0.30f}, {S::Straddle, 0.20f}, {S::Tuck, 0.30f, 0.f, 0.4f, 0.4f}, {S::Kickout, 0.18f}, {S::Reach, 0.20f} }, 3.5f, 1.5f, 0.2f);
			// corkscrew: a layout that turns over while it twists a full turn (arms crossed), tucks through the second rotation, opens
			// into its inverted straddle, tucks, reach (720 deg)
			Add(TEXT("corkscrew"), 720.f, { {S::Layout, 0.2f}, {S::Twist, 0.44f, 360.f}, {S::Tuck, 0.52f, 0.f, 0.3f, 0.3f}, {S::Straddle, 0.48f, 0.f, 0.3f, 0.3f}, {S::Tuck, 0.48f, 0.f, 0.3f, 0.4f}, {S::Reach, 0.20f} }, 4.0f, 1.2f, 0.2f);
			// short air (plain trick release): tuck to inverted, pencil hold, tuck round, reach
			// Tricks C r01: every program's final Reach is >= 0.36 s, so the catch window (CatchOpen 0.16 s before the end) opens only after
			// >= 0.2 s of the open reach -- r01 probe: backSingle's 0.24 s reach was caught 0.08 s in, straight out of a 446 deg/s tuck
			// round 06: backSingle stays the 360 deg short-air fallback (FitFlip's tight-air pick)
			// final round 10: tucks 0.32 -> 0.36/0.34 (its fast variant rendered 883 deg/s -- over F3's 800), reach 0.38 -> 0.32
			// final round 12: pencil hold 0.34 -> 0.44 s
			Add(TEXT("backSingle"), -360.f, { {S::Tuck, 0.36f, 0.f, 0.5f, 0.3f}, {S::Pencil, 0.44f}, {S::Tuck, 0.34f, 0.f, 0.3f, 0.6f}, {S::Reach, 0.32f} });
			// wall-run top-out: front flip over the roof edge, layout on top, throne into the landing
			Add(TEXT("wallFront"), 360.f, { {S::Tuck, 0.28f}, {S::Layout, 0.3f}, {S::Tuck, 0.28f}, {S::Throne, 0.38f} }, 0.f, 0.f);
			// ---- Tricks C round 1 (owner: "look like a gymnast", "many tricks"): the gymnastics vocabulary, built from the same keyed shapes.
			// Every program opens out of its rotation into a slow open shape (Kickout / Straddle / Layout / Reach) before the catch (clean open-out); a
			// twist always exits into a shape keyed out of the twist wrap (Straddle / Layout), never into the Kickout (which starts from the tuck grab); every
			// fast phase is a tuck or pike (the rate follows the shape: F3 / F5). Durations were tuned with tools/tricks/flip_sim.py so the
			// base program peaks <= ~650 deg/s (a fast 0.85x variant stays <= ~770). Twists: a body can only finish a WHOLE number of
			// twists facing along its travel (a half twist lands facing back), so the 180 / 540 programs do their named twist inside the
			// flip and turn the last half in slowly as they open toward the catch (the catch-turn), never as a spring at the attach.
			// Release push (Boost / Up, m/s) 2.0 / 1.0 on every new program (r01 probe: 3.5 / 1.5 on a flip every release took the chain from
			// 39 to 60 m/s in 12 s and through the avenue corner into a facade).
			// front tuck: set, tight tuck, held upright throne mid-way, second tuck, kick out, reach (720 deg in 2.18 s; a slow
			// shape inside every 330 deg chunk: flip_check F5)
			Add(TEXT("frontSingle"), 720.f, { {S::Tuck, 0.42f, 0.f, 0.6f, 0.3f}, {S::Layout, 0.26f}, {S::Tuck, 0.34f}, {S::Throne, 0.44f}, {S::Tuck, 0.34f, 0.f, 0.3f, 0.4f}, {S::Kickout, 0.20f}, {S::Reach, 0.22f} }, 2.0f, 1.0f, 0.2f);
			// front double tuck with a kick-out (the front twin of backDouble); a held upright throne between the rotations
			// (F4, owner clip S6's 0.48 s throne), tucks at 450-750 deg/s (F3); round 11: the layout between the first tucks keeps
			// the open shape rotating through the first rotation's end (the r10 throne-after-the-ball read as the trick being over)
			Add(TEXT("frontDouble"), 720.f, { {S::Tuck, 0.38f, 0.f, 0.55f, 0.3f}, {S::Layout, 0.26f}, {S::Tuck, 0.35f}, {S::Throne, 0.44f}, {S::Tuck, 0.35f, 0.f, 0.3f, 0.4f}, {S::Kickout, 0.20f}, {S::Reach, 0.22f} }, 2.0f, 1.0f, 0.2f);
			// back pike: the body folds at the hips with straight legs (keyed pike), a tucked half-turn, a held pencil, the second
			// tuck round, kick out, reach (720 deg)
			Add(TEXT("backPike"), -720.f, { {S::Pike, 0.44f, 0.f, 0.6f, 0.3f}, {S::Tuck, 0.30f}, {S::Layout, 0.26f}, {S::Pencil, 0.44f}, {S::Tuck, 0.34f, 0.f, 0.4f, 0.4f}, {S::Kickout, 0.20f}, {S::Reach, 0.22f} }, 2.0f, 1.0f, 0.2f);
			// back layout: the layout line keeps its identity through the middle, with a short tuck entry / exit (F3 450-750 deg/s);
			// 720 deg — held layout, fast tuck, a held pencil into the open-out (F4); round 11: the second tuck is split by a
			// straddle that keeps turning (no ball-then-stall read)
			Add(TEXT("backLayout"), -720.f, { {S::Tuck, 0.38f, 0.f, 0.55f, 0.2f}, {S::Layout, 0.44f, 0.f, 0.3f, 0.2f}, {S::Tuck, 0.33f}, {S::Pencil, 0.44f}, {S::Tuck, 0.33f, 0.f, 0.3f, 0.3f}, {S::Straddle, 0.20f}, {S::Reach, 0.22f} }, 2.0f, 1.0f, 0.2f);
			// barani: front pike with a half twist (180 deg, arms wrapped), a tuck through the second rotation, the straddle flings
			// open out of the wrap and turns the last half in toward the catch (720 deg)
			// round 08 (critic r06/r07 adjacent: barani's rendered peak sat at 1063 deg/s both rounds -- the twist's roll couples into
			// the measured body axis; a longer first twist (409 deg/s, still above the 250 deg/s correction freeze) pulls the rendered
			// peak down without moving the 720 deg total out of F2's 300-500 deg/s band: 720 / 2.34 s = 308)
			// final round 10 (r09: STILL 1018 rendered): the twist segments slow further (0.44 -> 0.54 s, the straddle catch-turn
			// 0.38 -> 0.46 s; eased peaks 643 -> 523 / 744 -> 614 deg/s) and the axis correction now re-bases at a twist's end
			// (WebTravCharacter.cpp) instead of discharging the stale error into the next tuck
			Add(TEXT("barani"), 720.f, { {S::Pike, 0.32f, 0.f, 0.5f, 0.3f}, {S::Twist, 0.50f, 180.f}, {S::Tuck, 0.39f}, {S::Straddle, 0.51f, 180.f, 0.25f, 0.25f}, {S::Tuck, 0.44f, 0.f, 0.4f, 0.4f}, {S::Reach, 0.19f} }, 2.0f, 1.0f, 0.22f);
			// back full: a back layout with one full twist (360 deg) in the middle of the rotation, short tucks at the entry / exit;
			// 720 deg — the second rotation opens into a held straddle
			Add(TEXT("fullTwist"), -720.f, { {S::Tuck, 0.34f, 0.f, 0.4f, 0.2f}, {S::Layout, 0.21f, 0.f, 0.3f}, {S::Twist, 0.54f, 360.f}, {S::Straddle, 0.47f, 0.f, 0.3f, 0.3f}, {S::Tuck, 0.60f, 0.f, 0.3f, 0.3f}, {S::Reach, 0.19f} }, 2.0f, 1.0f, 0.22f);
			// rudi: a tuck wraps one and a half twists (540 deg), the straddle opens out of the wrap and turns the last half in,
			// a second tuck and a held pencil finish the second rotation (720 deg)
			Add(TEXT("rudi"), 720.f, { {S::Tuck, 0.33f, 0.f, 0.5f, 0.3f}, {S::Twist, 0.46f, 540.f}, {S::Straddle, 0.24f, 180.f}, {S::Tuck, 0.28f}, {S::Pencil, 0.42f}, {S::Tuck, 0.44f, 0.f, 0.4f, 0.4f}, {S::Reach, 0.18f} }, 2.0f, 1.0f, 0.22f);
			// chain: three back rotations in one release with a shape per rotation (owner clip S3: tuck -> layout -> tuck -> straddle -> tuck
			// -> open, 3 rotations in 2.8 s, ~385 deg/s mean); the middle rotation holds an inverted pencil (owner S3 9.72-9.84, F4);
			// round 11: every rotation is delimited by a rotating open shape (no long ball, no post-rotation stall), 2.96 s, mean 365
			Add(TEXT("backTripleChain"), -1080.f, { {S::Tuck, 0.42f, 0.f, 0.55f, 0.3f}, {S::Layout, 0.30f}, {S::Tuck, 0.36f}, {S::Straddle, 0.26f}, {S::Tuck, 0.36f}, {S::Pencil, 0.44f}, {S::Tuck, 0.36f, 0.f, 0.3f, 0.4f}, {S::Layout, 0.24f}, {S::Kickout, 0.18f}, {S::Reach, 0.18f} }, 2.0f, 1.0f, 0.2f);
			// Four-fix pass: three deliberate catch families, rather than replaying Reach for every trick.
			// Keep the rotation/hold tables intact: this selects only the authored terminal body silhouette.
			for (FWebFlipProgram& F : P)
			{
				if (F.Name == FName(TEXT("frontSingle")) || F.Name == FName(TEXT("frontDouble")) || F.Name == FName(TEXT("frontPikeSwan")))
					F.CatchShape = S::Throne;
				else if (F.Name == FName(TEXT("corkscrew")) || F.Name == FName(TEXT("barani")) || F.Name == FName(TEXT("fullTwist")))
					F.CatchShape = S::Straddle;
			}
			return P;
		}

		float SegStart(const FWebFlipProgram& P, int32 K) { float T = 0.f; for (int32 I = 0; I < K; ++I) T += P.Segs[I].Dur; return T; }
		int32 SegAt(const FWebFlipProgram& P, float T)
		{
			float Acc = 0.f;
			for (int32 I = 0; I < P.Segs.Num(); ++I) { Acc += P.Segs[I].Dur; if (T < Acc) return I; }
			return P.Segs.Num() - 1;
		}
		// shape blend at time T: (A, B, W) and hold progress of A / B
		void ShapeAt(const FWebFlipProgram& P, float T, EWebFlipShape& A, EWebFlipShape& B, float& W, float& HA, float& HB)
		{
			const float Dur = P.Dur();
			T = FMath::Clamp(T, 0.f, Dur - 1e-4f);
			const int32 K = SegAt(P, T);
			const float S0 = SegStart(P, K), S1 = S0 + P.Segs[K].Dur;
			auto Hold = [&](int32 J, float Tt) { const float St = SegStart(P, J); return FMath::Clamp((Tt - St) / FMath::Max(0.05f, P.Segs[J].Dur), 0.f, 1.f); };
			if (K > 0 && T < S0 + BPost)
			{
				A = P.Segs[K - 1].Shape; B = P.Segs[K].Shape; W = Smooth((T - (S0 - BPre)) / (BPre + BPost));
				HA = 1.f; HB = Hold(K, T);
			}
			else if (K + 1 < P.Segs.Num() && T > S1 - BPre)
			{
				A = P.Segs[K].Shape; B = P.Segs[K + 1].Shape; W = Smooth((T - (S1 - BPre)) / (BPre + BPost));
				HA = Hold(K, T); HB = 0.f;
			}
			else { A = B = P.Segs[K].Shape; W = 0.f; HA = HB = Hold(K, T); }
			if (P.Segs.Last().Shape == EWebFlipShape::Reach && P.CatchShape != EWebFlipShape::Reach)
			{
				// The selected clips' established open keys are around u=.3. Enter those keys directly;
				// do not scrub Straddle all the way into its later tuck-up or add a random end pose.
				auto Catch = [&](EWebFlipShape& S, float& H)
				{
					if (S == EWebFlipShape::Reach) { S = P.CatchShape; H = 0.18f + 0.18f * H; }
				};
				Catch(A, HA); Catch(B, HB);
			}
		}
		// round 14: segment K's inertia at time T including its end ease (see FWebFlipSeg::EaseIn / EaseOut)
		constexpr float EaseW = 0.45f;
		float SegInertia(const FWebFlipProgram& P, int32 K, float T)
		{
			const FWebFlipSeg& S = P.Segs[K];
			const float U = FMath::Clamp((T - SegStart(P, K)) / FMath::Max(0.05f, S.Dur), 0.f, 1.f);
			return Inertia(S.Shape) * (1.f + S.EaseIn * (1.f - Smooth(U / EaseW)) + S.EaseOut * (1.f - Smooth((1.f - U) / EaseW)));
		}
		float InertiaAt(const FWebFlipProgram& P, float T)
		{
			const float Dur = P.Dur();
			T = FMath::Clamp(T, 0.f, Dur - 1e-4f);
			const int32 K = SegAt(P, T);
			const float S0 = SegStart(P, K), S1 = S0 + P.Segs[K].Dur;
			if (K > 0 && T < S0 + BPost)
				return FMath::Lerp(SegInertia(P, K - 1, T), SegInertia(P, K, T), Smooth((T - (S0 - BPre)) / (BPre + BPost)));
			if (K + 1 < P.Segs.Num() && T > S1 - BPre)
				return FMath::Lerp(SegInertia(P, K, T), SegInertia(P, K + 1, T), Smooth((T - (S1 - BPre)) / (BPre + BPost)));
			return SegInertia(P, K, T);
		}
		float Env(float T, float Dur)
		{
			const float In = 0.35f + 0.65f * Smooth(T / EnvIn);
			const float Out = 0.12f + 0.88f * Smooth((Dur - T) / EnvOut);
			return In * Out;
		}
		const FTable& Table(const FWebFlipProgram& P)
		{
			static TMap<const FWebFlipProgram*, FTable> Cache;
			if (const FTable* T = Cache.Find(&P)) { if (T->Ver == P.Ver) return *T; }
			FTable Tb;
			Tb.Ver = P.Ver;
			const float Dur = P.Dur();
			const int32 N = FMath::CeilToInt(Dur * TableHz) + 1;
			Tb.G.SetNum(N + 1);
			double Acc = 0.0;
			Tb.G[0] = 0.f;
			for (int32 I = 1; I <= N; ++I)
			{
				const float Tm = (I - 0.5f) / TableHz;
				Acc += Env(Tm, Dur) / InertiaAt(P, Tm) / TableHz;
				Tb.G[I] = float(Acc);
			}
			const float GEnd = Tb.G[FMath::Min(N, FMath::CeilToInt(Dur * TableHz))];
			Tb.L = GEnd > 1e-6f ? P.PitchDeg / GEnd : 0.f;
			for (float& V : Tb.G) V *= Tb.L;
			return Cache.Add(&P, Tb);
		}
	}

	const TCHAR* ShapeClip(EWebFlipShape S)
	{
		static const TCHAR* C[] = { TEXT("flipTuck"), TEXT("flipPike"), TEXT("flipLayout"), TEXT("flipSwan"), TEXT("flipPencil"),
			TEXT("flipStraddle"), TEXT("flipThrone"), TEXT("flipTwist"), TEXT("flipReach"), TEXT("flipKickout") };
		static_assert(UE_ARRAY_COUNT(C) == int32(EWebFlipShape::Num), "one clip per shape");
		return C[FMath::Clamp(int32(S), 0, int32(EWebFlipShape::Num) - 1)];
	}
	const TCHAR* ShapeName(EWebFlipShape S) { return ShapeClip(S) + 4; }

	// round 14: rendered hips->head axis minus the program pitch while each shape is held (probe f4, 60 fps; + = head forward)
	float ShapeAxisDeg(EWebFlipShape S)
	{
		switch (S)
		{
		case EWebFlipShape::Tuck: return 20.f;
		case EWebFlipShape::Pike: return 22.f;
		case EWebFlipShape::Swan: return -15.f;
		case EWebFlipShape::Kickout: return -6.f;
		case EWebFlipShape::Reach: return 3.f;
		default: return 0.f;
		}
	}

	// round 18: vertical extent (m, joints + 0.2 m pad) a shape reaches during its hold (flip_motion_sim.py z-extent): the trick camera backs
	// out ahead of an opening shape so the hero stays inside TC-C's .12-.36 of the frame at 5.0-6.4 m (TC4)
	float ShapeExtent(EWebFlipShape S)
	{
		switch (S)
		{
		case EWebFlipShape::Tuck: return 0.95f;
		case EWebFlipShape::Pike: return 1.3f;
		case EWebFlipShape::Twist: return 1.4f;
		case EWebFlipShape::Throne: return 1.5f;
		case EWebFlipShape::Reach: return 1.8f;
		default: return 2.0f; // layout, swan, pencil, straddle, kickout
		}
	}

	namespace
	{
		// one variant slot per base program (stable addresses: the rate-table cache and callers hold pointers)
		TArray<FWebFlipProgram>& Variants()
		{
			static TArray<FWebFlipProgram> V;
			if (V.Num() != Programs().Num()) { V = Programs(); for (FWebFlipProgram& P : V) P.Ver = -2; }
			return V;
		}
	}
	const FWebFlipProgram* FindBase(FName Name)
	{
		for (const FWebFlipProgram& P : Programs()) { if (P.Name == Name) return &P; }
		return nullptr;
	}
	const FWebFlipProgram* Find(FName Name)
	{
		const TArray<FWebFlipProgram>& B = Programs();
		for (int32 I = 0; I < B.Num(); ++I)
		{
			if (B[I].Name != Name) continue;
			const FWebFlipProgram& V = Variants()[I];
			return (bVariants && V.Ver >= 0) ? &V : &B[I];
		}
		return nullptr;
	}
	const FWebFlipProgram* MakeVariant(FName Name, float Scale, uint32 Seed)
	{
		const TArray<FWebFlipProgram>& B = Programs();
		static int32 VerCounter = 0;
		static const bool bTempoParsed = []() { int32 V = 1; if (FParse::Value(FCommandLine::Get(), TEXT("-WHTrickTempo="), V)) bTempo = V != 0; return true; }();
		(void)bTempoParsed;
		for (int32 I = 0; I < B.Num(); ++I)
		{
			if (B[I].Name != Name) continue;
			if (!bVariants) return &B[I];
			FWebFlipProgram& V = Variants()[I];
			V = B[I];
			FRandomStream R{ int32(Seed) };
			// Tricks C r01 (PLAN §4: same-type durations vary +-10-20 %; r23 flow flips at ~40 m/s all came out 0.86-0.99x): half of the
			// caller's release-speed / apex term plus a per-instance TEMPO -- this performance is a slow, floated one (+10-16 %) or a snappy one
			// (-10-13 %), alternating at random; the fast side is capped at 0.85x so a tuck never passes ~800 deg/s by much (FLIPS_SPEC F3)
			// r01 resume (probe: frontSingle / barani drew the same sign twice -> 12 / 65 deg/s apart): the first instance of a program picks the
			// sign at random, every later instance of the SAME program takes the opposite one, so a repeat is always the other performance
			static TArray<int32> LastSign; LastSign.SetNumZeroed(B.Num());
			const float Coin = R.FRand();
			const float Tempo = LastSign[I] != 0 ? -float(LastSign[I]) : (Coin < 0.5f ? -1.f : 1.f);
			LastSign[I] = Tempo > 0.f ? 1 : -1;
			const float TempoMag = Tempo > 0.f ? 0.10f + 0.06f * R.FRand() : 0.10f + 0.03f * R.FRand();
			// round 06: multi-rotation programs (>= 700 deg) run a tighter tempo band so the fast side never passes ~760 deg/s
			// (F3, critic r05's > 800 rendered peaks) and the slow side's mean rate stays over 300 deg/s (F2)
			// final round 10: the retimed programs run hotter means, so the band narrows to 0.92-1.03 (the r08/r09 slow variants
			// dropped the rendered mean under F2's 300 floor -- barani 291 -- and the fast ones stacked over 800)
			// final round 11: 0.92-1.03 -> 0.95-1.01 -- the r11 alternating programs peak ~690-735 base, so the fast variant plus
			// the shape-transition stack stays under F3's 800, and the slowest variant's mean stays >= 300 (frontPikeSwan 303/1.01)
			const bool bMulti = FMath::Abs(B[I].PitchDeg) >= 700.f;
			const float ScLo = bMulti ? 0.95f : 0.85f, ScHi = bMulti ? 1.01f : 1.20f;
			const float Sc = bTempo ? FMath::Clamp(1.f + 0.5f * (FMath::Clamp(Scale, 0.78f, 1.22f) - 1.f) + Tempo * TempoMag, ScLo, ScHi)
				: FMath::Clamp(Scale, 0.78f, 1.22f);
			// each segment its own jitter, renormalised so the total is exactly Sc x the base duration
			float Sum0 = 0.f, Sum1 = 0.f;
			for (FWebFlipSeg& Sg : V.Segs) { Sum0 += Sg.Dur; Sg.Dur *= 0.92f + 0.16f * R.FRand(); Sum1 += Sg.Dur; }
			for (FWebFlipSeg& Sg : V.Segs)
			{
				Sg.Dur *= Sc * Sum0 / FMath::Max(Sum1, 1e-3f);
				Sg.EaseIn = FMath::Max(0.f, Sg.EaseIn * (0.8f + 0.4f * R.FRand()));
				Sg.EaseOut = FMath::Max(0.f, Sg.EaseOut * (0.8f + 0.4f * R.FRand()));
			}
			V.CatchOpen = B[I].CatchOpen * Sc;
			// round 06 (F11: measured leg lag 0.067-0.158 s vs the 0.05-0.12 target): the measured lag is Lead + Lag (the upper-body
			// shape column switches Lead ahead, the legs' column Lag behind) -- narrowed so the sum lands mid-band
			V.Lead = FlipLead * (0.5f + 1.5f * R.FRand());   // 0.01-0.05 s: the arms open / close earlier or later per instance
			V.Lag = FlipLag * (0.8f + 0.5f * R.FRand());      // 0.044-0.072 s
			V.Scale = Sc;
			V.Ver = ++VerCounter;
			return &V;
		}
		return nullptr;
	}
	const TArray<FName>& ReleasePrograms()
	{
		static TArray<FName> N;
		if (!N.Num())
		{
			for (const TCHAR* S : { TEXT("backSingle"), TEXT("frontSingle"), TEXT("backPike"), TEXT("barani"), TEXT("backLayout"), TEXT("frontDouble"),
				TEXT("fullTwist"), TEXT("frontPikeSwan"), TEXT("backDouble"), TEXT("rudi"), TEXT("corkscrew"), TEXT("backTripleChain") }) N.Add(FName(S));
		}
		return N;
	}
	FName ChooseForInput(float StickFwd, float StickLat, int32 K, float AirS, FName Last)
	{
		static const TCHAR* Front[] = { TEXT("frontDouble"), TEXT("frontPikeSwan"), TEXT("barani"), TEXT("frontSingle"), TEXT("corkscrew"), TEXT("rudi") };
		static const TCHAR* Back[] = { TEXT("backDouble"), TEXT("backTripleChain"), TEXT("backPike"), TEXT("backSingle"), TEXT("backLayout"), TEXT("fullTwist") };
		static const TCHAR* Twist[] = { TEXT("barani"), TEXT("fullTwist"), TEXT("corkscrew"), TEXT("rudi") };
		TArray<FName> Pool;
		const float Mag = FMath::Sqrt(StickFwd * StickFwd + StickLat * StickLat);
		if (Mag < 0.35f) Pool = ReleasePrograms();
		else if (FMath::Abs(StickLat) > FMath::Abs(StickFwd)) { for (const TCHAR* S : Twist) Pool.Add(FName(S)); }
		else if (StickFwd > 0.f) { for (const TCHAR* S : Front) Pool.Add(FName(S)); }
		else { for (const TCHAR* S : Back) Pool.Add(FName(S)); }
		// the first program in the cycle (from K) that fits the air and is not a repeat; else the shortest that fits; else none
		FName Shortest = NAME_None; float ShortT = 1e9f;
		for (int32 I = 0; I < Pool.Num(); ++I)
		{
			const FName N = Pool[(K + I) % Pool.Num()];
			const FWebFlipProgram* P = FindBase(N);
			if (!P) continue;
			const bool bFits = AirS <= 0.f || P->CatchT() * 1.15f <= AirS;
			if (bFits && N != Last) return N;
			if (P->CatchT() < ShortT && N != Last) { ShortT = P->CatchT(); Shortest = N; }
		}
		return (AirS <= 0.f || ShortT * 1.15f <= AirS) ? Shortest : NAME_None;
	}
	const TArray<FName>& Names()
	{
		static TArray<FName> N;
		if (!N.Num()) for (const FWebFlipProgram& P : Programs()) N.Add(P.Name);
		return N;
	}

	FQuat PoseRotation(const FWebFlipPose& Pose, const FVector& PoseAxis, float EntryW, float Side)
	{
		const FQuat TwistQ(FVector(0, 0, 1), FMath::DegreesToRadians(double(Pose.TwistDeg) * Side));
		// First align the evaluated shape's actual long axis. Twisting the nominal frame before compensating
		// only its pitch made an arched/tucked shape orbit sideways as well as twist, adding real axis speed.
		// This rigid correction preserves every joint angle and lets the existing twist turn ABOUT that axis.
		const FQuat AlignQ = FQuat::FindBetweenNormals(PoseAxis, FVector(0, 0, 1));
		const FQuat ShapeQ = FQuat::Slerp(FQuat::Identity, AlignQ, FMath::Clamp(EntryW, 0.f, 1.f));
		return FQuat(FVector(0, 1, 0), FMath::DegreesToRadians(double(Pose.PitchDeg))) * TwistQ * ShapeQ;
	}

	FWebFlipPose Sample(const FWebFlipProgram& P, float T)
	{
		FWebFlipPose O;
		const float Dur = P.Dur();
		if (Dur <= 0.f) return O;
		O.bValid = true;
		const FTable& Tb = Table(P);
		const float Tc = FMath::Clamp(T, 0.f, Dur);
		const float X = Tc * TableHz;
		const int32 I0 = FMath::Clamp(FMath::FloorToInt(X), 0, Tb.G.Num() - 2);
		const float F = FMath::Clamp(X - I0, 0.f, 1.f);
		O.PitchDeg = FMath::Lerp(Tb.G[I0], Tb.G[I0 + 1], F);
		if (Tc >= Dur - 1e-4f) O.PitchDeg = P.PitchDeg;
		O.PitchRate = T < Dur ? Tb.L * Env(Tc, Dur) / InertiaAt(P, Tc) : 0.f;
		// twist: eased inside its own segments
		float Tw = 0.f, St = 0.f;
		for (const FWebFlipSeg& S : P.Segs)
		{
			if (S.TwistDeg != 0.f)
			{
				const float U = FMath::Clamp((Tc - St) / FMath::Max(0.05f, S.Dur), 0.f, 1.f);
				Tw += S.TwistDeg * 0.5f * (1.f - FMath::Cos(PI * U));
			}
			St += S.Dur;
		}
		O.TwistDeg = Tw;
		O.Seg = SegAt(P, Tc);
		ShapeAt(P, T + (P.Lead >= 0.f ? P.Lead : FlipLead), O.A, O.B, O.W, O.HoldA, O.HoldB);
		O.AxisOffDeg = FMath::Lerp(ShapeAxisDeg(O.A), ShapeAxisDeg(O.B), O.W);
		ShapeAt(P, T - (P.Lag >= 0.f ? P.Lag : FlipLag), O.LA, O.LB, O.LW, O.LHoldA, O.LHoldB);
		// r01 resume (L: a program that runs out before the web catches held its final reach still -- backLayout 0.01-0.06 m per 0.1 s):
		// past the end the reach plays back and forth between u 1 and .45 (its scissor / free-arm swing) until the traversal ends the flip
		if (P.Segs.Num() && (P.Segs.Last().Shape == EWebFlipShape::Reach || P.Segs.Last().Shape == EWebFlipShape::Kickout))
		{
			auto Pong = [](float Ov) { const float X = FMath::Fmod(Ov / 0.25f, 2.f); return 1.f - 0.55f * (1.f - FMath::Abs(1.f - X)); };
			const float OvU = T + (P.Lead >= 0.f ? P.Lead : FlipLead) - Dur, OvL = T - (P.Lag >= 0.f ? P.Lag : FlipLag) - Dur;
			auto CatchHold = [&](float Ov) { const float U = Pong(Ov); return P.CatchShape == EWebFlipShape::Reach ? U : 0.18f + 0.18f * U; };
			if (OvU > 0.f && O.W <= 0.f) O.HoldA = O.HoldB = CatchHold(OvU);
			if (OvL > 0.f && O.LW <= 0.f) O.LHoldA = O.LHoldB = CatchHold(OvL);
		}
		return O;
	}
}

// ---- Tricks C round 1: rendered-pose logger (opt-in, -WHTrickPose=<csv path>). Once per engine frame (OnEndFrame) it writes the hero's
// world bone positions (cm) and the head / chest bone axes for the gymnast-shape checks in tools/tricks/pose_check.py (tuck grip, layout
// hip / knee angles, pointed toes, head spot). It reads the pawn only; nothing in the traversal or the anim instance is changed by it.
namespace WebFlips
{
	namespace
	{
		struct FPoseLog
		{
			FString Path;
			TArray<FString> Rows;
			bool bInit = false, bOn = false, bHeader = false;
			double T0 = -1.0;
			static const TArray<FName>& Bones()
			{
				static TArray<FName> B;
				if (!B.Num())
				{
					for (const TCHAR* N : { TEXT("hips"), TEXT("spine2"), TEXT("neck"), TEXT("head"), TEXT("upperArm_L"), TEXT("forearm_L"), TEXT("hand_L"),
						TEXT("upperArm_R"), TEXT("forearm_R"), TEXT("hand_R"), TEXT("thigh_L"), TEXT("shin_L"), TEXT("foot_L"), TEXT("toe_L"),
						TEXT("thigh_R"), TEXT("shin_R"), TEXT("foot_R"), TEXT("toe_R") }) B.Add(FName(N));
				}
				return B;
			}
			void Flush()
			{
				if (!Rows.Num() || Path.IsEmpty()) return;
				FString Out;
				for (const FString& R : Rows) { Out += R; Out += TEXT("\n"); }
				FFileHelper::SaveStringToFile(Out, *Path, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM, &IFileManager::Get(), bHeader ? FILEWRITE_Append : FILEWRITE_None);
				bHeader = true;
				Rows.Reset();
			}
			// -WHTrickDumpFrom=<s> -WHTrickDumpTo=<s> (sequence seconds, i.e. world time minus the -WHTravPreroll pre-roll and one frame):
			// with -dumpmovie, movie frames are written only for this window (r.DumpingMovie toggled per frame), so a long fixed-step
			// capture can be rendered in segments of one deterministic run (r01: background-priority PNG dumps ran at ~1 frame/s)
			float DumpFrom = -1.f, DumpTo = -1.f, Preroll = 0.f, Warm = -1.f;
			bool bDumpWin = false, bDumpWas = false;
			void Tick()
			{
				if (!bInit)
				{
					bInit = true; bOn = FParse::Value(FCommandLine::Get(), TEXT("-WHTrickPose="), Path) && !Path.IsEmpty();
					bDumpWin = FParse::Value(FCommandLine::Get(), TEXT("-WHTrickDumpFrom="), DumpFrom) | FParse::Value(FCommandLine::Get(), TEXT("-WHTrickDumpTo="), DumpTo);
					FParse::Value(FCommandLine::Get(), TEXT("-WHTravPreroll="), Preroll);
					FParse::Value(FCommandLine::Get(), TEXT("-WHTrickWarm="), Warm);
					if (DumpTo < 0.f) DumpTo = 1e9f;
				}
				if (!GEngine) return;
				UWorld* W = nullptr;
				for (const FWorldContext& C : GEngine->GetWorldContexts())
				{
					if ((C.WorldType == EWorldType::Game || C.WorldType == EWorldType::PIE) && C.World()) { W = C.World(); break; }
				}
				if (bDumpWin)
				{
					// the flag set at the end of frame N decides whether frame N+1 is written: test N+1's sequence time
					const double SeqNext = W ? W->GetTimeSeconds() - double(Preroll) - 1.0 / 60.0 + 1.0 / 60.0 : -1.0;
					const bool bIn = W && SeqNext >= double(DumpFrom) - 1e-4 && SeqNext < double(DumpTo) - 1e-4;
					GIsDumpingMovie = bIn ? -1 : 0;
					if (bIn != bDumpWas) UE_LOG(LogTemp, Display, TEXT("WH_TRICK_DUMP %s at next-frame seq t %.4f"), bIn ? TEXT("on") : TEXT("off"), SeqNext);
					bDumpWas = bIn;
					// r01 resume (-WHTrickWarm=<s>): the world is not rendered outside [From - Warm, To) -- the simulation, animation (the hero
					// mesh ticks its pose when unseen) and telemetry run unchanged, only the GPU work of frames nobody keeps is skipped; Warm s
					// of rendered frames before the window let texture streaming, Lumen and TSR history settle before the first kept frame
					if (Warm >= 0.f && GEngine->GameViewport)
					{
						const bool bDraw = !W || (SeqNext >= double(DumpFrom - Warm) - 1e-4 && SeqNext < double(DumpTo) - 1e-4);
						if (bool(GEngine->GameViewport->bDisableWorldRendering) == bDraw)
						{
							GEngine->GameViewport->bDisableWorldRendering = !bDraw;
							UE_LOG(LogTemp, Display, TEXT("WH_TRICK_RENDER %s at next-frame seq t %.4f"), bDraw ? TEXT("on") : TEXT("off"), SeqNext);
						}
					}
				}
				if (!bOn || !W) return;
				APlayerController* PC = W->GetFirstPlayerController();
				ACharacter* Ch = PC ? Cast<ACharacter>(PC->GetPawn()) : nullptr;
				const UWebTraversalComponent* Tr = Ch ? Ch->FindComponentByClass<UWebTraversalComponent>() : nullptr;
				USkeletalMeshComponent* M = Ch ? Ch->GetMesh() : nullptr;
				if (!Tr || !M || !M->GetSkeletalMeshAsset()) return;
				if (Rows.Num() == 0 && !bHeader)
				{
					FString H = TEXT("frame,wt,mode,sub,anim_t,trick,trick_side,x_m,y_m,z_m,vx,vy,vz");
					for (const FName& B : Bones()) { const FString N = B.ToString(); H += FString::Printf(TEXT(",%s_x,%s_y,%s_z"), *N, *N, *N); }
					H += TEXT(",head_fx,head_fy,head_fz,head_ux,head_uy,head_uz,chest_fx,chest_fy,chest_fz,chest_ux,chest_uy,chest_uz,pelvis_fx,pelvis_fy,pelvis_fz");
					Rows.Add(H);
				}
				const FWebTravAnim& A = Tr->Anim;
				const FVector P = Tr->PosM();
				FString R = FString::Printf(TEXT("%llu,%.4f,%d,%s,%.4f,%s,%.0f,%.3f,%.3f,%.3f,%.2f,%.2f,%.2f"), (unsigned long long)GFrameCounter, W->GetTimeSeconds(),
					int32(A.Mode), *A.Sub.ToString(), A.T, A.Trick.IsNone() ? TEXT("") : *A.Trick.ToString(), A.TrickSide, P.X, P.Y, P.Z,
					A.Velocity.X / 100.0, A.Velocity.Y / 100.0, A.Velocity.Z / 100.0);
				for (const FName& B : Bones())
				{
					if (M->GetBoneIndex(B) == INDEX_NONE) { R += TEXT(",,,"); continue; }
					const FVector L = M->GetBoneLocation(B);
					R += FString::Printf(TEXT(",%.2f,%.2f,%.2f"), L.X, L.Y, L.Z);
				}
				// bone axes in world space: the imported (Blender) bones run along their local Y; X / Z span the bone's cross section
				auto Axes = [&](const TCHAR* N, bool bUp)
				{
					const FName B(N);
					if (M->GetBoneIndex(B) == INDEX_NONE) { R += bUp ? TEXT(",,,,,,") : TEXT(",,,"); return; }
					const FQuat Q = M->GetBoneQuaternion(B, EBoneSpaces::WorldSpace);
					const FVector Ax = Q.GetAxisX(), Ay = Q.GetAxisY(), Az = Q.GetAxisZ();
					R += FString::Printf(TEXT(",%.4f,%.4f,%.4f"), Az.X, Az.Y, Az.Z);
					if (bUp) R += FString::Printf(TEXT(",%.4f,%.4f,%.4f"), Ay.X, Ay.Y, Ay.Z);
					(void)Ax;
				};
				Axes(TEXT("head"), true); Axes(TEXT("spine2"), true); Axes(TEXT("hips"), false);
				Rows.Add(R);
				if (Rows.Num() >= 240) Flush();
			}
		};
		FPoseLog& PoseLog() { static FPoseLog L; return L; }
		struct FPoseLogReg
		{
			FPoseLogReg()
			{
				FCoreDelegates::OnEndFrame.AddLambda([]() { PoseLog().Tick(); });
				FCoreDelegates::OnPreExit.AddLambda([]() { PoseLog().Flush(); });
				FCoreDelegates::OnEnginePreExit.AddLambda([]() { PoseLog().Flush(); });
			}
		};
		FPoseLogReg GPoseLogReg;
	}
}
