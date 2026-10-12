// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
#include "Life/WHLifeTraffic.h"
#include "Look/WHCityLights.h"
#include "EngineUtils.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "HAL/PlatformTime.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Camera/PlayerCameraManager.h"
#include "Kismet/GameplayStatics.h"

DEFINE_LOG_CATEGORY_STATIC(LogWHLife, Log, All);

using namespace WHLife;

namespace
{
	struct FTypeDef { const TCHAR* Name; float Len, Wid; bool bBig; };
	// src/world/npc/traffic.js VTYPES (real-world sizes of the Blender models)
	const FTypeDef GTypes[NumTypes] = {
		{TEXT("taxi"), 5.39f, 1.99f, false}, {TEXT("taxi_hy"), 4.54f, 1.76f, false}, {TEXT("taxi_mv"), 5.08f, 1.99f, false}, {TEXT("taxi_gr"), 4.86f, 1.84f, false},
		{TEXT("sedan"), 4.85f, 1.84f, false}, {TEXT("hatch"), 4.26f, 1.79f, false}, {TEXT("sedan2"), 4.9f, 1.85f, false}, {TEXT("cross"), 4.6f, 1.86f, false},
		{TEXT("suv"), 4.9f, 1.95f, false}, {TEXT("suv2"), 5.35f, 2.03f, false}, {TEXT("pickup"), 5.9f, 2.03f, false}, {TEXT("van"), 5.98f, 2.06f, false},
		{TEXT("truck"), 7.3f, 2.3f, true}, {TEXT("bus"), 12.2f, 2.55f, true}, {TEXT("tour"), 11.f, 2.55f, true} };
	enum ET : int32 { T_taxi, T_taxi_hy, T_taxi_mv, T_taxi_gr, T_sedan, T_hatch, T_sedan2, T_cross, T_suv, T_suv2, T_pickup, T_van, T_truck, T_bus, T_tour };

	// npc/traffic.js CAR_COLORS (sRGB hex; the browser converts with pow 2.2)
	const uint32 GCarColors[] = { 0x0e0e0f, 0x151517, 0x1b1c1f, 0x101418, 0xe2e2df, 0xd8d8d4, 0xcfcfca, 0xe6e3da, 0xa9adb1, 0x9c9fa3, 0xb7b9bb, 0x8e9296, 0x6d7074, 0x55585c, 0x44474b,
		0x1b2a4a, 0x223a63, 0x2f4c7a, 0x5a1216, 0x6e1a1a, 0x8a1f1f, 0xb3a98f, 0x9b8f75, 0x2c3d2e, 0x44563f, 0x6b86a0, 0x4a3a2c, 0x3b4450, 0x7c8a8f, 0x2a2d33 };
	const uint32 GLivery[] = { 0x0b0b0c, 0x0e0e10, 0x121315, 0x0d1014 };
	const uint32 GVan[] = { 0xd6d6d2, 0xcfccc4, 0xc9c9c7, 0xd9d7d0 };
	inline FLinearColor Lin(uint32 C) { return FLinearColor(FMath::Pow(((C >> 16) & 255) / 255.f, 2.2f), FMath::Pow(((C >> 8) & 255) / 255.f, 2.2f), FMath::Pow((C & 255) / 255.f, 2.2f)); }

	inline uint32 Xs(uint32& S) { S ^= S << 13; S ^= S >> 17; S ^= S << 5; return S; }
	inline float Ff(uint32& S) { return (Xs(S) & 0xFFFFFF) / 16777216.f; }

	const float DensityByKind[4] = { 31.f, 44.f, 20.f, 41.f }; // cars per km of lane: av, st, ws, dg (traffic.js DENSITY)
	constexpr float StopBack = 5.f;                            // roads.js STOP_BACK
	constexpr float CompDecel = 3.2f;

	float Idm(float V, float V0, float Gap, float VLead, float A, float B, float S0, float T)
	{
		const float Dv = V - VLead;
		const float SStar = S0 + FMath::Max(0.f, V * T + V * Dv / (2.f * FMath::Sqrt(A * B)));
		const float Free = 1.f - FMath::Pow(FMath::Max(V, 0.f) / FMath::Max(V0, 0.1f), 4.f);
		const float Inter = FMath::Square(SStar / FMath::Max(Gap, 0.15f));
		return FMath::Clamp(A * (Free - Inter), -9.f, A);
	}
}

float AWHLifeTraffic::KindDensity(int32 Kind) const
{
	const int32 K = FMath::Clamp(Kind, 0, 3);
	return DensityByKind[K] * DensityScale * (K == 1 ? StreetDensityFactor : 1.f);
}

AWHLifeTraffic::AWHLifeTraffic()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PrePhysics;
	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
}

void AWHLifeTraffic::EndPlay(const EEndPlayReason::Type Reason)
{
	if (NightLights.IsValid() && NightProviderId >= 0) NightLights->UnregisterDynamicProvider(NightProviderId);
	NightProviderId = -1; NightLights.Reset();
	Super::EndPlay(Reason);
	bReady = false;
}

void AWHLifeTraffic::RegisterNightLights(AWHCityLights* Lights)
{
	if (!Lights || NightLights.Get() == Lights) return;
	NightLights = Lights;
	TWeakObjectPtr<AWHLifeTraffic> Self(this);
	TWeakObjectPtr<AWHCityLights> WeakLights(Lights);
	NightProviderId = Lights->RegisterDynamicProvider([Self, WeakLights](const FVector& Cam, TArray<FWHCLRecord>& Out)
	{
		AWHLifeTraffic* T = Self.Get(); AWHCityLights* L = WeakLights.Get();
		if (T && L) T->EmitNightLights(Cam, L->GetConfig(), Out);
	});
}

