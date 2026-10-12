// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Combat/WHCombatFx.h"
#include "Combat/WHCombatUtil.h"
#include "WebHomage.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

// Engine basic shapes are 100 cm: sphere diameter 100, cylinder diameter 100 x height 100 (centred).
static const double BASE_CM = 100.0;

void FWHCombatFx::Init(AActor* InOwner)
{
	Owner = InOwner;
	Sphere = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	Cyl = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	MGlow = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbFX.M_CmbFX"));
	MTrans = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbTrans.M_CmbTrans"));
	MSolid = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbSolid.M_CmbSolid"));
	MFlare = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbFlare.M_CmbFlare"));
	if (!MFlare) MFlare = MGlow;   // (the map script builds M_CmbFlare; without it the flare falls back to the plain additive glow)
}

FWHFxItem& FWHCombatFx::Alloc(EWHFxMat Mat, UStaticMesh* Mesh)
{
	int32 Idx = INDEX_NONE;
	for (int32 i = 0; i < Items.Num(); ++i)
		if (!Items[i].bLive && Items[i].Mat == Mat && Items[i].Comp && Items[i].Comp->GetStaticMesh() == Mesh) { Idx = i; break; }
	if (Idx == INDEX_NONE)
	{
		FWHFxItem It;
		AActor* O = Owner.Get();
		It.Comp = NewObject<UStaticMeshComponent>(O);
		It.Comp->SetStaticMesh(Mesh);
		It.Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		It.Comp->SetCastShadow(Mat == EWHFxMat::Solid);
		It.Comp->SetUsingAbsoluteLocation(true); It.Comp->SetUsingAbsoluteRotation(true); It.Comp->SetUsingAbsoluteScale(true);
		It.Comp->SetupAttachment(O->GetRootComponent());
		It.Comp->RegisterComponent();
		UMaterialInterface* Base = Mat == EWHFxMat::Glow ? MGlow : Mat == EWHFxMat::Trans ? MTrans : Mat == EWHFxMat::Flare ? MFlare : MSolid;
		if (Base) { It.Mid = UMaterialInstanceDynamic::Create(Base, O); It.Comp->SetMaterial(0, It.Mid); }
		It.Mat = Mat;
		Idx = Items.Add(It);
	}
	FWHFxItem& R = Items[Idx];
	UStaticMeshComponent* C = R.Comp; UMaterialInstanceDynamic* M = R.Mid;
	R = FWHFxItem();
	R.Comp = C; R.Mid = M; R.Mat = Mat; R.bLive = true;
	R.Comp->SetVisibility(true);
	++Spawned;
	return R;
}

void FWHCombatFx::Place(FWHFxItem& It, double K)
{
	FVector Sz = It.Size0 + (It.Size1 - It.Size0) * WHCmb::Smooth(K);
	FVector P = It.Pos, D = It.Dir;
	if (It.bStrand && It.A && It.B)
	{
		const FVector A = It.A(), B = It.B();
		D = B - A; const double L = D.Size(); D = L > 1e-4 ? D / L : FVector::UpVector;
		P = (A + B) * 0.5;
		Sz = FVector(It.Width, It.Width, L);
	}
	if (It.bStretch)
	{
		const double V = It.Vel.Size();
		if (V > 1e-3) D = It.Vel / V;
		Sz.Z = FMath::Max(Sz.X, V * 0.035);
	}
	const FQuat Q = FQuat::FindBetweenNormals(FVector::UpVector, D.GetSafeNormal());
	It.Comp->SetWorldLocationAndRotation(P * 100.0, Q);
	It.Comp->SetWorldScale3D(Sz); // basic shapes are 1 m at scale 1
	const double Op = FMath::Lerp(It.Op0, It.Op1, K);
	if (It.Mid)
	{
		It.Mid->SetVectorParameterValue(TEXT("Color"), It.Color);
		It.Mid->SetScalarParameterValue(TEXT("Opacity"), float(Op));
	}
}

