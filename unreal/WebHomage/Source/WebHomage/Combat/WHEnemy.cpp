// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Combat/WHEnemy.h"
#include "Combat/WHCombatDirector.h"
#include "Combat/WHCombatUtil.h"
#include "Animation/AnimSequence.h"
#include "Animation/Skeleton.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Traversal/WebTravWorld.h"

using namespace WHCmb;

static const double G = 22.0;
// contact time (clip s) and telegraph (s from the start of the swing to the contact: the wind-up is slowed to fill it)
static double HitT(FName A)
{
	static const TMap<FName, double> M = { { "thugPunch1", 0.33 }, { "thugPunch2", 0.20 }, { "thugKick", 0.30 }, { "bruteSlam", 0.57 } };
	const double* V = M.Find(A); return V ? *V : 0.25;
}
static double Tele(FName A)
{
	static const TMap<FName, double> M = { { "thugPunch1", 0.55 }, { "thugPunch2", 0.42 }, { "thugKick", 0.5 }, { "bruteSlam", 0.85 } };
	const double* V = M.Find(A); return V ? *V : 0.5;
}
static const TSet<FName>& Loops()
{
	static const TSet<FName> S = { "idle", "walk", "jog", "run", "sprint", "fightIdle", "thugIdle", "thugWebbedStruggle", "thugGunAim" };
	return S;
}
static const TSet<FName>& RootMotionClips()
{
	static const TSet<FName> S = { "thugStumbleBack", "thugStumbleLeft", "thugStumbleRight", "thugKnockdown", "thugGetUp" };
	return S;
}
static const double LOCO_WALK = 1.14, LOCO_JOG = 3.10, LOCO_RUN = 5.70;   // P2 foot speeds (walkStreet 114, hero jog 310, run 570 cm/s)

const FWHEnemyType& FWHEnemyType::Get(EWHEnemyType Ty)
{
	static FWHEnemyType Melee{ 50, 3.2, 1.35, 9, 1, { "thugPunch1", "thugPunch2", "thugKick" } };
	static FWHEnemyType Gunman{ 38, 3.0, 1.3, 6, 1, { "thugPunch2", "thugPunch1" } };
	static FWHEnemyType Brute{ 150, 2.4, 1.7, 18, 1.3, { "bruteSlam", "thugPunch1", "bruteSlam" } };   // r02: taller + much wider (below)
	return Ty == EWHEnemyType::Gunman ? Gunman : Ty == EWHEnemyType::Brute ? Brute : Melee;
}

AWHEnemy::AWHEnemy()
{
	PrimaryActorTick.bCanEverTick = false;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
	Mesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Mesh"));
	Mesh->SetupAttachment(Root);
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
	Mesh->bPerBoneMotionBlur = false;
}

const TCHAR* AWHEnemy::StateName() const
{
	static const TCHAR* N[] = { TEXT("hold"), TEXT("approach"), TEXT("attack"), TEXT("aim"), TEXT("fire"), TEXT("yanked"), TEXT("stagger"),
		TEXT("air"), TEXT("knock"), TEXT("down"), TEXT("getup"), TEXT("webbed"), TEXT("stuck"), TEXT("out") };
	return N[int32(State)];
}
const TCHAR* AWHEnemy::TypeName() const
{
	return Type == EWHEnemyType::Gunman ? TEXT("gunman") : Type == EWHEnemyType::Brute ? TEXT("brute") : TEXT("melee");
}