// the author's traffic.js provider (lines 161-199): moving cars near the camera get a headlight pair (a merged lamp for the farther ones) and a tail-light pair (nearer ones); the numbers come from
// night_city.json cars_provider. Browser frame in, UE cm out: this actor's car positions are browser metres (x east, z south) = UE (X, Y) / 100.
void AWHLifeTraffic::EmitNightLights(const FVector& Cam, const FWHCLConfig& C, TArray<FWHCLRecord>& Out) const
{
	if (!bReady) return;
	const FWHCLCarsCfg& K = C.CarsCfg;
	const float RadiusCm = C.CarGroup >= 0 ? C.Groups[C.CarGroup].RadiusCm : 9000.f;
	struct FNear { float D2; int32 I; FVector2D Ctr, Dir; };
	TArray<FNear> Near;
	for (int32 I = 0; I < Cars.Num(); ++I)
	{
		const WHLife::FCar& Car = Cars[I];
		if (!Car.bActive || Car.Inst < 0) continue;
		const FVector2D PF = PathPoint(Car, 0.9f), PR = PathPoint(Car, Car.Len - 0.9f);
		FVector2D Ctr = (PF + PR) * 0.5f, Dir = PF - PR;
		if (Dir.SizeSquared() < 1e-6f) Dir = FVector2D(1, 0);
		Dir.Normalize();
		if (Car.Where == 0) Ctr += FVector2D(-Dir.Y, Dir.X) * Car.Lat;
		const float D2 = FVector2D::DistSquared(Ctr * 100.f, FVector2D(Cam.X, Cam.Y));
		if (D2 > RadiusCm * RadiusCm) continue;
		Near.Add({ D2, I, Ctr, Dir });
	}
	Near.Sort([](const FNear& A, const FNear& B) { return A.D2 < B.D2; });
	auto Lin = [](uint32 Hex) { return FLinearColor::FromSRGBColor(FColor((Hex >> 16) & 255, (Hex >> 8) & 255, Hex & 255)); };
	const FLinearColor HC = Lin(K.HeadHex), TC = Lin(K.TailHex);
	auto Make = [](const FVector& Pos, const FVector& Dir, const FLinearColor& Col, float Intensity, uint8 Cat, uint8 Type, float RangeM, float Angle, float Pen, float RadiusM, float Vol, float Spec, bool bNoShadow, int32 Key)
	{
		FWHCLRecord R;
		FMemory::Memzero(R);
		const float Mx = FMath::Max3(Col.R, Col.G, Col.B);
		R.Pos[0] = Pos.X; R.Pos[1] = Pos.Y; R.Pos[2] = Pos.Z; R.Dir[0] = Dir.X; R.Dir[1] = Dir.Y; R.Dir[2] = Dir.Z; R.U[0] = 1.f;
		R.Col[0] = Col.R / Mx; R.Col[1] = Col.G / Mx; R.Col[2] = Col.B / Mx; R.Intensity = Intensity * Mx;
		R.Range = RangeM * 100.f; R.Cat = Cat; R.Type = Type; R.Flags = bNoShadow ? 2 : 0; R.Vol = uint8(FMath::Clamp(Vol, 0.f, 1.f) * 255.f + 0.5f);
		R.CosO = FMath::Cos(Angle); R.CosI = FMath::Cos(Angle * (1.f - Pen)); R.Radius = RadiusM * 100.f; R.Spec = Spec; R.AreaM2 = 1.f; R.Key = Key; R.Group = -1;
		return R;
	};
	const float Cq = FMath::Cos(-K.HeadTilt), Sq = FMath::Sin(-K.HeadTilt);
	for (int32 n = 0; n < Near.Num(); ++n)
	{
		const WHLife::FCar& Car = Cars[Near[n].I];
		const FVector2D Ctr = Near[n].Ctr, Dir = Near[n].Dir, Right(-Dir.Y, Dir.X);
		const bool bTwin = n < K.TwinCars;
		const bool bTs = Ctr.X > K.TsX0 && Ctr.X < K.TsX1 && Ctr.Y > K.TsZ0 && Ctr.Y < K.TsZ1;
		const float I = bTs ? K.HeadITimesSquare : K.HeadI;
		const float Fwd = Car.Len * 0.5f + K.HeadFrontExtraM, W = bTwin ? FMath::Max(K.MinLateralM, Car.Wid * 0.5f - K.HeadInsetM) : 0.f;
		const FVector HDir(Dir.X * Cq, Dir.Y * Cq, Sq);
		for (int32 k = bTwin ? -1 : 0; k <= (bTwin ? 1 : 0); k += bTwin ? 2 : 1)
		{
			const FVector2D P = Ctr + Dir * Fwd + Right * (W * k);
			Out.Add(Make(FVector(P.X * 100.f, P.Y * 100.f, 1.f + K.HeadHeightM * 100.f), HDir, HC, bTwin ? I : I * K.HeadMerged, 13, 1, K.HeadRangeM, K.HeadAngle, K.HeadPenumbra, K.HeadRadiusM, K.HeadVolume, K.HeadSpec, false, Near[n].I * 4 + (k > 0 ? 1 : 0)));
		}
		if (Near[n].D2 < K.TailMaxDistM * K.TailMaxDistM * 1e4f)
		{
			const float Tw = FMath::Max(K.MinLateralM, Car.Wid * 0.5f - K.TailInsetM), Back = Car.Len * 0.5f + K.TailBackExtraM;
			for (int32 k = -1; k <= 1; k += 2)
			{
				const FVector2D P = Ctr - Dir * Back + Right * (Tw * k);
				Out.Add(Make(FVector(P.X * 100.f, P.Y * 100.f, 1.f + K.TailHeightM * 100.f), FVector(-Dir.X, -Dir.Y, 0.f), TC, Car.Brake ? K.TailIBraking : K.TailI, 14, 0, K.TailRangeM, 1.f, 0.f, K.TailRadiusM, K.TailVolume, 1.f, true, Near[n].I * 4 + 2 + (k > 0 ? 1 : 0)));
			}
		}
	}
}

float AWHLifeTraffic::Frand(uint32& R) { return Ff(R); }

int32 AWHLifeTraffic::SigPhase(double T, int32 Axis)
{
	// props.js phase(): 40 s cycle. Axis 0 (avenue): green 0-22, amber 22-25, red 25-40. Axis 1 (street): red 0-26, green 26-37, amber 37-39, red 39-40. 2 green, 1 amber, 0 red.
	double C = FMath::Fmod(T, 40.0); if (C < 0.0) C += 40.0;
	if (Axis == 0) return C < 22.0 ? 2 : (C < 25.0 ? 1 : 0);
	return C < 26.0 ? 0 : (C < 37.0 ? 2 : (C < 39.0 ? 1 : 0));
}

FVector2D AWHLifeTraffic::ConnPos(const FConn& K, float S) const
{
	if (K.Poly.Num() < 2) return FVector2D::ZeroVector;
	S = FMath::Clamp(S, 0.f, K.Len);
	int32 I = 1; while (I < K.Cum.Num() - 1 && K.Cum[I] < S) ++I;
	const float Seg = FMath::Max(1e-4f, K.Cum[I] - K.Cum[I - 1]);
	return FMath::Lerp(K.Poly[I - 1], K.Poly[I], FMath::Clamp((S - K.Cum[I - 1]) / Seg, 0.f, 1.f));
}

// point `Behind` metres behind the car's front along its path (link -> connector -> link)
FVector2D AWHLifeTraffic::PathPoint(const FCar& C, float Behind) const
{
	float Q = C.S - Behind;
	if (C.Where == 2)
	{
		if (Q >= 0.f) { const FLink& L = Links[C.L1]; return LinkPos(L, FMath::Min(Q, L.Len)); }
		const FConn& K = Conns[C.K]; Q += K.Len;
		if (Q >= 0.f) return ConnPos(K, Q);
		const FLink& L0 = Links[C.L0]; Q += L0.Len; return LinkPos(L0, FMath::Max(0.f, Q));
	}
	if (C.Where == 1)
	{
		const FConn& K = Conns[C.K];
		if (Q >= 0.f) return ConnPos(K, Q);
		const FLink& L0 = Links[C.L0]; Q += L0.Len; return LinkPos(L0, FMath::Max(0.f, Q));
	}
	const FLink& L = Links[C.L0];
	return L.A + L.D * FMath::Max(0.f, Q); // on the link: the rear is behind the start only for a fresh spawn (clamped)
}

// ------------------------------------------------------------------------------------------------ data
void AWHLifeTraffic::ParseLanes()
{
	Links.Reset(); Conns.Reset(); LinkIdx.Reset();
	TMap<int32, int32> ConnIdx;
	TArray<FString> Lines; LaneData.ParseIntoArrayLines(Lines);
	TArray<TArray<int32>> Xdefs;
	for (const FString& Ln : Lines)
	{
		if (Ln.IsEmpty() || Ln[0] == '#') continue;
		TArray<FString> P; Ln.ParseIntoArray(P, TEXT(" "), true);
		if (P.Num() < 2) continue;
		auto F = [&P](int32 I) { return I < P.Num() ? FCString::Atof(*P[I]) : 0.f; };
		auto N = [&P](int32 I) { return I < P.Num() ? FCString::Atoi(*P[I]) : 0; };
		if (P[0] == TEXT("L") && P.Num() >= 15)
		{
			FLink L; L.Id = N(1); L.From = N(2); L.To = N(3);
			L.A = FVector2D(F(4), F(5)); L.D = FVector2D(F(6), F(7)); L.Len = F(8);
			L.Kind = N(9); L.Lane = N(10); L.Axis = N(11); L.bSig = N(12) != 0; L.bNoPark = N(13) != 0; L.bNarrow = N(14) != 0;
			for (int32 I = 15; I < P.Num(); ++I) L.ParkSides.Add(F(I));
			LinkIdx.Add(L.Id, Links.Num()); Links.Add(MoveTemp(L));
		}
		else if (P[0] == TEXT("C") && P.Num() >= 7)
		{
			FConn K; K.Id = N(1); K.FromLink = N(2); K.ToLink = N(3); K.Turn = N(4); K.Len = F(5);
			const int32 Np = N(6);
			for (int32 I = 0; I < Np && 7 + 2 * I + 1 < P.Num(); ++I) K.Poly.Add(FVector2D(F(7 + 2 * I), F(8 + 2 * I)));
			K.Cum.Add(0.f);
			for (int32 I = 1; I < K.Poly.Num(); ++I) K.Cum.Add(K.Cum.Last() + (K.Poly[I] - K.Poly[I - 1]).Size());
			if (K.Cum.Num() > 1) K.Len = K.Cum.Last();
			ConnIdx.Add(K.Id, Conns.Num()); Conns.Add(MoveTemp(K));
		}
		else if (P[0] == TEXT("X") && P.Num() >= 3)
		{
			TArray<int32> D; for (int32 I = 1; I < P.Num(); ++I) D.Add(N(I)); Xdefs.Add(MoveTemp(D));
		}
	}
	for (FConn& K : Conns)
	{
		const int32* A = LinkIdx.Find(K.FromLink); const int32* B = LinkIdx.Find(K.ToLink);
		K.FromLink = A ? *A : -1; K.ToLink = B ? *B : -1;
	}
	for (const TArray<int32>& D : Xdefs)
	{
		const int32* Ci = ConnIdx.Find(D[0]); if (!Ci) continue;
		for (int32 J = 1; J < D.Num(); ++J) if (const int32* Cj = ConnIdx.Find(D[J])) Conns[*Ci].Conflicts.Add(*Cj);
	}
	for (int32 I = 0; I < Conns.Num(); ++I)
	{
		if (Conns[I].FromLink < 0 || Conns[I].ToLink < 0) continue;
		Links[Conns[I].FromLink].Outs.Add(I); Links[Conns[I].ToLink].Ins.Add(I);
	}
	for (FLink& L : Links) L.bEntry = L.Ins.Num() == 0;
	int32 NEntry = 0, NExit = 0; for (const FLink& L : Links) { NEntry += L.bEntry; NExit += L.Outs.Num() == 0; }
	UE_LOG(LogWHLife, Log, TEXT("[life] lanes: %d links, %d connectors, %d entries, %d exits"), Links.Num(), Conns.Num(), NEntry, NExit);
}

