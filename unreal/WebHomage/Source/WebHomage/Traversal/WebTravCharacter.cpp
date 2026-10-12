// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Traversal/WebTravCharacter.h"
#include "Traversal/WebTraversalComponent.h"
#include "Traversal/WebTravScript.h"
#include "Traversal/Anim/WebTravAnimInstance.h"
#include "Traversal/WebTravFlips.h"
#include "HAL/IConsoleManager.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "ReferenceSkeleton.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "TextureResource.h"
#include "Core/WebHomagePlayerController.h"
#include "Characters/WHHeroSuit.h"
#include "CoreGlobals.h"
#include "ImageUtils.h"
#include "Async/Async.h"
#include "HAL/PlatformProcess.h"
#include "HAL/FileManager.h"
#include "Misc/CoreDelegates.h"
#include <atomic>
#include "WebHomage.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Materials/MaterialParameterCollection.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Components/DirectionalLightComponent.h"
#include "UObject/UObjectIterator.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "GenericPlatform/GenericPlatformInputDeviceMapper.h"
#include "Engine/LocalPlayer.h"
#include "Engine/StaticMesh.h"
#include "Core/WHSettings.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UnrealClient.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/SViewport.h"
#include "HAL/PlatformTime.h"
#include "GameFramework/PlayerInput.h"
#include "InputKeyEventArgs.h"
#include "UObject/ConstructorHelpers.h"

// round 11 (owner: mouse look far too fast): MouseRadPerUnit 0.033 -> 0.011 and a sensitivity multiplier console variable; 2026-10-01 -> 0.0025
static TAutoConsoleVariable<float> CVarWHMouseSensitivity(TEXT("wh.MouseSensitivity"), 1.0f,
	TEXT("Mouse look sensitivity multiplier for the traversal hero (1 = default, radians per mouse unit = MouseRadPerUnit x this)."), ECVF_Default);

namespace
{
	constexpr float MaxMouseDeltaPx = 120.f;   // per-frame mouse delta clamp (capture warps / focus changes)
	const FName N_swingLow(TEXT("swingLow")), N_trick(TEXT("trick")), N_tuckFlip(TEXT("tuckFlip")), N_layout(TEXT("layout")),
		N_corkscrew(TEXT("corkscrew")), N_scissor(TEXT("scissor")), N_rise(TEXT("rise")), N_dive(TEXT("dive")), N_zipPull(TEXT("zipPull")),
		N_release(TEXT("release")), N_jumpLaunch(TEXT("jumpLaunch")), N_wallRun(TEXT("wallRun")), N_wallRunSide(TEXT("wallRunSide")),
		N_topOut(TEXT("topOut"));
	const TCHAR* ModeName(EWebTravMode M)
	{
		switch (M)
		{
		case EWebTravMode::Ground: return TEXT("ground");
		case EWebTravMode::Air: return TEXT("air");
		case EWebTravMode::Swing: return TEXT("swing");
		case EWebTravMode::Zip: return TEXT("zip");
		case EWebTravMode::Perch: return TEXT("perch");
		case EWebTravMode::Wall: return TEXT("wall");
		case EWebTravMode::Land: return TEXT("land");
		}
		return TEXT("?");
	}
	double Smooth01(double X) { X = FMath::Clamp(X, 0.0, 1.0); return X * X * (3 - 2 * X); }
}

AWebTravCharacter::AWebTravCharacter()
{
	Traversal = CreateDefaultSubobject<UWebTraversalComponent>(TEXT("Traversal"));

	FigureRoot = CreateDefaultSubobject<USceneComponent>(TEXT("FigureRoot"));
	FigureRoot->SetupAttachment(RootComponent);
	FigureRoot->SetUsingAbsoluteLocation(true);
	FigureRoot->SetUsingAbsoluteRotation(true);
	GetMesh()->SetupAttachment(FigureRoot);
	GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	// the chase camera is driven directly (browser camera.js port), not by the spring arm
	CameraBoom->bDoCollisionTest = false;
	CameraBoom->bEnableCameraLag = false;
	FollowCamera->SetUsingAbsoluteLocation(true);
	FollowCamera->SetUsingAbsoluteRotation(true);
	FollowCamera->PostProcessBlendWeight = 1.f;
	FollowCamera->PostProcessSettings.bOverride_MotionBlurAmount = true;
	FollowCamera->PostProcessSettings.bOverride_MotionBlurMax = true;

	for (FVector& V : ReleaseHandCm) V = FVector::ZeroVector;
}

FWebTravAnim AWebTravCharacter::GetTravAnim() const
{
	return Traversal ? Traversal->Anim : FWebTravAnim();
}

// ------------------------------------------------------------------ input (browser input.js bindings)
void AWebTravCharacter::BuildTravInput()
{
	if (SwingAction)
	{
		return;
	}
	auto MakeAction = [this](const TCHAR* Name, EInputActionValueType Type)
	{
		UInputAction* A = NewObject<UInputAction>(this, Name);
		A->ValueType = Type;
		return A;
	};
	MoveAction = MakeAction(TEXT("IA_TravMove"), EInputActionValueType::Axis2D);
	LookAction = MakeAction(TEXT("IA_TravLook"), EInputActionValueType::Axis2D); // unused (kept non-null for the base class)
	JumpAction = MakeAction(TEXT("IA_TravJump"), EInputActionValueType::Boolean);
	SwingAction = MakeAction(TEXT("IA_TravSwing"), EInputActionValueType::Boolean);
	PadR2Action = MakeAction(TEXT("IA_TravPadR2"), EInputActionValueType::Boolean);
	PadL2Action = MakeAction(TEXT("IA_TravPadL2"), EInputActionValueType::Boolean);
	SprintAction = MakeAction(TEXT("IA_TravSprint"), EInputActionValueType::Boolean);
	ZipAction = MakeAction(TEXT("IA_TravZip"), EInputActionValueType::Boolean);
	DropAction = MakeAction(TEXT("IA_TravDrop"), EInputActionValueType::Boolean);
	QuickAction = MakeAction(TEXT("IA_TravQuick"), EInputActionValueType::Boolean);
	TrickAction = MakeAction(TEXT("IA_TravTrick"), EInputActionValueType::Boolean);
	LookMouseAction = MakeAction(TEXT("IA_TravLookMouse"), EInputActionValueType::Axis2D);
	LookPadAction = MakeAction(TEXT("IA_TravLookPad"), EInputActionValueType::Axis2D);

	MappingContext = NewObject<UInputMappingContext>(this, TEXT("IMC_Trav"));
	UInputMappingContext* IMC = MappingContext;
	auto MapMove = [IMC, this](const FKey& Key, bool bSwizzle, bool bNegate)
	{
		FEnhancedActionKeyMapping& M = IMC->MapKey(MoveAction, Key);
		if (bSwizzle)
		{
			UInputModifierSwizzleAxis* Swz = NewObject<UInputModifierSwizzleAxis>(IMC);
			Swz->Order = EInputAxisSwizzle::YXZ;
			M.Modifiers.Add(Swz);
		}
		if (bNegate) M.Modifiers.Add(NewObject<UInputModifierNegate>(IMC));
	};
	// Move: X = right, Y = forward (WASD + arrows + left stick)
	MapMove(EKeys::W, true, false); MapMove(EKeys::Up, true, false);
	MapMove(EKeys::S, true, true); MapMove(EKeys::Down, true, true);
	MapMove(EKeys::D, false, false); MapMove(EKeys::Right, false, false);
	MapMove(EKeys::A, false, true); MapMove(EKeys::Left, false, true);
	// sticks: radial dead zone (DualSense / any pad through the macOS GameController framework = standard Gamepad_* keys)
	auto DeadZone = [IMC](FEnhancedActionKeyMapping& M)
	{
		UInputModifierDeadZone* DZ = NewObject<UInputModifierDeadZone>(IMC);
		DZ->Type = EDeadZoneType::Radial;
		DZ->LowerThreshold = 0.12f;
		DZ->UpperThreshold = 1.f;
		M.Modifiers.Add(DZ);
	};
	DeadZone(IMC->MapKey(MoveAction, EKeys::Gamepad_Left2D));
	IMC->MapKey(LookMouseAction, EKeys::Mouse2D);
	DeadZone(IMC->MapKey(LookPadAction, EKeys::Gamepad_Right2D));
	// RIGHT MOUSE = web swing (hold); R2 = swing in air / parkour on ground (L2+R2 = zip)
	IMC->MapKey(SwingAction, EKeys::RightMouseButton);
	IMC->MapKey(PadR2Action, EKeys::Gamepad_RightTrigger);
	IMC->MapKey(PadL2Action, EKeys::Gamepad_LeftTrigger);
	// Space = jump (hold = charge) / A
	IMC->MapKey(JumpAction, EKeys::SpaceBar);
	IMC->MapKey(JumpAction, EKeys::Gamepad_FaceButton_Bottom);
	// Shift = wall run + ground parkour
	IMC->MapKey(SprintAction, EKeys::LeftShift);
	IMC->MapKey(SprintAction, EKeys::RightShift);
	IMC->MapKey(SprintAction, EKeys::Gamepad_LeftThumbstick);  // L3 (R2 also sprints on the ground)
	// E / MIDDLE MOUSE = web-zip / point-launch; Y / Triangle
	IMC->MapKey(ZipAction, EKeys::E);
	IMC->MapKey(ZipAction, EKeys::MiddleMouseButton);
	IMC->MapKey(ZipAction, EKeys::Gamepad_FaceButton_Top);
	// C / Ctrl = drop / dive; B / Circle
	IMC->MapKey(DropAction, EKeys::C);
	IMC->MapKey(DropAction, EKeys::LeftControl);
	IMC->MapKey(DropAction, EKeys::Gamepad_FaceButton_Right);
	// Q = quick web boost; L1
	IMC->MapKey(QuickAction, EKeys::Q);
	IMC->MapKey(QuickAction, EKeys::Gamepad_LeftShoulder);
	// F / X (Square) = air trick (round 04: tricks only on input; double-tap Space still works in the air)
	IMC->MapKey(TrickAction, EKeys::F);
	IMC->MapKey(TrickAction, EKeys::Gamepad_FaceButton_Left);
}

void AWebTravCharacter::NotifyControllerChanged()
{
	BuildTravInput(); // before the base, so its EnsureDefaultInput keeps our mapping context
	Super::NotifyControllerChanged();
}

void AWebTravCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	BuildTravInput();
	UEnhancedInputComponent* EIC = Cast<UEnhancedInputComponent>(PlayerInputComponent);
	if (!EIC)
	{
		UE_LOG(LogWebHomage, Error, TEXT("AWebTravCharacter needs an EnhancedInputComponent"));
		return;
	}
	auto BindHeld = [this, EIC](UInputAction* A, bool AWebTravCharacter::*Flag)
	{
		EIC->BindActionValueLambda(A, ETriggerEvent::Started, [this, Flag](const FInputActionValue&) { this->*Flag = true; });
		EIC->BindActionValueLambda(A, ETriggerEvent::Triggered, [this, Flag](const FInputActionValue&) { this->*Flag = true; });
		EIC->BindActionValueLambda(A, ETriggerEvent::Completed, [this, Flag](const FInputActionValue&) { this->*Flag = false; });
		EIC->BindActionValueLambda(A, ETriggerEvent::Canceled, [this, Flag](const FInputActionValue&) { this->*Flag = false; });
	};
	BindHeld(SwingAction, &AWebTravCharacter::bRMB);
	BindHeld(PadR2Action, &AWebTravCharacter::bR2);
	BindHeld(PadL2Action, &AWebTravCharacter::bL2);
	BindHeld(SprintAction, &AWebTravCharacter::bShift);
	BindHeld(ZipAction, &AWebTravCharacter::bZipKey);
	BindHeld(DropAction, &AWebTravCharacter::bDropKey);
	BindHeld(QuickAction, &AWebTravCharacter::bQuickKey);
	BindHeld(JumpAction, &AWebTravCharacter::bJumpKey);
	BindHeld(TrickAction, &AWebTravCharacter::bTrickKey);
	EIC->BindActionValueLambda(MoveAction, ETriggerEvent::Triggered, [this](const FInputActionValue& V) { LiveMove = V.Get<FVector2D>(); });
	EIC->BindActionValueLambda(MoveAction, ETriggerEvent::Completed, [this](const FInputActionValue&) { LiveMove = FVector2D::ZeroVector; });
	EIC->BindActionValueLambda(LookMouseAction, ETriggerEvent::Triggered, [this](const FInputActionValue& V) { MouseAccum += V.Get<FVector2D>(); });
	EIC->BindActionValueLambda(LookPadAction, ETriggerEvent::Triggered, [this](const FInputActionValue& V) { PadLook = V.Get<FVector2D>(); });
	EIC->BindActionValueLambda(LookPadAction, ETriggerEvent::Completed, [this](const FInputActionValue&) { PadLook = FVector2D::ZeroVector; });
}

// ------------------------------------------------------------------ setup
UStaticMeshComponent* AWebTravCharacter::AddPart(USceneComponent* Parent, const TCHAR* Name, UStaticMesh* Mesh, const FVector& Loc, const FVector& Scale,
	UMaterialInstanceDynamic* Mat)
{
	UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this, Name);
	C->SetupAttachment(Parent);
	C->SetStaticMesh(Mesh);
	C->SetRelativeLocation(Loc);
	C->SetRelativeScale3D(Scale);
	C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	C->SetGenerateOverlapEvents(false);
	if (Mat) C->SetMaterial(0, Mat);
	C->RegisterComponent();
	FigureParts.Add(C);
	return C;
}

void AWebTravCharacter::BuildFigure()
{
	UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	UStaticMesh* Sphere = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	UStaticMesh* Cyl = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Traversal/Materials/M_TravColor.M_TravColor"));
	if (!Base) Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	auto Mat = [this, Base](const FLinearColor& C, float Emissive)
	{
		UMaterialInstanceDynamic* M = UMaterialInstanceDynamic::Create(Base, this);
		M->SetVectorParameterValue(TEXT("Color"), C);
		M->SetScalarParameterValue(TEXT("Emissive"), Emissive);
		return M;
	};
	UMaterialInstanceDynamic* Red = Mat(FLinearColor(0.55f, 0.02f, 0.03f), 0.f);
	UMaterialInstanceDynamic* Blue = Mat(FLinearColor(0.02f, 0.05f, 0.30f), 0.f);
	UMaterialInstanceDynamic* White = Mat(FLinearColor(0.9f, 0.9f, 0.95f), 0.6f);
	WebMat = Mat(FLinearColor(0.09f, 0.09f, 0.11f), 0.0f); // round 09: dark line (r08 pale grey vanished on the pale facades; r07 emissive bloomed)

	// placeholder hero, 1.8 m: X forward, Y right, Z up, origin at the feet
	AddPart(FigureRoot, TEXT("Fig_Pelvis"), Cube, FVector(0, 0, 95), FVector(0.22, 0.32, 0.18), Blue);
	AddPart(FigureRoot, TEXT("Fig_Torso"), Cube, FVector(0, 0, 128), FVector(0.24, 0.40, 0.48), Red);
	AddPart(FigureRoot, TEXT("Fig_Head"), Sphere, FVector(0, 0, 166), FVector(0.24, 0.23, 0.26), Red);
	AddPart(FigureRoot, TEXT("Fig_EyeL"), Sphere, FVector(10, -5, 168), FVector(0.05, 0.07, 0.05), White);
	AddPart(FigureRoot, TEXT("Fig_EyeR"), Sphere, FVector(10, 5, 168), FVector(0.05, 0.07, 0.05), White);
	for (int32 S = 0; S < 2; ++S)
	{
		const double Side = S == 0 ? -1.0 : 1.0;
		USceneComponent* AP = NewObject<USceneComponent>(this, S == 0 ? TEXT("Fig_ArmL") : TEXT("Fig_ArmR"));
		AP->SetupAttachment(FigureRoot);
		AP->SetRelativeLocation(FVector(0, 23 * Side, 146));
		AP->RegisterComponent();
		ArmPivot[S] = AP;
		AddPart(AP, S == 0 ? TEXT("Fig_ArmL_M") : TEXT("Fig_ArmR_M"), Cyl, FVector(0, 0, -29), FVector(0.09, 0.09, 0.58), Red);
		AddPart(AP, S == 0 ? TEXT("Fig_HandL") : TEXT("Fig_HandR"), Sphere, FVector(0, 0, -60), FVector(0.1, 0.1, 0.1), Red);
		USceneComponent* LP = NewObject<USceneComponent>(this, S == 0 ? TEXT("Fig_LegL") : TEXT("Fig_LegR"));
		LP->SetupAttachment(FigureRoot);
		LP->SetRelativeLocation(FVector(0, 10 * Side, 88));
		LP->RegisterComponent();
		LegPivot[S] = LP;
		AddPart(LP, S == 0 ? TEXT("Fig_LegL_M") : TEXT("Fig_LegR_M"), Cyl, FVector(0, 0, -44), FVector(0.13, 0.13, 0.88), Blue);
	}
	// web strands: chains of thin cylinders (absolute transforms), 2 strands
	for (int32 I = 0; I < 2 * SEGS_PER_STRAND; ++I)
	{
		UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this, *FString::Printf(TEXT("WebSeg_%02d"), I));
		C->SetupAttachment(RootComponent);
		C->SetUsingAbsoluteLocation(true);
		C->SetUsingAbsoluteRotation(true);
		C->SetUsingAbsoluteScale(true);
		C->SetStaticMesh(Cyl);
		C->SetMaterial(0, WebMat);
		C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		C->SetCastShadow(false);
		C->SetVisibility(false);
		C->SetTranslucentSortPriority(10); // round 25: the two-tone strand is translucent (it reads the scene colour behind it)
		C->RegisterComponent();
		WebSegs.Add(C);
	}
	WebSegDpg.Init(-1, 2 * SEGS_PER_STRAND);
	// round 25: unlit two-tone strand (see RopeLook in WebTraversalComponent.h); built by Scripts/build_traversal.py (traversal_web_material.py)
	if (UMaterialInterface* WebBase = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Traversal/Materials/M_TravWeb.M_TravWeb")))
	{
		// final round 13: one MID per strand -- the material's background taps (BgUV0 / BgUV1) are per-strand vector params
		for (int32 SI = 0; SI < 2; ++SI) WebMatTwoTone[SI] = UMaterialInstanceDynamic::Create(WebBase, this);
	}
	else UE_LOG(LogTemp, Warning, TEXT("WebTrav: /Game/Traversal/Materials/M_TravWeb missing -- web strands keep the r24 dark line"));
	WebLookNow = 0;
}