void AWHEnemy::Setup(AWHCombatDirector* InDir, EWHEnemyType InType, int32 InIndex, const FVector& FeetM, double InYaw, const FString& MeshName)
{
	Dir = InDir; Type = InType; Index = InIndex; T = FWHEnemyType::Get(InType);
	Rng.Initialize(9173 + InIndex * 131);
	Hp = MaxHp = T.Hp; Pos = FeetM; Yaw = InYaw;
	Cd = InDir->Rnd(0.6, 2.0);
	bHasGun = InType == EWHEnemyType::Gunman;
	USkeletalMesh* SM = LoadObject<USkeletalMesh>(nullptr, *FString::Printf(TEXT("/Game/Characters/People/%s.%s"), *MeshName, *MeshName));
	if (!SM) UE_LOG(LogTemp, Warning, TEXT("WH_CMB enemy mesh missing: %s"), *MeshName);
	UnarmedMesh = MeshName;
	if (MeshName.EndsWith(TEXT("_Pistol"))) UnarmedMesh = MeshName.LeftChop(7);
	Mesh->SetSkeletalMesh(SM);
	Mesh->SetAnimationMode(EAnimationMode::AnimationBlueprint);
	Mesh->SetAnimInstanceClass(UWHEnemyAnim::StaticClass());
	if (SM)
	{ // the asset's own forward / up (reference pose) -> actor +X forward, +Z up (same method as the P3 hero)
		const FReferenceSkeleton& RS = SM->GetRefSkeleton();
		auto RefCS = [&RS](const TCHAR* Name)
		{
			int32 I = RS.FindBoneIndex(FName(Name)); FTransform X = FTransform::Identity;
			while (I != INDEX_NONE) { X = X * RS.GetRefBonePose()[I]; I = RS.GetParentIndex(I); }
			return X.GetLocation();
		};
		FVector Fwd = RefCS(TEXT("toe_L")) - RefCS(TEXT("foot_L")) + RefCS(TEXT("toe_R")) - RefCS(TEXT("foot_R"));
		MeshUp = (RefCS(TEXT("head")) - RefCS(TEXT("hips"))).GetSafeNormal();
		Fwd = (Fwd - MeshUp * FVector::DotProduct(Fwd, MeshUp)).GetSafeNormal();
		MeshCorr = FRotationMatrix::MakeFromXZ(Fwd, MeshUp).ToQuat().Inverse();
		Mesh->SetRelativeRotation(MeshCorr);
	}
	const double S = T.Scale;
	SetActorScale3D(Type == EWHEnemyType::Brute ? FVector(S * 1.4, S * 1.45, S) : FVector(S));   // brute: bulk reads by silhouette
	// cocoon: translucent web wraps on the torso / arms / legs, scaled by the web amount (fx.js Cocoon)
	UStaticMesh* Sph = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (UMaterialInterface* M = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbTrans.M_CmbTrans")))
	{
		CocoonMat = UMaterialInstanceDynamic::Create(M, this);
		CocoonMat->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.9f, 0.9f, 0.93f));
		CocoonMat->SetScalarParameterValue(TEXT("Opacity"), 0.85f);
		CocoonMat->SetScalarParameterValue(TEXT("Emissive"), 0.15f);
	}
	static const TCHAR* Bones[] = { TEXT("spine1"), TEXT("spine2"), TEXT("upperArm_L"), TEXT("upperArm_R"), TEXT("thigh_L"), TEXT("thigh_R"), TEXT("shin_L"), TEXT("shin_R") };
	for (const TCHAR* B : Bones)
	{
		UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
		C->SetStaticMesh(Sph); C->SetCollisionEnabled(ECollisionEnabled::NoCollision); C->SetCastShadow(false);
		C->SetupAttachment(Mesh, FName(B)); C->RegisterComponent();
		if (CocoonMat) C->SetMaterial(0, CocoonMat);
		C->SetVisibility(false);
		Cocoon.Add(C);
	}
	// r02 attack warning: a glowing "!" over the head (orange = melee, deep red = brute / gun) + the gunman's aim laser
	UStaticMesh* Cyl = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (UMaterialInterface* M = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbFX.M_CmbFX")))
	{
		WarnMat = UMaterialInstanceDynamic::Create(M, this); LaserMat = UMaterialInstanceDynamic::Create(M, this);
		LaserMat->SetVectorParameterValue(TEXT("Color"), FLinearColor(6.f, 0.25f, 0.2f));
	}
	auto Mk = [this](UStaticMesh* SMh, UMaterialInstanceDynamic* Mt)
	{
		UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
		C->SetStaticMesh(SMh); C->SetCollisionEnabled(ECollisionEnabled::NoCollision); C->SetCastShadow(false);
		C->SetUsingAbsoluteLocation(true); C->SetUsingAbsoluteRotation(true); C->SetUsingAbsoluteScale(true);
		C->SetupAttachment(Root); C->RegisterComponent(); if (Mt) C->SetMaterial(0, Mt); C->SetVisibility(false);
		return C;
	};
	WarnBar = Mk(Sph, WarnMat); WarnDot = Mk(Sph, WarnMat); Laser = Mk(Cyl, LaserMat);
	SyncActor();
	Play("thugIdle", 0.25);
}

bool AWHEnemy::WarnOn() const
{
	if (!Alive()) return false;
	return (State == EWHEnemyState::Attack && !bSwung) || State == EWHEnemyState::Aim || (State == EWHEnemyState::Fire && Shots < 3);
}

void AWHEnemy::UpdateWarn(double Dt)
{
	const bool bOn = WarnOn();
	WarnT = bOn ? WarnT + Dt : 0;
	if (WarnBar) WarnBar->SetVisibility(bOn);
	if (WarnDot) WarnDot->SetVisibility(bOn);
	const bool bGun = State == EWHEnemyState::Aim || State == EWHEnemyState::Fire;
	if (Laser) Laser->SetVisibility(bOn && bGun && bHasGun && Dir.IsValid());
	if (!bOn) return;
	const double Pop = FMath::Min(1.0, WarnT / 0.08), Pulse = 1.0 + 0.12 * FMath::Sin(WarnT * 26.0);
	const FVector H = FVector(Pos.X, Pos.Y, Pos.Z + 1.95 * T.Scale + 0.25);
	const double K = 0.9 * Pop * Pulse;
	WarnBar->SetWorldLocationAndRotation((H + FVector(0, 0, 0.2)) * 100.0, FQuat::Identity);
	WarnBar->SetWorldScale3D(FVector(0.085, 0.085, 0.26) * K);
	WarnDot->SetWorldLocationAndRotation(H * 100.0, FQuat::Identity);
	WarnDot->SetWorldScale3D(FVector(0.09) * K);
	if (WarnMat)
	{
		const FLinearColor Cw = bGun || Type == EWHEnemyType::Brute ? FLinearColor(7.f, 0.5f, 0.25f) : FLinearColor(7.f, 2.6f, 0.3f);
		WarnMat->SetVectorParameterValue(TEXT("Color"), Cw); WarnMat->SetScalarParameterValue(TEXT("Opacity"), 1.f);
	}
	if (Laser && Laser->IsVisible())
	{
		const FVector A = Muzzle(), B = Dir->PlayerChest();
		const FVector Dd = B - A; const double L = Dd.Size();
		Laser->SetWorldLocationAndRotation((A + B) * 50.0, FQuat::FindBetweenNormals(FVector::UpVector, Dd / FMath::Max(1e-3, L)));
		Laser->SetWorldScale3D(FVector(0.012, 0.012, L));
		if (LaserMat) LaserMat->SetScalarParameterValue(TEXT("Opacity"), float(State == EWHEnemyState::Aim ? 0.35 + 0.65 * FMath::Min(1.0, St / FMath::Max(0.1, AimDur)) : 1.0));
	}
}

UAnimSequence* AWHEnemy::Clip(FName Name)
{
	if (TObjectPtr<UAnimSequence>* S = Clips.Find(Name)) return S->Get();
	FString P;
	const FString N = Name.ToString();
	if (N == TEXT("walk")) P = TEXT("/Game/Characters/People/Anims/A_Street_walkStreet");
	else if (N == TEXT("jog") || N == TEXT("run") || N == TEXT("idle") || N == TEXT("fightIdle")) P = TEXT("/Game/Characters/Hero/Anims/A_Hero_") + N;
	else P = TEXT("/Game/Characters/Thug/Anims/A_Thug_") + N;
	UAnimSequence* Seq = LoadObject<UAnimSequence>(nullptr, *(P + TEXT(".") + FPaths::GetBaseFilename(P)));
	if (!Seq) UE_LOG(LogTemp, Warning, TEXT("WH_CMB enemy clip missing: %s"), *P);
	Clips.Add(Name, Seq);
	return Seq;
}

