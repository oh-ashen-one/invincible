// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Look/WHCityLights.h"
#include "Life/WHLifeTraffic.h"
#include "Look/WHLookHeroLight.h"
#include "WebHomage.h"

#include "Camera/PlayerCameraManager.h"
#include "Components/PointLightComponent.h"
#include "Components/RectLightComponent.h"
#include "Components/SpotLightComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "UnrealClient.h"

static TAutoConsoleVariable<int32> CVarEnable(TEXT("wh.CityLights.Enable"), 1, TEXT("0 disables the night city lights (all pooled lights released)."));
static TAutoConsoleVariable<float> CVarGain(TEXT("wh.CityLights.Gain"), 1.f, TEXT("Global multiplier of every pooled light."));
static TAutoConsoleVariable<float> CVarBudgetScale(TEXT("wh.CityLights.BudgetScale"), 1.f, TEXT("Scales every group budget (capped by the pool size)."));
static TAutoConsoleVariable<int32> CVarDebug(TEXT("wh.CityLights.Debug"), 0, TEXT("1: on-screen and log counts per category, active lights, ambient."));
static FAutoConsoleCommandWithWorld CmdReload(TEXT("wh.CityLights.Reload"), TEXT("Re-read Content/Night/CityLights.json"),
	FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
	{
		if (!World) return;
		for (TActorIterator<AWHCityLights> It(World); It; ++It) It->ReloadConfig();
	}));

static FString NightDir() { return FPaths::ProjectContentDir() / TEXT("Night"); }

// ------------------------------------------------------------------------------------------------ config
bool FWHCLConfig::Load(const FString& Path, FString& Err)
{
	FString Txt;
	if (!FFileHelper::LoadFileToString(Txt, *Path)) { Err = FString::Printf(TEXT("missing %s"), *Path); return false; }
	TSharedPtr<FJsonObject> J;
	if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Txt), J) || !J.IsValid()) { Err = FString::Printf(TEXT("unparsable %s"), *Path); return false; }
	auto F = [&](const TCHAR* K, float& V) { double D; if (J->TryGetNumberField(K, D)) V = float(D); };
	F(TEXT("K"), K); F(TEXT("EmissiveK"), EmissiveK); F(TEXT("fade_s"), FadeS); F(TEXT("rebuild_move_cm"), RebuildMoveCm); F(TEXT("rebuild_interval_s"), RebuildIntervalS);
	F(TEXT("volumetric_gain"), VolumetricGain); F(TEXT("shadow_radius_cm"), ShadowRadiusCm); F(TEXT("night_off_below"), NightOffBelow); F(TEXT("pool_headroom"), PoolHeadroom);
	int32 SS; if (J->TryGetNumberField(TEXT("shadow_slots"), SS)) ShadowSlots = SS;
	const TSharedPtr<FJsonObject>* Amb;
	if (J->TryGetObjectField(TEXT("ambient"), Amb))
	{
		auto A = [&](const TCHAR* Key, float& V) { double D; if ((*Amb)->TryGetNumberField(Key, D)) V = float(D); };
		A(TEXT("AMB_R"), AmbR); A(TEXT("AMB_SOFT"), AmbSoft); A(TEXT("AMB_GAIN"), AmbGain); A(TEXT("layer_y_m"), LayerYm); A(TEXT("hero_fill_base"), HeroFillBase); A(TEXT("hero_irradiance_scale"), HeroIrradianceScale);
	}
	const TSharedPtr<FJsonObject>* CP;
	if (J->TryGetObjectField(TEXT("cars_provider"), CP))
	{
		const TSharedPtr<FJsonObject>* H; const TSharedPtr<FJsonObject>* T; const TSharedPtr<FJsonObject>* B;
		auto Hex = [](const TSharedPtr<FJsonObject>& O, const TCHAR* K, uint32& V) { FString S; if (O->TryGetStringField(K, S)) V = (uint32)FParse::HexNumber(*S.Replace(TEXT("0x"), TEXT(""))); };
		auto Num = [](const TSharedPtr<FJsonObject>& O, const TCHAR* K, float& V) { double D; if (O->TryGetNumberField(K, D)) V = float(D); };
		FWHCLCarsCfg& CC = CarsCfg;
		if ((*CP)->TryGetObjectField(TEXT("headlight"), H))
		{
			Hex(*H, TEXT("color_hex"), CC.HeadHex); Num(*H, TEXT("intensity_per_lamp"), CC.HeadI); Num(*H, TEXT("intensity_times_square"), CC.HeadITimesSquare); Num(*H, TEXT("merged_factor"), CC.HeadMerged);
			Num(*H, TEXT("range_m"), CC.HeadRangeM); Num(*H, TEXT("angle_rad"), CC.HeadAngle); Num(*H, TEXT("penumbra"), CC.HeadPenumbra); Num(*H, TEXT("radius_m"), CC.HeadRadiusM);
			Num(*H, TEXT("volume"), CC.HeadVolume); Num(*H, TEXT("spec"), CC.HeadSpec); Num(*H, TEXT("tilt_down_rad"), CC.HeadTilt); Num(*H, TEXT("height_m"), CC.HeadHeightM);
			Num(*H, TEXT("front_extra_m"), CC.HeadFrontExtraM); Num(*H, TEXT("lateral_inset_m"), CC.HeadInsetM); Num(*H, TEXT("min_lateral_m"), CC.MinLateralM);
		}
		if ((*CP)->TryGetObjectField(TEXT("taillight"), T))
		{
			Hex(*T, TEXT("color_hex"), CC.TailHex); Num(*T, TEXT("intensity"), CC.TailI); Num(*T, TEXT("intensity_braking"), CC.TailIBraking); Num(*T, TEXT("range_m"), CC.TailRangeM);
			Num(*T, TEXT("radius_m"), CC.TailRadiusM); Num(*T, TEXT("volume"), CC.TailVolume); Num(*T, TEXT("height_m"), CC.TailHeightM); Num(*T, TEXT("back_extra_m"), CC.TailBackExtraM);
			Num(*T, TEXT("lateral_inset_m"), CC.TailInsetM); Num(*T, TEXT("max_distance_m"), CC.TailMaxDistM);
		}
		double D; if ((*CP)->TryGetNumberField(TEXT("twin_cars"), D)) CC.TwinCars = int32(D);
		if ((*CP)->TryGetObjectField(TEXT("times_square_box_m"), B))
		{
			const TArray<TSharedPtr<FJsonValue>>* X; const TArray<TSharedPtr<FJsonValue>>* Z;
			if ((*B)->TryGetArrayField(TEXT("x"), X) && X->Num() == 2) { CC.TsX0 = float((*X)[0]->AsNumber()); CC.TsX1 = float((*X)[1]->AsNumber()); }
			if ((*B)->TryGetArrayField(TEXT("z"), Z) && Z->Num() == 2) { CC.TsZ0 = float((*Z)[0]->AsNumber()); CC.TsZ1 = float((*Z)[1]->AsNumber()); }
		}
	}
	const TArray<TSharedPtr<FJsonValue>>* Gs;
	if (!J->TryGetArrayField(TEXT("groups"), Gs) || Gs->Num() == 0) { Err = TEXT("no groups in config"); return false; }
	Groups.Reset();
	for (const TSharedPtr<FJsonValue>& V : *Gs)
	{
		const TSharedPtr<FJsonObject> O = V->AsObject(); if (!O.IsValid()) continue;
		FWHCLGroupCfg G; G.Name = O->GetStringField(TEXT("name"));
		for (const TSharedPtr<FJsonValue>& C : O->GetArrayField(TEXT("categories"))) G.Cats.Add(int32(C->AsNumber()));
		double D;
		if (O->TryGetNumberField(TEXT("budget"), D)) G.Budget = int32(D);
		if (O->TryGetNumberField(TEXT("radius_m"), D)) G.RadiusCm = float(D) * 100.f;
		if (O->TryGetNumberField(TEXT("min_radius_m"), D)) G.MinRadiusCm = float(D) * 100.f;
		if (O->TryGetNumberField(TEXT("tile_radius_m"), D)) G.TileRadiusCm = float(D) * 100.f;
		if (O->TryGetNumberField(TEXT("gain"), D)) G.Gain = float(D);
		O->TryGetBoolField(TEXT("shadow"), G.bShadow);
		Groups.Add(G);
	}
	CarGroup = -1;
	for (int32 g = 0; g < Groups.Num(); g++) if (Groups[g].Cats.Contains(13) || Groups[g].Cats.Contains(14)) { CarGroup = g; break; }
	return true;
}

