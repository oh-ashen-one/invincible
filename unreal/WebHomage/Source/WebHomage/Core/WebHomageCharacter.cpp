// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Core/WebHomageCharacter.h"
#include "WebHomage.h"

#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/LocalPlayer.h"
#include "Engine/StaticMesh.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "HAL/IConsoleManager.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "UObject/ConstructorHelpers.h"

static TAutoConsoleVariable<int32> CVarWHAutoMove(
	TEXT("wh.AutoMove"),
	0,
	TEXT("1 = hero runs forward, turns slowly and jumps periodically (unattended capture/perf runs)."),
	ECVF_Default);

AWebHomageCharacter::AWebHomageCharacter()
{
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->InitCapsuleSize(42.f, 96.f);

	bUseControllerRotationPitch = false;
	bUseControllerRotationYaw = false;
	bUseControllerRotationRoll = false;

	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->bOrientRotationToMovement = true;
	Move->RotationRate = FRotator(0.f, 540.f, 0.f);
	Move->JumpZVelocity = 700.f;
	Move->AirControl = 0.35f;
	Move->MaxWalkSpeed = 600.f;
	Move->MinAnalogWalkSpeed = 20.f;
	Move->BrakingDecelerationWalking = 2000.f;
	Move->BrakingDecelerationFalling = 1500.f;

	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(RootComponent);
	CameraBoom->TargetArmLength = 400.f;
	CameraBoom->SocketOffset = FVector(0.f, 0.f, 60.f);
	CameraBoom->bUsePawnControlRotation = true;
	CameraBoom->bEnableCameraLag = true;
	CameraBoom->CameraLagSpeed = 12.f;

	FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
	FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	FollowCamera->bUsePawnControlRotation = false;
	FollowCamera->SetFieldOfView(80.f);

	ProxyBody = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ProxyBody"));
	ProxyBody->SetupAttachment(GetCapsuleComponent());
	ProxyBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	// Engine cylinder is 100x100x100 cm centred on origin -> scale to the capsule (84 x 192 cm).
	ProxyBody->SetRelativeScale3D(FVector(0.84f, 0.84f, 1.92f));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (CylinderMesh.Succeeded())
	{
		ProxyBody->SetStaticMesh(CylinderMesh.Object);
	}
}

void AWebHomageCharacter::BeginPlay()
{
	Super::BeginPlay();

	if (FParse::Param(FCommandLine::Get(), TEXT("WHAutoMove")))
	{
		CVarWHAutoMove->Set(1, ECVF_SetByCommandline);
	}
	if (GetMesh() && GetMesh()->GetSkinnedAsset())
	{
		ProxyBody->SetVisibility(false);
	}
	UE_LOG(LogWebHomage, Log, TEXT("WebHomageCharacter BeginPlay at %s"), *GetActorLocation().ToString());
}