// ------------------------------------------------------------------------------------------------ mixer-style play
int32 AWHEnemy::Play(FName Name, double Fade, double Ts, int32 Once, double At)
{
	UAnimSequence* Seq = Clip(Name);
	if (!Seq) return 0;
	const bool bOnce = Once < 0 ? !Loops().Contains(Name) : Once == 1;
	if (ActName == Name && !bOnce)
	{
		if (FWHClipTrack* Tr = Stack.Find(ActUid)) { Tr->Ts = Ts; return ActUid; }
	}
	FWHClipOpts O; O.Fade = Fade; O.Ts = Ts; O.bLoop = !bOnce; O.bHold = true; O.From = At >= 0 ? At : 0.0; O.bLockHips = RootMotionClips().Contains(Name);
	ActUid = Stack.Play(Name, Seq, O);
	ActName = Name;
	if (RootMotionClips().Contains(Name))
	{
		RmUid = ActUid;
		const USkeleton* Sk = Seq->GetSkeleton();
		const int32 HB = Sk ? Sk->GetReferenceSkeleton().FindBoneIndex(TEXT("hips")) : INDEX_NONE;
		FTransform X; if (HB != INDEX_NONE) Seq->GetBoneTransform(X, FSkeletonPoseBoneIndex(HB), FAnimExtractContext(O.From), false);
		RmPrev = X.GetLocation() - MeshUp * FVector::DotProduct(X.GetLocation(), MeshUp);
	}
	else RmUid = 0;
	return ActUid;
}

void AWHEnemy::RootMotion()
{
	FWHClipTrack* Tr = Stack.Find(RmUid);
	if (!Tr || !Tr->Seq) return;
	const USkeleton* Sk = Tr->Seq->GetSkeleton();
	const int32 HB = Sk ? Sk->GetReferenceSkeleton().FindBoneIndex(TEXT("hips")) : INDEX_NONE;
	if (HB == INDEX_NONE) return;
	FTransform X; Tr->Seq->GetBoneTransform(X, FSkeletonPoseBoneIndex(HB), FAnimExtractContext(Tr->T), false);
	const FVector H = X.GetLocation() - MeshUp * FVector::DotProduct(X.GetLocation(), MeshUp);
	const FVector D = H - RmPrev; RmPrev = H;
	const double W = Smooth(Tr->W) * (1.0 - Smooth(Tr->Out));
	// component space -> actor (mesh correction) -> world yaw, scaled (cm -> m)
	const FVector A = MeshCorr.RotateVector(D) * GetActorScale3D().X;
	const FVector Wd = FQuat(FVector::UpVector, Yaw).RotateVector(A) / 100.0 * W;
	if (FMath::Abs(Wd.X) + FMath::Abs(Wd.Y) > 1e-6) MoveXZ(Wd.X, Wd.Y);
}

void AWHEnemy::Locomote(double Sp, double Fade)
{
	if (Sp < 0.12) { Loco = NAME_None; Play("thugIdle", 0.3); return; }
	FName C = Sp > 4.6 ? FName("run") : Sp > 2.0 ? FName("jog") : FName("walk");
	if (Loco == "run" && Sp > 4.0) C = "run"; else if (Loco == "jog" && Sp > 1.6 && Sp < 5.2) C = "jog"; else if (Loco == "walk" && Sp < 2.4) C = "walk";
	Loco = C;
	const double Anchor = C == "run" ? LOCO_RUN : C == "jog" ? LOCO_JOG : LOCO_WALK;
	Play(C, Fade, Clamp(Sp / (Anchor * T.Scale), 0.55, 1.6));
}

// ------------------------------------------------------------------------------------------------ queries
FVector AWHEnemy::Chest() const
{
	const bool bLow = State == EWHEnemyState::Down || State == EWHEnemyState::Out;
	return Pos + FVector(0, 0, 1.25 * T.Scale + (bLow ? -0.95 : 0.0));
}
FVector AWHEnemy::HeadPos() const
{
	if (Mesh && Mesh->GetBoneIndex(TEXT("head")) != INDEX_NONE) return Mesh->GetBoneLocation(TEXT("head")) / 100.0;
	return Chest() + FVector(0, 0, 0.4);
}
FVector AWHEnemy::Muzzle() const
{
	const FVector Hand = Mesh && Mesh->GetBoneIndex(TEXT("hand_R")) != INDEX_NONE ? Mesh->GetBoneLocation(TEXT("hand_R")) / 100.0 : Chest();
	return Hand + YawDir(Yaw) * 0.16 + FVector(0, 0, 0.03);
}
double AWHEnemy::Ground() const { return Dir.IsValid() ? Dir->GroundHeight(Pos.X, Pos.Y, Pos.Z + 1.0) : 0.0; }

void AWHEnemy::MoveXZ(double Dx, double Dy, bool* bHitOut, FVector* HitN, FVector* HitP)
{
	if (bHitOut) *bHitOut = false;
	const double L = FMath::Sqrt(Dx * Dx + Dy * Dy); if (L < 1e-6 || !Dir.IsValid()) return;
	const FVector D(Dx / L, Dy / L, 0);
	FTravHit H;
	if (Dir->Raycast(Pos + FVector(0, 0, 0.9), D, L + 0.35, H) && !H.bGround && FMath::Abs(H.Normal.Z) < 0.6)
	{
		const FVector N = FlatNorm(H.Normal);
		const double Into = Dx * N.X + Dy * N.Y;
		if (Into < 0) { Dx -= N.X * Into; Dy -= N.Y * Into; }
		const double Room = H.Distance - 0.35; if (Room < 0) { Dx += N.X * -Room; Dy += N.Y * -Room; }
		Pos.X += Dx; Pos.Y += Dy;
		if (bHitOut) *bHitOut = true; if (HitN) *HitN = H.Normal; if (HitP) *HitP = H.Point;
		return;
	}
	Pos.X += Dx; Pos.Y += Dy;
}