void FWHCombatFx::Update(double GameDt, double RealDt)
{
	for (FWHFxItem& It : Items)
	{
		if (!It.bLive) continue;
		const double Dt = It.bReal ? RealDt : GameDt;
		It.T += Dt;
		if (It.T >= It.Life) { It.bLive = false; It.A = nullptr; It.B = nullptr; It.Comp->SetVisibility(false); continue; }
		if (It.bReal && It.T < It.Hold) { Place(It, 0); continue; }   // static while the hit-stop holds the frame
		It.Vel += It.Gravity * Dt;
		if (It.Drag > 0) It.Vel *= FMath::Exp(-It.Drag * Dt);
		It.Pos += It.Vel * Dt;
		Place(It, It.bReal ? (It.T - It.Hold) / FMath::Max(1e-3, It.Life - It.Hold) : It.T / It.Life);
	}
}

void FWHCombatFx::Clear()
{
	for (FWHFxItem& It : Items) { It.bLive = false; It.A = nullptr; It.B = nullptr; if (It.Comp) It.Comp->SetVisibility(false); }
	SenseIdx.Reset();
}

int32 FWHCombatFx::LiveCount() const
{
	int32 N = 0; for (const FWHFxItem& It : Items) N += It.bLive ? 1 : 0; return N;
}

void FWHCombatFx::Hit(const FVector& P, const FVector& Dir, double Heavy, const FLinearColor* Color, int32 HoldFrames)
{
	// A spark burst: a small additive core + radial streaks. HoldFrames > 0 keeps everything static for that many frames (the local hit-stop),
	// then the streaks fly out and fade in ~2.3 frames (r03: everything is gone 8 frames after the contact for a 5-frame hold).
	const FLinearColor C = Color ? *Color * 0.8f : FLinearColor(4.0f, 2.8f, 1.3f);
	const double Hold = HoldFrames > 0 ? (HoldFrames + 1.25) / 60.0 : 0.0, Life = Hold + (HoldFrames > 0 ? 2.3 / 60.0 : 0.09);
	{
		FWHFxItem& F = Alloc(EWHFxMat::Glow, Sphere);
		F.bReal = true; F.Hold = Hold; F.Pos = P; F.Life = Life;
		F.Size0 = FVector(0.1 + 0.08 * Heavy); F.Size1 = FVector(0.05);
		F.Color = C; F.Op0 = 0.9; F.Op1 = 0.0;
		Place(F, 0);
	}
	const int32 N = 8 + int32(8 * Heavy);
	const FVector D = Dir.GetSafeNormal();
	for (int32 i = 0; i < N; ++i)
	{
		FWHFxItem& S = Alloc(EWHFxMat::Glow, Cyl);
		const FVector R = (D * 0.9 + Rng.GetUnitVector()).GetSafeNormal();
		const double Len = Rng.FRandRange(0.16, 0.30 + 0.16 * Heavy) * (HoldFrames > 0 ? 1.5 : 1.0);   // r03: r02's 2-px ticks read as nothing at 5 m
		S.bReal = true; S.Hold = Hold; S.Life = Life;
		S.Dir = R; S.Pos = P + R * (0.08 + Len * 0.5); S.Vel = R * Rng.FRandRange(5.0, 9.0); S.Drag = 3.0;
		S.Size0 = FVector(0.02 + 0.012 * Heavy, 0.02 + 0.012 * Heavy, Len); S.Size1 = FVector(0.006, 0.006, Len * 0.6);
		S.Color = FLinearColor(C.R * 1.1f, C.G, C.B * 0.7f); S.Op0 = 1.0; S.Op1 = 0.0;
		Place(S, 0);
	}
}

