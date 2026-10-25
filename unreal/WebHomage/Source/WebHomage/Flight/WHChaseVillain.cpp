// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
#include "Flight/WHChaseVillain.h"
#include "WebHomage.h"

#include "Components/SkeletalMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "Engine/EngineTypes.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Animation/AnimSequence.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Flight/WHFlightWorld.h"
#include "Traversal/Anim/WHHeroV2AnimInstance.h"

const TCHAR* AWHChaseVillain::Taunts[] = {
	TEXT("Catch me if you can!"),
	TEXT("Too slow!"),
	TEXT("You'll never take me alive!"),
	TEXT("Is that all you've got?"),
	TEXT("Over here, hero!"),
	TEXT("Keep up!"),
};

AWHChaseVillain::AWHChaseVillain()
{
	PrimaryActorTick.bCanEverTick = true;
	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
	Body = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Body"));
	Body->SetupAttachment(Root);
}

void AWHChaseVillain::BeginPlay()
{
	Super::BeginPlay();
	int32 Arg = 1;
	FParse::Value(FCommandLine::Get(), TEXT("-WHChase="), Arg);
	if (Arg == 0) { SetActorHiddenInGame(true); SetActorTickEnabled(false); return; }

	SetupBody();

	UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this);
	const FVector Hero = (FW && FW->bHeroValid) ? FW->HeroPosCm : GetActorLocation();
	// spawn ~600 m out on a random bearing, ~140 m up: close enough to find, far enough to chase
	const double A = FMath::FRand() * 2.0 * PI;
	PosCm = Hero + FVector(FMath::Cos(A) * 60000.0, FMath::Sin(A) * 60000.0, 14000.0);
	SetActorLocation(PosCm);
	SpawnT = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	if (FW) FW->ChaseStartT = SpawnT;
	UE_LOG(LogWebHomage, Display, TEXT("WH_CHASE villain spawned at (%.0f %.0f %.0f) -- catch him!"), PosCm.X, PosCm.Y, PosCm.Z);
}

void AWHChaseVillain::SetupBody()
{
	static const TCHAR* V2Object = TEXT("/Game/Invincible/HeroV2/SK_InvincibleV2.SK_InvincibleV2");
	USkeletalMesh* Mesh = LoadObject<USkeletalMesh>(nullptr, V2Object);
	FWHHeroV2RefFrame RF;
	if (Mesh && UWHHeroV2AnimInstance::ComputeRefFrame(Mesh, RF))
	{
		Body->SetSkeletalMesh(Mesh);
		Body->SetAnimationMode(EAnimationMode::AnimationSingleNode);
		const double Scale = FMath::Clamp(185.0 / RF.HeightUnits, 1e-5, 1e3);
		const FQuat Corr = FRotationMatrix::MakeFromXZ(RF.Fwd, RF.Up).ToQuat().Inverse();
		const FVector Pivot = RF.Pelvis + RF.Up * (RF.BottomUp - FVector::DotProduct(RF.Pelvis, RF.Up));
		Body->SetRelativeScale3D(FVector(Scale));
		Body->SetRelativeRotation(Corr);
		Body->SetRelativeLocation(-Corr.RotateVector(Pivot * Scale));
		Body->SetBoundsScale(2.f);
		Body->SetCastShadow(true);
		Body->bPerBoneMotionBlur = false;
		Body->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
	}
	else
	{	// fallback: an un-posed capsule so the chase still works on a checkout without the v2 content
		UE_LOG(LogWebHomage, Warning, TEXT("WH_CHASE %s missing (%s): capsule stand-in"), V2Object,
			Mesh ? TEXT("bad ref frame") : TEXT("load failed"));
	}
	// the evil skin: M_CmbSolid is the codebase's parameterized lit-solid material (Color / Emissive / Rough / Metal)
	if (UMaterialInterface* Solid = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbSolid.M_CmbSolid")))
	{
		if (UMaterialInstanceDynamic* Mi = UMaterialInstanceDynamic::Create(Solid, this))
		{
			Mi->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.09f, 0.09f, 0.11f));   // near-black suit
			Mi->SetScalarParameterValue(TEXT("Emissive"), 0.10f);
			Mi->SetScalarParameterValue(TEXT("Rough"), 0.62f);
			Mi->SetScalarParameterValue(TEXT("Metal"), 0.25f);
			const int32 N = Body->GetNumMaterials();
			for (int32 I = 0; I < N; ++I) Body->SetMaterial(I, Mi);
		}
	}
	SeqHover = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Invincible/HeroV2/Anims/AS_Hover.AS_Hover"));
	SeqFly = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Invincible/HeroV2/Anims/AS_Fly.AS_Fly"));
	SeqBoost = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Invincible/HeroV2/Anims/AS_BoostHold.AS_BoostHold"));
	SetClip(SeqHover);
}

