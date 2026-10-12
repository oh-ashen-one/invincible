// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Characters/WHCharLoopWalker.h"
#include "Characters/WHCharAnimInstance.h"
#include "Characters/WHCharStage.h"
#include "Components/SkeletalMeshComponent.h"
#include "Materials/MaterialInterface.h"
#include "EngineUtils.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "HAL/FileManager.h"

namespace
{
	// telemetry (one buffer per process; the crowd map has one avoiding group)
	FString GLogPath; FString GLogBuf; bool GLogInit = false; int32 GLogFrames = 0;
	void FlushLog()
	{
		if (GLogPath.IsEmpty() || GLogBuf.IsEmpty()) return;
		FFileHelper::SaveStringToFile(GLogBuf, *GLogPath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM, &IFileManager::Get(), FILEWRITE_Append);
		GLogBuf.Reset();
	}
	void InitLog()
	{
		if (GLogInit) return;
		GLogInit = true;
		if (FParse::Value(FCommandLine::Get(), TEXT("WHWalkerLog="), GLogPath) && !GLogPath.IsEmpty())
		{
			IFileManager::Get().Delete(*GLogPath);
			GLogBuf = TEXT("frame,time,label,x,y,yaw,offset,min_pair_dist\n");
		}
	}
	constexpr float Horizons[] = {0.f, 0.5f, 1.0f, 1.5f, 2.0f};
	bool AvoidOff() { static const bool b = FParse::Param(FCommandLine::Get(), TEXT("WHNoAvoid")); return b; }   // -WHNoAvoid: the A/B baseline run (avoidance disabled)
	FString Label(const AActor* A)
	{
#if WITH_EDITOR
		return A->GetActorLabel();
#else
		return A->GetName();
#endif
	}
	void AppendRow(const AWHCharLoopWalker* M, uint64 Frame, float Time, float MinPair)
	{
		const FVector P = M->GetActorLocation();
		GLogBuf += FString::Printf(TEXT("%llu,%.4f,%s,%.2f,%.2f,%.2f,%.2f,%.2f\n"), Frame, Time, *Label(M), P.X, P.Y, M->GetActorRotation().Yaw, M->LaneOffset, MinPair);
		if (++GLogFrames % 4320 == 0) FlushLog();
	}
}

AWHCharLoopWalker::AWHCharLoopWalker()
{
	PrimaryActorTick.bCanEverTick = true;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	Mesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Mesh"));
	Mesh->SetupAttachment(RootComponent);
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
}

void AWHCharLoopWalker::BeginPlay()
{
	Super::BeginPlay();
	// round 08: -WHFlatClasses = every slot of the walker's mesh takes the unlit class-colour material /Game/Tests/Characters/Materials/MI_Flat_<SlotName> when it exists
	// (hero eye checks: lens magenta, bezel yellow, suit blue on the stencil key; an editor-time override did not survive into the running game)
	static const bool bFlatClasses = FParse::Param(FCommandLine::Get(), TEXT("WHFlatClasses"));
	if (bFlatClasses && Mesh)
	{
		const TArray<FName> Slots = Mesh->GetMaterialSlotNames();
		for (int32 i = 0; i < Slots.Num(); ++i)
		{
			const FString MatPath = FString::Printf(TEXT("/Game/Tests/Characters/Materials/MI_Flat_%s.MI_Flat_%s"), *Slots[i].ToString(), *Slots[i].ToString());
			if (UMaterialInterface* M = LoadObject<UMaterialInterface>(nullptr, *MatPath)) Mesh->SetMaterial(i, M);
		}
	}
	Center = GetActorLocation();
	Theta = FMath::DegreesToRadians(StartAngle);
	Yaw = GetActorRotation().Yaw;
	LineD = LineStart;
	HopT = FirstHopDelay >= 0.f ? HopInterval - FirstHopDelay : 0.f;
	bStarted = true;
	if (Mode == EWHWalkerMode::Loop || Mode == EWHWalkerMode::Line) Tick(0.f);
}