// ------------------------------------------------------------------------------------------------ data
bool FWHCLData::Load(const FString& Path, FString& Err)
{
	TArray<uint8> B;
	if (!FFileHelper::LoadFileToArray(B, *Path)) { Err = FString::Printf(TEXT("missing %s"), *Path); return false; }
	if (B.Num() < 52 || FMemory::Memcmp(B.GetData(), "SM2L", 4) != 0) { Err = TEXT("bad magic in CityLights.bin"); return false; }
	const uint32 Version = *reinterpret_cast<const uint32*>(B.GetData() + 4), Count = *reinterpret_cast<const uint32*>(B.GetData() + 8);
	if (Version != 1) { Err = FString::Printf(TEXT("CityLights.bin version %u"), Version); return false; }
	const int64 NeedBytes = 52 + int64(Count) * (68 + 16);
	if (int64(B.Num()) != NeedBytes) { Err = FString::Printf(TEXT("CityLights.bin size %d != %lld"), B.Num(), NeedBytes); return false; }
	Commit = FString(40, ANSI_TO_TCHAR(reinterpret_cast<const char*>(B.GetData() + 12)));
	Recs.SetNumUninitialized(Count);
	FMemory::Memzero(CatCounts); bAnyDay = false;
	const uint8* A = B.GetData() + 52;
	const uint8* Bb = A + int64(Count) * 68;
	for (uint32 i = 0; i < Count; i++)
	{
		FWHCLRecord& R = Recs[i];
		FMemory::Memcpy(R.Pos, A + int64(i) * 68, 16 * 4);
		R.Cat = A[int64(i) * 68 + 64]; R.Type = A[int64(i) * 68 + 65]; R.Flags = A[int64(i) * 68 + 66]; R.Vol = A[int64(i) * 68 + 67];
		const float* Bf = reinterpret_cast<const float*>(Bb + int64(i) * 16);
		R.CosO = Bf[0]; R.CosI = Bf[1]; R.Radius = Bf[2]; R.Spec = Bf[3];
		R.AreaM2 = R.Type == 2 ? FMath::Max(R.W * R.H / 1.0e4f, 1.0e-4f) : 1.f;
		R.Parent = -1; R.bHasTiles = false; R.Group = -1;
		if (R.Cat < 16) CatCounts[R.Cat]++;
		bAnyDay |= R.bDay();
	}
	return true;
}

void FWHCLData::Index(const FWHCLConfig& Cfg)
{
	const int32 NG = Cfg.Groups.Num();
	GroupGrid.Reset(); GroupGrid.SetNum(NG);
	AmbGrid.Reset();
	TMap<int32, int32> GroupOfCat;
	for (int32 g = 0; g < NG; g++) for (int32 C : Cfg.Groups[g].Cats) GroupOfCat.Add(C, g);
	auto CellOf = [](const FWHCLRecord& R, int32& CX, int32& CY) { CX = FMath::FloorToInt(R.Pos[0] / 3200.f); CY = FMath::FloorToInt(R.Pos[1] / 3200.f); };
	TMap<int64, TArray<int32>> Wholes;
	for (int32 i = 0; i < Recs.Num(); i++)
	{
		FWHCLRecord& R = Recs[i];
		R.Parent = -1; R.bHasTiles = false;
		const int32* G = GroupOfCat.Find(R.Cat);
		R.Group = G ? *G : -1;
		int32 CX, CY; CellOf(R, CX, CY);
		const int64 Key = CellKey(CX, CY);
		if (R.Group >= 0) GroupGrid[R.Group].FindOrAdd(Key).Add(i);
		AmbGrid.FindOrAdd(Key).Add(i);
		if (R.Cat == 9) Wholes.FindOrAdd(Key).Add(i);
	}
	for (int32 i = 0; i < Recs.Num(); i++)
	{
		FWHCLRecord& T = Recs[i];
		if (T.Cat != 10) continue;
		int32 CX, CY; CellOf(T, CX, CY);
		float BestD = 1e30f; int32 Best = -1;
		for (int32 dx = -1; dx <= 1; dx++) for (int32 dy = -1; dy <= 1; dy++)
		{
			const TArray<int32>* L = Wholes.Find(CellKey(CX + dx, CY + dy)); if (!L) continue;
			for (int32 w : *L)
			{
				const FWHCLRecord& Wh = Recs[w];
				const FVector Dl = T.Location() - Wh.Location(), N(Wh.Dir[0], Wh.Dir[1], Wh.Dir[2]), U(Wh.U[0], Wh.U[1], Wh.U[2]), V = FVector::CrossProduct(N, U);
				if (FVector::DotProduct(N, FVector(T.Dir[0], T.Dir[1], T.Dir[2])) < 0.99f) continue;
				if (FMath::Abs(FVector::DotProduct(Dl, N)) > 5.f || FMath::Abs(FVector::DotProduct(Dl, U)) > Wh.W * 0.5f + 5.f || FMath::Abs(FVector::DotProduct(Dl, V)) > Wh.H * 0.5f + 5.f) continue;
				const float D = Dl.SizeSquared(); if (D < BestD) { BestD = D; Best = w; }
			}
		}
		T.Parent = Best;
		if (Best >= 0) Recs[Best].bHasTiles = true;
	}
}

