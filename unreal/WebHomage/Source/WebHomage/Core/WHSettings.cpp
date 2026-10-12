// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Core/WHSettings.h"
#include "WebHomage.h"

#include "GenericPlatform/GenericApplication.h"
#include "HAL/IConsoleManager.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Scalability.h"
#include "UnrealClient.h"
#include "UnrealEngine.h"

namespace
{
	const TCHAR* GSection = TEXT("WebHomage.Settings");
}

FWHRenderRes WHComputeRenderRes()
{
	FWHRenderRes R;
	if (GEngine && GEngine->GameViewport && GEngine->GameViewport->Viewport)
	{
		R.Output = GEngine->GameViewport->Viewport->GetSizeXY();
	}
	auto CVarF = [](const TCHAR* Name, float Default) -> float
	{
		IConsoleVariable* V = IConsoleManager::Get().FindConsoleVariable(Name);
		return V ? V->GetFloat() : Default;
	};
	R.ScreenPercentage = CVarF(TEXT("r.ScreenPercentage"), 0.f);
	// Effective internal (pre-TSR) resolution. r.ScreenPercentage<=0 means the engine picks it from
	// r.ScreenPercentage.Default.Desktop.Mode (1 = based on display resolution, table in
	// [Rendering.AutoScreenPercentage]: 2160p display -> 1080p render). Mirrors LegacyScreenPercentageDriver.cpp.
	if (R.ScreenPercentage > 0.f)
	{
		R.Frac = R.ScreenPercentage / 100.f;
	}
	else if (int32(CVarF(TEXT("r.ScreenPercentage.Default.Desktop.Mode"), 1.f)) == 1 && R.Output.X > 0)
	{
		R.Mode = TEXT("auto_display");
		auto Px = [](float H) { return H * H * 16.f / 9.f; };
		float MinD = 720, MinR = 720, MidD = 2160, MidR = 1080, MaxD = 4320, MaxR = 1440;
		GConfig->GetFloat(TEXT("Rendering.AutoScreenPercentage"), TEXT("MinDisplayResolution"), MinD, GEngineIni);
		GConfig->GetFloat(TEXT("Rendering.AutoScreenPercentage"), TEXT("MinRenderingResolution"), MinR, GEngineIni);
		GConfig->GetFloat(TEXT("Rendering.AutoScreenPercentage"), TEXT("MidDisplayResolution"), MidD, GEngineIni);
		GConfig->GetFloat(TEXT("Rendering.AutoScreenPercentage"), TEXT("MidRenderingResolution"), MidR, GEngineIni);
		GConfig->GetFloat(TEXT("Rendering.AutoScreenPercentage"), TEXT("MaxDisplayResolution"), MaxD, GEngineIni);
		GConfig->GetFloat(TEXT("Rendering.AutoScreenPercentage"), TEXT("MaxRenderingResolution"), MaxR, GEngineIni);
		const float Disp = float(R.Output.X) * float(R.Output.Y);
		float Render;
		if (Disp < Px(MinD)) { Render = Disp * Px(MinR) / Px(MinD); }
		else if (Disp > Px(MaxD)) { Render = Disp * Px(MaxR) / Px(MaxD); }
		else if (Disp > Px(MidD)) { Render = FMath::Lerp(Px(MidR), Px(MaxR), (Disp - Px(MidD)) / (Px(MaxD) - Px(MidD))); }
		else { Render = FMath::Lerp(Px(MinR), Px(MidR), FMath::Clamp((Disp - Px(MinD)) / (Px(MidD) - Px(MinD)), 0.f, 1.f)); }
		R.Frac = FMath::Sqrt(CVarF(TEXT("r.ScreenPercentage.Auto.PixelCountMultiplier"), 1.f) * Render / Disp);
	}
	else
	{
		R.Frac = CVarF(TEXT("r.ScreenPercentage.Default"), 100.f) / 100.f;
	}
	R.Internal = FIntPoint(FMath::RoundToInt(R.Output.X * R.Frac), FMath::RoundToInt(R.Output.Y * R.Frac));
	return R;
}

FWHSettings& WHSettings()
{
	static FWHSettings S;
	return S;
}

float FWHSettings::FovDefault()
{
	return float(FMath::RadiansToDegrees(2.0 * FMath::Atan(FMath::Tan(FMath::DegreesToRadians(BaseVFovDefault * 0.5)) * 16.0 / 9.0)));
}