void AWHCharLoopWalker::Tick(float Dt)
{
	Super::Tick(Dt);
	UWHCharAnimInstance* AI = Mesh ? Cast<UWHCharAnimInstance>(Mesh->GetAnimInstance()) : nullptr;
	if (AI) AI->IdleOffset = AnimOffset;
	if (AI && Script.Num() > 0 && ScriptTarget.Get() != AI) { AI->Script = Script; ScriptTarget = AI; }   // round 09: the choreography goes to the AnimInstance once
	if (Mode == EWHWalkerMode::Loop)
	{
		const float S = FMath::Sin(Theta), C = FMath::Cos(Theta);
		const float Local = FMath::Max(10.f, FMath::Sqrt(FMath::Square(RadiusX * S) + FMath::Square(RadiusY * C)));
		const float Dir = bClockwise ? -1.f : 1.f;
		Theta += Dir * Speed * Dt / Local;
		const FVector P = Center + FVector(RadiusX * FMath::Cos(Theta), RadiusY * FMath::Sin(Theta), 0.f);
		const FVector T = FVector(-RadiusX * FMath::Sin(Theta), RadiusY * FMath::Cos(Theta), 0.f) * Dir;
		TickHop(Dt);
		SetActorLocationAndRotation(P + FVector(0, 0, Z), FRotator(0.f, T.Rotation().Yaw, 0.f));
		if (AI) { AI->ForcedSpeed = Speed; AI->bForceAir = bAir; AI->ForcedVerticalSpeed = Vz; AI->TakeoffTime = TakeoffT; }
	}
	else if (Mode == EWHWalkerMode::Line && bAvoid && !AvoidOff())
	{
		StepAvoidGroup(Dt, false);
		if (AI) { AI->ForcedSpeed = Speed; AI->bForceAir = bAir; AI->ForcedVerticalSpeed = Vz; AI->TakeoffTime = TakeoffT; }
	}
	else if (Mode == EWHWalkerMode::Line)
	{
		LineD += Speed * Dt;
		const float X = FMath::Fmod(LineD, FMath::Max(100.f, LineLength)) - LineLength * 0.5f;
		TickHop(Dt);
		SetActorLocationAndRotation(Center + FRotator(0.f, Yaw, 0.f).Vector() * X + FVector(0, 0, Z), FRotator(0.f, Yaw, 0.f));
		if (AI) { AI->ForcedSpeed = Speed; AI->bForceAir = bAir; AI->ForcedVerticalSpeed = Vz; AI->TakeoffTime = TakeoffT; }
		if (bAvoid && Dt > 0.f) { InitLog(); if (!GLogPath.IsEmpty()) AppendRow(this, GFrameCounter, GetWorld()->GetTimeSeconds(), -1.f); }   // baseline run (-WHNoAvoid): telemetry only
	}
	else if (Mode == EWHWalkerMode::Turntable)
	{
		Yaw += TurntableDegPerSec * Dt;
		SetActorRotation(FRotator(0.f, Yaw, 0.f));
		if (AI) AI->ForcedSpeed = Speed;
	}
	else if (Mode == EWHWalkerMode::Stand && StagePath.Num() > 0)
	{
		FVector P; float Y;
		SamplePath(WHStage::Now(GetWorld()), P, Y);
		const FVector Prev = GetActorLocation();
		SetActorLocationAndRotation(P, FRotator(0.f, Y, 0.f));
		const float Spd = (Dt > 1e-4f && !bPathFirst) ? FVector::Dist2D(P, Prev) / Dt : 0.f;
		bPathFirst = false;
		if (AI) AI->ForcedSpeed = Spd;
	}
	else if (AI) AI->ForcedSpeed = 0.f;
}

bool AWHCharLoopWalker::SamplePath(float T, FVector& OutP, float& OutYaw) const
{
	if (StagePath.Num() == 0) return false;
	if (T <= StagePath[0].Time || StagePath.Num() == 1) { OutP = StagePath[0].Loc; OutYaw = StagePath[0].Yaw; return true; }
	if (T >= StagePath.Last().Time) { OutP = StagePath.Last().Loc; OutYaw = StagePath.Last().Yaw; return true; }
	int32 I = 0;
	while (I + 2 < StagePath.Num() && T >= StagePath[I + 1].Time) ++I;
	const FWHPathKey& A = StagePath[I]; const FWHPathKey& B = StagePath[I + 1];
	const float U = FMath::Clamp((T - A.Time) / FMath::Max(1e-4f, B.Time - A.Time), 0.f, 1.f);
	OutP = FMath::Lerp(A.Loc, B.Loc, U);
	OutYaw = A.Yaw + FRotator::NormalizeAxis(B.Yaw - A.Yaw) * U;
	return true;
}

