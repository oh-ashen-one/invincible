// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Combat/WHCombatDirector.h"
#include "Combat/WHCombatHero.h"
#include "Combat/WHCombatSpidey.h"
#include "Combat/WHCombatUtil.h"
#include "Core/WHSettings.h"
#include "WebHomage.h"
#include "Camera/CameraComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "EngineUtils.h"
#include "Engine/DirectionalLight.h"
#include "Engine/ExponentialHeightFog.h"
#include "Engine/PointLight.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/RectLight.h"
#include "Engine/SkyLight.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/RectLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Engine/GameViewportClient.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/FileManager.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "HAL/IConsoleManager.h"
#include "Misc/CommandLine.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Traversal/WebTraversalComponent.h"
#include "UnrealClient.h"

using namespace WHCmb;

static const double HH = 0.95;   // body centre over the feet (browser H)

AWHCombatDirector::AWHCombatDirector()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PrePhysics;
	SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
}

AWHCombatDirector::~AWHCombatDirector()
{
	delete Me; Me = nullptr;
}

void AWHCombatDirector::EndPlay(const EEndPlayReason::Type Reason)
{
	if (!bSummaryDone) { WriteTelemetry(); WriteSummary(); }
	Fx.Clear();
	Super::EndPlay(Reason);
}

void AWHCombatDirector::Init(AWHCombatHero* InHero)
{
	Hero = InHero;
	delete Me; Me = new FWHSpidey(this, InHero);
	Fx.Init(this);
	AddTickPrerequisiteActor(InHero);
	if (InHero->GetMesh()) InHero->GetMesh()->PrimaryComponentTick.AddPrerequisite(this, PrimaryActorTick);
	const TCHAR* Cmd = FCommandLine::Get();
	FParse::Value(Cmd, TEXT("WHCmbScript="), ScriptPath);
	FParse::Value(Cmd, TEXT("WHCmbFight="), FightSpec);
	FParse::Value(Cmd, TEXT("WHCmbDist="), FightDist);
	FParse::Value(Cmd, TEXT("WHCmbQuit="), QuitAt);
	FParse::Value(Cmd, TEXT("WHCmbShotName="), ShotName);
	FParse::Value(Cmd, TEXT("WHCmbShakePx="), HitShakePx);   // r03 experiments / tuning: hit shake px (1080p) and Hz, flare size factor, per-blow variant sweep
	FParse::Value(Cmd, TEXT("WHCmbShakeHz="), HitShakeHz);
	FParse::Value(Cmd, TEXT("WHCmbHoldR="), HoldRadius);
	FParse::Value(Cmd, TEXT("WHCmbVigA="), VigAmp);
	{ double Fi = 1.0; if (FParse::Value(Cmd, TEXT("WHCmbFlareI="), Fi)) Fx.FlareI = Fi; }
	{ int32 Fo = 1; if (FParse::Value(Cmd, TEXT("WHCmbFlare="), Fo)) Fx.bFlareOff = Fo == 0; }   // r04 A/B: -WHCmbFlare=0 = no starburst (same sim, same frames otherwise)
	{ double Fk = 1.0; if (FParse::Value(Cmd, TEXT("WHCmbFlareK="), Fk)) Fx.FlareK = Fk; int32 Sw = 0; if (FParse::Value(Cmd, TEXT("WHCmbSweep="), Sw)) bShakeSweep = Sw != 0; }
	{ FString LookSpec; if (FParse::Value(Cmd, TEXT("WHCmbLook="), LookSpec, false) && !LookSpec.IsEmpty()) ApplyLook(LookSpec); }
	FString ShotList;
	if (FParse::Value(Cmd, TEXT("WHCmbShots="), ShotList, false))
	{
		TArray<FString> Parts; ShotList.ParseIntoArray(Parts, TEXT(","));
		for (const FString& P : Parts) ShotTimes.Add(FCString::Atod(*P));
		ShotTimes.Sort();
	}
	if (!FParse::Value(Cmd, TEXT("WHCmbOut="), OutDir)) OutDir = FPaths::ProjectSavedDir() / TEXT("WHCombat");
	OutDir = FPaths::ConvertRelativePathToFull(OutDir);
	IFileManager::Get().MakeDirectory(*OutDir, true);
	{ TActorIterator<ADirectionalLight> It(GetWorld()); if (It) { FVector F = It->GetActorForwardVector(); F.Z = 0; if (F.Normalize()) { SunTo = -F; bSunKnown = true; } } }
	if (!ScriptPath.IsEmpty()) LoadScript(ScriptPath);
	UE_LOG(LogWebHomage, Display, TEXT("WH_CMB director ready: script=%s fight=%s beats=%d shots=%d quit=%.1f out=%s"),
		*ScriptPath, *FightSpec, Beats.Num(), ShotTimes.Num(), QuitAt, *OutDir);
}

// r02 look presets without rebuilding the map: -WHCmbLook="sunI=9,sunR=255,sunG=190,sunB=130,sunPitch=-11,sunYaw=180,skyI=1,expBias=0,fogD=0.004,..."
// Keys: sunI sunR sunG sunB sunPitch sunYaw | skyI | expBias expMin expMax | fogD fogR fogG fogB | lampI | fillI | sat contrast vig. Only the keys given are changed.
void AWHCombatDirector::ApplyLook(const FString& Spec)
{
	TMap<FString, double> K;
	TArray<FString> Parts; Spec.ParseIntoArray(Parts, TEXT(","));
	for (const FString& P : Parts) { FString A, B; if (P.Split(TEXT("="), &A, &B)) K.Add(A.TrimStartAndEnd(), FCString::Atod(*B)); }
	auto Has = [&K](const TCHAR* Key) { return K.Contains(Key); };
	auto G = [&K](const TCHAR* Key, double Def) { const double* V = K.Find(Key); return V ? *V : Def; };
	UWorld* W = GetWorld(); if (!W) return;
	for (TActorIterator<ADirectionalLight> It(W); It; ++It)
	{
		UDirectionalLightComponent* C = Cast<UDirectionalLightComponent>(It->GetLightComponent()); if (!C) continue;
		if (Has(TEXT("sunI"))) C->SetIntensity(float(G(TEXT("sunI"), 6)));
		if (Has(TEXT("sunR")) || Has(TEXT("sunG")) || Has(TEXT("sunB"))) C->SetLightColor(FLinearColor(float(G(TEXT("sunR"), 255) / 255.0), float(G(TEXT("sunG"), 255) / 255.0), float(G(TEXT("sunB"), 255) / 255.0)));
		if (Has(TEXT("sunPitch")) || Has(TEXT("sunYaw"))) It->SetActorRotation(FRotator(G(TEXT("sunPitch"), -7), G(TEXT("sunYaw"), 128), 0));
	}
	for (TActorIterator<ASkyLight> It(W); It; ++It)
		if (USkyLightComponent* C = It->GetLightComponent()) { if (Has(TEXT("skyI"))) C->SetIntensity(float(G(TEXT("skyI"), 1))); C->RecaptureSky(); }
	for (TActorIterator<AExponentialHeightFog> It(W); It; ++It)
		if (UExponentialHeightFogComponent* C = It->GetComponent())
		{
			if (Has(TEXT("fogD"))) C->SetFogDensity(float(G(TEXT("fogD"), 0.006)));
			if (Has(TEXT("fogR")) || Has(TEXT("fogG")) || Has(TEXT("fogB"))) { C->FogInscatteringLuminance = FLinearColor(float(G(TEXT("fogR"), 0.08)), float(G(TEXT("fogG"), 0.07)), float(G(TEXT("fogB"), 0.09))); C->MarkRenderStateDirty(); }
		}
	for (TActorIterator<APostProcessVolume> It(W); It; ++It)
	{
		FPostProcessSettings& S = It->Settings;
		if (Has(TEXT("expBias"))) { S.bOverride_AutoExposureBias = true; S.AutoExposureBias = float(G(TEXT("expBias"), 0)); }
		if (Has(TEXT("expMin"))) { S.bOverride_AutoExposureMinBrightness = true; S.AutoExposureMinBrightness = float(G(TEXT("expMin"), 0.03)); }
		if (Has(TEXT("expMax"))) { S.bOverride_AutoExposureMaxBrightness = true; S.AutoExposureMaxBrightness = float(G(TEXT("expMax"), 8)); }
		if (Has(TEXT("sat"))) { S.bOverride_ColorSaturation = true; const float V = float(G(TEXT("sat"), 1)); S.ColorSaturation = FVector4(V, V, V, 1); }
		if (Has(TEXT("contrast"))) { S.bOverride_ColorContrast = true; const float V = float(G(TEXT("contrast"), 1)); S.ColorContrast = FVector4(V, V, V, V); }
		if (Has(TEXT("vig"))) { S.bOverride_VignetteIntensity = true; S.VignetteIntensity = float(G(TEXT("vig"), 0.4)); }
	}
	if (Has(TEXT("lampI"))) for (TActorIterator<APointLight> It(W); It; ++It) if (UPointLightComponent* C = Cast<UPointLightComponent>(It->GetLightComponent())) C->SetIntensity(float(G(TEXT("lampI"), 9000)));
	if (Has(TEXT("fillI"))) for (TActorIterator<ARectLight> It(W); It; ++It) if (URectLightComponent* C = Cast<URectLightComponent>(It->GetLightComponent())) C->SetIntensity(float(G(TEXT("fillI"), 40)));
	UE_LOG(LogWebHomage, Display, TEXT("WH_CMB look override: %s"), *Spec);
}

// ------------------------------------------------------------------------------------------------ script
// Minimal JSON reader for the script format (the module's Build.cs is shared: no Json module dependency). Values: objects,
// arrays, strings, numbers, true / false / null.
namespace
{
	struct FJ
	{
		enum EK { Null, Num, Str, Arr, Obj, Bool } K = Null;
		double N = 0; FString S; TArray<FJ> A; TArray<TPair<FString, FJ>> O;
		const FJ* Get(const TCHAR* Key) const { for (const auto& P : O) if (P.Key == Key) return &P.Value; return nullptr; }
		double Num_(const TCHAR* Key, double Def) const { const FJ* V = Get(Key); return V && V->K == Num ? V->N : Def; }
		FString Str_(const TCHAR* Key) const { const FJ* V = Get(Key); return V && V->K == Str ? V->S : FString(); }
	};
	struct FJParser
	{
		const FString& T; int32 I = 0; bool bErr = false;
		explicit FJParser(const FString& In) : T(In) {}
		void Ws() { while (I < T.Len() && FChar::IsWhitespace(T[I])) ++I; }
		bool Eat(TCHAR C) { Ws(); if (I < T.Len() && T[I] == C) { ++I; return true; } return false; }
		FJ Value()
		{
			FJ V; Ws(); if (I >= T.Len()) { bErr = true; return V; }
			const TCHAR C = T[I];
			if (C == '{')
			{
				++I; V.K = FJ::Obj;
				if (Eat('}')) return V;
				do { Ws(); FJ Key = Value(); if (Key.K != FJ::Str || !Eat(':')) { bErr = true; return V; } V.O.Add(TPair<FString, FJ>(Key.S, Value())); } while (Eat(','));
				if (!Eat('}')) bErr = true;
			}
			else if (C == '[')
			{
				++I; V.K = FJ::Arr;
				if (Eat(']')) return V;
				do { V.A.Add(Value()); } while (Eat(','));
				if (!Eat(']')) bErr = true;
			}
			else if (C == '"')
			{
				++I; V.K = FJ::Str;
				while (I < T.Len() && T[I] != '"') { if (T[I] == '\\' && I + 1 < T.Len()) ++I; V.S.AppendChar(T[I++]); }
				++I;
			}
			else if (T.Mid(I, 4) == TEXT("true")) { V.K = FJ::Bool; V.N = 1; I += 4; }
			else if (T.Mid(I, 5) == TEXT("false")) { V.K = FJ::Bool; V.N = 0; I += 5; }
			else if (T.Mid(I, 4) == TEXT("null")) { I += 4; }
			else
			{
				const int32 S0 = I;
				while (I < T.Len() && (FChar::IsDigit(T[I]) || T[I] == '-' || T[I] == '+' || T[I] == '.' || T[I] == 'e' || T[I] == 'E')) ++I;
				if (I == S0) { bErr = true; return V; }
				V.K = FJ::Num; V.N = FCString::Atod(*T.Mid(S0, I - S0));
			}
			return V;
		}
	};
}