void AWHLifeTraffic::BuildComponents()
{
	MovingISM.Reset(); ParkedISM.Reset(); FreeInst.SetNum(NumTypes); Xf.SetNum(NumTypes); HighWater.Init(0, NumTypes); Dirty.Init(false, NumTypes);
	for (int32 T = 0; T < NumTypes; ++T)
	{
		UStaticMesh* M = VehicleMeshes.IsValidIndex(T) ? VehicleMeshes[T].Get() : nullptr;
		for (int32 Pass = 0; Pass < 2; ++Pass)
		{
			UInstancedStaticMeshComponent* C = NewObject<UInstancedStaticMeshComponent>(this, *FString::Printf(TEXT("%s_%s"), Pass ? TEXT("Parked") : TEXT("Moving"), GTypes[T].Name));
			C->SetupAttachment(GetRootComponent());
			C->SetStaticMesh(M);
			if (VehicleMaterial) { for (int32 S = 0; S < (M ? M->GetStaticMaterials().Num() : 1); ++S) C->SetMaterial(S, VehicleMaterial); }
			C->SetMobility(Pass ? EComponentMobility::Static : EComponentMobility::Movable);
			C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			C->SetCanEverAffectNavigation(false);
			C->SetGenerateOverlapEvents(false);
			C->SetCastShadow(bCastShadows);
			C->SetVisibleInRayTracing(bVisibleInRayTracing);
			C->bAffectDistanceFieldLighting = false;
			C->NumCustomDataFloats = 4;
			C->SetCullDistances(FMath::RoundToInt(CullDistance * 0.85f), FMath::RoundToInt(CullDistance));
			C->RegisterComponent();
			(Pass ? ParkedISM : MovingISM).Add(C);
		}
	}
}

void AWHLifeTraffic::PlaceParked()
{
	FVector4 ClearR(0, 0, 0, 0); bool bClear = false;
	{ FString S; if (FParse::Value(FCommandLine::Get(), TEXT("WHLifeClearParked="), S)) { TArray<FString> P; S.ParseIntoArray(P, TEXT(":"), true); if (P.Num() >= 4) { bClear = true; ClearR = FVector4(FCString::Atof(*P[0]), FCString::Atof(*P[1]), FCString::Atof(*P[2]), FCString::Atof(*P[3])); } } }
	NumParked = 0; NumParkedTaxis = 0; ParkedPts.Reset(); ParkedTypes.Reset();
	TArray<FString> Lines; ParkedData.ParseIntoArrayLines(Lines);
	TArray<TArray<FTransform>> Tx; Tx.SetNum(NumTypes);
	TArray<TArray<float>> Cd; Cd.SetNum(NumTypes);
	for (const FString& Ln : Lines)
	{
		if (Ln.IsEmpty() || Ln[0] == '#') continue;
		TArray<FString> P; Ln.ParseIntoArray(P, TEXT(" "), true);
		if (P.Num() < 7) continue;
		const int32 T = FCString::Atoi(*P[0]); if (T < 0 || T >= NumTypes) continue;
		const float X = FCString::Atof(*P[1]) * 100.f, Y = FCString::Atof(*P[2]) * 100.f, Yaw = FCString::Atof(*P[3]);
		if (bClear && X > ClearR.X * 100.f && X < ClearR.Z * 100.f && Y > ClearR.Y * 100.f && Y < ClearR.W * 100.f) continue;   // -WHLifeClearParked=x0:z0:x1:z1 (browser m): the camera walks through here
		if (ParkedGapEveryM > 1.f && FMath::Abs(FMath::Sin(FMath::DegreesToRadians(Yaw))) > 0.7f)
		{	// avenue curb (cars parked along z): bus stop / loading zone north of the street k (streets at z = 0 mod ParkedGapEveryM), on half of the (curb, street) pairs
			const float Z = Y * 0.01f; const int32 K = FMath::RoundToInt(Z / ParkedGapEveryM); const float D = Z - K * ParkedGapEveryM;   // < 0: north of the street
			if (D < -ParkedGapStartM && D > -(ParkedGapStartM + ParkedGapLenM))
			{
				const int32 Key = FMath::RoundToInt(X * 0.01f * 0.5f);   // curb line, 2 m steps
				uint32 H = ((uint32)Key * 2654435761u) ^ ((uint32)K * 40503u) ^ ((uint32)ParkedGapSeed * 9973u); H ^= H >> 15; H *= 2246822519u; H ^= H >> 13;
				if (H & 1u) continue;
			}
		}
		Tx[T].Add(FTransform(FRotator(0.f, Yaw, 0.f), FVector(X, Y, 1.f)));
		ParkedPts.Add(FVector(X, Y, 80.f)); ParkedTypes.Add(T);
		Cd[T].Append({ FCString::Atof(*P[4]), FCString::Atof(*P[5]), FCString::Atof(*P[6]), P.Num() > 7 ? FCString::Atof(*P[7]) : 0.f });
		++NumParked; if (T <= T_taxi_gr) ++NumParkedTaxis;
	}
	for (int32 T = 0; T < NumTypes; ++T)
	{
		if (Tx[T].Num() == 0 || !ParkedISM.IsValidIndex(T)) continue;
		UInstancedStaticMeshComponent* C = ParkedISM[T];
		C->AddInstances(Tx[T], false, true, false);
		C->SetCustomData(0, Tx[T].Num() - 1, Cd[T], false);
		C->MarkRenderStateDirty();
	}
}

int32 AWHLifeTraffic::PickType(const FLink& L, uint32& R) const
{
	const bool bBig = L.Kind != 1 && L.Lane == 1;
	float r = Ff(R);
	if (bBig && r < BusShare) return T_bus;
	if (bBig && r < BusShare + 0.02f) return T_tour;
	r = Ff(R);
	if (r < 0.13f) return T_truck; if (r < 0.21f) return T_van; if (r < 0.28f) return T_taxi_hy; if (r < 0.34f) return T_taxi_mv;
	if (r < 0.41f) return T_taxi_gr; if (r < 0.44f) return T_taxi; if (r < 0.52f) return T_sedan; if (r < 0.60f) return T_sedan2;
	if (r < 0.66f) return T_hatch; if (r < 0.74f) return T_suv; if (r < 0.82f) return T_cross; if (r < 0.93f) return T_suv2;
	return T_pickup;
}