void AWHChaseVillain::SetClip(UAnimSequence* Seq)
{
	if (!Seq || Seq == CurSeq) return;
	CurSeq = Seq;
	Body->PlayAnimation(Seq, true);
}

void AWHChaseVillain::Tick(float Dt)
{
	Super::Tick(Dt);
	UWorld* W = GetWorld();
	if (!W || Dt <= 0.f) return;
	StepBrain(Dt);
	StepMove(Dt);
	Publish(W);
}

void AWHChaseVillain::StepBrain(float Dt)
{
	UWorld* W = GetWorld();
	UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this);
	if (!W || !FW || !FW->bHeroValid) return;
	const float Now = W->GetTimeSeconds();
	const FVector Hero = FW->HeroPosCm;
	const double DistM = FVector::Dist(PosCm, Hero) / 100.0;

	if (State == EState::Caught) return;

	// ---- catch: body contact, or E / Triangle held inside CatchRadiusM
	const bool bGrab = DistM <= CatchRadiusM && FW->bInteractHeld;
	if (DistM <= TouchRadiusM || bGrab) { OnCaught(Now); return; }

	// ---- chase trigger: the hero inside FleeRadius starts the flee; he keeps running briefly after the hero drops back
	if (State == EState::Roam && DistM <= FleeRadiusM) { State = EState::Flee; BurstCd = 1.0f; }
	if (State == EState::Flee) FleeHoldT = (DistM <= FleeRadiusM * 1.6) ? 1.6f : FleeHoldT - Dt;
	if (State == EState::Flee && FleeHoldT <= 0.f) { State = EState::Roam; bHaveWay = false; }

	if (State == EState::Roam)
	{
		const double WayD = bHaveWay ? FVector::Dist(PosCm, WayCm) / 100.0 : 0.0;
		if (!bHaveWay || WayD < 60.0) PickWaypoint();
	}
	MaybeTaunt(Now, DistM, Dt);

	// low passes scare the street, same as the hero's flyovers
	StimT -= Dt;
	if (StimT <= 0.f && VelCm.Size() / 100.0 > 20.0)
	{
		FHitResult Fh;
		if (W->LineTraceSingleByObjectType(Fh, PosCm, PosCm - FVector(0, 0, 14000.0), FCollisionObjectQueryParams(ECC_WorldStatic)) && Fh.Distance < 10000.0)
			FW->PushStimulus(EWHCrowdStimulus::Flyover, PosCm, 4500.f, 0.8f, 3.f, VelCm);
		StimT = 0.7f;
	}
}