void AWHCombatDirector::LoadScript(const FString& Path)
{
	FString Txt;
	if (!FFileHelper::LoadFileToString(Txt, *Path)) { UE_LOG(LogWebHomage, Error, TEXT("WH_CMB script missing: %s"), *Path); return; }
	FJParser P(Txt);
	const FJ J = P.Value();
	if (P.bErr || J.K != FJ::Obj) { UE_LOG(LogWebHomage, Error, TEXT("WH_CMB script parse error near %d: %s"), P.I, *Path); return; }
	if (J.Get(TEXT("spec"))) FightSpec = J.Str_(TEXT("spec"));
	FightDist = J.Num_(TEXT("dist"), FightDist);
	FightStartAt = J.Num_(TEXT("start"), FightStartAt);
	const double Q = J.Num_(TEXT("quit"), -1); if (Q > 0 && QuitAt < 0) QuitAt = Q;
	if (J.Get(TEXT("seed"))) Rng.Initialize(int32(J.Num_(TEXT("seed"), 0)));
	HeroMinHp = J.Num_(TEXT("hero_min_hp"), 0); bHeroArmor = J.Num_(TEXT("hero_armor"), 0) > 0;
	ReserveSpec = J.Str_(TEXT("reserve")); Reserve = ReserveSpec.Len();
	KeepAlive = int32(J.Num_(TEXT("keep"), 0));
	ReflexCd = J.Num_(TEXT("reflex"), 0);
	if (const FJ* Arr = J.Get(TEXT("beats")))
	{
		for (const FJ& O : Arr->A)
		{
			if (O.K != FJ::Obj) continue;
			FWHBeat B;
			B.T = O.Num_(TEXT("t"), 0); B.Key = FName(*O.Str_(TEXT("key"))); B.Hold = O.Num_(TEXT("hold"), 0);
			B.Toward = O.Str_(TEXT("toward")); B.Label = O.Str_(TEXT("label"));
				B.React = FName(*O.Str_(TEXT("react"))); B.Window = O.Num_(TEXT("window"), 3.0); B.Rel = O.Num_(TEXT("rel"), -1);
				B.bGuard = O.Get(TEXT("guard")) && O.Get(TEXT("guard"))->N > 0;
			Beats.Add(B);
		}
		Beats.Sort([](const FWHBeat& A, const FWHBeat& B) { return A.T < B.T; });
	}
}

void AWHCombatDirector::RunBeats()
{
	if (!bFightStarted && !FightSpec.IsEmpty() && RTime >= FightStartAt) { bFightStarted = true; StartFight(FightSpec, FightDist); }
	// release the scripted LMB hold
	for (FWHBeat& B : Beats)
	{
		if (B.Key == "attack" && B.Hold > 0 && B.bFired && B.Result.IsEmpty() && RTime >= B.FiredRT + B.Hold) { Input.LmbUp(); B.Result = TEXT("released"); }
	}
	if (RTime > StickUntil) StickDir = FVector::ZeroVector;
	if (ReflexCd > 0 && bEngaged && RTime - LastReflexRT > ReflexCd)
	{ // record runs: a skilled player reacts to the telegraph (the freeze step turns every reflex into a fixed-time beat)
		const FWHThreat* Th = NearestThreat();
		const double R = Th ? Th->At - Time : 9;
		const FName MN = Me->MoveName();
		bool bGuarded = false;
		for (const FWHBeat& B : Beats)
			if (B.bGuard && ((B.bFired && RTime - B.FiredRT < 0.45) || (!B.bFired && B.T - RTime < 0.25 && B.T - RTime > -1.5))) bGuarded = true;
		if (Th && !bGuarded && R >= 0.08 && R <= 0.22 && MN != "down" && MN != "finisher" && MN != "hit" && MN != "dodge" && !Me->bAirborne)
		{
			LastReflexRT = RTime; KeyPress("dodge");
			const FString Row = FString::Printf(TEXT("{\"t\":%.3f,\"rt\":%.3f,\"gt\":%.3f,\"key\":\"dodge\",\"hold\":0.00,\"toward\":\"\",\"label\":\"reflex dodge %.2f\",\"move_before\":\"%s\",\"react\":\"reflex %s in %.3f\"}"),
				RTime, RTime, Time, RTime, *MN.ToString(), Th->E.IsValid() ? *Th->E->Tag() : TEXT("?"), R);
			BeatRows.Add(Row);
			UE_LOG(LogWebHomage, Display, TEXT("WH_CMB_BEAT %s"), *Row);
		}
	}
	for (int32 Bi = 0; Bi < Beats.Num(); ++Bi)
	{
		FWHBeat& B = Beats[Bi];
		if (B.bFired) continue;
		double Due = B.T;
		if (B.Rel >= 0) { if (Bi == 0 || !Beats[Bi - 1].bFired) continue; Due = Beats[Bi - 1].FiredRT + B.Rel; }
		if (RTime < Due) continue;
		FString Why;
		if (B.React == "air")
		{ // juggle press: the hero hangs at the victim waiting for the next segment. If the launcher never happened, skip the press.
			const bool bReady = Me->M.Name == "air" || (Me->M.Name == "airStrike" && Me->M.bHitDone);
			if (!bReady)
			{
				if (RTime < Due + B.Window) continue;
				B.bFired = true; B.FiredRT = RTime; B.FiredGT = Time;
				const FString Row = FString::Printf(TEXT("{\"t\":%.3f,\"rt\":%.3f,\"gt\":%.3f,\"key\":\"%s\",\"hold\":0.00,\"toward\":\"\",\"label\":\"%s\",\"move_before\":\"%s\",\"react\":\"skipped: no air state\"}"),
					B.T, RTime, Time, *B.Key.ToString(), *B.Label, *Me->MoveName().ToString());
				BeatRows.Add(Row); UE_LOG(LogWebHomage, Display, TEXT("WH_CMB_BEAT %s"), *Row);
				continue;
			}
			Why = TEXT("hero waits in the air");
		}
		else if (B.React == "threat")
		{ // record-run reflex: press when the nearest threat is about to land (the frozen script replays the recorded time)
			const FWHThreat* Th = NearestThreat();
			const double R = Th ? Th->At - Time : 9;
			if (!(R >= 0.08 && R <= 0.25) && RTime < Due + B.Window) continue;
			Why = R >= 0.08 && R <= 0.25 ? FString::Printf(TEXT("threat %s in %.3f"), Th && Th->E.IsValid() ? *Th->E->Tag() : TEXT("?"), R) : TEXT("window timeout");
		}
		else if (B.React == "free")
		{
			if (!Me->IsFree() && RTime < Due + B.Window) continue;
			Why = Me->IsFree() ? TEXT("hero free") : TEXT("window timeout");
		}
		B.bFired = true; B.FiredRT = RTime; B.FiredGT = Time;
		StickDir = FVector::ZeroVector; StickUntil = RTime + 0.5;
		if (!B.Toward.IsEmpty())
		{
			for (AWHEnemy* E : Enemies) if (E && E->Tag() == B.Toward) StickDir = FlatNorm(E->Pos - Me->Pos);
		}
		if (B.Key == "attack")
		{
			Input.LmbDown(RTime, Time);
			if (B.Hold <= 0) Input.LmbUp();
		}
		else if (B.Key == "focus") { Me->Focus = 3; }
		else KeyPress(B.Key);
		const FString Row = FString::Printf(TEXT("{\"t\":%.3f,\"rt\":%.3f,\"gt\":%.3f,\"key\":\"%s\",\"hold\":%.2f,\"toward\":\"%s\",\"label\":\"%s\",\"move_before\":\"%s\",\"react\":\"%s\"}"),
			B.T, RTime, Time, *B.Key.ToString(), B.Hold, *B.Toward, *B.Label, *Me->MoveName().ToString(), *Why);
		BeatRows.Add(Row);
		UE_LOG(LogWebHomage, Display, TEXT("WH_CMB_BEAT %s"), *Row);
	}
}

// ------------------------------------------------------------------------------------------------ input
void AWHCombatDirector::KeyPress(FName Action) { if (bEngaged) Input.Press(Action, Time); }
void AWHCombatDirector::LmbDown() { if (bEngaged) Input.LmbDown(RTime, Time); }
void AWHCombatDirector::LmbUp() { Input.LmbUp(); }

// ------------------------------------------------------------------------------------------------ world
bool AWHCombatDirector::Raycast(const FVector& O, const FVector& D, double MaxD, FTravHit& Out) const
{
	if (!Hero || !Hero->GetTraversal()) return false;
	return Hero->GetTraversal()->TravWorld.Raycast(O, D, MaxD, Out);
}

double AWHCombatDirector::GroundHeight(double X, double Y, double FromZ) const
{
	if (!Hero || !Hero->GetTraversal()) return 0.0;
	const double G = Hero->GetTraversal()->TravWorld.GroundHeight(X, Y, FromZ);
	return G < -999 ? 0.0 : G;
}

// a hit is a facade (not a bin / lamp post) if the surface continues above and to both sides at about the same depth
bool AWHCombatDirector::IsFacade(const FVector& Point, const FVector& Normal) const
{
	FVector N(Normal.X, Normal.Y, 0); if (N.SizeSquared() < 0.25) return false; N.Normalize();
	const FVector Side(-N.Y, N.X, 0), Back = -N;
	static const double S[4][2] = { { 0, 1.4 }, { 0.9, 0.2 }, { -0.9, 0.2 }, { 0, 2.4 } };
	int32 Ok = 0;
	for (const auto& P : S)
	{
		FVector O = Point + N * 0.6 + Side * P[0]; O.Z += P[1];
		FTravHit H;
		if (Raycast(O, Back, 2.2, H) && H.Distance < 1.8) ++Ok;
	}
	return Ok >= 3;
}

bool AWHCombatDirector::FindWall(const FVector& Pos, const FVector& Dir, double MaxD, FVector& OutP, FVector& OutN) const
{
	FVector D0(Dir.X, Dir.Y, 0); if (D0.SizeSquared() < 1e-4) return false; D0.Normalize();
	double Best = 1e9; bool bAny = false;
	for (double A : { 0.0, 0.5, -0.5, 1.0, -1.0 })
	{
		const FVector D = FQuat(FVector::UpVector, A).RotateVector(D0);
		FTravHit H;
		if (Raycast(Pos, D, MaxD, H) && !H.bGround && FMath::Abs(H.Normal.Z) < 0.5 && H.Distance < Best && IsFacade(H.Point, H.Normal))
		{ Best = H.Distance; OutP = H.Point; OutN = H.Normal; bAny = true; }
	}
	return bAny;
}

// ------------------------------------------------------------------------------------------------ targeting
AWHEnemy* AWHCombatDirector::PickTarget(const FVector* Dir, double MaxD, const FVector& From, double MinD, double NeedView) const
{
	FVector Want;
	if (Dir && Dir->SizeSquared() > 0.04) Want = FlatNorm(*Dir);
	else Want = CamW > 0.5 ? YawDir(CYaw) : YawDir(Hero->GetTravCamera().Yaw);
	AWHEnemy* Best = nullptr; double Bs = 1e18;
	for (AWHEnemy* E : Enemies)
	{
		if (!E || !E->Targetable()) continue;
		const double D = HDist(From, E->Pos); if (D > MaxD || D < MinD) continue;
		if (FMath::Abs(E->Pos.Z - From.Z) > 6 && E->State != EWHEnemyState::Air) continue;
		if (E->State == EWHEnemyState::Air && E->Pos.Z - From.Z > 1.2 && !Me->bAirborne) continue;
		const FVector To = FlatNorm(E->Pos - From);
		const double Ang = FMath::Acos(FMath::Clamp(FVector::DotProduct(To, Want), -1.0, 1.0));
		if (NeedView > 0 && Ang > NeedView) continue;
		double Sc = D * 0.6 + Ang * 3.2;
		if (E == Me->Target.Get()) Sc -= 1.2;
		if (E->State == EWHEnemyState::Attack || E->State == EWHEnemyState::Approach) Sc -= 0.4;
		if (Sc < Bs) { Bs = Sc; Best = E; }
	}
	return Best;
}