// ------------------------------------------------------------------------------------------------ selection
bool FWHCLView::SphereIn(const FVector& C, float R) const
{
	if (!bFrustum) return false;
	const FVector D = C - Loc;
	const float CH = FMath::Cos(HalfH), SH = FMath::Sin(HalfH), CV = FMath::Cos(HalfV), SV = FMath::Sin(HalfV);
	const FVector Nl = Right * CH + Fwd * SH, Nr = -Right * CH + Fwd * SH, Nt = -Up * CV + Fwd * SV, Nb = Up * CV + Fwd * SV;
	return FVector::DotProduct(Nl, D) >= -R && FVector::DotProduct(Nr, D) >= -R && FVector::DotProduct(Nt, D) >= -R && FVector::DotProduct(Nb, D) >= -R;
}

void WHCLSelect(const FWHCLData& D, const FWHCLConfig& C, const FWHCLView& V, float BudgetScale, const TArray<TSet<int32>>* Assigned, FWHCLSelection& Out)
{
	const int32 NG = C.Groups.Num();
	Out.Chosen.Reset(); Out.Chosen.SetNum(NG); Out.Candidates.Reset(); Out.Candidates.SetNumZeroed(NG);
	struct FCand { float Score; int32 Idx; };
	TArray<FCand> Cand;
	for (int32 g = 0; g < NG; g++)
	{
		if (g >= D.GroupGrid.Num()) break;
		const FWHCLGroupCfg& G = C.Groups[g];
		Cand.Reset();
		const int32 X0 = FMath::FloorToInt((V.Loc.X - G.RadiusCm) / 3200.f), X1 = FMath::FloorToInt((V.Loc.X + G.RadiusCm) / 3200.f);
		const int32 Y0 = FMath::FloorToInt((V.Loc.Y - G.RadiusCm) / 3200.f), Y1 = FMath::FloorToInt((V.Loc.Y + G.RadiusCm) / 3200.f);
		for (int32 cx = X0; cx <= X1; cx++) for (int32 cy = Y0; cy <= Y1; cy++)
		{
			const TArray<int32>* L = D.GroupGrid[g].Find(FWHCLData::CellKey(cx, cy)); if (!L) continue;
			for (int32 i : *L)
			{
				const FWHCLRecord& R = D.Recs[i];
				const FVector P = R.Location();
				const float Dist = FVector::Dist(P, V.Loc);
				if (Dist > G.RadiusCm || Dist < G.MinRadiusCm) continue;
				if (G.TileRadiusCm > 0.f)
				{
					if (R.Cat == 9 && R.bHasTiles && Dist < G.TileRadiusCm) continue;                       // tiles replace their whole board
					if (R.Cat == 10 && R.Parent >= 0 && FVector::Dist(D.Recs[R.Parent].Location(), V.Loc) >= G.TileRadiusCm) continue;
				}
				Out.Candidates[g]++;
				const float dM = Dist * 0.01f;
				float Score = R.Intensity * R.AreaM2 / (dM * dM + 36.f);
				if (V.bFrustum && V.SphereIn(P, R.Range)) Score *= 1.5f;
				if (Assigned && Assigned->IsValidIndex(g) && (*Assigned)[g].Contains(i)) Score *= 1.25f;
				Cand.Add({ Score, i });
			}
		}
		const int32 Budget = G.Budget <= 0 ? Cand.Num() : FMath::Min(Cand.Num(), FMath::CeilToInt(G.Budget * FMath::Max(0.f, BudgetScale)));
		if (Budget < Cand.Num()) Cand.Sort([](const FCand& A, const FCand& B) { return A.Score > B.Score; });
		for (int32 k = 0; k < Budget; k++) Out.Chosen[g].Add(Cand[k].Idx);
	}
}

// ------------------------------------------------------------------------------------------------ actor
AWHCityLights::AWHCityLights()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PostUpdateWork;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

void AWHCityLights::ReloadConfig()
{
	FString Err;
	FWHCLConfig NewCfg;
	if (!NewCfg.Load(NightDir() / TEXT("CityLights.json"), Err)) { UE_LOG(LogWebHomage, Error, TEXT("WH_CITYLIGHTS reload failed: %s"), *Err); return; }
	DestroyPools();
	Cfg = NewCfg;
	if (Data.Recs.Num()) Data.Index(Cfg);
	BuildPools();
	LastRebuildPos = FVector(1e18); SinceRebuild = 1e9f;
	UE_LOG(LogWebHomage, Display, TEXT("WH_CITYLIGHTS reloaded config: K %.1f, %d groups"), Cfg.K, Cfg.Groups.Num());
}

FString AWHCityLights::CountsString() const
{
	static const TCHAR* Names[] = { TEXT("street_lamp"), TEXT("park_lamp"), TEXT("bridge_lamp"), TEXT("shop_front"), TEXT("neon"), TEXT("screen"), TEXT("skyline_flood"), TEXT("window_run"), TEXT("window_band"), TEXT("board_whole"), TEXT("board_tile"), TEXT("blade"), TEXT("signal") };
	FString S;
	for (int32 c = 0; c < 13; c++) S += FString::Printf(TEXT("%s%s=%d"), c ? TEXT(",") : TEXT(""), Names[c], Data.CatCounts[c]);
	return S;
}

