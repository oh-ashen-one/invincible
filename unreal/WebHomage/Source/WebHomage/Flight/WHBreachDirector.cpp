// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
// Invincible flight conversion (owner request 2026-10-15). See WHBreachDirector.h.
#include "Flight/WHBreachDirector.h"
#include "Flight/WHFlightWorld.h"
#include "WebHomage.h"
#include "Components/StaticMeshComponent.h"
#include "Components/DecalComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundWaveProcedural.h"
#include "GeometryCollection/GeometryCollectionActor.h"
#include "GeometryCollection/GeometryCollectionComponent.h"
#include "GeometryCollection/GeometryCollectionObject.h"
#include "HAL/PlatformTime.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace
{
	const FName NB_breachIn(TEXT("breachIn")), NB_breachOut(TEXT("breachOut")), NB_heroLand(TEXT("heroLand")), NB_sonicBoom(TEXT("sonicBoom")),
		NB_flyBump(TEXT("flyBump")), NB_takeoff(TEXT("takeoff"));
	const FLinearColor BdConcrete(0.42f, 0.40f, 0.37f), BdBrick(0.38f, 0.22f, 0.16f), BdSteel(0.20f, 0.21f, 0.23f), BdScorch(0.025f, 0.022f, 0.02f);
	FVector BdAnyPerp(const FVector& N) { return FVector::CrossProduct(N, FMath::Abs(N.Z) < 0.9 ? FVector::UpVector : FVector::ForwardVector).GetSafeNormal(); }
}

AWHBreachDirector::AWHBreachDirector()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bTickEvenWhenPaused = false;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

void AWHBreachDirector::BeginPlay()
{
	Super::BeginPlay();
	Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	Cyl = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	Sphere = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	MSolid = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbSolid.M_CmbSolid"));
	MTrans = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbTrans.M_CmbTrans"));
	MGlow = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbFX.M_CmbFX"));
	if (!MSolid) MSolid = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	MDecal = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Invincible/FX/M_CraterDecal.M_CraterDecal"));
	GcAsset = LoadObject<UGeometryCollection>(nullptr, TEXT("/Game/Invincible/Destruction/GC_FacadeChunk.GC_FacadeChunk"));
	bNoSlowMo = FParse::Param(FCommandLine::Get(), TEXT("WHNoSlowMo"));
	bNoAudio = FParse::Param(FCommandLine::Get(), TEXT("WHNoFlightAudio"));
	Fx.Init(this);
	UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT breach director ready: materials %s, authored fracture %s, crater decal %s, slow-mo %s"),
		MSolid && MTrans ? TEXT("ok") : TEXT("FALLBACK"), GcAsset ? TEXT("yes") : TEXT("no (proxy chunks only)"), MDecal ? TEXT("yes") : TEXT("no (disc)"),
		bNoSlowMo ? TEXT("off") : TEXT("on"));
}

void AWHBreachDirector::EndPlay(const EEndPlayReason::Type Reason)
{
	if (bSlowMo) UGameplayStatics::SetGlobalTimeDilation(this, 1.f);
	Fx.Clear();
	Super::EndPlay(Reason);
}

UStaticMeshComponent* AWHBreachDirector::MakeComp(UStaticMesh* Mesh, UMaterialInterface* Base, UMaterialInstanceDynamic*& OutMid, bool bShadow)
{
	UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
	C->SetStaticMesh(Mesh);
	C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	C->SetCastShadow(bShadow);
	C->SetUsingAbsoluteLocation(true); C->SetUsingAbsoluteRotation(true); C->SetUsingAbsoluteScale(true);
	C->SetupAttachment(RootComponent);
	C->SetMobility(EComponentMobility::Movable);
	C->RegisterComponent();
	OutMid = Base ? UMaterialInstanceDynamic::Create(Base, this) : nullptr;
	if (OutMid) C->SetMaterial(0, OutMid);
	C->SetVisibility(false);
	return C;
}