// ------------------------------------------------------------------------------------------------ damage intake
void AWHEnemy::Set(EWHEnemyState S)
{
	State = S; St = 0;
	if (S == EWHEnemyState::Hold || S == EWHEnemyState::Approach || S == EWHEnemyState::Attack || S == EWHEnemyState::Aim || S == EWHEnemyState::Fire) TurnRate = 0;
}

FWHHitResult AWHEnemy::Hit(const FWHHitIn& H)
{
	FWHHitResult R;
	if (!Alive() || !Dir.IsValid()) return R;
	R.bValid = true; ++HitsTaken;
	BlowDir = H.Dir; BlowCamRt = H.CamRight;
	AWHCombatDirector* C = Dir.Get();
	LastHitT = C->Time;
	const bool bArmored = Type == EWHEnemyType::Brute && Stun <= 0 && H.Kind != "throw" && H.Kind != "finisher" && H.Kind != "slam" && State != EWHEnemyState::Webbed;
	if (H.bStunBrute && Type == EWHEnemyType::Brute) Stun = 3.8;
	Hp -= H.Dmg * (bArmored ? 0.55 : 1.0);
	FaceYaw = FMath::Atan2(-H.Dir.Y, -H.Dir.X); bHasFace = true; // toward the attacker
	const double Rel = AngWrap(FaceYaw - Yaw); // attacker bearing in his frame (UE: + = on his RIGHT)
	const bool bDead = Hp <= 0;
	// r03: every blow twists the victim about the vertical axis (>= 30 deg within 0.3 s); the side follows the blow's side, else a seeded coin flip
	const int32 TwSide = H.Side != 0 ? (H.Side > 0 ? 1 : -1) : (Rng.FRand() < 0.5 ? -1 : 1);
	if (State == EWHEnemyState::Webbed && H.Kind != "air") { Knock(H.Dir, 10, 3.4, true); StartTwist(1.0, TwSide); R.bKnocked = true; return R; }
	if (bArmored && !bDead) { Flinch = 1; FlinchDir = Rng.FRand() < 0.5 ? -1 : 1; Slide = FlatNorm(H.Dir) * 6.2; StartTwist(0.66, TwSide); R.bArmored = true; return R; }
	if (H.Kind == "slam") { Vel = FVector(H.Dir.X * 2, H.Dir.Y * 2, -18); Set(EWHEnemyState::Air); Juggle = 0; bFalling = false; StartTwist(0.9, TwSide); R.bSlam = true; return R; }
	if (State == EWHEnemyState::Air && H.Kind != "air")
	{
		if (H.Kind == "ender" || H.Kind == "strike" || H.Kind == "throw")
		{ // r03: the ender of an air combo throws him away like a grounded heavy blow (>= 2 m)
			const double F = H.Kind == "ender" ? 8.0 : 9.0;
			Knock(H.Dir, F, 3.4); StartTwist(1.15, TwSide); R.bKnocked = true; return R;
		}
		Juggle = 0; Vel = FVector(H.Dir.X * 4, H.Dir.Y * 4, FMath::Min(Vel.Z, 1.0)); Flinch = 1; StartTwist(0.9, TwSide); R.bAir = true; return R;
	}
	if (State == EWHEnemyState::Air || H.Kind == "air") { AirHit(H); StartTwist(0.9, TwSide); if (bDead) Juggle = FMath::Min(Juggle, 0.25); R.bAir = true; return R; }
	if (H.Kind == "launch") { Launch(H.Dir); StartTwist(1.1, TwSide); R.bLaunched = true; return R; }
	if (H.Kind == "finisher") { Hp = 0; Knock(H.Dir, 9.5, 4.8, true); StartTwist(1.25, TwSide); R.bKnocked = true; return R; }
	if (bDead || H.Kind == "ender" || H.Kind == "strike" || H.Kind == "throw")
	{ // r03: heavy blows throw the victim >= 2 m (ender 8 m/s + 4.2 up: ~2.9 m of flight + the slide)
		const double F = H.Kind == "throw" ? 9 : H.Kind == "strike" ? 9 : bDead ? 8.5 : 8;
		Knock(H.Dir, F, H.Kind == "throw" ? 4.8 : 4.2); StartTwist(1.15, TwSide); R.bKnocked = true; return R;
	}
	// light hit: directional stumble (root motion carries him with his feet). Browser rel + = his left -> UE sign flipped.
	FName S = "back";
	if (FMath::Abs(Rel) > 0.9 && FMath::Abs(Rel) < 2.3) S = Rel > 0 ? FName("left") : FName("right");
	else if (FMath::Abs(Rel) <= 0.9 && H.Side) S = H.Side > 0 ? FName("right") : FName("left");
	if (S == LastStumble && Rng.FRand() < 0.5) S = "back";
	LastStumble = S;
	Set(EWHEnemyState::Stagger); TurnRate = FMath::Abs(Rel) > 2.3 ? 14 : 5;
	const double Ts = 1.15 + Rng.FRand() * 0.15;
	// r02: the flinch is already in the contact frame (clip entered at 0.1 s, r03: with NO fade + procedural head / torso snap + a body twist),
	// then the local hit-stop holds it and the victim is pushed >= 0.5 m along the blow
	Play(S == "back" ? FName("thugStumbleBack") : S == "left" ? FName("thugStumbleLeft") : FName("thugStumbleRight"), 0.0, Ts, 1, 0.1);
	Flinch = 1; FlinchDir = S == "left" ? -1 : S == "right" ? 1 : (Rng.FRand() < 0.5 ? -1 : 1);
	// r03: 6.5 m/s decaying at exp(-6 t): 0.75 m in the 0.22 s that follow the 5-frame hold (>= 0.5 m within 0.3 s), 1.1 m in all
	Slide = FlatNorm(H.Dir) * 6.5; StartTwist(0.85, TwSide);
	StagT = (S == "back" ? 0.7 : 0.6) / Ts - 0.06;
	C->OnEnemyInterrupted(this);
	R.bStagger = true;
	return R;
}

