// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// Piece P3 (traversal + camera): shared types. Port of src/player/traversal/anim.js (C1 contract) and the
// input struct of src/player/input.js.
//
// Units: the traversal simulation runs in METRES (browser constants unchanged), UE axes (Z up, X forward, Y right).
// World positions exposed to Blueprint / AnimBP (FWebTravAnim) are in CENTIMETRES like the rest of Unreal.
#pragma once

#include "CoreMinimal.h"
#include "WebTravTypes.generated.h"

/** Traversal modes (browser traversal.js `s.mode`; `Land` = ground while a landing recovery plays, C1 anim.mode). */
UENUM(BlueprintType)
enum class EWebTravMode : uint8
{
	Ground,
	Air,
	Swing,
	Zip,
	Perch,
	Wall,
	Land,
};

/**
 * One frame of player input (browser input.js poll() state). Held flags + edge flags ("Pressed").
 * move: X = right, Y = forward (-1..1). look: camera orbit this frame in radians (yaw right +, pitch down +).
 */
USTRUCT(BlueprintType)
struct WEBHOMAGE_API FWebTravInput
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") FVector2D Move = FVector2D::ZeroVector;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") FVector2D Look = FVector2D::ZeroVector;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") bool bSwing = false;   // RMB / R2
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") bool bJump = false;    // Space / A
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") bool bSprint = false;  // Shift / R2: parkour + wall run
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") bool bZip = false;     // E / MMB / Y / L2+R2
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") bool bDrop = false;    // C / Ctrl / B: drop + dive
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") bool bQuick = false;   // Q / L1: quick web boost
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") bool bTrick = false;   // F / X: air trick (round 04: tricks only on input)
	/** Round 11: requested flip program(s) for the next trick, comma-separated and cycled per trick (script key "flip"; empty = automatic). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") FString FlipReq;

	// edge flags (set by the sampler: held now, not held last frame). Cleared by traversal after the first substep.
	bool bSwingPressed = false, bJumpPressed = false, bZipPressed = false, bDropPressed = false, bQuickPressed = false, bSprintPressed = false, bTrickPressed = false;

	/** Fill the Pressed flags from the previous frame's held state (input.js poll()). */
	void ComputeEdges(const FWebTravInput& Prev)
	{
		bSwingPressed = bSwing && !Prev.bSwing;
		bJumpPressed = bJump && !Prev.bJump;
		bZipPressed = bZip && !Prev.bZip;
		bDropPressed = bDrop && !Prev.bDrop;
		bQuickPressed = bQuick && !Prev.bQuick;
		bSprintPressed = bSprint && !Prev.bSprint;
		bTrickPressed = bTrick && !Prev.bTrick;
	}
};

/** C1 swing block. */
USTRUCT(BlueprintType)
struct WEBHOMAGE_API FWebTravAnimSwing
{
	GENERATED_BODY()
	/** -1 back of the arc .. +1 front (atan2(along, below) / 1.25). */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float Phase = 0.f;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float Bank = 0.f;
	/** 0..1 web load (F_T relative to 2.6 g). */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float Tension = 0.f;
	/** Anchor point on the building (world, cm). */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FVector Anchor = FVector::ZeroVector;
	/** true = right hand holds the web. */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") bool bRightHand = true;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float RopeLengthCm = 0.f;
	/** Rope angle from straight down (rad; +pi/2 = level in front). */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float Angle = 0.f;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float Kick = 0.f;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") int32 Chain = 0;
};

/** C1 zip block. */
USTRUCT(BlueprintType)
struct WEBHOMAGE_API FWebTravAnimZip
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FVector Target = FVector::ZeroVector;
	/** Flight progress 0..1 (time fraction). */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float T = 0.f;
	/** fire | flight | catch | '' */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FName Phase;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") bool bWebs = false;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float Pitch = 0.f;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FVector Dir = FVector::ForwardVector;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") bool bDash = false;
};