bool AWebTravCharacter::SetupHeroMesh()
{
	// round 04: the real hero; round 10: paths are properties (HeroMeshPath / HeroLensMeshPath / HeroClipRoot / HeroClipPrefix)
	{
		FString V;
		if (FParse::Value(FCommandLine::Get(), TEXT("-WHHeroMesh="), V)) HeroMeshPath = V;
		if (FParse::Value(FCommandLine::Get(), TEXT("-WHHeroLens="), V)) HeroLensMeshPath = V.Equals(TEXT("none"), ESearchCase::IgnoreCase) ? FString() : V;
		if (FParse::Value(FCommandLine::Get(), TEXT("-WHHeroClips="), V)) HeroClipRoot = V;
		if (FParse::Value(FCommandLine::Get(), TEXT("-WHHeroClipPrefix="), V)) HeroClipPrefix = V;
	}
	USkeletalMesh* Body = HeroMeshPath.IsEmpty() ? nullptr : LoadObject<USkeletalMesh>(nullptr, *HeroMeshPath);
	if (!Body)
	{
		UE_LOG(LogWebHomage, Warning, TEXT("WH_TRAV hero mesh missing (%s): placeholder figure stays"), *HeroMeshPath);
		return false;
	}
	UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV hero: mesh %s, lens %s, clips %s/%s<clip>"), *HeroMeshPath,
		HeroLensMeshPath.IsEmpty() ? TEXT("(none)") : *HeroLensMeshPath, *HeroClipRoot, *HeroClipPrefix);
	UWebTravAnimInstance::ClipRoot = HeroClipRoot;
	UWebTravAnimInstance::ClipPrefix = HeroClipPrefix;
	USkeletalMeshComponent* M = GetMesh();
	M->SetAnimationMode(EAnimationMode::AnimationBlueprint);
	M->SetAnimInstanceClass(UWebTravAnimInstance::StaticClass());
	M->SetSkeletalMesh(Body);
	// [integration, traversal r18 merge] the HeroDev proxy (public/assets/spiderman.glb) carries the upstream browser suit texture, a copy
	// of a studio suit layout/emblem. The playable hero must wear P2's ORIGINAL round-08 suit (Tessera, MI_Hero_Suit), which is authored on
	// the same body UV atlas (tools/ue_char/hero_suit_r8.py evaluates the same spiderman.glb body). Override the 'SpiderSuit' slot whenever
	// that material exists (build_characters.py ran); traversal keeps its own skeleton, clips and flip shapes untouched.
	// round 26 (director hard line: no capture and no default launch may show the proxy's licensed-looking suit): the first entry of P2's
	// suit set (/Game/Characters/Hero/Suits/DA_HeroSuits, characters r14: Tessera) wins, then MI_Hero_Suit; when neither exists the slot
	// gets the engine's plain default material instead of the proxy texture. UWHHeroSuitSubsystem then applies the chosen / saved suit.
	{
		static const TCHAR* OriginalSuit = TEXT("/Game/Characters/Hero/Materials/MI_Hero_Suit.MI_Hero_Suit");
		const int32 Slot = M->GetMaterialIndex(FName(TEXT("SpiderSuit")));
		UMaterialInterface* Suit = nullptr;
		const TCHAR* Src = TEXT("none");
		if (Slot != INDEX_NONE)
		{
			if (const UWHHeroSuitSet* Set = LoadObject<UWHHeroSuitSet>(nullptr, UWHHeroSuitSubsystem::SetPath))
				for (const FWHHeroSuitEntry& E : Set->Suits) if (E.Material) { Suit = E.Material; Src = TEXT("DA_HeroSuits entry"); break; }
			if (!Suit) { Suit = LoadObject<UMaterialInterface>(nullptr, OriginalSuit); Src = TEXT("MI_Hero_Suit"); }
			if (!Suit)
			{
				Suit = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial")); Src = TEXT("NEUTRAL engine default (no original suit built)");
				UE_LOG(LogWebHomage, Warning, TEXT("WH_TRAV hero suit: no original suit (DA_HeroSuits / %s) - run build_characters.py; neutral material, never the proxy suit"), OriginalSuit);
			}
			if (Suit) M->SetMaterial(Slot, Suit);
		}
		UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV hero suit: %s %s"), Slot == INDEX_NONE ? TEXT("mesh has no SpiderSuit slot, unchanged") : Src, Suit ? *Suit->GetName() : TEXT("-"));
	}
	M->SetCastShadow(true);
	// round 06: the suit rendered white / unshaded for the first frames of a capture (textures streaming in late):
	// keep the hero's textures resident at full mip from the first frame
	M->SetTextureForceResidentFlag(true);
	M->bPerBoneMotionBlur = false; // round 09: limbs never smear (the city blurs, the hero stays crisp)
	M->PrestreamTextures(30.f, true);
	M->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
	M->PrimaryComponentTick.AddPrerequisite(this, PrimaryActorTick);
	// the asset's own forward / up axes (from its reference pose) -> figure root +X forward, +Z up
	const FReferenceSkeleton& RS = Body->GetRefSkeleton();
	auto RefCS = [&RS](const TCHAR* Name)
	{
		int32 I = RS.FindBoneIndex(FName(Name));
		FTransform T = FTransform::Identity;
		while (I != INDEX_NONE) { T = T * RS.GetRefBonePose()[I]; I = RS.GetParentIndex(I); }
		return T.GetLocation();
	};
	FVector Fwd = RefCS(TEXT("toe_L")) - RefCS(TEXT("foot_L")) + RefCS(TEXT("toe_R")) - RefCS(TEXT("foot_R"));
	const FVector Up = (RefCS(TEXT("head")) - RefCS(TEXT("hips"))).GetSafeNormal();
	Fwd = (Fwd - Up * FVector::DotProduct(Fwd, Up)).GetSafeNormal();
	const FQuat Basis = FRotationMatrix::MakeFromXZ(Fwd, Up).ToQuat();
	const FQuat Corr = Basis.Inverse();
	const FVector LeftDir = Corr.RotateVector(RefCS(TEXT("hand_L")) - RefCS(TEXT("hand_R")));
	{ // round 01: the finger axis of each hand in its bone space (reference pose: hand -> middle1), the strand origin is 7 cm along it (the palm)
		auto RefT = [&RS](const TCHAR* Name)
		{
			int32 I = RS.FindBoneIndex(FName(Name));
			FTransform T = FTransform::Identity;
			while (I != INDEX_NONE) { T = T * RS.GetRefBonePose()[I]; I = RS.GetParentIndex(I); }
			return T;
		};
		bPalmOk = true;
		for (int32 Sd = 0; Sd < 2; ++Sd)
		{
			const FTransform H = RefT(Sd ? TEXT("hand_R") : TEXT("hand_L"));
			const FVector Mid = RefCS(Sd ? TEXT("middle1_R") : TEXT("middle1_L"));
			PalmLocal[Sd] = H.InverseTransformVectorNoScale(Mid - H.GetLocation()).GetSafeNormal();
			if (PalmLocal[Sd].IsNearlyZero()) bPalmOk = false;
		}
		UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV palm axis (hand bone space): L (%.2f %.2f %.2f) R (%.2f %.2f %.2f), offset %.0f cm"), PalmLocal[0].X, PalmLocal[0].Y, PalmLocal[0].Z, PalmLocal[1].X, PalmLocal[1].Y, PalmLocal[1].Z, PalmOffsetCm);
	}
	const double FootZ = FMath::Min(Corr.RotateVector(RefCS(TEXT("toe_L"))).Z, Corr.RotateVector(RefCS(TEXT("foot_L"))).Z);
	const double HeadZ = Corr.RotateVector(RefCS(TEXT("head"))).Z;
	M->SetRelativeRotation(Corr);
	M->SetRelativeLocation(FVector(0, 0, 0));
	UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV hero mesh: fwd(asset)=%s up(asset)=%s left-after-corr=%s footZ=%.1f headZ=%.1f cm"),
		*Fwd.ToString(), *Up.ToString(), *LeftDir.GetSafeNormal().ToString(), FootZ, HeadZ);
	if (USkeletalMesh* Lens = HeroLensMeshPath.IsEmpty() ? nullptr : LoadObject<USkeletalMesh>(nullptr, *HeroLensMeshPath))
	{
		LensMesh = NewObject<USkeletalMeshComponent>(this, TEXT("HeroLenses"));
		LensMesh->SetupAttachment(M);
		LensMesh->SetSkeletalMesh(Lens);
		LensMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		LensMesh->RegisterComponent();
		LensMesh->SetLeaderPoseComponent(M);
		LensMesh->SetTextureForceResidentFlag(true);
	}
	for (UStaticMeshComponent* C : FigureParts) { if (C) C->SetVisibility(false); }
	for (USceneComponent* P : ArmPivot) { if (P) P->SetVisibility(false, true); }
	for (USceneComponent* P : LegPivot) { if (P) P->SetVisibility(false, true); }
	return true;
}

// round 26 (shared machine: 1080p movie frames at 0.25-0.9 /s; `sample` of the game thread: 77 % of it inside the synchronous PNG deflate of
// -dumpmovie, 20 % in the read-back flush): -WHMovieAsync takes the movie frames through UGameViewportClient::OnScreenshotCaptured (the engine
// then skips its own PNG write) and writes the SAME lossless PNG (zlib level 3, the engine default) on pool threads, in frame order by name
// (Saved/Screenshots/<platform>/MovieFrameNNNNN.png, numbered from 0 like -dumpmovie). At most 24 frames in flight (the game thread waits);
// EndPlay waits until every frame is on disk.
namespace WHMovieAsync
{
	std::atomic<int32> InFlight{0};
	int32 Next = 0;
	FDelegateHandle Handle;
	void OnShot(int32 W, int32 H, const TArray<FColor>& Bitmap)
	{
		if (!GIsDumpingMovie) return;
		while (InFlight.load() >= 24) FPlatformProcess::Sleep(0.002f);
		const FString Path = FPaths::ScreenShotDir() / FString::Printf(TEXT("MovieFrame%05d.png"), Next++);
		TArray<FColor> Copy = Bitmap;
		++InFlight;
		Async(EAsyncExecution::ThreadPool, [Path, W, H, Copy = MoveTemp(Copy)]()
		{
			FImageView Img(Copy.GetData(), W, H);
			if (!FImageUtils::SaveImageByExtension(*Path, Img, 0)) UE_LOG(LogWebHomage, Warning, TEXT("WH_TRAV movie async: write failed %s"), *Path);
			--InFlight;
		});
	}
	void Drain()
	{
		const double T0 = FPlatformTime::Seconds();
		while (InFlight.load() > 0 && FPlatformTime::Seconds() - T0 < 300.0) FPlatformProcess::Sleep(0.01f);
		UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV movie async: %d frames written, %d still in flight after %.1f s"), Next, InFlight.load(), FPlatformTime::Seconds() - T0);
	}
	void Arm()
	{
		if (Handle.IsValid()) return;
		IFileManager::Get().MakeDirectory(*FPaths::ScreenShotDir(), true);
		Handle = UGameViewportClient::OnScreenshotCaptured().AddStatic(&OnShot);
		FCoreDelegates::OnEnginePreExit.AddStatic(&Drain);   // the quit path may skip EndPlay: every frame on disk before the process ends
		UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV movie async PNG writer armed (%s)"), *FPaths::ScreenShotDir());
	}
}

void AWebTravCharacter::BeginPlay()
{
	Super::BeginPlay();
	UWebTravScript* TuneScript = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWebTravScript>() : nullptr;
	{ // round 07: -WHTravTune=Name=Value,... sets float tuning properties of the traversal component (tuning scans)
	  // round 17: the script's own "tune" string first, then the command line (which wins)
		FString CmdTune, Tune = TuneScript && TuneScript->IsActive() ? TuneScript->TuneString() : FString();
		if (FParse::Value(FCommandLine::Get(), TEXT("-WHTravTune="), CmdTune, false)) Tune = Tune.IsEmpty() ? CmdTune : Tune + TEXT(",") + CmdTune;
		if (!Tune.IsEmpty())
		{
			TArray<FString> Parts;
			Tune.ParseIntoArray(Parts, TEXT(","));
			for (const FString& Pr : Parts)
			{
				FString K, V;
				if (!Pr.Split(TEXT("="), &K, &V)) continue;
				if (FFloatProperty* FP = FindFProperty<FFloatProperty>(Traversal->GetClass(), FName(*K)))
				{
					FP->SetPropertyValue_InContainer(Traversal, FCString::Atof(*V));
					UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV tune %s = %s"), *K, *V);
				}
				else UE_LOG(LogWebHomage, Warning, TEXT("WH_TRAV tune: no float property %s"), *K);
			}
		}
	}
	{ // round 15: -WHCamTune=Name=Value,... sets the camera's named tuning doubles (FWebTravCamera::SetTune)
		FString CmdTune, Tune = TuneScript && TuneScript->IsActive() ? TuneScript->CamTuneString() : FString();
		if (FParse::Value(FCommandLine::Get(), TEXT("-WHCamTune="), CmdTune, false)) Tune = Tune.IsEmpty() ? CmdTune : Tune + TEXT(",") + CmdTune;
		if (!Tune.IsEmpty())
		{
			TArray<FString> Parts;
			Tune.ParseIntoArray(Parts, TEXT(","));
			for (const FString& Pr : Parts)
			{
				FString K, V;
				if (Pr.Split(TEXT("="), &K, &V) && Cam.SetTune(K, FCString::Atod(*V))) { UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV cam tune %s = %s"), *K, *V); }
				else { UE_LOG(LogWebHomage, Warning, TEXT("WH_TRAV cam tune: unknown %s"), *Pr); }
			}
		}
	}
	bLatchInput = FParse::Param(FCommandLine::Get(), TEXT("WHTravLatchInput"));
	if (FParse::Value(FCommandLine::Get(), TEXT("-WHTravInputTest="), InputTest) && !InputTest.IsEmpty())
	{
		bInputTestMouse = InputTest.Contains(TEXT("mouse"));
		FParse::Value(FCommandLine::Get(), TEXT("-WHMouseTestPx="), MouseTestPx);
		InputTestTicker = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateUObject(this, &AWebTravCharacter::InputTestTick));
		UE_LOG(LogWebHomage, Display, TEXT("WH_INPUTTEST %s armed (%s input)"), *InputTest, bLatchInput ? TEXT("round-18 event-latched") : TEXT("round-19 polled"));
	}
	float Pre = 0.f;
	if (FParse::Value(FCommandLine::Get(), TEXT("-WHTravPreroll="), Pre) && Pre > 0.f) { PrerollLeft = Pre; bHadPreroll = true; }
	if (FParse::Param(FCommandLine::Get(), TEXT("WHMovieAsync")) && GIsDumpingMovie != 0) WHMovieAsync::Arm(); // round 26
	{ // round 26: split movie capture
		double MF = 0.0;
		if (FParse::Value(FCommandLine::Get(), TEXT("-WHMovieFrom="), MF) && MF > 0.0 && GIsDumpingMovie != 0)
		{
			MovieFrom = MF; MovieDumpSaved = GIsDumpingMovie; GIsDumpingMovie = 0; bMovieGated = true;
			UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV movie dump gated until sequence t=%.4f"), MovieFrom);
		}
	}
	if (ProxyBody) ProxyBody->SetVisibility(false);
	GetCharacterMovement()->SetMovementMode(MOVE_None);
	GetCharacterMovement()->SetComponentTickEnabled(false);
	BuildFigure();
	bHeroMesh = SetupHeroMesh();
	{ // round 01: strands are drawn once the pose of this frame is final (TG_PostUpdateWork, after the hero mesh tick); the telemetry row is completed at the end of the frame
		PostTickFn.Target = this; PostTickFn.Phase = 0; PostTickFn.bCanEverTick = true; PostTickFn.bStartWithTickEnabled = true; PostTickFn.TickGroup = TG_PostUpdateWork;
		PostTickFn.RegisterTickFunction(GetLevel());
		if (bHeroMesh && GetMesh()) PostTickFn.AddPrerequisite(GetMesh(), GetMesh()->PrimaryComponentTick);
		EndTickFn.Target = this; EndTickFn.Phase = 1; EndTickFn.bCanEverTick = true; EndTickFn.bStartWithTickEnabled = true; EndTickFn.TickGroup = TG_LastDemotable;
		EndTickFn.RegisterTickFunction(GetLevel());
		EndTickFn.AddPrerequisite(this, PostTickFn);
		bPostTickRegistered = true;
	}
	{ // round 13: hero-only fill light (see HeroFillCd)
		FString FillArg;
		if (FParse::Value(FCommandLine::Get(), TEXT("-WHHeroFill="), FillArg))
		{
			FString A, B;
			if (FillArg.Split(TEXT(","), &A, &B)) { HeroFillCd = FCString::Atof(*A); HeroFillFlipCd = FCString::Atof(*B); }
			else HeroFillCd = HeroFillFlipCd = FCString::Atof(*FillArg);
		}
		if (bHeroMesh && (HeroFillCd > 0.f || HeroFillFlipCd > 0.f))
		{
			HeroFill = NewObject<UPointLightComponent>(this, TEXT("HeroFill"));
			HeroFill->SetupAttachment(RootComponent);
			HeroFill->SetUsingAbsoluteLocation(true);
			HeroFill->SetMobility(EComponentMobility::Movable);
			HeroFill->RegisterComponent();
			HeroFill->SetIntensityUnits(ELightUnits::Candelas);
			HeroFill->SetIntensity(HeroFillCd);
			HeroFill->SetLightColor(FLinearColor(1.0f, 0.93f, 0.84f));
			HeroFill->SetCastShadows(false);
			HeroFill->SetVolumetricScatteringIntensity(0.f);
			HeroFill->SetIndirectLightingIntensity(0.f);
			HeroFill->SetAttenuationRadius(600.f);
			HeroFill->SourceRadius = 20.f;
			HeroFill->SetLightingChannels(false, true, false); // channel 1 only
			GetMesh()->SetLightingChannels(true, true, false);
			if (LensMesh) LensMesh->SetLightingChannels(true, true, false);
			UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV hero fill light: %.0f cd (flip %.0f cd), %.1f m toward the camera"), HeroFillCd, HeroFillFlipCd, HeroFillDist);
		}
	}

	const UWebTravScript* Script = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWebTravScript>() : nullptr;
	if (Script) Traversal->RandomSeed = Script->Seed();
	Traversal->Cam = &Cam;
	Traversal->InitWorld(GetWorld(), this);

	// capsule centre (96 cm over the feet) -> traversal body centre (0.95 m over the feet)
	FVector PosM = (GetActorLocation() - FVector(0, 0, GetCapsuleComponent()->GetScaledCapsuleHalfHeight())) / 100.0 + FVector(0, 0, UWebTraversalComponent::H);
	double YawDeg = GetActorRotation().Yaw;
	double CamPitch = 0.14;
	if (Script && Script->IsActive() && Script->HasSpawn())
	{
		PosM = Script->SpawnPosM(); YawDeg = Script->SpawnYawDeg(); CamPitch = Script->SpawnCamPitch();
	}
	Traversal->Teleport(PosM, FMath::DegreesToRadians(YawDeg));
	if (Script && Script->IsActive()) Traversal->SetVelocityM(Script->SpawnVelM());
	Cam.Reset(Traversal->PosM(), FMath::DegreesToRadians(YawDeg));
	Cam.Pitch = CamPitch;
	// [F perf local patch, P3 to adopt] the two 480x270 scene captures below re-render the scene every frame (the full-scene depth
	// capture = a second Nanite/VSM/prepass pass). They only feed telemetry columns (hero mask / wall_frac / hero_occl), so they are
	// off unless -WHTravMask is passed (C's route/anim checks pass it; perf runs do not).
	if (bHeroMesh && Script && Script->WantsTelemetry() && FParse::Param(FCommandLine::Get(), TEXT("WHTravMask")))
	{ // pixel mask of the hero for telemetry: scene depth of the hero meshes only, 480x270, from the view camera
		MaskRT = NewObject<UTextureRenderTarget2D>(this, TEXT("HeroMaskRT"));
		MaskRT->RenderTargetFormat = ETextureRenderTargetFormat::RTF_RGBA16f;
		MaskRT->ClearColor = FLinearColor(65000.f, 65000.f, 65000.f, 1.f);
		MaskRT->InitAutoFormat(480, 270);
		MaskRT->UpdateResourceImmediate(true);
		MaskCapture = NewObject<USceneCaptureComponent2D>(this, TEXT("HeroMaskCapture"));
		MaskCapture->SetupAttachment(RootComponent);
		MaskCapture->SetUsingAbsoluteLocation(true);
		MaskCapture->SetUsingAbsoluteRotation(true);
		MaskCapture->CaptureSource = ESceneCaptureSource::SCS_SceneDepth;
		MaskCapture->PrimitiveRenderMode = ESceneCapturePrimitiveRenderMode::PRM_UseShowOnlyList;
		MaskCapture->ShowOnlyComponents.Add(GetMesh());
		if (LensMesh) MaskCapture->ShowOnlyComponents.Add(LensMesh);
		MaskCapture->bCaptureEveryFrame = true;
		MaskCapture->bCaptureOnMovement = false;
		MaskCapture->TextureTarget = MaskRT;
		MaskCapture->RegisterComponent();
		// round 08: the whole scene's depth from the same camera (web strands hidden) for wall_frac / hero_occl
		SceneRT = NewObject<UTextureRenderTarget2D>(this, TEXT("SceneDepthRT"));
		SceneRT->RenderTargetFormat = ETextureRenderTargetFormat::RTF_RGBA16f;
		SceneRT->ClearColor = FLinearColor(65000.f, 65000.f, 65000.f, 1.f);
		SceneRT->InitAutoFormat(480, 270);
		SceneRT->UpdateResourceImmediate(true);
		SceneCapture = NewObject<USceneCaptureComponent2D>(this, TEXT("SceneDepthCapture"));
		SceneCapture->SetupAttachment(RootComponent);
		SceneCapture->SetUsingAbsoluteLocation(true);
		SceneCapture->SetUsingAbsoluteRotation(true);
		SceneCapture->CaptureSource = ESceneCaptureSource::SCS_SceneDepth;
		SceneCapture->PrimitiveRenderMode = ESceneCapturePrimitiveRenderMode::PRM_RenderScenePrimitives;
		for (UStaticMeshComponent* W : WebSegs) { if (W) SceneCapture->HiddenComponents.Add(W); }
		SceneCapture->bCaptureEveryFrame = true;
		SceneCapture->bCaptureOnMovement = false;
		SceneCapture->TextureTarget = SceneRT;
		SceneCapture->RegisterComponent();
	}
	UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV ready: %d building boxes, spawn %s m yaw %.1f"), Traversal->BuildingCount(), *PosM.ToString(), YawDeg);
}

