// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
// Invincible flight conversion (owner request 2026-10-15): destruction PROXIES for through-building flight, crater landings and
// sonic booms. The procedural city is merged instanced geometry, so it is never fractured itself (that would cost the whole city
// its Nanite / instancing and break the two-renderer GPU budget). Instead, at each breach / landing a bounded set of proxies
// sells the destruction where the hero is:
//   - rubble chunks: pooled cubes simulated by Chaos rigid-body physics (hard cap MaxChunks, recycled oldest-first, 6 s life),
//   - glass spray: pooled thin shards integrated kinematically (no physics cost), tinted glass, fading,
//   - dust: the combat FX dust puffs (FWHCombatFx), a dark scorched-hole plate on the facade / a crater disc on the ground,
//   - optional authored fracture: if /Game/Invincible/Destruction/GC_FacadeChunk exists (a UGeometryCollection built in the editor,
//     see docs/invincible/HANDOFF steps), a crumbling geometry-collection actor is spawned at the hole too (cap MaxGcActors),
//   - optional crater decal: /Game/Invincible/FX/M_CraterDecal (deferred decal material) if it exists,
//   - a short global slow-mo when the camera cuts to the hero bursting out of a breach (-WHNoSlowMo or SlowMoScale 1 disables),
//   - synthesized audio (procedural sound waves: boom, crash, thud) when no authored cue exists at /Game/Invincible/Audio/S_*.
// Collateral damage is added to UWHFlightWorldSubsystem; the crowd reacts through the stimuli the flight component pushes.
//
// Round 3 (critic r2: breaches / sonic boom / craters looked fake). The assets below are built by Scripts/build_invincible_fx.py
// (headless commandlet) into /Game/Invincible/FX/ and are all OPTIONAL: every path falls back to the round-2 proxies when one is missing.
//   - M_BreachHole   deferred decal: procedural jagged near-black opening with a broken concrete rim, cracks and soot (facade, entry + exit),
//   - M_CraterDecal  deferred decal: scorched centre, fractured slab band, radial cracks (ground),
//   - M_InvVapour    translucent unlit fresnel-edged vapour (sonic-boom cone + rings, ground shock ring),
//   - M_InvDust      translucent lit eroded-edge dust puff (dense, larger, longer-lived smoke than the combat FX puffs),
//   - M_InvChunk     opaque lit concrete / brick speckle for debris pieces that did not get the hit facade's own material.
// Debris pieces take the material of the facade component the breach line-traces (opaque / masked surface materials only).
//
// Round 7 (critic r6 #4 / #8):
//   - boom ring: the shock rings wear M_InvShockRing r7 (a HARD, hot leading edge, a short wake, a clear interior); the cone is faint,
//   - breach hole: M_BreachHole r7 draws a recessed interior (reveal + virtual room); lit broken rim chunks are seated on the decal's own
//     analytic outline (BdHoleRadius), clamped to the facade by FitHoleHalf; the decal frame is passed to the material,
//   - debris by what was hit: the facade's merged-mesh "style" (UV channel 4 .y, Facade.ush) picks glass pane shards + steel bits for curtain-wall
//     towers, concrete / brick for masonry, steel for crown tiers (name / height fallbacks when the mesh keeps no CPU copy),
//   - thin / non-building solids (girders, bridges, asphalt, fire escapes, kit pieces) get sparks, a few puffs and steel bits only: no hole decal.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Traversal/WebTravTypes.h"
#include "Combat/WHCombatFx.h"
#include "WHBreachDirector.generated.h"

class UPrimitiveComponent;
class UStaticMeshComponent;
class UStaticMesh;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class USoundBase;
class UDecalComponent;

UCLASS()
class WEBHOMAGE_API AWHBreachDirector : public AActor
{
	GENERATED_BODY()
public:
	AWHBreachDirector();
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;

	/** Feed this frame's flight events (metres, from UWebTraversalComponent::Events). */
	void OnFlightEvents(const TArray<FWebTravEvent>& Events);