// ------------------------------------------------------------------------------------------------ threats / spider-sense
void AWHCombatDirector::Threat(AWHEnemy* E, double Lead, const TCHAR* Kind)
{
	FWHThreat T; T.E = E; T.At = Time + Lead; T.Kind = FName(Kind);
	Threats.Add(T);
	// r02: every threat is an attack start (melee wind-up / brute wind-up / gun aim). Longest gap between starts = aggression metric.
	if (LastAttackRT >= 0) MaxAttackGap = FMath::Max(MaxAttackGap, RTime - LastAttackRT);
	LastAttackRT = RTime; ++NAttackStarts;
	LogEvent(FString::Printf(TEXT("threat %s %s lead %.2f"), *E->Tag(), Kind, Lead));
}

void AWHCombatDirector::ClearThreats(const AWHEnemy* E)
{
	Threats.RemoveAll([E](const FWHThreat& T) { return T.E.Get() == E; });
}

const FWHThreat* AWHCombatDirector::NearestThreat() const
{
	const FWHThreat* B = nullptr;
	for (const FWHThreat& T : Threats)
	{
		const double R = T.At - Time; if (R < -0.08 || R > 0.8) continue;
		if (!B || T.At < B->At) B = &T;
	}
	return B;
}

bool AWHCombatDirector::HasToken(const AWHEnemy* E) const
{
	for (const auto& W : MeleeTokens) if (W.Get() == E) return true;
	for (const auto& W : GunTokens) if (W.Get() == E) return true;
	return false;
}

void AWHCombatDirector::ReleaseToken(AWHEnemy* E)
{
	if (MeleeTokens.RemoveAll([E](const TWeakObjectPtr<AWHEnemy>& W) { return W.Get() == E; }) > 0) GlobalCd = Rnd(0.15, 0.4);
	if (GunTokens.RemoveAll([E](const TWeakObjectPtr<AWHEnemy>& W) { return W.Get() == E; }) > 0) GunCd = FMath::Max(GunCd, Rnd(0.8, 1.6));
}

void AWHCombatDirector::OnDodge(const FWHThreat* T, bool bPerfect)
{
	++NDodges;
	if (bPerfect)
	{
		++NPerfect;
		// r02: short slow-mo, at most every 3 s (r01's 0.85 s x0.22 on every perfect dodge made the fight float)
		if (RTime - LastPerfectSlowRT > 3.0) { Slowmo(0.45, 0.35, 0.25); LastPerfectSlowRT = RTime; }
		Banner(TEXT("PERFECT DODGE")); Me->Focus = FMath::Min(3.0, Me->Focus + 0.35);
		Impact(0.15);
	}
	LogEvent(FString::Printf(TEXT("dodge %s threat=%s"), bPerfect ? TEXT("PERFECT") : TEXT("plain"), T && T->E.IsValid() ? *T->E->Tag() : TEXT("none")));
}

// ------------------------------------------------------------------------------------------------ hits dealt by the hero
void AWHCombatDirector::PlayerHit(AWHEnemy* E, const FWHPlayerHit& H)
{
	if (!E || !E->Alive()) return;
	static const TSet<FName> Melee = { "light", "ender", "launch", "strike", "air", "slam", "finisher" };
	const FVector HP = Me->Pos;
	if (Melee.Contains(H.Kind) && !H.bHasFrom)
	{ // melee blows only connect in reach: a blow that would land from further away whiffs
		const double Lim = (H.Reach < 0 ? 1.9 : H.Reach) + (E->Type == EWHEnemyType::Brute ? 0.3 : 0.0);
		const double Dy = (HP.Z - HH) - E->Pos.Z;
		if (HDist(HP, E->Pos) > Lim || Dy > 2.4 || Dy < -1.2)
		{
			++NWhiffs; LogEvent(FString::Printf(TEXT("whiff %s -> %s (%.2f m)"), *H.Kind.ToString(), *E->Tag(), HDist(HP, E->Pos))); return;
		}
	}
	const FVector From = H.bHasFrom ? H.From : HP;
	const FVector D = FlatNorm(E->Pos - From, YawDir(Hero->GetTraversal()->Facing()));
	FWHHitIn In; In.Dmg = H.Dmg; In.Dir = D; In.Kind = H.Kind; In.bStunBrute = H.bStunBrute; In.Side = H.Side;
	In.CamRight = FRotationMatrix(CamRotF).GetScaledAxis(EAxis::Y);   // r04: the recoil lean is biased sideways on the screen
	const FWHHitResult R = E->Hit(In);
	if (!R.bValid) return;
	const double Heavy = R.bArmored ? 0.1 : H.Heavy;
	FVector Cp = E->Chest() - D * 0.28;
	if (H.Kind == "air" || H.Kind == "slam" || E->State == EWHEnemyState::Air) Cp.Z = E->Pos.Z + 1.0;
	++NHits;
	if (R.bLaunched) ++NLaunch;
	if (H.Kind == "air" || H.Kind == "slam") ++NAirHits;
	if (H.Kind == "finisher") ++NFinishers;
	if (!H.bSilent)
	{
		const FLinearColor Arm(3.f, 3.f, 3.4f);
		// r03: a LOCAL freeze of the hero and this victim for 5 frames at 60 fps (critic r02: the whole-frame freeze read as stutter; 3-5 frames, only
		// the two bodies), the camera keeps a 2-4 px shake, an additive red-orange flare (~2 % of the frame) holds with the freeze and is gone 8 frames
		// after the contact.
		const int32 Fr = 5;
		BlowVariant();
		Fx.Impact(Cp, -D, Heavy, R.bArmored ? &Arm : nullptr, Fr);
		HitStop(Fr, E);
		if (H.Kind == "finisher")
		{ // finisher beat: freeze, then x0.25 slow-mo while the victim flies, the close-up camera holds 1.4 s past the blow
			Slowmo(1.1, 0.25, 0.5); Shake(0.35); Impact(0.4);
			if (CineS.bOn) CineS.Dur = FMath::Max(CineS.Dur, CineS.T + 1.4);
		}
		Shake(0.05 + Heavy * 0.25);
		if (Heavy > 0.5) Impact(0.12 + Heavy * 0.15);
		if (!R.bArmored) { ++ComboN; ComboT = 0; }
		if (Heavy > 0.5) CamPunchT = 0;
		const double Mult = 1 + FMath::Min(1.0, ComboN / 15.0);
		Me->Focus = FMath::Min(3.0, Me->Focus + (Heavy > 0.5 ? 0.14 : 0.075) * Mult);
	}
	LogEvent(FString::Printf(TEXT("hit %s -> %s dmg %.0f hp %.0f %s%s%s%s combo %d focus %.2f"), *H.Kind.ToString(), *E->Tag(), H.Dmg, FMath::Max(0.0, E->Hp),
		R.bArmored ? TEXT("ARMORED ") : TEXT(""), R.bLaunched ? TEXT("LAUNCHED ") : TEXT(""), R.bKnocked ? TEXT("KNOCKED ") : TEXT(""), R.bStagger ? TEXT("stagger ") : TEXT(""), ComboN, Me->Focus));
}

void AWHCombatDirector::GroundPound(const FVector& P)
{
	Fx.Dust(P, 0.9); Shake(0.35); Impact(0.35); BlowVariant(); Fx.Impact(P + FVector(0, 0, 0.35), FVector::UpVector, 0.6, nullptr, 5); HitStop(5);
	for (AWHEnemy* E : Enemies)
		if (E && E->Alive() && E->State != EWHEnemyState::Air && HDist(E->Pos, P) < 2.8)
		{ FWHPlayerHit H; H.Kind = "ender"; H.Dmg = 8; H.Heavy = 0.4; H.Reach = 3.2; H.bSilent = true; PlayerHit(E, H); HitStop(5, E); }
	LogEvent(TEXT("groundPound"));
}

void AWHCombatDirector::Heal(double N)
{
	Me->Hp = FMath::Min(Me->MaxHp, Me->Hp + N);
	Fx.Heal(Me->Pos);
	LogEvent(FString::Printf(TEXT("heal +%.0f hp %.0f"), N, Me->Hp));
}

void AWHCombatDirector::Cine(AWHEnemy* Target, double Dur, FName Kind)
{
	if (Kind != "finisher") { Slowmo(0.5, 0.45, 0.25); LogEvent(TEXT("pin beat (slow-mo only, no camera move)")); return; }
	CineS = FCine(); CineS.Target = Target; CineS.Dur = Dur; CineS.Kind = Kind; CineS.bOn = true;
	Slowmo(0.45, 0.55, 0.25);   // a light pre-slow on the wind-up; the takedown blow itself gets the deep slow-mo (PlayerHit)
	LogEvent(FString::Printf(TEXT("cine %s %s %.2f s"), *Kind.ToString(), Target ? *Target->Tag() : TEXT("-"), Dur));
}

void AWHCombatDirector::OnEnemyOut(AWHEnemy* E, const TCHAR* How)
{
	ReleaseToken(E); ClearThreats(E);
	const FString H(How);
	++NKOs;
	if (H == TEXT("wall")) Cine(E, 1.0, "pin");
	if (H == TEXT("wall") || H == TEXT("ground")) { Shake(0.12); Fx.WebHit(E->Chest(), FVector(0, 0, -1)); }
	if (H == TEXT("wall") && E->State == EWHEnemyState::Stuck) Me->Focus = FMath::Min(3.0, Me->Focus + 0.2);
	LogEvent(FString::Printf(TEXT("out %s %s"), *E->Tag(), How));
}

// ------------------------------------------------------------------------------------------------ hits dealt by enemies
FVector AWHCombatDirector::PlayerChest() const { return Me ? Me->Pos + FVector(0, 0, 0.45) : FVector::ZeroVector; }
bool AWHCombatDirector::HeroAirborne() const { return Me && Me->bAirborne; }
void AWHCombatDirector::Shake(double A) { CamTrauma = FMath::Min(1.0, CamTrauma + A); }

void AWHCombatDirector::Impact(double A)
{
	CamImpact = FMath::Min(1.0, CamImpact + A);
}

void AWHCombatDirector::EnemyStrike(AWHEnemy* E)
{
	ClearThreats(E);
	const FVector Pf = PlayerFeet;
	const double D = HDist(E->Pos, Pf), Dy = FMath::Abs(Pf.Z - E->Pos.Z);
	const bool bInReach = D <= E->T.Reach + 0.75 && Dy < 1.1;
	if (!bInReach || Me->Invuln()) { LogEvent(FString::Printf(TEXT("enemy swing %s %s missed (%s)"), *E->Tag(), *E->Atk.ToString(), Me->Invuln() ? TEXT("invulnerable") : TEXT("out of reach"))); return; }
	const bool bHeavy = E->Type == EWHEnemyType::Brute || (E->Atk == "thugKick" && Rng.FRand() < 0.3);
	const double Dmg = E->T.Dmg * (bHeavy && E->Type != EWHEnemyType::Brute ? 1.3 : 1.0);
	Me->TakeHit(E, Dmg, bHeavy);
	if (HeroMinHp > 0) Me->Hp = FMath::Max(Me->Hp, HeroMinHp);
	const FLinearColor Col(5, 2, 1.5);
	BlowVariant();
	Fx.Impact(Me->Pos + FVector(0, 0, 0.5), FlatNorm(Pf - E->Pos), bHeavy ? 0.6 : 0.2, &Col, 5);
	HitStop(5, E); Shake(bHeavy ? 0.3 : 0.16); if (bHeavy) Impact(0.25);
	ComboN = 0; ++NEnemyHits; DamageTaken += Dmg;
	LogEvent(FString::Printf(TEXT("hero hit by %s %s dmg %.0f hp %.0f%s"), *E->Tag(), *E->Atk.ToString(), Dmg, Me->Hp, bHeavy ? TEXT(" HEAVY") : TEXT("")));
}

