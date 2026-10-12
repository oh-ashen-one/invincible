// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Traversal/WebTravScript.h"
#include "WebHomage.h"

#include "HAL/FileManager.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"


// Minimal JSON reader for the script schema (objects, arrays, numbers, bools, strings). The Json module is not a direct
// dependency of WebHomage (Build.cs is integrator-owned), so this avoids a link dependency.
namespace WebTravJson
{
	struct FVal
	{
		enum EType { Null, Bool, Num, Str, Arr, Obj } Type = Null;
		bool B = false; double N = 0; FString S;
		TArray<TSharedPtr<FVal>> A;
		TMap<FString, TSharedPtr<FVal>> O;
		const FVal* Get(const TCHAR* K) const { const TSharedPtr<FVal>* P = O.Find(K); return P ? P->Get() : nullptr; }
	};
	struct FParser
	{
		const TCHAR* P;
		void Ws() { while (*P && FChar::IsWhitespace(*P)) ++P; }
		TSharedPtr<FVal> Parse()
		{
			Ws();
			TSharedPtr<FVal> V = MakeShared<FVal>();
			if (*P == TEXT('{'))
			{
				++P; V->Type = FVal::Obj; Ws();
				while (*P && *P != TEXT('}'))
				{
					Ws(); TSharedPtr<FVal> K = Parse(); Ws();
					if (*P == TEXT(':')) ++P;
					TSharedPtr<FVal> X = Parse();
					if (K.IsValid()) V->O.Add(K->S, X);
					Ws(); if (*P == TEXT(',')) ++P; Ws();
				}
				if (*P) ++P;
			}
			else if (*P == TEXT('['))
			{
				++P; V->Type = FVal::Arr; Ws();
				while (*P && *P != TEXT(']')) { V->A.Add(Parse()); Ws(); if (*P == TEXT(',')) ++P; Ws(); }
				if (*P) ++P;
			}
			else if (*P == TEXT('"'))
			{
				++P; V->Type = FVal::Str;
				while (*P && *P != TEXT('"')) { if (*P == TEXT('\\') && P[1]) ++P; V->S.AppendChar(*P); ++P; }
				if (*P) ++P;
			}
			else if (FCString::Strncmp(P, TEXT("true"), 4) == 0) { P += 4; V->Type = FVal::Bool; V->B = true; }
			else if (FCString::Strncmp(P, TEXT("false"), 5) == 0) { P += 5; V->Type = FVal::Bool; V->B = false; }
			else if (FCString::Strncmp(P, TEXT("null"), 4) == 0) { P += 4; }
			else
			{
				FString Num;
				while (*P && (FChar::IsDigit(*P) || *P == TEXT('-') || *P == TEXT('+') || *P == TEXT('.') || *P == TEXT('e') || *P == TEXT('E'))) { Num.AppendChar(*P); ++P; }
				if (Num.IsEmpty()) ++P;
				V->Type = FVal::Num; V->N = FCString::Atod(*Num);
			}
			return V;
		}
	};
}