	// critic r2 (breaches: "at least 20 debris chunks", mixed sizes): more, smaller pieces; the pool grew with them
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxChunks = 96;    // owner 2026-10-16 (breach lag): 240 live Chaos-simulated chunks hitched the frame
	UPROPERTY(EditAnywhere, Category="Destruction") int32 ChunksPerBreach = 24;   // (owner 2026-10-16 breach lag; was 44)
	UPROPERTY(EditAnywhere, Category="Destruction") int32 ChunksPerCrater = 16;
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxShards = 120;
	UPROPERTY(EditAnywhere, Category="Destruction") int32 ShardsPerBreach = 26;
	UPROPERTY(EditAnywhere, Category="Destruction") float ChunkLife = 6.f;
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxScars = 24;           // fallback scar discs (no decal assets) kept in the world (oldest recycled)
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxHoleDecals = 12;      // r3: facade opening decals kept in the world (oldest recycled)
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxCraterDecals = 6;     // r3: crater decals kept in the world (oldest recycled)
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxPuffs = 110;          // r3: dense dust puffs alive at once
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxRubble = 72;          // r3: static crater-rim rubble pieces kept (oldest recycled)
	UPROPERTY(EditAnywhere, Category="Destruction") int32 PuffsPerBreach = 14;
	UPROPERTY(EditAnywhere, Category="Destruction") float FacadeChunkFraction = 0.5f;   // r3: share of debris pieces that wear the traced facade material (-WHFacadeChunks=)
	UPROPERTY(EditAnywhere, Category="Destruction") float HoleHalfCm = 400.f;      // r3: half size of the opening decal box (the opening is ~39 % of it: ~3.1 m across at severity 0, ~3.7 m at 1)
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxGcActors = 4;
	UPROPERTY(EditAnywhere, Category="Destruction") float SlowMoScale = 1.0f;      // global time dilation at the breach exit cut (owner 2026-10-16: the 0.3x beat read as LAG when flying through buildings -> off; 0.3 was the r1 look)
	/** The pawn's camera cut to the breach exit: start the slow-mo beat. */
	void CutSlowMo();
	UPROPERTY(EditAnywhere, Category="Destruction") float SlowMoReal = 0.32f;      // real seconds at that scale (then eased back over 0.2 s)
	UPROPERTY(EditAnywhere, Category="Destruction") float BreachUSD = 1500000.f;   // + BreachUSDPerSev x severity
	UPROPERTY(EditAnywhere, Category="Destruction") float BreachUSDPerSev = 3000000.f;
	UPROPERTY(EditAnywhere, Category="Destruction") float CraterUSD = 40000.f;
	UPROPERTY(EditAnywhere, Category="Destruction") float CraterUSDPerSev = 400000.f;
	// r3 sonic boom (critic r2: "a vapour cone or ring at least 25 % of frame width stays visible for at least 0.3 s")
	// critic r4 fl04 / fl12 ("concentric flat screen-facing discs", camera inside the 9 m cone, white slab trail): the boom is now a SMALL
	// vapour cone wrapped around the hero's body (apex BoomConeLeadM ahead of his chest, opening back past his hips; the 3/4 chase lens sits
	// outside it, so it reads in perspective), two segmented shock RINGS around him (rings of short vapour tubes, not pancakes: seen
	// off-axis they read as ellipses around the body, and a lens passing through one goes through its hole), a segmented launch ring
	// left where he fired, and a burst of speed lines along the cone. Every vapour / dust piece fades near the lens (CamClearCm).
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomLife = 0.6f;         // s: cone life (r4 1.0)
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomFollow = 0.6f;       // s the cone stays glued to the hero
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomConeLenM = 1.8f;     // cone length at its birth (grows to 1.45x) (r4 9 m, around the camera)
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomConeRadM = 1.3f;     // cone base radius at its birth (grows to 1.7x) (r4 3.2 m)
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomConeLeadM = 1.4f;    // apex ahead of the body centre (m)
	UPROPERTY(EditAnywhere, Category="Destruction") int32 BoomRingSegs = 16;       // vapour tubes per glued shock ring (the launch ring uses 1.25x)
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomOpacity = 0.30f;     // peak of the material's Opacity parameter (0.62 whited out the screen once the vapour became exposure-correct)
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomGain = 1.1f;         // emissive gain of the boom vapour (material default 1.4; exposure-independent white)
	UPROPERTY(EditAnywhere, Category="Destruction") float CamClearCm = 160.f;      // vapour / dust fade out over this distance (cm) as the lens nears them
	UPROPERTY(EditAnywhere, Category="Destruction") float HeroClearMin = 0.12f;    // critic r4 landings: dust on the lens -> hero line keeps at most this share of its opacity
	// critic r6 #4 (fl04 1.517: "a soft filled disc, no edge peak"): bright thin leading edge, clear interior, fast and short-lived
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomRingLife = 0.40f;    // s: the glued rings (the launch ring too)
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomRingMaxM = 4.6f;     // m: radius of the main ring at its end (it starts at 0.5 m)
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomRingOpacity = 0.95f; // peak opacity of the main ring's leading edge
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomRimGain = 3.2f;      // extra emissive on the leading edge (exposure-independent: ~250/255 over sky)
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomConeOpacityK = 0.40f;// share of BoomOpacity the cone keeps (the ring is the read, not a haze)
	// critic r6 #8: hole rim chunks (static, seated on the opening's edge) and glass panes (kinematic, thin, glassy)
	UPROPERTY(EditAnywhere, Category="Destruction") int32 RimPerHole = 10;
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxHoleRim = 40;         // static rim pieces kept in the world (oldest recycled)
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxPanes = 40;           // kinematic glass-tower pane shards alive at once
	UPROPERTY(EditAnywhere, Category="Destruction") float TowerHeightCm = 11000.f; // fallback when the facade style is unreadable: hits above this are taken for curtain-wall towers