void AWHCharLoopWalker::TickHop(float Dt)
{
	if (HopInterval <= 0.f) return;
	HopT += Dt;
	if (!bAir && TakeoffT < 0.f && HopT >= HopInterval) { HopT = 0.f; TakeoffT = 0.f; }
	if (TakeoffT >= 0.f)
	{
		// grounded anticipation (the crouch is animated by UWHCharAnimInstance::Takeoff), then leave the ground
		TakeoffT += Dt;
		if (TakeoffT >= TakeoffTime) { TakeoffT = -1.f; bAir = true; Vz = HopVelocity; }
	}
	if (bAir) { Vz -= Gravity * Dt; Z += Vz * Dt; if (Z <= 0.f) { Z = 0.f; bAir = false; Vz = 0.f; } }
}

void AWHCharLoopWalker::RestartLine()
{
	LineD = LineStart; LaneOffset = 0.f; LatVel = 0.f; MinPairDistance = 1e9f;
	HopT = FirstHopDelay >= 0.f ? HopInterval - FirstHopDelay : 0.f; TakeoffT = -1.f; bAir = false; Z = 0.f; Vz = 0.f;
	if (Mode == EWHWalkerMode::Line)
	{
		if (bAvoid && !AvoidOff()) StepAvoidGroup(0.f, true);   // reposition now (and resolve the whole group at its restarted positions)
		else Tick(0.f);
	}
}

void AWHCharLoopWalker::EndPlay(const EEndPlayReason::Type Reason)
{
	FlushLog();
	Super::EndPlay(Reason);
}

// ---------------------------------------------------------------------------------------------------------------- round 07: avoidance
FVector AWHCharLoopWalker::AvoidPos(float Tau, float Off) const
{
	const FRotator Face(0.f, Yaw, 0.f);
	const float X = FMath::Fmod(LineD + Speed * Tau, FMath::Max(100.f, LineLength)) - LineLength * 0.5f;
	const FVector Lat = FRotator(0.f, Yaw + 90.f, 0.f).Vector();      // the walker's right-hand side (UE: +Y for yaw 0)
	return Center + Face.Vector() * X + Lat * Off;
}

void AWHCharLoopWalker::ApplyLine()
{
	const float DevYaw = FMath::RadiansToDegrees(FMath::Atan2(LatVel, FMath::Max(10.f, Speed)));
	SetActorLocationAndRotation(AvoidPos(0.f, LaneOffset) + FVector(0, 0, Z), FRotator(0.f, Yaw + DevYaw, 0.f));
}

