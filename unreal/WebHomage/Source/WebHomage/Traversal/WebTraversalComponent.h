// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// Piece P3: UWebTraversalComponent — C++ port of the browser's Insomniac-style traversal state machine
// (src/player/traversal/traversal.js). It runs its own 120 Hz substep and owns the body while it is active
// (CharacterMovement is switched off); collision uses Unreal traces / capsule penetration (FWebTravWorld).
//
//   modes: ground | air | swing | zip | perch | wall   (+ anim mode 'land' while a landing recovery plays)
//   kin moves: vault | cornerWrap | wallHop (scripted curves that take over the step)
//
// Owner feel notes from the browser are kept next to the code they shaped (user r4..r13, feedback #3..#19).
// Not ported yet (browser features): web slingshot (Ctrl), web tightrope (T), water plunge / yank, bridge halfway
// bounce, car-roof riding (C3 dynamics), tree-canopy anchors, Shift-walk (disabled in the browser too: user r-nowalk).
//
// Simulation units are METRES (browser constants unchanged), UE axes (Z up). Yaw angles: atan2(Y, X).
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Traversal/WebTravTypes.h"
#include "Traversal/WebTravWorld.h"
#include "Traversal/WebTravAnchors.h"
#include "WebTraversalComponent.generated.h"

class FWebTravCamera;

