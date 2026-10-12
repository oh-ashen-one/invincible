// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Core/WebHomagePlayerController.h"
#include "WebHomage.h"
#include "Core/WHSettings.h"
#include "Core/WHSettingsMenu.h"

#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Framework/Application/SlateApplication.h"
#include "InputCoreTypes.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

AWebHomagePlayerController::AWebHomagePlayerController()
{
	bShowMouseCursor = true; // (APlayerController ticks while paused, so Escape / P / Options still close the menu)
}

void AWebHomagePlayerController::BeginPlay()
{
	Super::BeginPlay();

	const TCHAR* Cmd = FCommandLine::Get();
	FString Dummy;
	bNeverCapture = FParse::Param(Cmd, TEXT("WHNoMouseCapture"))
		|| FParse::Param(Cmd, TEXT("WHAutoMove"))
		|| FParse::Value(Cmd, TEXT("WHShotAt="), Dummy)
		|| FParse::Value(Cmd, TEXT("WHPerfFrom="), Dummy)
		|| FParse::Value(Cmd, TEXT("WHQuitAt="), Dummy);
	bForceSettings = FParse::Param(Cmd, TEXT("WHShowSettings"));

	if (IsLocalController())
	{
		// Saved settings (look, FOV, camera shake, graphics) apply to interactive play only. Automated runs keep the defaults and
		// their command-line render settings, so captures / perf numbers are unchanged. Loaded once per process (BeginPlay runs per map).
		static bool bLoadedOnce = false;
		static bool bResLogged = false;
		// automated captures keep their command-line render settings, except when -WHProfile is given explicitly: then the profile's render settings apply (the window stays as launched)
		const bool bProfile = FWHSettings::ActiveProfile() != FWHSettings::EProfile::None;
		if ((!bNeverCapture || bProfile) && !bLoadedOnce)
		{
			bLoadedOnce = true;
			FWHSettings& S = WHSettings();
			S.Load();
			S.ApplyRender();
			if (!bNeverCapture) S.ApplyWindow();
		}
		if (!bResLogged)
		{
			bResLogged = true;   // every mode (interactive, capture, perf): the window resize is asynchronous, so log the real viewport / internal resolution a few seconds after the map starts
			FTimerHandle ResLogTimer;
			GetWorldTimerManager().SetTimer(ResLogTimer, FTimerDelegate::CreateStatic(&FWHSettings::LogRes), 3.0f, false);
		}
		ReleaseMouse();
		// interactive play starts with the mouse captured (owner: right-mouse swing must work immediately); Escape releases + opens settings
		if (!bNeverCapture) CaptureMouse();
	}
}

void AWebHomagePlayerController::EndPlay(const EEndPlayReason::Type Reason)
{
	if (SettingsMenu.IsValid())
	{
		if (!bNeverCapture) WHSettings().Save();
		RemoveMenuWidget();
	}
	Super::EndPlay(Reason);
}

void AWebHomagePlayerController::ReleaseMouse()
{
	FInputModeGameAndUI Mode;
	Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	Mode.SetHideCursorDuringCapture(false);
	SetInputMode(Mode);
	bShowMouseCursor = true;
	bMouseCaptured = false;
	if (FSlateApplication::IsInitialized())
	{
		FSlateApplication::Get().ReleaseAllPointerCapture();
		FSlateApplication::Get().SetAllUserFocusToGameViewport(); // keep keyboard + gamepad input in the game
	}
}

void AWebHomagePlayerController::CaptureMouse()
{
	if (bNeverCapture)
	{
		return;
	}
	FInputModeGameOnly Mode;
	SetInputMode(Mode);
	bShowMouseCursor = false;
	bMouseCaptured = true;
}

void AWebHomagePlayerController::OpenSettings()
{
	if (SettingsMenu.IsValid() || !IsLocalController() || !GEngine || !GEngine->GameViewport)
	{
		return;
	}
	// automated runs never open the menu, except the explicit screenshot flag -WHShowSettings
	if (bNeverCapture && !bForceSettings)
	{
		return;
	}
	ReleaseMouse();
	SettingsMenu = SNew(SWHSettingsMenu).Owner(this);
	GEngine->GameViewport->AddViewportWidgetContent(SettingsMenu.ToSharedRef(), 1000);

	FInputModeGameAndUI Mode;
	Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	Mode.SetHideCursorDuringCapture(false);
	const TSharedPtr<SWidget> Focus = SettingsMenu->GetInitialFocus().IsValid() ? SettingsMenu->GetInitialFocus() : StaticCastSharedPtr<SWidget>(SettingsMenu);
	Mode.SetWidgetToFocus(Focus);
	SetInputMode(Mode);
	bShowMouseCursor = true;
	if (FSlateApplication::IsInitialized() && Focus.IsValid())
	{
		FSlateApplication::Get().SetAllUserFocus(Focus, EFocusCause::Navigation);
	}

	// pause while open (interactive play only: the forced screenshot run must keep its game clock so its shots / quit still fire)
	bPausedByMenu = false;
	if (!bNeverCapture && !IsPaused())
	{
		bPausedByMenu = SetPause(true);
	}
	UE_LOG(LogWebHomage, Display, TEXT("WH_SETTINGS menu open (paused %d)"), bPausedByMenu ? 1 : 0);
}

void AWebHomagePlayerController::RemoveMenuWidget()
{
	if (SettingsMenu.IsValid())
	{
		if (GEngine && GEngine->GameViewport)
		{
			GEngine->GameViewport->RemoveViewportWidgetContent(SettingsMenu.ToSharedRef());
		}
		SettingsMenu.Reset();
	}
}

void AWebHomagePlayerController::CloseSettings(bool bRecapture)
{
	if (!SettingsMenu.IsValid())
	{
		return;
	}
	RemoveMenuWidget();
	if (bPausedByMenu)
	{
		SetPause(false);
		bPausedByMenu = false;
	}
	if (!bNeverCapture)
	{
		WHSettings().Save();
	}
	if (bRecapture && !bNeverCapture)
	{
		CaptureMouse();
	}
	else
	{
		ReleaseMouse();
	}
	UE_LOG(LogWebHomage, Display, TEXT("WH_SETTINGS menu closed"));
}

void AWebHomagePlayerController::QuitFromMenu()
{
	if (!bNeverCapture)
	{
		WHSettings().Save();
	}
	UKismetSystemLibrary::QuitGame(this, this, EQuitPreference::Quit, false);
}

void AWebHomagePlayerController::PlayerTick(float DeltaTime)
{
	Super::PlayerTick(DeltaTime);

	if (bForceSettings && !bForcedShown && IsLocalController())
	{
		bForcedShown = true;
		OpenSettings();
	}

	// Escape / P / gamepad Options toggle the menu (while it has focus, SWHSettingsMenu::OnKeyDown handles them; these catch the
	// case where the game viewport kept focus). In automated runs Escape only releases the mouse and the menu never opens.
	const bool bEsc = WasInputKeyJustPressed(EKeys::Escape);
	const bool bToggle = bEsc || WasInputKeyJustPressed(EKeys::P) || WasInputKeyJustPressed(EKeys::Gamepad_Special_Right);
	if (SettingsMenu.IsValid())
	{
		if (bToggle && !bForceSettings)
		{
			CloseSettings(/*bRecapture*/ true);
		}
		return;
	}
	if (bToggle && !bNeverCapture)
	{
		OpenSettings();
	}
	else if (bEsc)
	{
		ReleaseMouse();
	}
	else if (!bMouseCaptured && !bNeverCapture && WasInputKeyJustPressed(EKeys::LeftMouseButton))
	{
		CaptureMouse();
	}
}