	// ---- owner feedback 2026-10-15 #1 (Shift = sonic-boom super boost) / #3 (speed feedback): the charge's vapour gather + slow-mo, a bigger
	// boom (shock ring left at the launch point, shock shell, glass / dust shaken off nearby facades, street dust ring), and continuous
	// super-speed FX: world wind streaks the hero and the camera fly past, a vapour trail / two contrails glued to the body, a dust wake on
	// the street under a low pass. M_InvStreak (additive speed-line material, build_invincible_fx.py) is optional; M_InvVapour stands in.
	/** Per-frame flight state from the pawn: charge 0..1, super-speed weight 0..1, fast-cruise weight 0..1, hero body (m) and velocity (m/s). */
	void SetFlightFx(float ChargeK, float SuperK, float FastK, const FVector& PosM, const FVector& VelM);
	UPROPERTY(EditAnywhere, Category="Destruction") int32 MaxVapours = 180;        // pooled vapour / streak pieces (was a fixed 24; r5 110 -> 180 for the segmented rings)
	UPROPERTY(EditAnywhere, Category="Destruction") float StreakRate = 60.f;       // world wind streaks per second at full super speed
	UPROPERTY(EditAnywhere, Category="Destruction") float FastStreakRate = 14.f;   // per second at full fast-cruise weight outside the super line
	UPROPERTY(EditAnywhere, Category="Destruction") float StreakOpacity = 0.30f;
	UPROPERTY(EditAnywhere, Category="Destruction") float TrailEvery = 0.05f;      // s between body vapour-trail pieces in the super line
	UPROPERTY(EditAnywhere, Category="Destruction") float TrailOpacity = 0.35f;
	UPROPERTY(EditAnywhere, Category="Destruction") float TrailLenM = 1.1f;        // critic r4 fl04 (white slab to the frame corner): body trail length (r4 9-15 m, through the lens)
	UPROPERTY(EditAnywhere, Category="Destruction") float StreakCamClearM = 3.5f;  // world streaks never pass closer than this to the lens path
	UPROPERTY(EditAnywhere, Category="Destruction") float WakeMaxH = 35.f;         // m: a super pass lower than this raises street dust under him
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomRingRadM = 14.f;     // launch shock ring radius at its end (r4 24 m pancake)
	UPROPERTY(EditAnywhere, Category="Destruction") float BoomShakeRadM = 45.f;    // facades within this get glass / dust shaken off at the boom
	UPROPERTY(EditAnywhere, Category="Destruction") float GatherOpacity = 0.25f;   // the charge's gathering vapour shell / inward streaks

private:
	struct FChunk { UStaticMeshComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; FVector Scale = FVector::OneVector; double Born = -1e9, NextCheck = 0; bool bLive = false, bFrozen = false; };
	/** (critic r6 #8: bPane = a glass-tower pane shard, Peak its opacity, faded over the last 45 % of its life) */
	struct FShard { UStaticMeshComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; FVector Pos = FVector::ZeroVector, Vel = FVector::ZeroVector; FQuat Q = FQuat::Identity; FVector Spin = FVector::ZeroVector; double T = 0, Life = 1.5, Peak = 0.7; bool bLive = false, bPane = false; };
	struct FScar { UStaticMeshComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; };
	struct FRing { UStaticMeshComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; FVector Pos = FVector::ZeroVector; FQuat Q = FQuat::Identity; double T = 0, Life = 0.7, R1 = 30; bool bLive = false; };
	/** r3: one dense dust puff (a sphere with the eroded-edge dust material). Hidden until Delay, then Life s; sizes in cm. */
	/** (critic r4 landings: FlatZ squashes the puff vertically -- low ground dust -- and the Tick fades puffs on the lens -> hero line) */
	struct FPuff { UStaticMeshComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; FVector Pos = FVector::ZeroVector, Vel = FVector::ZeroVector; double T = 0, Delay = 0, Life = 1.6, S0 = 100, S1 = 300, Peak = 0.7, Drag = 2.2, Rise = 60, FlatZ = 1.0; bool bLive = false, bShown = false; };
	/** r3: a vapour cone (sonic boom) or a thin pancake ring (boom rings, ground shock ring). Anchor follows the hero for Follow s.
	 *  Owner feedback 2026-10-15 #1: Shape 0 cone, 1 ring (pancake), 2 ball (sphere shell), 3 streak (ellipsoid along Dir, M_InvStreak);
	 *  VelCm drifts a piece that does not follow; SideCm offsets a glued piece sideways; Env 0 fade-out after 40 %, 1 gather (ramps up
	 *  to the end), 2 streak (quick in, fades over the second half). */
	/** critic r4 fl04: Shape 4 = one tube of a segmented shock ring: Anchor is the ring CENTRE (glued: hero + Dir x (OffsetCm - DriftCms x T)),
	 *  Dir the ring axis, RadialU this tube's direction out from the centre; the ring radius goes Rad0 -> Rad1, the tube is SegLenK x radius
	 *  long (tangent) and ThickK x radius thick (clamped 10-60 cm).
	 *  critic r5 #8 (the ring read as a chain of ~20 bubbles): Shape 5 = the whole ring as ONE flattened sphere wearing M_InvShockRing, whose
	 *  opacity is an annulus in the mesh's own radius (Band = ring radius / mesh radius, BandW = tube half thickness / mesh radius): a continuous
	 *  band, clear in the middle. Same anchor / drift / radius / ThickK (clamped 12-70 cm) fields as shape 4. */
	struct FVapour { UStaticMeshComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; FVector Anchor = FVector::ZeroVector, Dir = FVector::ForwardVector; double T = 0, Life = 0.9, Follow = 0.45, OffsetCm = 0, Len0 = 700, Len1 = 1100, Rad0 = 240, Rad1 = 560, Peak = 0.55; bool bCone = true, bLive = false;
		int32 Shape = 0, Env = 0; FVector VelCm = FVector::ZeroVector, SideCm = FVector::ZeroVector;
		FVector RadialU = FVector::RightVector; double SegLenK = 0.5, ThickK = 0.08, DriftCms = 0.0; };
	/** r3: a deferred decal with an animated "Open" parameter (the opening / crater grows over Grow s). */
	/** (critic r5 #3: fl15 3.85 s / fl11 2.28 s / fl17 20.68 s -- the whole box of a FIRST-USE decal rendered as a flat dark panel for exactly one
	 *  frame, two frames after it was placed. The pools are now created at BeginPlay with their shaders finished, and a placed decal is shown from
	 *  the next engine frame on, with its parameters already set: bPendingShow / PlacedFrame.) */
	struct FDecalItem { UDecalComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr; double T = 0, Grow = 0.2; bool bGrowing = false, bPendingShow = false; uint64 PlacedFrame = 0; };
	/** r3: static (non-physics) rubble pieces of the crater rim: they sit on the traced ground, so they cannot hang in the air. */
	/** (critic r6 #8: GlassMid = the pane material of a hole-rim piece that is a glass tooth; the piece switches between Mid / GlassMid when recycled) */
	struct FRubble { UStaticMeshComponent* Comp = nullptr; UMaterialInstanceDynamic* Mid = nullptr, *GlassMid = nullptr; FVector Pos = FVector::ZeroVector, Scale = FVector::OneVector; FQuat Q = FQuat::Identity; double T = 0, Delay = 0, Life = 25; bool bLive = false; };
	/** r3: what the line trace at a breach / crater found (cm).
	 *  critic r6 #8: with bDescribe the first surface is named (Tag = lower-case component / actor / mesh / material names), a city facade material anywhere
	 *  along the trace sets bFacadeSeen and its merged-mesh style (Facade.ush: 1 masonry, 2 curtain glass, 3 ribbon, 4 deco, 5 party wall, 6 steel crown; -1 unknown). */
	struct FFacadeHit { bool bHit = false; FVector Point = FVector::ZeroVector, Normal = FVector::UpVector; UMaterialInterface* Mat = nullptr; FString Tag; bool bFacadeSeen = false; int32 Style = -1; };
	/** critic r6 #8: what a breach went through (picks the debris set, the hole's rim and the dust; Thin = no hole at all) */
	enum class EBdSurf : uint8 { Masonry, Glass, Steel, Thin };

