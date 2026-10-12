// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// Piece P3: the traversal hero pawn. Extends the F1 foundation character with
//  - UWebTraversalComponent (browser traversal state machine, 120 Hz substeps; CharacterMovement switched off),
//  - FWebTravCamera (browser chase camera: springs, FOV kick, speed shake) driving FollowCamera directly,
//  - Enhanced Input bound like the browser (RMB swing, Space jump, Shift sprint / wall-run, E zip, C dive, Q boost + pad),
//  - a placeholder figure (basic shapes, posed procedurally from the C1 anim struct) until P2's hero lands,
//  - web strands drawn as thin cylinder chains from the hand to the anchor (min on-screen width like the browser ribbon),
//  - scripted input playback + per-frame telemetry via UWebTravScript (-WHTravScript / -WHTravCsv).
#pragma once

#include "CoreMinimal.h"
#include "Containers/Ticker.h"
#include "Core/WebHomageCharacter.h"
#include "GameFramework/GameModeBase.h"
#include "Traversal/WebTravTypes.h"
#include "Traversal/WebTravCamera.h"
#include "Traversal/WebTravFlips.h"
#include "WebTravCharacter.generated.h"

class UWebTraversalComponent;
class UStaticMeshComponent;
class USceneComponent;
class UMaterialInstanceDynamic;
class UInputAction;

/** Final loop round 01: strands are drawn after this frame's pose is final. Phase 0 runs in TG_PostUpdateWork with the hero mesh's tick as a prerequisite (UpdateWebs), phase 1 in
 *  TG_LastDemotable (telemetry row: strand start as drawn + the final-pose palm). */
struct FWebTravPostTick : public FTickFunction
{
	class AWebTravCharacter* Target = nullptr;
	int32 Phase = 0;
	virtual void ExecuteTick(float DeltaTime, ELevelTick TickType, ENamedThreads::Type CurrentThread, const FGraphEventRef& MyCompletionGraphEvent) override;
	virtual FString DiagnosticMessage() override { return TEXT("WebTravPostTick"); }
};
template<> struct TStructOpsTypeTraits<FWebTravPostTick> : public TStructOpsTypeTraitsBase2<FWebTravPostTick> { enum { WithCopy = false }; };

UCLASS(config=Game)
class WEBHOMAGE_API AWebTravCharacter : public AWebHomageCharacter
{
	GENERATED_BODY()

public:
	AWebTravCharacter();

	virtual void Tick(float DeltaSeconds) override;

	UFUNCTION(BlueprintPure, Category="Traversal")
	UWebTraversalComponent* GetTraversal() const { return Traversal; }

	/** C1 animation contract for P2's AnimBP. */
	UFUNCTION(BlueprintPure, Category="Traversal")
	FWebTravAnim GetTravAnim() const;

	/** Live camera state (telemetry / debug). */
	const FWebTravCamera& GetTravCamera() const { return Cam; }

protected:
	virtual void BeginPlay() override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual void NotifyControllerChanged() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Traversal")
	TObjectPtr<UWebTraversalComponent> Traversal;

