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
#include "Flight/WHBreachDirector.h"
#include "Traversal/Anim/WHHeroV2AnimInstance.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "Camera/CameraActor.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"

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
	FString Tune;
	if (FParse::Value(FCommandLine::Get(), TEXT("-WHChaseTune="), Tune, false) && !Tune.IsEmpty()) ApplyTune(Tune);

	SetupBody();

	UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this);
	const FVector Hero = (FW && FW->bHeroValid) ? FW->HeroPosCm : GetActorLocation();
	// spawn ~280 m out on a random bearing, ~55 m up, hovering in place under a tall beacon: he is meant to be FOUND
	const double A = FMath::FRand() * 2.0 * PI;
	PosCm = Hero + FVector(FMath::Cos(A) * 28000.0, FMath::Sin(A) * 28000.0, 5500.0);
	SetActorLocation(PosCm);
	State = EState::WaitHere;
	SpawnT = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	if (FW) FW->ChaseStartT = SpawnT;
	if (Beacon) Beacon->SetVisibility(true);
	UE_LOG(LogWebHomage, Display, TEXT("WH_CHASE villain waiting at (%.0f %.0f %.0f) -- find him!"), PosCm.X, PosCm.Y, PosCm.Z);
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

	// the beacon: a tall thin glow column hanging off him (down from his hover) so he can be FOUND across the city
	if (UStaticMesh* Cyl = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder")))
	{
		Beacon = NewObject<UStaticMeshComponent>(this, TEXT("Beacon"));
		Beacon->SetupAttachment(RootComponent);
		Beacon->SetStaticMesh(Cyl);
		Beacon->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Beacon->SetCastShadow(false);
		Beacon->SetRelativeLocation(FVector(0, 0, -16000.0));   // column hangs 160 m below him to the rooftops
		Beacon->SetRelativeScale3D(FVector(1.6, 1.6, 320.0));   // cylinder is 100 cm tall at scale 1
		if (UMaterialInterface* FX = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbFX.M_CmbFX")))
			if (UMaterialInstanceDynamic* Mi = UMaterialInstanceDynamic::Create(FX, this))
			{
				Mi->SetVectorParameterValue(TEXT("Color"), FLinearColor(4.0f, 0.15f, 0.10f));
				Mi->SetScalarParameterValue(TEXT("Opacity"), 0.5f);
				Beacon->SetMaterial(0, Mi);
			}
		Beacon->RegisterComponent();
	}
	// the aura: a faint red shell around his body -- visible a few hundred metres out where a 1.85 m figure is just pixels
	if (UStaticMesh* Sph = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere")))
	{
		Aura = NewObject<UStaticMeshComponent>(this, TEXT("Aura"));
		Aura->SetupAttachment(Body);
		Aura->SetStaticMesh(Sph);
		Aura->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Aura->SetCastShadow(false);
		Aura->SetRelativeLocation(FVector(0, 0, 90.0));
		Aura->SetRelativeScale3D(FVector(4.0, 4.0, 5.0));
		if (UMaterialInterface* FX = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbFX.M_CmbFX")))
			if (UMaterialInstanceDynamic* Mi = UMaterialInstanceDynamic::Create(FX, this))
			{
				Mi->SetVectorParameterValue(TEXT("Color"), FLinearColor(3.0f, 0.10f, 0.08f));
				Mi->SetScalarParameterValue(TEXT("Opacity"), 0.30f);
				Aura->SetMaterial(0, Mi);
			}
		Aura->RegisterComponent();
	}
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
	// B after a catch restarts the chase (he re-spawns on a fresh bearing)
	if (State == EState::Caught)
	{
		if (APlayerController* PC = W->GetFirstPlayerController())
		{
			const bool bB = PC->IsInputKeyDown(EKeys::B);
			if (bB && !bPrevB) RestartChase(W->GetTimeSeconds());
			bPrevB = bB;
		}
	}
	StepBrain(Dt);
	StepMove(Dt);
	if (State == EState::Scene) StepScene(Dt);
	Publish(W);
}

// ---- the cutscene (owner request 2026-10-25): hero reaches him -> a few second exchange on different camera
// angles, then he bolts. The scene camera is a spawned ACameraActor; the view goes back to the pawn at the end.
void AWHChaseVillain::BeginScene(const FVector& HeroPosCm)
{
	UWorld* W = GetWorld();
	UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this);
	if (!W || !FW) return;
	State = EState::Scene;
	SceneT = 0.f;
	FW->bChaseScene = true;
	if (Beacon) Beacon->SetVisibility(false);
	if (APlayerController* PC = W->GetFirstPlayerController())
	{
		FActorSpawnParameters SP; SP.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		if (ACameraActor* Cam = W->SpawnActor<ACameraActor>(PosCm, FRotator::ZeroRotator, SP))
		{
			SceneCam = Cam;
			PC->SetViewTargetWithBlend(Cam, 0.5f);
		}
	}
	FW->ChaseLine = TEXT("VILLAIN: If you can't beat me in a race... I'm going to destroy this city.");
	FW->ChaseLineUntil = W->GetTimeSeconds() + 3.2f;
	UE_LOG(LogWebHomage, Display, TEXT("WH_CHASE cutscene start"));
}

void AWHChaseVillain::StepScene(float Dt)
{
	UWorld* W = GetWorld();
	UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this);
	if (!W || !FW || !SceneCam.IsValid()) { EndScene(); return; }
	SceneT += Dt;
	const float Now = W->GetTimeSeconds();
	const FVector Hero = FW->bHeroValid ? FW->HeroPosCm : PosCm + FVector(900, 0, 0);
	// beats: {endT, camera kind, line}; camera positions re-evaluated each frame so the shot tracks both flyers
	struct FBeat { float End; int32 Cam; const TCHAR* Line; };
	static const FBeat Beats[] = {
		{ 3.2f, 0, TEXT("VILLAIN: If you can't beat me in a race... I'm going to destroy this city.") },
		{ 6.2f, 1, TEXT("YOU: No -- don't do that. I'll stop you.") },
		{ 9.0f, 2, TEXT("VILLAIN: Oh yeah? Catch me if you can.") },
		{ 11.0f, 3, TEXT("") },
	};
	int32 I = 0;
	while (I < int32(UE_ARRAY_COUNT(Beats)) - 1 && SceneT >= Beats[I].End) ++I;
	const FBeat& B = Beats[I];
	if (B.Line[0] && FW->ChaseLineUntil < Now + B.End - SceneT - 0.2f) { FW->ChaseLine = B.Line; FW->ChaseLineUntil = Now + (B.End - SceneT) - 0.05f; }
	// ---- camera per beat: 0 wide side-on, 1 over-villain-shoulder on the hero, 2 over-hero-shoulder on the villain, 3 pull-back behind him
	const FVector Mid = (PosCm + Hero) * 0.5;
	const FVector ToV = (PosCm - Hero).GetSafeNormal();
	const FVector Side(-ToV.Y, ToV.X, 0.0);
	FVector CamPos; FVector LookAt;
	if (B.Cam == 0)      { CamPos = Mid + Side * 1600.0 + FVector(0, 0, 250.0); LookAt = Mid + FVector(0, 0, 80.0); }
	else if (B.Cam == 1) { CamPos = PosCm + ToV * 650.0 + FVector(0, 0, 180.0); LookAt = Hero + FVector(0, 0, 140.0); }
	else if (B.Cam == 2) { CamPos = Hero - ToV * 650.0 + FVector(0, 0, 180.0); LookAt = PosCm + FVector(0, 0, 140.0); }
	else                 { CamPos = PosCm - ToV * 500.0 + FVector(0, 0, 300.0); LookAt = PosCm + FVector(0, 0, 100.0); }
	SceneCam->SetActorLocation(CamPos);
	SceneCam->SetActorRotation((LookAt - CamPos).Rotation());
	if (SceneT >= Beats[UE_ARRAY_COUNT(Beats) - 1].End) EndScene();
}

void AWHChaseVillain::EndScene()
{
	UWorld* W = GetWorld();
	UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this);
	// he bolts: a long burst straight away from the hero starts the chase
	State = EState::Flee;
	BurstT = BurstDur + 1.5f;
	BurstCd = BurstEvery;
	FleeHoldT = 6.0f;
	SceneT = 0.f;
	if (FW)
	{
		FW->bChaseScene = false;
		FW->ChaseLine.Empty();
		FW->ChaseStartT = W ? W->GetTimeSeconds() : 0.f;   // the chase clock starts when he bolts, not at spawn
		FW->PushStimulus(EWHCrowdStimulus::SonicBoom, PosCm, 9000.f, 1.f, 3.f, FVector(0, 0, 30000.0));
	}
	if (SceneCam.IsValid())
	{
		if (W)
			if (APlayerController* PC = W->GetFirstPlayerController())
				if (PC->GetPawn()) PC->SetViewTargetWithBlend(PC->GetPawn(), 0.6f);
		SceneCam->Destroy();
		SceneCam = nullptr;
	}
	UE_LOG(LogWebHomage, Display, TEXT("WH_CHASE cutscene end -- he bolts"));
}