void AWHEnemy::Yank(const FVector& To, double DurS)
{
	if (!Alive()) return;
	Set(EWHEnemyState::Yanked); Yk.From = Pos; Yk.To = To; Yk.Dur = DurS; Yk.Prev = 0;
	FaceYaw = YawTo(Pos, To); bHasFace = true; TurnRate = 16;
	Play("thugKnockdown", 0.06, 0.3, 1, 0.1);
	Dir->OnEnemyInterrupted(this);
}

void AWHEnemy::Launch(const FVector& D)
{
	Set(EWHEnemyState::Air); Vel = FVector(D.X * 0.4, D.Y * 0.4, 10.2); Juggle = 1.7; TurnRate = 16; bFalling = false;
	Play("thugKnockdown", 0.08, 0.6, 1);
	Dir->OnEnemyInterrupted(this);
}

void AWHEnemy::AirHit(const FWHHitIn& H)
{
	Set(EWHEnemyState::Air); Juggle = 1.2; bFalling = false;
	Vel = FVector(H.Dir.X * 3.0, H.Dir.Y * 3.0, FMath::Max(Vel.Z, 3.0));   // r03: every juggle hit shoves him >= 0.5 m within 0.3 s (r02: 0.8 m/s)
	Play("thugStumbleBack", 0.05, 1.3, 1);
	Flinch = 1;
}

void AWHEnemy::Knock(const FVector& D, double Speed, double Up, bool bWebbed)
{
	Set(EWHEnemyState::Knock); bAirborne = true; bKnockWeb = bWebbed || Web >= 0.99; TurnRate = 22;
	Vel = FVector(D.X * Speed, D.Y * Speed, Up);
	Play("thugKnockdown", 0.06, 1.1, 1);
	Dir->OnEnemyInterrupted(this);
}

void AWHEnemy::AddWeb(double Amount, const FVector& D)
{
	if (!Alive()) return;
	if (bHasGun) { Disarm(D); Amount *= 0.5; }
	Web = FMath::Min(1.0, Web + Amount);
	if (Type == EWHEnemyType::Brute && Web >= 0.6) Stun = FMath::Max(Stun, 3.2);
	if (State == EWHEnemyState::Knock || (State == EWHEnemyState::Air && Juggle <= 0))
	{
		FVector P, N;
		if (Dir->FindWall(Chest(), D, 5, P, N)) { StickWall(P, N); return; }
	}
	if (State == EWHEnemyState::Down || State == EWHEnemyState::Out) { StickGround(); return; }
	if (State == EWHEnemyState::Webbed && St > 0.15) { Play("thugKnockdown", 0.1, 1.3, 1); StickGround(); return; }
	if (Web >= 0.99 && State != EWHEnemyState::Air && State != EWHEnemyState::Knock)
	{
		Set(EWHEnemyState::Webbed); WebT = 7; Play("thugWebbedStruggle", 0.18);
		Dir->OnEnemyInterrupted(this);
	}
}

void AWHEnemy::Disarm(const FVector& D)
{
	if (!bHasGun) return;
	bHasGun = false; AimW = 0;
	// the pistol is part of P2's armed mesh: swap to the unarmed person and throw a stand-in pistol away
	if (USkeletalMesh* SM = LoadObject<USkeletalMesh>(nullptr, *FString::Printf(TEXT("/Game/Characters/People/%s.%s"), *UnarmedMesh, *UnarmedMesh)))
		Mesh->SetSkeletalMeshAsset(SM);
	Dir->ThrowPistol(Muzzle(), D * -6.0 + FVector(0, 0, 4));
	if (State == EWHEnemyState::Aim || State == EWHEnemyState::Fire) { Set(EWHEnemyState::Hold); Dir->ReleaseToken(this); }
	Type = EWHEnemyType::Melee; const double Sc = T.Scale; T = FWHEnemyType::Get(EWHEnemyType::Melee); T.Scale = Sc;
	Dir->LogEvent(FString::Printf(TEXT("disarm %s"), *Tag()));
}

void AWHEnemy::StickWall(const FVector& Point, const FVector& Normal)
{
	Stuck = 1; Set(EWHEnemyState::Stuck); Web = 1; Vel = FVector::ZeroVector;
	const FVector N = FlatNorm(Normal);
	const double Gy = Ground();
	Pos = FVector(Point.X + N.X * 0.3, Point.Y + N.Y * 0.3, FMath::Max(Point.Z - 0.6, Gy + 0.9));
	Yaw = FMath::Atan2(N.Y, N.X); Pitch = 0;
	Play("thugWebbedStruggle", 0.12, 0.45);
	Dir->Fx.Splat(FVector(Point.X, Point.Y, Pos.Z + 1.2 * T.Scale), N, 2.6);
	Dir->Fx.Splat(FVector(Point.X, Point.Y, Pos.Z + 0.45), N, 1.4);
	Dir->OnEnemyOut(this, TEXT("wall"));
}

void AWHEnemy::StickGround()
{
	Stuck = 2; Set(EWHEnemyState::Stuck); Web = 1;
	Dir->Fx.Splat(FVector(Pos.X, Pos.Y, Ground() + 0.02) - YawDir(Yaw) * 0.8, FVector::UpVector, 2.1);
	Dir->OnEnemyOut(this, TEXT("ground"));
}