void UWebTravScript::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	const TCHAR* Cmd = FCommandLine::Get();
	FParse::Value(Cmd, TEXT("WHTravSeed="), SeedValue);
	FString Path;
	if (FParse::Value(Cmd, TEXT("WHTravScript="), Path))
	{
		FString Text;
		if (!FFileHelper::LoadFileToString(Text, *Path))
		{
			UE_LOG(LogWebHomage, Error, TEXT("WH_TRAV_SCRIPT cannot read %s"), *Path);
		}
		else
		{
			WebTravJson::FParser Parser{ *Text };
			const TSharedPtr<WebTravJson::FVal> RootP = Parser.Parse();
			const WebTravJson::FVal* Root = RootP.Get();
			if (!Root || Root->Type != WebTravJson::FVal::Obj)
			{
				UE_LOG(LogWebHomage, Error, TEXT("WH_TRAV_SCRIPT invalid JSON %s"), *Path);
			}
			else
			{
				using WebTravJson::FVal;
				if (const FVal* N = Root->Get(TEXT("name"))) ScriptName = N->S;
				if (const FVal* Spawn = Root->Get(TEXT("spawn")))
				{
					const FVal* P = Spawn->Get(TEXT("pos"));
					if (P && P->A.Num() == 3)
					{
						SpawnPos = FVector(P->A[0]->N, P->A[1]->N, P->A[2]->N);
						bHasSpawn = true;
					}
					if (const FVal* Y = Spawn->Get(TEXT("yaw"))) SpawnYaw = Y->N;
					if (const FVal* CP = Spawn->Get(TEXT("camPitch"))) SpawnCamPitch_ = CP->N;
					const FVal* SV = Spawn->Get(TEXT("vel"));
					if (SV && SV->A.Num() == 3) SpawnVel = FVector(SV->A[0]->N, SV->A[1]->N, SV->A[2]->N);
				}
				if (const FVal* Sd = Root->Get(TEXT("seed"))) SeedValue = int32(Sd->N);
				// round 17: per-script tuning ("tune": "Name=V,..." traversal floats, "camTune": camera doubles) -- same format as -WHTravTune /
				// -WHCamTune, applied before them (the command line wins); lets a route carry its own settings through capture_round.sh
				if (const FVal* TU = Root->Get(TEXT("tune"))) { if (TU->Type == FVal::Str) TuneStr = TU->S; }
				if (const FVal* CT = Root->Get(TEXT("camTune"))) { if (CT->Type == FVal::Str) CamTuneStr = CT->S; }
				if (const FVal* KeysJ = Root->Get(TEXT("keys")))
				{
					for (const TSharedPtr<FVal>& O : KeysJ->A)
					{
						if (!O.IsValid() || O->Type != FVal::Obj) continue;
						FKey K;
						if (const FVal* T = O->Get(TEXT("t"))) K.T = T->N;
						auto Vec2 = [&O](const TCHAR* Name, TOptional<FVector2D>& Out)
						{
							const FVal* A = O->Get(Name);
							if (A && A->A.Num() == 2) Out = FVector2D(A->A[0]->N, A->A[1]->N);
						};
						auto Bool = [&O](const TCHAR* Name, TOptional<bool>& Out)
						{
							const FVal* B = O->Get(Name);
							if (B && B->Type == FVal::Bool) Out = B->B;
						};
						Vec2(TEXT("move"), K.Move); Vec2(TEXT("look"), K.Look);
						Bool(TEXT("swing"), K.Swing); Bool(TEXT("jump"), K.Jump); Bool(TEXT("sprint"), K.Sprint);
						Bool(TEXT("zip"), K.Zip); Bool(TEXT("drop"), K.Drop); Bool(TEXT("quick"), K.Quick);
						Bool(TEXT("autoChain"), K.AutoChain);
						Bool(TEXT("trick"), K.Trick);
						if (const FVal* FL = O->Get(TEXT("flip"))) { if (FL->Type == FVal::Str) K.Flip = FL->S; else K.Flip = FString(); }
						if (const FVal* TE = O->Get(TEXT("trickEvery"))) K.TrickEvery = int32(TE->N);
						if (const FVal* SE = O->Get(TEXT("skyEvery"))) K.SkyEvery = int32(SE->N);
						if (const FVal* ST = O->Get(TEXT("skyTricks"))) K.SkyTricks = int32(ST->N);
						if (const FVal* SH = O->Get(TEXT("skyRepressH"))) K.SkyRepressH = SH->N;
						if (const FVal* SM = O->Get(TEXT("skyMax"))) K.SkyMax = SM->N;
						if (const FVal* SP = O->Get(TEXT("skyPhase"))) K.SkyPhase = SP->N;
						if (const FVal* HD = O->Get(TEXT("heading"))) { if (HD->Type == FVal::Num) K.Heading = HD->N; else K.Heading = 1e9; }
						if (const FVal* RP = O->Get(TEXT("releasePhase"))) K.ReleasePhase = RP->N;
						if (const FVal* GP = O->Get(TEXT("gap"))) K.Gap = GP->N;
						if (const FVal* RV = O->Get(TEXT("repressVz"))) K.RepressVz = RV->N;
						Keys.Add(K);
					}
					Keys.Sort([](const FKey& A, const FKey& B) { return A.T < B.T; });
				}
				bActive = true;
				UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV_SCRIPT '%s' keys=%d spawn=%s yaw=%.1f seed=%d"), *ScriptName, Keys.Num(),
					*SpawnPos.ToString(), SpawnYaw, SeedValue);
			}
		}
	}
	if (!FParse::Value(Cmd, TEXT("WHTravCsv="), CsvPath) && bActive)
	{
		FString Dir, Name = TEXT("trav");
		if (FParse::Value(Cmd, TEXT("WHShotDir="), Dir))
		{
			FParse::Value(Cmd, TEXT("WHShotName="), Name);
			CsvPath = Dir / (Name + TEXT("_telemetry.csv"));
		}
	}
	if (!CsvPath.IsEmpty())
	{
		CsvPath = FPaths::ConvertRelativePathToFull(CsvPath);
		IFileManager::Get().Delete(*CsvPath, false, true, true);
		UE_LOG(LogWebHomage, Display, TEXT("WH_TRAV_CSV %s"), *CsvPath);
	}
}

