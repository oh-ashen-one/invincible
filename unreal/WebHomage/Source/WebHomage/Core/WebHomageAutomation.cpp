// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Core/WebHomageAutomation.h"
#include "Core/WHSettings.h"
#include "WebHomage.h"

#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/GameInstance.h"
#include "HAL/FileManager.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformTime.h"
#include "Misc/CommandLine.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "RHI.h"
#include "UnrealClient.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Dom/JsonObject.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Traversal/WebTravCharacter.h"
#include "Traversal/WebTraversalComponent.h"
#include "Serialization/JsonSerializer.h"

void UWebHomageAutomation::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	const TCHAR* Cmd = FCommandLine::Get();

	FString ShotList;
	if (FParse::Value(Cmd, TEXT("WHShotAt="), ShotList, /*bShouldStopOnSeparator*/ false))
	{
		TArray<FString> Parts;
		ShotList.ParseIntoArray(Parts, TEXT(","));
		for (const FString& P : Parts)
		{
			ShotTimes.Add(FCString::Atod(*P));
		}
		ShotTimes.Sort();
	}
	if (!FParse::Value(Cmd, TEXT("WHShotDir="), ShotDir))
	{
		ShotDir = FPaths::ProjectSavedDir() / TEXT("WHCaptures");
	}
	ShotDir = FPaths::ConvertRelativePathToFull(ShotDir);
	FParse::Value(Cmd, TEXT("WHShotName="), ShotName);
	FParse::Value(Cmd, TEXT("WHPerfFrom="), PerfFrom);
	FParse::Value(Cmd, TEXT("WHPerfTo="), PerfTo);
	FParse::Value(Cmd, TEXT("WHQuitAt="), QuitAt);
	bCsv = FParse::Param(Cmd, TEXT("WHCsv"));
	{
		FString EA;
		if (FParse::Value(Cmd, TEXT("WHExecAt="), EA, false))
		{
			TArray<FString> Items; EA.ParseIntoArray(Items, TEXT(";"), true);
			for (const FString& It : Items) { FString T, C; if (It.Split(TEXT(":"), &T, &C)) ExecAt.Add(TPair<double, FString>(FCString::Atod(*T), C)); }
			ExecAt.Sort([](const TPair<double, FString>& A, const TPair<double, FString>& B) { return A.Key < B.Key; });
		}
	}
	FString CamFile;
	if (FParse::Value(Cmd, TEXT("WHShotCam="), CamFile))
	{
		FParse::Value(Cmd, TEXT("WHShotCamWait="), CamWait);
		FString Txt; TArray<TSharedPtr<FJsonValue>> Arr;
		if (FFileHelper::LoadFileToString(Txt, *CamFile) && FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Txt), Arr))
		{
			auto V3 = [](const TSharedPtr<FJsonObject>& O, const TCHAR* K) { const TArray<TSharedPtr<FJsonValue>>* A; FVector V = FVector::ZeroVector; if (O->TryGetArrayField(K, A) && A->Num() >= 3) V = FVector((*A)[0]->AsNumber(), (*A)[1]->AsNumber(), (*A)[2]->AsNumber()); return V; };
			for (const TSharedPtr<FJsonValue>& E : Arr)
			{
				const TSharedPtr<FJsonObject> O = E->AsObject(); if (!O) continue;
				FCamShot C; C.T = O->GetNumberField(TEXT("t")); C.Name = O->GetStringField(TEXT("name")); C.Pos = V3(O, TEXT("ue_pos_cm")); C.Target = V3(O, TEXT("ue_target_cm"));
				C.Fov = float(O->GetNumberField(TEXT("fov"))); C.bHero = O->HasField(TEXT("hero_visible")) && O->GetBoolField(TEXT("hero_visible"));
				if (O->HasField(TEXT("hero_pos_m"))) { C.bHeroPos = true; C.HeroPosM = V3(O, TEXT("hero_pos_m")); C.HeroYawDeg = O->HasField(TEXT("hero_yaw_deg")) ? O->GetNumberField(TEXT("hero_yaw_deg")) : 0.0; }
				CamShots.Add(C);
			}
			CamShots.Sort([](const FCamShot& A, const FCamShot& B) { return A.T < B.T; });
		}
		else UE_LOG(LogWebHomage, Error, TEXT("WH_SHOTCAM cannot read %s"), *CamFile);
		UE_LOG(LogWebHomage, Display, TEXT("WH_SHOTCAM %d shots from %s, wait %.2f s"), CamShots.Num(), *CamFile, CamWait);
	}

	bActive = ShotTimes.Num() > 0 || CamShots.Num() > 0 || (PerfFrom >= 0.0 && PerfTo > PerfFrom) || QuitAt > 0.0;
	LastWall = FPlatformTime::Seconds();
	if (bActive)
	{
		IFileManager::Get().MakeDirectory(*ShotDir, true);
		UE_LOG(LogWebHomage, Display, TEXT("WH_AUTOMATION shots=%d perf=[%.2f,%.2f] csv=%d quit=%.2f dir=%s"),
			ShotTimes.Num(), PerfFrom, PerfTo, bCsv ? 1 : 0, QuitAt, *ShotDir);
	}
}