// ------------------------------------------------------------------------------------------------ per frame
void AWHEnemy::Update(double Dt)
{
	AWHCombatDirector* C = Dir.Get(); if (!C) return;
	const FVector P = C->PlayerFeet;
	St += Dt; Cd -= Dt; Stun -= Dt; TwistT += Dt; RecT += Dt;
	Flinch = FMath::Max(0.0, Flinch - Dt * 5);
	if (Slide.SizeSquared() > 1e-4 && State != EWHEnemyState::Air && State != EWHEnemyState::Knock && State != EWHEnemyState::Yanked && Stuck == 0)
	{ MoveXZ(Slide.X * Dt, Slide.Y * Dt); Slide *= FMath::Exp(-6.0 * Dt); }
	else if (Slide.SizeSquared() <= 1e-4) Slide = FVector::ZeroVector;
	const double Dist = HDist(Pos, P);
	const double FaceP = YawTo(Pos, P);
	double Moving = 0;
	if ((State == EWHEnemyState::Knock || State == EWHEnemyState::Air) && St > 3.5)
	{
		Pos.Z = Ground(); if (ActName != "thugKnockdown") Play("thugKnockdown", 0.1, 1, 1, 0.6); LandDown();
	}
	if (bHasFace && TurnRate > 0) { Yaw = DampAngle(Yaw, FaceYaw, TurnRate, Dt); if (FMath::Abs(AngWrap(FaceYaw - Yaw)) < 0.02) TurnRate = 0; }
	if (State == EWHEnemyState::Stagger || State == EWHEnemyState::Knock || State == EWHEnemyState::Down || State == EWHEnemyState::GetUp) RootMotion();
	switch (State)
	{
	case EWHEnemyState::Hold:
	{
		const FVector Slot = C->SlotFor(this);
		FVector To(Slot.X - Pos.X, Slot.Y - Pos.Y, 0); const double L = To.Size();
		const bool bFar = L > 1.4;
		const double Sp = bFar ? (L > 6 ? T.Speed * 1.5 : T.Speed * 0.75) : FMath::Min(0.55, L * 1.5);
		const double Want = L > 0.15 ? Sp : 0;
		Spd = Damp(Spd, Want, Want > Spd ? 5 : 8, Dt);
		if (L > 0.15) { To /= L; MoveXZ(To.X * Spd * Dt, To.Y * Spd * Dt); Moving = Spd; }
		Yaw = DampAngle(Yaw, bFar ? FMath::Atan2(To.Y, To.X) : FaceP, bFar ? 8 : 6, Dt);
		Locomote(Spd > 0.9 || bFar ? Spd : 0);
		break;
	}
	case EWHEnemyState::Approach:
	{
		const double Reach = T.Reach;
		const double Sp = Dist > 4 ? 6.0 : 4.2;
		Spd = Damp(Spd, Dist > Reach + 0.9 ? Sp : 2.2, 6, Dt);
		if (Dist > Reach + 0.9)
		{
			const FVector D = FlatNorm(P - Pos);
			MoveXZ(D.X * Spd * Dt, D.Y * Spd * Dt); Moving = Spd;
			Locomote(Spd, 0.2);
		}
		Yaw = DampAngle(Yaw, FaceP, 12, Dt);
		if (Dist <= Reach + 1.6 && FMath::Abs(AngWrap(FaceP - Yaw)) < 0.8) StartSwing();   // r02: wind up earlier, close in during it
		else if (St > 2.4 || C->HeroAirborne()) { Set(EWHEnemyState::Hold); C->ReleaseToken(this); }
		break;
	}
	case EWHEnemyState::Attack:
	{
		FWHClipTrack* A = Stack.Find(ActUid);
		const double Ht = HitT(Atk), Te = Tele(Atk);
		const double K0 = Ht - 0.06;
		if (A) A->Ts = A->T < K0 ? K0 / FMath::Max(0.05, Te - 0.06) : (Type == EWHEnemyType::Brute ? 0.9 : 1.05);
		if (!bSwung)
		{
			Yaw = DampAngle(Yaw, FaceP, St < Te * 0.6 ? 10 : 3, Dt);
			const double Left = FMath::Max(0.06, Te - St), Gap = Dist - T.Reach * 0.92;
			if (Gap > 0.02) { const double S = FMath::Min3(Gap, Gap / Left * Dt, 3.6 * Dt); const FVector D = FlatNorm(P - Pos); MoveXZ(D.X * S, D.Y * S); }
		}
		if (!bSwung && A && A->T >= Ht) { bSwung = true; C->EnemyStrike(this); }
		if (bSwung && (!A || A->T >= A->Len - 0.12))
		{
			Set(EWHEnemyState::Hold); Play("thugIdle", 0.25); Cd = C->Rnd(1.3, 2.8) * (Type == EWHEnemyType::Brute ? 1.3 : 1); C->ReleaseToken(this);
		}
		break;
	}
	case EWHEnemyState::Aim:
	{
		Yaw = DampAngle(Yaw, FaceP, 10, Dt);
		AimW = FMath::Min(1.0, AimW + Dt / 0.22);
		if (bHasGun) Play("thugGunAim", 0.22); else Play("thugIdle", 0.2);
		if (St >= AimDur) { Set(EWHEnemyState::Fire); Shots = 0; NextShot = 0; }
		break;
	}
	case EWHEnemyState::Fire:
	{
		Yaw = DampAngle(Yaw, FaceP, 10, Dt);
		NextShot -= Dt;
		if (NextShot <= 0 && Shots < 3) { ++Shots; NextShot = 0.26; C->EnemyShoot(this); if (bHasGun) Play("thugGunFire", 0.04, 1.15, 1); }
		if (Shots >= 3 && St > 0.85) { Set(EWHEnemyState::Hold); Play("thugIdle", 0.3); Cd = C->Rnd(2.6, 4.2); C->ReleaseToken(this); }
		break;
	}
	case EWHEnemyState::Yanked:
	{
		const double U = Clamp(St / Yk.Dur, 0, 1), E = U * U * (3 - 2 * U);
		const double Dd = E - Yk.Prev; Yk.Prev = E;
		if (Dd > 0) MoveXZ((Yk.To.X - Yk.From.X) * Dd, (Yk.To.Y - Yk.From.Y) * Dd);
		Pos.Z = Ground() + FMath::Sin(PI * U) * 0.28;
		if (St > Yk.Dur + 0.35) { Set(EWHEnemyState::Stagger); StagT = 0.4; Play("thugStumbleBack", 0.12, 1.2, 1); }
		break;
	}
	case EWHEnemyState::Stagger:
		if (St > StagT) { Set(EWHEnemyState::Hold); Play("thugIdle", 0.25); Cd = FMath::Max(Cd, C->Rnd(0.8, 1.6)); }
		break;
	case EWHEnemyState::Air:
	{
		Juggle -= Dt;
		const bool bHang = Juggle > 0 && Vel.Z < 1.5;
		Vel.Z -= (bHang ? G * 0.12 : G) * Dt;
		if (bHang) Vel.Z = FMath::Max(Vel.Z, -1.0);
		Vel.X *= FMath::Exp(-3 * Dt); Vel.Y *= FMath::Exp(-3 * Dt);
		MoveXZ(Vel.X * Dt, Vel.Y * Dt); Pos.Z += Vel.Z * Dt;
		Pitch = Damp(Pitch, Juggle > 0 ? -1.15 : -0.6, 6, Dt);
		if (Juggle <= 0 && !bFalling && Vel.Z < -1) { bFalling = true; Play("thugKnockdown", 0.2, 1, 1, 0.3); }
		const double Gy = Ground();
		if (Pos.Z <= Gy && Vel.Z <= 0)
		{
			Pos.Z = Gy; const double Sev = Clamp(-Vel.Z / 16, 0.2, 1);
			C->Fx.Dust(Pos, 0.5 + Sev); C->Shake(0.12 * Sev + 0.05);
			FWHClipTrack* A = Stack.Find(ActUid);
			if (ActName != "thugKnockdown" || (A && A->T < 0.5)) Play("thugKnockdown", 0.1, 1, 1, 0.62);
			bFalling = false; LandDown();
		}
		break;
	}
	case EWHEnemyState::Knock:
	{
		Vel.Z -= G * Dt;
		bool bHit = false; FVector HN, HP;
		MoveXZ(Vel.X * Dt, Vel.Y * Dt, &bHit, &HN, &HP);
		Pos.Z += Vel.Z * Dt;
		if (bHit && FMath::Sqrt(Vel.X * Vel.X + Vel.Y * Vel.Y) > 3)
		{
			if (bKnockWeb && C->IsFacade(HP, HN)) { StickWall(HP, HN); break; }
			if (bKnockWeb) Pos.Z += 0.02;
			else
			{
				const FLinearColor Wc(2, 2, 2);
				C->Fx.Hit(Chest(), FlatNorm(HN), 0.4, &Wc); C->Shake(0.15);
				Vel.X *= -0.25; Vel.Y *= -0.25; Hp -= 6;
			}
		}
		const double Gy = Ground();
		if (Pos.Z <= Gy && Vel.Z <= 0)
		{
			Pos.Z = Gy;
			const double Hs = FMath::Sqrt(Vel.X * Vel.X + Vel.Y * Vel.Y);
			if (Hs > 0.6) { Vel.Z = 0; Vel.X *= FMath::Exp(-7 * Dt); Vel.Y *= FMath::Exp(-7 * Dt); if (!bDusted) { bDusted = true; C->Fx.Dust(Pos, 0.8); } }
			else LandDown();
		}
		break;
	}
	case EWHEnemyState::Down:
		Pitch = Damp(Pitch, 0, 8, Dt);
		if (St > DownT)
		{
			if (Hp <= 0) { bOut = true; Set(EWHEnemyState::Out); C->OnEnemyOut(this, TEXT("ko")); }
			else { Set(EWHEnemyState::GetUp); Play("thugGetUp", 0.15, 1.1, 1); }
		}
		break;
	case EWHEnemyState::GetUp:
		if (St > 1.4 / 1.1 - 0.12) { Set(EWHEnemyState::Hold); Play("thugIdle", 0.25); Cd = C->Rnd(0.8, 1.8); }
		break;
	case EWHEnemyState::Webbed:
		WebT -= Dt;
		if (WebT <= 0) { Web = 0.3; Set(EWHEnemyState::Hold); Play("thugIdle", 0.3); }
		break;
	case EWHEnemyState::Stuck: case EWHEnemyState::Out:
		Pitch = Damp(Pitch, 0, 8, Dt);
		break;
	}
	if (State != EWHEnemyState::Webbed && State != EWHEnemyState::Stuck && State != EWHEnemyState::Air && State != EWHEnemyState::Knock && State != EWHEnemyState::Down && WebT <= 0)
		Web = FMath::Max(0.0, Web - Dt * 0.05);
	switch (State)
	{ // ground follow when standing (not 'yanked': it sets its own height; not 'stuck': pinned)
	case EWHEnemyState::Hold: case EWHEnemyState::Approach: case EWHEnemyState::Attack: case EWHEnemyState::Aim: case EWHEnemyState::Fire:
	case EWHEnemyState::Stagger: case EWHEnemyState::GetUp: case EWHEnemyState::Webbed: case EWHEnemyState::Down: case EWHEnemyState::Out:
		Pos.Z = Damp(Pos.Z, Ground(), 20, Dt); Pitch = Damp(Pitch, 0, 8, Dt);
		break;
	default: break;
	}
	bMoving = Moving > 0;
}

