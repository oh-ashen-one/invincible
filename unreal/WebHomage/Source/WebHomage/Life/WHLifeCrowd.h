// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
// P6 City life: sidewalk crowd. Walkers are simulated cheaply and analytically on the pedestrian graph exported by
// tools/life/export_lanes.mjs (sidewalk corners, sidewalk edges along the avenue / street sides, crosswalk edges); only the
// walkers near the camera own a skeletal-mesh component (pooled per citizen model), so hundreds of walkers cost as much as the
// ~150 that can be seen. Every live walker plays P2's citizen walk cycle through UWHCharAnimInstance at the exact ground speed
// it moves (ForcedSpeed = actor speed, clip rate = speed / clip speed), so feet stay planted; each walker starts at a random
// gait phase. Walkers wait at crosswalks for the traffic signal (shared clock with AWHLifeTraffic).
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WHLifeCrowd.generated.h"

class USkeletalMesh;
class USkeletalMeshComponent;
class UAnimInstance;
class AWHLifeTraffic;
class UMaterialInterface;
class UDirectionalLightComponent;

namespace WHLife
{
	struct FWalker
	{
		int32 Model = 0, Edge = -1, Node = -1;   // Node = corner the walker is walking towards
		int8 Dir = 1;
		float S = 0.f;                            // progress along the edge in the travel direction (m)
		FVector2D Pos = FVector2D::ZeroVector;    // metres, browser frame
		float Heading = 0.f, Speed = 1.1f, Base = 1.1f, Lat = 0.8f, Scale = 1.f, WaitT = 0.f;
		uint8 State = 0;                          // 0 walking, 1 waiting at a corner for the walk signal
		int32 NextEdge = -1;
		float Target = 1.1f;                      // desired speed on this edge (m/s); Speed follows it with a limited acceleration
		bool bDecided = false;                    // NextEdge already chosen for the end of this edge
		int32 Comp = -1;                          // pool slot while live
		uint32 Rng = 1;
		float Tint = 1.f;
		uint8 Shade = 0; float ShadeT = 0.f;      // 1 = the sun is blocked at this walker (fill light on), next sun-visibility test time (game s)
		float LatAdj = 0.f, AdjTarget = 0.f;      // sidestep around walkers ahead (metres, right-hand positive); AdjTarget from UpdateAvoidance, LatAdj follows it
	};
}

UCLASS()
class WEBHOMAGE_API AWHLifeCrowd : public AActor
{
	GENERATED_BODY()
public:
	AWHLifeCrowd();
	virtual void BeginPlay() override;
	virtual void Tick(float Dt) override;

	/** Scripts/life_data/walk.txt (written by Scripts/build_life.py). */
	UPROPERTY(EditAnywhere, Category="Life|Data", meta=(MultiLine=true)) FString WalkData;
	/** Citizen skeletal meshes (materials are on the meshes). Distinct models: index = model id. */
	UPROPERTY(EditAnywhere, Category="Life|Data") TArray<TObjectPtr<USkeletalMesh>> Meshes;
	/** Optional per-model material override (same length as Meshes, entries may be null): outfit variants share one mesh. */
	UPROPERTY(EditAnywhere, Category="Life|Data") TArray<TObjectPtr<UMaterialInterface>> MaterialOverrides;
	/** Anim blueprint (child of UWHCharAnimInstance) shared by the citizen skeleton. */
	UPROPERTY(EditAnywhere, Category="Life|Data") TSubclassOf<UAnimInstance> AnimClass;
	/** Optional: the traffic actor whose signal clock the crowd obeys. */
	UPROPERTY(EditAnywhere, Category="Life|Data") TObjectPtr<AWHLifeTraffic> Traffic;