void AWHCombatDirector::EnemyShoot(AWHEnemy* E)
{
	const FVector Mz = E->Muzzle();
	const FVector Ch = PlayerChest();
	const FVector D = (Ch - Mz).GetSafeNormal();
	Fx.Muzzle(Mz, D);
	FTravHit Hb;
	const bool bBlocked = Raycast(Mz, D, FVector::Dist(Mz, Ch) - 0.5, Hb);
	const bool bMiss = Me->Invuln() || bBlocked || (Me->bAirborne && Rng.FRand() < 0.6) || (Me->Busy() && Rng.FRand() < 0.75);
	const FVector End = bMiss ? Ch + FVector(Rnd(-1, 1), Rnd(-1, 1), Rnd(-0.4, 1)) + D * 6 : Ch;
	Fx.Tracer(Mz, End);
	++NShots;
	if (E->Shots >= 3) ClearThreats(E);
	if (bMiss) { LogEvent(FString::Printf(TEXT("shot %s missed%s"), *E->Tag(), Me->Invuln() ? TEXT(" (invulnerable)") : bBlocked ? TEXT(" (blocked)") : TEXT(""))); return; }
	Me->Hp = FMath::Max(HeroMinHp, Me->Hp - E->T.Dmg);
	const FLinearColor Col(5, 2, 1.2);
	Fx.Hit(Ch, -D, 0.05, &Col);
	Shake(0.1); ComboN = 0; ++NShotHits; DamageTaken += E->T.Dmg;
	if ((Me->IsFree() && !Me->bAirborne) || Me->Hp <= 0) Me->TakeHit(E, 0, Me->Hp <= 0);
	LogEvent(FString::Printf(TEXT("shot %s HIT hp %.0f"), *E->Tag(), Me->Hp));
}

void AWHCombatDirector::ThrowPistol(const FVector& P, const FVector& V)
{
	UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
	C->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")));
	C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	C->SetUsingAbsoluteLocation(true); C->SetUsingAbsoluteRotation(true); C->SetUsingAbsoluteScale(true);
	C->SetupAttachment(GetRootComponent()); C->RegisterComponent();
	C->SetWorldScale3D(FVector(0.2, 0.035, 0.13));
	if (UMaterialInterface* M = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Combat/Materials/M_CmbSolid.M_CmbSolid")))
	{
		UMaterialInstanceDynamic* Mi = UMaterialInstanceDynamic::Create(M, this);
		Mi->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.03f, 0.03f, 0.035f)); Mi->SetScalarParameterValue(TEXT("Metal"), 0.6f);
		C->SetMaterial(0, Mi);
	}
	FLoose L; L.Obj = C; L.Pos = P; L.Vel = V;
	Loose.Add(L);
}

// ------------------------------------------------------------------------------------------------ time scale (real time based)
void AWHCombatDirector::HitStop(int32 Frames, AWHEnemy* Victim)
{ // r03 local hold: UpdateTime runs at the end of this frame; the next Frames rendered frames advance the hero + victim by dt = 0
	const double Until = RTime + (Frames - 0.5) / 60.0;
	HeroHoldUntil = FMath::Max(HeroHoldUntil, Until);
	if (Victim)
	{
		Victim->HoldUntil = FMath::Max(Victim->HoldUntil, Until);
		// the brawl around the contact is held with it: a moving neighbour (or its long shadow) crossing the victim's crop would read as no freeze
		if (HoldRadius > 0)
			for (AWHEnemy* O : Enemies)
				if (O && O != Victim && O->Alive() && HDist(O->Pos, Victim->Pos) < HoldRadius) O->HoldUntil = FMath::Max(O->HoldUntil, Until);
	}
	// camera shake: a linear oscillation along a random screen axis (own RNG: the sim's random stream is untouched), on for the hold + 2 frames
	const bool bNew = RTime > ShakeUntil;
	ShakeUntil = RTime + (Frames + 2.0) / 60.0;
	if (bNew)
	{
		ShakeStart = RTime; const double A = ShakeRng.FRandRange(0.0, 2 * PI); ShakeAx = FMath::Cos(A); ShakeAy = FMath::Sin(A);
	}
	++NHitStops;
}

void AWHCombatDirector::Slowmo(double Dur, double Scale, double Ease)
{
	FTimeReq R; R.Start = RTime; R.Until = RTime + Dur; R.Scale = Scale; R.Ease = Ease; R.bSlow = true; TimeReq.Add(R); ++NSlowmo;
	LogEvent(FString::Printf(TEXT("slowmo %.2f s x%.2f"), Dur, Scale));
}

void AWHCombatDirector::UpdateTime()
{ // slow-mo only (global time dilation). The hit-stop is local (r03): it never touches the global dilation.
	double Sc = 1, Slow = 0;
	for (int32 i = TimeReq.Num() - 1; i >= 0; --i)
	{
		const FTimeReq& R = TimeReq[i];
		if (RTime >= R.Until) { TimeReq.RemoveAt(i); continue; }
		double S = R.Scale;
		if (R.bSlow) { const double Left = R.Until - RTime; const double K = Smooth(Left / R.Ease); S = 1 - (1 - R.Scale) * K; Slow = FMath::Max(Slow, 1 - S); }
		Sc = FMath::Min(Sc, S);
	}
	TimeScale = Sc; SlowK = Slow;
	MinTimeScale = FMath::Min(MinTimeScale, Sc);
	UGameplayStatics::SetGlobalTimeDilation(this, float(Sc));
	// local holds for the NEXT tick (the dilation set on one tick applies to the next, same convention as the global one had)
	bHitStop = RTime < HeroHoldUntil;
	if (Hero) Hero->CustomTimeDilation = bHitStop ? 0.002f : 1.0f;
	for (AWHEnemy* E : Enemies) if (E) E->bHeld = RTime < E->HoldUntil;
}

// ------------------------------------------------------------------------------------------------ fight lifecycle
void AWHCombatDirector::StartFight(const FString& Spec, double Dist)
{
	const FVector Pf = Me->Pos - FVector(0, 0, HH);
	const FVector Fwd = YawDir(Hero->GetTravCamera().Yaw);
	FightCenter = Pf + Fwd * Dist * 0.6;
	const int32 L = Spec.Len();
	for (int32 i = 0; i < L; ++i)
	{
		const TCHAR Ch = Spec[i];
		const double A = (double(i) / L - 0.5) * 2.4;
		const double R = Ch == 'g' ? Dist + 4 : Dist + (i % 2) * 1.2;
		const FVector D = FQuat(FVector::UpVector, -A).RotateVector(Fwd);   // browser rotates +a about +Y (to his left): mirrored in UE
		FVector P = Pf + D * R; P.Z = GroundHeight(P.X, P.Y, Pf.Z + 2);
		SpawnEnemy(Ch, P);
	}
	bFight = true; bEngaged = true; ComboN = 0; Me->Hp = FMath::Max(Me->Hp, 60.0); WarnCount = 0; ClearT = 0;
	Input.Clear();
	FString Types; for (AWHEnemy* E : Enemies) Types += FString::Printf(TEXT("%s%s:%s(%.1f,%.1f) "), Types.IsEmpty() ? TEXT("") : TEXT(""), *E->Tag(), E->TypeName(), E->Pos.X, E->Pos.Y);
	LogEvent(TEXT("fight start ") + Types);
}

void AWHCombatDirector::SpawnEnemy(TCHAR Ch, const FVector& P)
{ // P2 armed street people (hero skeleton): variety per type
	static const TCHAR* MeleeMeshes[] = { TEXT("SK_Street_Thug_Bat"), TEXT("SK_Street_Tee_Bat"), TEXT("SK_Street_Beard_Pipe"), TEXT("SK_Street_Hood") };
	static const TCHAR* GunMeshes[] = { TEXT("SK_Street_Thug_Pistol"), TEXT("SK_Street_Hood_Pistol") };
	const EWHEnemyType Ty = Ch == 'g' ? EWHEnemyType::Gunman : Ch == 'b' ? EWHEnemyType::Brute : EWHEnemyType::Melee;
	int32 NM = 0, NG = 0; for (AWHEnemy* O : Enemies) if (O) { if (O->bHasGun || O->Type == EWHEnemyType::Gunman) ++NG; else if (O->Type != EWHEnemyType::Brute) ++NM; }
	const FString MeshName = Ty == EWHEnemyType::Gunman ? GunMeshes[NG % 2] : Ty == EWHEnemyType::Brute ? TEXT("SK_Street_Brute_Pipe") : MeleeMeshes[NM % 4];
	FActorSpawnParameters SP; SP.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	AWHEnemy* E = GetWorld()->SpawnActor<AWHEnemy>(AWHEnemy::StaticClass(), FTransform(P * 100.0), SP);
	if (!E) return;
	E->Setup(this, Ty, NextIndex++, P, YawTo(P, PlayerFeet), MeshName);
	E->Mesh->PrimaryComponentTick.AddPrerequisite(this, PrimaryActorTick);
	Enemies.Add(E);
}

// r02 reinforcements: keep the ring full (script "keep" standing enemies, "reserve" = spawn spec). They run in from ~13 m in front
// of the combat camera, so the player sees them arrive.
void AWHCombatDirector::Reinforce(double Dt)
{
	SpawnCd -= Dt;
	if (Reserve <= 0 || KeepAlive <= 0 || SpawnCd > 0) return;
	int32 N = 0; for (AWHEnemy* E : Enemies) if (E && E->Alive() && E->State != EWHEnemyState::Down) ++N;
	if (N >= KeepAlive) return;
	const FVector Pf = PlayerFeet;
	for (int32 Try = 0; Try < 8; ++Try)
	{
		const double A = CYaw + (Try % 2 ? 1 : -1) * (0.25 + 0.2 * Try) + Rnd(-0.1, 0.1);
		const FVector D = YawDir(A);
		double R = 13.0;
		FTravHit H; if (Raycast(Pf + FVector(0, 0, 1), D, R + 1, H) && !H.bGround) R = H.Distance - 1.5;
		if (R < 8) continue;
		FVector P = Pf + D * R; P.Z = GroundHeight(P.X, P.Y, Pf.Z + 2);
		const TCHAR Ch = ReserveSpec[ReserveSpec.Len() - Reserve];
		--Reserve; SpawnCd = 0.6;
		SpawnEnemy(Ch, P);
		LogEvent(FString::Printf(TEXT("reinforcement %s %c at %.1f m"), *Enemies.Last()->Tag(), Ch, R));
		return;
	}
}

void AWHCombatDirector::EndFight(bool bWon)
{
	if (!bFight) return;
	bFight = false; bEngaged = false; ComboN = 0;
	Threats.Reset(); MeleeTokens.Reset(); GunTokens.Reset();
	Me->Reset();
	if (bWon) { Banner(TEXT("AREA CLEAR")); Slowmo(0.8, 0.35, 0.5); }
	LogEvent(FString::Printf(TEXT("fight end %s"), bWon ? TEXT("WON") : TEXT("ended")));
}

