// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#include "Core/WHSettingsMenu.h"
#include "Core/WHSettings.h"
#include "Core/WebHomagePlayerController.h"
#include "Characters/WHHeroSuit.h"

#include "Brushes/SlateColorBrush.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Framework/Application/SlateApplication.h"
#include "InputCoreTypes.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Input/SSlider.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "WHSettingsMenu"

namespace
{
	const FLinearColor TextCol(0.93f, 0.95f, 0.98f, 1.f);
	const FLinearColor DimCol(0.62f, 0.66f, 0.73f, 1.f);
	const FLinearColor Accent(0.10f, 0.40f, 0.95f, 1.f);   // linear colours (Slate converts to sRGB on screen)
	const FLinearColor Danger(0.62f, 0.07f, 0.06f, 1.f);
	const FLinearColor Neutral(0.10f, 0.11f, 0.14f, 1.f);
	constexpr float RowH = 46.f;

	// brushes live as long as the module (the widget is rebuilt each time the menu opens)
	const FSlateBrush* Backdrop() { static FSlateColorBrush B(FLinearColor(0.f, 0.f, 0.f, 0.45f)); return &B; }
	const FSlateBrush* Panel() { static FSlateRoundedBoxBrush B(FLinearColor(0.012f, 0.014f, 0.020f, 0.95f), 14.f, FLinearColor(1.f, 1.f, 1.f, 0.10f), 1.f); return &B; }
	const FSlateBrush* RowBrush() { static FSlateRoundedBoxBrush B(FLinearColor::White, 8.f); return &B; }
	const FSlateBrush* Rule() { static FSlateColorBrush B(FLinearColor(1.f, 1.f, 1.f, 0.12f)); return &B; }

	FSlateFontInfo Font(const char* Style, int32 Size) { return FCoreStyle::GetDefaultFontStyle(Style, Size); }

	FLinearColor Scaled(const FLinearColor& C, float K) { return FLinearColor(C.R * K, C.G * K, C.B * K, 1.f); }

	/** Flat rounded button in a solid colour (the engine default button image is dark grey, so a tint alone looks muddy). */
	const FButtonStyle* ButtonStyle(const FLinearColor& C)
	{
		static TMap<uint32, FButtonStyle> Cache;
		const uint32 Key = GetTypeHash(C.ToFColor(true));
		if (const FButtonStyle* Found = Cache.Find(Key)) return Found;
		FButtonStyle S = FCoreStyle::Get().GetWidgetStyle<FButtonStyle>("Button");
		S.SetNormal(FSlateRoundedBoxBrush(C, 8.f));
		S.SetHovered(FSlateRoundedBoxBrush(Scaled(C, 1.3f), 8.f, FLinearColor(1.f, 1.f, 1.f, 0.85f), 2.f));
		S.SetPressed(FSlateRoundedBoxBrush(Scaled(C, 0.75f), 8.f));
		S.SetNormalPadding(FMargin(0.f)); S.SetPressedPadding(FMargin(0.f));
		return &Cache.Add(Key, S);
	}

	TSharedRef<SWidget> Separator()
	{
		return SNew(SBox).HeightOverride(1.f)[SNew(SBorder).BorderImage(Rule())];
	}

	TSharedRef<SWidget> Section(const FText& T)
	{
		return SNew(STextBlock).Text(T).Font(Font("Bold", 14)).ColorAndOpacity(DimCol);
	}

	bool IsAcceptKey(const FKeyEvent& E)
	{
		return FSlateApplication::Get().GetNavigationActionFromKey(E) == EUINavigationAction::Accept;
	}

	/** "<  Value  >" choice: left / right (D-pad, stick, arrows) or a click on either half steps it; Accept steps forward. */
	class SWHChoice : public SCompoundWidget
	{
	public:
		SLATE_BEGIN_ARGS(SWHChoice) {}
			SLATE_ARGUMENT(int32, Count)
		SLATE_END_ARGS()