// ------------------------------------------------------------------ per frame
void AWebTravCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const double Dt = FMath::Clamp(double(DeltaSeconds), 1e-4, 0.1);
	// round 12 (planning tool): -WHTravHeightmap=<csv> writes the traversal world's height field once (5 m grid, down-rays from
	// 600 m; x, y, top z, ground flag) — the roofs the sky-launch solver and the web search actually see (the exported
	// collision.json misses geometry the lit map has)
	{
		static bool bHmDone = false;
		FString HmPath;
		if (!bHmDone && Traversal && FParse::Value(FCommandLine::Get(), TEXT("-WHTravHeightmap="), HmPath))
		{
			bHmDone = true;
			FString Out = TEXT("x,y,z,ground,src\n");
			double HX0 = -320.0, HY0 = -620.0, HX1 = 680.0, HY1 = 380.0;
			FString Ext;
			if (FParse::Value(FCommandLine::Get(), TEXT("-WHTravHmExt="), Ext))
			{
				TArray<FString> E; Ext.ParseIntoArray(E, TEXT(","));
				if (E.Num() == 4) { HX0 = FCString::Atod(*E[0]); HY0 = FCString::Atod(*E[1]); HX1 = FCString::Atod(*E[2]); HY1 = FCString::Atod(*E[3]); }
			}
			for (double Y = HY0; Y <= HY1; Y += 5.0)
				for (double X = HX0; X <= HX1; X += 5.0)
				{
					// round 19: the traversal's own floor (GroundHeight: box / ground filter applied) + its source (floor audit)
					const double Z = Traversal->TravWorld.GroundHeight(X, Y, 600.0);
					if (Z > -999.0)
						Out += FString::Printf(TEXT("%.0f,%.0f,%.1f,%d,%d\n"), X, Y, Z, Traversal->TravWorld.LastGroundSrc == 2 ? 1 : 0, Traversal->TravWorld.LastGroundSrc);
				}
			FFileHelper::SaveStringToFile(Out, *HmPath);
			UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV heightmap written: %s"), *HmPath);
		}
	}
	{
		FString DaPath;
		if (!bDepthAuditDone && Traversal && FParse::Value(FCommandLine::Get(), TEXT("-WHTravDepthAudit="), DaPath) && ++DepthAuditFrames > 90)
		{
			bDepthAuditDone = true;
			RunDepthAudit(DaPath);
		}
	}
	// round 06: capture pre-roll (-WHTravPreroll=<s>): the start pose is rendered for a while (camera, exposure, Lumen settle)
	// with the traversal frozen and no input / telemetry; capture_round.sh trims these frames. Auto-exposure lag at the start
	// is what rendered the suit white / blown out in the first ~0.6 s of earlier captures.
	const bool bPre = PrerollLeft > 0.0;
	if (bPre) PrerollLeft -= Dt;
	else if (!bTravStarted)
	{
		bTravStarted = true; TravTime = 0.0;
		if (bHadPreroll)
		{
			if (UWebTravAnimInstance* AI = Cast<UWebTravAnimInstance>(GetMesh()->GetAnimInstance())) AI->ResetForSequenceStart();
			UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV preroll done: %d frames"), PrerollFrames);
		}
	}
	else TravTime += Dt;
	if (bPre) ++PrerollFrames;
	if (bMovieGated && bTravStarted && TravTime >= MovieFrom - 1e-6)
	{
		GIsDumpingMovie = MovieDumpSaved; bMovieGated = false;
		UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV movie dump on at sequence t=%.4f frame=%llu"), TravTime, (unsigned long long)GFrameCounter);
	}

	ReadHeroMask(); // previous frame's hero pixel mask (telemetry)
	// ---- input: live (keyboard / mouse / pad) or scripted playback
	FWebTravInput I;
	UWebTravScript* Script = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWebTravScript>() : nullptr;
	if (bPre) {} // pre-roll: no input
	else if (Script && Script->IsActive())
	{
		FVector2D LookRate;
		I = Script->Sample(TravTime, LookRate);
		I.Look = LookRate * Dt;
		if (bInputTestMouse)
		{ // round 20: -WHTravInputTest=mouseLook inside a scripted repro -- the injected mouse events add to the script's look (same gain as live)
			const float MSens = MouseRadPerUnit * FMath::Max(0.f, CVarWHMouseSensitivity.GetValueOnGameThread());
			LookMagFrame = MouseAccum.Size();
			I.Look += FVector2D(FMath::Clamp(MouseAccum.X, -MaxMouseDeltaPx, MaxMouseDeltaPx) * MSens, -FMath::Clamp(MouseAccum.Y, -MaxMouseDeltaPx, MaxMouseDeltaPx) * MSens);
		}
		double HeadingDeg = 0;
		if (Script->HeadingAt(TravTime, HeadingDeg))
		{ // steer toward a world direction: express it in camera-relative stick terms (what a player's stick would do)
			const double Mag = FMath::Max(I.Move.Size(), 0.0);
			const FVector W = FVector(FMath::Cos(FMath::DegreesToRadians(HeadingDeg)), FMath::Sin(FMath::DegreesToRadians(HeadingDeg)), 0);
			I.Move = FVector2D(FVector::DotProduct(W, Cam.RightFlat()), FVector::DotProduct(W, Cam.ForwardFlat())) * Mag;
		}
		double RelPhase = 0.45, Gap = 0.3, RepressVz = 1e9;
		if (Script->AutoChainAt(TravTime, RelPhase, Gap, RepressVz))
		{ // deterministic swing rhythm: hold through the arc, let go on the rising front, re-press after the gap
			const bool bSwinging = Traversal->IsSwinging();
			const FWebTravAnim& A = Traversal->Anim;
			// release on the rising front of the arc, or at the forward apex if the arc never gets that far
			const bool bFrontApex = A.Swing.Phase > 0.15f && Traversal->VelM().Z <= 0 && A.T > 0.6f;
			// round 07: a player lets go after the swoop — only once this swing has come down (vz < -3 m/s)
			if (!bSwinging) bAutoSawDescent = false;
			else if (Traversal->VelM().Z < -3.0) bAutoSawDescent = true;
			double SkyRepressH = 18.0, SkyMax = 3.0, SkyPhase = 0.8;
			int32 SkyTricks = 2;
			const int32 SkyEvery = Script->SkyEveryAt(TravTime, SkyRepressH, SkyTricks, SkyMax, SkyPhase);
			bool bKeepSwingThisFrame = false;
			// round 10: the sky release lets the arc climb further (skyPhase) before the launch
			// round 10 (T7 "peak at roofline height, then 1-4 storeys over the street"): the next release is a sky launch when it is
			// >= skyEvery releases after the previous one AND the lower street wall ahead is within reach (its roofline <=
			// SkyPeakMax + 8 m over the street; a player launches where he can top the block), or 5.5 s after the previous one anyway
			bool bSkyNext = false;
			if (SkyEvery > 0 && AutoReleases + 1 - LastSkyRelease >= SkyEvery && bSwinging)
			{
				// round 12: reachable = the apex that clears the tallest roof near the flip (SkyPeakNeeded) is within SkyPeakMax
				bool bReach = false;
				Traversal->SkyPeakNeeded(bReach);
				bSkyNext = bReach; // round 12: no forced launch any more (r10: "or 5.5 s after the last one anyway" flipped under the roofline)
			}
			const double RelPhaseEff = bSkyNext ? SkyPhase : RelPhase;
			// round 10 (Manhattan integration: releasePhase 0.85 left him hanging at 49 m for 14 s — a swing that never came down
			// fast or never reached the release phase): a player lets go of a stale swing after 2.4 s whatever its phase
			const bool bStale = bSwinging && A.ModeT > 2.4f;
			// round 10 (T1 rope held 0.5-1.6 s): past the low point and 1.45 s into the swing he lets go (the long web after a sky
			// launch held 2.1-2.2 s)
			// (the cut varies 1.25-1.55 s by release count so consecutive swings differ in length)
			// round 13 (T2 attach -> attach <= 3.3 s): a swing that ends in a flip program is let go at 1.05-1.2 s
			const int32 EveryNext = Script->TrickEveryAt(TravTime);
			// round 18 (critic r17 "f4's 4th flip missing its catch"): a flow flip is only pressed when a web is in reach where it ends
			// (canyons -- the lower roofline out of the flow climb's reach, the r13 "fires anyway" rule -- have webs on both sides all the way: the
			// predictor gave false negatives there, r18 render a: both tricks dropped; it only judges the low-roofline routes where r17 f4 missed)
			const bool bCanyon = Traversal->FlowApexGap() > double(Traversal->FlowReadyGain + Traversal->FlowHoldMax);
			const bool bCatchOk = !bSwinging || Traversal->CatchGuard <= 0.f || bCanyon || Traversal->CatchReachable(double(Traversal->CatchFlightS));
			const bool bTrickNext = EveryNext > 0 && (AutoReleases + 1) % EveryNext == 0 && !Traversal->bTrickLaunch && bCatchOk;
			// (round 14: 1.05-1.2 -> 0.92-1.06 s: the eased backDouble catches 0.07 s later, T2 kept <= 2.65 s)
			const float LongCut = bTrickNext ? 0.92f + 0.14f * float((AutoReleases * 37) % 7) / 6.f : 1.25f + 0.3f * float((AutoReleases * 37) % 7) / 6.f;
			// round 14: a swing that ends in a flow flip is let go at LongCut even before it rises (the flip solves its own climb; a flat
			// swing over a low roof held f4 1.4 s -> attach-to-attach 2.98 s)
			const bool bLong = bSwinging && bAutoSawDescent && A.ModeT > LongCut && (Traversal->VelM().Z > 0 || bTrickNext);
			// round 17 (TC8, critic r16 "fire flips from an apex >= 3 m over the lower roofline"): a swing that ends in a flow flip is held on
			// its RISING front until the flip's apex can clear the lower roofline within 30 m (FlowApexGap <= FlowReadyGain); the front apex
			// (vz <= 0) or a stale swing still lets go
			const bool bRoofHold = bTrickNext && Traversal->bFlowApexSolve && bSwinging && Traversal->VelM().Z > 0.5 && !bStale
				&& Traversal->FlowApexGap() > double(Traversal->FlowReadyGain)
				&& Traversal->FlowApexGap() <= double(Traversal->FlowReadyGain + Traversal->FlowHoldMax);
			// round 18: flow-flip release predicted within FlipPreT s (the LongCut clock, or the rising front nearing the release phase) and not
			// held for the roofline -> the trick camera pre-blends to its held 3/4 view before the release
			// (latched: once predicted it stays on until the release or the swing / trick plan ends -- a flickering prediction blended the camera
			// out and back in at 110 deg/s, r18 probe f4 3.6-4.4 s; a roof hold counts once its gap closes within FlipPreT at the climb rate)
			{
				const double Vz = Traversal->VelM().Z;
				const bool bPreNow = bTrickNext && bAutoHeld && bSwinging && bAutoSawDescent && !bStale
					&& (bRoofHold ? Traversal->FlowApexGap() - double(Traversal->FlowReadyGain) <= FMath::Max(0.0, Vz) * double(FlipPreT) + 0.5
						: (A.ModeT > LongCut - FlipPreT || (Vz > 0 && A.Swing.Phase > RelPhaseEff - 0.3f)));
				if (bPreNow) bAutoFlipPre = true;
				if (!bSwinging || !bTrickNext || !bAutoHeld) bAutoFlipPre = false;
			}
			if (bAutoHeld && bSwinging && !bRoofHold && ((bAutoSawDescent && ((A.Swing.Phase > RelPhaseEff && Traversal->VelM().Z > 0 && A.T > 0.25f) || bFrontApex)) || bStale || bLong))
			{
				bAutoHeld = false; AutoGapT = 0.0; ++AutoReleases;
				const int32 Every = Script->TrickEveryAt(TravTime);
				if (bSkyNext)
				{
					LastSkyRelease = AutoReleases; LastSkyT = TravTime; SkyPeakH = 0.0; // round 10: sky launch = jump pressed while the web is still held (jump-release) + trick pressed with it
					I.bJump = true; I.bTrick = true; bKeepSwingThisFrame = true;
					bSkyAuto = true; bSkyWasTrick = false; SkyTricksLeft = FMath::Max(0, SkyTricks - 1); SkyAutoT = 0.0;
				}
				else if (Every > 0 && AutoReleases % Every == 0 && !bCatchOk)
				{
					UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV catch guard: no web in reach %.1f s ahead at t %.2f -> plain release"), Traversal->CatchFlightS, TravTime);
				}
				else if (Every > 0 && AutoReleases % Every == 0)
				{ // trick pressed together with this release (round 12: with bTrickLaunch that release is a sky launch: same bookkeeping)
					I.bTrick = true;
					if (Traversal->bTrickLaunch)
					{
						LastSkyRelease = AutoReleases; LastSkyT = TravTime; SkyPeakH = 0.0; bKeepSwingThisFrame = true;
						bSkyAuto = true; bSkyWasTrick = false; SkyTricksLeft = FMath::Max(0, SkyTricks - 1); SkyAutoT = 0.0;
					}
				}
			}
			else if (!bAutoHeld && bSkyAuto)
			{ // sky phase: chain the next trick the moment one ends, then re-press once falling through skyRepressH
				AutoGapT += Dt;
				const bool bTrickNow = A.Sub == FName(TEXT("trick"));
				// round 12: the flip now plays at the apex (armed on the climb): the skyMax clock runs only outside the climb / program,
				// and the web is re-pressed in the program's final reach so the catch comes out of the reach (FLIPS_SPEC F8)
				if (!Traversal->IsFlipArmed() && !bTrickNow) SkyAutoT += Dt;
				bool bInReach = false;
				{
					float Ft = 0.f;
					if (const FWebFlipProgram* FP = bTrickNow ? FlipProgramNow(Ft) : nullptr)
						bInReach = FP->Segs.Num() > 0 && Ft >= FP->CatchT() - 0.02f; // round 13: the program's catch window (r20: -0.02, a fresh press cancels)
				}
				if (bSkyWasTrick && !bTrickNow && SkyTricksLeft > 0 && Traversal->VelM().Z > -12.0) { I.bTrick = true; --SkyTricksLeft; }
				bSkyWasTrick = bTrickNow;
				// round 10: re-press once he has fallen 12 m from the peak (or through skyRepressH): the long web after a sky launch
				// then carries him down to the street (StartSwing: SkyRopeMax) instead of a web-less fall
				const double HS = Traversal->HeightAboveStreet();
				SkyPeakH = FMath::Max(SkyPeakH, HS);
				if ((Traversal->VelM().Z < 0 && (HS <= SkyRepressH || HS <= SkyPeakH - 12.0) && !bTrickNow) || SkyAutoT >= SkyMax || bInReach)
				{
					bAutoHeld = true; bSkyAuto = false;
				}
			}
			else if (!bAutoHeld)
			{
				AutoGapT += Dt;
				// round 20: a fresh RMB press now cancels a running flip into a swing at once (owner bug 1), so the scripted player re-presses
				// only once the program reaches its catch window (as a player who wants to see the flip does); old canned tricks: last 0.35 s
				bool bFlipHold = Traversal->IsFlipArmed();
				if (A.Sub == FName(TEXT("trick")) || A.Sub == FName(TEXT("topOut")))
				{
					float Ft = 0.f;
					if (const FWebFlipProgram* FP = FlipProgramNow(Ft)) bFlipHold = FP->Segs.Num() > 0 && Ft < FP->CatchT() - 0.02f;
					else if (A.Sub == FName(TEXT("trick"))) bFlipHold = A.T < FMath::Max(0.62f, A.TrickDur - 0.35f);
				}
				if (AutoGapT >= Gap && Traversal->VelM().Z <= RepressVz && !bFlipHold) bAutoHeld = true;
			}
			bAutoWasSwinging = bSwinging;
			I.bSwing = bAutoHeld || bKeepSwingThisFrame;
		}
	}
	else PollLiveInput(Cast<APlayerController>(GetController()), I, DeltaSeconds);
	MouseAccum = FVector2D::ZeroVector;
	I.ComputeEdges(PrevInput);
	PrevInput = I;

	// ---- camera look, traversal, camera
	// settings menu (2026-10-01): FOV + camera shake. WHSettings() stays at its defaults (58.0 deg, shake on) in automated runs.
	Cam.BaseVFov = WHSettings().BaseVFov() * double(CamFovScale);   // round 03: a narrower lens (50 deg vertical at the 58 deg menu default): the hero reads larger, keystoning drops
	Cam.bJolts = WHSettings().bCameraShake;
	Cam.ApplyLook(I.Look);
	// pre-roll: the camera state is restored after the frame is set up and the traversal is only posed (not stepped), so the
	// sequence that follows is bit-identical to a run without pre-roll
	const FWebTravCamera PreCam = Cam;
	if (bPre) Traversal->PosePreview(); else Traversal->UpdateTraversal(Dt, I);
	for (const FWebTravEvent& E : Traversal->Events)
	{ // player.js event -> camera mapping
		const FString T = E.Type.ToString();
		if (T == TEXT("land") && E.Severity > 0.02f) Cam.Impact(E.Severity);
		else if (T == TEXT("perch")) Cam.Impact(E.Severity * 0.6);
		else if (T == TEXT("pointLaunch")) { Cam.Impact(0.18); Cam.Kick(0.7); }
		else if (T == TEXT("zipLaunch")) Cam.Kick(FMath::Min(1.0, 0.45 + E.Dist / 60.0));
		else if (T == TEXT("quickBoost")) { Cam.Kick(0.22 + 0.18 * E.K); Cam.Shake(0.04); }
		else if (T == TEXT("wall") && E.bRun) Cam.Shake(0.08);
		else if (T == TEXT("swingWallKick")) Cam.Shake(0.1 + 0.3 * E.Severity);
	}
	if (!bPre && !(Script && Script->IsActive())) WatchInput(Cast<APlayerController>(GetController()), I, DeltaSeconds);
	FTravCamInput CI;
	CI.Pos = Traversal->PosM(); CI.Vel = Traversal->VelM(); CI.Mode = Traversal->Anim.Mode; CI.Sub = Traversal->Sub(); CI.ModeT = Traversal->ModeT();
	CI.bHasAnchor = Traversal->IsSwinging(); CI.Anchor = Traversal->SwingAnchor();
	CI.bHasSwingDir = Traversal->IsSwinging(); CI.SwingDir = Traversal->SwingDir();
	CI.WallNormal = Traversal->WallNormal(); CI.Facing = Traversal->Facing(); CI.bDive = Traversal->IsDiving();
	CI.Tension = Traversal->SwingTension(); CI.Bank = Traversal->SwingBank();
	CI.HAbove = Traversal->PosM().Z - UWebTraversalComponent::H - Traversal->FloorBelow();
	CI.SwingAngle = Traversal->Anim.Swing.Angle;
	CI.SwingT = Traversal->SwingTime();
	CI.bSky = Traversal->IsSkyLaunch();
	// round 12: the flip camera starts searching for a sky background ~0.35 s before an armed apex flip begins
	CI.bFlipSoon = Traversal->IsFlipArmed() && Traversal->VelM().Z < double(Traversal->SkyTrickVz) + 5.0;
	// round 18: a predicted flow-flip release (auto-chain), or (live) the trick button held while swinging = the trick is coming at the release
	CI.bFlipPre = Traversal->IsSwinging() && (bAutoFlipPre || (!(Script && Script->IsActive()) && I.bTrick));
	{ float Ft = 0.f; CI.bFlip = Traversal->Anim.Sub == N_trick && FlipProgramNow(Ft) != nullptr; } // round 11: flip camera
	{ // round 16: compactness of the flip's upper-body shape (this frame's camera uses the previous frame's pose): the trick camera pulls in during a tuck / pike
		float Ft = 0.f;
		CI.FlipCompact = 0.f;
		const FWebFlipProgram* FPc = CI.bFlip ? FlipProgramNow(Ft) : nullptr;
		if (FPc && LastFlip.bValid)
		{
			auto Cmp = [](EWebFlipShape S) { return S == EWebFlipShape::Tuck ? 1.f : (S == EWebFlipShape::Pike ? 0.6f : 0.f); };
			const float Now = FMath::Lerp(Cmp(LastFlip.A), Cmp(LastFlip.B), LastFlip.W);
			// anticipation: the camera starts backing out 0.22 s before a tuck / pike ends (min of now and 0.22 s ahead), so the open shape that follows
			// (kickout / swan) is not seen at the tuck distance; it pulls in only when the compact shape has actually begun
			const FWebFlipPose Ahead = WebFlips::Sample(*FPc, FMath::Min(Ft + 0.22f, FPc->Dur()));
			const float Fut = Ahead.bValid ? FMath::Lerp(Cmp(Ahead.A), Cmp(Ahead.B), Ahead.W) : Now;
			CI.FlipCompact = FMath::Min(Now, Fut);
		}
		// round 18: the hero's vertical extent for the trick camera's distance (critic r17 TC-C "distance 4.1-4.4 m, h p90 .37-.46"): the posed body
		// now (joints of the previous frame's pose + 0.2 m pad) and the program's shape table 0.1 / 0.25 s ahead -- the larger wins, so the
		// camera backs out ahead of an opening shape and only comes in once a compact one has begun
		CI.FlipExtent = 0.f;
		if (FPc && bHeroMesh)
		{
			const USkeletalMeshComponent* M = GetMesh();
			double Zmin = 1e9, Zmax = -1e9;
			for (const TCHAR* Bn : { TEXT("head"), TEXT("hips"), TEXT("hand_L"), TEXT("hand_R"), TEXT("foot_L"), TEXT("foot_R") })
			{
				const double Z = M->GetBoneLocation(FName(Bn)).Z / 100.0;
				Zmin = FMath::Min(Zmin, Z); Zmax = FMath::Max(Zmax, Z);
			}
			float Ext = Zmax > Zmin ? float(Zmax - Zmin) + 0.2f : 0.f;
			for (const float Ah : { 0.1f, 0.25f })
			{
				const FWebFlipPose Pa = WebFlips::Sample(*FPc, FMath::Min(Ft + Ah, FPc->Dur()));
				if (Pa.bValid) Ext = FMath::Max(Ext, FMath::Lerp(WebFlips::ShapeExtent(Pa.A), WebFlips::ShapeExtent(Pa.B), Pa.W));
			}
			CI.FlipExtent = Ext;
		}
	}
	// round 15: the direction to the sun for the sun-aware trick camera (the level's atmosphere sun light 0; retried for the first
	// frames in case the look rig streams in after BeginPlay)
	if (!Cam.bHaveSun && SunTries < 240)
	{
		++SunTries;
		const UDirectionalLightComponent* Best = nullptr;
		for (TObjectIterator<UDirectionalLightComponent> It; It; ++It)
		{
			const UDirectionalLightComponent* L = *It;
			if (!L || L->GetWorld() != GetWorld() || !L->IsRegistered() || !L->IsVisible()) continue;
			const bool bSun = L->IsUsedAsAtmosphereSunLight() && L->GetAtmosphereSunLightIndex() == 0;
			if (bSun) { Best = L; break; }
			if (!Best || L->Intensity > Best->Intensity) Best = L;
		}
		if (Best)
		{
			Cam.SunDir = -Best->GetDirection().GetSafeNormal();
			Cam.bHaveSun = true;
			const FRotator SR = Cam.SunDir.Rotation();
			UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV sun: %s (%s), direction to the sun yaw %.1f elevation %.1f deg"), *Best->GetOwner()->GetName(),
				Best->IsUsedAsAtmosphereSunLight() ? TEXT("atmosphere sun") : TEXT("brightest directional"), SR.Yaw, SR.Pitch);
		}
	}
	Cam.HeroProjH = ProjectHeroH();
	Cam.Update(Dt, CI, Traversal->TravWorld);
	Traversal->TravWorld.PushOutOfCrowns(Cam.CamPos, 0.5);   // round 01 (Gap 3): the lens never sits inside a tree crown

	// ---- move the actor (capsule) with the simulated body
	const FVector BodyCm = Traversal->PosM() * 100.0;
	SetActorLocationAndRotation(BodyCm - FVector(0, 0, UWebTraversalComponent::H * 100.0) + FVector(0, 0, GetCapsuleComponent()->GetScaledCapsuleHalfHeight()),
		FRotator(0, FMath::RadiansToDegrees(Traversal->Facing()), 0), false, nullptr, ETeleportType::TeleportPhysics);

	// ---- camera component
	const FVector CamCm = Cam.CamPos * 100.0;
	FollowCamera->SetWorldLocationAndRotation(CamCm, Cam.CamRot);
	double Aspect = 16.0 / 9.0;
	if (GEngine && GEngine->GameViewport && GEngine->GameViewport->Viewport)
	{
		const FIntPoint Sz = GEngine->GameViewport->Viewport->GetSizeXY();
		if (Sz.X > 0 && Sz.Y > 0) Aspect = double(Sz.X) / double(Sz.Y);
	}
	const double HFov = 2.0 * FMath::Atan(FMath::Tan(FMath::DegreesToRadians(Cam.OutVFov * 0.5)) * Aspect);
	FollowCamera->SetFieldOfView(float(FMath::RadiansToDegrees(HFov)));
	// round 08 (critic r07: blur smeared the whole frame and the hero at all times): no base amount, only at real speed
	FollowCamera->PostProcessSettings.MotionBlurAmount = float(FMath::Clamp(0.35 * Cam.MotionBlur, 0.0, 0.5));
	FollowCamera->PostProcessSettings.MotionBlurMax = float(1.0 + 2.0 * Cam.MotionBlur);
	if (MaskCapture) { MaskCapture->SetWorldLocationAndRotation(CamCm, Cam.CamRot); MaskCapture->FOVAngle = FollowCamera->FieldOfView; }
	if (SceneCapture) { SceneCapture->SetWorldLocationAndRotation(CamCm, Cam.CamRot); SceneCapture->FOVAngle = FollowCamera->FieldOfView; }
	UpdateHeroFill();

	// ---- figure + webs
	PoseFigure(float(Dt));
	if (bHeroMesh)
	{
		if (UWebTravAnimInstance* AI = Cast<UWebTravAnimInstance>(GetMesh()->GetAnimInstance()))
		{
			const FWebTravStrand& St = Traversal->Strands[0];
			const bool bWeb = St.bActive && St.ReleaseT < 0.f;
			AI->SetDrive(Traversal->Anim, bWeb, St.Anchor * 100.0, St.bRightHand, I.bSwing);
		}
		for (UStaticMeshComponent* C : FigureParts) { if (C) C->SetVisibility(false); }
	}
	FigureRoot->SetVisibility(FVector::Dist(CamCm, BodyCm) > 85.0, true);
	if (bHeroMesh) { for (UStaticMeshComponent* C : FigureParts) { if (C) C->SetVisibility(false); } }
	PendingWebDt = float(Dt); PendingCamCm = CamCm;   // round 01: the strands are drawn in PostAnimTick, after this frame's pose is final

	// ---- telemetry
	if (bPre) { Cam = PreCam; return; }
	if (Script && Script->WantsTelemetry()) PushTelemetry(TravTime, I);
	++FrameIndex;
}

