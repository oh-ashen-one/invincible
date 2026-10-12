// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// Player settings (owner playtest 2026-10-01: "just add settings"): look sensitivity, invert Y, field of view, camera shake.
// One live instance (WHSettings()) read by the traversal pawn every frame and edited by the in-game menu (SWHSettingsMenu).
// Persisted in GameUserSettings.ini, section [WebHomage.Settings] (Saved/Config/<platform>/GameUserSettings.ini).
// Automated runs never Load() it, so scripted captures always see the defaults below (bit-identical camera).
#pragma once

#include "CoreMinimal.h"

/** Output size (actual viewport), r.ScreenPercentage and the effective internal (pre-TSR) resolution. One implementation for WH_PERF, WH_CMB_RES and WH_RES. */
struct WEBHOMAGE_API FWHRenderRes
{
	FIntPoint Output = FIntPoint::ZeroValue;
	float ScreenPercentage = 0.f;   // r.ScreenPercentage (<= 0: the engine picks it from the display resolution)
	FString Mode = TEXT("manual");  // manual | auto_display
	float Frac = 1.f;
	FIntPoint Internal = FIntPoint::ZeroValue;
};
WEBHOMAGE_API FWHRenderRes WHComputeRenderRes();

struct WEBHOMAGE_API FWHSettings
{
	// ---- ranges / defaults
	static constexpr float MouseSensMin = 0.1f, MouseSensMax = 3.0f, MouseSensDefault = 1.0f;
	static constexpr float PadSensMin = 0.1f, PadSensMax = 3.0f, PadSensDefault = 1.0f;
	/** Field of view is shown as the HORIZONTAL angle at 16:9. The traversal camera's base is 58 deg vertical (browser three.js),
	 *  which is 89.16 deg horizontal at 16:9; at the default the camera keeps exactly 58.0 (no float round trip). */
	static constexpr float FovMin = 60.f, FovMax = 110.f;
	static float FovDefault();          // 89.16 (58 deg vertical at 16:9)
	static constexpr double BaseVFovDefault = 58.0;

	float MouseSens = MouseSensDefault; // mirrors the console variable wh.MouseSensitivity
	float PadSens = PadSensDefault;     // multiplies the right-stick look rate
	bool bInvertY = false;
	float FovH = 0.f;                   // 0 = default (set in the constructor)
	bool bCameraShake = true;           // landing / launch / wall jolts (FWebTravCamera Shake / Impact / Kick)

	// ---- graphics (owner 2026-10-01: "open it on max settings"): fresh install = Cinematic, 100 %, borderless at desktop res.
	// Applied only in interactive runs (never in automated captures / perf runs, which keep their command-line render settings).
	static constexpr int32 QualityMax = 4;                  // scalability 0..4 = Low, Medium, High, Epic, Cinematic
	static constexpr int32 ResScaleMin = 50, ResScaleMax = 100;
	enum EWinMode : int32 { WinWindowed = 0, WinBorderless = 1, WinFullscreen = 2 };
	int32 Quality = QualityMax;
	int32 ResScale = 100;               // r.ScreenPercentage
	int32 WindowMode = WinBorderless;
	bool bVSync = true;
	// ---- run profile (-WHProfile=fidelity|playable): overrides the render fields for this run only; Save() keeps the previously loaded values.
	//   fidelity: Cinematic, 100 %, windowed at -ResX/-ResY (default 3840x2160), vsync off.   -WHPreparedPlaytest is an alias of fidelity.
	//   playable: Cinematic, TSR (r.AntiAliasingMethod 4), r.ScreenPercentage = -WHResScale=<int> (default 67), windowed at -ResX/-ResY, vsync off.
	enum class EProfile : uint8 { None, Fidelity, Playable };
	static constexpr int32 PlayableResScaleDefault = 67;
	static EProfile ActiveProfile();        // parsed once from the command line
	static const TCHAR* ProfileName(EProfile P);
	static int32 ProfileResScale();         // 100 (fidelity) / -WHResScale (playable), clamped 25..100
	static FIntPoint ProfileOutputSize();   // -ResX / -ResY, default 3840x2160
	int32 EffectiveQuality() const;
	int32 EffectiveResScale() const;
	bool EffectiveVSync() const;
	int32 SavedQuality = QualityMax, SavedResScale = 100, SavedWindowMode = WinBorderless;  // values read from the ini before a profile overrode the fields
	bool bSavedVSync = true;
	/** One 'WH_RES profile=... output=... r.ScreenPercentage=... internal=... aa=... quality=...' line (call once the viewport exists). */
	static void LogRes();

	// ---- hero suit (round 11, piece G): index into /Game/Characters/Hero/Suits/DA_HeroSuits and the suit's id (the id wins when the set is re-ordered)
	int32 SuitIndex = 0;
	FString SuitId;
	/** Read / write only the suit keys of GameUserSettings.ini (the in-play suit swap saves at once; -WHSuitPersist uses them in automated runs). */
	void LoadSuit();
	void SaveSuit() const;

	/** True once Load() ran (interactive play). ApplyRender / ApplyWindow do nothing until then. */
	bool bLive = false;
	static FText QualityName(int32 Q);
	static FText WindowModeName(int32 M);
	/** Scalability + r.ScreenPercentage + r.VSync (cheap, may be called every change). */
	void ApplyRender() const;
	/** Window mode at the primary desktop resolution (borderless / fullscreen) or a centred window. */
	void ApplyWindow() const;

	FWHSettings();

	/** Vertical base FOV for FWebTravCamera (exactly 58.0 at the default). */
	double BaseVFov() const;
	void Clamp();
	void ResetToDefaults();
	/** Read from GameUserSettings.ini (missing keys keep the defaults), push wh.MouseSensitivity, mark live. Interactive runs only. */
	void Load();
	/** Pull wh.MouseSensitivity, write GameUserSettings.ini and flush it. */
	void Save();
	/** Push MouseSens into the wh.MouseSensitivity console variable. */
	void ApplyCVars() const;
	/** Read wh.MouseSensitivity back (it may be changed from the console). */
	void SyncFromCVars();
};

/** The live settings (defaults until a non-automated controller loads them). */
WEBHOMAGE_API FWHSettings& WHSettings();