void AWHBreachDirector::OnFlightEvents(const TArray<FWebTravEvent>& Events)
{
	for (const FWebTravEvent& E : Events)
	{
		if (E.Type == NB_breachIn) Breach(E.Pos, E.Dir, E.Severity, true);
		else if (E.Type == NB_breachOut) Breach(E.Pos, E.Dir, E.Severity, false);
		else if (E.Type == NB_heroLand) Crater(E.Pos, E.Severity);
		else if (E.Type == NB_sonicBoom) Boom(E.Pos, E.Dir);
		else if (E.Type == NB_flyBump) Bump(E.Pos, E.Dir, E.Severity);
		else if (E.Type == NB_takeoff) Fx.Dust(E.Pos, 0.6);
	}
}

void AWHBreachDirector::Breach(const FVector& PosM, const FVector& DirM, float Sev, bool bEntry)
{
	const FVector P = PosM * 100.0;
	const FVector D = DirM.GetSafeNormal();
	// debris: entry blows inward (with the hero), exit blows outward; both spray forward along the flight line
	const double Sp = 1800.0 + 2600.0 * Sev;
	SpawnChunks(P, D, ChunksPerBreach, Sp, bEntry ? BdConcrete : BdBrick, 35.0 + 30.0 * Sev);
	SpawnShards(P, D, ShardsPerBreach, Sp * 1.2);
	Fx.Dust(PosM, 2.5 + 2.5 * Sev);
	Fx.Dust(PosM + D * 3.0, 2.0 + 2.0 * Sev);
	{ FLinearColor Spark(3.0f, 2.2f, 1.4f); Fx.Hit(PosM, D, 1.0, &Spark); }
	// the hole: a scorched plate flush with the facade, square-on to the flight line (the facade normal is ~ -D at an entry)
	const FQuat Q = FRotationMatrix::MakeFromZX(-D, BdAnyPerp(D)).ToQuat();
	PlaceScar(P - D * (bEntry ? 5.0 : -5.0), Q, FVector(3.2 + 1.6 * Sev, 2.6 + 1.2 * Sev, 0.08), BdScorch);
	if (GcAsset) SpawnGc(P, D);
	PlaySynth(1, P, 0.8f + 0.2f * Sev);
	if (bEntry)
	{
		LastBreachEntry = P;
		if (!bNoSlowMo && SlowMoScale < 0.999f) StartSlowMo();
		if (UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this))
		{
			++FW->Breaches;
			FW->AddCollateral(BreachUSD + BreachUSDPerSev * Sev, TEXT("building breach"));
		}
	}
	UE_LOG(LogWebHomage, Display, TEXT("WH_FLIGHT breach %s fx at %s sev %.2f (chunks live %d)"), bEntry ? TEXT("in") : TEXT("out"), *PosM.ToString(), Sev,
		Chunks.FilterByPredicate([](const FChunk& C) { return C.bLive; }).Num());
}

void AWHBreachDirector::Crater(const FVector& PosM, float Sev)
{
	const FVector P = PosM * 100.0;
	// crater: a dark disc flush with the floor (or the authored decal), a raised rubble ring, dust, a shock ring
	if (MDecal)
	{
		UDecalComponent* Dc = nullptr;
		if (Decals.Num() < MaxScars)
		{
			Dc = NewObject<UDecalComponent>(this);
			Dc->SetupAttachment(RootComponent);
			Dc->SetUsingAbsoluteLocation(true); Dc->SetUsingAbsoluteRotation(true); Dc->SetUsingAbsoluteScale(true);
			Dc->RegisterComponent();
			Decals.Add(Dc);
		}
		else { Dc = Decals[NextDecal % Decals.Num()]; ++NextDecal; }
		Dc->SetDecalMaterial(MDecal);
		const double R = 220.0 + 260.0 * Sev;
		Dc->DecalSize = FVector(120.0, R, R);
		Dc->SetWorldLocationAndRotation(P, FRotator(-90.0, 0.0, 0.0));
		Dc->SetVisibility(true);
	}
	else PlaceScar(P + FVector(0, 0, 2.0), FQuat::Identity, FVector(4.2 + 4.0 * Sev, 4.2 + 4.0 * Sev, 0.03), BdScorch);
	SpawnChunks(P + FVector(0, 0, 20.0), FVector::UpVector, ChunksPerCrater, 700.0 + 900.0 * Sev, BdConcrete, 25.0 + 25.0 * Sev);
	Fx.Dust(PosM, 3.0 + 4.0 * Sev);
	{
		FRing* Rg = nullptr;
		for (FRing& R : Rings) if (!R.bLive) { Rg = &R; break; }
		if (!Rg && Sphere) { FRing N; N.Comp = MakeComp(Sphere, MTrans ? MTrans.Get() : MSolid.Get(), N.Mid, false); KeepAlive.Add(N.Comp); Rings.Add(N); Rg = &Rings.Last(); }
		if (Rg) { Rg->bLive = true; Rg->T = 0; Rg->Life = 0.55; Rg->R1 = 9.0 + 12.0 * Sev; Rg->Pos = P + FVector(0, 0, 40.0); Rg->Q = FQuat::Identity; Rg->Comp->SetVisibility(true); }
	}
	PlaySynth(2, P, 0.6f + 0.4f * Sev);
	if (UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this))
	{
		++FW->Craters;
		FW->AddCollateral(CraterUSD + CraterUSDPerSev * Sev, TEXT("crater landing"));
	}
}