void AWebTravCharacter::UpdateHeroFill()
{
	if (!HeroFill) return;
	const FVector Hero = Traversal->PosM() * 100.0 + FVector(0, 0, 20.0);
	const FVector CamCm = Cam.CamPos * 100.0;
	FVector To = CamCm - Hero;
	To = To.SizeSquared() > 1.0 ? To.GetSafeNormal() : FVector(-1, 0, 0);
	HeroFill->SetWorldLocation(Hero + To * (HeroFillDist * 100.0) + FVector(0, 0, HeroFillUp * 100.0));
	double K = FMath::Clamp(Cam.FlipK, 0.0, 1.0);
	// round 15 (rendered f2 4.73 s: with the sun now behind the camera the sunlit hero + the 18000 cd flip fill read pale / clipped): the
	// fill only lifts a BACKLIT hero -- scaled by how much the view looks toward the sun, down to HeroFillFrontK x base when front-lit
	double Scale = 1.0;
	if (Cam.bHaveSun)
	{
		const double B = FMath::SmoothStep(-0.3, 0.4, FVector::DotProduct(-To, Cam.SunDir)); // 1 = looking into the sun (backlit hero)
		K *= B;
		Scale = FMath::Lerp(double(HeroFillFrontK), 1.0, B);
	}
	// the fill is tuned for the 26-44 klux day sun: it fades out with the night factor (MPC_City NightK, as AWHCityLights reads it); at night the hero is lit by the world + AWHLookHeroLight
	static TWeakObjectPtr<UMaterialParameterCollection> NightMpc;
	if (!NightMpc.IsValid()) NightMpc = LoadObject<UMaterialParameterCollection>(nullptr, TEXT("/Game/City/Materials/MPC_City.MPC_City"));
	const double NightK = NightMpc.IsValid() && GetWorld() ? FMath::Clamp(double(UKismetMaterialLibrary::GetScalarParameterValue(GetWorld(), NightMpc.Get(), TEXT("NightK"))), 0.0, 1.0) : 0.0;
	HeroFill->SetIntensity(float(FMath::Lerp(FMath::Lerp(double(HeroFillCd), double(HeroFillFlipCd), K) * Scale, double(HeroFillNightCd), NightK)));
}

const FWebFlipProgram* AWebTravCharacter::FlipProgramNow(float& OutT) const
{
	const FWebTravAnim& A = Traversal->Anim;
	OutT = A.T;
	if (A.Mode != EWebTravMode::Air) return nullptr;
	if (A.Sub == N_trick && !A.Trick.IsNone()) return WebFlips::Find(A.Trick);
	if (A.Sub == N_topOut && bHeroMesh)
	{ // round 11: the wall-run top-out flip is a program too (only with the flip shape clips: the old releaseFlip clip spins by itself)
		const UWebTravAnimInstance* AI = Cast<UWebTravAnimInstance>(GetMesh()->GetAnimInstance());
		if (AI && AI->HasFlipClips()) return WebFlips::Find(FName(TEXT("wallFront")));
	}
	return nullptr;
}

FVector AWebTravCharacter::HandWorldCm(bool bRight) const
{
	if (bHeroMesh && GetMesh()) return GetMesh()->GetBoneLocation(bRight ? FName(TEXT("hand_R")) : FName(TEXT("hand_L")));
	const USceneComponent* P = ArmPivot[bRight ? 1 : 0];
	if (!P) return Traversal->PosM() * 100.0;
	return P->GetComponentTransform().TransformPosition(FVector(0, 0, -60));
}

FVector AWebTravCharacter::PalmWorldCm(bool bRight) const
{
	const USkeletalMeshComponent* M = bHeroMesh ? GetMesh() : nullptr;
	if (M && bPalmOk)
	{
		const int32 BI = M->GetBoneIndex(bRight ? FName(TEXT("hand_R")) : FName(TEXT("hand_L")));
		if (BI != INDEX_NONE)
		{
			const FTransform T = M->GetBoneTransform(BI);
			return T.GetLocation() + T.TransformVectorNoScale(PalmLocal[bRight ? 1 : 0]) * (PalmOffsetCm * M->GetComponentScale().Z);
		}
	}
	return HandWorldCm(bRight);
}

void FWebTravPostTick::ExecuteTick(float DeltaTime, ELevelTick TickType, ENamedThreads::Type CurrentThread, const FGraphEventRef& MyCompletionGraphEvent)
{
	if (!Target || !IsValid(Target)) return;
	if (Phase == 0) Target->PostAnimTick(DeltaTime); else Target->EndAnimTick();
}

void AWebTravCharacter::PostAnimTick(float Dt)
{
	// Compensate the authored pose's lean AFTER this frame has been evaluated. The old loop compared
	// previous-frame bones with the new program angle and fed its stored correction back a second time;
	// its catch-up therefore added bursts to a tuck and oscillated at shape boundaries. Measuring in the
	// figure's own frame also keeps a banked/twisting world-axis projection out of the control signal.
	float FlipT = 0.f;
	if (bHeroMesh && LastFlip.bValid && FlipProgramNow(FlipT) && GetMesh())
	{
		const USkeletalMeshComponent* Mesh = GetMesh();
		const FVector WorldAxis = (Mesh->GetBoneLocation(TEXT("head")) - Mesh->GetBoneLocation(TEXT("hips"))).GetSafeNormal();
		if (!WorldAxis.IsNearlyZero())
		{
			const FVector PoseAxis = FigureRoot->GetComponentQuat().UnrotateVector(WorldAxis);
			FlipOffQ = WebFlips::PoseRotation(LastFlip, PoseAxis, float(Smooth01(FlipT / 0.15)), Traversal->Anim.TrickSide);
			const FQuat Q = (FlipBodyFrame * FlipOffQ).GetNormalized();
			// Keep the traversal centre fixed; the only change is the authored pose's root rotation about it.
			FigureRoot->SetWorldLocationAndRotation(Traversal->PosM() * 100.0 - Q.RotateVector(FVector(0, 0, 95)), Q);
		}
	}
	// Hand/palm locations and the material's strand origins now see this same corrected rendered pose.
	UpdateWebs(PendingWebDt, PendingCamCm);
}

void AWebTravCharacter::EndAnimTick()
{
	if (!bRowPending) return;
	bRowPending = false;
	if (UWebTravScript* Script = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWebTravScript>() : nullptr)
		Script->AddTelemetryRow(PendingRow + BuildCols25() + FinalSwingCols(PendingRowT));
}

void AWebTravCharacter::PoseFigure(float Dt)
{
	const FWebTravAnim& A = Traversal->Anim;
	FQuat Body = A.BodyQ;
	bool bSpringUsed = false;
	{ // round 01 (W4): at the attach (the pendulum starts when the tip lands) the body orientation follows the rope frame through a critically damped spring (~0.3 s, never a one-frame turn)
		const bool bSw = A.Mode == EWebTravMode::Swing;
		if (bSw && !bPrevSwingMode) { AttachT = 0.0; SpringResid0 = bBodySpringInit ? BodySpringQ.AngularDistance(Body) : 0.0; }
		if (bSw) { AttachT += Dt; OffSwingT = 0.0; }
		else { if (bPrevSwingMode) OffSwingT = 0.0; else OffSwingT += Dt; }
		bPrevSwingMode = bSw;
		if (!bBodySpringInit) { BodySpringQ = Body; BodySpringVel = FVector::ZeroVector; bBodySpringInit = true; }
		// round 08 (W4 s3 t=10.43: the wall entry 0.15 s after a swing attach snapped the chest at 1576 deg/s -- the spring only
		// covered swing mode, so the wall frame replaced the rope frame in one step): the spring stays live into a wall entry
		// fresh off a swing until it has converged (or 0.5 s), so the body turns onto the wall at <= 320 deg/s like the attach
		// round 10 (critic r09 gap 3: a one-frame ~840-3340 deg/s chest snap 0.43 s after the s3 wallJump catch, reproducible in a
		// nullrhi probe at t=14.00): the 0.45 s window expired with the spring still ~20-50 deg off (a wall-entry frame is far from
		// the rope frame and the traversal's own rate gate (Sw.T < 0.4) ends at the same time) -- the residual landed in one frame.
		// The spring now runs until CONVERGED (residual <= 2 deg), capped at 0.9 s, same 320 deg/s step limit throughout.
		// round 11 (r11 probe: bare wallJump -> swing attaches measured 548-759 deg/s on the chest -- the route's wall exits
		// start the spring 60-180 deg off the rope frame; the r10 ramp (omega 10 -> 40 at 0.3 s, cap 260) sums with the clip
		// crossfade past the 700 line): a big-gap attach (> 60 deg) runs a gentler, longer ramp (omega 10 until 0.45 s, then
		// -> 30; step cap 200) and its convergence window extends to 1.3 s so the cap never expires unconverged (the r09 bug
		// class). Plain chain catches (gap <= 60 deg) keep the r10 behaviour.
		const bool bBigAttach = SpringResid0 > FMath::DegreesToRadians(60.0);
		const double SpringCapT = bBigAttach ? 1.3 : 0.9;
		const bool bSpring = (bSw && (AttachT < 0.45 || (AttachT < SpringCapT && BodySpringQ.AngularDistance(Body) > FMath::DegreesToRadians(2.0))))
			|| (A.Mode == EWebTravMode::Wall && OffSwingT < 0.5 && BodySpringQ.AngularDistance(Body) > FMath::DegreesToRadians(2.0));
		if (bSpring)
		{
			const double Omega = bSw ? (AttachT < (bBigAttach ? 0.45 : 0.3) ? 10.0 : FMath::Lerp(10.0, bBigAttach ? 30.0 : 40.0, Smooth01((AttachT - (bBigAttach ? 0.45 : 0.3)) / 0.15))) : 10.0;
			FQuat D = Body * BodySpringQ.Inverse();   // spring state -> target, as a rotation vector
			if (D.W < 0) D = FQuat(-D.X, -D.Y, -D.Z, -D.W);
			FVector X = -D.ToRotationVector();       // the spring's offset from the target
			const double Xs = Omega * Dt, Ex = 1.0 / (1.0 + Xs + 0.48 * Xs * Xs + 0.235 * Xs * Xs * Xs);
			const FVector Tmp = (BodySpringVel + X * Omega) * Dt;
			BodySpringVel = (BodySpringVel - Tmp * Omega) * Ex;
			X = (X + Tmp) * Ex;
			FQuat NewQ = (FQuat::MakeFromRotationVector(X) * Body).GetNormalized();
			{ // the turn onto the rope never exceeds 260 deg/s (a head-down attach is up to 150 deg away; round 10: 320 -> 280 -> 260 --
				// it stacks with the hips-align slew and the clip crossfade at the catch, and the spring now runs until converged);
				// round 11: a big-gap attach (wall exit, SpringResid0 > 60 deg) caps at 200
				const double Step = BodySpringQ.AngularDistance(NewQ), MaxStep = FMath::DegreesToRadians(bBigAttach ? 200.0 : 260.0) * Dt;
				if (Step > MaxStep) NewQ = FQuat::Slerp(BodySpringQ, NewQ, MaxStep / Step).GetNormalized();
			}
			BodySpringQ = NewQ;
			Body = BodySpringQ; bSpringUsed = true;
		}
		else { BodySpringQ = Body; BodySpringVel = FVector::ZeroVector; }
	}
	FVector Root = bSpringUsed ? Traversal->PosM() * 100.0 - Body.RotateVector(FVector(0, 0, 95)) : A.RootPos;
	FQuat Q = Body;
	// round 11 (FLIPS_BRIEF): gymnast flip programs rotate the whole body about its centre — pitch about the lateral axis, twist
	// about the long axis — on the program's momentum timeline (WebTravFlips); a cut program (web catch / landing) hands its last
	// rotation to a 0.07 s spring back to the body frame, so a catch never pops
	float FlipT = 0.f;
	const FWebFlipProgram* FP = FlipProgramNow(FlipT);
	if (FP)
	{
		const FWebFlipPose FPo = WebFlips::Sample(*FP, FlipT);
		// round 14: minus the shape's own hips->head lean (ramped in over the first 0.15 s while the anim crossfades into the first
		// shape), so the visible body axis turns at the program's eased rate instead of spiking at every shape change
		const double AxisOff = FPo.AxisOffDeg * Smooth01(FlipT / 0.15);
		FlipBodyFrame = Body;
		// The same-frame evaluated pose replaces this provisional authored-shape compensation in PostAnimTick.
		FlipOffQ = FQuat(FVector(0, 1, 0), FMath::DegreesToRadians(double(FPo.PitchDeg) - AxisOff))
			* FQuat(FVector(0, 0, 1), FMath::DegreesToRadians(double(FPo.TwistDeg) * A.TrickSide));
		LastFlip = FPo; LastFlipName = FP->Name;
	}
	else
	{
		// round 05 (critic r04 / A5: chest rate through the catch median 646 deg/s): a catch at the END of a program (the reach, body
		// <= ~70 deg off upright) decays its residual rotation at <= 340 deg/s instead of the 0.07 s snap (which spikes > 400 deg/s).
		// round 07: the mid-program CANCEL snap (kept in r05/r06 for owner bug 1's press latency) is rate-limited the same way --
		// the press still fires the web at once; only the body's unwind is bounded.
		// round 07 (critic r06 s3 W4 t=20.68, 2187 deg/s: the topOut catch landed mid wallFront rotation and took the >70 deg
		// cancel snap): EVERY residual decays rate-limited now (the press's answer is the web firing, not the body snap);
		// <= 340 deg/s keeps the catch inside W4's never->700 band even with the attach spring's own 320 on top
		// round 10 (critic r09: A5 chest-rate median on s3 599 deg/s -- the residual unwind STACKS on the attach spring's turn onto
		// the rope frame and the clip crossfade): 340 -> 240 deg/s, and while the attach spring is still converging (its own 320
		// deg/s is the dominant motion) the residual bleeds at <= 100 deg/s so the two never sum past the 400 bar.
		const double Ang = FlipOffQ.GetAngle();
		if (Ang > FMath::DegreesToRadians(0.2))
		{
			// round 12 (r11 s3 W4 50 % / A5 702: the route's bare wall-exit catches are big-gap attaches whose spring window is
			// 1.3 s; the residual's 100 deg/s bleed window ended at 0.9 s, so the tail stacked on the still-converging spring):
			// the slow bleed covers the spring's whole convergence window for a big-gap attach
			const bool bBigGap = SpringResid0 > FMath::DegreesToRadians(60.0);
			const double CapDps = (A.Mode == EWebTravMode::Swing && AttachT < (bBigGap ? 1.3 : 0.9)) ? 100.0 : 240.0;
			const double MaxStep = FMath::DegreesToRadians(CapDps) * Dt;
			const double Step = FMath::Min(Ang * (1.0 - FMath::Exp(-Dt / 0.10)), MaxStep);
			FlipOffQ = FQuat::Slerp(FlipOffQ, FQuat::Identity, FMath::Clamp(Step / Ang, 0.0, 1.0));
		}
		else FlipOffQ = FQuat::Identity;
		LastFlip = FWebFlipPose(); LastFlipName = NAME_None;
	}
	if (FP || FlipOffQ.GetAngle() > FMath::DegreesToRadians(0.2))
	{
		Q = Body * FlipOffQ;
		const FVector Centre = Traversal->PosM() * 100.0;
		Root = Centre - Q.RotateVector(FVector(0, 0, 95));
	}
	else if (A.Sub == N_trick && !A.Trick.IsNone() && A.TrickDur > 0)
	{
		const double E = Smooth01(A.T / A.TrickDur);
		double Ang = 0;
		FVector Axis(0, 1, 0);
		if (A.Trick == N_tuckFlip) Ang = 2 * PI * E;
		else if (A.Trick == N_layout) Ang = 2 * PI * E * A.TrickSide;
		else if (A.Trick == N_corkscrew) { Ang = 2 * PI * E * A.TrickSide; Axis = FVector(1, 0, 0); }
		if (Ang != 0)
		{
			Q = Body * FQuat(Axis, Ang);
			const FVector Centre = Traversal->PosM() * 100.0;
			Root = Centre - Q.RotateVector(FVector(0, 0, 95));
		}
	}
	// round 04: air cycles keep the whole body moving — a slow barrel roll and pitch sway, phased per cycle
	// round 06: its weight is a spring (was switched on at full amplitude when a trick ended: one-frame body pop)
	const bool bSwayOn = bHeroMesh && A.Mode == EWebTravMode::Air && A.Sub != N_trick && A.Sub != N_topOut; // round 09: dives sway too
	SwayW = FMath::Clamp(SwayW + (bSwayOn ? Dt / 0.2f : -Dt / 0.2f), 0.f, 1.f);
	if (bHeroMesh && A.Mode == EWebTravMode::Air && SwayW > 0.001f)
	{
		if (const UWebTravAnimInstance* AI = Cast<UWebTravAnimInstance>(GetMesh()->GetAnimInstance()))
		{
			if (AI->InAirCycle())
			{
				const double Tc = AI->AirCycleTime(), Ph = AI->AirCycleCount() * 1.7;
				const double Ramp = FMath::Clamp(Tc / 0.3, 0.0, 1.0) * Smooth01(SwayW); // round 09: dives sway too
				// round 20: at speed the body holds the streamlined line (sway down to 20 % from 22 to 32 m/s)
				const double FastK = UWebTravAnimInstance::bAirSpeedPose ? Smooth01((A.Speed - 22.0) / 10.0) : 0.0;
				const double SwayAmp = 1.0 - 0.8 * FastK;
				const double RollA = 0.3 * Ramp * SwayAmp * FMath::Sin(2 * PI * 1.05 * Tc + Ph) * (AI->AirCycleCount() % 2 ? 1.0 : -1.0);
				const double PitchA = 0.2 * Ramp * SwayAmp * FMath::Sin(2 * PI * 0.8 * Tc + Ph * 0.5);
				SwayDeltaQ = FQuat(FVector(1, 0, 0), RollA) * FQuat(FVector(0, 1, 0), PitchA);   // round 01: remembered so it can decay when the swing starts
				const FQuat Q2 = Q * SwayDeltaQ;
				const FVector Centre = Traversal->PosM() * 100.0;
				Root = Centre - Q2.RotateVector(FVector(0, 0, 95));
				Q = Q2;
			}
		}
	}
	if (!(bHeroMesh && A.Mode == EWebTravMode::Air && SwayW > 0.001f))
	{ // round 01 (W4): the air-sway lean (up to 34 deg of roll) used to vanish in the swing's first frame (1500 deg/s chest spike): it decays over ~0.1 s instead
	  // round 10 (critic r09: W4 chest rate on plain chain catches 400-570 deg/s): the sway decay stacks on the attach spring + the
	  // air->swing crossfade at the attach -- 0.1 -> 0.2 s (peak ~170 -> ~85 deg/s)
		SwayDeltaQ = FQuat::Slerp(SwayDeltaQ, FQuat::Identity, 1.0 - FMath::Exp(-Dt / 0.2));
		if (SwayDeltaQ.GetAngle() > FMath::DegreesToRadians(0.3))
		{
			Q = Q * SwayDeltaQ;
			Root = Traversal->PosM() * 100.0 - Q.RotateVector(FVector(0, 0, 95));
		}
	}
	FigureRoot->SetWorldLocationAndRotation(Root, Q);

	// limb directions in figure space (X forward, Y right, Z up); pivots hang along -Z by default
	auto ToLocal = [this](const FVector& WorldDir) { return FigureRoot->GetComponentQuat().UnrotateVector(WorldDir).GetSafeNormal(); };
	FVector Arm[2], Leg[2];
	const double Sp = A.Speed;
	const EWebTravMode M = A.Mode;
	for (int32 S = 0; S < 2; ++S)
	{
		const double Sd = S == 0 ? -1.0 : 1.0;
		Arm[S] = FVector(0.05, 0.18 * Sd, -1);
		Leg[S] = FVector(0, 0.05 * Sd, -1);
	}
	if (M == EWebTravMode::Ground)
	{
		RunPhase += Dt * Sp * 0.95;
		const double AA = FMath::Min(1.0, Sp / 8.0) * 0.9, LA = FMath::Min(1.0, Sp / 8.0) * 0.8;
		for (int32 S = 0; S < 2; ++S)
		{
			const double Sd = S == 0 ? -1.0 : 1.0;
			Arm[S] = FVector(FMath::Sin(RunPhase + (S ? PI : 0)) * AA, 0.15 * Sd, -1);
			Leg[S] = FVector(FMath::Sin(RunPhase + (S ? 0 : PI)) * LA, 0.05 * Sd, -1);
		}
	}
	else if (M == EWebTravMode::Land)
	{
		for (int32 S = 0; S < 2; ++S) { const double Sd = S == 0 ? -1.0 : 1.0; Arm[S] = FVector(0.5, 0.5 * Sd, -0.6); Leg[S] = FVector(0.6, 0.2 * Sd, -1); }
	}
	else if (M == EWebTravMode::Air)
	{
		const bool bDive = A.bDive || A.Sub == N_dive;
		for (int32 S = 0; S < 2; ++S)
		{
			const double Sd = S == 0 ? -1.0 : 1.0;
			if (bDive) { Arm[S] = FVector(-1, 0.25 * Sd, 0.15); Leg[S] = FVector(-0.25, 0.08 * Sd, -1); }
			else if (A.Sub == N_rise || A.Sub == N_jumpLaunch) { Arm[S] = FVector(0.3, 0.6 * Sd, 0.5); Leg[S] = FVector(S ? -0.3 : 0.5, 0.1 * Sd, -1); }
			else if (A.Sub == N_trick || A.Sub == N_release)
			{
				Arm[S] = FVector(0.1, 1.0 * Sd, 0.25);
				Leg[S] = A.Trick == N_tuckFlip ? FVector(1.0, 0.15 * Sd, -0.3) : A.Trick == N_scissor ? FVector(S ? 0.8 : -0.6, 0.1 * Sd, -1) : FVector(0.3, 0.2 * Sd, -1);
			}
			else if (A.Sub == N_zipPull) { Arm[S] = S ? FVector(1, 0.1, 0.25) : FVector(-0.2, -0.8, -0.2); Leg[S] = FVector(-0.3, 0.1 * Sd, -1); }
			else { Arm[S] = FVector(0.1, 0.9 * Sd, 0.3); Leg[S] = FVector(0.3, 0.2 * Sd, -1); }
		}
	}
	else if (M == EWebTravMode::Swing)
	{
		const int32 WebHand = A.Swing.bRightHand ? 1 : 0;
		const double Fwd = -A.Swing.Phase * 0.55 + 0.2;
		for (int32 S = 0; S < 2; ++S)
		{
			const double Sd = S == 0 ? -1.0 : 1.0;
			const FVector Shoulder = ArmPivot[S]->GetComponentLocation();
			Arm[S] = S == WebHand ? ToLocal(A.Swing.Anchor - Shoulder) : FVector(0.2, 0.9 * Sd, -0.2);
			Leg[S] = FVector(Fwd + (S ? 0.15 : -0.1), 0.1 * Sd, -1);
		}
	}
	else if (M == EWebTravMode::Zip)
	{
		for (int32 S = 0; S < 2; ++S)
		{
			const double Sd = S == 0 ? -1.0 : 1.0;
			Arm[S] = ToLocal(A.Zip.Target - ArmPivot[S]->GetComponentLocation());
			Leg[S] = FVector(-0.4, 0.1 * Sd, -1);
		}
	}
	else if (M == EWebTravMode::Wall)
	{
		const double Ph = A.Wall.Phase * 2 * PI;
		for (int32 S = 0; S < 2; ++S)
		{
			const double Sd = S == 0 ? -1.0 : 1.0;
			const double Sw = A.Wall.bFast ? FMath::Sin(Ph + (S ? PI : 0)) : 0;
			Arm[S] = FVector(0.6 + 0.3 * Sw, 0.45 * Sd, 0.5);
			Leg[S] = FVector(0.4 - 0.4 * Sw, 0.3 * Sd, -0.7);
		}
	}
	else if (M == EWebTravMode::Perch)
	{
		for (int32 S = 0; S < 2; ++S) { const double Sd = S == 0 ? -1.0 : 1.0; Arm[S] = FVector(0.7, 0.3 * Sd, -0.6); Leg[S] = FVector(0.9, 0.3 * Sd, -0.35); }
	}
	// quick web boost: the web hand reaches for its anchor
	if (A.bQuickActive && A.QuickT < 0.4f)
	{
		const int32 H = A.bQuickRightHand ? 1 : 0;
		const FWebTravStrand& St = Traversal->Strands[0];
		if (St.bActive) Arm[H] = ToLocal(St.Anchor * 100.0 - ArmPivot[H]->GetComponentLocation());
	}
	const double K = 1.0 - FMath::Exp(-18.0 * Dt);
	for (int32 S = 0; S < 2; ++S)
	{
		const FQuat WA = FQuat::FindBetweenNormals(FVector(0, 0, -1), Arm[S].GetSafeNormal());
		const FQuat WL = FQuat::FindBetweenNormals(FVector(0, 0, -1), Leg[S].GetSafeNormal());
		ArmPivot[S]->SetRelativeRotation(FQuat::Slerp(ArmPivot[S]->GetRelativeRotation().Quaternion(), WA, K));
		LegPivot[S]->SetRelativeRotation(FQuat::Slerp(LegPivot[S]->GetRelativeRotation().Quaternion(), WL, K));
	}
}