void AWHChaseVillain::StepMove(float Dt)
{
	UWorld* W = GetWorld();
	UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this);
	if (!W || !FW) return;
	const FVector Hero = FW->HeroPosCm;
	WeaveT += Dt;

	FVector Want; double Speed;
	if (State == EState::Caught)
	{
		Want = FVector::ZeroVector; Speed = 0.0;
	}
	else if (State == EState::Flee)
	{
		// run directly away from the hero with a lateral weave; brief bursts on a cooldown
		FVector Away = PosCm - Hero;
		if (Away.SizeSquared() < 1.0) Away = FVector(1.0, 0, 0);
		Away.Normalize();
		const FVector Side(-Away.Y, Away.X, 0.0);
		FVector Dir = Away + Side * (0.55 * FMath::Sin(WeaveT * 2.1)) + FVector(0, 0, 0.10 * FMath::Sin(WeaveT * 1.3));
		BurstCd -= Dt;
		if (BurstCd <= 0.f) { BurstT = BurstDur; BurstCd = BurstEvery; }
		Speed = FleeSpeed;
		if (BurstT > 0.f) { BurstT -= Dt; Speed = BurstSpeed; }
		Dir.Normalize();
		Want = Dir * Speed * 100.0;
	}
	else
	{
		FVector Dir = (bHaveWay ? WayCm - PosCm : FVector::ZeroVector);
		if (Dir.SizeSquared() < 1.0) Dir = FVector(0, 0, 0);
		else Dir.Normalize();
		Dir += FVector(0.25 * FMath::Sin(WeaveT * 0.9), 0.25 * FMath::Cos(WeaveT * 0.7), 0.12 * FMath::Sin(WeaveT * 1.1));
		Dir.Normalize();
		Speed = RoamSpeed;
		Want = Dir * Speed * 100.0;
	}

	// ---- world guards: floor below and solids ahead (two cheap line traces; he never breaches)
	FHitResult Hit;
	const FVector Vn = VelCm.GetSafeNormal();
	const FVector Ahead = (Vn.IsNearlyZero() ? GetActorForwardVector() : Vn) * (Speed * 100.0 * 1.5 + 20000.0);
	if (W->LineTraceSingleByObjectType(Hit, PosCm, PosCm + Ahead, FCollisionObjectQueryParams(ECC_WorldStatic)))
	{
		const FVector N = Hit.ImpactNormal;
		FVector Deflect = FVector::VectorPlaneProject(Want.GetSafeNormal(), N) + N * 0.8 + FVector(0, 0, 0.5);
		Want = Deflect.GetSafeNormal() * FMath::Max(Speed, 30.0) * 100.0;
	}
	if (W->LineTraceSingleByObjectType(Hit, PosCm, PosCm - FVector(0, 0, 50000.0), FCollisionObjectQueryParams(ECC_WorldStatic))
		&& Hit.Distance < MinAltM * 100.0 + (VelCm.Z < 0.0 ? double(-VelCm.Z) * 1.2 : 0.0))
		Want.Z = FMath::Max(Want.Z, FMath::Abs(Want.Z) + FMath::Max(3000.0, FMath::Abs(VelCm.Z) * 0.8));

	VelCm += (Want - VelCm) * FMath::Min(1.0, 3.0 * Dt);
	if (State == EState::Caught) VelCm *= FMath::Max(0.0, 1.0 - 4.0 * Dt);
	PosCm += VelCm * Dt;
	SetActorLocation(PosCm);

	// ---- facing: yaw into the travel; pitch the body along the path only in the path-aligned clips
	const double Spd = VelCm.Size() / 100.0;
	UAnimSequence* WantSeq = (Spd < 8.0 || State == EState::Caught) ? SeqHover : (Spd > 85.0 ? SeqBoost : SeqFly);
	SetClip(WantSeq);
	const double Yaw = Spd > 2.0 ? FMath::RadiansToDegrees(FMath::Atan2(VelCm.Y, VelCm.X)) : GetActorRotation().Yaw;
	const bool bPathClip = (WantSeq == SeqFly || WantSeq == SeqBoost);
	FlyPitch += (((bPathClip && Spd > 2.0) ? FMath::RadiansToDegrees(FMath::Asin(FMath::Clamp(VelCm.Z / VelCm.Size(), -1.0, 1.0))) : 0.0) - FlyPitch) * FMath::Min(1.0, 6.0 * Dt);
	FRotator R = GetActorRotation(); R.Yaw = float(Yaw); R.Pitch = float(FMath::Clamp(FlyPitch, -60.0, 60.0)); R.Roll = 0.0;
	SetActorRotation(R);
}

void AWHChaseVillain::PickWaypoint()
{
	UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this);
	const FVector Hero = (FW && FW->bHeroValid) ? FW->HeroPosCm : PosCm;
	const double A = FMath::FRand() * 2.0 * PI;
	const double R = FMath::FRandRange(300.0, 900.0) * 100.0;
	const double Z = FMath::FRandRange(MinAltM + 8.0, MaxAltM) * 100.0;
	WayCm = Hero + FVector(FMath::Cos(A) * R, FMath::Sin(A) * R, Z);
	bHaveWay = true;
}

void AWHChaseVillain::MaybeTaunt(float Now, double DistM, float Dt)
{
	UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this);
	TauntCd -= Dt;
	if (FW && TauntCd <= 0.f && DistM <= 160.0 && DistM > TouchRadiusM && Now >= SpawnT + 5.f)
	{
		const int32 I = FMath::RandHelper(int32(UE_ARRAY_COUNT(Taunts)));
		FW->VillainTaunt = Taunts[I];
		FW->VillainTauntUntil = Now + 4.f;
		TauntCd = 7.f;
	}
}

void AWHChaseVillain::OnCaught(float Now)
{
	State = EState::Caught;
	CaughtT = Now;
	UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this);
	if (FW)
	{
		FW->bVillainCaught = true;
		FW->ChaseCaughtT = Now;
		FW->VillainTaunt = TEXT("Okay, okay -- you got me.");
		FW->VillainTauntUntil = Now + 6.f;
		FW->PushStimulus(EWHCrowdStimulus::Landing, PosCm, 5000.f, 1.f, 4.f, FVector::ZeroVector);
	}
	UE_LOG(LogWebHomage, Display, TEXT("WH_CHASE villain caught after %.1f s"), Now - (FW ? FW->ChaseStartT : 0.f));
}

void AWHChaseVillain::Publish(UWorld* W)
{
	UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this);
	if (!FW) return;
	FW->VillainPosCm = PosCm;
	FW->VillainVelCm = VelCm;
	FW->VillainState = int32(State);
	FW->bVillainActive = State != EState::Caught;
	FW->bVillainCaught = State == EState::Caught;
	if (W && W->GetTimeSeconds() > FW->VillainTauntUntil) FW->VillainTaunt.Empty();
}