void AWHCityLights::BeginPlay()
{
	Super::BeginPlay();
	bActive = false;
	FString Err;
	if (!Cfg.Load(NightDir() / TEXT("CityLights.json"), Err) || !Data.Load(NightDir() / TEXT("CityLights.bin"), Err))
	{
		LoadError = Err;
		UE_LOG(LogWebHomage, Error, TEXT("WH_CITYLIGHTS missing or invalid data: %s (actor disabled)"), *Err);
		SetActorTickEnabled(false);
		return;
	}
	Data.Index(Cfg);
	MPC = LoadObject<UMaterialParameterCollection>(nullptr, TEXT("/Game/City/Materials/MPC_City.MPC_City"));
	if (!MPC) UE_LOG(LogWebHomage, Warning, TEXT("WH_CITYLIGHTS MPC_City not found: NightK stays 0, lights stay off"));
	BuildPools();
	bActive = true;
	for (TActorIterator<AWHLifeTraffic> It(GetWorld()); It; ++It) It->RegisterNightLights(this);   // (traffic registers itself too when it starts later)
	UE_LOG(LogWebHomage, Display, TEXT("WH_CITYLIGHTS loaded %d records, cats=%s (commit %s, %d pooled lights)"), Data.Recs.Num(), *CountsString(), *Data.Commit.Left(8), Pools.Num());
}

void AWHCityLights::EndPlay(const EEndPlayReason::Type Reason)
{
	DynProviders.Reset();
	DestroyPools();
	Super::EndPlay(Reason);
}

void AWHCityLights::BuildPools()
{
	const int32 NG = Cfg.Groups.Num();
	Pools.Reset(); Pools.SetNum(NG * 3);
	RecToSlot.Reset(); RecToSlot.SetNum(NG);
	TArray<int32> TypeMask; TypeMask.SetNumZeroed(NG);
	TArray<int32> GroupCount; GroupCount.SetNumZeroed(NG);
	for (const FWHCLRecord& R : Data.Recs) if (R.Group >= 0) { TypeMask[R.Group] |= 1 << R.Type; GroupCount[R.Group]++; }
	if (Cfg.CarGroup >= 0)
	{
		const int32 N = FMath::CeilToInt(FMath::Max(1, Cfg.Groups[Cfg.CarGroup].Budget) * FMath::Max(1.f, Cfg.PoolHeadroom));
		for (int32 t = 0; t < 2; t++)
		{
			DynSlots[t].SetNum(N);
			for (FDynSlot& S : DynSlots[t])
			{
				ULocalLightComponent* L = t == 0 ? static_cast<ULocalLightComponent*>(NewObject<UPointLightComponent>(this, NAME_None, RF_Transient)) : static_cast<ULocalLightComponent*>(NewObject<USpotLightComponent>(this, NAME_None, RF_Transient));
				L->SetMobility(EComponentMobility::Movable); L->SetVisibility(false); L->SetCastShadows(false); L->SetIntensityUnits(ELightUnits::Candelas);
				L->SetupAttachment(GetRootComponent()); L->RegisterComponent();
				S.Comp = L;
			}
		}
	}
	for (int32 g = 0; g < NG; g++)
	{
		const int32 N = Cfg.Groups[g].Budget <= 0 ? GroupCount[g] : FMath::CeilToInt(Cfg.Groups[g].Budget * FMath::Max(1.f, Cfg.PoolHeadroom));
		for (int32 t = 0; t < 3; t++)
		{
			FPool& P = Pools[g * 3 + t]; P.Group = g; P.Type = t;
			if (!(TypeMask[g] & (1 << t))) continue;
			P.Slots.SetNum(N);
			for (FSlot& S : P.Slots)
			{
				ULocalLightComponent* L = t == 0 ? static_cast<ULocalLightComponent*>(NewObject<UPointLightComponent>(this, NAME_None, RF_Transient))
					: t == 1 ? static_cast<ULocalLightComponent*>(NewObject<USpotLightComponent>(this, NAME_None, RF_Transient))
					: static_cast<ULocalLightComponent*>(NewObject<URectLightComponent>(this, NAME_None, RF_Transient));
				L->SetMobility(EComponentMobility::Movable);
				L->SetVisibility(false);
				L->SetCastShadows(false);
				L->SetIntensityUnits(t == 2 ? ELightUnits::Nits : ELightUnits::Candelas);
				L->SetupAttachment(GetRootComponent());
				L->RegisterComponent();
				S.Comp = L;
			}
		}
	}
}

void AWHCityLights::DestroyPools()
{
	for (FPool& P : Pools) for (FSlot& S : P.Slots) if (S.Comp) { S.Comp->DestroyComponent(); S.Comp = nullptr; }
	for (int32 t = 0; t < 3; t++) { for (FDynSlot& S : DynSlots[t]) if (S.Comp) { S.Comp->DestroyComponent(); S.Comp = nullptr; } DynSlots[t].Reset(); }
	DynKeyToSlot.Reset(); DynPrev.Reset();
	Pools.Reset(); RecToSlot.Reset();
	ActiveLights = 0;
}

float AWHCityLights::ReadNightK() const
{
	if (!MPC || !GetWorld()) return 0.f;
	return FMath::Clamp(UKismetMaterialLibrary::GetScalarParameterValue(GetWorld(), MPC, TEXT("NightK")), 0.f, 1.f);
}

bool AWHCityLights::GetView(FWHCLView& V) const
{
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	if (!PC || !PC->PlayerCameraManager) return false;
	const FRotator Rot = PC->PlayerCameraManager->GetCameraRotation();
	V.Loc = PC->PlayerCameraManager->GetCameraLocation();
	const FRotationMatrix M(Rot);
	V.Fwd = M.GetUnitAxis(EAxis::X); V.Right = M.GetUnitAxis(EAxis::Y); V.Up = M.GetUnitAxis(EAxis::Z);
	float Aspect = 16.f / 9.f;
	if (GEngine && GEngine->GameViewport && GEngine->GameViewport->Viewport) { const FIntPoint S = GEngine->GameViewport->Viewport->GetSizeXY(); if (S.X > 0 && S.Y > 0) Aspect = float(S.X) / float(S.Y); }
	V.HalfH = FMath::DegreesToRadians(FMath::Clamp(PC->PlayerCameraManager->GetFOVAngle(), 10.f, 170.f) * 0.5f);
	V.HalfV = FMath::Atan(FMath::Tan(V.HalfH) / Aspect);
	V.bFrustum = true;
	return true;
}