UCLASS(ClassGroup=(WebHomage), meta=(BlueprintSpawnableComponent))
class WEBHOMAGE_API UWebTraversalComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UWebTraversalComponent();

	/** World setup (building index) — call once the level is loaded. */
	void InitWorld(UWorld* World, const AActor* Owner);
	/** World Partition / streamed levels: the traversal solids of a level are added when it becomes visible and removed when it goes (FWebTravWorld::AddLevel / RemoveLevel). */
	void OnLevelAddedToWorld(ULevel* Level, UWorld* InWorld);
	void OnLevelRemovedFromWorld(ULevel* Level, UWorld* InWorld);
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;
	/** One frame: substeps at 120 Hz. `I` is consumed (edge flags cleared). Writes Anim + Events. */
	void UpdateTraversal(double Dt, FWebTravInput I);
	/** Place the body (metres; feet snapped to the floor if below). */
	void Teleport(const FVector& PosM, double YawRad);
	/** Set the body velocity (m/s), e.g. a scripted airborne start. */
	void SetVelocityM(const FVector& V) { S.Vel = V; if (V.SizeSquared() > 1) { S.Facing = FMath::Atan2(V.Y, V.X); } }

	/** C1 animation contract (read by P2's AnimBP). */
	UPROPERTY(BlueprintReadOnly, Category="Traversal")
	FWebTravAnim Anim;

	UFUNCTION(BlueprintPure, Category="Traversal")
	const FWebTravAnim& GetTravAnim() const { return Anim; }

	/** Progression hook 'swingReleaseBoost' multiplier. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal")
	float ReleaseBoostMul = 1.f;
	/** Round 07: a held swing button re-searches for the next anchor this long (s) after a web release, even while rising. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float ReattachAfter = 0.22f;
	// round 20 tunables (-WHTravTune=Name=V): wall-gait torso lean off the facade (rad), air body-to-velocity alignment speed band (m/s),
	// setback look-ahead above a ledge (m), E-from-wall facade-top search range (m)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float WallGaitLeanR = 0.08f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float WallGaitFootOffR = 0.42f; // round 21 (r20 .30): hips ~.5 m off the facade so the forward-bent driven knee clears it
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AirAlignV0 = 22.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AirAlignV1 = 28.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float SetbackLook = 5.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float WallZipRange = 260.f;
	// round 23: a facade top more than this far above the hero (m) is only the fallback of a wall zip; the nearest roof edge / corner first (0 = off)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float WallZipFarUp = 110.f;
	// round 23 (Z23: w2 E-zip must end on a perch <= 2 s after fire): when the facade top is far and nothing passes the camera-facing search,
	// a second search up to this range (m) takes the nearest visible roof edge / corner in any direction off the wall (run direction preferred)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float WallZipFarRange = 90.f;
	// round 23 (director: vertical run torso 5-20 deg off wall-up; c ran a 33 deg diagonal with a 30 deg torso): a vertical-dominant run
	// (stick mostly up) keeps its run line within this many degrees of the wall's up axis (0 = r22 free diagonal)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float WallVertMaxDeg = 10.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AntiTunnel = 1.f;
	// round 24 (critic r23 biggest gap, SPEC T7 / T3: "every 4 s a release from >= 30 m over the floor down to a 3-13 m low point, drop >= 20 m;
	// rope on screen 25-45 %"): ALTITUDE CHAIN. AltChain 1 = a plain web release (and a flow flip) is solved for an apex AltApexH..AltApexH +
	// AltApexJit m over the floor (feet; per-release deterministic jitter), the release velocity turned up toward it (speed kept, at most
	// AltTurnDeg of turn, horizontal >= AltHMin m/s, vz <= AltVzMax m/s; the climb above it still goes forward); a swing entered >= AltEntryMin m
	// over the street bottoms out AltLowLo..AltLowHi m over the street (alternating halves of the band, so consecutive arcs differ) instead of
	// the shallow / deep drop below the entry. 0 = r23 (ReleaseVzMax forward pop, shallow / deep arcs).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AltChain = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AltApexH = 33.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AltApexJit = 5.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AltVzMax = 34.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AltTurnDeg = 40.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AltHMin = 14.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AltFlowVzMax = 26.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AltEntryMin = 20.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AltLowLo = 5.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AltLowHi = 10.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AltOpenAhead = 35.f; // round 24: open street needed ahead (m; 0 = always)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AltOpenUp = 8.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AltWeaveK = 0.4f; // round 24: corridor weave scale (low points near the centre)
	bool bAltArcNext = false, bAltSwing = false; // round 24: the next / current swing follows an altitude release (alt arc + centred weave)
	// round 25 (critic r24 biggest gap, SPEC T5 / T6: "the rope readable on every web_on frame, 2-4 px, mean luminance >= 25/255 off a 6 px
	// band either side, over dark glass AND pale facades"; r07 emissive beam bloomed, r08 pale line vanished on pale facades, r09-r24 dark
	// lit line vanished on dark glass): read by the character's web strands (the rope look; no gameplay effect).
	// RopeLook 1 = an UNLIT two-tone strand (/Game/Traversal/Materials/M_TravWeb: bright core, dark rim, exposure-compensated so the core
	// never blooms, no fog) whose core share follows the luminance of the scene behind the strand -- sampled UNIFORMLY per strand
	// (final round 13, critic r12: per-pixel taps beaded / flickered against mixed facades): 4 taps at two fixed screen points along the
	// line (BgUV0 / BgUV1 vector params, pushed per strand per frame by UpdateWebs): over a dark background the bright core fills
	// RopeCoreDark of the width, over a bright one only RopeCoreBright (the dark rim carries the line); the step is binary in the
	// strand-average luminance and biased BRIGHT (RopePivot x 1.2-1.4), so a mixed facade gets one continuous bright-carrying line
	// (a mid plateau averaged the strand to the facade's own level -- r13 build 2 probe); screen-space width clamp RopePxMin..RopePxMax px.
	// 0 = r24 (lit dark M_TravColor line, world width 1.6 cm / 0.25 % of the distance).
	// r25 build 2: RopeSolid 1 = ONE tone over the whole strand width (bright over a dark background, near-black over a bright one; the
	// two-tone core/rim averaged back to the background's level in the resolved 3-4 px line: 18/65 frames passed), drawn after motion
	// blur with a manual scene-depth test (M_TravWeb); width clamp 2.8-3.4 px (the build-1 3.2-4.0 px clamp measured up to 4.5 px).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float RopeLook = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float RopeSolid = 0.f;
	// r25 build 3: unused strand segments stay registered as visible at a 1e-4 scale (no render-proxy re-creation on the attach frame)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float RopeKeepProxy = 1.f;
	// r25 build 4: the shot strand's travelling wave (30 cm world, decays in ~0.3 s) bounded to RopeWavePx on screen (< 0 = unbounded, r24)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float RopeWavePx = 1.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float RopePxMin = 3.2f;
	// round 09 (critic r08 adjacent: the night halo reads > 4 px on near-vertical strands over dark glass; 7 of 8 s5 W5 fails
	// are width): 3.4 -> 3.3 px at the top of the clamp (the measured width runs ~0.5-0.9 px of AA / bloom halo over the drawn)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float RopePxMax = 3.3f;
	// round 08 (critic r07: web read 7 -> 5 -- the strand averaged back to the background because CoreBright == CoreDark pinned the
	// core share at 0.5 and Pivot 100 sat above every exposed-luminance reading, so the adaptivity never fired): the core share now
	// actually switches at Pivot (exposure-applied pre-tonemap luminance: dark glass ~0.02-0.08, lit facades ~0.2-0.5, sky ~0.6-1.2) --
	// over dark backgrounds the bright core fills RopeCoreDark of the width, over bright ones the dark rim (1 - RopeCoreBright) carries it
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float RopeCoreBright = 0.15f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float RopeCoreDark = 0.9f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float RopePivot = 0.30f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float RopeCoreLvl = 1.15f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float RopeRimLvl = 0.03f;
	int32 AltRelIdx = 0;        // round 24: plain / flow releases solved by the altitude chain (jitter index)
	double AltApexWant = -1.0;  // telemetry: apex (m over the floor) the last altitude release was solved for (-1 none)
	/** Round 24: vertical release speed that tops out D m higher (StepAir gravity: G, x0.55 under |vz| 3.5). */
	static double AltVzFor(double D);
	// round 21 (-WHTravTune): side-run torso raised this many degrees above the run line toward the wall's up axis (0 = r20 plank);
	// MantleStep 1 = a setback is crossed ON the surfaces (up the lip, along the ledge top, onto the next face; limbs stay on them), 0 = r20 hop
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float WallSideRaiseDeg = 25.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float MantleStep = 1.f;
	// round 22 (critic r21 "side-run slither": box wider than tall; director target: upright parkour sprint, torso within 30 deg of the
	// wall's up axis, facing along the run line): WallSideUpright 1 = the side run is an upright runner side-on to the facade (body up =
	// wall-up leaned WallSideLeanDeg forward along the run line and WallSideOutDeg out from the wall so the feet reach it; chest along the
	// run line); 0 = the r21 frame (chest to the wall, body WallSideRaiseDeg above the run line). WallSideFootOff = root offset (m) before the
	// out-tilt (feet ~.1 m off the facade, hips ~.4 m)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float WallSideUpright = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float WallSideLeanDeg = 14.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float WallSideOutDeg = 16.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float WallSideFootOff = 0.36f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float WallSideClimbDamp = 10.f; // round 22 (r21 3): climb-speed decay on a sideways run (1/s)
	/** Round 11: true = the round-04..10 browser tricks (tuckFlip / layout / corkscrew / scissor) instead of the flip programs. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") bool bLegacyTricks = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlipReachHold = 0.2f;
	/** round 05 (F8): the final reach also holds without the button while the catch is on its way (s before falling out of the trick). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlipReachIdle = 0.8f;
	/** round 01: offset of the program cycle index (K) used by ChooseForInput; scripts set it (tune) so each case of a clip starts at a different program of its stick pool */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlipKStart = 0.f;
	/** round 04 (live defaults = the capture chain tune since the owner live fix): anchor candidates must be above the hand (rise / run >= AnchorElevMin) and not behind the travel line (cos of the horizontal angle >= AnchorAheadMin; -2 = off) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AnchorElevMin = 0.1f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AnchorAheadMin = -2.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlipFloorClear = 6.f;  // round 11: a flip must be done this high over the floor
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlipCatchRoom = 0.35f; // round 11: s left after the program's reach for the catch // round 11: held final reach while no web has caught (a sky launch then dives into the catch, owner clip S6 ends the same way)
	/** round 05 (critic r04 gap 3: "s2 t=8-12, a 4 s micro-rocking hang"; "cap hangs at ~1.5 s"): a swing that stalls (slow, near the
	 * bottom, web taut) for HangCapS s lets go and the still-held button fires the next web at once (the chain continues; the release
	 * itself gets the usual pop). 0 = off. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float HangCapS = 1.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float HangStallSpd = 5.f; // m/s under which a swing counts as stalled
	/** Round 07: a web stuck while rising faster than this (m/s) starts its pendulum at the top of the hop, at most PendingMax s later. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float PendingVz = 5.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float PendingMax = 0.5f;
	/** round 02: the largest lean (rad from world up) of a free fall that is not a dive / glide: 1.45 = nearly horizontal, head leading; never head-down */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AirPitchMax = 1.1f;
	/** Round 07: upward speed kept by a plain web release (m/s); the rest turns into forward speed. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float ReleaseVzMax = 8.f;
	/** Round 08: facade clearance kept by the canyon spring (m) and the spring rate (1/s). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float WallClearance = 14.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float WallKeepRate = 2.5f;
	/** Round 09: weave inside the corridor — swing target line toward the active anchor (x WeaveK, <= WeaveAmp m off centre). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float WeaveK = 0.45f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float WeaveAmp = 6.f;
	/** Round 09: alternating arc depth below the entry height (m): odd swings shallow, even swings deep. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float ArcDropShallow = 8.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float ArcDropDeep = 12.f;
	/** Round 10: lowest designed arc bottom (feet over the floor, m; T7: 1-4 storeys over the street, never skimming car roofs). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float ArcLowMin = 15.f;
	/** Round 10: the first web after a sky launch bottoms out ArcLowMin + 0..SkyArcExtra m over the street (dives back into the canyon). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float SkyArcExtra = 4.f;
	/** Round 09: the next anchor search leans this far (deg) toward the side opposite the previous web. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AnchorAltDeg = 8.f;
	/**
	 * Round 10 (critic r09 T3/T4/T7: four identical 2 s swings, never at the roofline): a jump-release with a trick pressed is a
	 * SKY LAUNCH — the release climbs at up to SkyLaunchVz m/s (plain jump-release: 22), gravity is x SkyHangK while |vz| <
	 * SkyHangVz (hang time at the top, tricks chained on input), and no web is searched on the way up. The camera drops under the
	 * hero and looks up (sky behind him) until he falls faster than 8 m/s.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float SkyLaunchVz = 26.f;
	/** Round 10 (T7 "peak at roofline height"): the launch speed is solved so the apex lands SkyRoofOver m above the lower street
	 *  wall's roofline beside the path ahead (RoofBesideAhead), the peak clamped to SkyPeakMin..SkyPeakMax m over the street and the
	 *  launch to SkyLaunchVz..SkyLaunchVzMax m/s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float SkyRoofOver = 3.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float SkyPeakMin = 38.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float SkyPeakMax = 90.f; // r10-r11 58
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float SkyLaunchVzMax = 60.f; // r10-r11 52
	/** Round 10: rope cap (and pivot reach) of the first web after a sky launch (a long dive back to the street). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float SkyRopeMax = 50.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float SkyHangK = 0.55f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float SkyHangVz = 7.f;
	/** Round 10: gravity scale on the rest of a sky launch's climb (vz >= SkyHangVz): the release carries him to the roofline. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float SkyRiseK = 1.0f; // r10-r11 1.4 (round 12: taller launches under the vz cap)
	/**
	 * Round 12 (critic r11 single gap: release tricks low in the canyon, facades behind the hero): every release trick starts from
	 * an apex above the rooftops. A trick pressed at a web release is a sky launch (bTrickLaunch), the launch is solved so its apex
	 * sits SkyApexOver m above the TALLEST roof within SkyTallR m of the path the flip program will cover (TallestRoofAlong), and the
	 * program is armed on the climb and starts once the climb has slowed to SkyTrickVz m/s (it then plays in the apex hang). The
	 * peak cap SkyPeakMax rose 58 -> 90 m over the street; where even that cannot clear the roofs the flip still plays at the cap.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") bool bTrickLaunch = false; // round 13: off (see bFlowTricks)
	/**
	 * Round 13 (critic r12 single gap: "each trick is an isolated set piece: 1.7 s rise, trick, 1.3 s dive, then a camera cut"): a trick
	 * pressed at a web release starts its flip program AT the release (no climb first). The release's climb is solved per program so
	 * that, under FlowFlipGK x gravity while the program plays, he is FlowCatchRise m above the release height, still inside the street
	 * canyon (facades above him to web onto), when the program's catch window opens (FWebFlipProgram::CatchOpen s before its end,
	 * inside the final reach): the next web attaches there. Release -> next attach = program length - CatchOpen + one search step.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") bool bFlowTricks = true;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlowFlipGK = 0.45f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlowCatchRise = 3.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlowVzMin = 6.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlowVzMax = 14.f;
	/**
	 * Round 15 (orchestrator reconciliation of critic r11 "sky behind the hero" and critic r14 "do not tilt up into the sun": sky by
	 * HEIGHT, not by camera pitch): a flow flip's climb is solved so the catch window opens FlowRoofOver m above the LOWER street wall's
	 * roofline beside the path ahead (RoofBesideAhead, FlowRoofAhead m) whenever that needs a rise between FlowCatchRise and FlowRiseMax m
	 * (a roofline further up than that is out of reach for a flow flip: the r13 FlowCatchRise rule is kept, no rocket launch).
	 * FlowRoofOver 0 = off.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlowRoofOver = 3.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlowRiseMax = 14.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlowRoofAhead = 40.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlowRoofMinH = 16.f;
	double FlowRoofUsed = -1.0, FlowRiseUsed = 0.0; // telemetry: roofline (m over the street) and rise of the last flow flip
	/**
	 * Round 17 (critic r16 single gap: "every trick is shot from the street into a dark facade"; TRICK_CAMERA_SPEC TC8): a flow flip fires
	 * from an APEX with the hips >= FlowRoofOver m over the lower roofline within FlowRoofR m. Roofline = per street side the HIGHEST roof
	 * sample (>= FlowRoofMinH over the street: canopies ignored) within FlowRoofR m behind / beside / ahead, lower side wins (FlowRoofTarget).
	 * bFlowApexSolve: the release's climb is solved for the program's APEX (hips at target + FlowApexMargin), not for the catch height, and
	 * the flow vz cap is FlowApexVzMax; a swing that ends in a flip is held on its rising front until the apex is reachable
	 * (FlowApexGap <= FlowReadyGain, autoChain; a live player lets go at the top of the swing the same way).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") bool bFlowApexSolve = true;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlowRoofR = 30.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlowApexMargin = 1.0f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlowApexVzMax = 20.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlowApexMin = 2.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlowReadyGain = 9.0f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float FlowHoldMax = 12.0f; // the roof hold applies only while the gap is under FlowReadyGain + this (a canyon roofline is not waited for)
	/** Round 17: world Z the hips must reach at the flip apex (lower roofline within FlowRoofR + FlowRoofOver + FlowApexMargin); -1 = no roof. */
	double FlowRoofTarget(const FVector& Dir, double* OutRoofOverStreet = nullptr) const;
	/** Round 17: target - hips now (m; <= 0 already above it); -1e9 when there is no roofline rule here. Cached 0.1 s. */
	double FlowApexGap() const;
	/** Round 18 (critic r17: f4's 4th flip missed its catch over a plaza): is a web in reach where a flow flip released now ends (Dur s of flight at the
	 *  current horizontal speed x CatchSpeedK)? The auto-chain only presses the trick when it is (else a plain release). Cached 0.1 s. */
	bool CatchReachable(double Dur) const;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float CatchSpeedK = 1.08f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float CatchFlightS = 1.55f; // release -> catch window (CatchT: backDouble 1.6, corkscrew 1.51, frontPikeSwan 1.43)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float CatchGuard = 1.f;    // 0 = off
	/** Round 17: apex gain (m) of a flow flip released now with vertical speed Vz0 (program boost included). */
	double FlowApexGain(double Vz0, const struct FWebFlipProgram* FP) const;
	mutable double GapCacheT = -1e9, GapCacheV = -1e9;
	mutable double CatchCacheT = -1e9; mutable bool bCatchCacheV = true;
	FVector RouteDir = FVector::ZeroVector; // round 17: smoothed horizontal travel direction (unit)
	double FlowApexWant = 0.0; // telemetry: apex hips Z the last flow flip was solved for (world m; 0 none)
	bool bFlowChoose = false; // round 13: ChooseTrick/FitFlip called for a flow flip (its air is solved, not ballistic)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float SkyApexOver = 6.f;
	/** Round 12: gravity scale while a sky launch's flip program plays (from vz 9 m/s: ~5 m more climb, ends near its start height). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float SkyFlipGK = 0.32f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float SkyTallR = 30.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float SkyTrickVz = 9.f;
	/** Round 10: a new web's anchor must sit at least this far (m) above the body (critic r09: rope anchored below / behind, b 2.0 s). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float AnchorMinAbove = 3.f;

	/**
	 * Fraction of the anchor's lateral offset (relative to the swing direction) kept in the physics pivot.
	 * 1 = browser r13 flight dynamics (pivot = the real anchor: a facade anchor 15-25 m to the side swings him sideways).
	 * 0 = travel-plane pivot (older browser build, spiderman-learnings 02 §5): the web still draws to the real anchor but the
	 * arc stays in the direction of travel, and steering turns the whole arc about the body. P3 round-01 default: 0.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal")
	float PivotLateralKeep = 0.25f; // round 09: 0.1 -> 0.25 (the pivot keeps some of the anchor's side: a weave)

	/** Travel-plane pivot only: the pivot sits at least this high over the body at attach (m)... */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal")
	float MinPivotRise = 6.f;
	/** ...and at least this steep (deg) from the body, so an attach never turns forward speed into a vertical climb. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal")
	float MinPivotElevDeg = 35.f;

	/** Canyon keeping: extra arc dip per metre the swing entry is above the anchor band (0 = browser r10f only). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal")
	float CanyonDipK = 0.6f;

	/**
	 * Round 02 (critic: "swings are flat"): deep vertical pendulum. With PivotLateralKeep < 1 every swing's pivot is built so
	 * the circle through the body bottoms out ArcBottomMin..ArcBottomMax m above the floor (random per swing, so no two arcs
	 * are alike) and at least MinArcDrop m below the entry height (never below 3 m: car roofs).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float ArcBottomMin = 5.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float ArcBottomMax = 12.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float ArcDropJitter = 5.f;   // round 07: extra drop 0..N m per swing
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float MinArcDrop = 14.f;   // round 07: 16 -> 14 (critic r06: depth AND rhythm; drop test >= 10 m)
	/** Max horizontal distance of the virtual pivot ahead of the body (m). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float MaxPivotAhead = 30.f;   // round 07: 55 -> 30
	/** Longest virtual rope (m): high entries keep a brisk ~2 s arc and bottom out higher instead of a slow 50 m pendulum. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float RopeCapJitter = 0.12f;   // round 07: rope cap 30-34 m per swing
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal") float MaxArcRope = 34.f;   // round 07: 50 -> 34 (1.2-1.8 s swings)

	/** Deterministic trick RNG seed (replays). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Traversal")
	int32 RandomSeed = 1234;

	FWebTravCamera* Cam = nullptr;
	FWebTravWorld TravWorld;
	FDelegateHandle LevelAddedHandle, LevelRemovedHandle;
	TWeakObjectPtr<UWorld> StreamWorld;
	TUniquePtr<FWebTravAnchors> Anchors;
	TArray<FWebTravEvent> Events;
	FWebTravStrand Strands[2];

	// ---- read-only accessors for camera / telemetry (metres)
	EWebTravMode Mode() const { return S.Mode; }
	/** Owner playtest: white strands exist only during an active swing, never release/zip/boost tails. */
	bool CanRenderSwingWeb(int32 StrandIndex) const
	{
		return StrandIndex >= 0 && StrandIndex < 2 && S.Mode == EWebTravMode::Swing
			&& Strands[StrandIndex].bActive && Strands[StrandIndex].ReleaseT < 0.f;
	}
	const FVector& QuickBoostDir() const { return S.Q.Dir; }
	FName Sub() const { return S.Sub; }
	double ModeT() const { return S.ModeT; }
	const FVector& PosM() const { return S.Pos; }
	/** final loop telemetry: fraction (0..1) of the segment A->B (metres) that is clear of building / world geometry (1 = clear); read-only query */
	double StrandClearFraction(const FVector& A, const FVector& B) const;
	const FVector& VelM() const { return S.Vel; }
	FVector RootPosM() const { return RootPos; }
	double Facing() const { return S.Facing; }
	bool IsDiving() const { return S.bDive || S.bGliding; }
	/** Round 10: airborne from a sky launch (jump-release + trick) and not yet falling into the dive. */
	/** Round 10: feet height over the street / building mass below (props, trees, awnings ignored). */
	double HeightAboveStreet() const { return FeetZ() - TravWorld.StreetHeight(S.Pos.X, S.Pos.Y, FeetZ() + 0.1); }
	bool IsSkyLaunch() const { return S.bSky && S.Mode == EWebTravMode::Air; }
	/** Round 10: roofline (m, world Z) of the LOWER of the two street walls beside the path 0..Ahead m ahead along Dir; -1 if none. */
	double RoofBesideAhead(const FVector& Dir, double Ahead = 60.0) const;
	/** Round 10: that roofline over the street below (m), along the current horizontal velocity; -1 if none. */
	double SkyRoofOverStreet() const;
	/** Round 10: sky-launch telemetry: the peak the launch was solved for (m over the street), the roofline used (m over the street). */
	double SkyPeakWant = 0.0, SkyRoofUsed = 0.0;
	/** Round 12: highest roof (m, world Z) within R m of the horizontal path D0..D1 m along Dir from From (down-ray grid, 5 m); -1 if none. */
	double TallestRoofAlong(const FVector& From, const FVector& Dir, double D0, double D1, double Rad) const;
	/** Round 12: the sky-launch peak (m over the street) a trick release here would need to clear the tallest roof near its flip
	 *  (current velocity; cached 0.25 s) and whether it is within SkyPeakMax. */
	double SkyPeakNeeded(bool& bReachable) const;
	/** Round 12: tallest roof used by the last sky launch (m over the street; -1 none) and the flip program armed for the apex. */
	double SkyTallUsed = -1.0;
	bool IsFlipArmed() const { return !S.ArmedFlip.IsNone() && S.Mode == EWebTravMode::Air; }
	FName ArmedFlipName() const { return S.ArmedFlip; }
	mutable bool bRoofDebug = false;
	mutable double NeedCacheT = -1e9, NeedCacheV = 0.0;
	mutable bool bNeedCacheOk = false;
	/** Round 12: peak (m over Street) solved for a launch from Pos with horizontal speed HS along HV: max(RoofRule, tallest roof near
	 *  the apex path + SkyApexOver), clamped to SkyPeakMin..SkyPeakMax; TallOut = that tallest roof over Street (-1 none), bOk = reachable. */
	double SolveSkyPeak(const FVector& Pos, const FVector& HV, double HS, double Street, double RoofRule, double& TallOut, bool& bOk) const;
	double SkyV0For(double PeakOver, double Street, double FeetZNow) const;
	bool IsSwinging() const { return S.Mode == EWebTravMode::Swing; }
	const FVector& SwingAnchor() const { return S.Sw.Anchor; }
	const FVector& SwingDir() const { return S.Sw.Dir; }
	double SwingTension() const { return S.Sw.Tension; }
	double SwingBank() const { return S.Sw.Bank; }
	double SwingRope() const { return S.Sw.Rope; }
	double SwingTime() const { return S.Sw.T; }
	int32 Chain() const { return S.Chain; }
	const FVector& WallNormal() const { return S.W.Normal; }
	FName TrickName() const { return S.Trick; }
	double HeightAboveFloor_() const { return HeightAboveFloor(); }
	double FloorBelow() const { return FloorAt(S.Pos.X, S.Pos.Y, FeetZ() + 0.1); }
	bool HasZipTarget() const { return Anchors && Anchors->HasTarget(); }
	FVector ZipTargetPos() const { return Anchors && Anchors->HasTarget() ? Anchors->Best().Pos : FVector::ZeroVector; }
	FQuat BodyQuat() const { return FinalQ; }
	/** Round 06 capture pre-roll: write Anim / root from the current state without stepping the simulation. */
	void PosePreview() { FinalQ = Orient(1e-4); WriteAnim(FinalQ); }
	int32 BuildingCount() const { return TravWorld.Boxes.Num(); }
	int32 ZipKindCode() const;
	/** Round 19: why the last E press did what it did (highlighted / facadeTop / nearest / wallZip / pointLaunch / webDash / none). */
	FName LastZipWhy;
	int32 LastLandSrc = 0;
	int32 FlipVarCount = 0;
	FRandomStream FlipRng{ 20261001 }; // round 19: own stream (the swing solver's Rng sequence and the r18 routes stay unchanged)
	int32 GroundSrcNow() const { (void)FloorAt(S.Pos.X, S.Pos.Y, FeetZ() + 0.1); return TravWorld.LastGroundSrc; }
	FString LastZipFrom;
	/** Round 20 telemetry: setback mantles and top-outs of this run. */
	int32 SetbackCount = 0, TopOutCount = 0, TunnelStops = 0;
	/** Round 20: a fresh RMB press cancels a trick / top-out flip / wall run into a swing at once (-WHTrickCancel=0 = r19). */
	bool bTrickCancel = true;
	bool bPerchTopFix = true; // round 20: facadeTop perches on the highest top within 0.15-0.6 m of the edge (parapets); -WHPerchTopFix=0 = r19
	bool bFacadeWeb = true; // round 20: -WHFacadeWeb=0 = no facade web after a wall cancel (A/B)
	/** Round 20: rope wrap guard (strand grazing its own facade near the anchor; re-anchor turn limit). -WHRopeGuard=0 = r19. */
	bool bRopeGuard = true;
	float RopeGuardNear = 6.f, RopeGuardDeg = 40.f;
	int32 FlipCancels = 0;
	bool NearestZip(FTravZipPoint& Out, FName& Why) const;
	bool TryMantleSetback(const FVector& N0);
	/** Round 20: wall normal on real facade triangles -- the face of the building box under the contact when one is within 1.5 m (window
	 *  jambs, mullions and pilasters gave the side run a new normal every frame), else the raw normal. */
	FVector CleanWallNormal(const FVector& Pt, const FVector& RawN) const;
	/** Round 20: facade plane in front of the body from a 3 x 2 ray grid along -N (most protruding valid hit, cleaned normal). */
	bool WallPlane(const FVector& N, FVector& OutN, FVector& OutPoint) const;