/** C1 wall block. */
USTRUCT(BlueprintType)
struct WEBHOMAGE_API FWebTravAnimWall
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FVector Normal = FVector::ForwardVector;
	/** x right, y up (-1..1). */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FVector2D Move = FVector2D::ZeroVector;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") bool bFast = false;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float Phase = 0.f;
	/** 1 = run cycle rotated onto the wall, 0 = crawl frame. */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float RunK = 0.f;
	/** Round 19: wall surface point at body height (world cm) and the travel direction along the wall (unit, world). */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FVector Point = FVector::ZeroVector;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FVector Up = FVector::UpVector;
	/** Round 22: 0..1 blend into the upright side run (runner side-on to the facade, chest along the run line). */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float SideUp = 0.f;
};

/** C1 perch block. */
USTRUCT(BlueprintType)
struct WEBHOMAGE_API FWebTravAnimPerch
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FVector Point = FVector::ZeroVector;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FVector Normal = FVector::ForwardVector;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FName Kind;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FVector Impact = FVector::ZeroVector;
};

/**
 * Invincible flight block (2026-10-15, UWHFlightComponent). bActive = the flight controller owns the body this frame.
 * Flight sub-states are written to FWebTravAnim::Sub (mode Air unless noted):
 *   takeoff (crouch-launch off the ground, ~0.35 s) | hover (upright, slow) | fly (forward flight, superman line) |
 *   boost (fly above the boost speed) | brake (instant stop, legs swing forward) | dash (short burst) |
 *   slam (dive straight down for a superhero landing) | breach (passing through a building) |
 *   landHero (mode Land: superhero landing, one knee + fist down, ~0.9 s) ; walking on the ground keeps the ground subs.
 */
USTRUCT(BlueprintType)
struct WEBHOMAGE_API FWebTravAnimFlight
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly, Category="Flight") bool bActive = false;
	/** 0 hover .. 1 at cruise speed .. up to 2 at max boost speed (speed / cruise, clamped). */
	UPROPERTY(BlueprintReadOnly, Category="Flight") float SpeedK = 0.f;
	/** Bank (rad, + = rolling right into a right turn) and body pitch (rad, + = nose down) the controller applied to BodyQ. */
	UPROPERTY(BlueprintReadOnly, Category="Flight") float Bank = 0.f;
	UPROPERTY(BlueprintReadOnly, Category="Flight") float Pitch = 0.f;
	/** Stick in the body frame (x right, y forward), for hover leans. */
	UPROPERTY(BlueprintReadOnly, Category="Flight") FVector2D Stick = FVector2D::ZeroVector;
	/** Vertical intent -1 (descend) .. +1 (ascend). */
	UPROPERTY(BlueprintReadOnly, Category="Flight") float Climb = 0.f;
	/** 1 at a sonic boom, decays over ~0.6 s. */
	UPROPERTY(BlueprintReadOnly, Category="Flight") float BoomK = 0.f;
	/** Leading fist: true = right arm forward in the fly pose. */
	UPROPERTY(BlueprintReadOnly, Category="Flight") bool bRightFist = true;
	/** Seconds in flight (continuous across flight subs). */
	UPROPERTY(BlueprintReadOnly, Category="Flight") float FlightT = 0.f;
	/** Critic r2 (round 3 hero request, fl16 3.55 / 7.25 s "a fire escape went through his head and arm"): a facade alongside the body --
	 *  WallSide in the body frame (-1 left .. +1 right, 0 none) and WallDist (m, body centre to the facade). Meant to be filled by the
	 *  flight controller while it slides along / brushes a wall; until then the defaults change nothing. With a wall within 1.5 m the anim
	 *  leads with the far-side fist and tucks the wall-side free arm and leg in. */
	UPROPERTY(BlueprintReadOnly, Category="Flight") float WallSide = 0.f;
	UPROPERTY(BlueprintReadOnly, Category="Flight") float WallDist = 99.f;
};

/**
 * C1 animation contract (browser traversal/anim.js), written by UWebTraversalComponent every frame.
 * P2's AnimBP reads this (AWebTravCharacter::GetTravAnim / UWebTraversalComponent::Anim).
 * Positions / velocities in cm and cm/s (Unreal units). Sub-state names match the browser strings.
 */