void AWebTravCharacter::UpdateWebs(float Dt, const FVector& CamPosCm)
{
	// round 25: the rope look (RopeLook 1 = unlit two-tone M_TravWeb with a screen-space width clamp; 0 = r24 lit dark line)
	const bool bTwoTone = Traversal->RopeLook > 0.5f && WebMatTwoTone[0] != nullptr && WebMatTwoTone[1] != nullptr;
	if (WebLookNow != (bTwoTone ? 1 : 0))
	{
		WebLookNow = bTwoTone ? 1 : 0;
		for (int32 SI = 0; SI < 2; ++SI)
			for (int32 K = 0; K < SEGS_PER_STRAND; ++K)
				if (UStaticMeshComponent* C = WebSegs[SI * SEGS_PER_STRAND + K]) C->SetMaterial(0, bTwoTone ? static_cast<UMaterialInterface*>(WebMatTwoTone[SI].Get()) : static_cast<UMaterialInterface*>(WebMat.Get()));
	}
	if (bTwoTone)
	{
		for (int32 SI = 0; SI < 2; ++SI)
		{
			WebMatTwoTone[SI]->SetScalarParameterValue(TEXT("CoreBright"), Traversal->RopeCoreBright);
			WebMatTwoTone[SI]->SetScalarParameterValue(TEXT("CoreDark"), Traversal->RopeCoreDark);
			WebMatTwoTone[SI]->SetScalarParameterValue(TEXT("Pivot"), Traversal->RopePivot);
			WebMatTwoTone[SI]->SetScalarParameterValue(TEXT("CoreLvl"), Traversal->RopeCoreLvl);
			WebMatTwoTone[SI]->SetScalarParameterValue(TEXT("RimLvl"), Traversal->RopeRimLvl);
			WebMatTwoTone[SI]->SetScalarParameterValue(TEXT("Solid"), Traversal->RopeSolid);
		}
	}
	// pixels per cm at 1 cm distance: viewport height / (2 tan(vfov / 2)) -- the strand width is clamped in screen space
	double ViewH = 1080.0, Aspect = 16.0 / 9.0;
	if (GEngine && GEngine->GameViewport && GEngine->GameViewport->Viewport)
	{
		const FIntPoint Sz = GEngine->GameViewport->Viewport->GetSizeXY();
		if (Sz.Y > 0) ViewH = double(Sz.Y);
		if (Sz.X > 0 && Sz.Y > 0) Aspect = double(Sz.X) / double(Sz.Y);
	}
	const double PxK = ViewH / (2.0 * FMath::Tan(FMath::DegreesToRadians(FMath::Clamp(double(Cam.OutVFov), 20.0, 150.0) * 0.5)));
	for (int32 SI = 0; SI < 2; ++SI)
	{
		bRopeDrawn[SI] = false;
		const FWebTravStrand& St = Traversal->Strands[SI];
		const bool bReleased = St.bActive && St.ReleaseT >= 0.f;
		const bool bInFlight = St.bActive && !bReleased && St.Age < St.ShootDur;   // round 11: the shot is still flying
		const FVector Hand = PalmWorldCm(St.bRightHand);
		if (bReleased && !bWasReleased[SI]) ReleaseHandCm[SI] = Hand;
		bWasReleased[SI] = bReleased;
		FVector A = Hand, B = St.AnchorNow() * 100.0;
		double Fade = 1.0, Wave = 0.0, Droop = 0.0, Curl = 0.0;
		if (St.bActive)
		{
			// shot: cubic ease-out extension, a decaying sine wave along the strand while it flies (web.js)
			const double U = FMath::Clamp(St.Age / FMath::Max(St.ShootDur, 0.01f), 0.0, 1.0);
			const double Ext = 1 - FMath::Pow(1 - U, 1.25);   // round 02: near-constant tip speed with a short ease at the end (the cubic put 27 % of the length in the first frame)
			B = A + (B - A) * Ext;
			Wave = 30.0 * FMath::Exp(-9.0 * St.Age) * (1 - St.Taut);
			if (St.Age > St.ShootDur) Wave *= FMath::Clamp(1.0 - (St.Age - St.ShootDur) / 0.08, 0.0, 1.0);   // round 01 (W6): straight within 0.10 s of the tip landing (0.08 s fade)
			if (bReleased)
			{ // round 09 (W8, critic r08: the strand's pixel length collapsed 950 -> 0 px in ~0.07 s at s1 t=4.85-4.92): the strand
			  // lets go of the anchor and shrinks back toward the hand over 0.36 s with an EASE-OUT profile -- fast while the far
			  // end is off-screen, slow while the endpoint crosses the frame near the hero (the r08 smoothstep's slow start spent
			  // 0.15 s off-screen and collapsed the visible length in 5 frames; an anchor-ward retract of the near end left the
			  // frame behind the lens in ~4 frames at 50 m/s). Slack sag from the first frames, fade 0.14 -> 0.38 s: length
			  // shrink >= 0.15 s AND alpha fade >= 0.15 s (both measurements of W8; drawn ~0.37 s <= 0.40).
			  // round 13 (critic r12, s4 t=15.75: the tail still collapsed 520 -> 0 px in 4 frames -- a release whose anchor sits
			  // behind the lens foreshortens the retract along the view axis): past R = 0.24 s the geometric shrink PINS at 89 %
			  // (a short slack stub at the hand) and the alpha fade alone carries the last 0.14 s, so the strand never vanishes
			  // by collapse; the slack sag now runs 0.30 s so the stub reads as a spent strand, not a cut.
				const double R = St.ReleaseT;
				const double X = FMath::Min(1.0, R / 0.36);
				double E = 1.0 - (1.0 - X) * (1.0 - X);
				if (R > 0.24) E = 0.889;
				A = Hand;                                   // stays near the hero (the camera tracks him: the retract must stay in view)
				B = Hand + (B - Hand) * (1.0 - E);
				Fade = FMath::Clamp(1.0 - (R - 0.14) / 0.24, 0.0, 1.0);
				Wave = 0.0;
				Droop = FMath::Min(180.0, 0.35 * FVector::Dist(A, B)) * FMath::Sin(PI * FMath::Min(1.0, R / 0.30));   // slack shows early
				Curl = 14.0 * (1.0 - E) * FMath::Sin(R * 30.0);
			}
		}
		const FVector D = B - A;
		const FVector Perp = FVector::CrossProduct(D.GetSafeNormal(), FVector::UpVector).GetSafeNormal();
		bool bPrefixHide = true;   // round 11: the lens-hide is a contiguous hand-end prefix rule (see below)
		for (int32 K = 0; K < SEGS_PER_STRAND; ++K)
		{
			UStaticMeshComponent* C = WebSegs[SI * SEGS_PER_STRAND + K];
			// r25 build 3: with RopeKeepProxy an unused segment stays "visible" at a 1e-4 scale instead of being hidden -- a segment
			// switched visible on the attach frame rendered one frame late (rope_r25_check: no strand in the frame of the first web_on row)
			auto HideSeg = [&](UStaticMeshComponent* Seg)
			{
				if (bTwoTone && Traversal->RopeKeepProxy > 0.5f) { Seg->SetWorldScale3D(FVector(1e-4)); Seg->SetVisibility(true); }
				else Seg->SetVisibility(false);
			};
			if (!St.bActive || Fade <= 0.01 || D.Size() < 5.0) { HideSeg(C); continue; }
			auto P = [&](double U)
			{
				const FVector Q = A + D * U;
				double Wv = Wave;
				// r25 build 4: the flying strand's wave is bounded on SCREEN (RopeWavePx at that point's distance): the 30 cm world wave
				// put the attach-frame strand 5-15 px off its hand -> anchor line (rope_r25_check, a 0.4 / 3.4 s)
				if (bTwoTone && Traversal->RopeWavePx >= 0.f) Wv = FMath::Min(Wv, double(Traversal->RopeWavePx) * FVector::Dist(Q, CamPosCm) / PxK);
				return Q + Perp * (Wv * FMath::Sin(U * PI * 3 + St.Age * 40.0) * FMath::Sin(U * PI) + Curl * FMath::Sin(U * PI * 2.0)) - FVector(0, 0, Droop * FMath::Sin(U * PI));
			};
			const double U0 = FMath::Pow(double(K) / SEGS_PER_STRAND, 1.6), U1 = FMath::Pow(double(K + 1) / SEGS_PER_STRAND, 1.6);   // round 01: short segments at the hand end (the camera is nearest there; the lens-hide must not take the strand start)
			const FVector P0 = P(U0), P1 = P(U1);
			const FVector Mid = (P0 + P1) * 0.5;
			const double Len = FVector::Dist(P0, P1);
			// round 08 (critic r07: thick blooming beam): world width 1.2 cm, never thinner than ~1.2 px at 1080p
			const double CamD = FVector::Dist(Mid, CamPosCm);
			{ // never draw a strand segment on the lens (round 01: the nearest point of the segment, 1.2 m; the segments are up to 4 m long, the midpoint test hid the hand end)
			  // round 11 (critic r10 gap 1, orchestrator-verified on s2 t=2.76-2.80: the strand read as a mid-air segment starting
			  // 70-87 px off the palm): hiding ANY segment inside the zone punched holes mid-strand (a drawn hand stub, then a gap,
			  // then the rest), and during the shot's flight it detached the growing strand from the palm. Now the hide applies only
			  // as a CONTIGUOUS prefix from the hand end -- once a segment is drawn every later segment draws too (no mid-air holes);
			  // and while the shot flies the zone shrinks 120 -> 45 cm so the strand reads hand->tip on every flight frame. The width
			  // is screen-space clamped either way, so a near-lens pass is a thin line, never a blob.
				const double HideR = bInFlight ? 45.0 : 120.0;
				const FVector Sg = P1 - P0; const double SgL2 = FMath::Max(Sg.SizeSquared(), 1.0);
				const double Tn = FMath::Clamp(FVector::DotProduct(CamPosCm - P0, Sg) / SgL2, 0.0, 1.0);
				if (bPrefixHide && FVector::Dist(CamPosCm, P0 + Sg * Tn) < HideR) { HideSeg(C); continue; }
				bPrefixHide = false;
			}
			double W = FMath::Max(1.6, 0.0025 * CamD) * Fade; // round 09: 1.6 cm, >= ~2 px at 1080p (TRAVERSAL-SPEC T6: 2-4 px)
			if (bTwoTone)
			{ // round 25: 1.6 cm world width, clamped to RopePxMin..RopePxMax px on screen (at the segment's distance); a released strand
				// thins out by the fade as before
				const double Px = FMath::Clamp(1.6 * PxK / CamD, double(Traversal->RopePxMin), double(FMath::Max(Traversal->RopePxMin, Traversal->RopePxMax))) * FMath::Lerp(1.0, 0.72, 0.5 * (U0 + U1));   // round 01 (W5): taper toward the anchor; round 08: 0.62 -> 0.72 (the measured width halo adds ~0.5-0.9 px over the drawn one; the far end must stay >= 2 px)
				W = Px * CamD / PxK * Fade;
			}
			C->SetWorldLocationAndRotation(Mid, FRotationMatrix::MakeFromZ((P1 - P0).GetSafeNormal()).ToQuat());
			C->SetWorldScale3D(FVector(W / 100.0, W / 100.0, Len / 100.0));
			C->SetVisibility(true);
			{ // round 12 (critic r11 gap 1, s2_c1 t=2.5-2.9: a dark corner fin sits between the CAMERA and the strand's
			  // near-hand stretch -- telemetry hand->anchor clear=1.0, so this is render-depth occlusion, and the strand
			  // reads detached from the palm for ~0.3 s): the first ~2 m from the hand render in the FOREGROUND depth
			  // group (depth-tested only against other foreground primitives), so a foreground edge can never sever the
			  // strand from the palm. W7's anchor filter keeps the hand->anchor line clear of geometry by design, so the
			  // foreground pass only ever restores a stretch the anchor search already proved clear; the width keeps its
			  // screen-space clamp, so this never reads as a beam over the lens.
				const int8 WantDpg = D.Size() * U0 <= 200.0 ? 1 : 0;
				const int32 SegI = SI * SEGS_PER_STRAND + K;
				if (WebSegDpg[SegI] != WantDpg)
				{
					WebSegDpg[SegI] = WantDpg;
					C->SetDepthPriorityGroup(WantDpg ? ESceneDepthPriorityGroup::SDPG_Foreground : ESceneDepthPriorityGroup::SDPG_World);
				}
			}
			if (!bRopeDrawn[SI]) { RopeDrawA[SI] = P0; RopeDrawWA[SI] = W; bRopeDrawn[SI] = true; }
			RopeDrawB[SI] = P1; RopeDrawWB[SI] = W;
		}
		if (bTwoTone && bRopeDrawn[SI])
		{ // final round 13 (critic r12 gap 1: the strand beaded / flickered in daylight -- the background luminance was evaluated
		  // PER PIXEL, so a mixed facade flipped the core share fragment-by-fragment): the material now samples the scene colour
		  // at two FIXED screen points along the drawn strand (35 % / 70 % hand -> anchor), pushed here per strand per frame, so
		  // the tone is one value for the whole strand and evolves smoothly (uniform line, no dashes, no frame flicker)
			const FRotationMatrix RM(Cam.CamRot);
			const FVector CF = RM.GetUnitAxis(EAxis::X), CR = RM.GetUnitAxis(EAxis::Y), CU = RM.GetUnitAxis(EAxis::Z);
			const double TV = FMath::Tan(FMath::DegreesToRadians(FMath::Clamp(double(Cam.OutVFov), 20.0, 150.0) * 0.5));
			auto PushUV = [&](double U, const TCHAR* Name)
			{
				const FVector Rel = FMath::Lerp(RopeDrawA[SI], RopeDrawB[SI], U) / 100.0 - Cam.CamPos;
				const double Z = FVector::DotProduct(Rel, CF);
				if (Z < 0.3) return;   // behind / on the lens: keep last frame's sample point
				const double Ux = FMath::Clamp(0.5 + 0.5 * FVector::DotProduct(Rel, CR) / (Z * TV * Aspect), 0.0, 1.0);
				const double Uy = FMath::Clamp(0.5 - 0.5 * FVector::DotProduct(Rel, CU) / (Z * TV), 0.0, 1.0);
				WebMatTwoTone[SI]->SetVectorParameterValue(Name, FLinearColor(float(Ux), float(Uy), 0.f, 0.f));
			};
			PushUV(0.35, TEXT("BgUV0"));
			PushUV(0.70, TEXT("BgUV1"));
		}
	}
}