		TFunction<int32()> Get;
		TFunction<void(int32)> Set;
		TFunction<FText(int32)> Name;

		void Construct(const FArguments& A, TFunction<int32()> InGet, TFunction<void(int32)> InSet, TFunction<FText(int32)> InName)
		{
			Count = FMath::Max(1, A._Count);
			Get = MoveTemp(InGet); Set = MoveTemp(InSet); Name = MoveTemp(InName);
			ChildSlot
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
				[
					SNew(STextBlock).Text(FText::FromString(TEXT("<"))).Font(Font("Bold", 20)).ColorAndOpacity(Accent)
				]
				+ SHorizontalBox::Slot().FillWidth(1.f).HAlign(HAlign_Center).VAlign(VAlign_Center)
				[
					SNew(STextBlock).Font(Font("Bold", 20)).ColorAndOpacity(TextCol)
					.Text_Lambda([this] { return Name(Get()); })
				]
				+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
				[
					SNew(STextBlock).Text(FText::FromString(TEXT(">"))).Font(Font("Bold", 20)).ColorAndOpacity(Accent)
				]
			];
		}
		void Step(int32 D) { Set((Get() + D + Count) % Count); }
		virtual bool SupportsKeyboardFocus() const override { return true; }
		virtual FReply OnMouseButtonDown(const FGeometry& G, const FPointerEvent& E) override
		{
			const float X = G.AbsoluteToLocal(E.GetScreenSpacePosition()).X;
			Step(X < G.GetLocalSize().X * 0.5f ? -1 : 1);
			return FReply::Handled().SetUserFocus(SharedThis(this), EFocusCause::Mouse);
		}
		virtual FReply OnKeyDown(const FGeometry& G, const FKeyEvent& E) override
		{
			if (IsAcceptKey(E)) { Step(1); return FReply::Handled(); }
			return SCompoundWidget::OnKeyDown(G, E);
		}
		virtual FNavigationReply OnNavigation(const FGeometry& G, const FNavigationEvent& E) override
		{
			if (E.GetNavigationType() == EUINavigation::Left) { Step(-1); return FNavigationReply::Stop(); }
			if (E.GetNavigationType() == EUINavigation::Right) { Step(1); return FNavigationReply::Stop(); }
			return SCompoundWidget::OnNavigation(G, E);
		}
	private:
		int32 Count = 1;
	};
}