private:
	enum class EKin : uint8 { None, Vault, CornerWrap, WallHop, Mantle };

	struct FSwing
	{
		FVector Anchor = FVector::ZeroVector, Normal = FVector::ForwardVector, Pivot = FVector::ZeroVector, Dir = FVector::ForwardVector;
		double Rope = 20, RopeTarget = 20, T = 0, Phase = 0, Bank = 0, Tension = 0, Kick = 0, KickCd = 0, AngMax = -9, Angle = 0, TautT = 0, Y0 = 0;
		double SideT = 0, SideK = 0, ModelT = 0, WrapT = 0, FdTension = 0, StallT = 0; // round 05: StallT = seconds this swing has been a stalled hang
		bool bRightHand = true, bApexed = false, bSideN = false;
		FVector SideN = FVector::ZeroVector;
		FName Kind;
	};
	struct FZip
	{
		FVector Target = FVector::ZeroVector, Normal = FVector::ForwardVector, P0 = FVector::ZeroVector, P1 = FVector::ZeroVector, P2 = FVector::ZeroVector;
		FVector FlightDir = FVector::ForwardVector, LaunchDir = FVector::ForwardVector;
		FName Kind;
		double T = 0, U = 0, Tau = 0, Dur = 0.5, FireDur = 0.05, Taut = 0, Len = 0, V0 = 0, VP = 0, DR = 0, DC = 0, DB = 0, TC = 0, TBrake = 0, AB = 0, Pitch = 0;
		double LUT[33] = { 0 };
		bool bLaunch = false, bDash = false, bWebs = false, bFromGround = false;
	};
	struct FPerch
	{
		FVector Pos = FVector::ZeroVector, Normal = FVector::ForwardVector, Impact = FVector::ZeroVector;
		FName Kind;
		bool bRoof = true;
	};
	struct FWall
	{
		FVector Normal = FVector::ForwardVector, Up = FVector::UpVector, Point = FVector::ZeroVector, LockDir = FVector::ZeroVector;
		FVector2D Move = FVector2D::ZeroVector;
		double RunV = 0, Phase = 0, Off = 0, Dist = 0.38, RunK = 0, LockMx = 0, ZipT = 0, SideUpK = 0; // round 22: SideUpK 0..1 upright side-run blend
		bool bFast = false, bLockDir = false, bZipWeb = false;
	};
	struct FKin
	{
		EKin Type = EKin::None;
		double T = 0, Dur = 0.3, Sp = 0, Floor = 0;
		FVector P0 = FVector::ZeroVector, P1 = FVector::ZeroVector, P2 = FVector::ZeroVector, N0 = FVector::ZeroVector, N1 = FVector::ZeroVector;
		FVector ExitVel = FVector::ZeroVector, Dir1 = FVector::ZeroVector;
		bool bRun = false, bHasDir1 = false;
		// wallHop
		double TA = 0, TB = 0, F0 = 0, Apex = 0, LandTop = 0, DTot = 0, ExitSpeed = 0;
		FVector Inward = FVector::ZeroVector;
		// round 21 surface-following setback step: centre polyline (m), surface normal per vertex, cumulative length, distance travelled
		FVector MQ[6], MN[6]; double ML[6] = { 0 }; int32 MNum = 0; double MS = 0;
		FVector CurN = FVector::ZeroVector, CurPt = FVector::ZeroVector; // current support surface (normal, closest point) while stepping
	};
	struct FQuick
	{
		bool bActive = false, bRightHand = true;
		double T = 0, K = 1, Last = -9;
		int32 N = 0, Seq = 0;
		FVector Dir = FVector::ForwardVector;
	};
	struct FState
	{
		EWebTravMode Mode = EWebTravMode::Air;
		EWebTravMode PrevMode = EWebTravMode::Air; // round 06: the mode before the last SetMode (wall-entry easing)
		FName Sub;
		double SubT = 0, ModeT = 0;
		FVector Pos = FVector::ZeroVector, Vel = FVector::ZeroVector, Carry = FVector::ZeroVector;
		double Facing = 0, Speed = 0, FloorZ = 0, StepOff = 0;
		bool bGrounded = false, bCharging = false;
		double ChargeT = 0, JumpCharge = 0, Coyote = 0, JumpBuf = 0;
		double AirT = 0, ApexZ = 0, RelT = 99, NoAnchorT = 0, AirTapT = -9;
		bool bDive = false, bGliding = false, bGroundSwing = false, bJumpRelHold = false, bAirTrickUsed = false;
		bool bWallCancel = false; FVector WallCancelN = FVector::ZeroVector, WallCancelDir = FVector::ZeroVector; // round 20
		FSwing Sw;
		int32 Chain = 0;
		double SinceSwing = 99;
		bool bLastTrick = false, bTrickBoosted = false, bTrickNoUp = false;
		FName Trick, LastTrickName;
		double TrickSide = 1, TrickDur = 0, TrickSnapT = 9, TrickLat = 0, TrickSteep = 0;
		int32 FlipCycle = 0, AutoFlipK = 0; // round 11: flip program cycling (script list / automatic choice)
		double TrickBuf = 0;
		double SearchT = 0, SwingCooldown = 0, WallCooldown = 0, ZipCooldown = 0, DashWebT = 0, QuickBuf = 0;
		int32 DashCount = 0;
		FZip Z;
		FPerch P;
		FWall W;
		FKin Kin;
		double LandSeverity = 0, LandLock = 0;
		FQuat BodyQ = FQuat::Identity;
		double Roll = 0, Pitch = 0, Bank = 0, RollA = 0, PitchA = 0;
		bool bSky = false;      // round 10: sky launch (jump-release + trick) until the next web / landing
		bool bFlowFlip = false; // round 13: a flip program started at a web release (floats at FlowFlipGK until it ends)
		FName ArmedFlip;        // round 12: flip program armed at a sky launch, started on the climb's last SkyTrickVz m/s
		bool bTopOut = false;   // round 06: airborne from a wall-run top-out (crouch landing on touchdown)
		int32 SwingIdx = 0;     // round 09: swings started (alternating arc depth)
		int32 LastAnchorSide = 0; // round 09: side of the last web anchor (+1 right of travel, -1 left)
		// round 07: web stuck on the rise, swing pending until the top of the hop
		bool bWebPending = false, bPendingTurn = false, bPendingRight = true;
		double NoAnchorReach = -1; bool bNoAnchorRight = true; FVector NoAnchorAim = FVector::ForwardVector;   // round 01 (W10)
		double PendingT = 0, PendingShoot = 0;   // PendingShoot: the strand's shot time; the pendulum starts when the tip has landed (round 01, W3)
		FTravAnchor PendingA;
		FVector PendingFwd = FVector::ForwardVector, PendingTurn = FVector::ForwardVector;
		FQuick Q;
		double Clock = 0;
	};

	// ---- helpers
	double FeetZ() const { return S.Pos.Z - H; }
	double FloorAt(double X, double Y, double Z) const { return TravWorld.GroundHeight(X, Y, Z - 0.5); }
	double StandAt(double X, double Y, double Z) const;
	FVector InputDir(const FWebTravInput& I) const;
	void SetMode(EWebTravMode M, FName Sub);
	void SetSub(FName Sub);
	bool Collide(double StepH, double Rad, FTravContact& C);
	bool Collide(FTravContact& C) { return Collide(STEP, R, C); }
	static bool HDir(const FVector& V, FVector& Out);
	double VmaxC() const { return VMAX + CHAIN_CAP * S.Chain; }
	void CapSpeed(double M);
	void CapSpeed() { CapSpeed(VmaxC()); }
	double HeightAboveFloor() const { return FeetZ() - FloorAt(S.Pos.X, S.Pos.Y, FeetZ() + 0.1); }
	double ReleaseBoost() const { return RELEASE_BOOST * ReleaseBoostMul; }
	void Emit(FName Type, float Sev = 0.f, float Dist = 0.f, float K = 1.f, bool bRun = false);

	// ---- web strands
	void WebAttach(bool bRight, const FVector& Anchor, double ShootDur = 0.08, bool bSecond = false);
	void WebRelease(bool bSnap = false);
	void WebReleaseSecond();

	// ---- ground
	void EnterGround(FName Sub);
	void StepGround(double H, FWebTravInput& I);
	bool StartMantleOnto(const FTravContact& C);
	void LaunchJump(bool bParkour);
	void StartVault(const FTravContact& C, bool bFast);
	// ---- air
	void StepAir(double H, FWebTravInput& I);
	void Land(double F, const FWebTravInput& I);
	void Corridor(double H, const FVector& InD);
	// ---- swing
	bool SteerHeading(const FVector& InD, FVector& Out) const;
	double FacadeAvoid(double H);
	FVector TravelDir(const FWebTravInput& I) const;
	bool TryStartSwing(const FWebTravInput& I);
	bool FacadeAnchor(FTravAnchor& A) const; // round 20: RMB on a wall -- web up the facade ahead of the kick when the search finds nothing
	void StartSwing(const FTravAnchor& A, const FVector& Fwd, const FVector* Turn, double HS);
	double SwingPhase() const;
	FVector PivotFor(const FVector& AnchorPoint) const;
	double SwingAngle() const;
	void StepSwing(double H, FWebTravInput& I);
	bool AnchorCheck(double H);
	void Reanchor(const FTravAnchor& A);
	void RopeWrap(double H);
	// ---- tricks / release
	FName ChooseTrick(const FWebTravInput& I);
	void SolveFlowClimb(FName TrickN, const FVector& HV, bool bAltRel);   // the flow flip's solved climb (release + mid-air F)
	bool AirFlipPress(const FWebTravInput& I);
	FName FitFlip(FName Want) const;
	double AirTimeToClear() const;
	bool PickHandRight(const FVector& AnchorPt, const FVector& Fwd) const;   // round 01 (W9): the anchor's side relative to the travel line at the press
	static constexpr double ShootAnticip = 0.033;   // round 04: s between the press (arm starts) and the strand's first drawn frame
	static double ShootDurFor(double Dist) { return FMath::Clamp(Dist / 225.0, 0.08, 0.20); }   // round 01 (W3): tip speed 250 m/s inside 0.06-0.20 s
	bool AnchorStrandClear(const FTravAnchor& A) const;   // round 01 (W7): hand->anchor line free of building geometry and tree crowns
	void StartTrick(FName Name);
	void TrickBoost(const FWebTravInput& I);
	void ReleaseSwing(bool bJump, const FWebTravInput& I);
	// ---- wall
	bool WideWall(const FVector& N, const FVector& Point) const;
	void EnterWall(const FVector& N, const FVector& Point, bool bRun, double Speed);
	FVector WallBasis(const FVector& N) const;
	void StepWall(double H, FWebTravInput& I);
	void WallZip();
	double WallProtrusion(const FVector& N, double BX, double BY) const;
	void StartCornerWrap(const FVector& N1, const FVector& P1, double Dur, const FVector& Dir1, double Mx);
	bool StartWallHop(const FVector& N, bool bFast);
	void StepWallHop(double H);
	void StepKin(double H);
	// ---- zip / perch / launches
	void StartZip(const FTravZipPoint& T);
	void ZipCurve(const FVector& Vel);
	double ZipDist(double Tau) const;
	double ZipArcE(double D) const;
	bool ZipClear() const;
	FVector Bez(double E) const;
	void StepZip(double H, FWebTravInput& I);
	void ArriveZip();
	void AnchorLaunch(const FVector& TravelV);
	void PointLaunch(const FVector& Normal, const FVector& TravelV);
	void WebDash();
	// ---- quick boost
	void QuickBoostStart();
	void QuickImpulse();
	void StepQuickBoost(double Dt);
	void StepPerch(double H, FWebTravInput& I);
	// ---- orientation / anim
	FQuat Orient(double Dt);
	void WriteAnim(const FQuat& Q);

	FState S;
	FRandomStream Rng;
	FWebTravInput LastInput;
	bool bLeaveSwingOK = false;
	bool bWorldReady = false;
	FVector RootPos = FVector::ZeroVector;
	FQuat FinalQ = FQuat::Identity;
	double LastVelYaw = 0;
	double CorrT = 0; FVector CorrPush = FVector::ZeroVector;
	FVector CorrWallN[8]; double CorrWallD[8] = { 0 }; int32 CorrN = 0; // round 08: facade planes around the body (normal, distance m)
	double AvoidT = 0, AvoidRate = 0;