void UWebHomageAutomation::Deinitialize()
{
	if (bPerfRunning)
	{
		WritePerf();
	}
	bActive = false;
	Super::Deinitialize();
}

TStatId UWebHomageAutomation::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UWebHomageAutomation, STATGROUP_Tickables);
}

void UWebHomageAutomation::TickCamShots(UWorld* World)
{
	for (int32 i = 0; i < CamShots.Num(); ++i)
	{
		FCamShot& C = CamShots[i];
		if (!C.bPlaced && Elapsed >= C.T)
		{
			APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0);
			if (!PC) return;
			if (!CamActor.IsValid())
			{
				FActorSpawnParameters SP; SP.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
				CamActor = World->SpawnActor<ACameraActor>(C.Pos, FRotator::ZeroRotator, SP);
			}
			ACameraActor* Cam = CamActor.Get(); if (!Cam) return;
			Cam->SetActorLocationAndRotation(C.Pos, FRotationMatrix::MakeFromX((C.Target - C.Pos).GetSafeNormal()).Rotator());
			UCameraComponent* CC = Cam->GetCameraComponent();
			CC->SetFieldOfView(C.Fov); CC->bConstrainAspectRatio = false;
			if (PC->GetViewTarget() != Cam) PC->SetViewTarget(Cam);
			if (APawn* Pawn = PC->GetPawn()) { Pawn->SetActorHiddenInGame(!C.bHero); bHeroHidden = !C.bHero; }
			C.bPlaced = true;
			if (C.bHeroPos) if (AWebTravCharacter* H = Cast<AWebTravCharacter>(PC->GetPawn())) if (UWebTraversalComponent* T = H->GetTraversal())
			{ // the author's player position + yaw (Pos.Z = feet height; Teleport raises it to the floor when lower)
				T->Teleport(FVector(C.HeroPosM.X, C.HeroPosM.Y, C.HeroPosM.Z + UWebTraversalComponent::H), FMath::DegreesToRadians(C.HeroYawDeg));
			}
			UE_LOG(LogWebHomage, Display, TEXT("WH_SHOTCAM place %s at t=%.2f pos (%.0f %.0f %.0f) fov %.1f hero %d"), *C.Name, Elapsed, C.Pos.X, C.Pos.Y, C.Pos.Z, C.Fov, C.bHero ? 1 : 0);
		}
		if (C.bPlaced && !C.bShot && C.bHeroPos)   // hold the pose (mid-air states would otherwise fall during the settle time)
			if (APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0)) if (AWebTravCharacter* H = Cast<AWebTravCharacter>(PC->GetPawn())) if (UWebTraversalComponent* T = H->GetTraversal())
				T->Teleport(FVector(C.HeroPosM.X, C.HeroPosM.Y, C.HeroPosM.Z + UWebTraversalComponent::H), FMath::DegreesToRadians(C.HeroYawDeg));
		if (C.bPlaced && !C.bShot && Elapsed >= C.T + CamWait)
		{
			const FString File = ShotDir / FString::Printf(TEXT("%s_%02d_%s.png"), *ShotName, i, *C.Name);
			FScreenshotRequest::RequestScreenshot(File, false, false);
			UE_LOG(LogWebHomage, Display, TEXT("WH_SHOT %s"), *File);
			C.bShot = true;
		}
	}
}

