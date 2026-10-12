// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// In-game settings menu, pure Slate (no .uasset). Opened / closed by AWebHomagePlayerController (Escape, P, gamepad Options).
// Edits WHSettings() live; the controller saves it when the menu closes.
// Gamepad: D-pad / left stick move between rows, left / right change sliders and choices, Cross (face bottom) confirms /
// toggles, Circle (face right) or Options resumes.
#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"

class AWebHomagePlayerController;

class SWHSettingsMenu : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SWHSettingsMenu) {}
		SLATE_ARGUMENT(TWeakObjectPtr<AWebHomagePlayerController>, Owner)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	/** The widget that should receive focus when the menu opens (first row, so the gamepad can navigate at once). */
	TSharedPtr<SWidget> GetInitialFocus() const { return FirstFocus; }

	virtual bool SupportsKeyboardFocus() const override { return true; }
	virtual FReply OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent) override;
	// the full-screen backdrop swallows clicks so they never reach the game viewport (no capture, no attack) while the menu is open
	virtual FReply OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override { return FReply::Handled(); }
	virtual FReply OnMouseButtonUp(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override { return FReply::Handled(); }

private:
	TWeakObjectPtr<AWebHomagePlayerController> Owner;
	TSharedPtr<SWidget> FirstFocus;

	TSharedRef<SWidget> Row(const FText& Label, TSharedRef<SWidget> Control, TSharedPtr<SWidget> Focusable, TSharedPtr<SWidget> Value);
	TSharedRef<SWidget> SliderRow(const FText& Label, float Min, float Max, float Step,
		TFunction<float()> Get, TFunction<void(float)> Set, TFunction<FText(float)> Format, bool bFirst = false);
	TSharedRef<SWidget> CheckRow(const FText& Label, TFunction<bool()> Get, TFunction<void(bool)> Set);
	TSharedRef<SWidget> ChoiceRow(const FText& Label, int32 Count, TFunction<int32()> Get, TFunction<void(int32)> Set, TFunction<FText(int32)> Name);
	TSharedRef<SWidget> MenuButton(const FText& Label, const FLinearColor& Tint, TFunction<void()> OnClick);
	void Resume();
};