void FWHCombatFx::Impact(const FVector& P, const FVector& Dir, double Heavy, const FLinearColor* Color, int32 HoldFrames)
{
	(void)Dir;
	if (bFlareOff) return;
	// r04 starburst. Unit U = the frame width in metres at the contact's depth; every length below is a share of it, so the picture is the same at any distance.
	//   N = 6 (7 / 8 for heavier blows) thin streaks, evenly spread around the contact (random phase, +-18 % jitter), each in the camera's image plane, from
	//   0.030 U (a hollow centre: only the small hot core sits on the victim's chest) to 0.128-0.16 U (length 0.098-0.127 U: always >= 8 % of the frame width)
	//   and tapering in 6 steps (0.0094 U -> 0.0036 U wide). Covered share of its bounding circle ~8 %, of the frame ~0.5 %: the victim's body stays readable.
	const FRotationMatrix CM(CamRot);
	const FVector Fw = bCam ? CM.GetScaledAxis(EAxis::X) : (P - CamP).GetSafeNormal();
	const FVector Right = bCam ? CM.GetScaledAxis(EAxis::Y) : FVector::RightVector;
	const FVector Up = bCam ? CM.GetScaledAxis(EAxis::Z) : FVector::UpVector;
	const double Depth = bCam ? FMath::Max(1.5, FVector::DotProduct(P - CamP, Fw)) : 5.5;
	const double U = 2.0 * Depth * FMath::Tan(FMath::DegreesToRadians(CamFovH * 0.5)) * FlareK;
	const double Hold = (HoldFrames + 1.25) / 60.0, Life = Hold + 2.3 / 60.0;
	const bool bTint = Color != nullptr && Color->R + Color->G + Color->B > 8.0f && Color->B > 3.0f;   // armoured (white) blow: cooler, white-hot streaks
	const int32 N = Heavy >= 0.55 ? 8 : Heavy >= 0.25 ? 7 : 6;
	const double Phase = FlareRng.FRandRange(0.0, 2.0 * PI), Step = 2.0 * PI / N;
	UE_LOG(LogWebHomage, Display, TEXT("WH_CMB_FLARE streaks %d depth %.2f m frame width %.2f m fov %.1f hold %d frames centre (%.2f, %.2f, %.2f)%s"), N, Depth, U, CamFovH, HoldFrames, P.X, P.Y, P.Z, bTint ? TEXT(" white") : TEXT(""));
	for (int32 i = 0; i < N; ++i)
	{
		const double A = Phase + i * Step + FlareRng.FRandRange(-0.18, 0.18) * Step;
		const FVector Dv = (Right * FMath::Cos(A) + Up * FMath::Sin(A)).GetSafeNormal();
		const double L = U * FlareRng.FRandRange(0.098, 0.115) * (1.0 + 0.1 * Heavy);
		const double R0 = U * 0.030;   // hollow centre: the streaks start beyond the victim's torso, so the body under the burst stays readable
		const int32 NS = 6;   // 6 stacked cylinders per streak: a smooth taper (0.94 -> 0.36 of the base width) and a colour that cools from orange to red-orange
		for (int32 j = 0; j < NS; ++j)
		{
			FWHFxItem& S = Alloc(EWHFxMat::Flare, Cyl);
			const double T = (j + 0.5) / NS, SegL = L / NS, C = R0 + L * T, W = U * 0.0100 * (1.0 - 0.7 * T);
			S.bReal = true; S.Hold = Hold; S.Life = Life;
			S.Dir = Dv; S.Pos = P + Dv * C;
			S.Size0 = FVector(W, W, SegL * 1.15); S.Size1 = FVector(W * 0.45, W * 0.45, SegL);
			S.Color = bTint ? FLinearColor(FMath::Lerp(2.2f, 1.5f, float(T)), FMath::Lerp(2.0f, 1.3f, float(T)), FMath::Lerp(1.7f, 1.05f, float(T)))
			                : FLinearColor(FMath::Lerp(2.4f, 1.5f, float(T)), FMath::Lerp(0.95f, 0.19f, FMath::Pow(float(T), 0.8f)), FMath::Lerp(0.16f, 0.02f, float(T)));
			S.Op0 = FlareI; S.Op1 = 0.0;
			Place(S, 0);
		}
	}
	{ // hot core: a small bright dot where the blow lands (3.5 % of the frame width)
		FWHFxItem& F = Alloc(EWHFxMat::Flare, Sphere);
		F.bReal = true; F.Hold = Hold; F.Pos = P; F.Life = Life;
		F.Size0 = FVector(U * 0.035); F.Size1 = FVector(U * 0.015);
		F.Color = bTint ? FLinearColor(2.4f, 2.2f, 2.0f) : FLinearColor(2.6f, 1.5f, 0.4f); F.Op0 = FlareI; F.Op1 = 0.0;
		Place(F, 0);
	}
}