	void Breach(const FVector& PosM, const FVector& DirM, float Sev, bool bEntry);
	void Crater(const FVector& PosM, float Sev);
	void Boom(const FVector& PosM, const FVector& DirM);
	void Bump(const FVector& PosM, const FVector& NormalM, float Sev);
	/** the old signature: debris along DirN (kept for the fallback paths) */
	void SpawnChunks(const FVector& PosCm, const FVector& DirN, int32 N, double SpeedCms, const FLinearColor& Tint, double SizeCm);
	/** r3 debris: N pieces of mixed size (many 8-25 cm, a few to 50 cm) scattered on a disc of SpawnRadiusCm around OriginCm, flung along Axis (share AxisBias) and radially;
	 *  a share of them (FacadeChunkFraction) wears Look (the traced facade material), the rest M_InvChunk / flat tints (Brick = share of those that are brick).
	 *  critic r6 #8: Set 1 = steel bits (thin bars / plates, steel tints, never the facade look), SizeScale scales every piece. */
	void SpawnDebris(const FVector& OriginCm, const FVector& Axis, double SpawnRadiusCm, double SpeedCms, double AxisBias, int32 N, UMaterialInterface* Look, const FLinearColor& Tint, float Brick, int32 Set = 0, float SizeScale = 1.f);
	void SpawnShards(const FVector& PosCm, const FVector& DirN, int32 N, double SpeedCms);
	/** critic r6 #8: glass-tower pane shards -- 18-55 cm flat 1.6 cm boxes with M_InvGlassShard (translucent, glints), kinematic like the glints */
	void SpawnPanes(const FVector& PosCm, const FVector& DirN, int32 N, double SpeedCms);
	void PlaceScar(const FVector& PosCm, const FQuat& Q, const FVector& ScaleM, const FLinearColor& Color);
	void SpawnGc(const FVector& PosCm, const FVector& DirN);
	void StartSlowMo();
	void PlaySynth(int32 Kind, const FVector& PosCm, float Volume);   // 0 boom, 1 crash, 2 thud
	USoundBase* Authored(int32 Kind) const;
	UStaticMeshComponent* MakeComp(UStaticMesh* Mesh, UMaterialInterface* Base, UMaterialInstanceDynamic*& OutMid, bool bShadow);