void AWHCityLights::ConfigureLight(ULocalLightComponent* L, const FWHCLRecord& R)
{
	const FVector Loc = R.Location(), Dir(R.Dir[0], R.Dir[1], R.Dir[2]);
	FRotator Rot = Dir.Rotation();
	if (R.Type == 2) Rot = FRotationMatrix::MakeFromXY(Dir.GetSafeNormal(), FVector(R.U[0], R.U[1], R.U[2])).Rotator();
	L->SetWorldLocationAndRotation(Loc, Rot);
	L->SetLightColor(FLinearColor(R.Col[0], R.Col[1], R.Col[2]), true);
	L->SetAttenuationRadius(FMath::Max(R.Range, 10.f));
	L->SetVolumetricScatteringIntensity(float(R.Vol) / 255.f * Cfg.VolumetricGain);
	if (USpotLightComponent* Sp = Cast<USpotLightComponent>(L))
	{
		const float Outer = FMath::Clamp(FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(R.CosO, -1.f, 1.f))), 1.f, 80.f);
		const float Inner = FMath::Clamp(FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(R.CosI, -1.f, 1.f))), 0.f, Outer);
		Sp->SetOuterConeAngle(Outer); Sp->SetInnerConeAngle(Inner);
		Sp->SetSourceRadius(R.Radius);
	}
	else if (UPointLightComponent* Pt = Cast<UPointLightComponent>(L))
	{
		Pt->SetSourceRadius(R.Radius);
	}
	else if (URectLightComponent* Rc = Cast<URectLightComponent>(L))
	{
		Rc->SetSourceWidth(FMath::Max(R.W, 1.f)); Rc->SetSourceHeight(FMath::Max(R.H, 1.f));
	}
	L->SetCastShadows(false);
	if (R.Type == 1) { L->ContactShadowLength = 0.1f; }   // unshadowed lamp spots: screen-space contact shadows (10 %) keep leaves / props from lighting each other through
	L->SetIntensity(0.f);
	L->SetVisibility(true);
}

void AWHCityLights::AssignSlot(FPool& P, int32 SlotIdx, int32 RecIdx)
{
	FSlot& S = P.Slots[SlotIdx];
	ConfigureLight(S.Comp, Data.Recs[RecIdx]);
	S.Rec = RecIdx; S.Fade = 0.f; S.bTarget = true; S.AppliedIntensity = -1.f; S.bShadowOn = false;
}

int32 AWHCityLights::RegisterDynamicProvider(FWHCLDynProvider Fn)
{
	DynProviders.Add(TPair<int32, FWHCLDynProvider>(NextProviderId, MoveTemp(Fn)));
	return NextProviderId++;
}

void AWHCityLights::UnregisterDynamicProvider(int32 Handle)
{
	DynProviders.RemoveAll([Handle](const TPair<int32, FWHCLDynProvider>& P) { return P.Key == Handle; });
}

// dynamic lights (cars): candidates from every provider, scored like the static ones (intensity / (d^2 + 36), view bonus, 1.25x hysteresis), top `budget` of the "cars" group
void AWHCityLights::RebuildDynamic(const FWHCLView& V)
{
	if (Cfg.CarGroup < 0) return;
	const FWHCLGroupCfg& G = Cfg.Groups[Cfg.CarGroup];
	TArray<FWHCLRecord> Cand;
	for (const TPair<int32, FWHCLDynProvider>& P : DynProviders) P.Value(V.Loc, Cand);
	const double Now = FPlatformTime::Seconds();
	TMap<int32, TPair<FVector, double>> NewPrev;
	struct FC { float Score; int32 I; };
	TArray<FC> Scored;
	for (int32 i = 0; i < Cand.Num(); i++)
	{
		FWHCLRecord& R = Cand[i];
		NewPrev.Add(R.Key, TPair<FVector, double>(R.Location(), Now));
		const float Dist = FVector::Dist(R.Location(), V.Loc);
		if (Dist > G.RadiusCm || Dist < G.MinRadiusCm) continue;
		const float dM = Dist * 0.01f;
		float Score = R.Intensity * R.AreaM2 / (dM * dM + 36.f);
		if (V.bFrustum && V.SphereIn(R.Location(), R.Range)) Score *= 1.5f;
		if (DynKeyToSlot.Contains(R.Key)) Score *= 1.25f;
		Scored.Add({ Score, i });
	}
	Scored.Sort([](const FC& A, const FC& B) { return A.Score > B.Score; });
	const int32 Budget = FMath::Min(Scored.Num(), FMath::CeilToInt(G.Budget * FMath::Max(0.f, CVarBudgetScale.GetValueOnGameThread())));
	TSet<int32> Want;
	for (int32 k = 0; k < Budget; k++) Want.Add(Cand[Scored[k].I].Key);
	for (auto It = DynKeyToSlot.CreateIterator(); It; ++It)
	{
		if (Want.Contains(It.Key())) continue;
		DynSlots[It.Value() >> 16][It.Value() & 0xffff].bTarget = false;   // fades out, then frees the slot
		It.RemoveCurrent();
	}
	for (int32 k = 0; k < Budget; k++)
	{
		FWHCLRecord& R = Cand[Scored[k].I];
		FVector Vel = FVector::ZeroVector;
		if (const TPair<FVector, double>* Pr = DynPrev.Find(R.Key)) { const double Dt = Now - Pr->Value; if (Dt > 0.02 && Dt < 1.0) Vel = (R.Location() - Pr->Key) / float(Dt); }
		if (const int32* Ex = DynKeyToSlot.Find(R.Key))
		{
			FDynSlot& S = DynSlots[*Ex >> 16][*Ex & 0xffff];
			S.Rec = R; S.Vel = Vel;
			S.Comp->SetWorldLocation(R.Location());
			continue;
		}
		const int32 T = R.Type == 1 ? 1 : 0;
		int32 Free = INDEX_NONE;
		for (int32 s = 0; s < DynSlots[T].Num(); s++) if (DynSlots[T][s].Key < 0) { Free = s; break; }
		if (Free == INDEX_NONE) continue;
		FDynSlot& S = DynSlots[T][Free];
		ConfigureLight(S.Comp, R);
		S.Key = R.Key; S.Rec = R; S.Vel = Vel; S.Fade = 0.f; S.bTarget = true; S.Applied = -1.f;
		DynKeyToSlot.Add(R.Key, (T << 16) | Free);
	}
	DynPrev = MoveTemp(NewPrev);
}