FLinearColor AWHLifeTraffic::PickColor(int32 T, uint32& R) const
{
	const float r = Ff(R);
	if (T == T_taxi_gr) return r < 0.3f ? Lin(0x9aae4c) : Lin(0xf5a900);
	if (T <= T_taxi_gr) return Lin(0xf5a900);
	if ((T == T_suv2 && r < 0.7f) || (T == T_sedan2 && r < 0.4f) || (T == T_suv && r < 0.3f)) return Lin(GLivery[FMath::FloorToInt(r * 97.f) % 4]);
	if (T == T_truck || T == T_van) return Lin(GVan[FMath::FloorToInt(r * 4.f) % 4]);
	if (T == T_tour) return Lin(0xb3121a);
	if (T == T_bus) return Lin(0xe4e4e0);
	return Lin(GCarColors[FMath::FloorToInt(r * UE_ARRAY_COUNT(GCarColors)) % UE_ARRAY_COUNT(GCarColors)]);
}

// ------------------------------------------------------------------------------------------------ lifecycle
void AWHLifeTraffic::BeginPlay()
{
	Super::BeginPlay();
	FParse::Value(FCommandLine::Get(), TEXT("WHLifeStats="), StatsInterval);
	FParse::Value(FCommandLine::Get(), TEXT("WHLifeClearAhead="), ClearAheadM);
	{ FString G; if (FParse::Value(FCommandLine::Get(), TEXT("WHLifeClearCurb="), G)) { TArray<FString> P; G.ParseIntoArray(P, TEXT(":"), true); if (P.Num() >= 1) ClearCurbAheadM = FCString::Atof(*P[0]); if (P.Num() >= 2) ClearCurbOffsetM = FCString::Atof(*P[1]); } }
	FParse::Value(FCommandLine::Get(), TEXT("WHLifeDensity="), DensityScale);
	{ FString G; if (FParse::Value(FCommandLine::Get(), TEXT("WHLifeParkGap="), G)) { TArray<FString> P; G.ParseIntoArray(P, TEXT(":"), true); if (P.Num() >= 1) ParkedGapEveryM = FCString::Atof(*P[0]); if (P.Num() >= 2) ParkedGapLenM = FCString::Atof(*P[1]); if (P.Num() >= 3) ParkedGapSeed = FCString::Atoi(*P[2]); if (P.Num() >= 4) ParkedGapStartM = FCString::Atof(*P[3]); } }
	if (FParse::Param(FCommandLine::Get(), TEXT("WHLifeRT"))) bVisibleInRayTracing = true;
	if (FParse::Param(FCommandLine::Get(), TEXT("WHLifeNoShadow"))) bCastShadows = false;
	if (FParse::Param(FCommandLine::Get(), TEXT("WHLifeOff")) || FParse::Param(FCommandLine::Get(), TEXT("WHTrafficOff"))) { UE_LOG(LogWHLife, Display, TEXT("[life] traffic disabled by command line")); return; }
	GlobalRng = 0x9E3779B9u * (uint32)(Seed + 1);
	ParseLanes();
	if (Links.Num() == 0) { UE_LOG(LogWHLife, Warning, TEXT("[life] no lane data")); return; }
	BuildComponents();
	PlaceParked();
	Cars.SetNum(MaxCars + 8);
	FreeCars.Reset(); for (int32 I = Cars.Num() - 1; I >= 0; --I) FreeCars.Add(I);
	SimClock = 3.0 + Ff(GlobalRng) * 30.0;
	FParse::Value(FCommandLine::Get(), TEXT("WHLifeSignalPhase="), SignalPhaseAtStart);
	if (SignalPhaseAtStart >= 0.f && bSimulate)
	{ // the signal clock reads SignalPhaseAtStart when the pre-roll ends (= game time 0): fixed-camera signal clips
		const double Start = FMath::Fmod((double)SignalPhaseAtStart - (double)PreRollSeconds - (double)SignalOffset, 40.0);
		SimClock = Start + 80.0;
	}
	BuildSignals();
	FParse::Value(FCommandLine::Get(), TEXT("WHLifeActiveRadius="), ActiveRadiusM);
	if (bSimulate)
	{
		if (ActiveRadiusM > 0.f) { LinkActive.Init(0, Links.Num()); UpdateActivity(true); }
		else PopulateInitial();
		const float Step = 0.1f; const int32 N = FMath::RoundToInt(PreRollSeconds / Step);
		for (int32 I = 0; I < N; ++I) StepSim(Step);
	}
	bReady = true;
	for (TActorIterator<AWHCityLights> It(GetWorld()); It; ++It) RegisterNightLights(*It);   // night: headlights / taillights (AWHCityLights registers with us too when it starts later)
	PushInstances();
	UE_LOG(LogWHLife, Log, TEXT("[life] BeginPlay: %d moving, %d parked (%d taxis) instances, pre-roll %.0f s"), NumMoving, NumParked, NumParkedTaxis, PreRollSeconds);
}

void AWHLifeTraffic::Tick(float Dt)
{
	Super::Tick(Dt);
	if (!bReady || !bSimulate) return;
	const double T0 = FPlatformTime::Seconds();
	Accum += FMath::Min(Dt, 0.1f);
	const float Step = 1.f / 30.f;
	int32 Guard = 0;
	if (ActiveRadiusM > 0.f) { ActivityT += Dt; if (ActivityT >= 0.5f) { ActivityT = 0.f; UpdateActivity(false); } }
	while (Accum >= Step && Guard++ < 4) { StepSim(Step); Accum -= Step; }
	const double T1 = FPlatformTime::Seconds();
	UpdateSignals();
	bClearCam = false;
	if (CameraClearM > 0.f && GetWorld()) if (APlayerCameraManager* CM = UGameplayStatics::GetPlayerCameraManager(GetWorld(), 0)) { const FVector L = CM->GetCameraLocation(); if (L.Z < 450.f && !L.IsNearlyZero(50.f)) { bClearCam = true; ClearM = FVector2D(L.X, L.Y) * 0.01f; const FVector F = CM->GetCameraRotation().Vector(); const FVector2D F2(F.X, F.Y); ClearFwd = F2.SizeSquared() > 1e-4f ? F2.GetSafeNormal() : FVector2D(1, 0); } }
	PushInstances();
	const double T2 = FPlatformTime::Seconds();
	LastSimMs = (T1 - T0) * 1000.f; LastPushMs = (T2 - T1) * 1000.f;
	if (StatsInterval > 0.f) { StatsT += Dt; if (StatsT >= StatsInterval) { StatsT = 0.f; UE_LOG(LogWHLife, Log, TEXT("%s"), *StatsString()); } }
}

void AWHLifeTraffic::DumpCars(const FString& Path) const
{
	FString Out = TEXT("x,z,v,link,where,type,reserved,wait,acc\n");
	for (const FCar& C : Cars)
	{
		if (!C.bActive) continue;
		const FVector2D P = PathPoint(C, C.Len * 0.5f);
		const int32 LinkId = C.Where == 2 ? Links[C.L1].Id : Links[C.L0].Id;
		Out += FString::Printf(TEXT("%.2f,%.2f,%.2f,%d,%d,%d,%d,%.1f,%.2f\n"), P.X, P.Y, C.V, LinkId, (int32)C.Where, C.Type, C.bReserved ? 1 : 0, C.WaitT, C.Acc);
	}
	FFileHelper::SaveStringToFile(Out, *Path);
}

FString AWHLifeTraffic::StatsString() const
{
	return FString::Printf(TEXT("[life] moving %d (stopped %d, stopped in a junction box now %d, worst %d, box car-seconds %.1f) parked %d (taxis %d) sim %.2f ms push %.2f ms clock %.1f signal av/st %d/%d"), NumMoving, NumStopped, NumBoxStopped, MaxBoxStopped, BoxStopSeconds, NumParked, NumParkedTaxis, LastSimMs, LastPushMs, SimClock, SigPhase(GetSignalClock(), 0), SigPhase(GetSignalClock(), 1));
}