void AWebTravCharacter::ReadHeroMask()
{
	PxTop = PxBottom = PxLeft = PxRight = -1.f; WallFrac = HeroOccl = -1.f; VisTop = VisBottom = -1.f; VisPx = -1;
	if (!MaskRT) return;
	FTextureRenderTargetResource* Res = MaskRT->GameThread_GetRenderTargetResource();
	if (!Res) return;
	TArray<FLinearColor> Px;
	if (!Res->ReadLinearColorPixels(Px) || Px.Num() != 480 * 270) return;
	// round 08: near-wall share (non-hero pixels whose scene depth < 6 m) and hero occlusion (hero pixels with something
	// > 0.3 m in front of the hero surface)
	if (SceneRT)
	{
		if (FTextureRenderTargetResource* SR = SceneRT->GameThread_GetRenderTargetResource())
		{
			TArray<FLinearColor> Sc;
			if (SR->ReadLinearColorPixels(Sc) && Sc.Num() == Px.Num())
			{
				int32 Near = 0, NonHero = 0, Hero = 0, Occ = 0;
				// view rays of the capture camera: a near pixel whose world point lies on the street (z < 0.4 m) is floor, not
				// a facade, and is not counted
				const FRotationMatrix RM(Cam.CamRot);
				const FVector CF = RM.GetUnitAxis(EAxis::X), CR = RM.GetUnitAxis(EAxis::Y), CU = RM.GetUnitAxis(EAxis::Z);
				const double TV = FMath::Tan(FMath::DegreesToRadians(Cam.OutVFov * 0.5)), TH = TV * 480.0 / 270.0;
				for (int32 K = 0; K < Px.Num(); ++K)
				{
					const float HD = Px[K].R, SD = Sc[K].R;
					if (HD < 20000.f)
					{
						++Hero;
						if (SD < HD - 30.f) ++Occ;
						else
						{ // round 20 (critic r19: "telemetry bbox .25 while a parapet hides all but the shoulders"): bbox of the VISIBLE hero pixels
							const float Yp = float(K / 480);
							VisTop = VisTop < 0.f ? Yp * 4.f : FMath::Min(VisTop, Yp * 4.f); VisBottom = FMath::Max(VisBottom, (Yp + 1.f) * 4.f);
						}
						continue;
					}
					++NonHero;
					if (SD >= 600.f) continue;
					const double U = ((K % 480) + 0.5) / 480.0 * 2.0 - 1.0, V = 1.0 - ((K / 480) + 0.5) / 270.0 * 2.0;
					const double WZ = Cam.CamPos.Z + (CF.Z + CR.Z * U * TH + CU.Z * V * TV) * SD / 100.0;
					if (WZ > 0.4) ++Near;
				}
				WallFrac = float(Near) / float(FMath::Max(1, Px.Num()));
				HeroOccl = Hero > 0 ? float(Occ) / float(Hero) : 1.f;
				VisPx = (Hero - Occ) * 16; // in 1920x1080 pixels
			}
		}
	}
	int32 Y0 = 9999, Y1 = -1, X0 = 9999, X1 = -1;
	for (int32 Y = 0; Y < 270; ++Y)
	{
		for (int32 X = 0; X < 480; ++X)
		{
			if (Px[Y * 480 + X].R < 20000.f) { Y0 = FMath::Min(Y0, Y); Y1 = FMath::Max(Y1, Y); X0 = FMath::Min(X0, X); X1 = FMath::Max(X1, X); }
		}
	}
	if (Y1 >= 0) { PxTop = Y0 * 4.f; PxBottom = (Y1 + 1) * 4.f; PxLeft = X0 * 4.f; PxRight = (X1 + 1) * 4.f; } // 1920x1080 pixels
	HeroSil = TEXT("0");
	if (Y1 >= 0)
	{ // 16x16 occupancy grid over the bbox (a cell is set when >= 30 % of its mask pixels are hero)
		const int32 BW = X1 - X0 + 1, BH = Y1 - Y0 + 1;
		uint8 Bits[256]; FMemory::Memzero(Bits);
		for (int32 Gy = 0; Gy < 16; ++Gy)
			for (int32 Gx = 0; Gx < 16; ++Gx)
			{
				const int32 xa = X0 + Gx * BW / 16, xb = FMath::Max(xa + 1, X0 + (Gx + 1) * BW / 16), ya = Y0 + Gy * BH / 16, yb = FMath::Max(ya + 1, Y0 + (Gy + 1) * BH / 16);
				int32 N = 0, H = 0;
				for (int32 Y = ya; Y < yb && Y < 270; ++Y) for (int32 X = xa; X < xb && X < 480; ++X) { ++N; if (Px[Y * 480 + X].R < 20000.f) ++H; }
				Bits[Gy * 16 + Gx] = (N > 0 && H * 10 >= N * 3) ? 1 : 0;
			}
		HeroSil.Empty();
		for (int32 K = 0; K < 256; K += 4) HeroSil += FString::Printf(TEXT("%x"), Bits[K] * 8 + Bits[K + 1] * 4 + Bits[K + 2] * 2 + Bits[K + 3]);
	}
}

// final loop round 00 (W / A checkers): strand state, the strand as drawn this frame (start = the hand read in UpdateWebs, tip), the hand and shoulder bones as the
// mesh holds them at telemetry time (= the pose of the previous frame: the anim instance evaluates after the actor tick), and the chest angular rate. Read-only.
FString AWebTravCharacter::FinalSwingCols(double T)
{
	USkeletalMeshComponent* M = bHeroMesh ? GetMesh() : nullptr;
	if (M && !bFwBones)
	{
		bFwBones = true;
		FString All;
		auto Find = [&](std::initializer_list<const TCHAR*> Needles) -> FName
		{
			for (const TCHAR* N : Needles) for (int32 B = 0; B < M->GetNumBones(); ++B) { const FString Nm = M->GetBoneName(B).ToString().ToLower(); if (Nm == N) return M->GetBoneName(B); }
			return NAME_None;
		};
		for (int32 B = 0; B < M->GetNumBones(); ++B) All += M->GetBoneName(B).ToString() + TEXT(" ");
		FwShoulder[0] = Find({ TEXT("upperarm_l"), TEXT("arm_l"), TEXT("shoulder_l") }); FwShoulder[1] = Find({ TEXT("upperarm_r"), TEXT("arm_r"), TEXT("shoulder_r") });
		FwChest = Find({ TEXT("spine2"), TEXT("spine_03"), TEXT("spine03"), TEXT("chest") });
		UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV final bones: shoulder L=%s R=%s chest=%s; all: %s"), *FwShoulder[0].ToString(), *FwShoulder[1].ToString(), *FwChest.ToString(), *All);
	}
	auto V3 = [](const FVector& Cm) { return FString::Printf(TEXT("%.4f,%.4f,%.4f"), Cm.X / 100.0, Cm.Y / 100.0, Cm.Z / 100.0); };
	FString O;
	for (int32 SI = 0; SI < 2; ++SI)
	{
		const FWebTravStrand& St = Traversal->Strands[SI];
		const double U = St.bActive ? FMath::Clamp(double(St.Age) / FMath::Max(double(St.ShootDur), 0.01), 0.0, 1.0) : 0.0;
		double Wave0 = St.bActive ? 30.0 * FMath::Exp(-9.0 * St.Age) * (1.0 - St.Taut) : 0.0;
		if (St.Age > St.ShootDur) Wave0 *= FMath::Clamp(1.0 - (St.Age - St.ShootDur) / 0.08, 0.0, 1.0);
		if (St.bActive && St.ReleaseT >= 0.f) Wave0 = 0.0;
		const double Clear = bRopeDrawn[SI] ? Traversal->StrandClearFraction(RopeDrawA[SI] / 100.0, St.Anchor) : 1.0;
		O += FString::Printf(TEXT(",%d,%d,%.4f,%.4f,%.4f,%d,%s,%s,%s,%.3f,%.2f,%.3f"), St.bActive ? 1 : 0, St.bRightHand ? 1 : 0, St.Age, St.ShootDur, St.ReleaseT, bRopeDrawn[SI] ? 1 : 0,
			*V3(St.Anchor * 100.0), bRopeDrawn[SI] ? *V3(RopeDrawA[SI]) : TEXT("0,0,0"), bRopeDrawn[SI] ? *V3(RopeDrawB[SI]) : TEXT("0,0,0"), St.Taut, Wave0, Clear);
		(void)U;
	}
	if (M)
	{
		O += TEXT(",") + V3(M->GetBoneLocation(FName(TEXT("hand_L")))) + TEXT(",") + V3(M->GetBoneLocation(FName(TEXT("hand_R"))));
		O += TEXT(",") + V3(FwShoulder[0].IsNone() ? FVector::ZeroVector : M->GetBoneLocation(FwShoulder[0])) + TEXT(",") + V3(FwShoulder[1].IsNone() ? FVector::ZeroVector : M->GetBoneLocation(FwShoulder[1]));
		double Rate = 0.0;
		if (!FwChest.IsNone())
		{
			const FQuat Q = M->GetBoneQuaternion(FwChest, EBoneSpaces::WorldSpace);
			if (FwChestHas && T > FwChestPrevT + 1e-6) Rate = FMath::RadiansToDegrees(FwChestPrev.AngularDistance(Q)) / (T - FwChestPrevT);
			FwChestPrev = Q; FwChestPrevT = T; FwChestHas = true;
		}
		O += FString::Printf(TEXT(",%.1f"), Rate);
		O += TEXT(",") + V3(PalmWorldCm(false)) + TEXT(",") + V3(PalmWorldCm(true));   // the palms of the final pose
		O += FString::Printf(TEXT(",%.3f"), Traversal->Anim.NoAnchorT);   // the no-anchor reach gesture clock (< 0 none)
		O += TEXT(",") + (HeroSil.IsEmpty() ? FString(TEXT("0")) : HeroSil);
	}
	else O += TEXT(",0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0");
	return O;
}

double AWebTravCharacter::ProjectHeroH() const
{
	if (!bHeroMesh || !GetMesh()) return -1.0;
	const FRotationMatrix RM(Cam.CamRot);
	const FVector CF = RM.GetUnitAxis(EAxis::X), CU = RM.GetUnitAxis(EAxis::Z);
	const double TV = FMath::Tan(FMath::DegreesToRadians(FMath::Max(10.0, Cam.OutVFov) * 0.5));
	double MinY = 1e9, MaxY = -1e9;
	const USkeletalMeshComponent* M = GetMesh();
	for (int32 Bi = 0; Bi < M->GetNumBones(); ++Bi)
	{
		const FVector BP = M->GetBoneLocation(M->GetBoneName(Bi));
		for (int32 K = 0; K < 8; ++K)
		{
			const FVector Corner(BP.X + ((K & 1) ? 10.0 : -10.0), BP.Y + ((K & 2) ? 10.0 : -10.0), BP.Z + ((K & 4) ? 10.0 : -10.0));
			const FVector Rel = Corner / 100.0 - Cam.CamPos;
			const double Z = FVector::DotProduct(Rel, CF);
			if (Z < 0.3) return -1.0;
			const double SY = 0.5 - 0.5 * FVector::DotProduct(Rel, CU) / (Z * TV);
			MinY = FMath::Min(MinY, SY); MaxY = FMath::Max(MaxY, SY);
		}
	}
	return MaxY - MinY;
}

FString AWebTravCharacter::BuildCols25()
{
	// round 25: the drawn strand (the longer one when two are drawn) projected through the final camera: hand end A / far end B in normalized
	// screen coordinates (0..1, may lie outside the frame; B clipped to the near plane), and the strand width in px at each end (viewport
	// height), plus the rope look (1 = two-tone) and the perch yaw hold flag of the camera
	FString Cols25 = TEXT(",0,-1,-1,-1,-1,-1,-1");
	{
		int32 Best = -1; double BestL = 0.0;
		for (int32 SI = 0; SI < 2; ++SI) { if (bRopeDrawn[SI]) { const double L = FVector::Dist(RopeDrawA[SI], RopeDrawB[SI]); if (L > BestL) { BestL = L; Best = SI; } } }
		if (Best >= 0)
		{
			const FRotationMatrix RM(Cam.CamRot);
			const FVector CF = RM.GetUnitAxis(EAxis::X), CR = RM.GetUnitAxis(EAxis::Y), CU = RM.GetUnitAxis(EAxis::Z);
			const double TV = FMath::Tan(FMath::DegreesToRadians(Cam.OutVFov * 0.5));
			double Aspect = 16.0 / 9.0, ViewH = 1080.0;
			if (GEngine && GEngine->GameViewport && GEngine->GameViewport->Viewport)
			{
				const FIntPoint Sz = GEngine->GameViewport->Viewport->GetSizeXY();
				if (Sz.X > 0 && Sz.Y > 0) { Aspect = double(Sz.X) / double(Sz.Y); ViewH = double(Sz.Y); }
			}
			FVector RA = RopeDrawA[Best] / 100.0 - Cam.CamPos, RB = RopeDrawB[Best] / 100.0 - Cam.CamPos;
			double ZA = FVector::DotProduct(RA, CF), ZB = FVector::DotProduct(RB, CF);
			if (ZA < 0.05 && ZB >= 0.05) { RA = RA + (RB - RA) * ((0.05 - ZA) / (ZB - ZA)); ZA = 0.05; }
			if (ZB < 0.05 && ZA >= 0.05) { RB = RA + (RB - RA) * ((ZA - 0.05) / (ZA - ZB)); ZB = 0.05; }
			if (ZA >= 0.05 && ZB >= 0.05)
			{
				auto SX = [&](const FVector& R, double Z) { return 0.5 + 0.5 * FVector::DotProduct(R, CR) / (Z * TV * Aspect); };
				auto SY = [&](const FVector& R, double Z) { return 0.5 - 0.5 * FVector::DotProduct(R, CU) / (Z * TV); };
				const double PxK = ViewH / (2.0 * TV);
				Cols25 = FString::Printf(TEXT(",%d,%.5f,%.5f,%.5f,%.5f,%.2f,%.2f"), int32(bRopeDrawn[0]) + int32(bRopeDrawn[1]), SX(RA, ZA), SY(RA, ZA), SX(RB, ZB), SY(RB, ZB),
					RopeDrawWA[Best] / 100.0 / FMath::Max(0.05, ZA) * PxK, RopeDrawWB[Best] / 100.0 / FMath::Max(0.05, ZB) * PxK);
			}
		}
	}
	Cols25 += FString::Printf(TEXT(",%d,%d"), WebLookNow, Cam.PerchYawHeld);
	return Cols25;
}