	// ---- round 3
	/** line trace A -> B (cm) against the world's solids; fills point / normal of the first hit and the first visible opaque surface material along the line */
	bool TraceFacade(const FVector& StartCm, const FVector& EndCm, FFacadeHit& Out, bool bDescribe = false) const;
	/** critic r6 #8: names the first surface the trace hit and (for a city facade material) reads its style from the triangle's vertices */
	void DescribeSurface(UPrimitiveComponent* C, UMaterialInterface* M, int32 FaceIndex, FFacadeHit& Out) const;
	/** critic r6 #8: what the breach went through. SpanCm = the narrower in-plane extent of the facade plane around the hit (-1 unknown) */
	EBdSurf ClassifyHit(const FFacadeHit& H, bool bOnWall, const FVector& PointCm, double SpanCm) const;
	/** critic r6 #8 (fl15: "a small hole in a bridge girder"): a thin / non-building solid -- sparks, a few puffs and steel bits, no hole */
	void ThinStrike(const FVector& PtCm, const FVector& N, const FVector& D, float Sev, bool bEntry);
	/** nearest ground below P (cm): z of the surface (or P.Z when nothing is found) and its material */
	double TraceGroundZ(const FVector& PCm, UMaterialInterface** OutMat = nullptr) const;
	void ProbeCone();
	void ExcludeHeroFromDecals();
	FDecalItem* AcquireDecal(TArray<FDecalItem>& Pool, int32& Next, int32 MaxN, UMaterialInterface* Mat);
	/** critic r5 #3 / #8: decal pools, part of the debris pool and the FX shaders are made ready at BeginPlay (no first-use frame) */
	void PrewarmPools();
	/** critic r5 #8 (fl14 5.35-5.40 s: the opening decal ran past the wall edge over the background): the decal half size (cm) that stays on the
	 *  facade plane around PointCm (probed with line traces along its in-plane axes; OutShift = in-plane centre shift away from a near edge) */
	double FitHoleHalf(const FVector& PointCm, const FVector& OutN, double Half, FVector& OutShift, double* OutSpanCm = nullptr) const;
	FChunk* NewChunk();
	/** (critic r6 #8: Half / Shift = the fitted decal box from FitHoleHalf; Kind picks the rim look; the decal's frame goes to the material, bOnWall seats rim chunks on its edge) */
	void PlaceHole(const FVector& PointCm, const FVector& IntoWall, float Sev, double Half, const FVector& Shift, EBdSurf Kind, bool bOnWall);
	/** critic r6 #8: lit broken rim -- RimPerHole static pieces on the opening's analytic outline (BdHoleRadius = the shader's), standing off the facade plane */
	void SpawnHoleRim(const FVector& CentreCm, const FVector& U, const FVector& V, const FVector& N, double HalfCm, double Seed, EBdSurf Kind);
	void PlaceCraterDecal(const FVector& PCm, float Sev);
	void SpawnPuff(const FVector& PosCm, const FVector& VelCms, double S0, double S1, double Life, double Peak, double DelayS, const FLinearColor& Col, double FlatZ = 1.0, double RiseCms = -1.0);
	void BreachDust(const FVector& PointCm, const FVector& OutN, const FVector& FlightDir, float Sev, bool bEntry, EBdSurf Kind = EBdSurf::Masonry);
	void CraterDust(const FVector& PCm, float Sev);
	void SpawnVapour(bool bCone, const FVector& AnchorCm, const FVector& Dir, double FollowS, double OffsetCm, double Len0, double Len1, double Rad0, double Rad1, double Peak, double Life, float EdgePow);
	void SpawnRim(const FVector& PCm, float Sev, UMaterialInterface* GroundMat);
	// owner feedback 2026-10-15 #1 / #3
	FVapour* SpawnShape(int32 Shape, const FVector& AnchorCm, const FVector& Dir, double FollowS, double OffsetCm, double Len0, double Len1, double Rad0, double Rad1, double Peak, double Life, float EdgePow, int32 Env);
	void ChargeFx(const FVector& PosM, const FVector& DirM, float SlowScale, float RealDur);
	/** critic r4 fl04: one segmented shock ring of NSeg vapour tubes around the axis Dir at CentreCm (glued to the hero for FollowS s)
	 *  critic r6 #4: Env 3 = the ring envelope (snaps in over 15 ms, holds, fades from 30 % of its life), RimScale scales the leading edge's extra gain;
	 *  ThickK is the tube half thickness / radius as given (clamped 12-70 cm), no longer x 1.5 */
	void SpawnRing(const FVector& CentreCm, const FVector& Dir, int32 NSeg, double FollowS, double OffsetCm, double DriftCms, double R0, double R1, double ThickK, double Peak, double Life, int32 Env = 0, double RimScale = 1.0);
	/** the player's view location (cm) this frame; false without a camera manager */
	bool ViewPos(FVector& OutCm) const;
	/** 0..1 visibility factor of a vapour / dust piece at distance DistCm from the lens (fades over CamClearCm) */
	double CamFade(double DistCm) const;
	void ShakeFacades(const FVector& PCm);
	void FlightFxTick(double Dt);
	void EndChargeSlowMo();