void AWHBreachDirector::Boom(const FVector& PosM, const FVector& DirM)
{
	// a vapour cone / shock ring square-on to the flight line, expanding over ~0.7 s, and the boom itself
	FRing* Rg = nullptr;
	for (FRing& R : Rings) if (!R.bLive) { Rg = &R; break; }
	if (!Rg && Sphere) { FRing N; N.Comp = MakeComp(Sphere, MGlow ? MGlow.Get() : MTrans.Get(), N.Mid, false); KeepAlive.Add(N.Comp); Rings.Add(N); Rg = &Rings.Last(); }
	if (Rg)
	{
		const FVector D = DirM.GetSafeNormal();
		Rg->bLive = true; Rg->T = 0; Rg->Life = 0.7; Rg->R1 = 28.0;
		Rg->Pos = PosM * 100.0 - D * 150.0;
		Rg->Q = FRotationMatrix::MakeFromZX(D, BdAnyPerp(D)).ToQuat();
		Rg->Comp->SetVisibility(true);
	}
	PlaySynth(0, PosM * 100.0, 1.f);
}

void AWHBreachDirector::Bump(const FVector& PosM, const FVector& NormalM, float Sev)
{
	Fx.Dust(PosM, 0.8 + 1.2 * Sev);
	SpawnChunks(PosM * 100.0, NormalM.GetSafeNormal(), 4 + int32(6 * Sev), 500.0 + 700.0 * Sev, BdConcrete, 18.0);
	if (UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this)) FW->AddCollateral(5000.f + 20000.f * Sev, TEXT("facade scrape"));
}

void AWHBreachDirector::SpawnChunks(const FVector& PosCm, const FVector& DirN, int32 N, double SpeedCms, const FLinearColor& Tint, double SizeCm)
{
	if (!Cube) return;
	const FVector Side = BdAnyPerp(DirN), Up = FVector::CrossProduct(DirN, Side);
	for (int32 K = 0; K < N; ++K)
	{
		FChunk* Ch = nullptr;
		if (Chunks.Num() < MaxChunks)
		{
			FChunk New;
			New.Comp = MakeComp(Cube, MSolid, New.Mid, true);
			New.Comp->SetCollisionProfileName(TEXT("PhysicsActor"));
			New.Comp->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
			New.Comp->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
			New.Comp->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
			New.Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			KeepAlive.Add(New.Comp);
			Chunks.Add(New);
			Ch = &Chunks.Last();
		}
		else { Ch = &Chunks[NextChunk % Chunks.Num()]; ++NextChunk; } // recycle the oldest
		UStaticMeshComponent* C = Ch->Comp;
		C->SetSimulatePhysics(false);
		const double S = SizeCm * Rng.FRandRange(0.45f, 1.25f) / 100.0;
		const FVector Off = Side * Rng.FRandRange(-120.f, 120.f) + Up * Rng.FRandRange(-120.f, 120.f);
		C->SetWorldLocationAndRotation(PosCm + Off, FRotator(Rng.FRandRange(0.f, 360.f), Rng.FRandRange(0.f, 360.f), Rng.FRandRange(0.f, 360.f)));
		C->SetWorldScale3D(FVector(S * Rng.FRandRange(0.6f, 1.4f), S * Rng.FRandRange(0.6f, 1.4f), S * Rng.FRandRange(0.4f, 1.0f)));
		if (Ch->Mid)
		{
			const float V = Rng.FRandRange(0.8f, 1.15f);
			Ch->Mid->SetVectorParameterValue(TEXT("Color"), FLinearColor(Tint.R * V, Tint.G * V, Tint.B * V, 1.f));
			Ch->Mid->SetScalarParameterValue(TEXT("Rough"), 0.9f);
		}
		C->SetVisibility(true);
		C->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		C->SetSimulatePhysics(true);
		const FVector Cone = (DirN + Side * Rng.FRandRange(-0.55f, 0.55f) + Up * Rng.FRandRange(-0.35f, 0.65f)).GetSafeNormal();
		C->SetPhysicsLinearVelocity(Cone * SpeedCms * Rng.FRandRange(0.35f, 1.0f));
		C->SetPhysicsAngularVelocityInDegrees(FVector(Rng.FRandRange(-720.f, 720.f), Rng.FRandRange(-720.f, 720.f), Rng.FRandRange(-720.f, 720.f)));
		Ch->bLive = true; Ch->Born = GetWorld()->GetTimeSeconds();
	}
}