USTRUCT(BlueprintType)
struct WEBHOMAGE_API FWebTravAnim
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly, Category="Traversal") EWebTravMode Mode = EWebTravMode::Ground;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") EWebTravMode FromMode = EWebTravMode::Ground;
	/** ground: idle walk run sprint jumpCharge vault | land: landLight landMedium landHard landRoll | air: jumpLaunch rise apex fall dive
	 *  release trick pointLaunch wallJump zipPull | swing: swingLow swingBottom swingHigh wallKick | zip: zipFire zipFlight zipCatch |
	 *  perch: perchLand perchIdle | wall: crawl wallRun wallRunSide cornerWrap wallZip */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FName Sub;
	/** Seconds in the current sub-state / mode. */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float T = 0.f;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float ModeT = 0.f;
	/** m/s (ground: locomotion speed; else |velocity|). */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float Speed = 0.f;
	/** cm/s. */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FVector Velocity = FVector::ZeroVector;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") bool bGrounded = true;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float JumpCharge = 0.f;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FWebTravAnimSwing Swing;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FWebTravAnimZip Zip;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FWebTravAnimWall Wall;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FWebTravAnimPerch Perch;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float LandingSeverity = 0.f;
	/** layout | corkscrew | tuckFlip | scissor | None */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FName Trick;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float TrickSide = 1.f;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float TrickDur = 0.f;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") bool bDive = false;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") bool bGlide = false;
	/** Yaw of the body (deg, UE convention). */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float FacingDeg = 0.f;
	/** Root orientation incl. bank / pitch. */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FQuat BodyQ = FQuat::Identity;
	/** Feet position (world, cm). */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FVector RootPos = FVector::ZeroVector;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float StepOffset = 0.f;
	/** Quick web boost: one-arm yank. */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") bool bQuickActive = false;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float QuickT = 0.f;
	// round 01 (W10): the reach-and-miss gesture of a press with no anchor (s since the press, < 0 = none), the reaching hand, the aim (world, unit)
	UPROPERTY(BlueprintReadOnly, Category="Traversal") float NoAnchorT = -1.f;
	UPROPERTY(BlueprintReadOnly, Category="Traversal") bool bNoAnchorRight = true;
	FVector NoAnchorAim = FVector::ForwardVector;
	float WebShotK = -1.f;   // round 02: progress of a web in flight while the body is still ballistic (0..1, < 0 = none)
	UPROPERTY(BlueprintReadOnly, Category="Traversal") bool bQuickRightHand = true;
	/** Invincible flight (2026-10-15): valid while Flight.bActive. */
	UPROPERTY(BlueprintReadOnly, Category="Traversal") FWebTravAnimFlight Flight;
};

/** One-frame traversal event for camera / audio (browser `events`). */
struct FWebTravEvent
{
	FName Type;
	float Severity = 0.f;
	float Dist = 0.f;
	float K = 1.f;
	bool bRun = false;
	// Invincible flight (2026-10-15): where / which way (metres, world) for flight events (sonicBoom, breachIn, breachOut, heroLand, ...)
	FVector Pos = FVector::ZeroVector;
	FVector Dir = FVector::ZeroVector;
};

/** A web strand to draw (the swing web, zip webs, dash / quick-boost webs). Metres. */
struct FWebTravStrand
{
	bool bActive = false;
	bool bRightHand = true;
	FVector Anchor = FVector::ZeroVector;
	float Age = 0.f;         // s since attach
	float ShootDur = 0.08f;  // s for the strand to reach the anchor
	float Taut = 0.f;
	float ReleaseT = -1.f;   // >= 0: released, fading (s since release)
	bool bSnap = false;      // released with an elastic snap
	FVector AnchorFrom = FVector::ZeroVector; float BlendT = 1.f;   // round 02: a re-anchored strand slides from AnchorFrom to Anchor
	FVector AnchorNow() const { const float K = BlendT * BlendT * (3.f - 2.f * BlendT); return FMath::Lerp(AnchorFrom, Anchor, K); }
};