void AWHChaseVillain::RestartChase(float Now)
{
	UWHFlightWorldSubsystem* FW = UWHFlightWorldSubsystem::Get(this);
	const FVector Hero = (FW && FW->bHeroValid) ? FW->HeroPosCm : PosCm;
	const double A = FMath::FRand() * 2.0 * PI;
	PosCm = Hero + FVector(FMath::Cos(A) * 28000.0, FMath::Sin(A) * 28000.0, 5500.0);
	VelCm = FVector::ZeroVector;
	State = EState::WaitHere; bHaveWay = false;
	BurstT = BurstCd = TauntCd = FleeHoldT = BreachCd = 0.f;
	SpawnT = Now; CaughtT = -1.f;
	if (Beacon) Beacon->SetVisibility(true);
	if (FW) { FW->bVillainCaught = false; FW->ChaseStartT = Now; FW->VillainTaunt = TEXT("Round two -- come find me!"); FW->VillainTauntUntil = Now + 5.f; }
	SetActorLocation(PosCm);
	UE_LOG(LogWebHomage, Display, TEXT("WH_CHASE restart: villain waiting at (%.0f %.0f %.0f)"), PosCm.X, PosCm.Y, PosCm.Z);
}

void AWHChaseVillain::ApplyTune(const FString& S)
{
	TArray<FString> KVs; S.ParseIntoArray(KVs, TEXT(","), true);
	for (FString KV : KVs)
	{
		FString K, V; if (!KV.Split(TEXT("="), &K, &V)) continue;
		const double D = FCString::Atod(*V);
		if (K == TEXT("RoamSpeed")) RoamSpeed = float(D);
		else if (K == TEXT("FleeSpeed")) FleeSpeed = float(D);
		else if (K == TEXT("BurstSpeed")) BurstSpeed = float(D);
		else if (K == TEXT("BurstDur")) BurstDur = float(D);
		else if (K == TEXT("BurstEvery")) BurstEvery = float(D);
		else if (K == TEXT("FleeRadius")) FleeRadiusM = float(D);
		else if (K == TEXT("CatchRadius")) CatchRadiusM = float(D);
		else if (K == TEXT("MinAlt")) MinAltM = float(D);
		else if (K == TEXT("MaxAlt")) MaxAltM = float(D);
	}
	UE_LOG(LogWebHomage, Display, TEXT("WH_CHASE tune: roam %.0f flee %.0f burst %.0f (%.1f s / %.1f s) radius %.0f catch %.0f"),
		RoamSpeed, FleeSpeed, BurstSpeed, BurstDur, BurstEvery, FleeRadiusM, CatchRadiusM);
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

	// ---- catch: body contact, or E / Triangle held inside CatchRadiusM (only once he is fleeing)
	if (State == EState::Flee || State == EState::Roam)
	{
		const bool bGrab = DistM <= CatchRadiusM && FW->bInteractHeld;
		if (DistM <= TouchRadiusM || bGrab) { OnCaught(Now); return; }
	}
	else if (State == EState::WaitHere && DistM <= TalkRangeM)
	{
		BeginScene(Hero);
		return;
	}

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
	if (State == EState::Caught || State == EState::WaitHere || State == EState::Scene)
	{
		// hover in place: gentle bob, facing the hero when he is near
		const float Now = W->GetTimeSeconds();
		Want = FVector(0, 0, 60.0 * FMath::Sin(Now * 1.4));
		Speed = 0.0;
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

	// ---- world guards: floor below and solids ahead (two cheap line traces). Roaming he steers around; while FLEEING he
	// punches straight through walls (breach proxies fire on the facade) -- owner request 2026-10-25.
	FHitResult Hit;
	const FVector Vn = VelCm.GetSafeNormal();
	const FVector Ahead = (Vn.IsNearlyZero() ? GetActorForwardVector() : Vn) * (Speed * 100.0 * 1.5 + 20000.0);
	BreachCd -= Dt;
	if (W->LineTraceSingleByObjectType(Hit, PosCm, PosCm + Ahead, FCollisionObjectQueryParams(ECC_WorldStatic)))
	{
		const FVector N = Hit.ImpactNormal;
		const bool bWall = FMath::Abs(N.Z) < 0.6;
		if (State == EState::Flee && bWall && BreachCd <= 0.f)
		{
			if (!Breach.IsValid()) { TActorIterator<AWHBreachDirector> It(W); if (It) Breach = *It; }
			if (Breach.IsValid())
			{
				const float Sev = float(FMath::Clamp(FVector2D(VelCm.X, VelCm.Y).Size() / 12000.0, 0.3, 1.0));
				Breach->VillainBreach(Hit.ImpactPoint / 100.0, VelCm.GetSafeNormal(), Sev);
				FW->PushStimulus(EWHCrowdStimulus::Impact, Hit.ImpactPoint, 6000.f, 1.f, 4.f, VelCm);
				UE_LOG(LogWebHomage, Display, TEXT("WH_CHASE villain breach at %s sev %.2f"), *Hit.ImpactPoint.ToString(), Sev);
				BreachCd = 0.9f;
			}
		}
		if (!bWall || State != EState::Flee || BreachCd <= 0.f)
		{
			FVector Deflect = FVector::VectorPlaneProject(Want.GetSafeNormal(), N) + N * 0.8 + FVector(0, 0, 0.5);
			Want = Deflect.GetSafeNormal() * FMath::Max(Speed, 30.0) * 100.0;
		}
		// fleeing + wall + breach just fired: keep the line (he goes through)
	}
	if (W->LineTraceSingleByObjectType(Hit, PosCm, PosCm - FVector(0, 0, 50000.0), FCollisionObjectQueryParams(ECC_WorldStatic))
		&& Hit.Distance < MinAltM * 100.0 + (VelCm.Z < 0.0 ? double(-VelCm.Z) * 1.2 : 0.0))
		Want.Z = FMath::Max(Want.Z, FMath::Abs(Want.Z) + FMath::Max(3000.0, FMath::Abs(VelCm.Z) * 0.8));

	VelCm += (Want - VelCm) * FMath::Min(1.0, 3.0 * Dt);
	if (State == EState::Caught) VelCm *= FMath::Max(0.0, 1.0 - 4.0 * Dt);
	PosCm += VelCm * Dt;
	SetActorLocation(PosCm);

	// hovering / in the scene: face the hero
	if ((State == EState::WaitHere || State == EState::Scene || State == EState::Caught) && FW->bHeroValid)
	{
		const FVector To = Hero - PosCm;
		if (To.SizeSquared2D() > 1.0) SetActorRotation(FRotator(0.0, float(FMath::RadiansToDegrees(FMath::Atan2(To.Y, To.X))), 0.0));
	}

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