void AWHCityLights::ApplyIntensity(FSlot& S, float Gain)
{
	const FWHCLRecord& R = Data.Recs[S.Rec];
	const float I = R.Intensity * Cfg.K * Gain * Cfg.Groups[R.Group].Gain * S.Fade * (R.bDay() ? 1.f : NightK);
	if (FMath::Abs(I - S.AppliedIntensity) > FMath::Max(0.002f * I, 1e-3f)) { S.Comp->SetIntensity(I); S.AppliedIntensity = I; }
}

void AWHCityLights::Rebuild(const FWHCLView& V)
{
	const int32 NG = Cfg.Groups.Num();
	TArray<TSet<int32>> Assigned; Assigned.SetNum(NG);
	for (int32 g = 0; g < NG; g++) for (const TPair<int32, int32>& KV : RecToSlot[g]) Assigned[g].Add(KV.Key);
	FWHCLSelection Sel;
	WHCLSelect(Data, Cfg, V, CVarBudgetScale.GetValueOnGameThread(), &Assigned, Sel);
	for (int32 g = 0; g < NG; g++)
	{
		TSet<int32> Want(Sel.Chosen[g]);
		for (auto It = RecToSlot[g].CreateIterator(); It; ++It)
		{
			if (Want.Contains(It.Key())) continue;
			const FWHCLRecord& R = Data.Recs[It.Key()];
			Pools[g * 3 + R.Type].Slots[It.Value()].bTarget = false;   // fades out, then frees the slot
			It.RemoveCurrent();
		}
		for (int32 Idx : Sel.Chosen[g])
		{
			if (RecToSlot[g].Contains(Idx)) continue;
			FPool& P = Pools[g * 3 + Data.Recs[Idx].Type];
			int32 Free = INDEX_NONE;
			for (int32 s = 0; s < P.Slots.Num(); s++) if (P.Slots[s].Rec < 0) { Free = s; break; }
			if (Free == INDEX_NONE) continue;
			AssignSlot(P, Free, Idx);
			RecToSlot[g].Add(Idx, Free);
		}
	}
}

void AWHCityLights::UpdateShadows(const FVector& HeroLoc)
{
	struct FC { float D; FPool* P; int32 S; };
	TArray<FC> C;
	for (int32 g = 0; g < Cfg.Groups.Num(); g++)
	{
		if (!Cfg.Groups[g].bShadow) continue;
		for (int32 t = 0; t < 3; t++)
		{
			FPool& P = Pools[g * 3 + t];
			if (t != 1) continue;   // spots only
			for (int32 s = 0; s < P.Slots.Num(); s++)
			{
				FSlot& S = P.Slots[s];
				if (S.Rec < 0 || !S.bTarget || Data.Recs[S.Rec].Cat != 0) continue;
				float D = FVector::Dist(Data.Recs[S.Rec].Location(), HeroLoc);
				if (D > Cfg.ShadowRadiusCm) continue;
				if (S.bShadowOn) D *= 0.8f;   // hysteresis: current shadow casters are favoured
				C.Add({ D, &P, s });
			}
		}
	}
	C.Sort([](const FC& A, const FC& B) { return A.D < B.D; });
	TSet<FSlot*> On;
	for (int32 i = 0; i < FMath::Min(C.Num(), Cfg.ShadowSlots); i++) On.Add(&C[i].P->Slots[C[i].S]);
	for (FPool& P : Pools) for (FSlot& S : P.Slots)
	{
		const bool Want = On.Contains(&S);
		if (S.Rec >= 0 && Want != S.bShadowOn) { S.Comp->SetCastShadows(Want); S.bShadowOn = Want; }
		else if (S.Rec < 0) S.bShadowOn = false;
	}
}