FWHSettings::EProfile FWHSettings::ActiveProfile()
{
	static const EProfile Cached = []()
	{
		FString Name;
		if (FParse::Value(FCommandLine::Get(), TEXT("WHProfile="), Name))
		{
			if (Name.Equals(TEXT("fidelity"), ESearchCase::IgnoreCase)) return EProfile::Fidelity;
			if (Name.Equals(TEXT("playable"), ESearchCase::IgnoreCase)) return EProfile::Playable;
			UE_LOG(LogWebHomage, Error, TEXT("WH_PROFILE unknown -WHProfile=%s (expected fidelity|playable); ignored"), *Name);
		}
		return FParse::Param(FCommandLine::Get(), TEXT("WHPreparedPlaytest")) ? EProfile::Fidelity : EProfile::None;
	}();
	return Cached;
}

const TCHAR* FWHSettings::ProfileName(EProfile P)
{
	return P == EProfile::Fidelity ? TEXT("fidelity") : P == EProfile::Playable ? TEXT("playable") : TEXT("none");
}

int32 FWHSettings::ProfileResScale()
{
	if (ActiveProfile() != EProfile::Playable) return 100;
	int32 Scale = PlayableResScaleDefault;
	FParse::Value(FCommandLine::Get(), TEXT("WHResScale="), Scale);
	return FMath::Clamp(Scale, 25, 100);
}

FIntPoint FWHSettings::ProfileOutputSize()
{
	int32 W = 3840, H = 2160;
	FParse::Value(FCommandLine::Get(), TEXT("ResX="), W);
	FParse::Value(FCommandLine::Get(), TEXT("ResY="), H);
	return FIntPoint(FMath::Clamp(W, 640, 8192), FMath::Clamp(H, 360, 8192));
}

int32 FWHSettings::EffectiveQuality() const { return ActiveProfile() != EProfile::None ? QualityMax : Quality; }
int32 FWHSettings::EffectiveResScale() const { return ActiveProfile() != EProfile::None ? ProfileResScale() : ResScale; }
bool FWHSettings::EffectiveVSync() const { return ActiveProfile() != EProfile::None ? false : bVSync; }

void FWHSettings::LogRes()
{
	const FWHRenderRes R = WHComputeRenderRes();
	int32 AA = -1;
	if (IConsoleVariable* CV = IConsoleManager::Get().FindConsoleVariable(TEXT("r.AntiAliasingMethod"))) AA = CV->GetInt();
	static const TCHAR* AANames[] = { TEXT("none"), TEXT("FXAA"), TEXT("TAA"), TEXT("MSAA"), TEXT("TSR") };
	const FString AAName = AA >= 0 && AA < 5 ? FString(AANames[AA]) : FString::FromInt(AA);
	UE_LOG(LogWebHomage, Display, TEXT("WH_RES profile=%s output=%dx%d r.ScreenPercentage=%.1f internal=%dx%d aa=%s quality=%s"),
		ProfileName(ActiveProfile()), R.Output.X, R.Output.Y, R.ScreenPercentage, R.Internal.X, R.Internal.Y, *AAName,
		*QualityName(WHSettings().EffectiveQuality()).ToString());
}

FWHSettings::FWHSettings()
{
	FovH = FovDefault();
}

double FWHSettings::BaseVFov() const
{
	if (FMath::Abs(FovH - FovDefault()) < 0.05f)
	{
		return BaseVFovDefault;
	}
	return FMath::RadiansToDegrees(2.0 * FMath::Atan(FMath::Tan(FMath::DegreesToRadians(double(FovH) * 0.5)) * 9.0 / 16.0));
}

void FWHSettings::Clamp()
{
	MouseSens = FMath::Clamp(MouseSens, MouseSensMin, MouseSensMax);
	PadSens = FMath::Clamp(PadSens, PadSensMin, PadSensMax);
	FovH = FMath::Clamp(FovH, FovMin, FovMax);
	Quality = FMath::Clamp(Quality, 0, QualityMax);
	ResScale = FMath::Clamp(ResScale, ResScaleMin, ResScaleMax);
	WindowMode = FMath::Clamp(WindowMode, 0, 2);
}