void FWHCombatFx::Dust(const FVector& P, double Amount)
{
	const int32 N = 4 + int32(6 * Amount);
	for (int32 i = 0; i < N; ++i)
	{
		FWHFxItem& D = Alloc(EWHFxMat::Trans, Sphere);
		const double A = Rng.FRandRange(0.0, 2 * PI);
		D.Pos = P + FVector(FMath::Cos(A), FMath::Sin(A), 0) * Rng.FRandRange(0.1, 0.5) + FVector(0, 0, 0.1);
		D.Vel = FVector(FMath::Cos(A), FMath::Sin(A), 0) * Rng.FRandRange(1.0, 2.8) * Amount + FVector(0, 0, Rng.FRandRange(0.3, 1.2));
		D.Drag = 2.5; D.Life = Rng.FRandRange(0.6, 1.1);
		const double S = Rng.FRandRange(0.2, 0.36) * (0.7 + 0.5 * Amount);
		D.Size0 = FVector(S * 0.5); D.Size1 = FVector(S * 1.8);
		D.Color = FLinearColor(0.10f, 0.09f, 0.08f); D.Op0 = 0.24; D.Op1 = 0.0;   // r02: darker dust (in daylight the old grey read as white discs)
		Place(D, 0);
	}
}

int32 FWHCombatFx::Strand(TFunction<FVector()> A, TFunction<FVector()> B, double Life, double Sag, double Fade)
{
	FWHFxItem& S = Alloc(EWHFxMat::Solid, Cyl);
	S.bStrand = true; S.A = MoveTemp(A); S.B = MoveTemp(B); S.Life = Life; S.Width = 0.014; S.Sag = Sag;
	S.Color = FLinearColor(0.85f, 0.87f, 0.9f); S.Op0 = 1; S.Op1 = 1;
	S.Tag = NextTag++;
	if (S.Mid) { S.Mid->SetScalarParameterValue(TEXT("Emissive"), 0.6f); S.Mid->SetScalarParameterValue(TEXT("Rough"), 0.5f); }
	Place(S, 0);
	return S.Tag;
}

void FWHCombatFx::KillTag(int32 Tag)
{
	for (FWHFxItem& It : Items) if (It.bLive && It.Tag == Tag) { It.bLive = false; It.A = nullptr; It.B = nullptr; It.Comp->SetVisibility(false); }
}

void FWHCombatFx::WebHit(const FVector& P, const FVector& Dir)
{
	const FLinearColor W(2.6f, 2.7f, 2.9f);
	Hit(P, -Dir, 0.15, &W);
	for (int32 i = 0; i < 5; ++i)
	{
		FWHFxItem& D = Alloc(EWHFxMat::Trans, Sphere);
		D.Pos = P + Rng.GetUnitVector() * 0.12; D.Vel = Rng.GetUnitVector() * 0.6; D.Drag = 3; D.Life = 0.5;
		D.Size0 = FVector(0.08); D.Size1 = FVector(0.22); D.Color = FLinearColor(0.9f, 0.9f, 0.92f); D.Op0 = 0.7; D.Op1 = 0.0;
		Place(D, 0);
	}
}

void FWHCombatFx::Pellet(const FVector& P)
{
	FWHFxItem& D = Alloc(EWHFxMat::Glow, Sphere);
	D.Pos = P; D.Life = 0.04; D.Size0 = FVector(0.1); D.Size1 = FVector(0.1); D.Color = FLinearColor(2.6f, 2.7f, 2.9f); D.Op0 = 1; D.Op1 = 0.6;
	Place(D, 0);
}

void FWHCombatFx::Muzzle(const FVector& P, const FVector& Dir)
{
	FWHFxItem& F = Alloc(EWHFxMat::Glow, Sphere);
	F.Pos = P + Dir * 0.08; F.Life = 0.06; F.Size0 = FVector(0.22, 0.22, 0.22); F.Size1 = FVector(0.1);
	F.Color = FLinearColor(9.0f, 5.0f, 1.6f); F.Op0 = 1; F.Op1 = 0;
	Place(F, 0);
	FWHFxItem& C = Alloc(EWHFxMat::Glow, Cyl);
	C.Pos = P + Dir * 0.2; C.Dir = Dir; C.Life = 0.05; C.Size0 = FVector(0.06, 0.06, 0.35); C.Size1 = FVector(0.02, 0.02, 0.2);
	C.Color = FLinearColor(9.0f, 4.5f, 1.2f); C.Op0 = 1; C.Op1 = 0;
	Place(C, 0);
}