void AWHLifeTraffic::GetPoints(TArray<FVector>& Moving, TArray<int32>& MovingType, TArray<FVector>& Parked, TArray<int32>& ParkedType) const
{
	Moving.Reset(); MovingType.Reset();
	for (const FCar& C : Cars)
	{
		if (!C.bActive) continue;
		const FVector2D P = PathPoint(C, C.Len * 0.5f);
		Moving.Add(FVector(P.X * 100.f, P.Y * 100.f, 80.f)); MovingType.Add(C.Type);
	}
	Parked = ParkedPts; ParkedType = ParkedTypes;
}

int32 AWHLifeTraffic::CountInCone(FVector Eye, FVector Forward, float HalfAngleDeg, float Range) const
{
	int32 N = 0; const FVector F = Forward.GetSafeNormal(); const float CosA = FMath::Cos(FMath::DegreesToRadians(HalfAngleDeg));
	for (const FCar& C : Cars)
	{
		if (!C.bActive) continue;
		const FVector2D P = PathPoint(C, C.Len * 0.5f); const FVector W(P.X * 100.f, P.Y * 100.f, 80.f);
		const FVector D = W - Eye; const float Dist = D.Size();
		if (Dist < Range && Dist > 100.f && FVector::DotProduct(D / Dist, F) > CosA) ++N;
	}
	return N;
}

// ------------------------------------------------------------------------------------------------ spawning
int32 AWHLifeTraffic::SpawnCar(int32 LinkI, float Front, float V, bool)
{
	if (FreeCars.Num() == 0) return -1;
	const FLink& L = Links[LinkI];
	uint32 R = Xs(GlobalRng) ^ (uint32)(LinkI * 7919 + 13);
	if (R == 0) R = 1;
	const int32 T = PickType(L, R);
	const int32 CI = FreeCars.Pop();
	FCar& C = Cars[CI]; C = FCar();
	C.bActive = true; C.Type = T; C.Len = GTypes[T].Len; C.Wid = GTypes[T].Wid; C.Rng = R;
	C.V0 = (L.Kind == 1 ? 9.f : 12.5f) + Ff(C.Rng) * 3.5f; C.V = FMath::Min(V, C.V0);
	C.DA = 1.6f + Ff(C.Rng) * 0.8f; C.DTH = 0.8f + Ff(C.Rng) * 0.6f; C.DS0 = 1.5f + Ff(C.Rng);
	C.Lat = (Ff(C.Rng) < 0.25f ? 0.3f : 0.1f) * (Ff(C.Rng) < 0.5f ? -1.f : 1.f);
	C.Color = PickColor(T, C.Rng);
	C.L0 = LinkI; C.Where = 0; C.S = FMath::Max(Front, C.Len + 1.f); C.K = -1;
	C.K = ChooseNext(C, L);
	// instance slot
	int32 Slot;
	if (FreeInst[T].Num() > 0) Slot = FreeInst[T].Pop();
	else
	{
		Slot = HighWater[T]++;
		const FTransform Hidden(FRotator::ZeroRotator, FVector(0, 0, -1e6), FVector::ZeroVector);
		MovingISM[T]->AddInstance(Hidden, true);
		Xf[T].Add(Hidden);
	}
	C.Inst = Slot;
	const float CD[4] = { C.Color.R, C.Color.G, C.Color.B, 0.f };
	MovingISM[T]->SetCustomData(Slot, TConstArrayView<float>(CD, 4), false);
	Dirty[T] = true;
	return CI;
}

void AWHLifeTraffic::DespawnCar(int32 CI)
{
	FCar& C = Cars[CI]; if (!C.bActive) return;
	Release(C, CI);
	if (C.Inst >= 0) { Xf[C.Type][C.Inst] = FTransform(FRotator::ZeroRotator, FVector(0, 0, -5000.f), FVector(0.001f)); FreeInst[C.Type].Add(C.Inst); Dirty[C.Type] = true; }
	C.bActive = false; C.Inst = -1; FreeCars.Add(CI);
}

void AWHLifeTraffic::PopulateInitial()
{
	for (int32 LI = 0; LI < Links.Num(); ++LI) PopulateLink(LI);
}

void AWHLifeTraffic::PopulateLink(int32 LI)
{
	{
		FLink& L = Links[LI];
		uint32 R = 0x51ED27u ^ (uint32)(L.Id * 2654435761u); if (!R) R = 1;
		const float Target = L.Len / 1000.f * KindDensity(L.Kind) * (0.8f + 0.4f * Ff(R));
		const int32 N = FMath::RoundToInt(Target + Ff(R) - 0.5f);
		TArray<float> Placed;
		for (int32 K = 0; K < N; ++K)
		{
			for (int32 Try = 0; Try < 12; ++Try)
			{
				const float S = 8.f + Ff(R) * FMath::Max(1.f, L.Len - 12.f);
				bool bOk = true; for (float P : Placed) if (FMath::Abs(P - S) < 14.f) { bOk = false; break; }
				if (!bOk) continue;
				const int32 CI = SpawnCar(LI, S, 6.f + Ff(R) * 6.f, true);
				if (CI >= 0) Placed.Add(S);
				break;
			}
		}
		L.NextSpawn = (float)SimClock + 0.5f + Ff(R) * 3.f;
	}
}

void AWHLifeTraffic::UpdateActivity(bool bForce)
{
	if (ActiveRadiusM <= 0.f || !GetWorld()) return;
	APlayerCameraManager* CM = UGameplayStatics::GetPlayerCameraManager(GetWorld(), 0);
	if (!CM) return;
	const FVector Cam = CM->GetCameraLocation();
	const FVector2D P(Cam.X / 100.0, Cam.Y / 100.0);
	if (LinkActive.Num() != Links.Num()) LinkActive.Init(0, Links.Num());
	const float In2 = ActiveRadiusM * ActiveRadiusM, Out2 = (ActiveRadiusM * 1.3f) * (ActiveRadiusM * 1.3f);
	TArray<uint8> Emptied; Emptied.Init(0, Links.Num()); bool bAny = false;
	int32 NAct = 0, NDeact = 0;
	for (int32 LI = 0; LI < Links.Num(); ++LI)
	{
		const FLink& L = Links[LI];
		const float D2 = FVector2D::DistSquared(P, L.A + L.D * (L.Len * 0.5f));
		if (!LinkActive[LI] && D2 < In2) { LinkActive[LI] = 1; PopulateLink(LI); ++NAct; }
		else if (LinkActive[LI] && D2 > Out2) { LinkActive[LI] = 0; Emptied[LI] = 1; bAny = true; ++NDeact; }
	}
	if (bAny)
		for (int32 CI = 0; CI < Cars.Num(); ++CI)
		{
			const FCar& C = Cars[CI]; if (!C.bActive) continue;
			if ((C.L0 >= 0 && Emptied[C.L0]) || (C.Where == 2 && C.L1 >= 0 && Emptied[C.L1])) DespawnCar(CI);
		}
	if (bForce || NAct || NDeact) UE_LOG(LogWHLife, Verbose, TEXT("[life] activity: +%d -%d links"), NAct, NDeact);
}

int32 AWHLifeTraffic::ChooseNext(FCar& C, const FLink& L)
{
	if (L.Outs.Num() == 0) return -1;
	float Tot = 0.f; TArray<float, TInlineAllocator<8>> W;
	const bool bBig = GTypes[C.Type].bBig;
	for (int32 KI : L.Outs)
	{
		const FConn& K = Conns[KI];
		float X = K.Turn == 0 ? 0.66f : (bBig && K.Turn == 1 ? 0.02f : 0.17f);
		// drivers avoid an out link that is backed up to the corner
		const FLink& N = Links[K.ToLink];
		if (N.Cars.Num() > 0) { const FCar& Q = Cars[N.Cars[0]]; const float Tail = Q.S - Q.Len; if (Tail < C.Len + 8.f) X *= 0.08f + 0.92f * FMath::Max(0.f, Tail) / (C.Len + 8.f); }
		W.Add(X); Tot += X;
	}
	float R = Ff(C.Rng) * Tot;
	for (int32 I = 0; I < W.Num(); ++I) { R -= W[I]; if (R <= 0.f) return L.Outs[I]; }
	return L.Outs.Last();
}