void SWHSettingsMenu::Construct(const FArguments& InArgs)
{
	Owner = InArgs._Owner;
	WHSettings().SyncFromCVars();

	auto Times = [](float V) { return FText::FromString(FString::Printf(TEXT("%.2fx"), V)); };
	auto Deg = [](float V) { return FText::FromString(FString::Printf(TEXT("%.0f°"), V)); };
	auto Pct = [](float V) { return FText::FromString(FString::Printf(TEXT("%.0f%%"), V)); };

	ChildSlot
	[
		SNew(SOverlay)
		+ SOverlay::Slot()
		[
			SNew(SBorder).BorderImage(Backdrop())
		]
		+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center).Padding(16.f)
		[
			SNew(SBox).WidthOverride(800.f)
			[
				SNew(SBorder).BorderImage(Panel()).Padding(FMargin(40.f, 28.f))
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot().AutoHeight()
					[
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot().FillWidth(1.f).VAlign(VAlign_Bottom)
						[
							SNew(STextBlock).Text(LOCTEXT("Title", "SETTINGS")).Font(Font("Bold", 34)).ColorAndOpacity(TextCol)
						]
						+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Bottom).Padding(0.f, 0.f, 0.f, 6.f)
						[
							SNew(STextBlock).Text(LOCTEXT("Hint", "Esc / P / Options to resume")).Font(Font("Regular", 15)).ColorAndOpacity(DimCol)
						]
					]
					+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 12.f, 0.f, 12.f) [ Separator() ]

					+ SVerticalBox::Slot().AutoHeight().Padding(10.f, 0.f, 0.f, 2.f) [ Section(LOCTEXT("SecControls", "CONTROLS")) ]
					+ SVerticalBox::Slot().AutoHeight()
					[
						SliderRow(LOCTEXT("Mouse", "Mouse sensitivity"), FWHSettings::MouseSensMin, FWHSettings::MouseSensMax, 0.05f,
							[] { return WHSettings().MouseSens; },
							[](float V) { WHSettings().MouseSens = V; WHSettings().ApplyCVars(); }, Times, /*bFirst*/ true)
					]
					+ SVerticalBox::Slot().AutoHeight()
					[
						CheckRow(LOCTEXT("InvertY", "Invert Y (look)"),
							[] { return WHSettings().bInvertY; }, [](bool b) { WHSettings().bInvertY = b; })
					]
					+ SVerticalBox::Slot().AutoHeight()
					[
						SliderRow(LOCTEXT("Pad", "Gamepad look sensitivity"), FWHSettings::PadSensMin, FWHSettings::PadSensMax, 0.05f,
							[] { return WHSettings().PadSens; }, [](float V) { WHSettings().PadSens = V; }, Times)
					]

					+ SVerticalBox::Slot().AutoHeight().Padding(10.f, 12.f, 0.f, 2.f) [ Section(LOCTEXT("SecCamera", "CAMERA")) ]
					+ SVerticalBox::Slot().AutoHeight()
					[
						SliderRow(LOCTEXT("Fov", "Field of view"), FWHSettings::FovMin, FWHSettings::FovMax, 1.f,
							[] { return WHSettings().FovH; }, [](float V) { WHSettings().FovH = V; }, Deg)
					]
					+ SVerticalBox::Slot().AutoHeight()
					[
						CheckRow(LOCTEXT("Shake", "Camera shake"),
							[] { return WHSettings().bCameraShake; }, [](bool b) { WHSettings().bCameraShake = b; })
					]

					+ SVerticalBox::Slot().AutoHeight().Padding(10.f, 12.f, 0.f, 2.f) [ Section(LOCTEXT("SecHero", "HERO")) ]
					+ SVerticalBox::Slot().AutoHeight()
					[
						ChoiceRow(LOCTEXT("HeroSuit", "Suit (T / D-pad Up in play)"), FMath::Max(1, WHHeroSuits::Count()),
							[] { return WHHeroSuits::Current(); }, [](int32 I) { WHHeroSuits::Set(I, TEXT("menu")); },
							[](int32 I) { return WHHeroSuits::Name(I); })
					]

					+ SVerticalBox::Slot().AutoHeight().Padding(10.f, 12.f, 0.f, 2.f) [ Section(LOCTEXT("SecGraphics", "GRAPHICS")) ]
					+ SVerticalBox::Slot().AutoHeight()
					[
						ChoiceRow(LOCTEXT("Quality", "Quality preset"), FWHSettings::QualityMax + 1,
							[] { return WHSettings().Quality; }, [](int32 Q) { WHSettings().Quality = Q; WHSettings().ApplyRender(); },
							[](int32 Q) { return FWHSettings::QualityName(Q); })
					]
					+ SVerticalBox::Slot().AutoHeight()
					[
						SliderRow(LOCTEXT("ResScale", "Resolution scale"), float(FWHSettings::ResScaleMin), float(FWHSettings::ResScaleMax), 5.f,
							[] { return float(WHSettings().ResScale); },
							[](float V) { const int32 R = FMath::RoundToInt(V / 5.f) * 5; if (R != WHSettings().ResScale) { WHSettings().ResScale = R; WHSettings().ApplyRender(); } },
							Pct)
					]
					+ SVerticalBox::Slot().AutoHeight()
					[
						ChoiceRow(LOCTEXT("Window", "Window mode"), 3,
							[] { return WHSettings().WindowMode; }, [](int32 M) { WHSettings().WindowMode = M; WHSettings().ApplyWindow(); },
							[](int32 M) { return FWHSettings::WindowModeName(M); })
					]
					+ SVerticalBox::Slot().AutoHeight()
					[
						CheckRow(LOCTEXT("VSync", "V-sync"),
							[] { return WHSettings().bVSync; }, [](bool b) { WHSettings().bVSync = b; WHSettings().ApplyRender(); })
					]

					+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 16.f, 0.f, 18.f) [ Separator() ]
					+ SVerticalBox::Slot().AutoHeight()
					[
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot().FillWidth(1.f).Padding(0.f, 0.f, 10.f, 0.f)
						[
							MenuButton(LOCTEXT("Resume", "Resume"), Accent, [this] { Resume(); })
						]
						+ SHorizontalBox::Slot().FillWidth(1.f).Padding(5.f, 0.f)
						[
							MenuButton(LOCTEXT("Defaults", "Reset defaults"), Neutral, [] { WHSettings().ResetToDefaults(); })
						]
						+ SHorizontalBox::Slot().FillWidth(1.f).Padding(10.f, 0.f, 0.f, 0.f)
						[
							MenuButton(LOCTEXT("Quit", "Quit game"), Danger, [this] { if (Owner.IsValid()) Owner->QuitFromMenu(); })
						]
					]
					+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0.f, 14.f, 0.f, 0.f)
					[
						SNew(STextBlock)
						.Text(LOCTEXT("Footer", "Left click in the game captures the mouse.  Escape releases it and opens this menu."))
						.Font(Font("Regular", 13)).ColorAndOpacity(DimCol)
					]
				]
			]
		]
	];
}