void AWHBreachDirector::SpawnShards(const FVector& PosCm, const FVector& DirN, int32 N, double SpeedCms)
{
	if (!Cube) return;
	const FVector Side = BdAnyPerp(DirN), Up = FVector::CrossProduct(DirN, Side);
	for (int32 K = 0; K < N; ++K)
	{
		FShard* Sh = nullptr;
		if (Shards.Num() < MaxShards)
		{
			FShard New;
			New.Comp = MakeComp(Cube, MTrans ? MTrans.Get() : MSolid.Get(), New.Mid, false);
			KeepAlive.Add(New.Comp);
			Shards.Add(New);
			Sh = &Shards.Last();
		}
		else { Sh = &Shards[NextShard % Shards.Num()]; ++NextShard; }
		Sh->bLive = true; Sh->T = 0; Sh->Life = Rng.FRandRange(0.9f, 1.8f);
		Sh->Pos = PosCm + Side * Rng.FRandRange(-150.f, 150.f) + Up * Rng.FRandRange(-120.f, 150.f);
		Sh->Vel = (DirN + Side * Rng.FRandRange(-0.8f, 0.8f) + Up * Rng.FRandRange(-0.4f, 0.9f)).GetSafeNormal() * SpeedCms * Rng.FRandRange(0.3f, 1.0f);
		Sh->Q = FRotator(Rng.FRandRange(0.f, 360.f), Rng.FRandRange(0.f, 360.f), 0.f).Quaternion();
		Sh->Spin = FVector(Rng.FRandRange(-12.f, 12.f), Rng.FRandRange(-12.f, 12.f), Rng.FRandRange(-12.f, 12.f));
		const float S = Rng.FRandRange(0.06f, 0.22f);
		Sh->Comp->SetWorldScale3D(FVector(S, S * Rng.FRandRange(0.5f, 1.2f), 0.006f));
		if (Sh->Mid)
		{
			Sh->Mid->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.62f, 0.78f, 0.86f, 1.f));
			Sh->Mid->SetScalarParameterValue(TEXT("Opacity"), 0.55f);
			Sh->Mid->SetScalarParameterValue(TEXT("Emissive"), 0.4f);
		}
		Sh->Comp->SetVisibility(true);
	}
}

void AWHBreachDirector::PlaceScar(const FVector& PosCm, const FQuat& Q, const FVector& ScaleM, const FLinearColor& Color)
{
	if (!Cyl) return;
	FScar* Sc = nullptr;
	if (Scars.Num() < MaxScars)
	{
		FScar New; New.Comp = MakeComp(Cyl, MSolid, New.Mid, false); KeepAlive.Add(New.Comp); Scars.Add(New); Sc = &Scars.Last();
	}
	else { Sc = &Scars[NextScar % Scars.Num()]; ++NextScar; }
	Sc->Comp->SetWorldLocationAndRotation(PosCm, Q);
	Sc->Comp->SetWorldScale3D(ScaleM);
	if (Sc->Mid) { Sc->Mid->SetVectorParameterValue(TEXT("Color"), Color); Sc->Mid->SetScalarParameterValue(TEXT("Rough"), 1.f); }
	Sc->Comp->SetVisibility(true);
}