// port of citylights.js ambAdd / updateAmbient (AMB_R 70 m, AMB_SOFT 6 m, AMB_GAIN 0.16): lights bounce off the lit streets / facades around the
// player; split into a lower hemisphere (street bounce) and an upper one. Units: metres, irradiance-like browser units.
void AWHCityLights::UpdateAmbient(const FWHCLView& V, float Dt)
{
	AmbAcc += Dt;
	if (AmbAcc >= Cfg.RebuildIntervalS || Dt <= 0.f)
	{
		AmbAcc = 0.f;
		AmbTargetLo = AmbTargetHi = FVector::ZeroVector;
		if (NightK >= 0.01f)
		{
			APawn* Pawn = UGameplayStatics::GetPlayerPawn(this, 0);
			const FVector P = (Pawn ? Pawn->GetActorLocation() : V.Loc) + FVector(0, 0, 100.f);
			const float RcmAmb = Cfg.AmbR * 100.f;
			const int32 X0 = FMath::FloorToInt((P.X - RcmAmb) / 3200.f), X1 = FMath::FloorToInt((P.X + RcmAmb) / 3200.f), Y0 = FMath::FloorToInt((P.Y - RcmAmb) / 3200.f), Y1 = FMath::FloorToInt((P.Y + RcmAmb) / 3200.f);
			const float TileR = 6000.f, NearRun = 3800.f;
			for (int32 cx = X0; cx <= X1; cx++) for (int32 cy = Y0; cy <= Y1; cy++)
			{
				const TArray<int32>* L = Data.AmbGrid.Find(FWHCLData::CellKey(cx, cy)); if (!L) continue;
				for (int32 i : *L)
				{
					const FWHCLRecord& R = Data.Recs[i];
					const FVector D = (R.Location() - P) * 0.01f;       // metres
					const float D2 = D.SizeSquared();
					const float RcmReach = R.Type == 2 ? R.Range + 0.5f * FMath::Sqrt(R.W * R.W + R.H * R.H) : R.Range;
					const float Rw = FMath::Min(Cfg.AmbR, FMath::Max(25.f, RcmReach * 0.01f * 2.5f));
					if (D2 > Rw * Rw) continue;
					const float Dist = FVector::Dist(R.Location(), P);
					// the author's providers: runs only near, bands farther; board tiles near, whole boards far
					if (R.Cat == 7 && Dist >= NearRun) continue;
					if (R.Cat == 8 && Dist < NearRun) continue;
					if (R.Cat == 9 && R.bHasTiles && Dist < TileR) continue;
					if (R.Cat == 10 && R.Parent >= 0 && FVector::Dist(Data.Recs[R.Parent].Location(), P) >= TileR) continue;
					const float d = FMath::Sqrt(D2);
					const float T = FMath::Clamp((d - 0.55f * Rw) / (Rw - 0.55f * Rw), 0.f, 1.f);
					const float Win = 1.f - T * T * (3.f - 2.f * T);
					const float F = (R.bDay() ? 1.f : NightK) * Cfg.AmbGain * Win * (R.Type == 2 ? R.AreaM2 : 1.f) / (D2 + Cfg.AmbSoft * Cfg.AmbSoft);
					const float Up = FMath::Clamp(D.Z / (d + 1.f), -1.f, 1.f);
					const float Lo = 0.62f + 0.18f * FMath::Max(0.f, Up);
					const FVector Cc(R.Col[0] * R.Intensity, R.Col[1] * R.Intensity, R.Col[2] * R.Intensity);
					AmbTargetLo += Cc * (F * Lo); AmbTargetHi += Cc * (F * (1.f - Lo));
				}
			}
			for (int32 t = 0; t < 2; t++) for (const FDynSlot& S : DynSlots[t])
			{
				if (S.Key < 0 || !S.bTarget) continue;
				const FWHCLRecord& R = S.Rec;
				const FVector D = (R.Location() - P) * 0.01f;
				const float D2 = D.SizeSquared(), Rw = Cfg.AmbR;
				if (D2 > Rw * Rw) continue;
				const float d = FMath::Sqrt(D2), T2 = FMath::Clamp((d - 0.55f * Rw) / (0.45f * Rw), 0.f, 1.f), Win = 1.f - T2 * T2 * (3.f - 2.f * T2);
				const float F = NightK * Cfg.AmbGain * Win / (D2 + Cfg.AmbSoft * Cfg.AmbSoft);
				const float Lo = 0.62f + 0.18f * FMath::Max(0.f, FMath::Clamp(D.Z / (d + 1.f), -1.f, 1.f));
				const FVector Cc(R.Col[0] * R.Intensity, R.Col[1] * R.Intensity, R.Col[2] * R.Intensity);
				AmbTargetLo += Cc * (F * Lo); AmbTargetHi += Cc * (F * (1.f - Lo));
			}
			const float G = CVarGain.GetValueOnGameThread();
			AmbTargetLo *= G; AmbTargetHi *= G;
		}
	}
	const float A = 1.f - FMath::Exp(-Dt / 0.5f);
	AmbLo = FMath::Lerp(AmbLo, AmbTargetLo, A); AmbHi = FMath::Lerp(AmbHi, AmbTargetHi, A);
	AmbientLower = FLinearColor(AmbLo.X, AmbLo.Y, AmbLo.Z); AmbientUpper = FLinearColor(AmbHi.X, AmbHi.Y, AmbHi.Z);
}

void AWHCityLights::DriveHero()
{
	if (!HeroLight.IsValid())
	{
		TActorIterator<AWHLookHeroLight> It(GetWorld());
		if (It) HeroLight = *It;
		if (!HeroLight.IsValid()) return;
	}
	AWHLookHeroLight* H = HeroLight.Get();
	static const FVector Lum(0.2126, 0.7152, 0.0722);
	const float FillD = H->FillDistance * 0.01f, TopD = 3.2f;
	const float DriveLo = Cfg.K * FVector::DotProduct(AmbLo, Lum) * FillD * FillD * Cfg.HeroIrradianceScale;
	const float DriveHi = Cfg.K * FVector::DotProduct(AmbHi, Lum) * TopD * TopD * Cfg.HeroIrradianceScale;
	const float BaseFill = H->GetBaseFillIntensity() * Cfg.HeroFillBase;
	FLinearColor Col = H->GetBaseFillColor();
	const float Mx = FMath::Max3(AmbLo.X, AmbLo.Y, AmbLo.Z);
	if (Mx > 1e-6f)
	{
		const FLinearColor N(AmbLo.X / Mx, AmbLo.Y / Mx, AmbLo.Z / Mx);
		Col = FMath::Lerp(Col, N, FMath::Clamp(DriveLo / (DriveLo + BaseFill + 1.f), 0.f, 1.f));
	}
	H->SetAmbientDrive(Col, BaseFill + DriveLo, DriveHi);
}

void AWHCityLights::DebugReport() const
{
	TArray<int32> PerCat; PerCat.SetNumZeroed(13);
	for (const FPool& P : Pools) for (const FSlot& S : P.Slots) if (S.Rec >= 0 && S.Fade > 0.f) PerCat[Data.Recs[S.Rec].Cat]++;
	FString S = FString::Printf(TEXT("WH_CITYLIGHTS night %.2f active %d ambLo (%.3f %.3f %.3f) ambHi (%.3f %.3f %.3f) cats:"), NightK, ActiveLights, AmbLo.X, AmbLo.Y, AmbLo.Z, AmbHi.X, AmbHi.Y, AmbHi.Z);
	for (int32 c = 0; c < 13; c++) S += FString::Printf(TEXT(" %d"), PerCat[c]);
	UE_LOG(LogWebHomage, Display, TEXT("%s"), *S);
	if (GEngine && CVarDebug.GetValueOnGameThread() >= 2) GEngine->AddOnScreenDebugMessage(0x5C17, 1.5f, FColor::Yellow, S);   // 1: log only, 2: also on screen
}

