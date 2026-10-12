// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "WebHomagePlayerController.generated.h"

/**
 * Mouse-safety player controller (owner rule: the game must never trap the mouse).
 *  - Starts RELEASED: cursor visible, not locked, not captured (look with right-mouse held).
 *  - Left click in the game window captures the mouse for mouse-look.
 *  - Escape ALWAYS releases it again (and shows the cursor).
 *  - Automated runs (-WHNoMouseCapture, or any -WHShotAt/-WHPerfFrom/-WHQuitAt/-WHAutoMove)
 *    never capture at all.
 * Keys are read in PlayerTick via WasInputKeyJustPressed, independent of Enhanced Input
 * mapping, so no pawn/input asset can swallow Escape.
 * Settings menu (owner 2026-10-01 "just add settings"): Escape (releases the mouse) / P / gamepad Start open the pure-Slate
 * SWHSettingsMenu and pause the game; Resume / Escape / P close it, save GameUserSettings.ini and recapture the mouse.
 * Automated runs never open it and never load the saved settings (captures keep the default camera), except
 * -WHShowSettings, which shows it (without pausing, without capturing) for screenshot verification.
 */
UCLASS()
class WEBHOMAGE_API AWebHomagePlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	AWebHomagePlayerController();

	virtual void PlayerTick(float DeltaTime) override;

	UFUNCTION(BlueprintCallable, Category="WebHomage|Input")
	void ReleaseMouse();

	UFUNCTION(BlueprintCallable, Category="WebHomage|Input")
	void CaptureMouse();

	UFUNCTION(BlueprintPure, Category="WebHomage|Input")
	bool IsMouseCaptured() const { return bMouseCaptured; }

	UFUNCTION(BlueprintCallable, Category="WebHomage|Settings")
	void OpenSettings();

	/** Close the menu, save the settings, unpause; bRecapture = take the mouse back (never in automated runs). */
	UFUNCTION(BlueprintCallable, Category="WebHomage|Settings")
	void CloseSettings(bool bRecapture);

	UFUNCTION(BlueprintPure, Category="WebHomage|Settings")
	bool IsSettingsOpen() const { return SettingsMenu.IsValid(); }

	void QuitFromMenu();

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;

private:
	bool bMouseCaptured = false;
	bool bNeverCapture = false;
	bool bForceSettings = false;     // -WHShowSettings (debug / screenshot)
	bool bForcedShown = false;
	bool bPausedByMenu = false;
	TSharedPtr<class SWHSettingsMenu> SettingsMenu;
	void RemoveMenuWidget();
};