void AWHCharLoopWalker::StepAvoidGroup(float Dt, bool bForce)
{
	InitLog();
	UWorld* W = GetWorld(); if (!W) return;
	const uint64 Frame = GFrameCounter;
	if (!bForce && StepStamp == Frame && Dt > 0.f) return;         // a member already stepped the whole group this frame
	TArray<AWHCharLoopWalker*> G;
	for (TActorIterator<AWHCharLoopWalker> It(W); It; ++It)
		if (It->bAvoid && It->bStarted && It->Mode == EWHWalkerMode::Line) G.Add(*It);
	G.Sort([](const AWHCharLoopWalker& A, const AWHCharLoopWalker& B) { return A.GetName() < B.GetName(); });   // fixed order: results never depend on tick order
	const int32 N = G.Num();
	for (AWHCharLoopWalker* M : G) { M->StepStamp = Frame; if (Dt > 0.f) { M->LineD += M->Speed * Dt; M->TickHop(Dt); } }
	if (Dt > 0.f)
	{
		// 1. plan: each walker picks the sideways offset (from its lane) that keeps its capsule clear of everybody's predicted capsules
		TArray<float> Target; Target.SetNum(N);
		TArray<FVector> Pj; Pj.SetNum(5 * N);     // predicted positions of every walker at each horizon, at its CURRENT offset
		for (int32 h = 0; h < 5; ++h) for (int32 i = 0; i < N; ++i) Pj[h * N + i] = G[i]->AvoidPos(Horizons[h], G[i]->LaneOffset);
		for (int32 i = 0; i < N; ++i)
		{
			AWHCharLoopWalker* M = G[i];
			const float Need = 2.f * M->AvoidRadius + M->AvoidMargin;
			float Best = TNumericLimits<float>::Max(), BestO = M->LaneOffset;
			for (int32 k = -52; k <= 52; ++k)
			{
				const float O = 5.f * k;
				float Cost = FMath::Abs(O) + (O < 0.f ? 20.f : 0.f) + 0.5f * FMath::Abs(O - M->LaneOffset);
				for (int32 h = 0; h < 5; ++h)
				{
					const FVector P = M->AvoidPos(Horizons[h], O);
					for (int32 j = 0; j < N; ++j)
					{
						if (j == i) continue;
						const float Dd = FVector::Dist2D(P, Pj[h * N + j]);
						const float NeedIJ = M->AvoidRadius + G[j]->AvoidRadius + FMath::Max(M->AvoidMargin, G[j]->AvoidMargin);
						if (Dd < NeedIJ) Cost += (h == 0 ? 100000.f : 1000.f) * (NeedIJ - Dd) / NeedIJ;
					}
				}
				if (Cost < Best) { Best = Cost; BestO = O; }
			}
			Target[i] = BestO; (void)Need;
		}
		for (int32 i = 0; i < N; ++i)
		{
			AWHCharLoopWalker* M = G[i];
			const float Vl = FMath::Min(M->AvoidLateralSpeed, 0.47f * M->Speed);      // at most ~25 degrees of heading change
			const float D = FMath::Clamp(Target[i] - M->LaneOffset, -Vl * Dt, Vl * Dt);
			M->LaneOffset += D;
			M->LatVel += (D / Dt - M->LatVel) * FMath::Min(1.f, 5.f * Dt);
		}
		// 2. hard limit: capsules that still overlap at this instant are pushed apart (sideways components only), a few relaxation passes
		for (int32 Pass = 0; Pass < 6; ++Pass)
		{
			bool bAny = false;
			for (int32 a = 0; a < N; ++a) for (int32 b = a + 1; b < N; ++b)
			{
				AWHCharLoopWalker* A = G[a]; AWHCharLoopWalker* B = G[b];
				const FVector Dv = A->AvoidPos(0.f, A->LaneOffset) - B->AvoidPos(0.f, B->LaneOffset);
				const float Dist = FVector(Dv.X, Dv.Y, 0.f).Size();
				const float Need2 = A->AvoidRadius + B->AvoidRadius + 0.5f;   // hard limit: 2R + 0.5 cm
				if (Dist < Need2 && Dist > 1e-3f)
				{
					bAny = true;
					const FVector n = FVector(Dv.X, Dv.Y, 0.f) / Dist; const float Deficit = Need2 - Dist;
					A->LaneOffset += FVector::DotProduct(FRotator(0.f, A->Yaw + 90.f, 0.f).Vector(), n) * Deficit * 0.525f;
					B->LaneOffset -= FVector::DotProduct(FRotator(0.f, B->Yaw + 90.f, 0.f).Vector(), n) * Deficit * 0.525f;
				}
			}
			if (!bAny) break;
		}
	}
	// 3. apply + telemetry
	float MinAll = 1e9f;
	for (int32 a = 0; a < N; ++a)
	{
		float Mn = 1e9f;
		for (int32 b = 0; b < N; ++b) if (a != b)
			Mn = FMath::Min(Mn, FVector::Dist2D(G[a]->AvoidPos(0.f, G[a]->LaneOffset), G[b]->AvoidPos(0.f, G[b]->LaneOffset)));
		G[a]->MinPairDistance = Mn; MinAll = FMath::Min(MinAll, Mn);
	}
	for (AWHCharLoopWalker* M : G) M->ApplyLine();
	if (Dt > 0.f && !GLogPath.IsEmpty())
		for (AWHCharLoopWalker* M : G) AppendRow(M, Frame, W->GetTimeSeconds(), M->MinPairDistance);
}