// ------------------------------------------------------------------------------------------------ junction control
void AWHLifeTraffic::Release(FCar& C, int32 CI)
{
	if (!C.bReserved) return;
	if (C.K >= 0) Conns[C.K].Reserved.RemoveSingleSwap(CI);
	C.bReserved = false;
}

bool AWHLifeTraffic::CanClear(const FCar& C, const FLink& L) const
{
	// amber: a car that can stop comfortably at the line must; otherwise it goes on
	const float D = (L.Len - StopBack) - C.S;
	return !(D > C.V * C.V / (2.f * CompDecel) + 0.5f);
}

bool AWHLifeTraffic::TryReserve(FCar& C)
{
	// (find our own id) cars are addressed by index; C is a reference into Cars
	const int32 Me = (int32)(&C - Cars.GetData());
	if (C.K < 0) return true;
	FConn& K = Conns[C.K];
	if (K.Reserved.Contains(Me)) { C.bReserved = true; return true; }
	for (int32 Kc : K.Conflicts) if (Conns[Kc].Reserved.Num() > 0) return false;
	// exit space on the out link (whole car + margin + the cars already committed to this connector)
	const FLink& Out = Links[K.ToLink];
	float Space = 1e9f;
	if (Out.Cars.Num() > 0) { const FCar& Q = Cars[Out.Cars[0]]; Space = Q.S - Q.Len; }
	float Need = C.Len + 2.5f;
	for (int32 Id : K.Reserved) { const FCar& Q = Cars[Id]; if (Q.Where < 2) Need += Q.Len + 2.f; }
	if (Space < Need) return false;
	// left turns give way to oncoming traffic that is close to the box and moving (patience 9 s)
	if (K.Turn == 1 && C.WaitT < 9.f)
	{
		for (int32 Kc : K.Conflicts)
		{
			const FConn& X = Conns[Kc]; if (X.Turn == 1) continue;
			const FLink& Src = Links[X.FromLink];
			for (int32 Oi : Src.Cars)
			{
				const FCar& Q = Cars[Oi]; if (Q.Where != 0 || Q.bReserved) continue;
				if (Src.Len - Q.S < 24.f && Q.V > 2.5f) return false;
			}
		}
	}
	K.Reserved.Add(Me); C.bReserved = true; return true;
}

// ------------------------------------------------------------------------------------------------ leader search
void AWHLifeTraffic::FindLeader(int32 CI, float& Gap, float& VLead)
{
	const FCar& C = Cars[CI];
	Gap = 1e9f; VLead = C.V;
	auto Consider = [&](float G, float V) { if (G < Gap) { Gap = G; VLead = V; } };
	if (C.Where == 1)
	{
		const FConn& K = Conns[C.K];
		for (int32 Oi : K.Cars) { if (Oi == CI) continue; const FCar& Q = Cars[Oi]; if (Q.S > C.S) Consider(Q.S - Q.Len - C.S, Q.V); }
		if (Gap > 1e8f && K.ToLink >= 0)
		{
			const FLink& Out = Links[K.ToLink];
			if (Out.Cars.Num() > 0) { const FCar& Q = Cars[Out.Cars[0]]; Consider(K.Len - C.S + (Q.S - Q.Len), Q.V); }
		}
		return;
	}
	const int32 LI = C.Where == 0 ? C.L0 : C.L1;
	const FLink& L = Links[LI];
	for (int32 Oi : L.Cars) { if (Oi == CI) continue; const FCar& Q = Cars[Oi]; if (Q.S > C.S) { Consider(Q.S - Q.Len - C.S, Q.V); break; } }
	if (C.Where == 0)
	{
		// cars whose front is already in the box but whose rear is still on this link
		for (int32 KI : L.Outs)
			for (int32 Oi : Conns[KI].Cars)
			{
				if (Oi == CI) continue; const FCar& Q = Cars[Oi];
				if (Q.S < Q.Len) Consider(L.Len + (Q.S - Q.Len) - C.S, Q.V);
			}
		if (Gap > 1e8f && C.K >= 0)
		{
			const FConn& K = Conns[C.K]; const float Base = L.Len - C.S;
			for (int32 Oi : K.Cars) { const FCar& Q = Cars[Oi]; Consider(Base + (Q.S - Q.Len), Q.V); }
			if (Gap > 1e8f)
			{
				const FLink& Out = Links[K.ToLink];
				if (Out.Cars.Num() > 0) { const FCar& Q = Cars[Out.Cars[0]]; Consider(Base + K.Len + (Q.S - Q.Len), Q.V); }
			}
		}
	}
}