void UWebHomageAutomation::Tick(float DeltaTime)
{
	// Only drive automation from game worlds (standalone / PIE), not editor preview worlds.
	const UGameInstance* GI = GetGameInstance();
	if (!GI || !GI->GetWorld() || !GI->GetWorld()->IsGameWorld())
	{
		return;
	}

	const double Now = FPlatformTime::Seconds();
	const double WallDelta = Now - LastWall;
	LastWall = Now;
	Elapsed += DeltaTime;

	// Perf window: record real frame-to-frame wall time and the RHI's GPU frame time.
	if (!bPerfDone && PerfFrom >= 0.0 && PerfTo > PerfFrom)
	{
		if (!bPerfRunning && Elapsed >= PerfFrom)
		{
			bPerfRunning = true;
			FrameMs.Reset();
			FrameT.Reset();
			GpuMs.Reset();
			if (bCsv && GEngine)
			{
				GEngine->Exec(GI->GetWorld(), TEXT("CsvProfile Start"));
			}
			UE_LOG(LogWebHomage, Display, TEXT("WH_PERF_START t=%.2f"), Elapsed);
		}
		else if (bPerfRunning)
		{
			FrameT.Add(float(Elapsed));
			FrameMs.Add(float(WallDelta * 1000.0));
			GpuMs.Add(float(FPlatformTime::ToMilliseconds(RHIGetGPUFrameCycles(0))));
			if (Elapsed >= PerfTo)
			{
				if (bCsv && GEngine)
				{
					GEngine->Exec(GI->GetWorld(), TEXT("CsvProfile Stop"));
				}
				WritePerf();
			}
		}
	}

	TickCamShots(GI->GetWorld());
	while (NextExec < ExecAt.Num() && Elapsed >= ExecAt[NextExec].Key)
	{
		UE_LOG(LogWebHomage, Display, TEXT("WH_EXEC t=%.2f %s"), Elapsed, *ExecAt[NextExec].Value);
		if (GEngine) GEngine->Exec(GI->GetWorld(), *ExecAt[NextExec].Value);
		++NextExec;
	}

	while (NextShot < ShotTimes.Num() && Elapsed >= ShotTimes[NextShot])
	{
		const FString File = ShotDir / FString::Printf(TEXT("%s_%02d_t%05.1f.png"), *ShotName, NextShot, ShotTimes[NextShot]);
		// -WHShowSettings (settings-menu verification): include the Slate UI in the shot; every other run stays scene-only
		static const bool bShotUI = FParse::Param(FCommandLine::Get(), TEXT("WHShowSettings"));
		FScreenshotRequest::RequestScreenshot(File, /*bShowUI*/ bShotUI, /*bAddFilenameSuffix*/ false);
		UE_LOG(LogWebHomage, Display, TEXT("WH_SHOT %s"), *File);
		++NextShot;
	}

	if (QuitAt > 0.0 && !bQuitRequested && Elapsed >= QuitAt)
	{
		bQuitRequested = true;
		if (bPerfRunning)
		{
			WritePerf();
		}
		UE_LOG(LogWebHomage, Display, TEXT("WH_QUIT t=%.2f"), Elapsed);
		if (GIsEditor)
		{
			UE_LOG(LogWebHomage, Display, TEXT("WH_QUIT ignored inside the editor (PIE); stop PIE via MCP StopPIE."));
		}
		else if (GEngine)
		{
			GEngine->Exec(GI->GetWorld(), TEXT("quit"));
		}
	}
}

