// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// Piece P5 (combat): one combat enemy — C++ port of src/game/combat/enemy.js.
// Visual: P2's armed street people (/Game/Characters/People/SK_Street_*_{Bat,Pistol,Pipe}, hero skeleton) driven by
// UWHEnemyAnim with P2's thug clips (/Game/Characters/Thug/Anims/A_Thug_*) + walk / jog / run for locomotion.
// Types: melee (hp 50), gunman (hp 38, pistol, keeps distance, fires 3-shot bursts), brute (hp 150, scale 1.24, armoured).
// States: hold · approach · attack · aim · fire · yanked · stagger · air · knock · down · getup · webbed · stuck · out
// The actor is ticked by AWHCombatDirector (Update / Late), never on its own. Metres internally (actor location = feet, cm).
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Combat/WHClipStack.h"
#include "Combat/WHCombatAnim.h"
#include "WHEnemy.generated.h"

class AWHCombatDirector;
class USkeletalMeshComponent;
class UStaticMeshComponent;
class UAnimSequence;
class UMaterialInstanceDynamic;

UENUM()
enum class EWHEnemyType : uint8 { Melee, Gunman, Brute };

UENUM()
enum class EWHEnemyState : uint8 { Hold, Approach, Attack, Aim, Fire, Yanked, Stagger, Air, Knock, Down, GetUp, Webbed, Stuck, Out };

struct FWHEnemyType
{
	double Hp = 50, Speed = 3.2, Reach = 1.35, Dmg = 9, Scale = 1;
	TArray<FName> Attacks;
	static const FWHEnemyType& Get(EWHEnemyType T);
};

/** Result of a hit (enemy.js hit() return object). */
struct FWHHitResult
{
	bool bValid = false, bArmored = false, bKnocked = false, bAir = false, bLaunched = false, bStagger = false, bSlam = false;
};

/** A hit dealt to an enemy (enemy.js h). Dir: horizontal unit, attacker -> enemy. */
struct FWHHitIn
{
	double Dmg = 0;
	FVector Dir = FVector::ForwardVector;
	FName Kind;            // light ender launch air slam strike throw finisher
	bool bStunBrute = false;
	int32 Side = 0;        // +1 = the blow lands on his left, -1 his right
	FVector CamRight = FVector::ZeroVector;   // r04: the camera's right axis (world): biases the recoil lean sideways on the screen so the tilt reads from any camera
};

UCLASS(NotPlaceable)
class WEBHOMAGE_API AWHEnemy : public AActor
{
	GENERATED_BODY()

public:
	AWHEnemy();

	void Setup(AWHCombatDirector* InDir, EWHEnemyType InType, int32 InIndex, const FVector& FeetM, double InYaw, const FString& MeshName);

	// ---- queries (metres)
	FVector Pos;                        // feet, metres
	FVector Chest() const;
	FVector HeadPos() const;
	FVector Muzzle() const;
	bool Alive() const { return !bOut && Stuck == 0; }
	bool Targetable() const { return Alive() && State != EWHEnemyState::Down && State != EWHEnemyState::GetUp; }
	const TCHAR* StateName() const;
	const TCHAR* TypeName() const;
	FString Tag() const { return FString::Printf(TEXT("e%d"), Index); }

	// ---- enemy.js API
	void Set(EWHEnemyState S);
	FWHHitResult Hit(const FWHHitIn& H);
	void Yank(const FVector& To, double Dur);
	void Launch(const FVector& Dir);
	void AirHit(const FWHHitIn& H);
	void Knock(const FVector& Dir, double Speed, double Up, bool bWebbed = false);
	void AddWeb(double Amount, const FVector& Dir);
	void Disarm(const FVector& Dir);
	void StickWall(const FVector& Point, const FVector& Normal);
	void StickGround();
	void MoveXZ(double Dx, double Dy, bool* bHit = nullptr, FVector* HitN = nullptr, FVector* HitP = nullptr);
	double Ground() const;
	void Update(double Dt);
	void Late(double Dt);
	void LandDown();
	void StartSwing();
	int32 Play(FName Name, double Fade = 0.18, double Ts = 1.0, int32 Once = -1, double At = -1.0);
	void Locomote(double Sp, double Fade = 0.25);
	void RootMotion();