	FWHCombatFx Fx;
	UPROPERTY(Transient) TObjectPtr<UStaticMesh> Cube;
	UPROPERTY(Transient) TObjectPtr<UStaticMesh> Cyl;
	UPROPERTY(Transient) TObjectPtr<UStaticMesh> Sphere;
	UPROPERTY(Transient) TObjectPtr<UStaticMesh> Cone;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MSolid;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MTrans;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MGlow;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MDecal;     // crater decal (M_CraterDecal)
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MHole;      // facade opening decal (M_BreachHole)
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MVapour;    // M_InvVapour
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MDust;      // M_InvDust
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MChunk;     // M_InvChunk
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MStreak;    // M_InvStreak (owner feedback 2026-10-15: additive speed lines; optional)
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MRing;      // M_InvShockRing (critic r5 #8: one continuous vapour annulus; optional, tubes fall back)
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MGlassShard; // M_InvGlassShard (critic r6 #8: glass-tower pane shards; optional, M_CmbTrans falls back)
	UPROPERTY(Transient) TObjectPtr<UObject> GcAsset;
	UPROPERTY(Transient) TArray<TObjectPtr<UObject>> KeepAlive;   // components / MIDs created at runtime (never trimmed)
	UPROPERTY(Transient) TArray<TObjectPtr<UObject>> AudioKeep;   // procedural sound waves (trimmed)
	UPROPERTY(Transient) TArray<TObjectPtr<AActor>> GcActors;
	TWeakObjectPtr<UMaterialInterface> LastFacadeMat;             // the last traced facade material (bumps reuse it)
	TArray<FChunk> Chunks;
	TArray<FShard> Shards;
	TArray<FShard> Panes;       // critic r6 #8
	TArray<FScar> Scars;
	TArray<FRing> Rings;
	TArray<FPuff> Puffs;
	TArray<FVapour> Vapours;
	TArray<FDecalItem> HoleDecals, CraterDecals;
	TArray<FRubble> Rubble;
	TArray<FRubble> HoleRim;    // critic r6 #8: static rim pieces of the breach openings
	int32 NextChunk = 0, NextShard = 0, NextScar = 0, NextGc = 0, NextPuff = 0, NextVapour = 0, NextHole = 0, NextCrater = 0, NextRubble = 0, NextPane = 0, NextHoleRim = 0;
	FRandomStream Rng = FRandomStream(20261015);
	double SlowMoUntil = -1.0, SlowMoEaseEnd = -1.0;
	bool bSlowMo = false, bNoSlowMo = false, bNoAudio = false;
	double LastCutSlowMoT = -100.0;
	double LastBumpTraceT = -100.0;
	double ConeHCm = 100.0, ConeWCm = 100.0, ConeMidZCm = 0.0;   // /Engine/BasicShapes/Cone bounds (cm) and which end is the apex
	bool bConeApexUp = true;
	FVector LastBreachEntry = FVector::ZeroVector;
	// owner feedback 2026-10-15 #1 / #3: flight FX state (set by SetFlightFx every pawn frame; cm / cm/s) and the charge slow-mo (real time)
	float FxChargeK = 0.f, FxSuperK = 0.f, FxFastK = 0.f;
	FVector FxPosCm = FVector::ZeroVector, FxVelCm = FVector::ZeroVector;
	bool bFxValid = false;
	FVector CamCm = FVector::ZeroVector;   // critic r4: the view location this tick (fades, streak placement)
	bool bCamOk = false;
	double StreakAcc = 0.0, TrailT = 0.0, WakeT = 0.0, GatherT = 0.0;
	bool bChargeSlow = false;
	double ChargeSlowEnd = 0.0;
};