void AWHEnemy::LandDown()
{
	if (bKnockWeb || Web >= 0.95)
	{
		const FVector D = Vel.SizeSquared() > 0.01 ? Vel : -YawDir(Yaw);
		FVector P, N;
		if (Dir->FindWall(Chest(), D, 4.5, P, N)) { StickWall(P, N); return; }
	}
	Set(EWHEnemyState::Down); Vel = FVector::ZeroVector; bAirborne = false; bDusted = false;
	DownT = Hp <= 0 ? 1.1 : Dir->Rnd(1.3, 2.0);
	if (Web >= 0.95 || bKnockWeb) StickGround();
}

void AWHEnemy::StartSwing()
{
	FName A = T.Attacks[Rng.RandRange(0, T.Attacks.Num() - 1)];
	if (A == Atk && Rng.FRand() < 0.6) A = T.Attacks[Rng.RandRange(0, T.Attacks.Num() - 1)];
	Atk = A; bSwung = false; Loco = NAME_None;
	Set(EWHEnemyState::Attack); Play(Atk, 0.12, 0.5, 1);
	Dir->Threat(this, Tele(Atk), Type == EWHEnemyType::Brute ? TEXT("heavy") : TEXT("melee"));
}

// ------------------------------------------------------------------------------------------------ late: procedural + visuals
void AWHEnemy::Late(double Dt)
{
	Stack.Advance(Dt);
	const bool bAiming = bHasGun && (State == EWHEnemyState::Aim || State == EWHEnemyState::Fire);
	if (!bAiming) AimW = FMath::Max(0.0, AimW - Dt * 4);
	double AimPitchV = 0;
	if (AimW > 0.01 && Dir.IsValid())
	{
		const FVector Tg = Dir->PlayerChest(), Sh = Chest();
		const double Pt = Clamp(FMath::Atan2(Tg.Z - Sh.Z, FMath::Max(1.0, HDist(Tg, Sh))), -0.6, 0.9);
		AimP = Damp(AimP, Pt, 8, Dt);
		AimPitchV = AimP * Smooth(AimW);
	}
	TArray<FWHClipSample> S; Stack.Snapshot(S);
	FWHProcLayer Pr; Pr.Flinch = float(Flinch); Pr.FlinchDir = float(FlinchDir); Pr.AimPitch = float(AimPitchV);
	if (UWHEnemyAnim* AI = Cast<UWHEnemyAnim>(Mesh->GetAnimInstance())) AI->SetFrame(S, Pr);
	SyncActor();
	UpdateCocoon(Dt);
	UpdateWarn(Dt);
}