public:
	// ---- constants (browser traversal.js :16-65)
	static constexpr double H = 0.95, R = 0.36, HEIGHT = 1.8, STEP = 0.55, G = 24, GS = 25;
	static constexpr double WALK = 2.6, RUN = 9.8, SPRINT = 15.5, WALLRUN = 14, VMAX = 45;
	static constexpr double CHAIN_BUF = 1.6, CHAIN_CAP = 2.5, CHAIN_REL = 1.5;
	static constexpr int32 CHAIN_MAX = 6;
	static constexpr double SWING_JUMP = 4.0, SWING_JUMP_UP = 16, SWING_JUMP_VY = 22, REL_NOTRICK = 4.0, REL_UP = 9, REL_UP_VY = 16;
	static constexpr double SWING_DIP = 6, SWING_GAIN = 5, RELEASE_BOOST = 1.5, SWING_DRAG = 0.0022, PUMP_MAX_ANG = 1.15;
	static constexpr double JUMP = 11.2, JUMP_MAX = 19.5;
	// round 06 wall-run body: lean back off the wall (rad) and feet offset from the wall plane (m) while running
	static constexpr double WallRunLean = 0.16, WallRunFootOff = 0.42;
	// round 19: procedural IK stride -- hips off the facade, torso leaned back (round 20: UPROPERTYs WallGaitLeanR / WallGaitFootOffR)
	static constexpr double WEB_MASS = 80;
};