void AWHBreachDirector::SpawnGc(const FVector& PosCm, const FVector& DirN)
{
	UGeometryCollection* GC = Cast<UGeometryCollection>(GcAsset.Get());
	if (!GC || MaxGcActors <= 0) return;
	if (GcActors.Num() >= MaxGcActors)
	{
		const int32 I = NextGc % GcActors.Num(); ++NextGc;
		if (GcActors[I]) GcActors[I]->Destroy();
		GcActors.RemoveAt(I);
	}
	FActorSpawnParameters SP; SP.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	AGeometryCollectionActor* A = GetWorld()->SpawnActor<AGeometryCollectionActor>(PosCm, FRotationMatrix::MakeFromX(-DirN).Rotator(), SP);
	if (!A) return;
	if (UGeometryCollectionComponent* C = A->GetGeometryCollectionComponent())
	{
		C->SetRestCollection(GC);
		C->SetSimulatePhysics(true);
		C->CrumbleActiveClusters();
	}
	A->SetLifeSpan(8.f);
	GcActors.Add(A);
}

void AWHBreachDirector::StartSlowMo()
{
	UGameplayStatics::SetGlobalTimeDilation(this, FMath::Clamp(SlowMoScale, 0.05f, 1.f));
	const double Now = FPlatformTime::Seconds();
	SlowMoUntil = Now + SlowMoReal; SlowMoEaseEnd = SlowMoUntil + 0.2;
	bSlowMo = true;
}

USoundBase* AWHBreachDirector::Authored(int32 Kind) const
{
	const TCHAR* Path = Kind == 0 ? TEXT("/Game/Invincible/Audio/S_SonicBoom.S_SonicBoom") : Kind == 1 ? TEXT("/Game/Invincible/Audio/S_Breach.S_Breach") : TEXT("/Game/Invincible/Audio/S_HeroLand.S_HeroLand");
	return LoadObject<USoundBase>(nullptr, Path);
}

void AWHBreachDirector::PlaySynth(int32 Kind, const FVector& PosCm, float Volume)
{
	if (bNoAudio) return;
	if (USoundBase* A = Authored(Kind)) { UGameplayStatics::PlaySoundAtLocation(this, A, PosCm, Volume); return; }
	// synthesized one-shot (mono 48 kHz int16): boom = N-wave crack + 38 Hz thump; crash = noise burst + debris crackle; thud = 55 Hz thump + noise
	const int32 Rate = 48000;
	const double Dur = Kind == 0 ? 1.6 : Kind == 1 ? 1.4 : 1.0;
	const int32 N = int32(Dur * Rate);
	TArray<uint8> Bytes; Bytes.SetNumUninitialized(N * 2);
	int16* Pcm = reinterpret_cast<int16*>(Bytes.GetData());
	FRandomStream R(1234 + Kind);
	double Lp = 0.0;
	for (int32 I = 0; I < N; ++I)
	{
		const double T = double(I) / Rate;
		const double Noise = R.FRandRange(-1.f, 1.f);
		Lp += (Noise - Lp) * (Kind == 1 ? 0.35 : 0.08);
		double V = 0.0;
		if (Kind == 0)
		{
			const double Crack = T < 0.012 ? (1.0 - 2.0 * T / 0.012) : 0.0;           // N-wave
			const double Thump = FMath::Sin(2.0 * PI * 38.0 * T) * FMath::Exp(-T * 3.2);
			V = 0.9 * Crack + 0.8 * Thump + 0.35 * Lp * FMath::Exp(-T * 2.0);
		}
		else if (Kind == 1)
		{
			const double Burst = Lp * FMath::Exp(-T * 3.5);
			const double Crackle = (R.FRand() < 0.004 * FMath::Exp(-T * 2.0)) ? R.FRandRange(-1.f, 1.f) : 0.0;
			V = 0.85 * Burst + 0.6 * Crackle + 0.5 * FMath::Sin(2.0 * PI * 48.0 * T) * FMath::Exp(-T * 5.0);
		}
		else
		{
			V = 0.9 * FMath::Sin(2.0 * PI * 55.0 * T) * FMath::Exp(-T * 4.5) + 0.4 * Lp * FMath::Exp(-T * 6.0);
		}
		const double Fade = FMath::Clamp((Dur - T) / 0.05, 0.0, 1.0);
		Pcm[I] = int16(FMath::Clamp(V * Fade, -1.0, 1.0) * 30000.0);
	}
	USoundWaveProcedural* W = NewObject<USoundWaveProcedural>(this);
	W->SetSampleRate(Rate);
	W->NumChannels = 1;
	W->Duration = float(Dur);
	W->SoundGroup = SOUNDGROUP_Default;
	W->bLooping = false;
	W->QueueAudio(Bytes.GetData(), Bytes.Num());
	KeepAlive.Add(W);
	if (KeepAlive.Num() > 900) KeepAlive.RemoveAt(0, 100); // components live in the pools; old procedural waves are released
	UGameplayStatics::PlaySoundAtLocation(this, W, PosCm, Volume);
}

void AWHBreachDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const double Dt = DeltaSeconds;
	Fx.Update(Dt, Dt);
	// slow-mo (real time)
	if (bSlowMo)
	{
		const double Now = FPlatformTime::Seconds();
		if (Now >= SlowMoEaseEnd) { UGameplayStatics::SetGlobalTimeDilation(this, 1.f); bSlowMo = false; }
		else if (Now >= SlowMoUntil)
		{
			const double K = (Now - SlowMoUntil) / FMath::Max(1e-3, SlowMoEaseEnd - SlowMoUntil);
			UGameplayStatics::SetGlobalTimeDilation(this, float(FMath::Lerp(double(SlowMoScale), 1.0, K * K * (3.0 - 2.0 * K))));
		}
	}
	// chunks: retire after ChunkLife (or if they fell out of the world)
	const double Now = GetWorld()->GetTimeSeconds();
	for (FChunk& C : Chunks)
	{
		if (!C.bLive) continue;
		if (Now - C.Born > ChunkLife || C.Comp->GetComponentLocation().Z < -50000.0)
		{
			C.Comp->SetSimulatePhysics(false);
			C.Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			C.Comp->SetVisibility(false);
			C.bLive = false;
		}
	}
	// glass: ballistic, spinning, fading
	for (FShard& S : Shards)
	{
		if (!S.bLive) continue;
		S.T += Dt;
		if (S.T >= S.Life) { S.bLive = false; S.Comp->SetVisibility(false); continue; }
		S.Vel += FVector(0, 0, -980.0) * Dt;
		S.Vel *= FMath::Exp(-0.8 * Dt);
		S.Pos += S.Vel * Dt;
		if (S.Spin.SizeSquared() > 0) S.Q = (FQuat(S.Spin.GetSafeNormal(), S.Spin.Size() * Dt) * S.Q).GetNormalized();
		S.Comp->SetWorldLocationAndRotation(S.Pos, S.Q);
		if (S.Mid) S.Mid->SetScalarParameterValue(TEXT("Opacity"), float(0.55 * (1.0 - S.T / S.Life)));
	}
	// shock rings: flattened sphere expanding square-on to the flight line
	for (FRing& Rg : Rings)
	{
		if (!Rg.bLive) continue;
		Rg.T += Dt;
		const double K = FMath::Clamp(Rg.T / Rg.Life, 0.0, 1.0);
		if (K >= 1.0) { Rg.bLive = false; Rg.Comp->SetVisibility(false); continue; }
		const double R = 0.5 + Rg.R1 * (1.0 - (1.0 - K) * (1.0 - K));
		Rg.Comp->SetWorldLocationAndRotation(Rg.Pos, Rg.Q);
		Rg.Comp->SetWorldScale3D(FVector(R, R, 0.04 + 0.3 * K));
		if (Rg.Mid)
		{
			Rg.Mid->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.85f, 0.9f, 1.0f, 1.f));
			Rg.Mid->SetScalarParameterValue(TEXT("Opacity"), float(0.45 * (1.0 - K)));
		}
	}
}