FText FWHSettings::QualityName(int32 Q)
{
	switch (Q)
	{
	case 0: return NSLOCTEXT("WHSettings", "QLow", "Low");
	case 1: return NSLOCTEXT("WHSettings", "QMedium", "Medium");
	case 2: return NSLOCTEXT("WHSettings", "QHigh", "High");
	case 3: return NSLOCTEXT("WHSettings", "QEpic", "Epic");
	default: return NSLOCTEXT("WHSettings", "QCinematic", "Cinematic");
	}
}

FText FWHSettings::WindowModeName(int32 M)
{
	switch (M)
	{
	case WinWindowed: return NSLOCTEXT("WHSettings", "WWindowed", "Windowed");
	case WinFullscreen: return NSLOCTEXT("WHSettings", "WFullscreen", "Fullscreen");
	default: return NSLOCTEXT("WHSettings", "WBorderless", "Borderless");
	}
}

// Playable profile only: Config/PerfPlayable.cvars (tools/perf_ue2/overrides/perf60_hwl2.cvars, flattened) -- hardware-RT Lumen, Nanite error 8, cheaper VSM / cloud / fog, TSR history 100 %.
// -WHPerfPreset=0 skips it, -WHPerfPreset=<file> reads another cvar list (A/B runs); fidelity never reads it.
static void ApplyPerfPresetFile()
{
	FString Path = FPaths::Combine(FPaths::ProjectConfigDir(), TEXT("PerfPlayable.cvars"));
	FString Arg;
	if (FParse::Value(FCommandLine::Get(), TEXT("WHPerfPreset="), Arg))
	{
		if (Arg == TEXT("0")) { UE_LOG(LogWebHomage, Display, TEXT("WH_PERFPRESET off (-WHPerfPreset=0)")); return; }
		Path = Arg;
	}
	TArray<FString> Lines;
	if (!FFileHelper::LoadFileToStringArray(Lines, *Path)) { UE_LOG(LogWebHomage, Warning, TEXT("WH_PERFPRESET %s not found"), *Path); return; }
	int32 N = 0, Missing = 0;
	for (const FString& L : Lines)
	{
		FString K, V;
		if (L.TrimStartAndEnd().IsEmpty() || L.StartsWith(TEXT("#")) || !L.Split(TEXT("="), &K, &V)) continue;
		if (IConsoleVariable* CV = IConsoleManager::Get().FindConsoleVariable(*K.TrimStartAndEnd())) { CV->Set(*V.TrimStartAndEnd(), ECVF_SetByCode); ++N; }
		else { ++Missing; UE_LOG(LogWebHomage, Warning, TEXT("WH_PERFPRESET unknown cvar %s"), *K); }
	}
	UE_LOG(LogWebHomage, Display, TEXT("WH_PERFPRESET applied %d cvars from %s (%d unknown)"), N, *Path, Missing);
}

