// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// Piece P5 (combat): the hero's side of combat — C++ port of src/game/combat/spidey.js (move set, motion, clip stack).
// Moves: strike (combo jab / cross / hook / kick > ender: roundhouse, rising uppercut or flying kick; dash in on the run, or a
// leaping flying kick beyond DASH_MAX) · launcher (hold attack) · air combo (3 hits, the third slams) · air slam (hold in air)
// · dive strike · dodge (back / side flip; perfect = slow-mo 0.85 s + counter) · web strike (E, far) / yank strike (E, near)
// · web shooter (F) · finisher (Q, 1 focus; 2 on brutes) · heal (Z, 1 focus) · hit reactions / knockdown + get-up.
// Motion: while a move runs, the body centre (metres) is this class's; it is committed every frame through
// UWebTraversalComponent::Teleport (ground or air) and handed back to traversal as a ballistic fall (SetVelocityM) when a move
// ends airborne. Not ported yet: throw (props.js), Space jump-evade / jump-cancel (needs a traversal input hook).
#pragma once

#include "CoreMinimal.h"
#include "Combat/WHClipStack.h"

class AWHCombatDirector;
class AWHCombatHero;
class AWHEnemy;
class UWHCombatHeroAnim;
struct FWHThreat;

struct FWHMoveSpec
{
	FName Clip; double From = 0, Hit = 0.2, Ts = 1.3, Reach = 0.95, Dmg = 9; FName Kind; int32 Side = 0; double Until = -1;
};

/** Current move (spidey.js `M`): the union of every move's fields. */
struct FWHMove
{
	FName Name = "free";
	double T = 0;
	bool bHitDone = false;
	TWeakObjectPtr<AWHEnemy> Target;
	FName Clip, Kind; double From = 0, Until = -1, Hit = 0.2, Ts = 1, Dmg = 0, Reach = 1; int32 Side = 0;
	FVector P0 = FVector::ZeroVector, Dir0 = FVector::ZeroVector;
	bool bLong = false, bClipOn = false, bNoMove = false;
	double Fly = 0.3, ClipAt = 0, DashDur = 0, RunT = 0, RunD = 0, Windup = 0, V0 = 0, D0 = 1, PressT = 0;
	int32 Track = 0;
	// launcher rise / air
	bool bRise = false; double RiseT = 0; FVector RiseFrom = FVector::ZeroVector; double IdleT = 0; int32 Seg = -1;
	double AFrom = 0, AUntil = 0, AHit = 0, ADmg = 0; FName AKind;
	// dodge / hit / down
	FVector Move = FVector::ZeroVector; bool bSide = false, bPerfect = false; double Dist = 0, Go = 0; bool bDead = false, bUp = false;
	FVector HDir = FVector::ZeroVector;
	// dive / web strike
	double Arrive = 0.4, Arc = 0.5, Ts2 = 1, FlyT0 = 0; bool bPulled = false;
	bool bRecover = false; double Recover = 0, RDur = 0.25, Ry = 0; FVector R0 = FVector::ZeroVector, RDir = FVector::ZeroVector;
	FVector SlamFrom = FVector::ZeroVector;
};

class WEBHOMAGE_API FWHSpidey
{
public:
	FWHSpidey(AWHCombatDirector* InC, AWHCombatHero* InHero);

	/** One frame (after traversal): input -> moves -> motion -> body commit. Dt = game dt. */
	void Override(double Dt);
	/** Clip stack advance + snapshot to the anim instance. */
	void Late(double Dt);
	void TakeHit(AWHEnemy* E, double Dmg, bool bHeavy);
	void Reset();

	bool IsFree() const { return M.Name == "free"; }
	bool Busy() const { return M.Name != "free"; }
	bool Invuln() const;
	FName MoveName() const { return M.Name; }
	FVector Feet() const { return Pos - FVector(0, 0, H); }

	double Hp = 100, MaxHp = 100, Focus = 0, InvulnUntil = 0, CounterUntil = 0, LastAttackT = -9;
	int32 ComboStep = 0;
	bool bAirborne = false;
	TWeakObjectPtr<AWHEnemy> Target;
	FWHMove M;
	FVector Pos = FVector::ZeroVector;   // body centre (m) while a move owns the body
	FVector Vel = FVector::ZeroVector;
	FString LastResult;                   // what the last action did (beat log)
	static constexpr double H = 0.95;

private:
	// helpers
	void Face(double Yaw) { YawGoal = Yaw; bYawGoal = true; }
	void Turn(double Dt, double Rate = 14, double MaxW = 11);
	void KinTo(const FVector& P);
	void GroundXY(double X, double Y);
	void Start(FName Name);
	void Free(double Fade = 0.22, const FVector* V = nullptr);
	bool OnGround() const;
	double Nearest(double MaxD) const;
	UWHCombatHeroAnim* Anim() const;
	int32 PlayClip(FName Name, const FWHClipOpts& O);
	FWHClipTrack* Track() { return Layer.Find(M.Track); }
	FVector InputDir() const;
	double GroundZ(double X, double Y, double FromZ) const;
	// moves
	FName ChooseMove(int32 Step, AWHEnemy* T);
	static double DashDist(double U, double D, double T, double V0, double V1);
	void StrikeWith(AWHEnemy* T, const FWHMoveSpec& S, bool bEnder = false, bool bNoLong = false, FName Name = "strike", bool bNoMove = false);
	void PlayStrikeClip();
	void Strike(AWHEnemy* T, int32 Step);
	void Launcher(AWHEnemy* T);
	void AirStrike(AWHEnemy* T, int32 Seg, bool bForceSlam = false);
	double ArcOver(const FVector& P0, const FVector& To, double Base) const;
	void DiveStrike(AWHEnemy* T);
	void WebStrike(AWHEnemy* T);
	void YankStrike(AWHEnemy* T);
	void Dodge(const FVector& ThreatDir, bool bPerfect, const FVector& InDir);
	void WebShoot(AWHEnemy* T);
	void Finisher(AWHEnemy* T);
	void Motion(double Dt);
	bool AttackInput(bool bHold);
	bool DoAction(FName K);
	void Measure(double Dt);
	void Commit();
	void Stance(double Dt);

	AWHCombatDirector* C;
	AWHCombatHero* Hero;
	FWHClipStack Layer;
	double YawGoal = 0, VisYaw = 0; bool bYawGoal = false;
	bool bKin = false;          // the body is airborne on a scripted segment this frame
	bool bOwned = false;        // a move owns the body this frame (commit)
	bool bAirEnd = false; FVector AirEndV = FVector::ZeroVector;
	FVector PrevPos = FVector::ZeroVector;
	FName LastMove;
	int32 StanceUid = 0;
	FRandomStream Rng = FRandomStream(1234);
};