void AWHCombatDirector::DirectorStep(double Dt)
{
	const FVector Pf = PlayerFeet;
	GlobalCd -= Dt; GunCd -= Dt;
	TArray<AWHEnemy*> Standing;
	for (AWHEnemy* E : Enemies)
	{
		if (!E || !E->Alive()) continue;
		switch (E->State)
		{
		case EWHEnemyState::Hold: case EWHEnemyState::Approach: case EWHEnemyState::Attack: case EWHEnemyState::Aim: case EWHEnemyState::Fire:
		case EWHEnemyState::Stagger: case EWHEnemyState::GetUp: Standing.Add(E); break;
		default: break;
		}
	}
	// surround: melee enemies around the player at ~3 m, gunmen at ~10 m. r02: the ring stays in the arc the combat camera sees
	// (+-100 deg from its view direction), so nobody stands between the lens and the hero and the whole group is on screen.
	const bool bCamArc = CamW > 0.3;
	for (int32 Gp = 0; Gp < 2; ++Gp)
	{
		TArray<AWHEnemy*> Group;
		for (AWHEnemy* E : Standing) if ((E->Type == EWHEnemyType::Gunman) == (Gp == 1)) Group.Add(E);
		if (!Group.Num()) continue;
		const bool bGun = Gp == 1;
		const double Arc = bGun ? 0.62 : 1.4;
		TArray<double> Ang;
		for (AWHEnemy* E : Group) Ang.Add(FMath::Atan2(E->Pos.Y - Pf.Y, E->Pos.X - Pf.X));
		const double MinSep = bGun ? 0.35 : FMath::Min((bCamArc ? 2 * Arc : 2 * PI) / Group.Num(), 1.1);
		for (int32 It = 0; It < 6; ++It)
		{
			for (int32 i = 0; i < Ang.Num(); ++i)
				for (int32 j = i + 1; j < Ang.Num(); ++j)
				{
					const double D = AngWrap(Ang[j] - Ang[i]);
					if (FMath::Abs(D) < MinSep) { const double Push = (MinSep - FMath::Abs(D)) * 0.5 * (D >= 0 ? 1 : -1); Ang[i] -= Push; Ang[j] += Push; }
				}
			if (bCamArc) for (double& A : Ang) { const double R = AngWrap(A - CYaw); A = CYaw + FMath::Clamp(R, -Arc, Arc); }
		}
		for (int32 i = 0; i < Group.Num(); ++i)
		{
			AWHEnemy* E = Group[i];
			double R = bGun ? 8.5 + (i % 2) * 1.5 : E->Type == EWHEnemyType::Brute ? 3.6 : 2.8 + (i % 2) * 0.9;
			if (Me->bAirborne && !bGun) R += 1.2;
			const FVector D(FMath::Cos(Ang[i]), FMath::Sin(Ang[i]), 0);
			FTravHit H;
			if (Raycast(Pf + FVector(0, 0, 1), D, R + 0.6, H) && !H.bGround) R = FMath::Max(1.8, H.Distance - 0.8);
			Slots.Add(E, FVector(Pf.X + D.X * R, Pf.Y + D.Y * R, Pf.Z));
		}
	}
	// r02 aggression scheduler: several committed attackers, and a new wind-up at least every ~0.6-0.8 s (SM2 street fights keep
	// the pressure on). Melee attackers are not sent while the hero is airborne (they could not reach him): gunmen fill those gaps.
	MeleeTokens.RemoveAll([](const TWeakObjectPtr<AWHEnemy>& W) { return !W.IsValid() || !W->Alive() || (W->State != EWHEnemyState::Approach && W->State != EWHEnemyState::Attack); });
	GunTokens.RemoveAll([](const TWeakObjectPtr<AWHEnemy>& W) { return !W.IsValid() || !W->Alive() || (W->State != EWHEnemyState::Aim && W->State != EWHEnemyState::Fire); });
	const double Gap = LastAttackRT < 0 ? 9 : RTime - LastAttackRT;
	const bool bPressure = Gap > 0.55;
	const int32 MaxMelee = Gap > 0.7 ? 3 : 2;
	if (MeleeTokens.Num() < MaxMelee && (GlobalCd <= 0 || bPressure) && (!Me->bAirborne || Gap > 0.8))
	{
		AWHEnemy* Best = nullptr; double Bs = 1e18;
		for (AWHEnemy* E : Standing)
		{
			if ((E->Type == EWHEnemyType::Gunman && E->bHasGun) || E->State != EWHEnemyState::Hold || (E->Cd > 0 && !bPressure)) continue;
			const double D = HDist(E->Pos, Pf); if (D > 9) continue;
			const double Sc = D + Rng.FRand() * 2 + (E->Cd > 0 ? 2 : 0);
			if (Sc < Bs) { Bs = Sc; Best = E; }
		}
		if (Best)
		{
			MeleeTokens.Add(Best); Best->Set(EWHEnemyState::Approach); GlobalCd = Rnd(0.25, 0.5); LogEvent(TEXT("token melee ") + Best->Tag());
			if (Me->bAirborne) Best->StartSwing();   // hero above him: he swings up at once (it misses unless the hero comes down into it)
		}
	}
	if (Gap > 0.8)
	{ // pressure: the nearest attacker still closing in winds up now (the wind-up itself closes up to ~1.5 m)
		AWHEnemy* Best = nullptr; double Bd = 1e9;
		for (const auto& W : MeleeTokens)
			if (W.IsValid() && W->State == EWHEnemyState::Approach) { const double Dd = HDist(W->Pos, Pf); if (Dd < W->T.Reach + 2.6 && Dd < Bd) { Bd = Dd; Best = W.Get(); } }
		if (Best) Best->StartSwing();
	}
	const int32 MaxGun = (Me->bAirborne || Gap > 0.9) ? 2 : 1;
	if (GunTokens.Num() < MaxGun && (GunCd <= 0 || Gap > 0.8))
	{
		for (AWHEnemy* E : Standing)
		{
			if (!E->bHasGun || E->State != EWHEnemyState::Hold || (E->Cd > 0 && Gap < 0.8)) continue;
			const double D = HDist(E->Pos, Pf); if (D > 24 || D < 2.5) continue;
			const FVector From = E->Pos + FVector(0, 0, 1.4), To = PlayerChest();
			FTravHit H;
			if (Raycast(From, (To - From).GetSafeNormal(), FVector::Dist(From, To) - 0.5, H)) continue;
			GunTokens.Add(E); E->Set(EWHEnemyState::Aim); E->AimDur = 0.8; GunCd = Rnd(1.0, 1.8); Threat(E, 0.8, TEXT("gun"));
			LogEvent(TEXT("token gun ") + E->Tag());
			break;
		}
	}
}

FVector AWHCombatDirector::SlotFor(const AWHEnemy* E) const
{
	const FVector* S = Slots.Find(E);
	return S ? *S : PlayerFeet;
}

void AWHCombatDirector::Separate()
{
	auto Free = [](const AWHEnemy* E) { return E && E->Alive() && E->State != EWHEnemyState::Air && E->State != EWHEnemyState::Knock && E->State != EWHEnemyState::Down; };
	for (int32 i = 0; i < Enemies.Num(); ++i)
	{
		AWHEnemy* A = Enemies[i]; if (!Free(A)) continue;
		for (int32 j = i + 1; j < Enemies.Num(); ++j)
		{
			AWHEnemy* B = Enemies[j]; if (!Free(B)) continue;
			const double Dx = B->Pos.X - A->Pos.X, Dy = B->Pos.Y - A->Pos.Y, D = FMath::Sqrt(Dx * Dx + Dy * Dy), Mn = 0.85 * FMath::Max(A->T.Scale, B->T.Scale);
			if (D < Mn && D > 1e-4)
			{ // r03: a body held by the local hit-stop is immovable (the other one takes the whole correction)
				const double Ka = A->bHeld ? 0.0 : B->bHeld ? 1.0 : 0.5, Kb = B->bHeld ? 0.0 : A->bHeld ? 1.0 : 0.5, K = (Mn - D) / D;
				if (Ka > 0) A->MoveXZ(-Dx * K * Ka, -Dy * K * Ka);
				if (Kb > 0) B->MoveXZ(Dx * K * Kb, Dy * K * Kb);
			}
		}
		if (A->bHeld) continue;
		const FVector Pf = PlayerFeet;
		const double Dx = A->Pos.X - Pf.X, Dy = A->Pos.Y - Pf.Y, D = FMath::Sqrt(Dx * Dx + Dy * Dy), Mn = 0.8 * A->T.Scale;
		if (D < Mn && D > 1e-4 && FMath::Abs(A->Pos.Z - Pf.Z) < 1) A->MoveXZ(Dx / D * (Mn - D), Dy / D * (Mn - D));
		if (bCamLast && CamW > 0.5)
		{ // r02: nobody stands at the lens (a foreground body fills a quarter of the frame): keep a 3.2 m bubble around the camera
			const double Cx = A->Pos.X - BubbleP.X, Cy = A->Pos.Y - BubbleP.Y, Cd = FMath::Sqrt(Cx * Cx + Cy * Cy);
			const double Rb = (3.2 + 0.9 * CineK) * (0.7 + 0.3 * A->T.Scale) * (A->Type == EWHEnemyType::Brute ? 1.15 : 1.0); if (Cd < Rb && Cd > 1e-3) A->MoveXZ(Cx / Cd * (Rb - Cd) * 0.35, Cy / Cd * (Rb - Cd) * 0.35);
		}
	}
}

// ------------------------------------------------------------------------------------------------ web shooter
void AWHCombatDirector::FireWeb(AWHEnemy* T)
{
	FShot S; S.P = MakeShared<FVector>(Hero->HandM(true)); S.Target = T;
	TWeakObjectPtr<AWHCombatHero> WH = Hero; TSharedPtr<FVector> P = S.P;
	S.Strand = Fx.Strand([WH]() { return WH.IsValid() ? WH->HandM(true) : FVector::ZeroVector; }, [P]() { return *P; }, 2.0, 0, 0.14);
	Shots.Add(S);
	LogEvent(TEXT("web fired -> ") + T->Tag());
}

void AWHCombatDirector::UpdateShots(double Dt)
{
	for (int32 i = Shots.Num() - 1; i >= 0; --i)
	{
		FShot& S = Shots[i]; S.T += Dt;
		AWHEnemy* T = S.Target.Get();
		if (!S.bHit)
		{
			const FVector To = T ? T->Chest() : *S.P;
			const FVector D = To - *S.P; const double L = D.Size();
			const double Step = 48 * Dt;
			if (L <= Step || S.T > 1 || !T)
			{
				S.bHit = true; *S.P = To;
				if (T && T->Alive())
				{
					T->AddWeb(0.34, D.GetSafeNormal());
					Fx.WebHit(To, D.GetSafeNormal()); Me->Focus = FMath::Min(3.0, Me->Focus + 0.03); ++NWebHits;
					LogEvent(FString::Printf(TEXT("web hit %s web %.2f state %s"), *T->Tag(), T->Web, T->StateName()));
				}
			}
			else *S.P += D / L * Step;
			Fx.Pellet(*S.P);
		}
		else
		{
			S.Fade += Dt / 0.14;
			if (S.Fade >= 1) { Fx.KillTag(S.Strand); Shots.RemoveAt(i); continue; }
		}
	}
}

// ------------------------------------------------------------------------------------------------ combat camera (r02)
bool AWHCombatDirector::Project(const FVector& CamP, const FRotator& CamR, double FovDeg, const FVector& P, double& Sx, double& Sy)
{
	const FVector L = CamR.UnrotateVector(P - CamP);
	if (L.X < 0.05) { Sx = Sy = -1; return false; }
	const double Th = FMath::Tan(FMath::DegreesToRadians(FovDeg) * 0.5);
	Sx = 0.5 + 0.5 * (L.Y / L.X) / Th;
	Sy = 0.5 - 0.5 * (L.Z / L.X) / Th * (16.0 / 9.0);
	return true;
}

bool AWHCombatDirector::ScreenBox(const USkeletalMeshComponent* M, const FVector& CamP, const FRotator& CamR, double FovDeg, double& X0, double& Y0, double& X1, double& Y1, double& Dist)
{
	X0 = Y0 = 9; X1 = Y1 = -9; Dist = 1e9; bool bAny = false;
	if (!M) return false;
	const TArray<FTransform>& Cs = M->GetComponentSpaceTransforms();
	const FTransform Ct = M->GetComponentTransform();
	double Top = -1e9;
	for (const FTransform& B : Cs) Top = FMath::Max(Top, Ct.TransformPosition(B.GetLocation()).Z / 100.0);
	for (int32 i = 0; i < Cs.Num(); ++i)
	{
		FVector Wp = Ct.TransformPosition(Cs[i].GetLocation()) / 100.0;
		if (Wp.Z >= Top - 1e-3) Wp.Z += 0.12;   // head top above the head bone
		double Sx, Sy;
		if (!Project(CamP, CamR, FovDeg, Wp, Sx, Sy)) continue;
		X0 = FMath::Min(X0, Sx); X1 = FMath::Max(X1, Sx); Y0 = FMath::Min(Y0, Sy); Y1 = FMath::Max(Y1, Sy); bAny = true;
		Dist = FMath::Min(Dist, FVector::Dist(Wp, CamP));
	}
	return bAny;
}