TSharedRef<SWidget> SWHSettingsMenu::Row(const FText& Label, TSharedRef<SWidget> Control, TSharedPtr<SWidget> Focusable, TSharedPtr<SWidget> Value)
{
	TWeakPtr<SWidget> WeakF = Focusable;
	return SNew(SBorder)
		.BorderImage(RowBrush())
		.Padding(FMargin(10.f, 0.f))
		.BorderBackgroundColor_Lambda([WeakF]
		{
			const TSharedPtr<SWidget> F = WeakF.Pin();
			const bool bFocus = F.IsValid() && (F->HasAnyUserFocus().IsSet() || F->IsHovered());
			return FSlateColor(bFocus ? FLinearColor(Accent.R, Accent.G, Accent.B, 0.20f) : FLinearColor::Transparent);
		})
		[
			SNew(SBox).HeightOverride(RowH)
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().FillWidth(0.47f).VAlign(VAlign_Center)
				[
					SNew(STextBlock).Text(Label).Font(Font("Regular", 20)).ColorAndOpacity(TextCol)
				]
				+ SHorizontalBox::Slot().FillWidth(0.39f).VAlign(VAlign_Center).Padding(8.f, 0.f)
				[
					Control
				]
				+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
				[
					SNew(SBox).WidthOverride(90.f).HAlign(HAlign_Right)
					[
						Value.IsValid() ? Value.ToSharedRef() : SNullWidget::NullWidget
					]
				]
			]
		];
}

TSharedRef<SWidget> SWHSettingsMenu::SliderRow(const FText& Label, float Min, float Max, float Step,
	TFunction<float()> Get, TFunction<void(float)> Set, TFunction<FText(float)> Format, bool bFirst)
{
	TSharedRef<SSlider> Slider = SNew(SSlider)
		.MinValue(Min).MaxValue(Max).StepSize(Step)
		.RequiresControllerLock(false)   // gamepad: left / right change the value directly, up / down move to the next row
		.SliderBarColor(FLinearColor(1.f, 1.f, 1.f, 0.25f))
		.SliderHandleColor(Accent)
		.Value_Lambda([Get] { return Get(); })
		.OnValueChanged_Lambda([Set, Min, Max](float V) { Set(FMath::Clamp(V, Min, Max)); });
	if (bFirst)
	{
		FirstFocus = Slider;
	}
	TSharedRef<SWidget> ValueText = SNew(STextBlock).Font(Font("Bold", 20)).ColorAndOpacity(TextCol)
		.Text_Lambda([Get, Format] { return Format(Get()); });
	return Row(Label, Slider, Slider, ValueText);
}