void FWHCombatFx::Tracer(const FVector& A, const FVector& B)
{
	FWHFxItem& T = Alloc(EWHFxMat::Glow, Cyl);
	const FVector D = B - A; const double L = D.Size();
	T.Pos = (A + B) * 0.5; T.Dir = L > 1e-4 ? D / L : FVector::ForwardVector; T.Life = 0.07;
	T.Size0 = FVector(0.012, 0.012, L); T.Size1 = FVector(0.004, 0.004, L);
	T.Color = FLinearColor(6.0f, 4.2f, 1.6f); T.Op0 = 1; T.Op1 = 0;
	Place(T, 0);
}

void FWHCombatFx::Splat(const FVector& P, const FVector& N, double Size)
{
	for (int32 i = 0; i < 3; ++i)
	{
		FWHFxItem& S = Alloc(EWHFxMat::Trans, Cyl);
		const double K = 1.0 - 0.28 * i;
		S.Pos = P + N * (0.01 + 0.004 * i) + Rng.GetUnitVector() * 0.08 * Size * i; S.Dir = N; S.Life = 60.0;
		S.Size0 = FVector(Size * 0.5 * K, Size * 0.42 * K, 0.004); S.Size1 = S.Size0;
		S.Color = FLinearColor(0.92f, 0.93f, 0.95f); S.Op0 = 0.72; S.Op1 = 0.6;
		Place(S, 0);
	}
}

void FWHCombatFx::Sense(double Level, bool bRed, const FVector& Head, double Dt)
{
	SenseT += Dt;
	// 6 short streaks radiating from the head (the "tingle"), pulsing with the level; hidden at 0
	const int32 N = 6;
	while (SenseIdx.Num() < N)
	{
		FWHFxItem& S = Alloc(EWHFxMat::Glow, Cyl);
		S.Life = 1e9; S.Op0 = S.Op1 = 0; S.Size0 = S.Size1 = FVector(0.01, 0.01, 0.1);
		SenseIdx.Add(int32(&S - Items.GetData()));
	}
	for (int32 i = 0; i < N; ++i)
	{
		if (!Items.IsValidIndex(SenseIdx[i])) continue;
		FWHFxItem& S = Items[SenseIdx[i]];
		S.bLive = true; S.T = 0; S.Life = 1e9;
		const double A = (i / double(N)) * 2 * PI + 0.35;
		const double Pulse = 0.75 + 0.25 * FMath::Sin(SenseT * 30.0 + i);
		const FVector Out = FVector(0, FMath::Cos(A), FMath::Sin(A) * 0.7 + 0.35).GetSafeNormal();
		S.Dir = Out; S.Pos = Head + Out * (0.22 + 0.06 * Level);
		S.Size0 = S.Size1 = FVector(0.012, 0.012, 0.12 + 0.14 * Level);
		S.Color = bRed ? FLinearColor(7.0f, 0.9f, 0.4f) : FLinearColor(6.0f, 3.0f, 0.6f);
		S.Op0 = S.Op1 = Level * Pulse;
		S.Comp->SetVisibility(Level > 0.02);
		Place(S, 0);
	}
}

void FWHCombatFx::Heal(const FVector& P)
{
	for (int32 i = 0; i < 24; ++i)
	{
		FWHFxItem& D = Alloc(EWHFxMat::Glow, Sphere);
		const double A = i / 24.0 * 2 * PI;
		D.Pos = P + FVector(FMath::Cos(A) * 0.6, FMath::Sin(A) * 0.6, -0.6 + Rng.FRand() * 0.4);
		D.Vel = FVector(0, 0, Rng.FRandRange(1.5, 3.0)); D.Drag = 1; D.Life = 0.8;
		D.Size0 = FVector(0.06); D.Size1 = FVector(0.02); D.Color = FLinearColor(1.5f, 3.5f, 2.0f); D.Op0 = 1; D.Op1 = 0;
		Place(D, 0);
	}
}