// SM2-style group framing (refs group-fight-nm, street-fight-cars): mid-high, 4-6 m back, pitched 15-25 deg down, framing the hero
// plus his 3 nearest enemies. Each frame it scores candidate orbit yaws (hero / group on screen, no body within 2.6 m of the lens
// or on the lens-hero line, no wall in between, reward for every standing enemy in view, cost for turning) and turns toward the
// best at <= 55 deg/s: no cuts, no snaps. During a hit-stop freeze the camera holds its last transform exactly.
void AWHCombatDirector::CombatCamera(double RDt)
{
	UCameraComponent* Cam = Hero->Camera(); if (!Cam) return;
	const FVector Pc = Me->Pos;
	const FVector P3Pos = Cam->GetComponentLocation() / 100.0;
	const FRotator P3Rot = Cam->GetComponentRotation();
	const double P3Fov = Cam->FieldOfView;
	double NearD = 1e9;
	for (AWHEnemy* E : Enemies) if (E && E->Alive()) NearD = FMath::Min(NearD, HDist(E->Pos, Pc));
	const double Want = bFight && bEngaged && NearD < 16 ? 1 : 0;
	if (bDtFrozen && bCamLast && CamW > 0.5)
	{ // r03: while the hero is held the framing controller does not advance (nothing drifts across the victim's crop); only the 2-4 px hit shake runs
	  // on top of the held framing camera, so the whole frame keeps changing (other enemies, dust, the shake) while the two bodies stay still
		FRotator R = BaseCamR; double Fv = BaseCamFov;
		HitShake(R, Fv);
		Cam->SetWorldLocationAndRotation(BaseCamP * 100.0, R); Cam->SetFieldOfView(float(Fv));
		LastCamPos = BaseCamP; LastCamRot = R; LastFov = float(Fv);
		CamPosM = BaseCamP; CamRotF = R; CamFovF = Fv; Fx.SetCam(BaseCamP, Fv, R);
		ImpactVignette(Cam);
		return;
	}
	CamW = Damp(CamW, Want, Want > 0 ? 2.0 : 1.3, RDt);
	const double W = Smooth(CamW);
	CamPunchT += RDt;
	CamPunch = CamPunchT < 0.12 ? Smooth(CamPunchT / 0.12) : 1 - Smooth((CamPunchT - 0.12) / 0.4);
	if (!bCamInit) { CYaw = CYawGoal = FMath::DegreesToRadians(P3Rot.Yaw); CHero = Pc; bCamInit = true; }
	// hero anchor: tight follow, lag capped at 0.7 m (the hero never drifts toward the frame edge during a dash)
	CHero.X = Damp(CHero.X, Pc.X, 12, RDt); CHero.Y = Damp(CHero.Y, Pc.Y, 12, RDt); CHero.Z = Damp(CHero.Z, Pc.Z, 7, RDt);
	{ const FVector Lg = CHero - Pc; if (Lg.Size() > 0.7) CHero = Pc + Lg.GetSafeNormal() * 0.7; }
	// framing set: the 3 nearest standing enemies
	TArray<AWHEnemy*> Near, Stand;
	for (AWHEnemy* E : Enemies)
		if (E && E->Alive() && E->State != EWHEnemyState::Down && E->State != EWHEnemyState::Knock) Stand.Add(E);
	Stand.Sort([&Pc](const AWHEnemy& A, const AWHEnemy& B) { return HDist(A.Pos, Pc) < HDist(B.Pos, Pc); });
	for (AWHEnemy* E : Stand) if (Near.Num() < 3 && HDist(E->Pos, Pc) < 11) Near.Add(E);
	FVector OffT = FVector::ZeroVector;
	if (Near.Num()) { FVector Cn = FVector::ZeroVector; for (AWHEnemy* E : Near) Cn += E->Pos; OffT = Flat(Cn / Near.Num() - Pc) * 0.4; if (OffT.Size() > 1.4) OffT = OffT.GetSafeNormal() * 1.4; }
	COff.X = Damp(COff.X, OffT.X, 2.5, RDt); COff.Y = Damp(COff.Y, OffT.Y, 2.5, RDt); COff.Z = 0;
	const double Gz = GroundHeight(Pc.X, Pc.Y, Pc.Z + 0.5);
	const double Air = FMath::Clamp((Pc.Z - HH) - Gz, 0.0, 4.0);
	const double Pitch = FMath::Lerp(21.0, 15.5, FMath::Clamp(Air / 2.5, 0.0, 1.0));
	CPitch = Damp(CPitch, Pitch, 3, RDt);
	auto FocusNow = [&]() { FVector F = CHero + COff; F.Z = FMath::Max(Gz + 1.0, CHero.Z + 0.05); return F; };
	FVector Focus = FocusNow();
	auto RotFor = [&](double Yaw) { return FRotator(-CPitch, FMath::RadiansToDegrees(Yaw), 0); };
	auto CamFor = [&](double Yaw, double Dist) { return Focus - RotFor(Yaw).Vector() * Dist; };
	auto OutBy = [&](const FVector& Cp, const FRotator& R, const FVector& P, double M, double Fv = -1.0) -> double
	{
		double Sx, Sy; if (!Project(Cp, R, Fv > 0 ? Fv : CFov, P, Sx, Sy)) return 1.0;
		return FMath::Max(0.0, FMath::Max(M - Sx, Sx - (1 - M))) + FMath::Max(0.0, FMath::Max(M - Sy, Sy - (1 - M)));
	};
	const FVector HeroTop = Pc + FVector(0, 0, 0.95), HeroFeet = Pc - FVector(0, 0, HH);
	auto FramePen = [&](const FVector& Cp, const FRotator& R)
	{
		double C = 20 * (OutBy(Cp, R, HeroTop, 0.1) + OutBy(Cp, R, HeroFeet, 0.1));
		for (AWHEnemy* E : Near) C += 6 * (OutBy(Cp, R, E->Pos + FVector(0, 0, 1.75 * E->T.Scale), 0.04) + OutBy(Cp, R, E->Pos, 0.04));
		return C;
	};
	auto Score = [&](double Yaw, double Dist)
	{
		const FVector Cp = CamFor(Yaw, Dist); const FRotator R = RotFor(Yaw);
		double C = FramePen(Cp, R) + 0.9 * FMath::Abs(AngWrap(Yaw - CYaw));
		if (bSunKnown) C += 4.0 * FMath::Max(0.0, FVector::DotProduct(FlatNorm(R.Vector()), SunTo) - 0.25);   // r02: do not look straight into the sun (everything turns into black silhouettes)
		const FVector Dv = Cp - Focus; FTravHit H;
		if (Raycast(Focus, Dv.GetSafeNormal(), Dv.Size() + 0.3, H)) C += 8 + (Dv.Size() + 0.3 - H.Distance);
		for (AWHEnemy* E : Enemies)
		{
			if (!E || E->State == EWHEnemyState::Out || E->Stuck) continue;
			const double Dh = HDist(E->Pos, Cp); if (Dh < 3.6) C += (3.6 - Dh) * 4;
			const FVector Ec = E->Pos + FVector(0, 0, 1.0 * E->T.Scale);
			const FVector Q = FMath::ClosestPointOnSegment(Ec, Cp, Pc);
			if (FVector::Dist(Q, Ec) < 0.6 && FVector::Dist(Q, Pc) > 0.5) C += 3;
		}
		for (AWHEnemy* E : Stand)
			if (OutBy(Cp, R, E->Pos + FVector(0, 0, 1.7 * E->T.Scale), 0.02) + OutBy(Cp, R, E->Pos, 0.02) <= 0) C -= 0.6;
		{ // critic r01: no body may hide the hero. An enemy nearer to the lens than the hero whose (widened, scale-aware) screen area
		  // overlaps the hero's costs a lot (the brute is 1.3 x taller and ~1.4 x wider)
			double Hx, Hy; const double Dh0 = FVector::Dist(Cp, Pc);
			if (Project(Cp, R, CFov, Pc, Hx, Hy))
				for (AWHEnemy* E : Enemies)
				{
					if (!E || !E->Alive() || E->State == EWHEnemyState::Out || E->Stuck) continue;
					if (FVector::Dist(Cp, E->Pos + FVector(0, 0, 0.9)) > Dh0 - 0.3) continue;
					double Ex, Ey; if (!Project(Cp, R, CFov, E->Pos + FVector(0, 0, 0.9 * E->T.Scale), Ex, Ey)) continue;
					const double Sc = E->T.Scale, Wd = (0.075 + 0.05 * Sc) * (E->Type == EWHEnemyType::Brute ? 1.5 : 1.0);
					if (FMath::Abs(Ex - Hx) < Wd + 0.05 && FMath::Abs(Ey - Hy) < 0.3 * Sc) C += 7 * Sc;
				}
		}
		return C;
	};
	if (W > 0.002)
	{
		double BestY = CYawGoal, BestS = Score(CYawGoal, CDist);
		if (!CineS.bOn) for (int32 k = -7; k <= 7; ++k)   // (paused during the finisher beat: it orbits from the current yaw)
		{
			const double Y = CYaw + k * 0.17; const double S = Score(Y, CDist);
			if (S < BestS - 0.4) { BestS = S; BestY = Y; }
		}
		CYawGoal = BestY;
		const double Step = AngWrap(CYawGoal - CYaw) * (1 - FMath::Exp(-2.2 * RDt));
		CYaw = AngWrap(CYaw + FMath::Clamp(Step, -0.95 * RDt, 0.95 * RDt));
		double WantD = 6.0;
		for (double D : { 4.4, 5.0, 5.6 }) if (FramePen(CamFor(CYaw, D), RotFor(CYaw)) <= 0) { WantD = D; break; }
		CDist = Damp(CDist, WantD, 1.5, RDt);
	}
	else { CYaw = CYawGoal = FMath::DegreesToRadians(P3Rot.Yaw); CHero = Pc; COff = FVector::ZeroVector; }
	// hard hero margin: pull the framing offset back toward the hero until his head and feet sit inside a 7 % border
	for (int32 It = 0; It < 4; ++It)
	{
		if (OutBy(CamFor(CYaw, CDist), RotFor(CYaw), HeroTop, 0.07) + OutBy(CamFor(CYaw, CDist), RotFor(CYaw), HeroFeet, 0.07) <= 0) break;
		COff *= 0.5; CHero = CHero + (Pc - CHero) * 0.5; Focus = FocusNow();
	}
	FVector CamP = CamFor(CYaw, CDist); FRotator CamR = RotFor(CYaw);
	{ // walls between focus and lens: pull in (never closer than 2.2 m)
		const FVector Dv = CamP - Focus; FTravHit H;
		if (Raycast(Focus, Dv.GetSafeNormal(), Dv.Size() + 0.3, H)) CamP = Focus + Dv.GetSafeNormal() * FMath::Max(2.2, H.Distance - 0.3);
		const double Gy = GroundHeight(CamP.X, CamP.Y, CamP.Z + 0.3) + 0.4; if (CamP.Z < Gy) CamP.Z = Gy;
	}
	if (CamPunch > 0) CamP += CamR.Vector() * 0.22 * CamPunch;
	double Fov = CFov;
	// finisher beat (r02): the SAME framing camera pushes in and orbits ~30 deg to a low 3/4 view centred between hero and victim, eased
	// in over 0.45 s (slow-mo x0.25 runs with it) and out over 0.6 s. No cut, no position lerp between two vantage points (the r02
	// draft's side camera whipped 100 deg in 0.3 s and cut the hero off); the hero margin pass below still applies.
	if (CineS.bOn)
	{
		CineS.T += RDt;
		AWHEnemy* T = CineS.Target.Get();
		if (CineS.T > CineS.Dur || !T) { CineS.bOn = false; CineK = 0; }
		else
		{
			CineK = Smooth(CineS.T / 0.7) * (1 - Smooth((CineS.T - (CineS.Dur - 0.8)) / 0.8));
			const FVector Tp = T->Chest();
			if (!CineS.bSide)
			{ // orbit side chosen once: the candidate with no wall or other body between the lens and hero / victim
				double Bs = 1e18;
				for (double Off : { 0.32, -0.32, 0.18, -0.18, 0.0 })
				{
					const double Y = CYaw + Off;
					const FVector Mid0 = (Pc + Tp) * 0.5;
					const FVector Cp0 = Mid0 - RotFor(Y).Vector() * 3.6;
					double Sc = FMath::Abs(Off) < 0.01 ? 0.5 : 0.0;
					FTravHit H2; if (Raycast(Mid0, (Cp0 - Mid0).GetSafeNormal(), 3.9, H2)) Sc += 10;
					for (AWHEnemy* E : Enemies)
					{
						if (!E || E == T || E->State == EWHEnemyState::Out || E->Stuck) continue;
						const FVector Ep = E->Pos + FVector(0, 0, 1.0);
						if (HDist(Ep, Cp0) < 2.4) Sc += 6;
						for (const FVector& Tg : { Pc, Tp }) if (FVector::Dist(FMath::ClosestPointOnSegment(Ep, Cp0, Tg), Ep) < 0.8) Sc += 4;
					}
					if (Sc < Bs) { Bs = Sc; CineS.SideYaw = Off; }
				}
				CineS.bSide = true;
			}
			const double K = CineK;
			const FVector Mid = (Pc + Tp) * 0.5;
			const FVector Foc = Focus + (Mid - Focus) * (0.6 * K);
			const double Yw = CYaw + CineS.SideYaw * K;
			const double Pt = FMath::Lerp(CPitch, 14.0, K);
			const double Dst = FMath::Max(3.4, CDist - 1.3 * K);
			CamR = FRotator(-Pt, FMath::RadiansToDegrees(Yw), 0);
			CamP = Foc - CamR.Vector() * Dst;
			const FVector Dv = CamP - Foc; FTravHit Hh;
			if (Raycast(Foc, Dv.GetSafeNormal(), Dv.Size() + 0.3, Hh)) CamP = Foc + Dv.GetSafeNormal() * FMath::Max(2.0, Hh.Distance - 0.3);
			const double Gy2 = GroundHeight(CamP.X, CamP.Y, CamP.Z + 0.3) + 0.4; if (CamP.Z < Gy2) CamP.Z = Gy2;
			Fov = FMath::Lerp(Fov, 68.0, K);
		}
	}
	// blend from / to the P3 chase camera
	FVector OutP = P3Pos + (CamP - P3Pos) * W;
	FRotator OutR = FQuat::Slerp(P3Rot.Quaternion(), CamR.Quaternion(), W).Rotator();
	const double OutFov = FMath::Lerp(P3Fov, Fov, W);
	// shake / impact (trauma decays and the shake phase advances in real time, but not during a hit-stop freeze)
	CamTrauma = FMath::Max(0.0, CamTrauma - RDt * 1.8);
	CamImpact = FMath::Max(0.0, CamImpact - RDt * 3.0);
	ShakePh += RDt * 47.0;
	if (CamTrauma > 0.001 || CamImpact > 0.001)
	{
		const double Tr = CamTrauma * CamTrauma;
		OutR.Pitch += Tr * 1.6 * FMath::Sin(ShakePh * 1.3) - CamImpact * 0.9;
		OutR.Yaw += Tr * 1.3 * FMath::Sin(ShakePh * 0.9 + 1.7);
		OutR.Roll += Tr * 1.0 * FMath::Sin(ShakePh * 1.1 + 0.4);
	}
	BubbleP = OutP;   // the camera bubble (Separate) uses the camera BEFORE the bone-based margin pass: the sim never depends on bone poses (nullrhi vs rendered runs stay identical)
	{ // hero margin (critic r01: the hero was cut at the frame edge): dolly back along the view axis. A SOFT controller aims at a 10 %
	  // border (the pull rises at <= 4 m/s and relaxes at 0.8 m/s), and a hard pass (8 cm steps, at once) guarantees 5.5 % even when the
	  // hero's bones jump (a flip, arms up): a sudden pose change is the only thing that can still pop the camera.
		MarginPull = FMath::Max(0.0, MarginPull - RDt * 0.8);
		const FVector Fw = OutR.Vector();
		auto HeroMargin = [&](double Pull, const FVector& Shift)
		{
			double X0, Y0, X1, Y1, Dd;
			if (!ScreenBox(Hero->GetMesh(), OutP - Fw * Pull + Shift, OutR, OutFov, X0, Y0, X1, Y1, Dd)) return -1.0;
			return FMath::Min(FMath::Min(X0, Y0), FMath::Min(1.0 - X1, 1.0 - Y1));
		};
		if (bFight && bEngaged)
		{ // the soft target looks 0.18 s ahead (the hero's velocity: moving the camera by -V dt equals the hero moving by +V dt), so a dash
		  // or a flip widens the frame BEFORE the hard pass has to snap it
			const FVector Ahead = -Me->Vel * 0.18;
			double Need = MarginPull;
			for (int32 It = 0; It < 40 && (HeroMargin(Need, FVector::ZeroVector) < 0.10 || HeroMargin(Need, Ahead) < 0.08); ++It) Need += 0.08;
			if (Need > MarginPull) MarginPull = FMath::Min(Need, MarginPull + RDt * 8.0);
			for (int32 It = 0; It < 40 && HeroMargin(MarginPull, FVector::ZeroVector) < 0.055; ++It) MarginPull += 0.08;
		}
		OutP -= Fw * MarginPull;
	}
	BaseCamP = OutP; BaseCamR = OutR; BaseCamFov = OutFov;   // the framing camera BEFORE the r03 hit shake (held while the hero is held)
	double ShFov = OutFov;
	HitShake(OutR, ShFov);
	Cam->SetWorldLocationAndRotation(OutP * 100.0, OutR);
	Cam->SetFieldOfView(float(ShFov));
	LastCamPos = OutP; LastCamRot = OutR; LastFov = float(ShFov); bCamLast = true;
	CamPosM = OutP; CamRotF = OutR; CamFovF = ShFov; Fx.SetCam(OutP, OutFov, OutR);
	ImpactVignette(Cam);
}