static float Percentile(TArray<float> V, float P)
{
	if (V.Num() == 0)
	{
		return 0.f;
	}
	V.Sort();
	const int32 Idx = FMath::Clamp(int32(FMath::CeilToInt(P * V.Num())) - 1, 0, V.Num() - 1);
	return V[Idx];
}

void UWebHomageAutomation::WritePerf()
{
	bPerfRunning = false;
	bPerfDone = true;
	const int32 N = FrameMs.Num();
	double Sum = 0.0, GpuSum = 0.0;
	for (float F : FrameMs) { Sum += F; }
	for (float G : GpuMs) { GpuSum += G; }
	const double Avg = N ? Sum / N : 0.0;
	const double GpuAvg = N ? GpuSum / N : 0.0;

	const FWHRenderRes RenderRes = WHComputeRenderRes();
	const FIntPoint Size = RenderRes.Output;
	const float ScreenPct = RenderRes.ScreenPercentage;
	const FString SPMode = RenderRes.Mode;
	const int32 InternalW = RenderRes.Internal.X;
	const int32 InternalH = RenderRes.Internal.Y;
	int32 Under60 = 0;
	for (float F : FrameMs) { if (F > 1000.f / 60.f + 0.5f) { ++Under60; } }

	const FString Json = FString::Printf(TEXT("{\n  \"frames\": %d,\n  \"seconds\": %.3f,\n  \"avg_ms\": %.3f,\n  \"avg_fps\": %.2f,\n  \"p50_ms\": %.3f,\n  \"p95_ms\": %.3f,\n  \"p99_ms\": %.3f,\n  \"max_ms\": %.3f,\n  \"frames_over_16_67ms\": %d,\n  \"gpu_avg_ms\": %.3f,\n  \"gpu_p95_ms\": %.3f,\n  \"output_w\": %d,\n  \"output_h\": %d,\n  \"r_ScreenPercentage\": %.1f,\n  \"screen_percentage_mode\": \"%s\",\n  \"internal_w\": %d,\n  \"internal_h\": %d,\n  \"rhi\": \"%s\"\n}\n"),
		N, Sum / 1000.0, Avg, Avg > 0 ? 1000.0 / Avg : 0.0,
		Percentile(FrameMs, 0.50f), Percentile(FrameMs, 0.95f), Percentile(FrameMs, 0.99f), Percentile(FrameMs, 1.0f), Under60,
		GpuAvg, Percentile(GpuMs, 0.95f), Size.X, Size.Y, ScreenPct, *SPMode, InternalW, InternalH, GDynamicRHI ? GDynamicRHI->GetName() : TEXT("?"));
	{
		FString Csv = TEXT("t_s,frame_ms,gpu_ms\n");
		for (int32 i = 0; i < FrameMs.Num() && i < FrameT.Num() && i < GpuMs.Num(); ++i) Csv += FString::Printf(TEXT("%.4f,%.3f,%.3f\n"), FrameT[i], FrameMs[i], GpuMs[i]);
		FFileHelper::SaveStringToFile(Csv, *(ShotDir / (ShotName + TEXT("_frames.csv"))));
	}
	const FString Path = ShotDir / (ShotName + TEXT("_perf.json"));
	FFileHelper::SaveStringToFile(Json, *Path);
	UE_LOG(LogWebHomage, Display, TEXT("WH_PERF frames=%d avg_ms=%.2f fps=%.1f p95_ms=%.2f p99_ms=%.2f gpu_avg_ms=%.2f out=%dx%d internal=%dx%d (%s) -> %s"),
		N, Avg, Avg > 0 ? 1000.0 / Avg : 0.0, Percentile(FrameMs, 0.95f), Percentile(FrameMs, 0.99f), GpuAvg, Size.X, Size.Y, InternalW, InternalH, *SPMode, *Path);
}
