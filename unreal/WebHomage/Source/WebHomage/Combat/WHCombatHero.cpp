// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Combat/WHCombatHero.h"
#include "Combat/WHCombatDirector.h"
#include "Combat/WHCombatAnim.h"
#include "Core/WebHomagePlayerController.h"
#include "Components/InputComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Camera/CameraComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "InputCoreTypes.h"

AWHCombatHero::AWHCombatHero()
{
}

void AWHCombatHero::BeginPlay()
{
	// The traversal pawn's hero-only fill (5000 / 18000 cd point light 1.8 m from the hero, ~1500 lux) is tuned for the Manhattan look
	// (sun 26000-44000 lux). Combat_Street's sun is 10 lux, so the same fill was ~150x the key: auto-exposure adapts to the street and the
	// hero rendered as a blown-out white figure (its glossy-street reflection = the yellow streaks at its feet). No fill in combat;
	// -WHHeroFill=<cd>,<cd> on the command line still overrides (parsed in Super::BeginPlay).
	HeroFillCd = 0.f; HeroFillFlipCd = 0.f;
	Super::BeginPlay();
	// combat animation on top of the traversal animation: same clips / proxy, plus the combat clip stack
	if (USkeletalMeshComponent* M = GetMesh())
	{
		if (M->GetSkeletalMeshAsset() && M->GetAnimInstance() && M->GetAnimInstance()->IsA(UWebTravAnimInstance::StaticClass()))
		{
			M->SetAnimInstanceClass(UWHCombatHeroAnim::StaticClass());
		}
	}
	{ TActorIterator<AWHCombatDirector> It(GetWorld()); if (It) Dir = *It; }
	if (!Dir)
	{
		FActorSpawnParameters P; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		Dir = GetWorld()->SpawnActor<AWHCombatDirector>(AWHCombatDirector::StaticClass(), FTransform::Identity, P);
	}
	if (Dir) Dir->Init(this);
}

FVector AWHCombatHero::HandM(bool bRight) const
{
	const FName B = bRight ? FName(TEXT("hand_R")) : FName(TEXT("hand_L"));
	const USkeletalMeshComponent* M = GetMesh();
	if (M && M->GetSkeletalMeshAsset() && M->GetBoneIndex(B) != INDEX_NONE) return M->GetBoneLocation(B) / 100.0;
	return GetActorLocation() / 100.0 + FVector(0, 0, 0.3);
}

FVector AWHCombatHero::HeadM() const
{
	const USkeletalMeshComponent* M = GetMesh();
	if (M && M->GetSkeletalMeshAsset() && M->GetBoneIndex(TEXT("head")) != INDEX_NONE) return M->GetBoneLocation(TEXT("head")) / 100.0;
	return GetActorLocation() / 100.0 + FVector(0, 0, 0.75);
}

void AWHCombatHero::SetupPlayerInputComponent(UInputComponent* IC)
{
	Super::SetupPlayerInputComponent(IC);
	if (!IC) return;
	IC->BindKey(EKeys::LeftMouseButton, IE_Pressed, this, &AWHCombatHero::KAttackDown);
	IC->BindKey(EKeys::LeftMouseButton, IE_Released, this, &AWHCombatHero::KAttackUp);
	IC->BindKey(EKeys::Gamepad_FaceButton_Left, IE_Pressed, this, &AWHCombatHero::KAttackDown);
	IC->BindKey(EKeys::Gamepad_FaceButton_Left, IE_Released, this, &AWHCombatHero::KAttackUp);
	IC->BindKey(EKeys::F, IE_Pressed, this, &AWHCombatHero::KWeb);
	IC->BindKey(EKeys::E, IE_Pressed, this, &AWHCombatHero::KStrike);
	IC->BindKey(EKeys::MiddleMouseButton, IE_Pressed, this, &AWHCombatHero::KStrike);
	IC->BindKey(EKeys::Q, IE_Pressed, this, &AWHCombatHero::KFinisher);
	IC->BindKey(EKeys::Z, IE_Pressed, this, &AWHCombatHero::KHeal);
	IC->BindKey(EKeys::R, IE_Pressed, this, &AWHCombatHero::KThrow);
	IC->BindKey(EKeys::C, IE_Pressed, this, &AWHCombatHero::KDodge);
	IC->BindKey(EKeys::LeftControl, IE_Pressed, this, &AWHCombatHero::KDodge);
	IC->BindKey(EKeys::Gamepad_FaceButton_Right, IE_Pressed, this, &AWHCombatHero::KDodge);
	// 2026-10-01 owner ("connect a PS5 controller and play"): every combat action on the pad (DualSense via the macOS
	// GameController framework = standard Gamepad_* keys). Square attack (above), Circle dodge (above), Triangle web strike
	// (also traversal zip, like keyboard E), R1 finisher, D-pad left web shooter, D-pad right throw, D-pad down heal.
	IC->BindKey(EKeys::Gamepad_FaceButton_Top, IE_Pressed, this, &AWHCombatHero::KStrike);
	IC->BindKey(EKeys::Gamepad_RightShoulder, IE_Pressed, this, &AWHCombatHero::KFinisher);
	IC->BindKey(EKeys::Gamepad_DPad_Left, IE_Pressed, this, &AWHCombatHero::KWeb);
	IC->BindKey(EKeys::Gamepad_DPad_Right, IE_Pressed, this, &AWHCombatHero::KThrow);
	IC->BindKey(EKeys::Gamepad_DPad_Down, IE_Pressed, this, &AWHCombatHero::KHeal);
}

void AWHCombatHero::KAttackDown() { if (Dir) Dir->LmbDown(); }
void AWHCombatHero::KAttackUp() { if (Dir) Dir->LmbUp(); }
void AWHCombatHero::KWeb() { if (Dir) Dir->KeyPress("web"); }
void AWHCombatHero::KStrike() { if (Dir) Dir->KeyPress("strike"); }
void AWHCombatHero::KFinisher() { if (Dir) Dir->KeyPress("finisher"); }
void AWHCombatHero::KHeal() { if (Dir) Dir->KeyPress("heal"); }
void AWHCombatHero::KThrow() { if (Dir) Dir->KeyPress("throw"); }
void AWHCombatHero::KDodge() { if (Dir) Dir->KeyPress("dodge"); }

AWHCombatGameMode::AWHCombatGameMode()
{
	DefaultPawnClass = AWHCombatHero::StaticClass();
	PlayerControllerClass = AWebHomagePlayerController::StaticClass();
}