	UPROPERTY(EditAnywhere, Category="Life") int32 Seed = 11;
	/** Walkers per km of sidewalk edge, by road kind (edge axis 0 = avenue sidewalks, 1 = street sidewalks). Two-way flow: half walk each way. */
	UPROPERTY(EditAnywhere, Category="Life") float PerKmAvenue = 1600.f;
	UPROPERTY(EditAnywhere, Category="Life") float PerKmStreet = 1100.f;
	/** Density factor of the EAST sidewalks of the avenues (walk graph Side +1). The east side of a Midtown avenue is the shaded one in the afternoon sun of the test maps (and in S1 sits behind scaffolding
	 *  sheds and pillars), and a street-level camera in the lanes sees it at a grazing angle across the whole roadway: with equal densities it reads as the thinner sidewalk (round 02: 0-17 % of the people
	 *  the detector finds were on the right). 1 = both sides equal. Command line: -WHLifeEast=<factor>. */
	UPROPERTY(EditAnywhere, Category="Life") float AvenueEastFactor = 1.3f;
	/** Camera-centred population: walkers exist within this distance (cm) of the camera; farther ones are recycled to the far edge of the disc
	 *  (out of view when possible), so the density around the camera stays high wherever it goes and the cost stays bounded. */
	UPROPERTY(EditAnywhere, Category="Life") float SpawnRadius = 19000.f;
	UPROPERTY(EditAnywhere, Category="Life") int32 MaxWalkers = 6000;
	/** cm: walkers farther than this from the camera are simulated but have no mesh. A camera above HighCamFromCm (a swing, a rooftop, the S2 view) sees people much farther down the
	 *  avenue: the live radius grows linearly to LiveRadiusHigh at HighCamToCm. */
	UPROPERTY(EditAnywhere, Category="Life") float LiveRadius = 11000.f;
	UPROPERTY(EditAnywhere, Category="Life") float LiveRadiusHigh = 18000.f;
	UPROPERTY(EditAnywhere, Category="Life") float HighCamFromCm = 1200.f;
	UPROPERTY(EditAnywhere, Category="Life") float HighCamToCm = 3200.f;
	/** Live walkers must be inside the camera's view cone widened by this many degrees (or closer than NearAllRadius, in any direction). */
	UPROPERTY(EditAnywhere, Category="Life") float ViewMarginDeg = 30.f;
	UPROPERTY(EditAnywhere, Category="Life") float NearAllRadius = 1000.f;
	/** Looks per citizen mesh (the mesh list is variant-major: index = variant * NumCitizens + citizen), used to keep the same head from appearing twice near each other. */
	UPROPERTY(EditAnywhere, Category="Life") int32 NumVariants = 5;
	UPROPERTY(EditAnywhere, Category="Life") int32 MaxAssignPerRefresh = 14;
	UPROPERTY(EditAnywhere, Category="Life") int32 PoolPerModel = 6;
	/** Sidewalk walking band, metres from the edge line measured toward the roadway (negative = toward the buildings): P1 puts trees, lamps, hydrants and litter bins
	 *  in the curb strip, so people keep to the building side of it. Avenue sidewalks are 5 m wide (line 2.2 m from the curb), street sidewalks 4 m. */
	UPROPERTY(EditAnywhere, Category="Life") float AvenueBandMin = -2.25f;
	UPROPERTY(EditAnywhere, Category="Life") float AvenueBandMax = 0.25f;
	UPROPERTY(EditAnywhere, Category="Life") float StreetBandMin = -1.65f;
	UPROPERTY(EditAnywhere, Category="Life") float StreetBandMax = 0.2f;
	/** Street-level camera personal space (m): walkers step around the camera instead of walking through it (only when the camera is below 4.5 m). */
	UPROPERTY(EditAnywhere, Category="Life") float CameraAvoidRadius = 0.85f;
	/** Walkers farther than this (cm) from the camera do not cast shadows (the virtual shadow map cost of a skinned mesh is high, the shadow is a few pixels). */
	UPROPERTY(EditAnywhere, Category="Life") float ShadowRadius = 6500.f;
	/** Clip speed (cm/s) at which the citizen walk cycle plays at rate 1 without foot sliding (P2: stride 1.1543 m / (32/30 s) = 108). */
	UPROPERTY(EditAnywhere, Category="Life") float ClipSpeed = 108.f;
	UPROPERTY(EditAnywhere, Category="Life") float SpeedMin = 100.f;
	UPROPERTY(EditAnywhere, Category="Life") float SpeedMax = 135.f;
	UPROPERTY(EditAnywhere, Category="Life") float SidewalkZ = 15.f;
	UPROPERTY(EditAnywhere, Category="Life") bool bCastShadows = true;
	/** Ray tracing (Lumen hardware RT) sees the walkers. Off by default: skinned meshes need a BLAS refit per frame. */
	UPROPERTY(EditAnywhere, Category="Life") bool bVisibleInRayTracing = false;
	UPROPERTY(EditAnywhere, Category="Life") float StatsInterval = 0.f;
	/** Character fill light (round 03): one unshadowed directional light on lighting channel 1 that only the walkers use (no GI contribution), aimed along the camera
	 *  view and pitched down FillPitchDeg. It lifts walkers standing in deep shade (sidewalk sheds, canyon floors) so they read as people instead of black cut-outs.
	 *  Lux; 0 = off. Command line: -WHLifeFill=<lux>, -WHLifeFillSteps=<t>:<lux>,<t>:<lux>... (game seconds, for sweeps), -WHLifeFillPitch=<deg>. */
	UPROPERTY(EditAnywhere, Category="Life|Fill") float FillLux = 1800.f;
	/** The fill applies only to walkers the sun does not reach (a line trace towards the atmosphere sun light, every ~1 s per live walker): people in the sun keep their natural light. -WHLifeFillAll turns it off (everyone gets the fill). */
	UPROPERTY(EditAnywhere, Category="Life|Fill") bool bFillShadeOnly = true;
	UPROPERTY(EditAnywhere, Category="Life|Fill") float FillPitchDeg = 38.f;
	UPROPERTY(EditAnywhere, Category="Life|Fill") float FillTemperature = 5200.f;
	/** Share of walkers that keep to the right half of the sidewalk band (in their own direction of travel): opposite flows use opposite halves instead of walking through each other. */
	UPROPERTY(EditAnywhere, Category="Life") float KeepRight = 0.78f;
	/** Camera faster than this (cm/s): walkers recycled from behind reappear AHEAD of the camera's motion (a fast swing keeps a full sidewalk in front of it), not off-screen anywhere. */
	UPROPERTY(EditAnywhere, Category="Life") float AheadSpeedCms = 500.f;
	/** Cosine of the half angle of the sector ahead of a fast camera in which recycled walkers are placed (0.9 = 26 deg). A wide sector (round 03 first build: 0.5 = 60 deg) put four of five of them on cross-street sidewalks
	 *  hundreds of metres to the side of the avenue the camera follows, so the avenue's own sidewalks thinned out in mid flight. Command line -WHLifeAheadCos=<cos>. */
	UPROPERTY(EditAnywhere, Category="Life") float AheadCosMin = 0.9f;
	/** Fixed camera for the live set (test rigs); ignored if zero. */
	UPROPERTY(EditAnywhere, Category="Life") FVector FocusOverride = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category="Life|Stats") int32 NumWalkers = 0;
	UPROPERTY(BlueprintReadOnly, Category="Life|Stats") int32 NumLive = 0;
	UPROPERTY(BlueprintReadOnly, Category="Life|Stats") int32 NumWaiting = 0;
	UPROPERTY(BlueprintReadOnly, Category="Life|Stats") int32 NumShade = 0;
	UPROPERTY(BlueprintReadOnly, Category="Life|Stats") float LastSimMs = 0.f;

	UFUNCTION(BlueprintCallable, Category="Life") FString StatsString() const;
	/** Live walkers (C++ only): world positions of the feet-level pivot (cm), model ids, and their skeletal components. */
	void GetLive(TArray<FVector>& Pos, TArray<int32>& Model, TArray<USkeletalMeshComponent*>& Comps, TArray<float>& Speed) const;
	/** Live walkers whose position is inside a cone in front of Eye (also returns the number of distinct models via OutModels). */
	UFUNCTION(BlueprintCallable, Category="Life") int32 CountInCone(FVector Eye, FVector Forward, float HalfAngleDeg, float Range, int32& OutModels) const;