// r03 impact vignette: over the hold the vignette ramps from the map's 0.3 up by VigAmp (linear per frame, so every hold frame changes), and eases back in 2 frames.
// It darkens the frame EDGES only: the whole-frame diff stays >= 1.0 during a hold while the hero / victim in the middle of the frame stay put.
void AWHCombatDirector::ImpactVignette(UCameraComponent* Cam) const
{
	if (!Cam || VigAmp <= 0.0) return;   // off: the camera's post-process settings are left untouched
	const double K = FMath::Clamp((ShakeUntil - RTime) * 30.0, 0.0, 1.0);
	const double Ramp = FMath::Clamp((RTime - ShakeStart) * 60.0 / 6.0, 0.0, 1.0);
	Cam->PostProcessSettings.bOverride_VignetteIntensity = K > 0.0;
	Cam->PostProcessSettings.VignetteIntensity = float(VigBase + VigAmp * K * Ramp);
	Cam->PostProcessBlendWeight = K > 0.0 ? 1.0f : 0.0f;
}

// r03 hit shake: a RADIAL shake of HitShakePx (1080p px displacement at the frame edge) at HitShakeHz, from the contact frame for the hold + 2 frames (full for
// the hold, eased out over the last 2 frames): a small roll about the view axis plus a small zoom pulse (FOV), both proportional to the distance from the
// frame centre. The whole frame keeps changing (buildings, street, far enemies move 2-4 px at the edges) while the hero / victim near the middle move well
// under a pixel, so the victim crop stays still (experiment 1: a plain 2 px translation moved every crop by ~1.4 gray levels per frame, 0.6 px did nothing
// for the whole-frame diff). Both start at zero displacement, so the contact frame itself does not jump.
void AWHCombatDirector::HitShake(FRotator& R, double& Fov) const
{
	ShakeOutPx = ShakeOutPx2 = 0;
	const double K = FMath::Clamp((ShakeUntil - RTime) * 30.0, 0.0, 1.0);
	if (K <= 0.0 || HitShakePx <= 0.0) return;
	const double T = RTime - ShakeStart;
	// quadrature: the roll's speed is largest where the zoom's is smallest, so the per-frame motion at the frame edge stays ~constant over the whole hold
	// (a plain sine has zero speed at its peak, which is where 5-frame holds dipped below a whole-frame diff of 1.0 in experiment 3)
	const double Om = 2.0 * PI * HitShakeHz * T;
	ShakeOutPx = HitShakePx * K * FMath::Sin(Om);                          // roll: edge displacement, px
	ShakeOutPx2 = 0.5 * HitShakePx * K * (1.0 - FMath::Cos(Om));          // zoom: edge displacement, px (0 .. HitShakePx)
	R.Roll += FMath::RadiansToDegrees(ShakeOutPx / 1000.0) * (ShakeAy >= 0 ? 1.0 : -1.0);
	Fov = FMath::RadiansToDegrees(2.0 * FMath::Atan(FMath::Tan(FMath::DegreesToRadians(Fov * 0.5)) * (1.0 - ShakeOutPx2 / 960.0)));
}

// experiment runs (-WHCmbSweep=1): every blow gets the next (shake px, shake Hz, flare size) variant, logged as an event, so ONE movie shows how each
// setting behaves in the victim-crop / whole-frame tests. Normal runs: no-op.
void AWHCombatDirector::BlowVariant()
{
	if (!bShakeSweep) return;
	static const double Px[] = { 0, 0, 3, 3 }, Hz[] = { 4, 4, 4, 4 }, Fk[] = { 1.0, 1.0, 1.0, 1.0 }, Hr[] = { 0, 2.5, 2.5, 4.0 };
	const int32 V = ShakeSweepN++ % 4;
	HitShakePx = Px[V]; HitShakeHz = Hz[V]; Fx.FlareK = Fk[V]; HoldRadius = Hr[V];
	LogEvent(FString::Printf(TEXT("variant %d shake %.1f px %.1f Hz flareK %.2f holdR %.1f"), V, Px[V], Hz[V], Fk[V], Hr[V]));
}