void AWebTravCharacter::PushTelemetry(double T, const FWebTravInput& I)
{
	UWebTravScript* Script = GetGameInstance()->GetSubsystem<UWebTravScript>();
	Script->SetTelemetryHeader(TEXT("frame,t,mode,sub,x_m,y_m,z_m,vx,vy,vz,speed_mps,hspeed_mps,height_above_floor_m,anchor_x,anchor_y,anchor_z,")
		TEXT("rope_m,tension,chain,trick,zip_target,zt_x,zt_y,zt_z,cam_x,cam_y,cam_z,cam_yaw_deg,cam_pitch_deg,cam_vfov_deg,cam_dist_m,motion_blur,")
		TEXT("in_move_x,in_move_y,in_swing,in_jump,in_sprint,in_zip,in_drop,in_quick,cam_orbit_pitch_deg,cam_auto_pitch_deg,cam_occ_hold,")
		TEXT("hero_bbox_h,hero_bbox_w,hero_cy,hero_in_frame,cam_hero_dist_m,cam_in_geometry,frame_s_target,in_trick,")
		TEXT("anim_node,anim_clip,anim_weight,air_flavor,pose_sig,pcm_x,pcm_y,pcm_z,pcm_pitch,pcm_yaw,pcm_fov,px_top,px_bottom,px_left,px_right,head_hip_dz,limb_z,body_rope_deg,web_on,wall_frac,hero_occl,hero_cx,pcm_roll,")
		TEXT("flip_prog,flip_t,flip_pitch_deg,flip_twist_deg,flip_rate_dps,flip_shape,flip_shape_legs,body_axis_deg,body_pitch_deg,body_roll_deg,flip_armed,flipcam_k,flipcam_yaw_deg,flipcam_elev_deg,flipcam_sky,sky_tall_m,sky_peak_want_m,cam_slew,hero_fill_cd,flipcam_sun_deg,view_sun_deg,flow_roof_m,flow_rise_m,flipcam_glare,flipcam_dist_m,flipcam_tier,flipcam_abort,flipcam_zk,cam_lens25,flow_apex_want_z,flow_gap_m,")
		TEXT("in_cap,vp_cap,vp_focus,look_px,ground_src,wall_ik_w,gait_ph,swing_leg_w,tuck_w,tuck_wrist_shin_m,tuck_knee_gap_m,flip_scale,foot_wall_l,foot_wall_r,hand_wall_l,hand_wall_r,zip_why,")
		TEXT("body_vel_deg,body_wallup_deg,cam_enclosed,vis_pts,vis_up_m,setbacks,topouts,tunnel_stops,cam_slew8,zip_reach_w,solid_mode,")
		TEXT("flip_cancels,air_fast_w,air_track_k,hero_vis_top,hero_vis_bottom,hero_vis_px,")
		TEXT("foot_sep_run_m,knee_gap_lat_m,knee_wall_l,knee_wall_r,limb_wall_max_m,body_run_elev_deg,")
		TEXT("torso_wallup_deg,chest_run_deg,side_up_k,ankle_sep_plane_m,hip_wall_m,ankle_sep_3d_m,alt_apex_want_m,cam_look_dir,cam_gnd_crane_m,cam_gnd_stop,")
		TEXT("rope_drawn,rope_ax,rope_ay,rope_bx,rope_by,rope_wpx_a,rope_wpx_b,rope_look,cam_perch_hold,")
		TEXT("fw_s0_on,fw_s0_hand,fw_s0_age,fw_s0_shoot,fw_s0_rel,fw_s0_drawn,fw_s0_ax,fw_s0_ay,fw_s0_az,fw_s0_sx,fw_s0_sy,fw_s0_sz,fw_s0_tx,fw_s0_ty,fw_s0_tz,fw_s0_taut,fw_s0_wave_cm,fw_s0_clear,")
		TEXT("fw_s1_on,fw_s1_hand,fw_s1_age,fw_s1_shoot,fw_s1_rel,fw_s1_drawn,fw_s1_ax,fw_s1_ay,fw_s1_az,fw_s1_sx,fw_s1_sy,fw_s1_sz,fw_s1_tx,fw_s1_ty,fw_s1_tz,fw_s1_taut,fw_s1_wave_cm,fw_s1_clear,")
		TEXT("fw_hl_x,fw_hl_y,fw_hl_z,fw_hr_x,fw_hr_y,fw_hr_z,fw_shl_x,fw_shl_y,fw_shl_z,fw_shr_x,fw_shr_y,fw_shr_z,fw_chest_rate_dps,fw_pl_x,fw_pl_y,fw_pl_z,fw_pr_x,fw_pr_y,fw_pr_z,fw_reach_t,hero_sil"));
	const FVector P = Traversal->PosM(), V = Traversal->VelM();
	const bool bSw = Traversal->IsSwinging();
	const FVector An = bSw ? Traversal->SwingAnchor() : FVector::ZeroVector;
	const FWebTravAnim& A = Traversal->Anim;
	// hero screen-space box: corners of every placeholder part's bounds projected through the final camera
	double MinX = 1e9, MaxX = -1e9, MinY = 1e9, MaxY = -1e9;
	bool bBehind = false;
	{
		const FRotationMatrix RM(Cam.CamRot);
		const FVector CF = RM.GetUnitAxis(EAxis::X), CR = RM.GetUnitAxis(EAxis::Y), CU = RM.GetUnitAxis(EAxis::Z);
		const double TV = FMath::Tan(FMath::DegreesToRadians(Cam.OutVFov * 0.5));
		double Aspect = 16.0 / 9.0;
		if (GEngine && GEngine->GameViewport && GEngine->GameViewport->Viewport)
		{
			const FIntPoint Sz = GEngine->GameViewport->Viewport->GetSizeXY();
			if (Sz.X > 0 && Sz.Y > 0) Aspect = double(Sz.X) / double(Sz.Y);
		}
		const FVector CP = Cam.CamPos;
		TArray<FBox> Boxes;
		if (bHeroMesh)
		{ // bone positions padded by 10 cm (limb thickness)
			const USkeletalMeshComponent* M = GetMesh();
			for (int32 Bi = 0; Bi < M->GetNumBones(); ++Bi)
			{
				const FVector BP = M->GetBoneLocation(M->GetBoneName(Bi));
				Boxes.Add(FBox(BP - FVector(10), BP + FVector(10)));
			}
		}
		else { for (const UStaticMeshComponent* C : FigureParts) { if (C) Boxes.Add(C->Bounds.GetBox()); } }
		for (const FBox& B : Boxes)
		{
			for (int32 K = 0; K < 8; ++K)
			{
				const FVector Corner((K & 1) ? B.Max.X : B.Min.X, (K & 2) ? B.Max.Y : B.Min.Y, (K & 4) ? B.Max.Z : B.Min.Z);
				const FVector Rel = Corner / 100.0 - CP;
				const double Z = FVector::DotProduct(Rel, CF);
				if (Z < 0.05) { bBehind = true; continue; }
				const double SX = 0.5 + 0.5 * FVector::DotProduct(Rel, CR) / (Z * TV * Aspect);
				const double SY = 0.5 - 0.5 * FVector::DotProduct(Rel, CU) / (Z * TV);
				MinX = FMath::Min(MinX, SX); MaxX = FMath::Max(MaxX, SX); MinY = FMath::Min(MinY, SY); MaxY = FMath::Max(MaxY, SY);
			}
		}
	}
	const bool bInFrame = !bBehind && MinX >= 0 && MaxX <= 1 && MinY >= 0 && MaxY <= 1;
	// pose signature: head / hands / feet relative to the hips, in camera right / up (m) — screen silhouette proxy
	FString Node = TEXT("none"), ClipN = TEXT("none"), Sig, LimbZ;
	double HeadHipDz = 0.0, BodyRope = -1.0;
	float AW = 0.f; int32 Flav = -1;
	if (bHeroMesh)
	{
		const USkeletalMeshComponent* M = GetMesh();
		if (const UWebTravAnimInstance* AI = Cast<UWebTravAnimInstance>(M->GetAnimInstance()))
		{
			Node = AI->CurrentNode().ToString(); ClipN = AI->DominantClip().ToString(); AW = AI->TotalClipWeight(); Flav = AI->AirFlavor();
		}
		const FRotationMatrix RM(Cam.CamRot);
		const FVector CR = RM.GetUnitAxis(EAxis::Y), CU = RM.GetUnitAxis(EAxis::Z);
		const FVector Hip = M->GetBoneLocation(TEXT("hips"));
		for (const TCHAR* Bn : { TEXT("head"), TEXT("hand_L"), TEXT("hand_R"), TEXT("foot_L"), TEXT("foot_R") })
		{
			const FVector D = (M->GetBoneLocation(FName(Bn)) - Hip) / 100.0;
			Sig += FString::Printf(TEXT("%s%.3f %.3f"), Sig.IsEmpty() ? TEXT("") : TEXT(" "), FVector::DotProduct(D, CR), FVector::DotProduct(D, CU));
		}
		// round 06: world-up offsets from the hips (m): head, and hands / feet (limb phase on a wall = their order up the wall)
		HeadHipDz = (M->GetBoneLocation(TEXT("head")).Z - Hip.Z) / 100.0;
		// round 07: body axis (hips -> head) vs the web (hips -> anchor), degrees, while swinging
		if (bSw)
		{
			const FVector BodyAx = (M->GetBoneLocation(TEXT("head")) - Hip).GetSafeNormal(), RopeAx = (An * 100.0 - Hip).GetSafeNormal();
			BodyRope = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FVector::DotProduct(BodyAx, RopeAx), -1.0, 1.0)));
		}
		for (const TCHAR* Bn : { TEXT("hand_L"), TEXT("hand_R"), TEXT("foot_L"), TEXT("foot_R") })
		{
			LimbZ += FString::Printf(TEXT("%s%.3f"), LimbZ.IsEmpty() ? TEXT("") : TEXT(" "), (M->GetBoneLocation(FName(Bn)).Z - Hip.Z) / 100.0);
		}
	}
	// round 11: flip program state + the RENDERED body axis from the bones (hips -> head): angle from world up (0..180), and the
	// signed pitch of that axis in the facing plane (+ = head forward) and roll in the lateral plane
	double BodyAxis = -1.0, BodyPitch = 0.0, BodyRoll = 0.0;
	if (bHeroMesh)
	{
		const USkeletalMeshComponent* M = GetMesh();
		const FVector Ax = (M->GetBoneLocation(TEXT("head")) - M->GetBoneLocation(TEXT("hips"))).GetSafeNormal();
		const double Fy = FMath::DegreesToRadians(A.FacingDeg);
		const FVector Fw(FMath::Cos(Fy), FMath::Sin(Fy), 0.0), Rt(-FMath::Sin(Fy), FMath::Cos(Fy), 0.0);
		BodyAxis = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(Ax.Z, -1.0, 1.0)));
		// round 11 (r10 NOTES: rudi's 1964 deg/s rendered "peak" at flip_t 0.13-0.17 is a measurement artifact): the pitch reading
		// atan2(Ax.Fw, Ax.Z) is singular where the body axis points along +/- Rt (a fast twist carrying the body through the banked
		// sideways-horizontal cone): atan2(~0, ~0) flips ~180 deg in 1-2 frames while the true axis rate is ~700 deg/s. Inside the
		// cone the facing-plane pitch is ill-defined, so hold the last pre-cone reading; the series stays continuous through it.
		const double LatA = FVector::DotProduct(Ax, Rt);
		if (FMath::Abs(LatA) > 0.97 && bBodyPitchHold) BodyPitch = BodyPitchHold;
		else { BodyPitch = FMath::RadiansToDegrees(FMath::Atan2(FVector::DotProduct(Ax, Fw), Ax.Z)); BodyPitchHold = BodyPitch; bBodyPitchHold = true; }
		BodyRoll = FMath::RadiansToDegrees(FMath::Atan2(FVector::DotProduct(Ax, Rt), Ax.Z));
	}
	float FlipTNow = 0.f;
	const bool bFlipNow = FlipProgramNow(FlipTNow) != nullptr && LastFlip.bValid;
	const FString FlipCols = FString::Printf(TEXT("%s,%.3f,%.1f,%.1f,%.1f,%s,%s,%.1f,%.1f,%.1f"),
		bFlipNow ? *LastFlipName.ToString() : TEXT(""), bFlipNow ? FlipTNow : -1.f, bFlipNow ? LastFlip.PitchDeg : 0.f, bFlipNow ? LastFlip.TwistDeg : 0.f,
		bFlipNow ? LastFlip.PitchRate : 0.f,
		bFlipNow ? (LastFlip.W < 0.5f ? WebFlips::ShapeName(LastFlip.A) : WebFlips::ShapeName(LastFlip.B)) : TEXT(""),
		bFlipNow ? (LastFlip.LW < 0.5f ? WebFlips::ShapeName(LastFlip.LA) : WebFlips::ShapeName(LastFlip.LB)) : TEXT(""),
		BodyAxis, BodyPitch, BodyRoll);
	// the camera the engine actually rendered with (player camera manager cache)
	FVector PcmLoc = FVector::ZeroVector; FRotator PcmRot = FRotator::ZeroRotator; float PcmFov = 0.f;
	if (const APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		if (PC->PlayerCameraManager) { PcmLoc = PC->PlayerCameraManager->GetCameraLocation(); PcmRot = PC->PlayerCameraManager->GetCameraRotation(); PcmFov = PC->PlayerCameraManager->GetFOVAngle(); }
	}
	const FString Row = FString::Printf(
		TEXT("%lld,%.4f,%s,%s,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.2f,%.2f,%.2f,%.2f,%.3f,%d,%s,%d,%.2f,%.2f,%.2f,%.3f,%.3f,%.3f,%.2f,%.2f,%.2f,%.3f,%.3f,%.2f,%.2f,%d,%d,%d,%d,%d,%d,%.2f,%.2f,%.2f,%.4f,%.4f,%.4f,%d,%.3f,%d,%.3f,%d,%s,%s,%.3f,%d,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.0f,%.0f,%.0f,%.0f,%.3f,%s,%.1f,%d,%.3f,%.3f,%.4f,%.2f"),
		FrameIndex, T, ModeName(A.Mode), *A.Sub.ToString(), P.X, P.Y, P.Z, V.X, V.Y, V.Z, V.Size(), FVector2D(V.X, V.Y).Size(),
		P.Z - UWebTraversalComponent::H - Traversal->FloorBelow(), An.X, An.Y, An.Z, bSw ? Traversal->SwingRope() : 0.0, bSw ? Traversal->SwingTension() : 0.0,
		Traversal->Chain(), A.Trick.IsNone() ? TEXT("") : *A.Trick.ToString(), Traversal->HasZipTarget() ? 1 : 0,
		Traversal->ZipTargetPos().X, Traversal->ZipTargetPos().Y, Traversal->ZipTargetPos().Z,
		Cam.CamPos.X, Cam.CamPos.Y, Cam.CamPos.Z, Cam.CamRot.Yaw, Cam.CamRot.Pitch, Cam.OutVFov, FVector::Dist(Cam.CamPos, P), Cam.MotionBlur,
		I.Move.X, I.Move.Y, I.bSwing ? 1 : 0, I.bJump ? 1 : 0, I.bSprint ? 1 : 0, I.bZip ? 1 : 0, I.bDrop ? 1 : 0, I.bQuick ? 1 : 0,
		-FMath::RadiansToDegrees(Cam.Pitch), -FMath::RadiansToDegrees(Cam.DebugAutoPitch()), Cam.DebugOccHold(),
		bBehind ? 1.0 : MaxY - MinY, bBehind ? 1.0 : MaxX - MinX, bBehind ? -1.0 : 0.5 * (MinY + MaxY), bInFrame ? 1 : 0, Cam.HeroDist,
		Cam.bCamInGeometry ? 1 : 0, Cam.FrameS, I.bTrick ? 1 : 0, *Node, *ClipN, AW, Flav, *Sig,
		PcmLoc.X / 100.0, PcmLoc.Y / 100.0, PcmLoc.Z / 100.0, PcmRot.Pitch, PcmRot.Yaw, PcmFov, PxTop, PxBottom, PxLeft, PxRight,
		HeadHipDz, LimbZ.IsEmpty() ? TEXT("-") : *LimbZ, BodyRope,
		(Traversal->Strands[0].bActive && Traversal->Strands[0].ReleaseT < 0.f) || (Traversal->Strands[1].bActive && Traversal->Strands[1].ReleaseT < 0.f) ? 1 : 0, WallFrac, HeroOccl, bBehind ? -1.0 : 0.5 * (MinX + MaxX), PcmRot.Roll);
	// round 12: armed apex flip, flip camera view search (yaw offset from behind, elevation below the hero, ring sky share of the
	// chosen view), tallest roof near the last sky launch's flip and its solved peak (m over the street)
	// round 13: camera output slew-limit flags (1 position, 2 pitch, 4 yaw) and the hero fill light (cd)
	const FString Flip12 = FString::Printf(TEXT(",%s,%.3f,%.1f,%.1f,%.2f,%.1f,%.1f,%d,%.0f"),
		Traversal->IsFlipArmed() ? *Traversal->ArmedFlipName().ToString() : TEXT(""), Cam.FlipK,
		Cam.FlipOffDeg, FMath::RadiansToDegrees(FMath::Asin(FMath::Clamp(Cam.FlipDrop / FMath::Max(1.0, Cam.FlipDist), 0.0, 0.6))), Cam.FlipSkyShare,
		Traversal->SkyTallUsed, Traversal->SkyPeakWant, Cam.SlewFlags, HeroFill ? HeroFill->Intensity : 0.f);
	// round 15: sun angle of the searched flip view, sun angle of the RENDERED view (camera manager forward vs the direction to the sun;
	// -1 = no sun found), roofline (m over the street) and rise of the last flow flip
	const double ViewSun = Cam.bHaveSun ? FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FVector::DotProduct(PcmRot.Vector(), Cam.SunDir), -1.0, 1.0))) : -1.0;
	// round 16: trick camera distance after the dolly (m), selection tier (-1 none, 0 obstruction + sun ok, 1 sun rule failed, 2 pulled in, 3 plain chase), abort flag, height weight
	const FString Cols15 = FString::Printf(TEXT(",%.1f,%.1f,%.1f,%.1f,%.2f,%.2f,%d,%d,%.3f,%d"), Cam.FlipSunDeg, ViewSun, Traversal->FlowRoofUsed, Traversal->FlowRiseUsed, Cam.FlipGlare,
		Cam.FlipDistNow, Cam.FlipTier, Cam.bFlipAbort ? 1 : 0, Cam.FlipZK, Cam.bLensTouch ? 1 : 0);
	// round 17: apex hips Z the last flow flip was solved for (world m, 0 none) and the roofline gap now (target - hips, m; -999 no roof)
	const double Gap = Traversal->FlowApexGap();
	const FString Cols17 = FString::Printf(TEXT(",%.2f,%.2f"), Traversal->FlowApexWant, Gap < -1e8 ? -999.0 : Gap);
	// round 19: input / capture state, floor source, wall-run IK stride, swing leg shaping, tuck closure, flip variant, limb-to-wall gaps
	FString Cols19;
	{
		const AWebHomagePlayerController* WPC = Cast<AWebHomagePlayerController>(GetController());
		UGameViewportClient* GVC = GetWorld() ? GetWorld()->GetGameViewport() : nullptr;
		FViewport* VP = GVC ? GVC->Viewport : nullptr;
		float WallW = 0.f, GaitPh = 0.f, SwLeg = 0.f, TuckW = 0.f;
		double WristShin = -1.0, KneeGap = -1.0;
		double FootWall[2] = { -1.0, -1.0 }, HandWall[2] = { -1.0, -1.0 };
		if (bHeroMesh)
		{
			const USkeletalMeshComponent* M = GetMesh();
			if (const UWebTravAnimInstance* AI = Cast<UWebTravAnimInstance>(M->GetAnimInstance()))
			{
				WallW = AI->Frame.WallW; GaitPh = AI->Frame.GaitPh; SwLeg = AI->Frame.SwingLegW; TuckW = AI->Frame.TuckW;
			}
			const FVector KL = M->GetBoneLocation(TEXT("shin_L")), KR = M->GetBoneLocation(TEXT("shin_R"));
			const FVector AL = M->GetBoneLocation(TEXT("foot_L")), AR = M->GetBoneLocation(TEXT("foot_R"));
			KneeGap = FVector::Dist(KL, KR) / 100.0;
			auto SegDist = [](const FVector& P, const FVector& A0, const FVector& B0)
			{
				const FVector AB = B0 - A0;
				const double T = FMath::Clamp(FVector::DotProduct(P - A0, AB) / FMath::Max(AB.SizeSquared(), 1e-6), 0.0, 1.0);
				return FVector::Dist(P, A0 + AB * T) / 100.0;
			};
			const FVector WL = M->GetBoneLocation(TEXT("hand_L")), WR = M->GetBoneLocation(TEXT("hand_R"));
			WristShin = FMath::Max(FMath::Min(SegDist(WL, KL, AL), SegDist(WL, KR, AR)), FMath::Min(SegDist(WR, KR, AR), SegDist(WR, KL, AL)));
			if (A.Mode == EWebTravMode::Wall)
			{
				const FVector N = A.Wall.Normal, WP = A.Wall.Point;
				FootWall[0] = FVector::DotProduct(M->GetBoneLocation(TEXT("toe_L")) - WP, N) / 100.0;
				FootWall[1] = FVector::DotProduct(M->GetBoneLocation(TEXT("toe_R")) - WP, N) / 100.0;
				HandWall[0] = FVector::DotProduct(WL - WP, N) / 100.0;
				HandWall[1] = FVector::DotProduct(WR - WP, N) / 100.0;
			}
		}
		const FWebFlipProgram* FPv = (A.Sub == FName(TEXT("trick")) && !A.Trick.IsNone()) ? WebFlips::Find(A.Trick) : nullptr;
		Cols19 = FString::Printf(TEXT(",%d,%d,%d,%.1f,%d,%.2f,%.3f,%.2f,%.2f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%s"),
			WPC && WPC->IsMouseCaptured() ? 1 : 0, VP && VP->HasMouseCapture() ? 1 : 0, VP && VP->HasFocus() ? 1 : 0, LookMagFrame,
			Traversal->GroundSrcNow(), WallW, GaitPh, SwLeg, TuckW, WristShin, KneeGap, FPv ? FPv->Scale : 0.f,
			FootWall[0], FootWall[1], HandWall[0], HandWall[1], *Traversal->LastZipWhy.ToString());
	}
	// round 20: body axis (hips -> head, rendered bones) vs the velocity and vs the wall's run axis; camera enclosed / hero probe points visible
	// from the lens / visibility lift; setback mantles, top-outs, anti-tunnel stops; zip reach weight; solid mode
	FString Cols20;
	{
		double BodyVel = -1.0, BodyWall = -1.0;
		float ZipW = 0.f, AirFW = 0.f, AirTK = 0.f;
		if (bHeroMesh)
		{
			const USkeletalMeshComponent* M = GetMesh();
			const FVector Ax = (M->GetBoneLocation(TEXT("head")) - M->GetBoneLocation(TEXT("hips"))).GetSafeNormal();
			if (V.Size() > 1.0) BodyVel = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FVector::DotProduct(Ax, V.GetSafeNormal()), -1.0, 1.0)));
			if (A.Mode == EWebTravMode::Wall)
			{
				FVector Up = A.Wall.Up - A.Wall.Normal * FVector::DotProduct(A.Wall.Up, A.Wall.Normal);
				if (!Up.IsNearlyZero()) BodyWall = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FVector::DotProduct(Ax, Up.GetSafeNormal()), -1.0, 1.0)));
			}
			if (const UWebTravAnimInstance* AI = Cast<UWebTravAnimInstance>(M->GetAnimInstance())) { ZipW = AI->Frame.ZipReachW; AirFW = AI->Frame.AirFastW; AirTK = AI->Frame.AirTrackK; }
		}
		Cols20 = FString::Printf(TEXT(",%.1f,%.1f,%d,%d,%.2f,%d,%d,%d,%d,%.2f,%d"), BodyVel, BodyWall, Cam.bCamEnclosed ? 1 : 0, Cam.VisPts, Cam.VisUp,
			Traversal->SetbackCount, Traversal->TopOutCount, Traversal->TunnelStops, (Cam.SlewFlags & 8) ? 1 : 0, ZipW, Traversal->TravWorld.SolidMode)
			+ FString::Printf(TEXT(",%d,%.3f,%.3f,%.0f,%.0f,%d"), Traversal->FlipCancels, AirFW, AirTK, VisTop, VisBottom, VisPx);
	}
	// round 21 (critic r20 W test split): on a wall, foot separation ALONG the run axis (ankles), knee gap ACROSS it, knees / every
	// hand+toe distance off the support surface, and the body axis' signed angle above the run line toward the wall's up axis
	FString Cols21 = TEXT(",-1,-1,-1,-1,-1,-999");
	if (bHeroMesh && A.Mode == EWebTravMode::Wall)
	{
		const USkeletalMeshComponent* M = GetMesh();
		const FVector N = A.Wall.Normal.GetSafeNormal(), WP = A.Wall.Point;
		FVector U = A.Wall.Up - N * FVector::DotProduct(A.Wall.Up, N);
		const FVector Zp = FVector::UpVector - N * FVector::DotProduct(FVector::UpVector, N);
		if (U.SizeSquared() < 1e-4) U = Zp;
		U = U.GetSafeNormal();
		const FVector Sd = FVector::CrossProduct(U, N).GetSafeNormal();
		auto Bn = [M](const TCHAR* B) { return M->GetBoneLocation(B); };
		const double Sep = FMath::Abs(FVector::DotProduct(Bn(TEXT("foot_L")) - Bn(TEXT("foot_R")), U)) / 100.0;
		const double KLat = FMath::Abs(FVector::DotProduct(Bn(TEXT("shin_L")) - Bn(TEXT("shin_R")), Sd)) / 100.0;
		const double KwL = FVector::DotProduct(Bn(TEXT("shin_L")) - WP, N) / 100.0, KwR = FVector::DotProduct(Bn(TEXT("shin_R")) - WP, N) / 100.0;
		double LMax = 0.0;
		for (const TCHAR* B : { TEXT("toe_L"), TEXT("toe_R"), TEXT("hand_L"), TEXT("hand_R") }) LMax = FMath::Max(LMax, FMath::Abs(FVector::DotProduct(Bn(B) - WP, N)) / 100.0);
		const FVector Ax = (Bn(TEXT("head")) - Bn(TEXT("hips"))).GetSafeNormal();
		FVector Pp = Zp - U * FVector::DotProduct(Zp, U);
		if (Pp.SizeSquared() < 1e-4) Pp = Sd;
		Pp = Pp.GetSafeNormal();
		const double Elev = FMath::RadiansToDegrees(FMath::Atan2(FVector::DotProduct(Ax, Pp), FVector::DotProduct(Ax, U)));
		Cols21 = FString::Printf(TEXT(",%.3f,%.3f,%.3f,%.3f,%.3f,%.1f"), Sep, KLat, KwL, KwR, LMax, Elev);
	}
	// round 22 (director r22 target: torso within 30 deg of the wall's up axis, facing along the run line): 3D angle of the torso (hips ->
	// neck / head) to the wall-up axis, angle of the chest (mesh forward) to the run line (along the facade), upright side-run blend
	FString Cols22 = TEXT(",-1,-1,0,-1");
	if (bHeroMesh && A.Mode == EWebTravMode::Wall)
	{
		const USkeletalMeshComponent* M = GetMesh();
		const FVector N = A.Wall.Normal.GetSafeNormal();
		FVector Zp = FVector::UpVector - N * FVector::DotProduct(FVector::UpVector, N);
		Zp = Zp.IsNearlyZero() ? FVector::UpVector : Zp.GetSafeNormal();
		FVector U = A.Wall.Up - N * FVector::DotProduct(A.Wall.Up, N);
		U -= Zp * FVector::DotProduct(U, Zp);
		const FVector Ax = (M->GetBoneLocation(TEXT("head")) - M->GetBoneLocation(TEXT("hips"))).GetSafeNormal();
		const double Tw = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FVector::DotProduct(Ax, Zp), -1.0, 1.0)));
		double Ch = -1.0;
		if (!U.IsNearlyZero())
		{
			FVector F = Traversal->Anim.BodyQ.GetForwardVector();
			F -= Zp * FVector::DotProduct(F, Zp);
			if (!F.IsNearlyZero()) Ch = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FVector::DotProduct(F.GetSafeNormal(), U.GetSafeNormal()), -1.0, 1.0)));
		}
		FVector DA = M->GetBoneLocation(TEXT("foot_L")) - M->GetBoneLocation(TEXT("foot_R"));
		DA -= N * FVector::DotProduct(DA, N); // ankle separation in the facade plane (along the run + up the wall)
		Cols22 = FString::Printf(TEXT(",%.1f,%.1f,%.2f,%.3f"), Tw, Ch, A.Wall.SideUp, DA.Size() / 100.0);
	}
	// round 23 (director r23: hips <= .45 m off the face; legs apart): hips distance off the support surface, 3D ankle separation
	FString Cols23 = TEXT(",-1,-1");
	if (bHeroMesh && A.Mode == EWebTravMode::Wall)
	{
		const USkeletalMeshComponent* M = GetMesh();
		const FVector N = A.Wall.Normal.GetSafeNormal();
		Cols23 = FString::Printf(TEXT(",%.3f,%.3f"), FVector::DotProduct(M->GetBoneLocation(TEXT("hips")) - A.Wall.Point, N) / 100.0,
			FVector::Dist(M->GetBoneLocation(TEXT("foot_L")), M->GetBoneLocation(TEXT("foot_R"))) / 100.0);
	}
	// round 24: altitude-chain apex want (m over the floor), camera turn direction of the user look, ground / perch crane lift (m)
	const FString Cols24 = FString::Printf(TEXT(",%.1f,%d,%.2f,%d"), Traversal->AltApexWant, Cam.LookYawDir, Cam.GndCrane, Cam.GndStopped + (Cam.bGndLensHold ? 2 : 0));

	PendingRow = Row + TEXT(",") + FlipCols + Flip12 + Cols15 + Cols17 + Cols19 + Cols20 + Cols21 + Cols22 + Cols23 + Cols24;   // the row is completed in EndAnimTick (strand columns of the final pose)
	PendingRowT = T; bRowPending = true;
}