	// ---- state (public: the director reads / writes most of it like the browser)
	EWHEnemyType Type = EWHEnemyType::Melee;
	FWHEnemyType T;
	int32 Index = 0;
	double Hp = 50, MaxHp = 50;
	EWHEnemyState State = EWHEnemyState::Hold;
	double St = 0, Yaw = 0, FaceYaw = 0, TurnRate = 0;
	bool bHasFace = false;
	FVector Vel = FVector::ZeroVector;
	double Web = 0, WebT = 0, Stun = 0, Cd = 1, Flinch = 0, FlinchDir = 1, Pitch = 0, LastHitT = -9, Juggle = 0, AimW = 0, AimP = 0;
	bool bOut = false, bHasGun = false, bSwung = false, bFalling = false, bKnockWeb = false, bDusted = false, bAirborne = false;
	int32 Stuck = 0;   // 0 no, 1 wall, 2 ground
	int32 Shots = 0;
	double NextShot = 0, AimDur = 0.95, StagT = 0.5, DownT = 1.5, Spd = 0;
	FName Atk, Loco, LastStumble, ActName;
	int32 ActUid = 0;
	struct FYank { FVector From, To; double Dur = 0.3, Prev = 0; } Yk;
	bool bMoving = false;
	int32 HitsTaken = 0;
	FVector Slide = FVector::ZeroVector;   // r02: hit push (m/s, decays): every light hit moves the victim >= 0.3 m
	// r03 local hit-stop: while HoldUntil (director real time) is in the future the director passes this enemy dt = 0 (pose, clip, slide, twist all
	// held) and the rest of the world keeps running. bHeld = the value the director applied to THIS tick (set at the end of the previous tick).
	double HoldUntil = -1; bool bHeld = false;
	// r03 hit twist: the whole body yaws about the vertical axis through the pelvis on every blow (rad, signed): 72 % of TwistAmp in the contact
	// frame, peak at 0.09 s, back to 0 by 0.6 s. Visual only (the actor yaw / hit box are untouched).
	double TwistAmp = 0, TwistT = 9, TwistNow = 0;
	/** start a twist. A blow that lands while a twist is still > 10 deg reverses it (so the change from the pre-blow pose is always >= 30 deg).
	 *  r04: the same call starts the recoil lean (RecAmp = max(0.62, 0.7 x twist) rad = 35-50 deg) in the direction of the blow (BlowDir, set by Hit()). */
	void StartTwist(double AmpRad, int32 Sign)
	{
		if (FMath::Abs(TwistNow) > 0.17) Sign = TwistNow > 0 ? -1 : 1;
		TwistAmp = AmpRad * Sign; TwistT = 0;
		RecAmp = FMath::Max(0.62, 0.7 * AmpRad); RecT = 0;
		FVector L = BlowDir; L.Z = 0;
		if (!L.Normalize()) L = FVector::ForwardVector;
		FVector Rt = BlowCamRt; Rt.Z = 0;
		if (Rt.Normalize())
		{ // lean 45 deg to the blow axis, towards the side of the screen the blow already points to (or the twist's side when it points along the view axis)
			const double D = FVector::DotProduct(L, Rt);
			const double Sg = FMath::Abs(D) > 0.15 ? (D > 0 ? 1.0 : -1.0) : double(Sign);
			L = (L + Rt * (Sg * 0.95)).GetSafeNormal();
		}
		RecDirW = L;
	}
	/** r04 hit recoil: the whole body tilts about the knees (0.45 m) towards RecDirW: 65 % of RecAmp in the contact frame, peak at 0.1 s, upright again by 0.56 s.
	 *  Visual only. TiltNow = the angle between the body's up axis and the vertical (recoil + tumble), deg, for the frame record. */
	double RecAmp = 0, RecT = 9, RecNow = 0, TiltNow = 0;
	FVector RecDirW = FVector::ForwardVector, BlowDir = FVector::ZeroVector, BlowCamRt = FVector::ZeroVector;
	/** total visual yaw (rad) = actor yaw + twist */
	double VisYaw() const { return Yaw + TwistNow; }
	/** r02: attack warning visible (melee / brute wind-up until the blow, gun aim + burst). */
	bool WarnOn() const;

	UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> Root;
	UPROPERTY(VisibleAnywhere) TObjectPtr<USkeletalMeshComponent> Mesh;

private:
	UAnimSequence* Clip(FName Name);
	void UpdateCocoon(double Dt);
	void SyncActor();
	TWeakObjectPtr<AWHCombatDirector> Dir;
	FWHClipStack Stack;
	UPROPERTY(Transient) TMap<FName, TObjectPtr<UAnimSequence>> Clips;
	UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> Cocoon;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> CocoonMat;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> WarnBar;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> WarnDot;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Laser;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> WarnMat;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> LaserMat;
	double WarnT = 0;
	void UpdateWarn(double Dt);
	FString UnarmedMesh;
	FQuat MeshCorr = FQuat::Identity;
	FVector MeshUp = FVector::UpVector;   // hips -> head in the skeleton's component space
	int32 RmUid = 0;
	FVector RmPrev = FVector::ZeroVector;
	FRandomStream Rng;
	double CocoonLvl = 0;
};