	/** Root of the placeholder figure (feet, oriented by the traversal body quaternion). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Placeholder")
	TObjectPtr<USceneComponent> FigureRoot;

	/** Mouse look: radians per Mouse2D unit (browser 0.0023 rad / px; Mouse2D arrives pre-scaled by 0.07). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Input")
	float MouseTestPx = 6.f; // round 20: px per engine frame injected by -WHTravInputTest=mouseLook (-WHMouseTestPx=)
	float MouseRadPerUnit = 0.0025f; // 2026-10-01 owner playtest ("tiny move = seizure"): Enhanced Input mouse = raw pixels, so 0.011 rad/px (0.6 deg) spun the camera; 0.0025 rad/px (~0.14 deg, typical PC TPS); x wh.MouseSensitivity

	/** Right stick look rate (rad/s) at full deflection (browser 900 px/s x 0.0023). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Input")
	FVector2D PadLookRate = FVector2D(2.07, 1.38);

	/**
	 * Round 10 (Manhattan integration issue P3-1): hero mesh / clips are data, not code. Priority (last wins): these defaults
	 * (the HeroDev proxy) < [/Script/WebHomage.WebTravCharacter] in Game ini < a Blueprint subclass / placed-actor value <
	 * command line -WHHeroMesh=<obj path> -WHHeroLens=<obj path or "none"> -WHHeroClips=<folder> -WHHeroClipPrefix=<prefix>.
	 * Clip asset = <HeroClipRoot>/<HeroClipPrefix><browser clip name> (P2: /Game/Characters/Hero/Anims + "A_Hero_").
	 * HeroLensMeshPath empty = no separate lens mesh (P2's lenses are material slots on the body).
	 */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="Hero")
	FString HeroMeshPath = TEXT("/Game/Traversal/HeroDev/HeroDev/SkeletalMeshes/SpiderMan.SpiderMan");
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="Hero")
	FString HeroLensMeshPath = TEXT("/Game/Traversal/HeroDev/HeroDev/SkeletalMeshes/Lenses.Lenses");
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="Hero")
	FString HeroClipRoot = TEXT("/Game/Traversal/HeroDev");
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="Hero")
	FString HeroClipPrefix;

	/**
	 * Round 13 (critic r12: "the hero is black at f4 8.45 s, V 44/255" -- a flip seen from below against a bright sky): a camera-side
	 * fill light that lights ONLY the hero (lighting channel 1; the hero meshes are on channels 0 + 1, the city on 0), no shadows, no GI.
	 * Candela = HeroFillCd + (HeroFillFlipCd - HeroFillCd) x flip-camera weight; placed HeroFillDist m from the hero toward the camera,
	 * HeroFillUp m above that line. Command line: -WHHeroFill=<base cd>,<flip cd> (0,0 = off).
	 */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="Hero") float HeroFillCd = 5000.f;
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="Hero") float HeroFillFlipCd = 18000.f;
	/** round 03: multiplier on the menu's base vertical FOV used by the chase camera (0.862 = 50 deg at the 58 deg default) */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="Camera") float CamFovScale = 0.862f;
	/** round 01: at night (MPC NightK 1) the hero-only fill stays at this candela (was faded to 0): a subtle fill so the hero reads against the lit facades */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="Hero") float HeroFillNightCd = 1400.f;
	/** Round 15: fill multiplier when the hero is front-lit by the sun (camera looking away from it). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="Hero") float HeroFillFrontK = 0.3f;
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="Hero") float HeroFillDist = 1.8f;
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="Hero") float HeroFillUp = 0.4f;

private:
	void BuildTravInput();
	void BuildFigure();
	bool SetupHeroMesh();
	void PoseFigure(float Dt);
	float SwayW = 0.f; // round 06: air-sway weight (spring)
	// round 01 (W4): the body frame blends into the rope frame at the attach with a critically damped spring (visual only)
	FQuat SwayDeltaQ = FQuat::Identity;
		FQuat BodySpringQ = FQuat::Identity; FVector BodySpringVel = FVector::ZeroVector; double AttachT = 9.0; bool bPrevSwingMode = false; bool bBodySpringInit = false;
		double OffSwingT = 9.0;   // round 08: time since the swing mode was left (the attach spring stays live into a fresh wall entry)
		double SpringResid0 = 0.0;   // round 11: the attach-frame spring gap (rad) -- big-gap catches (wall exits) take the gentler ramp
	FQuat FlipOffQ = FQuat::Identity;   // round 11: flip rotation relative to the body frame (springs back when a program is cut)
	FWebFlipPose LastFlip;              // round 11: telemetry
	FName LastFlipName;
	FQuat FlipBodyFrame = FQuat::Identity; // current traversal body frame for same-frame authored-pose lean compensation
	FVector FlipPoseAxis = FVector::UpVector; // author-local evaluated axis, used only to predict the pre-evaluation root for aiming
	bool bFlipPoseAxisValid = false;
	int32 FlipPoseAxisVer = -1;
	float FlipPoseAxisT = -1.f;
	const FWebFlipProgram* FlipProgramNow(float& OutT) const;
	void UpdateWebs(float Dt, const FVector& CamPosCm);
	FVector HandWorldCm(bool bRight) const;
	void PushTelemetry(double T, const FWebTravInput& I);
	UStaticMeshComponent* AddPart(USceneComponent* Parent, const TCHAR* Name, class UStaticMesh* Mesh, const FVector& Loc, const FVector& Scale, UMaterialInstanceDynamic* Mat);

	// input actions (transient, built at runtime like the F1 foundation)
	UPROPERTY(Transient) TObjectPtr<UInputAction> SwingAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> PadR2Action;
	UPROPERTY(Transient) TObjectPtr<UInputAction> PadL2Action;
	UPROPERTY(Transient) TObjectPtr<UInputAction> SprintAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> ZipAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> DropAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> QuickAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> TrickAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> LookMouseAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> LookPadAction;

	// live input state
	FVector2D LiveMove = FVector2D::ZeroVector, MouseAccum = FVector2D::ZeroVector, PadLook = FVector2D::ZeroVector;
	bool bRMB = false, bR2 = false, bL2 = false, bShift = false, bZipKey = false, bDropKey = false, bQuickKey = false, bJumpKey = false, bTrickKey = false;
	FWebTravInput PrevInput;
	// round 19 (owner playtest 2026-10-01: RMB swing and mouse look "eventually stop working"): held buttons / sticks are POLLED from the
	// player input key state every frame (the Started / Completed event latches stayed set when a release was lost to a pause, a menu
	// or a focus change, so a new press was never an edge); a capture watchdog re-takes a lost mouse capture while the player has the
	// game captured; WH_INPUT log lines + telemetry columns record every capture / focus / menu transition.
	void PollLiveInput(class APlayerController* PC, FWebTravInput& I, float Dt);
	void WatchInput(class APlayerController* PC, const FWebTravInput& I, float Dt);
	double LastLiveTickReal = -1.0;
	uint64 LastLiveFrame = 0;
	double InputTestClock = 0.0;
	int32 InCapState = -1;          // packed pc_cap | vp_cap << 1 | vp_focus << 2 | app_active << 3 | menu << 4
	float CapLostT = 0.f, RecaptureCd = 0.f;
	int32 NRecaptures = 0;
	double LookMagFrame = 0.0;      // this frame's mouse delta (px) before the capture gate
	float StatT = 0.f; double StatLook = 0.0; int32 StatLookFrames = 0, StatPress = 0, StatSwingStart = 0, StatNoAnchor = 0, StatZipPress = 0, StatZipFail = 0;
	float PressWatchT = 0.f; FString PressFrom; int32 PressNoAnchor = 0;
	// round 19 scripted repro of the live-input bugs: -WHTravInputTest=pauseRelease injects real key events into the player controller on a
	// real-time core ticker (it runs while the game is paused): RMB held, game paused, RMB released DURING the pause, unpause, RMB pressed
	// again -> must swing. -WHTravLatchInput = the round-18 event-latched flags (the A/B that shows the old failure).
	bool bLatchInput = false;
	FString InputTest;
	FTSTicker::FDelegateHandle InputTestTicker;
	double InputTestT0 = -1.0;
	int32 InputTestStep = 0, InputTestPresses = 0, InputTestSwings = 0;
	double InputTestPressT = -1.0;
	bool InputTestTick(float Dt);
	// round 20: -WHTravInputTest=mouseLook injects real mouse-axis events (MouseX / MouseY, IE_Axis) through the player controller; the
	// automated run cannot capture the OS mouse (run_game.sh passes -WHNoMouseCapture: never trap the owner's mouse), so the capture gate
	// is bypassed for injected look only while this test runs
	bool bInputTestMouse = false;
	double InjectedPx = 0.0, MouseTestYaw0 = 0.0;
	bool bMouseTestYaw0 = false;
	// round 20: -WHTravDepthAudit=<csv>: top-down orthographic scene-depth render of the city (all visible / without the name-excluded
	// signs, screens, props, foliage) vs the traversal floor (GroundHeight) on the 5 m audit grid
	int32 DepthAuditFrames = 0;
	bool bDepthAuditDone = false;
	void RunDepthAudit(const FString& Path);
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;

	FWebTravCamera Cam;
	int32 SunTries = 0; // round 15: frames spent looking for the level's sun light
	double TravTime = 0.0;
	bool bTravStarted = false;
	bool bAutoSawDescent = false; // round 07: auto-chain rule, this swing has descended
	// round 18: the auto-chain predicts its next flow-flip release FlipPreT s ahead (the trick camera pre-blends; critic r17 TC-A window)
	bool bAutoFlipPre = false;
	float FlipPreT = 0.38f;
	double PrerollLeft = 0.0;  // round 06: capture pre-roll (s), -WHTravPreroll=
	bool bHadPreroll = false;
	// round 26: split movie capture (-WHMovieFrom=<sequence s>): -dumpmovie writes frames only from that sequence time on (the replay is
	// deterministic; the earlier frames come from a run that quits there). 0 = off
	double MovieFrom = 0.0; int32 MovieDumpSaved = 0; bool bMovieGated = false;
	int32 PrerollFrames = 0;
	// autoChain rhythm rule state
	bool bAutoHeld = true, bAutoWasSwinging = false;
	double AutoGapT = 0.0;
	int32 AutoReleases = 0;
	// round 10: auto-chain sky launch (jump-release + chained tricks, re-press below skyRepressH)
	bool bSkyAuto = false, bSkyWasTrick = false;
	int32 SkyTricksLeft = 0, LastSkyRelease = -100;
	double LastSkyT = -100.0, SkyPeakH = 0.0;
	double SkyAutoT = 0.0;
	int64 FrameIndex = 0;

	// placeholder figure parts
	UPROPERTY(Transient) TObjectPtr<USceneComponent> ArmPivot[2];   // 0 = left, 1 = right
	UPROPERTY(Transient) TObjectPtr<USceneComponent> LegPivot[2];
	UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> FigureParts;
	UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> WebSegs;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> WebMat;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> WebMatTwoTone[2]; // round 25: M_TravWeb (null when the asset is missing); final round 13: one MID per strand (the background taps are per-strand vector params)
	int32 WebLookNow = -1;
	TArray<int8> WebSegDpg;   // round 12: cached depth-priority group per segment (0 world, 1 foreground); -1 = never set
	// round 25: the strand as drawn this frame (cm; telemetry projects it through the final camera), and its width (cm) at each end
	FVector RopeDrawA[2], RopeDrawB[2];
	double RopeDrawWA[2] = { 0.0, 0.0 }, RopeDrawWB[2] = { 0.0, 0.0 };
	bool bRopeDrawn[2] = { false, false };
	// final loop round 00: telemetry-only state (read-only bone samples; never feeds back into the sim, the camera or the pose)
	bool bFwBones = false; FName FwShoulder[2], FwChest; FQuat FwChestPrev = FQuat::Identity; double FwChestPrevT = -1.0; bool FwChestHas = false;
	double BodyPitchHold = 0.0; bool bBodyPitchHold = false;   // round 11: body_pitch_deg holds through the sideways cone (see the telemetry row)
	FString FinalSwingCols(double T);
	// round 01: post-pose strand tick + palm origin
	FWebTravPostTick PostTickFn, EndTickFn;
	bool bPostTickRegistered = false;
	float PendingWebDt = 0.f; FVector PendingCamCm = FVector::ZeroVector;
	FString PendingRow; double PendingRowT = 0.0; bool bRowPending = false;
	FVector PalmLocal[2] = { FVector::ZeroVector, FVector::ZeroVector };   // finger axis (hand bone space, unit) from the reference pose: [0] left, [1] right
	bool bPalmOk = false;
	FString BuildCols25();
	double ProjectHeroH() const;   // round 04: bone-box height of the hero through the camera (fraction of the frame, -1 none)
public:
	void PostAnimTick(float Dt);
	void EndAnimTick();
	FVector PalmWorldCm(bool bRight) const;   // hand bone + PalmOffsetCm along the finger axis (the strand origin)
	static constexpr double PalmOffsetCm = 7.0;
private:
	UPROPERTY(Transient) TObjectPtr<class USkeletalMeshComponent> LensMesh;
	UPROPERTY(Transient) TObjectPtr<class UPointLightComponent> HeroFill; // round 13
	void UpdateHeroFill();
	bool bHeroMesh = false;
	// round 05: pixel measurement of the hero (depth capture that shows only the hero, same camera as the view)
	UPROPERTY(Transient) TObjectPtr<class USceneCaptureComponent2D> MaskCapture;
	UPROPERTY(Transient) TObjectPtr<class UTextureRenderTarget2D> MaskRT;
	float PxTop = -1.f, PxBottom = -1.f, PxLeft = -1.f, PxRight = -1.f;
	FString HeroSil;   // round 04: hero silhouette, 16x16 grid over its mask bbox (hex, 64 chars; '0' = none) -- telemetry only
	float VisTop = -1.f, VisBottom = -1.f; int32 VisPx = -1; // round 20: visible (unoccluded) hero pixels
	// round 08: full-scene depth from the view camera (same 480x270 grid) -> near-wall share and hero occlusion
	UPROPERTY(Transient) TObjectPtr<class USceneCaptureComponent2D> SceneCapture;
	UPROPERTY(Transient) TObjectPtr<class UTextureRenderTarget2D> SceneRT;
	float WallFrac = -1.f, HeroOccl = -1.f;
	void ReadHeroMask();
	double RunPhase = 0.0;
	FVector ReleaseHandCm[2];
	bool bWasReleased[2] = { false, false };
	static constexpr int32 SEGS_PER_STRAND = 12;
};

/** Game mode for traversal test maps: spawns AWebTravCharacter with the mouse-safe controller. */
UCLASS()
class WEBHOMAGE_API AWebTravGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AWebTravGameMode();
};