// ------------------------------------------------------------------------------------------------ per frame
void AWHCombatDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!Hero || !Me || !Hero->GetTraversal()) return;
	const double Dt = FMath::Clamp(double(DeltaSeconds), 0.0, 0.1);
	const double RDt = FMath::Clamp(double(GetWorld()->DeltaRealTimeSeconds), 0.0, 0.1);
	bDtFrozen = bHitStop;   // the hold applied to THIS tick was set by the previous tick's UpdateTime
	const double HDt = bDtFrozen ? 0.0 : Dt;   // r03: the hero's own dt (0 while he is held; the rest of the world runs)
	Time += Dt; RTime += RDt; ++Frame;
	if (Frame == 40) LogRenderRes();
	if (TimeScale < 0.999) { SlowmoGameT += Dt; SlowmoRealT += RDt; }
	RunBeats();
	// hero (spidey.js override): input -> moves -> body placed through the traversal component
	Me->Override(HDt);
	PlayerFeet = Me->Pos - FVector(0, 0, HH);
	if (bFight)
	{
		FVector C = FVector::ZeroVector; int32 N = 0;
		for (AWHEnemy* E : Enemies) if (E && E->Alive()) { C += E->Pos; ++N; }
		if (N) FightCenter += (C / N - FightCenter) * (1 - FMath::Exp(-0.5 * Dt));
			if (bEngaged) { DirectorStep(Dt); Reinforce(Dt); }
		if (!N && Enemies.Num()) { ClearT += Dt; if (ClearT > 1.3 && (Me->IsFree() || ClearT > 3)) EndFight(true); } else ClearT = 0;
	}
	for (AWHEnemy* E : Enemies) if (E && (bEngaged || !E->Alive())) E->Update(E->bHeld ? 0.0 : Dt);
	Separate();
	for (AWHEnemy* E : Enemies) if (E) E->Late(E->bHeld ? 0.0 : Dt);
	Me->Late(HDt);
	if (PendingShot.IsValid() && Time >= PendingShotAt) { AWHEnemy* T = PendingShot.Get(); PendingShot = nullptr; if (T->Alive()) FireWeb(T); }
	UpdateShots(Dt);
	for (FLoose& L : Loose)
	{
		if (L.bRest || !L.Obj) continue;
		L.Vel.Z -= 20 * Dt; L.Pos += L.Vel * Dt;
		const double Gy = GroundHeight(L.Pos.X, L.Pos.Y, L.Pos.Z + 0.5);
		if (L.Pos.Z < Gy + 0.03) { L.Pos.Z = Gy + 0.03; if (L.Vel.Z < -3) { L.Vel.Z *= -0.3; L.Vel.X *= 0.5; L.Vel.Y *= 0.5; } else L.bRest = true; }
		L.Obj->SetWorldLocationAndRotation(L.Pos * 100.0, FRotator(Time * 700, Time * 400, 0));
	}
	// threats -> spider-sense (streaks + slow-mo hint for the first warnings of a fight)
	Threats.RemoveAll([this](const FWHThreat& T) { return T.At <= Time - 0.15 || !T.E.IsValid() || !T.E->Alive(); });
	double Lvl = 0; bool bRed = false;
	for (FWHThreat& T : Threats)
	{
		const double R = T.At - Time; const double K = FMath::Clamp(1 - R / 0.75, 0.0, 1.0) * (R > -0.1 ? 1 : 0);
		if (K > Lvl) { Lvl = K; bRed = T.Kind == "gun"; }
		if (!T.bHinted && R < 0.5 && R > 0.2)
		{
			T.bHinted = true;
			if (WarnCount < 2 && Hero->GetTraversal()->Mode() == EWebTravMode::Ground) Slowmo(0.28, 0.45, 0.2);
			++WarnCount;
		}
	}
	SenseLvl = bEngaged ? Lvl : 0;
	Fx.Sense(SenseLvl, bRed, Hero->HeadM() + FVector(0, 0, 0.08), Dt);
	Fx.Update(Dt, RDt);
	ComboT += Dt; if (ComboT > 3.2) ComboN = 0;
	if (bHitStop) ++NFrozenFrames;
	CombatCamera(RDt);
	FrameRecord();
	UpdateTime();   // (after the record: the record shows the hold / time scale that was applied to THIS frame)
	// automation: telemetry row, stills, quit
	TelemetryRows.Add(FString::Printf(TEXT("%lld,%.4f,%.4f,%.3f,%s,%.3f,%.3f,%.3f,%.0f,%.2f,%d,%.2f,%d,%s,%s,%.2f,%s"),
		Frame, RTime, Time, TimeScale, *Me->MoveName().ToString(), Me->Pos.X, Me->Pos.Y, Me->Pos.Z, Me->Hp, Me->Focus, ComboN, SenseLvl,
		Threats.Num(), CineS.bOn ? *CineS.Kind.ToString() : TEXT("-"), Hero->GetTraversal()->Mode() == EWebTravMode::Ground ? TEXT("ground") : TEXT("air"),
		CamW, *StateString()));
	while (NextShot < ShotTimes.Num() && RTime >= ShotTimes[NextShot])
	{
		const FString File = OutDir / FString::Printf(TEXT("%s_%02d_t%05.2f.png"), *ShotName, NextShot, ShotTimes[NextShot]);
		FScreenshotRequest::RequestScreenshot(File, false, false);
		LogEvent(TEXT("still ") + File);
		++NextShot;
	}
	if (QuitAt > 0 && RTime >= QuitAt && !bQuitSent)
	{
		bQuitSent = true;
		WriteTelemetry(); WriteSummary();
		if (APlayerController* PC = GetWorld()->GetFirstPlayerController()) PC->ConsoleCommand(TEXT("quit"));
		else FGenericPlatformMisc::RequestExit(false);
	}
}

// r02 per-frame record for the pixel measurements: camera, and each character's screen-space box (all skeleton bones projected with
// the final camera of this frame; head top padded). The rendered frame shows this simulation state (movie frames lag by the render
// pipeline; docs/night1/combat/measure_r02.py calibrates the offset from the hit-stop freezes).
void AWHCombatDirector::FrameRecord()
{
	if (!bFight && Enemies.Num() == 0) return;
	auto Box = [this](const USkeletalMeshComponent* M, double& X0, double& Y0, double& X1, double& Y1, double& Dist) -> bool
	{ return ScreenBox(M, CamPosM, CamRotF, CamFovF, X0, Y0, X1, Y1, Dist); };
	double X0, Y0, X1, Y1, D;
	// r03: frz = the hero was held (dt 0) in THIS frame; shk = the hit shake's screen offset in 1080p px (along yaw, pitch); each enemy row ends with
	// [.., alive, visual yaw deg (actor yaw + hit twist), held in this frame, r04: body tilt deg (up axis vs vertical: recoil lean + tumble)]
	FString Row = FString::Printf(TEXT("{\"f\":%lld,\"rt\":%.4f,\"ts\":%.3f,\"frz\":%d,\"shk\":[%.2f,%.2f],\"cine\":%.2f,\"cam\":[%.3f,%.3f,%.3f,%.2f,%.2f,%.2f,%.2f],\"move\":\"%s\","),
		Frame, RTime, TimeScale, bDtFrozen ? 1 : 0, ShakeOutPx, ShakeOutPx2, CineK, CamPosM.X, CamPosM.Y, CamPosM.Z, CamRotF.Pitch, CamRotF.Yaw, CamRotF.Roll, CamFovF, *Me->MoveName().ToString());
	Box(Hero->GetMesh(), X0, Y0, X1, Y1, D);
	Row += FString::Printf(TEXT("\"hero\":[%.3f,%.3f,%.3f,%.4f,%.4f,%.4f,%.4f,%.2f],\"e\":["), Me->Pos.X, Me->Pos.Y, Me->Pos.Z - HH, X0, Y0, X1, Y1, D);
	bool bFirst = true;
	for (AWHEnemy* E : Enemies)
	{
		if (!E) continue;
		const bool bOk = Box(E->Mesh, X0, Y0, X1, Y1, D);
		const bool bWarn = E->WarnOn();
		Row += FString::Printf(TEXT("%s[\"%s\",\"%s\",\"%s\",%.3f,%.3f,%.3f,%.4f,%.4f,%.4f,%.4f,%.2f,%d,%d,%.1f,%d,%.1f]"), bFirst ? TEXT("") : TEXT(","), *E->Tag(), E->TypeName(), E->StateName(),
			E->Pos.X, E->Pos.Y, E->Pos.Z, bOk ? X0 : -1.0, bOk ? Y0 : -1.0, bOk ? X1 : -1.0, bOk ? Y1 : -1.0, D, bWarn ? 1 : 0, E->Alive() ? 1 : 0,
			FMath::RadiansToDegrees(E->VisYaw()), E->bHeld ? 1 : 0, E->TiltNow);
		bFirst = false;
	}
	Row += TEXT("]}");
	FrameRows.Add(Row);
}

FString AWHCombatDirector::StateString() const
{
	FString S;
	for (const AWHEnemy* E : Enemies)
	{
		if (!E) continue;
		S += FString::Printf(TEXT("%s%c:%s%s:%d%s"), S.IsEmpty() ? TEXT("") : TEXT(" "), E->TypeName()[0], E->StateName(),
			E->Stuck == 1 ? TEXT("-wall") : E->Stuck == 2 ? TEXT("-ground") : TEXT(""), FMath::Max(0, FMath::RoundToInt(E->Hp)),
			E->Web > 0.01 ? *FString::Printf(TEXT(":w%.1f"), E->Web) : TEXT(""));
	}
	return S;
}

void AWHCombatDirector::LogEvent(const FString& S)
{
	const FString Row = FString::Printf(TEXT("{\"rt\":%.3f,\"gt\":%.3f,\"ts\":%.3f,\"move\":\"%s\",\"ev\":\"%s\"}"), RTime, Time, TimeScale,
		Me ? *Me->MoveName().ToString() : TEXT("-"), *S.Replace(TEXT("\""), TEXT("'")));
	EventRows.Add(Row);
	UE_LOG(LogWebHomage, Display, TEXT("WH_CMB_EV %s"), *Row);
}

void AWHCombatDirector::WriteTelemetry()
{
	if (OutDir.IsEmpty()) return;
	FString Csv = TEXT("frame,rt,gt,timescale,move,x_m,y_m,z_m,hp,focus,combo,sense,threats,cine,trav,cam_w,enemies\n");
	for (const FString& R : TelemetryRows) { Csv += R; Csv += TEXT("\n"); }
	FFileHelper::SaveStringToFile(Csv, *(OutDir / (ShotName + TEXT("_telemetry.csv"))));
	FFileHelper::SaveStringToFile(FString::Join(EventRows, TEXT("\n")) + TEXT("\n"), *(OutDir / (ShotName + TEXT("_events.jsonl"))));
	FFileHelper::SaveStringToFile(FString::Join(BeatRows, TEXT("\n")) + TEXT("\n"), *(OutDir / (ShotName + TEXT("_beats.jsonl"))));
	FFileHelper::SaveStringToFile(FString::Join(FrameRows, TEXT("\n")) + TEXT("\n"), *(OutDir / (ShotName + TEXT("_frames.jsonl"))));
}

// r04: disclose the render resolution of every capture (output size, r.ScreenPercentage, the internal pre-TSR size: same rule as WebHomageAutomation's perf json)
void AWHCombatDirector::LogRenderRes() const
{
	const FWHRenderRes R = WHComputeRenderRes();
	UE_LOG(LogWebHomage, Display, TEXT("WH_CMB_RES output %dx%d r.ScreenPercentage %.1f mode %s internal %dx%d (pre-TSR) TSR upscale %.2f"), R.Output.X, R.Output.Y, R.ScreenPercentage, *R.Mode,
		R.Internal.X, R.Internal.Y, R.Frac > 0.f ? 1.f / R.Frac : 0.f);
}

void AWHCombatDirector::WriteSummary()
{
	bSummaryDone = true;
	if (OutDir.IsEmpty()) return;
	int32 Alive = 0; FString Final;
	for (const AWHEnemy* E : Enemies) if (E) { Alive += E->Alive() ? 1 : 0; }
	const FString J = FString::Printf(TEXT("{\n \"engine\": \"ue5.8\", \"frames\": %lld, \"real_s\": %.3f, \"game_s\": %.3f,\n \"enemies\": %d, \"enemies_alive\": %d, \"final_states\": \"%s\",\n")
		TEXT(" \"hero_hp\": %.0f, \"hero_focus\": %.2f, \"damage_taken\": %.0f,\n \"hits\": %d, \"whiffs\": %d, \"kos\": %d, \"launches\": %d, \"air_hits\": %d, \"finishers\": %d,\n")
		TEXT(" \"dodges\": %d, \"perfect_dodges\": %d, \"web_hits\": %d, \"enemy_melee_hits\": %d, \"shots\": %d, \"shot_hits\": %d,\n")
		TEXT(" \"hitstops\": %d, \"frozen_frames\": %d, \"slowmos\": %d, \"min_timescale\": %.3f, \"slowmo_game_s\": %.3f, \"slowmo_real_s\": %.3f,\n")
		TEXT(" \"attack_starts\": %d, \"max_attack_gap_s\": %.3f, \"spawned\": %d, \"reserve_left\": %d,\n \"beats\": %d, \"beats_fired\": %d, \"fx_spawned\": %d\n}\n"),
		Frame, RTime, Time, Enemies.Num(), Alive, *StateString(), Me->Hp, Me->Focus, DamageTaken, NHits, NWhiffs, NKOs, NLaunch, NAirHits, NFinishers,
		NDodges, NPerfect, NWebHits, NEnemyHits, NShots, NShotHits, NHitStops, NFrozenFrames, NSlowmo, MinTimeScale, SlowmoGameT, SlowmoRealT,
		NAttackStarts, MaxAttackGap, Enemies.Num(), Reserve,
		Beats.Num(), Beats.FilterByPredicate([](const FWHBeat& B) { return B.bFired; }).Num(), Fx.Spawned);
	FFileHelper::SaveStringToFile(J, *(OutDir / (ShotName + TEXT("_summary.json"))));
	UE_LOG(LogWebHomage, Display, TEXT("WH_CMB_SUMMARY %s"), *J.Replace(TEXT("\n"), TEXT(" ")));
}