void AWHCityLights::Tick(float Dt)
{
	Super::Tick(Dt);
	if (!bActive) return;
	const bool bOn = CVarEnable.GetValueOnGameThread() != 0;
	NightK = bOn ? ReadNightK() : 0.f;
	if (MpcLogClock >= 0.f)
	{
		MpcLogClock += Dt;
		if (MpcLogClock > 3.f && MPC)
		{
			MpcLogClock = -1.f;
			auto G = [this](const TCHAR* N) { return UKismetMaterialLibrary::GetScalarParameterValue(GetWorld(), MPC, N); };
			UE_LOG(LogWebHomage, Display, TEXT("WH_MPC NightK=%.3f InteriorGain=%.3f ShopGain=%.3f EmissiveScale=%.1f DnTime=%.0f DayEmisK=%.2f (facade material inputs; P.z = NightK)"), G(TEXT("NightK")), G(TEXT("InteriorGain")), G(TEXT("ShopGain")), G(TEXT("EmissiveScale")), G(TEXT("DnTime")), G(TEXT("DayEmisK")));
		}
	}
	const float Gain = CVarGain.GetValueOnGameThread();
	FWHCLView V;
	const bool bView = GetView(V);
	const bool bOff = NightK < Cfg.NightOffBelow && !Data.bAnyDay;
	SinceRebuild += Dt;
	if (bOff)
	{
		for (int32 g = 0; g < RecToSlot.Num(); g++)
		{
			for (const TPair<int32, int32>& KV : RecToSlot[g]) Pools[g * 3 + Data.Recs[KV.Key].Type].Slots[KV.Value].bTarget = false;
			RecToSlot[g].Reset();
		}
		for (int32 t = 0; t < 2; t++) for (FDynSlot& S : DynSlots[t]) if (S.Key >= 0) S.bTarget = false;
		DynKeyToSlot.Reset();
	}
	else if (bView && (SinceRebuild >= Cfg.RebuildIntervalS || FVector::Dist(V.Loc, LastRebuildPos) > Cfg.RebuildMoveCm))
	{
		Rebuild(V);
		RebuildDynamic(V);
		SinceRebuild = 0.f; LastRebuildPos = V.Loc;
		APawn* Pawn = UGameplayStatics::GetPlayerPawn(this, 0);
		UpdateShadows(Pawn ? Pawn->GetActorLocation() : V.Loc);
	}
	int32 Active = 0;
	const bool bIntensityDirty = FMath::Abs(NightK - LastNightK) > 1e-4f || FMath::Abs(Gain - LastGain) > 1e-4f;
	for (FPool& P : Pools) for (FSlot& S : P.Slots)
	{
		if (S.Rec < 0) continue;
		const float Step = Dt / FMath::Max(Cfg.FadeS, 1e-3f);
		const float Before = S.Fade;
		S.Fade = FMath::Clamp(S.Fade + (S.bTarget ? Step : -Step), 0.f, 1.f);
		if (S.Fade <= 0.f && !S.bTarget) { S.Comp->SetIntensity(0.f); S.Comp->SetVisibility(false); S.Rec = -1; S.AppliedIntensity = -1.f; S.bShadowOn = false; continue; }
		if (S.Fade != Before || bIntensityDirty) ApplyIntensity(S, Gain);
		Active++;
	}
	for (int32 t = 0; t < 2; t++) for (FDynSlot& S : DynSlots[t])
	{
		if (S.Key < 0) continue;
		const float Step = Dt / FMath::Max(Cfg.FadeS, 1e-3f);
		const float Before = S.Fade;
		S.Fade = FMath::Clamp(S.Fade + (S.bTarget ? Step : -Step), 0.f, 1.f);
		if (S.Fade <= 0.f && !S.bTarget) { S.Comp->SetIntensity(0.f); S.Comp->SetVisibility(false); S.Key = -1; S.Applied = -1.f; continue; }
		if (!S.Vel.IsNearlyZero()) { S.Rec.Pos[0] += S.Vel.X * Dt; S.Rec.Pos[1] += S.Vel.Y * Dt; S.Rec.Pos[2] += S.Vel.Z * Dt; S.Comp->SetWorldLocation(S.Rec.Location()); }
		if (S.Fade != Before || bIntensityDirty)
		{
			const float I = S.Rec.Intensity * Cfg.K * Gain * Cfg.Groups[Cfg.CarGroup].Gain * S.Fade * NightK;
			if (FMath::Abs(I - S.Applied) > FMath::Max(0.002f * I, 1e-3f)) { S.Comp->SetIntensity(I); S.Applied = I; }
		}
		Active++;
	}
	LastNightK = NightK; LastGain = Gain; ActiveLights = Active;
	if (bView) UpdateAmbient(V, Dt);
	DriveHero();
	if (CVarDebug.GetValueOnGameThread() > 0) { DebugT += Dt; if (DebugT >= 1.f) { DebugT = 0.f; DebugReport(); } }
}

// ------------------------------------------------------------------------------------------------ self test
FString UWHCityLightsLibrary::SelfTest(FVector CamPos)
{
	static FWHCLConfig Cfg; static FWHCLData Data; static bool bLoaded = false; static FString Err;
	if (!bLoaded)
	{
		bLoaded = Cfg.Load(NightDir() / TEXT("CityLights.json"), Err) && Data.Load(NightDir() / TEXT("CityLights.bin"), Err);
		if (bLoaded) Data.Index(Cfg);
	}
	TSharedRef<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetBoolField(TEXT("ok"), bLoaded);
	if (!bLoaded) Out->SetStringField(TEXT("error"), Err);
	else
	{
		FWHCLView V; V.Loc = CamPos;
		FWHCLSelection Sel;
		WHCLSelect(Data, Cfg, V, 1.f, nullptr, Sel);
		Out->SetNumberField(TEXT("records"), Data.Recs.Num());
		Out->SetStringField(TEXT("commit"), Data.Commit);
		TSharedRef<FJsonObject> Groups = MakeShared<FJsonObject>();
		double Total = 0.0; int32 TotalSel = 0;
		for (int32 g = 0; g < Cfg.Groups.Num(); g++)
		{
			TSharedRef<FJsonObject> G = MakeShared<FJsonObject>();
			double Inten = 0.0; TMap<int32, int32> ByCat;
			for (int32 i : Sel.Chosen[g]) { const FWHCLRecord& R = Data.Recs[i]; Inten += double(R.Intensity) * Cfg.K * Cfg.Groups[g].Gain; ByCat.FindOrAdd(R.Cat)++; }
			G->SetNumberField(TEXT("candidates"), Sel.Candidates[g]);
			G->SetNumberField(TEXT("selected"), Sel.Chosen[g].Num());
			G->SetNumberField(TEXT("intensity_k"), Inten);
			TSharedRef<FJsonObject> BC = MakeShared<FJsonObject>();
			for (const TPair<int32, int32>& KV : ByCat) BC->SetNumberField(FString::FromInt(KV.Key), KV.Value);
			G->SetObjectField(TEXT("by_cat"), BC);
			Groups->SetObjectField(Cfg.Groups[g].Name, G);
			Total += Inten; TotalSel += Sel.Chosen[g].Num();
		}
		Out->SetObjectField(TEXT("groups"), Groups);
		Out->SetNumberField(TEXT("selected_total"), TotalSel);
		Out->SetNumberField(TEXT("total_intensity_k"), Total);
	}
	FString S;
	FJsonSerializer::Serialize(Out, TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&S));
	return S;
}