void FWHSettings::ApplyRender() const
{
	if (!bLive) return; // automated runs keep their command-line render settings
	// Scalability::SetQualityLevels directly: the "scalability" console command would also SaveState() into GameUserSettings.ini
	// [ScalabilityGroups], which the engine re-applies at startup -- that would leak into automated capture / perf runs.
	Scalability::FQualityLevels Q;
	Q.SetFromSingleQualityLevel(EffectiveQuality());
	Q.ResolutionQuality = float(EffectiveResScale());
	Scalability::SetQualityLevels(Q, /*bForce*/ true);
	if (IConsoleVariable* CV = IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenPercentage")))
	{
		CV->Set(float(EffectiveResScale()), ECVF_SetByCode);
	}
	if (IConsoleVariable* CV = IConsoleManager::Get().FindConsoleVariable(TEXT("r.VSync")))
	{
		CV->Set(EffectiveVSync() ? 1 : 0, ECVF_SetByCode);
	}
	if (ActiveProfile() == EProfile::Playable)
	{
		if (IConsoleVariable* CV = IConsoleManager::Get().FindConsoleVariable(TEXT("r.AntiAliasingMethod")))
		{
			CV->Set(4, ECVF_SetByCode);   // TSR
		}
		ApplyPerfPresetFile();
	}
}

void FWHSettings::ApplyWindow() const
{
	if (!bLive) return;
	FDisplayMetrics DM;
	FDisplayMetrics::RebuildDisplayMetrics(DM);
	int32 W = FMath::Max(640, DM.PrimaryDisplayWidth), H = FMath::Max(360, DM.PrimaryDisplayHeight);
	// owner playtest 2026-10-01: on macOS the WindowedFullscreen path left mouse clicks unregistered (menu buttons + right-mouse swing dead
	// while keys worked). Borderless = a plain window covering the primary display instead.
	EWindowMode::Type Mode = PLATFORM_MAC ? EWindowMode::Windowed : EWindowMode::WindowedFullscreen;
	if (WindowMode == WinFullscreen)
	{
		Mode = EWindowMode::Fullscreen;
	}
	else if (WindowMode == WinWindowed)
	{
		Mode = EWindowMode::Windowed;
		// a 16:9 window at most 80 % of the desktop (1920x1080 on a 3440x1440 ultrawide)
		const int32 WW = FMath::Min(1920, int32(W * 0.8f));
		W = WW; H = WW * 9 / 16;
	}
	// A run profile (and -WHPreparedPlaytest, its fidelity alias) must not silently replace its requested size with
	// the desktop's ultrawide resolution. This affects only explicit profile launches.
	if (ActiveProfile() != EProfile::None)
	{
		const FIntPoint Out = ProfileOutputSize();
		W = Out.X; H = Out.Y;
		Mode = EWindowMode::Windowed;
	}
	FSystemResolution::RequestResolutionChange(W, H, Mode);
	UE_LOG(LogWebHomage, Display, TEXT("WH_SETTINGS window %s %dx%d"), *WindowModeName(WindowMode).ToString(), W, H);
}

void FWHSettings::ResetToDefaults()
{
	const bool bWasLive = bLive;
	const int32 KeepSuit = SuitIndex; const FString KeepSuitId = SuitId;   // 'Reset defaults' resets look / graphics, not the hero's suit
	const int32 KeepQ = SavedQuality, KeepR = SavedResScale, KeepW = SavedWindowMode; const bool bKeepV = bSavedVSync;   // the ini values a profile run must still write back
	*this = FWHSettings();
	bLive = bWasLive;
	SuitIndex = KeepSuit; SuitId = KeepSuitId;
	SavedQuality = KeepQ; SavedResScale = KeepR; SavedWindowMode = KeepW; bSavedVSync = bKeepV;
	ApplyCVars();
	ApplyRender();
	ApplyWindow();
}

void FWHSettings::ApplyCVars() const
{
	if (IConsoleVariable* CV = IConsoleManager::Get().FindConsoleVariable(TEXT("wh.MouseSensitivity")))
	{
		CV->Set(MouseSens, ECVF_SetByGameSetting);
	}
}

void FWHSettings::SyncFromCVars()
{
	if (IConsoleVariable* CV = IConsoleManager::Get().FindConsoleVariable(TEXT("wh.MouseSensitivity")))
	{
		MouseSens = FMath::Clamp(CV->GetFloat(), MouseSensMin, MouseSensMax);
	}
}

void FWHSettings::Load()
{
	if (!GConfig)
	{
		return;
	}
	GConfig->GetFloat(GSection, TEXT("MouseSensitivity"), MouseSens, GGameUserSettingsIni);
	GConfig->GetFloat(GSection, TEXT("GamepadLookSensitivity"), PadSens, GGameUserSettingsIni);
	GConfig->GetBool(GSection, TEXT("InvertY"), bInvertY, GGameUserSettingsIni);
	GConfig->GetFloat(GSection, TEXT("FieldOfView"), FovH, GGameUserSettingsIni);
	GConfig->GetBool(GSection, TEXT("CameraShake"), bCameraShake, GGameUserSettingsIni);
	GConfig->GetInt(GSection, TEXT("QualityPreset"), Quality, GGameUserSettingsIni);
	GConfig->GetInt(GSection, TEXT("ResolutionScale"), ResScale, GGameUserSettingsIni);
	GConfig->GetInt(GSection, TEXT("WindowMode"), WindowMode, GGameUserSettingsIni);
	GConfig->GetBool(GSection, TEXT("VSync"), bVSync, GGameUserSettingsIni);
	GConfig->GetInt(GSection, TEXT("HeroSuit"), SuitIndex, GGameUserSettingsIni);
	GConfig->GetString(GSection, TEXT("HeroSuitId"), SuitId, GGameUserSettingsIni);
	Clamp();
	SavedQuality = Quality; SavedResScale = ResScale; SavedWindowMode = WindowMode; bSavedVSync = bVSync;
	if (ActiveProfile() != EProfile::None)
	{
		Quality = QualityMax;
		ResScale = ProfileResScale();
		WindowMode = WinWindowed;
		bVSync = false;
		if (FParse::Param(FCommandLine::Get(), TEXT("WHPreparedPlaytest")))
		{
			UE_LOG(LogWebHomage, Display, TEXT("WH_PREVIEW quality=Cinematic internal=100%% (requested output follows ResX/ResY)"));
		}
		UE_LOG(LogWebHomage, Display, TEXT("WH_PROFILE %s: quality Cinematic, res scale %d%%, windowed, vsync off (this run only; saved render settings are kept)"),
			ProfileName(ActiveProfile()), ResScale);
	}
	Clamp();
	bLive = true;
	ApplyCVars();
	UE_LOG(LogWebHomage, Display, TEXT("WH_SETTINGS loaded from %s: mouse %.2f pad %.2f invertY %d fov %.1f (vertical %.2f) shake %d quality %d res %d%% window %d vsync %d"),
		*GGameUserSettingsIni, MouseSens, PadSens, bInvertY ? 1 : 0, FovH, BaseVFov(), bCameraShake ? 1 : 0, Quality, ResScale, WindowMode, bVSync ? 1 : 0);
}

void FWHSettings::Save()
{
	if (!GConfig)
	{
		return;
	}
	SyncFromCVars();
	Clamp();
	GConfig->SetFloat(GSection, TEXT("MouseSensitivity"), MouseSens, GGameUserSettingsIni);
	GConfig->SetFloat(GSection, TEXT("GamepadLookSensitivity"), PadSens, GGameUserSettingsIni);
	GConfig->SetBool(GSection, TEXT("InvertY"), bInvertY, GGameUserSettingsIni);
	GConfig->SetFloat(GSection, TEXT("FieldOfView"), FovH, GGameUserSettingsIni);
	GConfig->SetBool(GSection, TEXT("CameraShake"), bCameraShake, GGameUserSettingsIni);
	const bool bProfile = ActiveProfile() != EProfile::None;
	GConfig->SetInt(GSection, TEXT("QualityPreset"), bProfile ? SavedQuality : Quality, GGameUserSettingsIni);
	GConfig->SetInt(GSection, TEXT("ResolutionScale"), bProfile ? SavedResScale : ResScale, GGameUserSettingsIni);
	GConfig->SetInt(GSection, TEXT("WindowMode"), bProfile ? SavedWindowMode : WindowMode, GGameUserSettingsIni);
	GConfig->SetBool(GSection, TEXT("VSync"), bProfile ? bSavedVSync : bVSync, GGameUserSettingsIni);
	GConfig->SetInt(GSection, TEXT("HeroSuit"), SuitIndex, GGameUserSettingsIni);
	GConfig->SetString(GSection, TEXT("HeroSuitId"), *SuitId, GGameUserSettingsIni);
	GConfig->Flush(false, GGameUserSettingsIni);
	UE_LOG(LogWebHomage, Display, TEXT("WH_SETTINGS saved to %s"), *GGameUserSettingsIni);
}

void FWHSettings::LoadSuit()
{
	if (!GConfig) return;
	GConfig->GetInt(GSection, TEXT("HeroSuit"), SuitIndex, GGameUserSettingsIni);
	GConfig->GetString(GSection, TEXT("HeroSuitId"), SuitId, GGameUserSettingsIni);
	UE_LOG(LogWebHomage, Display, TEXT("WH_SETTINGS suit read from %s: HeroSuit=%d HeroSuitId=%s"), *GGameUserSettingsIni, SuitIndex, *SuitId);
}

void FWHSettings::SaveSuit() const
{
	if (!GConfig) return;
	GConfig->SetInt(GSection, TEXT("HeroSuit"), SuitIndex, GGameUserSettingsIni);
	GConfig->SetString(GSection, TEXT("HeroSuitId"), *SuitId, GGameUserSettingsIni);
	GConfig->Flush(false, GGameUserSettingsIni);
	UE_LOG(LogWebHomage, Display, TEXT("WH_SETTINGS suit saved to %s: HeroSuit=%d HeroSuitId=%s"), *GGameUserSettingsIni, SuitIndex, *SuitId);
}