// ------------------------------------------------------------------ live input (round 19)
void AWebTravCharacter::PollLiveInput(APlayerController* PC, FWebTravInput& I, float Dt)
{
	// a frame gap (pause menu, focus loss, hitch) longer than 0.3 s real time: every button still held counts as a fresh press
	const double Now = FPlatformTime::Seconds();
	// (a skipped engine frame = the pawn did not tick = the game was paused; fixed-step benchmark runs pause in very little real time)
	if (!bLatchInput && LastLiveTickReal > 0.0 && (Now - LastLiveTickReal > 0.3 || GFrameCounter > LastLiveFrame + 1)) PrevInput = FWebTravInput();
	LastLiveTickReal = Now; LastLiveFrame = GFrameCounter;
	FVector2D Stick = LiveMove, RStick = PadLook;
	if (PC && !bLatchInput)
	{
		auto Down = [PC](const FKey& K) { return PC->IsInputKeyDown(K); };
		bRMB = Down(EKeys::RightMouseButton);
		bR2 = Down(EKeys::Gamepad_RightTrigger);
		bL2 = Down(EKeys::Gamepad_LeftTrigger);
		bShift = Down(EKeys::LeftShift) || Down(EKeys::RightShift) || Down(EKeys::Gamepad_LeftThumbstick);
		bZipKey = Down(EKeys::E) || Down(EKeys::MiddleMouseButton) || Down(EKeys::Gamepad_FaceButton_Top);
		bDropKey = Down(EKeys::C) || Down(EKeys::LeftControl) || Down(EKeys::Gamepad_FaceButton_Right);
		bQuickKey = Down(EKeys::Q) || Down(EKeys::Gamepad_LeftShoulder);
		bJumpKey = Down(EKeys::SpaceBar) || Down(EKeys::Gamepad_FaceButton_Bottom);
		bTrickKey = Down(EKeys::F) || Down(EKeys::Gamepad_FaceButton_Left);
		const FVector2D Kb((Down(EKeys::D) || Down(EKeys::Right) ? 1.f : 0.f) - (Down(EKeys::A) || Down(EKeys::Left) ? 1.f : 0.f),
			(Down(EKeys::W) || Down(EKeys::Up) ? 1.f : 0.f) - (Down(EKeys::S) || Down(EKeys::Down) ? 1.f : 0.f));
		auto Dead = [](FVector2D V) { const float L = V.Size(); return L < 0.12f ? FVector2D::ZeroVector : V * (FMath::Min(1.f, (L - 0.12f) / 0.88f) / L); };
		const FVector2D LS = Dead(FVector2D(PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftX), PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftY)));
		Stick = Kb.IsNearlyZero() ? LS : Kb;
		RStick = Dead(FVector2D(PC->GetInputAnalogKeyState(EKeys::Gamepad_RightX), PC->GetInputAnalogKeyState(EKeys::Gamepad_RightY)));
	}
	I.Move = Stick.Size() > 1 ? Stick.GetSafeNormal() : Stick;
	I.bSwing = bRMB || (bR2 && !bL2);
	I.bSprint = bShift || (bR2 && !bL2);
	I.bZip = bZipKey || (bL2 && bR2);
	I.bJump = bJumpKey; I.bDrop = bDropKey; I.bQuick = bQuickKey; I.bTrick = bTrickKey;
	// look: mouse (yaw right +, pitch down +) and right stick rate
	const float MSens = MouseRadPerUnit * FMath::Max(0.f, CVarWHMouseSensitivity.GetValueOnGameThread());
	// owner playtest 2026-10-01: mouse look only while the game has the mouse (left click captures, Escape releases). With the cursor free,
	// moving it over the window -- or the right-mouse capture warp when a swing starts -- produced huge one-frame deltas. Clamp spikes too.
	const AWebHomagePlayerController* WPC = Cast<AWebHomagePlayerController>(PC);
	const bool bMouseLook = !WPC || WPC->IsMouseCaptured() || bInputTestMouse;
	LookMagFrame = MouseAccum.Size();
	const FVector2D MouseD = bMouseLook ? FVector2D(FMath::Clamp(MouseAccum.X, -MaxMouseDeltaPx, MaxMouseDeltaPx), FMath::Clamp(MouseAccum.Y, -MaxMouseDeltaPx, MaxMouseDeltaPx)) : FVector2D::ZeroVector;
	// 2026-10-01 settings menu: gamepad look sensitivity and Invert Y (mouse and stick). The right stick is never gated by mouse capture.
	const FWHSettings& St = WHSettings();
	const double YSign = St.bInvertY ? -1.0 : 1.0;
	const double PadK = St.PadSens;
	I.Look = FVector2D(MouseD.X * MSens, -MouseD.Y * MSens * YSign)
		+ FVector2D(RStick.X * PadLookRate.X * PadK, -RStick.Y * PadLookRate.Y * PadK * YSign) * Dt;
}

void AWebTravCharacter::WatchInput(APlayerController* PC, const FWebTravInput& I, float Dt)
{
	AWebHomagePlayerController* WPC = Cast<AWebHomagePlayerController>(PC);
	UGameViewportClient* GVC = GetWorld() ? GetWorld()->GetGameViewport() : nullptr;
	FViewport* VP = GVC ? GVC->Viewport : nullptr;
	const bool bPcCap = WPC && WPC->IsMouseCaptured();
	const bool bVpCap = VP && VP->HasMouseCapture();
	const bool bVpFocus = VP && VP->HasFocus();
	const bool bApp = FSlateApplication::IsInitialized() && FSlateApplication::Get().IsActive();
	const bool bMenu = WPC && WPC->IsSettingsOpen();
	const int32 St = (bPcCap ? 1 : 0) | (bVpCap ? 2 : 0) | (bVpFocus ? 4 : 0) | (bApp ? 8 : 0) | (bMenu ? 16 : 0);
	if (St != InCapState)
	{
		UE_LOG(LogWebHomage, Display, TEXT("WH_INPUT t %.2f state: player-captured %d, viewport capture %d, viewport focus %d, app active %d, menu %d (mode %s, rmb %d)"),
			TravTime, bPcCap ? 1 : 0, bVpCap ? 1 : 0, bVpFocus ? 1 : 0, bApp ? 1 : 0, bMenu ? 1 : 0, ModeName(Traversal->Anim.Mode), I.bSwing ? 1 : 0);
		InCapState = St;
	}
	// capture watchdog: the player has the game captured (no Escape), the app is in front, no menu, but the viewport lost its mouse
	// capture (focus stolen by a window / widget, a click that landed outside) -> take it back (never while released, never in the background)
	RecaptureCd = FMath::Max(0.f, RecaptureCd - Dt);
	if (bPcCap && bApp && !bMenu && !bVpCap && GVC) CapLostT += Dt; else CapLostT = 0.f;
	if (CapLostT > 0.3f && RecaptureCd <= 0.f)
	{
		ULocalPlayer* LP = PC ? PC->GetLocalPlayer() : nullptr;
		TSharedPtr<SViewport> VW = GVC->GetGameViewportWidget();
		if (LP && VW.IsValid())
		{
			const TSharedRef<SViewport> VR = VW.ToSharedRef();
			LP->GetSlateOperations().SetUserFocus(VR, EFocusCause::SetDirectly).CaptureMouse(VR).LockMouseToWidget(VR).UseHighPrecisionMouseMovement(VR);
			++NRecaptures; RecaptureCd = 1.f; CapLostT = 0.f;
			UE_LOG(LogWebHomage, Warning, TEXT("WH_INPUT t %.2f recapture #%d: the game had the mouse but the viewport lost its capture (focus %d)"), TravTime, NRecaptures, bVpFocus ? 1 : 0);
		}
	}
	// swing-press diagnosis: a press that has not attached a web 0.6 s later (in the air / on a wall) is logged with its reason
	for (const FWebTravEvent& E : Traversal->Events)
	{
		if (E.Type == FName(TEXT("swingStart"))) { ++StatSwingStart; PressWatchT = 0.f; }
		else if (E.Type == FName(TEXT("noAnchor"))) { ++StatNoAnchor; ++PressNoAnchor; }
	}
	if (I.bSwingPressed)
	{
		++StatPress; PressWatchT = 0.6f; PressNoAnchor = 0;
		PressFrom = FString::Printf(TEXT("%s/%s"), ModeName(Traversal->Anim.Mode), *Traversal->Anim.Sub.ToString());
	}
	if (I.bZipPressed) ++StatZipPress;
	if (PressWatchT > 0.f)
	{
		PressWatchT -= Dt;
		const EWebTravMode M = Traversal->Anim.Mode;
		if (M == EWebTravMode::Swing || M == EWebTravMode::Zip || Traversal->Anim.Sub == FName(TEXT("zipPull"))) PressWatchT = 0.f;
		else if (PressWatchT <= 0.f && I.bSwing && M != EWebTravMode::Ground && M != EWebTravMode::Land && M != EWebTravMode::Perch)
		{
			UE_LOG(LogWebHomage, Display, TEXT("WH_INPUT t %.2f swing press from %s: no web after 0.6 s (now %s/%s, %d searches without an anchor, %.1f m over the floor)"),
				TravTime, *PressFrom, ModeName(M), *Traversal->Anim.Sub.ToString(), PressNoAnchor, Traversal->HeightAboveFloor_());
		}
	}
	StatLook += LookMagFrame; if (LookMagFrame > 0.0) ++StatLookFrames;
	StatT += Dt;
	if (StatT >= 10.f)
	{
		UE_LOG(LogWebHomage, Display, TEXT("WH_INPUT 10 s: mouse %.0f px over %d frames (player-captured %d, viewport capture %d), rmb presses %d, swings %d, searches without anchor %d, zip presses %d, recaptures %d"),
			StatLook, StatLookFrames, bPcCap ? 1 : 0, bVpCap ? 1 : 0, StatPress, StatSwingStart, StatNoAnchor, StatZipPress, NRecaptures);
		StatT = 0.f; StatLook = 0.0; StatLookFrames = StatPress = StatSwingStart = StatNoAnchor = StatZipPress = 0;
	}
}

void AWebTravCharacter::RunDepthAudit(const FString& Path)
{
	// extent = the heightmap's (-WHTravHmExt=x0,y0,x1,y1, default the Midtown 3x3 export), 1 m per pixel, camera 900 m up looking down
	double X0 = -320.0, Y0 = -620.0, X1 = 680.0, Y1 = 380.0;
	FString Ext;
	if (FParse::Value(FCommandLine::Get(), TEXT("-WHTravHmExt="), Ext))
	{
		TArray<FString> E; Ext.ParseIntoArray(E, TEXT(","));
		if (E.Num() == 4) { X0 = FCString::Atod(*E[0]); Y0 = FCString::Atod(*E[1]); X1 = FCString::Atod(*E[2]); Y1 = FCString::Atod(*E[3]); }
	}
	const double Wd = FMath::Max(X1 - X0, Y1 - Y0);
	const int32 N = FMath::Clamp(int32(Wd), 64, 2048);
	const double Xc = 0.5 * (X0 + X1), Yc = 0.5 * (Y0 + Y1), Zc = 900.0;
	UTextureRenderTarget2D* RT = NewObject<UTextureRenderTarget2D>(this, TEXT("DepthAuditRT"));
	RT->RenderTargetFormat = ETextureRenderTargetFormat::RTF_R32f;
	RT->ClearColor = FLinearColor(1e7f, 0.f, 0.f, 1.f);
	RT->InitAutoFormat(N, N);
	RT->UpdateResourceImmediate(true);
	USceneCaptureComponent2D* C = NewObject<USceneCaptureComponent2D>(this, TEXT("DepthAuditCapture"));
	C->SetupAttachment(RootComponent);
	C->SetUsingAbsoluteLocation(true); C->SetUsingAbsoluteRotation(true);
	C->ProjectionType = ECameraProjectionMode::Orthographic;
	C->OrthoWidth = float(Wd * 100.0);
	C->bAutoCalculateOrthoPlanes = false;
	C->CaptureSource = ESceneCaptureSource::SCS_SceneDepth;
	C->bCaptureEveryFrame = false; C->bCaptureOnMovement = false;
	C->TextureTarget = RT;
	C->HiddenActors.Add(this);
	C->RegisterComponent();
	C->SetWorldLocationAndRotation(FVector(Xc, Yc, Zc) * 100.0, FRotator(-90.0, 0.0, 0.0));
	auto Grab = [&](TArray<FLinearColor>& Px)
	{
		C->CaptureScene();
		FTextureRenderTargetResource* Res = RT->GameThread_GetRenderTargetResource();
		return Res && Res->ReadLinearColorPixels(Px) && Px.Num() == N * N;
	};
	TArray<FLinearColor> A, B;
	const bool bA = Grab(A);
	for (const TWeakObjectPtr<UPrimitiveComponent>& E : Traversal->TravWorld.ExcludedComps) { if (E.IsValid()) C->HiddenComponents.Add(E.Get()); }
	const bool bB = Grab(B);
	// pixel (col, row) of world (x, y): camera pitched -90 at yaw 0 -> image up = +X, image right = +Y (the checker also tests the
	// other orientations and reports the best match, so a convention slip shows up as a flagged orientation, not as bad numbers)
	auto Px = [&](const TArray<FLinearColor>& Img, double X, double Y) -> double
	{
		const int32 Col = FMath::FloorToInt((Y - (Yc - Wd * 0.5)) / Wd * N), Row = FMath::FloorToInt(((Xc + Wd * 0.5) - X) / Wd * N);
		if (Col < 0 || Col >= N || Row < 0 || Row >= N) return -9999.0;
		const double D = Img[Row * N + Col].R;
		return D > 9e6 ? -9999.0 : Zc - D / 100.0;
	};
	FString Out = TEXT("x,y,trav,src,vis_all,vis_solid\n");
	for (double Y = Y0; Y <= Y1; Y += 5.0)
		for (double X = X0; X <= X1; X += 5.0)
		{
			const double Z = Traversal->TravWorld.GroundHeight(X, Y, 600.0);
			Out += FString::Printf(TEXT("%.0f,%.0f,%.2f,%d,%.2f,%.2f\n"), X, Y, Z, Traversal->TravWorld.LastGroundSrc, bA ? Px(A, X, Y) : -9999.0, bB ? Px(B, X, Y) : -9999.0);
		}
	FFileHelper::SaveStringToFile(Out, *Path);
	// the raw images too (row-major, metres of height), for the orientation check
	FString Raw = FString::Printf(TEXT("# n %d xc %.1f yc %.1f w %.1f zc %.1f\n"), N, Xc, Yc, Wd, Zc);
	for (int32 K = 0; K < N * N && bB; ++K) { Raw += FString::Printf(TEXT("%.1f"), B[K].R > 9e6 ? -9999.0 : Zc - B[K].R / 100.0); Raw += (K % N == N - 1) ? TEXT("\n") : TEXT(","); }
	FFileHelper::SaveStringToFile(Raw, *(FPaths::ChangeExtension(Path, TEXT("")) + TEXT("_solid_raw.csv")));
	UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV depth audit written: %s (%dx%d, ok %d/%d, %d excluded components hidden in pass B)"), *Path, N, N, bA ? 1 : 0, bB ? 1 : 0, Traversal->TravWorld.ExcludedComps.Num());
	C->DestroyComponent();
}

void AWebTravCharacter::EndPlay(const EEndPlayReason::Type Reason)
{
	if (InputTestTicker.IsValid()) { FTSTicker::GetCoreTicker().RemoveTicker(InputTestTicker); InputTestTicker.Reset(); }
	if (WHMovieAsync::Handle.IsValid()) { WHMovieAsync::Drain(); UGameViewportClient::OnScreenshotCaptured().Remove(WHMovieAsync::Handle); WHMovieAsync::Handle.Reset(); }
	if (bPostTickRegistered) { PostTickFn.UnRegisterTickFunction(); EndTickFn.UnRegisterTickFunction(); bPostTickRegistered = false; }
	Super::EndPlay(Reason);
}

bool AWebTravCharacter::InputTestTick(float Dt)
{
	APlayerController* PC = Cast<APlayerController>(GetController());
	if (!PC || !bTravStarted) return true;
	// engine-step clock (the ticker's Dt is the fixed step in -benchmark runs; it keeps running while the game is paused)
	InputTestClock += FMath::Clamp(double(Dt), 0.0, 0.1);
	const double Now = InputTestClock;
	if (InputTestT0 < 0.0) InputTestT0 = Now;
	const double T = Now - InputTestT0;
	if (bInputTestMouse)
	{ // round 20: real mouse-axis events, 6 px per engine frame right for 2 s (720 px at 60 fps), then 4 px per frame up for 1 s
		const double Yaw = Cam.CamRot.Yaw;
		if (T >= 0.5 && !bMouseTestYaw0) { bMouseTestYaw0 = true; MouseTestYaw0 = Yaw; UE_LOG(LogWebHomage, Display, TEXT("WH_INPUTTEST mouseLook t %.2f start: camera yaw %.1f pitch %.1f"), T, Yaw, Cam.CamRot.Pitch); }
		// round 20 (critic r19 "mouse 0 px over 0 frames"): the events take the HARDWARE path's form -- the game viewport, the default input
		// device, delta + delta time + 1 device sample (FSceneViewport mouse-move -> InputAxis), not a simulated key event
		auto Mouse = [&](const FKey& Key, float Delta)
		{
			FViewport* VP = GEngine && GEngine->GameViewport ? GEngine->GameViewport->Viewport : nullptr;
			const FInputKeyEventArgs Args(VP, IPlatformInputDeviceMapper::Get().GetDefaultInputDevice(), Key, Delta, Dt, 1, FPlatformTime::Cycles64());
			PC->InputKey(Args);
		};
		if (T >= 0.5 && T < 2.5) { Mouse(EKeys::MouseX, MouseTestPx); InjectedPx += MouseTestPx; }
		else if (T >= 3.0 && T < 4.0) { Mouse(EKeys::MouseY, MouseTestPx * 0.66f); InjectedPx += MouseTestPx * 0.66f; }
		if (T >= 2.5 && InputTestStep == 0) { InputTestStep = 1; UE_LOG(LogWebHomage, Display, TEXT("WH_INPUTTEST mouseLook t %.2f after %.0f px right: camera yaw %.1f (turned %.1f deg)"), T, InjectedPx, Yaw, FRotator::NormalizeAxis(Yaw - MouseTestYaw0)); }
		if (T >= 4.0 && InputTestStep == 1)
		{
			InputTestStep = 2;
			UE_LOG(LogWebHomage, Display, TEXT("WH_INPUTTEST RESULT mouseLook: %.0f px injected, camera yaw turned %.1f deg, pitch now %.1f"), InjectedPx, FRotator::NormalizeAxis(Yaw - MouseTestYaw0), Cam.CamRot.Pitch);
			return false;
		}
		return true;
	}
	enum EOp { Press, Release, Pause, Unpause, Report, End };
	struct FStep { double T; EOp Op; FKey Key; };
	// pauseRelease: (1) a normal press / release / press, (2) the release lost to a pause, (3) the release lost to a focus flush gap
	static const FStep Steps[] = {
		{ 0.6, Press, EKeys::RightMouseButton }, { 1.8, Release, EKeys::RightMouseButton }, { 2.4, Press, EKeys::RightMouseButton },
		{ 3.4, Pause, EKeys::Invalid }, { 3.7, Release, EKeys::RightMouseButton }, { 4.2, Unpause, EKeys::Invalid },
		{ 4.8, Press, EKeys::RightMouseButton }, { 6.0, Release, EKeys::RightMouseButton }, { 6.6, Press, EKeys::RightMouseButton },
		{ 7.6, Pause, EKeys::Invalid }, { 7.9, Release, EKeys::RightMouseButton }, { 8.1, Press, EKeys::RightMouseButton }, { 8.4, Unpause, EKeys::Invalid },
		{ 9.4, Release, EKeys::RightMouseButton }, { 10.0, Press, EKeys::RightMouseButton }, { 11.0, Release, EKeys::RightMouseButton },
		{ 11.6, Report, EKeys::Invalid }, { 12.0, End, EKeys::Invalid } };
	// swing detection for the last press (game-time independent: polled every engine frame)
	if (InputTestPressT >= 0.0 && Traversal->IsSwinging())
	{
		++InputTestSwings;
		UE_LOG(LogWebHomage, Display, TEXT("WH_INPUTTEST press %d -> swing after %.2f s"), InputTestPresses, Now - InputTestPressT);
		InputTestPressT = -1.0;
	}
	while (InputTestStep < int32(UE_ARRAY_COUNT(Steps)) && T >= Steps[InputTestStep].T)
	{
		const FStep& St = Steps[InputTestStep++];
		switch (St.Op)
		{
		case Press:
			if (InputTestPressT >= 0.0) UE_LOG(LogWebHomage, Warning, TEXT("WH_INPUTTEST press %d -> NO SWING"), InputTestPresses);
			PC->InputKey(FInputKeyEventArgs::CreateSimulated(St.Key, IE_Pressed, 1.f));
			++InputTestPresses; InputTestPressT = Traversal->IsSwinging() ? -1.0 : Now;
			UE_LOG(LogWebHomage, Display, TEXT("WH_INPUTTEST t %.2f press %d (%s, mode %s)"), T, InputTestPresses, *St.Key.ToString(), ModeName(Traversal->Anim.Mode));
			break;
		case Release:
			PC->InputKey(FInputKeyEventArgs::CreateSimulated(St.Key, IE_Released, 0.f));
			UE_LOG(LogWebHomage, Display, TEXT("WH_INPUTTEST t %.2f release (%s)%s"), T, *St.Key.ToString(), PC->IsPaused() ? TEXT(" while PAUSED") : TEXT(""));
			break;
		case Pause: PC->SetPause(true); UE_LOG(LogWebHomage, Display, TEXT("WH_INPUTTEST t %.2f pause"), T); break;
		case Unpause: PC->SetPause(false); UE_LOG(LogWebHomage, Display, TEXT("WH_INPUTTEST t %.2f unpause"), T); break;
		case Report:
			if (InputTestPressT >= 0.0) { UE_LOG(LogWebHomage, Warning, TEXT("WH_INPUTTEST press %d -> NO SWING"), InputTestPresses); InputTestPressT = -1.0; }
			UE_LOG(LogWebHomage, Display, TEXT("WH_INPUTTEST RESULT %s: %d presses, %d swings started (%s input)"), *InputTest, InputTestPresses, InputTestSwings,
				bLatchInput ? TEXT("round-18 event-latched") : TEXT("round-19 polled"));
			break;
		case End: return false;
		}
	}
	return true;
}

// ------------------------------------------------------------------ game mode
AWebTravGameMode::AWebTravGameMode()
{
	DefaultPawnClass = AWebTravCharacter::StaticClass();
	PlayerControllerClass = AWebHomagePlayerController::StaticClass();
}