// ------------------------------------------------------------------------------------------------ the step
void AWHLifeTraffic::StepSim(float Dt)
{
	SimClock += Dt;
	const double Clock = SimClock + SignalOffset;
	// 1. per-link / per-connector lists (front on it), ascending S
	for (FLink& L : Links) L.Cars.Reset();
	for (FConn& K : Conns) K.Cars.Reset();
	for (int32 I = 0; I < Cars.Num(); ++I)
	{
		const FCar& C = Cars[I]; if (!C.bActive) continue;
		if (C.Where == 0) Links[C.L0].Cars.Add(I); else if (C.Where == 1) Conns[C.K].Cars.Add(I); else Links[C.L1].Cars.Add(I);
	}
	for (FLink& L : Links) L.Cars.Sort([this](int32 A, int32 B) { return Cars[A].S < Cars[B].S; });
	for (FConn& K : Conns) K.Cars.Sort([this](int32 A, int32 B) { return Cars[A].S < Cars[B].S; });

	// 2. accelerations
	NumStopped = 0;
	for (int32 I = 0; I < Cars.Num(); ++I)
	{
		FCar& C = Cars[I]; if (!C.bActive) continue;
		float Gap, VL; FindLeader(I, Gap, VL);
		float V0 = C.V0, Acc;
		float StopGap = 1e9f; bool bRed = false;
		if (C.Where == 0)
		{
			const FLink& L = Links[C.L0]; const float ToEnd = L.Len - C.S;
			if (C.K < 0 && L.Outs.Num() > 0) C.K = ChooseNext(C, L);
			if (C.K >= 0)
			{
				const FConn& K = Conns[C.K];
				const float Vt = K.Turn == 0 ? 1e9f : (K.Turn == 1 ? 5.5f : 4.5f);
				if (Vt < C.V + 3.f && ToEnd < 60.f) { const float G2 = FMath::Max(0.3f, ToEnd - 0.5f); if (C.V > Vt && G2 < Gap) { Gap = G2; VL = Vt; } }
				if (L.bSig && C.S < L.Len - StopBack - 0.25f)
				{
					const int32 Ph = SigPhase(Clock, L.Axis);
					if (Ph == 0 || (Ph == 1 && !CanClear(C, L))) { StopGap = (L.Len - StopBack) - C.S; bRed = true; }
				}
				if (StopGap > 1e8f && !C.bReserved)
				{
					const float Look = 7.f + C.V * C.V / 6.f;
					if (ToEnd < Look && !TryReserve(C)) StopGap = FMath::Max(0.f, ToEnd - 0.4f);
				}
			}
		}
		else if (C.Where == 1)
		{
			const FConn& K = Conns[C.K];
			V0 = FMath::Min(V0, K.Turn == 0 ? V0 : (K.Turn == 1 ? 6.f : 4.8f));
		}
		Acc = Idm(C.V, V0, Gap, VL, C.DA, 3.2f, C.DS0, C.DTH);
		if (StopGap < 1e8f)
		{
			const float G = FMath::Max(0.05f, StopGap + C.DS0 * 0.75f - 0.2f);
			Acc = FMath::Min(Acc, Idm(C.V, V0, G, 0.f, C.DA, 3.2f, C.DS0, C.DTH));
			if (C.V < 0.3f) C.WaitT += Dt;
		}
		else if (C.V > 0.5f) C.WaitT = 0.f;
		// reaction time: a driver held by the red / amber does not pull away in the same instant the light turns green
		if (bRed) C.bRedHold = true;
		else if (C.bRedHold) { C.bRedHold = false; if (C.V < 0.6f) C.GoDelay = ReactionMin + Ff(C.Rng) * FMath::Max(0.f, ReactionMax - ReactionMin); }
		if (C.GoDelay > 0.f) { C.GoDelay -= Dt; if (C.V < 0.6f) Acc = FMath::Min(Acc, 0.f); else C.GoDelay = 0.f; }
		if (C.V < 0.2f) { NumStopped++; C.StuckT += Dt; } else C.StuckT = 0.f;
		C.Acc = Acc;
		C.Brake = (Acc < -0.7f || (C.V < 0.4f && (StopGap < 1e8f || Gap < 8.f))) ? 1 : 0;
	}

	// 3. integrate + transitions
	for (int32 I = 0; I < Cars.Num(); ++I)
	{
		FCar& C = Cars[I]; if (!C.bActive) continue;
		C.Age += Dt;
		float NV = C.V + C.Acc * Dt;
		if (NV < 0.f) { NV = 0.f; }
		const float DS = 0.5f * (C.V + NV) * Dt;
		C.V = NV; C.S += DS;
		if (C.Where == 0)
		{
			const FLink& L = Links[C.L0];
			if (C.S >= L.Len)
			{
				if (C.K < 0) { DespawnCar(I); continue; }
				if (!C.bReserved) { Conns[C.K].Reserved.Add(I); C.bReserved = true; } // overshoot safety
				C.S -= L.Len; C.Where = 1;
			}
		}
		if (C.Where == 1)
		{
			const FConn& K = Conns[C.K];
			if (C.S >= K.Len) { C.S -= K.Len; C.Where = 2; C.L1 = K.ToLink; }
		}
		if (C.Where == 2 && C.S >= C.Len)
		{
			Release(C, I);
			C.L0 = C.L1; C.L1 = -1; C.K = -1; C.Where = 0;
			if (ActiveRadiusM > 0.f && LinkActive.IsValidIndex(C.L0) && !LinkActive[C.L0]) { DespawnCar(I); continue; }   // rolled out of the active radius
			C.K = ChooseNext(C, Links[C.L0]);
		}
		if (C.StuckT > 120.f) { DespawnCar(I); }
	}

	// 3b. junction-box watch: a car standing (< 0.3 m/s) with any part of its body inside a junction box
	{
		int32 BS = 0;
		for (int32 I = 0; I < Cars.Num(); ++I)
		{
			FCar& C = Cars[I]; if (!C.bActive) continue;
			const bool bIn = C.Where == 1 || (C.Where == 2 && C.S < C.Len);
			if (bIn && C.V < 0.3f)
			{
				const float Prev = C.BoxStopT; C.BoxStopT += Dt; BoxStopSeconds += Dt;
				if (C.BoxStopT > 0.8f) ++BS;
				if (Prev <= 1.5f && C.BoxStopT > 1.5f)
				{
					const FVector2D P = PathPoint(C, C.Len * 0.5f);
					UE_LOG(LogWHLife, Display, TEXT("WH_LIFE_BOXSTOP t=%.1f clock=%.1f car type %d at (%.1f, %.1f) m where=%d S=%.1f/%.1f v=%.2f reserved=%d turn=%d"), SimClock, SimClock + SignalOffset, C.Type, P.X, P.Y, (int32)C.Where, C.S, C.Where == 1 ? Conns[C.K].Len : C.Len, C.V, C.bReserved ? 1 : 0, C.K >= 0 ? Conns[C.K].Turn : -1);
				}
			}
			else C.BoxStopT = 0.f;
		}
		NumBoxStopped = BS; MaxBoxStopped = FMath::Max(MaxBoxStopped, BS);
	}

	// 4. inflow at the region boundary
	int32 Alive = 0; for (const FCar& C : Cars) Alive += C.bActive;
	for (int32 LI = 0; LI < Links.Num(); ++LI)
	{
		FLink& L = Links[LI];
		if (!L.bEntry || Clock < 0 || (float)SimClock < L.NextSpawn || Alive >= MaxCars) continue;
		if (ActiveRadiusM > 0.f && LinkActive.IsValidIndex(LI) && !LinkActive[LI]) continue;
		{ // inflow only tops the link up to the browser's steady-state density (traffic.js linkTarget), so cross streets do not fill with standing queues
			const float Target = L.Len / 1000.f * KindDensity(L.Kind);
			if ((float)L.Cars.Num() >= Target) { L.NextSpawn = (float)SimClock + 1.5f; continue; }
		}
		float Tail = 1e9f; for (int32 Oi : L.Cars) { const FCar& Q = Cars[Oi]; Tail = FMath::Min(Tail, Q.S - Q.Len); }
		uint32 R = Xs(GlobalRng);
		const float Gap = 4.f + Ff(R) * 10.f;
		if (Tail > 6.f + Gap)
		{
			const int32 CI = SpawnCar(LI, 6.f, 9.f, true);
			if (CI >= 0) { ++Alive; L.Cars.Add(CI); }
		}
		const float Flow = FMath::Max(0.05f, KindDensity(L.Kind) * (L.Kind == 1 ? 9.f : 12.f) / 1000.f); // veh/s
		L.NextSpawn = (float)SimClock + (0.5f + Ff(R)) / Flow;
	}
	NumMoving = Alive;
}

// ------------------------------------------------------------------------------------------------ signal lens overlay
// P1's signal props (mast / post heads) carry a static aState snapshot; this overlay draws the live lenses on top: a flat emissive disc per lens
// (red / amber / green), lit by the same 40 s clock the cars and pedestrians obey. Head geometry: src/world/props.js signalHeadX (lenses on the
// +x face at y +0.33 / 0 / -0.33 of the head centre), mast arm heads at (0, 5.3, 4.2 | 7.6), pole head (0.25, 3.3, 0), post head (0.22, 3.5, 0).
void AWHLifeTraffic::BuildSignals()
{
	Lenses.Reset(); LastSig[0] = LastSig[1] = -1; LensISM = nullptr;
	if (SignalData.IsEmpty() || !SignalMesh || !SignalMaterial) return;
	LensISM = NewObject<UInstancedStaticMeshComponent>(this, TEXT("SignalLenses"));
	LensISM->SetupAttachment(GetRootComponent());
	LensISM->SetStaticMesh(SignalMesh); LensISM->SetMaterial(0, SignalMaterial);
	LensISM->SetMobility(EComponentMobility::Movable);
	LensISM->SetCollisionEnabled(ECollisionEnabled::NoCollision); LensISM->SetCanEverAffectNavigation(false); LensISM->SetGenerateOverlapEvents(false);
	LensISM->SetCastShadow(false); LensISM->SetVisibleInRayTracing(false); LensISM->bAffectDistanceFieldLighting = false;
	LensISM->NumCustomDataFloats = 4;
	LensISM->SetCullDistances(30000, 40000);
	LensISM->RegisterComponent();
	struct FHead { float Lx, Ly, Lz; };
	static const FHead MastHeads[3] = { { 0.195f, 5.3f, 4.2f }, { 0.195f, 5.3f, 7.6f }, { 0.445f, 3.3f, 0.f } };
	static const FHead PostHeads[1] = { { 0.415f, 3.5f, 0.f } };
	static const float LensY[3] = { 0.33f, 0.f, -0.33f };   // red, amber, green
	static const float Col[3][3] = { { 1.f, 0.05f, 0.03f }, { 1.f, 0.5f, 0.02f }, { 0.05f, 1.f, 0.45f } };
	TArray<FTransform> Tx; TArray<float> Cd;
	TArray<FString> Lines; SignalData.ParseIntoArrayLines(Lines);
	for (const FString& Ln : Lines)
	{
		if (Ln.IsEmpty() || Ln[0] == '#') continue;
		TArray<FString> P; Ln.ParseIntoArray(P, TEXT(" "), true);
		if (P.Num() < 4 || (P[0] != TEXT("M") && P[0] != TEXT("P"))) continue;
		const bool bMast = P[0] == TEXT("M");
		const float Px = FCString::Atof(*P[1]), Pz = FCString::Atof(*P[2]), Ry = FCString::Atof(*P[3]);
		const float C = FMath::Cos(Ry), S = FMath::Sin(Ry);
		const int32 NH = bMast ? 3 : 1;
		for (int32 H = 0; H < NH; ++H)
		{
			const FHead& Hd = bMast ? MastHeads[H] : PostHeads[0];
			for (int32 K = 0; K < 3; ++K)
			{
				const float Lx = Hd.Lx, Ly = Hd.Ly + LensY[K], Lz = Hd.Lz;
				const float Wx = Px + Lx * C + Lz * S, Wz = Pz - Lx * S + Lz * C, Wy = 0.15f + Ly;
				Tx.Add(FTransform(FRotator(-90.f, -FMath::RadiansToDegrees(Ry), 0.f), FVector(Wx * 100.f, Wz * 100.f, Wy * 100.f), FVector(LensDiameterCm / 100.f, LensDiameterCm / 100.f, 0.02f)));
				Cd.Append({ Col[K][0], Col[K][1], Col[K][2], 0.f });
				FLens L; L.Axis = bMast ? 0 : 1; L.Color = K; L.Inst = Lenses.Num(); Lenses.Add(L);
			}
		}
	}
	if (Tx.Num() == 0) return;
	LensISM->AddInstances(Tx, false, true, false);
	LensISM->SetCustomData(0, Tx.Num() - 1, Cd, false);
	LensISM->MarkRenderStateDirty();
	UE_LOG(LogWHLife, Log, TEXT("[life] signals: %d lens instances (%d masts/posts)"), Lenses.Num(), Lines.Num());
	UpdateSignals();
}