private:
	struct FEdge { int32 A = 0, B = 0, Kind = 0, Axis = 0, Side = 0; float Len = 0.f; FVector2D U = FVector2D::ZeroVector; };
	TArray<FVector2D> Pts;
	TArray<FEdge> Edges;
	TArray<TArray<int32>> Adj; // node -> edge indices
	TArray<WHLife::FWalker> Walkers;
	UPROPERTY(Transient) TArray<TObjectPtr<USkeletalMeshComponent>> Pool;
	TArray<int32> PoolModel;                 // model of each pool slot
	TArray<TArray<int32>> FreeSlots;         // per model
	TArray<int32> SlotOwner;                 // pool slot -> walker (-1 free)
	double Clock = 0.0;
	float RefreshT = 0.f, StatsT = 0.f;
	bool bReady = false;

	void ParseWalk();
	void Populate(const FVector& Cam);
	void SpawnWalker(WHLife::FWalker& W, int32 EI, uint32& R, int8 Dir, float S);
	bool Respawn(WHLife::FWalker& W, const FVector& Cam, bool bPreferOffscreen);
	bool GetView(FVector& OutLoc, FVector& OutFwd, float& OutHalfDeg) const;
	TArray<float> EdgeCum;                   // cumulative length * density over the sidewalk edges (respawn picks)
	FVector Center = FVector::ZeroVector;
	FVector2D AvoidM = FVector2D::ZeroVector; bool bAvoid = false;   // camera ground position (m) walkers avoid
	float LatFor(const FEdge& E, int8 Dir, uint32& R) const;
	bool bCentered = false;
	int32 FirstRefreshes = 0, TickCount = 0;
	UPROPERTY(Transient) TObjectPtr<UDirectionalLightComponent> FillLight;
	TArray<TPair<float, float>> FillSteps;   // (game s, lux) sweep from -WHLifeFillSteps
	TArray<int32> RespIdx; TArray<float> RespCum;   // sidewalk edges that reach the recycle ring around the camera (rebuilt at every refresh), cumulative length * density
	void BuildRespawnEdges(const FVector& Cam);
	float EdgeDensity(const FEdge& E) const { return E.Axis == 0 ? PerKmAvenue * (E.Side > 0 ? AvenueEastFactor : 1.f) : PerKmStreet; }   // walkers per km of this sidewalk edge
	FVector PrevCam = FVector::ZeroVector, CamVel = FVector::ZeroVector; bool bHavePrevCam = false;   // camera velocity (cm/s), smoothed
	void UpdateFill();
	void UpdateShade();
	void TestShade(WHLife::FWalker& W, struct FCollisionQueryParams& Q, double Now);
	FVector SunDir = FVector::ZeroVector; bool bHaveSun = false; double NextSunSearch = 0.0; int32 ShadeCursor = 0;
	void UpdateAvoidance();
	void PickNextEdge(WHLife::FWalker& W);
	FVector2D LinePos(const FEdge& E, int8 Dir, float S) const { return Dir > 0 ? Pts[E.A] + E.U * S : Pts[E.B] - E.U * S; }
	void StepWalker(WHLife::FWalker& W, float Dt);
	void EnterEdge(WHLife::FWalker& W, int32 Edge, int32 FromNode, bool bKeepPos);
	bool MayCross(const FEdge& E, float Speed) const;
	/** No car body is on / next to the crosswalk edge right now (cached 0.25 s per edge): people wait for the crosswalk to clear as well as for the walk signal. */
	bool CrosswalkClear(int32 EdgeIdx);
	TMap<int32, TPair<double, bool>> XClear;
	void RefreshLive(const FVector& Cam);
	void Assign(int32 WalkerI, int32 Slot);
	void Unassign(int32 WalkerI);
	void Apply(WHLife::FWalker& W);
	FVector CameraLocation() const;
	double SignalClock() const;
};