TSharedRef<SWidget> SWHSettingsMenu::CheckRow(const FText& Label, TFunction<bool()> Get, TFunction<void(bool)> Set)
{
	TSharedRef<SCheckBox> Box = SNew(SCheckBox)
		.IsChecked_Lambda([Get] { return Get() ? ECheckBoxState::Checked : ECheckBoxState::Unchecked; })
		.OnCheckStateChanged_Lambda([Set](ECheckBoxState St) { Set(St == ECheckBoxState::Checked); })
		[
			SNew(STextBlock).Font(Font("Regular", 19)).Margin(FMargin(6.f, 0.f, 0.f, 0.f))
			.ColorAndOpacity_Lambda([Get] { return FSlateColor(Get() ? TextCol : DimCol); })
			.Text_Lambda([Get] { return Get() ? LOCTEXT("On", "On") : LOCTEXT("Off", "Off"); })
		];
	return Row(Label, Box, Box, nullptr);
}

TSharedRef<SWidget> SWHSettingsMenu::ChoiceRow(const FText& Label, int32 Count, TFunction<int32()> Get, TFunction<void(int32)> Set, TFunction<FText(int32)> Name)
{
	TSharedRef<SWHChoice> C = SNew(SWHChoice, MoveTemp(Get), MoveTemp(Set), MoveTemp(Name)).Count(Count);
	return Row(Label, C, C, nullptr);
}

TSharedRef<SWidget> SWHSettingsMenu::MenuButton(const FText& Label, const FLinearColor& Tint, TFunction<void()> OnClick)
{
	TSharedPtr<SButton> Btn;
	SAssignNew(Btn, SButton)
		.ButtonStyle(ButtonStyle(Tint))
		.HAlign(HAlign_Center).VAlign(VAlign_Center)
		.ContentPadding(FMargin(16.f, 10.f))
		.OnClicked_Lambda([OnClick] { OnClick(); return FReply::Handled(); })
		[
			SNew(STextBlock).Text(Label).Font(Font("Bold", 19)).ColorAndOpacity(FLinearColor::White)
		];
	// gamepad / keyboard focus: brighten the button like a mouse hover
	TWeakPtr<SButton> WeakB = Btn;
	Btn->SetBorderBackgroundColor(TAttribute<FSlateColor>::CreateLambda([WeakB]
	{
		const TSharedPtr<SButton> B = WeakB.Pin();
		return FSlateColor((B.IsValid() && B->HasAnyUserFocus().IsSet()) ? FLinearColor(1.4f, 1.4f, 1.4f, 1.f) : FLinearColor::White);
	}));
	return Btn.ToSharedRef();
}

void SWHSettingsMenu::Resume()
{
	if (Owner.IsValid())
	{
		Owner->CloseSettings(/*bRecapture*/ true);
	}
}

FReply SWHSettingsMenu::OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent)
{
	// keys bubble here from the focused row: Escape / P / Options / Circle (face right) = back to the game
	const FKey K = InKeyEvent.GetKey();
	if (K == EKeys::Escape || K == EKeys::P || K == EKeys::Gamepad_Special_Right || K == EKeys::Gamepad_FaceButton_Right)
	{
		Resume();
		return FReply::Handled();
	}
	return SCompoundWidget::OnKeyDown(MyGeometry, InKeyEvent);
}

#undef LOCTEXT_NAMESPACE