void AWHLifeTraffic::UpdateSignals()
{
	if (!LensISM || Lenses.Num() == 0) return;
	bool bDirty = false;
	for (int32 Axis = 0; Axis < 2; ++Axis)
	{
		const int32 S = SigPhase(GetSignalClock(), Axis);
		if (S == LastSig[Axis]) continue;
		LastSig[Axis] = S; bDirty = true;
		for (const FLens& L : Lenses) if (L.Axis == Axis) LensISM->SetCustomDataValue(L.Inst, 3, L.Color == S ? 1.f : 0.f, false);
	}
	if (bDirty) LensISM->MarkRenderStateDirty();
}

bool AWHLifeTraffic::AnyCarNearSegment(const FVector2D& A, const FVector2D& B, float DistM) const
{
	const FVector2D AB = B - A; const float L2 = FMath::Max(1e-3f, AB.SizeSquared()); const float D2 = DistM * DistM;
	for (const FCar& C : Cars)
	{
		if (!C.bActive) continue;
		for (int32 K = 0; K < 3; ++K)
		{
			const FVector2D P = PathPoint(C, C.Len * 0.5f * K);
			const float T = FMath::Clamp(FVector2D::DotProduct(P - A, AB) / L2, 0.f, 1.f);
			if (FVector2D::DistSquared(P, A + AB * T) < D2) return true;
		}
	}
	return false;
}

void AWHLifeTraffic::GetMovingInfo(TArray<FVector>& Pos, TArray<float>& Speed, TArray<int32>& LaneKey) const
{
	Pos.Reset(); Speed.Reset(); LaneKey.Reset();
	for (const FCar& C : Cars)
	{
		if (!C.bActive) continue;
		const FVector2D P = PathPoint(C, C.Len * 0.5f);
		const FLink& L = Links[C.Where == 2 ? C.L1 : C.L0];
		const int32 Dir = FMath::Abs(L.D.X) > FMath::Abs(L.D.Y) ? (L.D.X > 0 ? 3 : 4) : (L.D.Y < 0 ? 1 : 2);
		Pos.Add(FVector(P.X * 100.f, P.Y * 100.f, 80.f)); Speed.Add(C.V); LaneKey.Add(L.Kind * 100 + L.Lane * 10 + Dir);
	}
}

void AWHLifeTraffic::GetLinkQueue(int32 LinkFileId, int32& NumCars, int32& Stopped, float& FrontToLine) const
{
	NumCars = 0; Stopped = 0; FrontToLine = -1.f;
	const int32* Ix = LinkIdx.Find(LinkFileId); if (!Ix) return;
	const FLink& L = Links[*Ix];
	float Best = 1e9f;
	for (const FCar& C : Cars)
	{
		if (!C.bActive || C.Where != 0 || C.L0 != *Ix) continue;
		++NumCars; if (C.V < 0.3f) ++Stopped;
		Best = FMath::Min(Best, (L.Len - StopBack) - C.S);
	}
	if (NumCars) FrontToLine = Best;
}

// ------------------------------------------------------------------------------------------------ render push
void AWHLifeTraffic::PushInstances()
{
	for (int32 I = 0; I < Cars.Num(); ++I)
	{
		FCar& C = Cars[I]; if (!C.bActive || C.Inst < 0) continue;
		const FVector2D PF = PathPoint(C, 0.9f), PR = PathPoint(C, C.Len - 0.9f);
		FVector2D Ctr = (PF + PR) * 0.5f, Dir = PF - PR;
		if (Dir.SizeSquared() < 1e-6f) Dir = FVector2D(1, 0);
		Dir.Normalize();
		if (C.Where == 0) { Ctr += FVector2D(-Dir.Y, Dir.X) * C.Lat; }
		const float Yaw = FMath::RadiansToDegrees(FMath::Atan2(Dir.Y, Dir.X));
		const float Pitch = C.Brake && C.V > 1.f ? 0.6f : 0.f;
		bool bHide = false;
		if (bClearCam)
		{ // distance from the camera to the car's body rectangle (centre, heading, length x width)
			const FVector2D Dc = ClearM - Ctr; const float Al = FMath::Abs(FVector2D::DotProduct(Dc, Dir)), La = FMath::Abs(FVector2D::DotProduct(Dc, FVector2D(-Dir.Y, Dir.X)));
			bHide = FMath::Sqrt(FMath::Square(FMath::Max(Al - C.Len * 0.5f, 0.f)) + FMath::Square(FMath::Max(La - C.Wid * 0.5f, 0.f))) < CameraClearM;
			if (!bHide && ClearAheadM > 0.f)
			{ // corridor ahead of the camera (fixed shots): the car's centre, from the camera, along / across the view heading
				const FVector2D Dv = Ctr - ClearM; const float Ah = FVector2D::DotProduct(Dv, ClearFwd), Cr = FMath::Abs(FVector2D::DotProduct(Dv, FVector2D(-ClearFwd.Y, ClearFwd.X)));
				const float Reach = FMath::Max(C.Len, C.Wid) * 0.5f;
				bHide = Ah > -Reach && Ah < ClearAheadM + Reach && Cr < ClearAheadHalfWidthM + C.Wid * 0.5f;
				if (!bHide && ClearCurbAheadM > ClearAheadM) bHide = Ah > -Reach && Ah < ClearCurbAheadM + Reach && Cr + C.Wid * 0.5f > ClearCurbOffsetM && Cr < ClearAheadHalfWidthM + C.Wid * 0.5f;   // curb lanes reach farther
			}
		}
		Xf[C.Type][C.Inst] = bHide ? FTransform(FRotator::ZeroRotator, FVector(0, 0, -5000.f), FVector(0.001f)) : FTransform(FRotator(Pitch, Yaw, 0.f), FVector(Ctr.X * 100.f, Ctr.Y * 100.f, 1.f));
		// brake-light state changes are rare: only write custom data when it differs from the ISM copy
		UInstancedStaticMeshComponent* M = MovingISM[C.Type];
		const int32 Idx = C.Inst * 4 + 3;
		if (M->PerInstanceSMCustomData.IsValidIndex(Idx) && M->PerInstanceSMCustomData[Idx] != (float)C.Brake)
		{
			const float CD[4] = { C.Color.R, C.Color.G, C.Color.B, (float)C.Brake };
			M->SetCustomData(C.Inst, TConstArrayView<float>(CD, 4), false); Dirty[C.Type] = true;
		}
	}
	for (int32 T = 0; T < NumTypes; ++T)
	{
		if (HighWater[T] == 0 || !MovingISM.IsValidIndex(T)) continue;
		MovingISM[T]->BatchUpdateInstancesTransforms(0, Xf[T], true, true, false);
		Dirty[T] = false;
	}
}