void AWebHomageCharacter::EnsureDefaultInput()
{
	if (!MoveAction)
	{
		MoveAction = NewObject<UInputAction>(this, TEXT("IA_Move_Default"));
		MoveAction->ValueType = EInputActionValueType::Axis2D;
	}
	if (!LookAction)
	{
		LookAction = NewObject<UInputAction>(this, TEXT("IA_Look_Default"));
		LookAction->ValueType = EInputActionValueType::Axis2D;
	}
	if (!JumpAction)
	{
		JumpAction = NewObject<UInputAction>(this, TEXT("IA_Jump_Default"));
		JumpAction->ValueType = EInputActionValueType::Boolean;
	}
	if (MappingContext)
	{
		return;
	}

	MappingContext = NewObject<UInputMappingContext>(this, TEXT("IMC_Default"));

	auto MapMoveKey = [this](const FKey& Key, bool bSwizzle, bool bNegate)
	{
		FEnhancedActionKeyMapping& M = MappingContext->MapKey(MoveAction, Key);
		if (bSwizzle)
		{
			UInputModifierSwizzleAxis* Swz = NewObject<UInputModifierSwizzleAxis>(MappingContext);
			Swz->Order = EInputAxisSwizzle::YXZ;
			M.Modifiers.Add(Swz);
		}
		if (bNegate)
		{
			M.Modifiers.Add(NewObject<UInputModifierNegate>(MappingContext));
		}
	};
	// Move: X = right, Y = forward.
	MapMoveKey(EKeys::W, true, false);
	MapMoveKey(EKeys::S, true, true);
	MapMoveKey(EKeys::D, false, false);
	MapMoveKey(EKeys::A, false, true);
	auto StickDeadZone = [this](FEnhancedActionKeyMapping& M)
	{ // radial dead zone first in the modifier chain (worn sticks / DualSense drift)
		UInputModifierDeadZone* DZ = NewObject<UInputModifierDeadZone>(MappingContext);
		DZ->Type = EDeadZoneType::Radial; DZ->LowerThreshold = 0.12f; DZ->UpperThreshold = 1.f;
		M.Modifiers.Insert(DZ, 0);
	};
	StickDeadZone(MappingContext->MapKey(MoveAction, EKeys::Gamepad_Left2D));

	// Look: mouse XY; invert Y so mouse-up looks up.
	{
		FEnhancedActionKeyMapping& M = MappingContext->MapKey(LookAction, EKeys::Mouse2D);
		UInputModifierNegate* NegY = NewObject<UInputModifierNegate>(MappingContext);
		NegY->bX = false; NegY->bY = true; NegY->bZ = false;
		M.Modifiers.Add(NegY);
	}
	{
		FEnhancedActionKeyMapping& M = MappingContext->MapKey(LookAction, EKeys::Gamepad_Right2D);
		StickDeadZone(M);
		UInputModifierNegate* NegY = NewObject<UInputModifierNegate>(MappingContext);
		NegY->bX = false; NegY->bY = true; NegY->bZ = false;
		M.Modifiers.Add(NegY);
		UInputModifierScalar* Scale = NewObject<UInputModifierScalar>(MappingContext);
		Scale->Scalar = FVector(3.f, 3.f, 1.f);
		M.Modifiers.Add(Scale);
	}

	MappingContext->MapKey(JumpAction, EKeys::SpaceBar);
	MappingContext->MapKey(JumpAction, EKeys::Gamepad_FaceButton_Bottom);
}

void AWebHomageCharacter::AddMappingContext()
{
	const APlayerController* PC = Cast<APlayerController>(Controller);
	if (!PC || !MappingContext)
	{
		return;
	}
	if (ULocalPlayer* LP = PC->GetLocalPlayer())
	{
		if (UEnhancedInputLocalPlayerSubsystem* Sub = LP->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
		{
			Sub->AddMappingContext(MappingContext, 0);
		}
	}
}

void AWebHomageCharacter::NotifyControllerChanged()
{
	Super::NotifyControllerChanged();
	EnsureDefaultInput();
	AddMappingContext();
}

void AWebHomageCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	EnsureDefaultInput();
	if (UEnhancedInputComponent* EIC = Cast<UEnhancedInputComponent>(PlayerInputComponent))
	{
		EIC->BindAction(JumpAction, ETriggerEvent::Started, this, &ACharacter::Jump);
		EIC->BindAction(JumpAction, ETriggerEvent::Completed, this, &ACharacter::StopJumping);
		EIC->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AWebHomageCharacter::Move);
		EIC->BindAction(LookAction, ETriggerEvent::Triggered, this, &AWebHomageCharacter::Look);
	}
	else
	{
		UE_LOG(LogWebHomage, Error, TEXT("'%s' needs an EnhancedInputComponent (check DefaultInput.ini)."), *GetNameSafe(this));
	}
}

void AWebHomageCharacter::Move(const FInputActionValue& Value)
{
	const FVector2D Axis = Value.Get<FVector2D>();
	if (!Controller)
	{
		return;
	}
	const FRotator YawRot(0.f, Controller->GetControlRotation().Yaw, 0.f);
	const FRotationMatrix M(YawRot);
	AddMovementInput(M.GetUnitAxis(EAxis::X), Axis.Y);
	AddMovementInput(M.GetUnitAxis(EAxis::Y), Axis.X);
}

void AWebHomageCharacter::Look(const FInputActionValue& Value)
{
	const FVector2D Axis = Value.Get<FVector2D>() * LookSensitivity;
	AddControllerYawInput(Axis.X);
	AddControllerPitchInput(Axis.Y);
}

void AWebHomageCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (CVarWHAutoMove.GetValueOnGameThread() == 0 || !Controller)
	{
		return;
	}
	AddControllerYawInput(6.f * DeltaSeconds); // slow circle (scaled by PC yaw scale)
	const FRotator YawRot(0.f, Controller->GetControlRotation().Yaw, 0.f);
	AddMovementInput(FRotationMatrix(YawRot).GetUnitAxis(EAxis::X), 1.f);
	AutoMoveJumpTimer += DeltaSeconds;
	if (AutoMoveJumpTimer > 3.f)
	{
		AutoMoveJumpTimer = 0.f;
		Jump();
	}
}
