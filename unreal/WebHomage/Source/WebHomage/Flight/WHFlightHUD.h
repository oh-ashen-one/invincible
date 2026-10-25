// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
// Invincible flight conversion (owner request 2026-10-15): the rescue overlay. A small Canvas HUD (no Slate / UMG, so it never
// competes with the Slate settings menu, which is added to the viewport above the canvas and pauses the game while open):
//   - top-right (owner request 2026-10-16: moved from the top-left): lives saved, lives lost, collateral damage ($), then one row per
//     active emergency (type, distance, rescue clock);
//   - top-left (owner request 2026-10-16): a small always-on keyboard controls panel (H hides / shows it);
//   - an on-screen diamond marker over each active emergency, or a chevron at the screen edge when it is off screen / behind;
//   - a short bottom-centre prompt with a hold bar while the hero is in range of an emergency.
// Installed by the hero with PC->ClientSetHUD(AWHFlightHUD::StaticClass()). -WHNoHUD draws nothing (clean captures).
// Nothing here damages the hero (the hero cannot die).
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "WHFlightHUD.generated.h"

class AWHRescueDirector;
class UFont;
struct FWHEmergency;

UCLASS()
class WEBHOMAGE_API AWHFlightHUD : public AHUD
{
	GENERATED_BODY()
public:
	AWHFlightHUD();

	virtual void BeginPlay() override;
	virtual void DrawHUD() override;

	/** -WHNoHUD: draw nothing. */
	bool bNoOverlay = false;

	/** Owner request 2026-10-16: the top-left controls panel; toggled with H (edge-detected in DrawHUD). */
	bool bShowControls = true;

private:
	void DrawControls();
	void DrawPanel(const AWHRescueDirector* Dir, const FVector& Hero);
	void DrawMarkers(const AWHRescueDirector* Dir, const FVector& Hero);
	void DrawPrompt(const AWHRescueDirector* Dir);
	/** Enemy-race mini-game (owner request 2026-10-25): villain marker + distance, taunt line, caught banner. */
	void DrawChase(const class UWHFlightWorldSubsystem* Sub, const FVector& Hero);
	void Text(const FString& Str, float X, float Y, const FLinearColor& Col, UFont* InFont, float Scale, bool bCentreX = false);
	float TextW(const FString& Str, UFont* InFont, float Scale) const;

	static FString Money(double USD);
	static FString Clock(double Seconds);
	static FString TypeLabel(const FWHEmergency& E);
	static FLinearColor TypeColor(const FWHEmergency& E);

	TWeakObjectPtr<AWHRescueDirector> Director;
	float UiScale = 1.f;   // 1 at 1080p
	bool bPrevHKey = false;   // H key state last drawn frame (toggle edge)
};