void UWebTravScript::Deinitialize()
{
	Flush();
	Super::Deinitialize();
}

FWebTravInput UWebTravScript::Sample(double T, FVector2D& OutLookRate) const
{
	FWebTravInput I;
	FVector2D Look = FVector2D::ZeroVector;
	for (const FKey& K : Keys)
	{
		if (K.T > T + 1e-6) break;
		if (K.Move) I.Move = *K.Move;
		if (K.Look) Look = *K.Look;
		if (K.Swing) I.bSwing = *K.Swing;
		if (K.Jump) I.bJump = *K.Jump;
		if (K.Sprint) I.bSprint = *K.Sprint;
		if (K.Zip) I.bZip = *K.Zip;
		if (K.Drop) I.bDrop = *K.Drop;
		if (K.Quick) I.bQuick = *K.Quick;
		if (K.Trick) I.bTrick = *K.Trick;
		if (K.Flip) I.FlipReq = *K.Flip;
	}
	if (I.Move.Size() > 1.0) I.Move = I.Move.GetSafeNormal();
	OutLookRate = FVector2D(FMath::DegreesToRadians(Look.X), FMath::DegreesToRadians(Look.Y));
	return I;
}

int32 UWebTravScript::TrickEveryAt(double T) const
{
	int32 N = 0;
	for (const FKey& K : Keys)
	{
		if (K.T > T + 1e-6) break;
		if (K.AutoChain) N = K.TrickEvery;
	}
	return N;
}

int32 UWebTravScript::SkyEveryAt(double T, double& OutRepressH, int32& OutTricks, double& OutMax, double& OutPhase) const
{
	int32 N = 0;
	for (const FKey& K : Keys)
	{
		if (K.T > T + 1e-6) break;
		if (K.AutoChain) { N = K.SkyEvery; OutRepressH = K.SkyRepressH; OutTricks = K.SkyTricks; OutMax = K.SkyMax; OutPhase = K.SkyPhase; }
	}
	return N;
}

bool UWebTravScript::HeadingAt(double T, double& OutYawDeg) const
{
	bool bOn = false;
	for (const FKey& K : Keys)
	{
		if (K.T > T + 1e-6) break;
		if (K.Heading) { bOn = *K.Heading < 1e8; OutYawDeg = *K.Heading; }
	}
	return bOn;
}

bool UWebTravScript::AutoChainAt(double T, double& OutReleasePhase, double& OutGap, double& OutRepressVz) const
{
	bool bOn = false;
	for (const FKey& K : Keys)
	{
		if (K.T > T + 1e-6) break;
		if (K.AutoChain) { bOn = *K.AutoChain; OutReleasePhase = K.ReleasePhase; OutGap = K.Gap; OutRepressVz = K.RepressVz; }
	}
	return bOn;
}

void UWebTravScript::AddTelemetryRow(const FString& Row)
{
	if (CsvPath.IsEmpty()) return;
	Rows.Add(Row);
	if (Rows.Num() >= 120) Flush();
}

void UWebTravScript::Flush()
{
	if (CsvPath.IsEmpty() || (Rows.Num() == 0 && bWroteHeader)) return;
	FString Out;
	if (!bWroteHeader)
	{
		Out += CsvHeader + TEXT("\n");
		bWroteHeader = true;
	}
	for (const FString& R : Rows) { Out += R; Out += TEXT("\n"); }
	Rows.Reset();
	FFileHelper::SaveStringToFile(Out, *CsvPath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM, &IFileManager::Get(), FILEWRITE_Append);
}