void AWHEnemy::SyncActor()
{
	// air / knock tumble about the pelvis (0.95 m): the mesh pitches back around a pivot, the actor stays upright
	const double Piv = 95.0;
	const FQuat Tilt = FQuat::FindBetweenNormals(FVector::UpVector, FVector(-FMath::Sin(-Pitch), 0, FMath::Cos(Pitch)).GetSafeNormal());
	double Tw = 0;
	if (TwistT < 0.62 && TwistAmp != 0.0)
	{ // r03 hit twist: 72 % of the amplitude in the contact frame, peak at 0.09 s, gone by 0.6 s
		const double P = TwistT < 0.09 ? Lerp(0.72, 1.0, Smooth(TwistT / 0.09)) : 1.0 - Smooth((TwistT - 0.09) / 0.51);
		Tw = TwistAmp * P;
	}
	TwistNow = Tw;
	// r04 recoil lean about the knees (see StartTwist): 65 % in the contact frame, peak at 0.1 s, gone by 0.56 s
	double Rc = 0;
	if (RecT < 0.56 && RecAmp > 0.0)
	{
		const double P = RecT < 0.10 ? Lerp(0.65, 1.0, Smooth(RecT / 0.10)) : 1.0 - Smooth((RecT - 0.10) / 0.46);
		Rc = RecAmp * P;
	}
	RecNow = Rc;
	FQuat Rec = FQuat::Identity;
	if (Rc > 1e-3)
	{
		const double Cy = FMath::Cos(Yaw), Sy = FMath::Sin(Yaw);
		const FVector Ll(RecDirW.X * Cy + RecDirW.Y * Sy, -RecDirW.X * Sy + RecDirW.Y * Cy, 0);
		Rec = FQuat::FindBetweenNormals(FVector::UpVector, FVector(Ll.X * FMath::Sin(Rc), Ll.Y * FMath::Sin(Rc), FMath::Cos(Rc)).GetSafeNormal());
	}
	const FQuat Inner = FQuat(FVector::UpVector, Tw) * Tilt;
	const FQuat Comb = Rec * Inner;
	const double Piv2 = 45.0;
	TiltNow = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(Comb.RotateVector(FVector::UpVector).Z, -1.0, 1.0)));
	Mesh->SetRelativeRotation(Comb * MeshCorr);
	// inner rotation about the pelvis (0.95 m), then the recoil about the knees (0.45 m)
	Mesh->SetRelativeLocation(Rec.RotateVector(FVector(0, 0, Piv) - Inner.RotateVector(FVector(0, 0, Piv)) - FVector(0, 0, Piv2)) + FVector(0, 0, Piv2));
	SetActorLocationAndRotation(Pos * 100.0, FRotator(0, FMath::RadiansToDegrees(Yaw), 0), false, nullptr, ETeleportType::TeleportPhysics);
}

void AWHEnemy::UpdateCocoon(double Dt)
{
	CocoonLvl = Damp(CocoonLvl, Web, 10, Dt);
	const bool bShow = CocoonLvl > 0.08;
	for (int32 i = 0; i < Cocoon.Num(); ++i)
	{
		UStaticMeshComponent* C = Cocoon[i]; if (!C) continue;
		C->SetVisibility(bShow);
		if (!bShow) continue;
		const bool bTorso = i < 2;
		const double K = Clamp((CocoonLvl - (bTorso ? 0.0 : 0.3)) / 0.7, 0, 1);
		const double R = bTorso ? 0.36 : 0.2;
		C->SetRelativeScale3D(FVector(R * (0.3 + 0.7 * K), (bTorso ? 0.42 : 0.5) * (0.3 + 0.7 * K), R * (0.3 + 0.7 * K)));
	}
}
