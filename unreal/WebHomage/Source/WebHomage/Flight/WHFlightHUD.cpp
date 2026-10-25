// Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation.
#include "Flight/WHFlightHUD.h"
#include "Flight/WHFlightWorld.h"
#include "Flight/WHRescueDirector.h"
#include "CanvasItem.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "Math/RotationMatrix.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace
{
	const FLinearColor White(0.95f, 0.95f, 0.95f, 1.f);
	const FLinearColor Dim(0.72f, 0.74f, 0.78f, 1.f);
	const FLinearColor Urgent(1.0f, 0.28f, 0.2f, 1.f);
	const FLinearColor Good(0.45f, 1.0f, 0.55f, 1.f);
	const FLinearColor Panel(0.f, 0.f, 0.f, 0.38f);
	const FLinearColor KeyYellow(1.0f, 0.86f, 0.28f, 1.f);   // owner request 2026-10-16: key names in the controls panel

	// Owner request 2026-10-16: the controls panel rows (keyboard + mouse). One line per action; a row may carry a second key / action pair.
	// Bindings verified against WebTravCharacter.cpp (IMC + PollLiveInput) and WHFlightComponent.cpp (StepAirSub / StepFlight):
	// Space = takeoff on the ground / climb in the air (second airborne press within DoubleTapTime 0.3 s = the dive), RMB = fly line,
	// Shift = sonic-boom charge + launch (held = super speed), C / LeftCtrl = descend, E = brake (also the rescue hold / set-down),
	// Q = dash, F = slam (air only), Esc / P = settings menu (WebHomagePlayerController).
	struct FCtlRow { const TCHAR* Key; const TCHAR* Act; const TCHAR* Key2; const TCHAR* Act2; };
	const FCtlRow CtlRows[] = {
		{ TEXT("WASD"),     TEXT("move / strafe / turn"),                 nullptr,      nullptr },
		{ TEXT("Mouse"),    TEXT("look / steer flight"),                  nullptr,      nullptr },
		{ TEXT("Space"),    TEXT("take off / climb"),                     nullptr,      nullptr },
		{ TEXT("Space x2"), TEXT("superhero landing (in air)"),           nullptr,      nullptr },
		{ TEXT("Hold RMB"), TEXT("fly"),                                  nullptr,      nullptr },
		{ TEXT("Shift"),    TEXT("sonic boom boost (hold = super speed)"), nullptr,     nullptr },
		{ TEXT("C / Ctrl"), TEXT("descend"),                              nullptr,      nullptr },
		{ TEXT("E"),        TEXT("brake / rescue (hold) / set down"),     nullptr,      nullptr },
		{ TEXT("Q"),        TEXT("dash"),                                 TEXT("F"),    TEXT("slam (in air)") },
		{ TEXT("Esc / P"),  TEXT("menu / release mouse"),                 nullptr,      nullptr },
		{ TEXT("H"),        TEXT("hide / show controls"),                 nullptr,      nullptr },
	};
}

AWHFlightHUD::AWHFlightHUD()
{
	bShowHUD = true;
}

void AWHFlightHUD::BeginPlay()
{
	Super::BeginPlay();
	bNoOverlay = FParse::Param(FCommandLine::Get(), TEXT("WHNoHUD"));
}

FString AWHFlightHUD::Money(double USD)
{
	USD = FMath::Max(0.0, USD);
	if (USD >= 1.0e9) return FString::Printf(TEXT("$%.2fB"), USD / 1.0e9);
	if (USD >= 1.0e6) return FString::Printf(TEXT("$%.1fM"), USD / 1.0e6);
	if (USD >= 1.0e3) return FString::Printf(TEXT("$%.0fK"), USD / 1.0e3);
	return FString::Printf(TEXT("$%.0f"), USD);
}

FString AWHFlightHUD::Clock(double Seconds)
{
	const int32 T = FMath::Max(0, FMath::CeilToInt(Seconds));
	return FString::Printf(TEXT("%d:%02d"), T / 60, T % 60);
}

FString AWHFlightHUD::TypeLabel(const FWHEmergency& E)
{
	switch (E.Type)
	{
	case EWHEmergencyType::Fire:  return TEXT("FIRE");
	case EWHEmergencyType::Crane: return E.bFalling ? TEXT("CRANE  FALLING") : TEXT("CRANE");
	case EWHEmergencyType::Bus:   return TEXT("BUS");
	}
	return TEXT("");
}

FLinearColor AWHFlightHUD::TypeColor(const FWHEmergency& E)
{
	switch (E.Type)
	{
	case EWHEmergencyType::Fire:  return FLinearColor(1.0f, 0.42f, 0.12f, 1.f);
	case EWHEmergencyType::Crane: return FLinearColor(1.0f, 0.82f, 0.2f, 1.f);
	case EWHEmergencyType::Bus:   return FLinearColor(0.35f, 0.8f, 1.0f, 1.f);
	}
	return White;
}

void AWHFlightHUD::Text(const FString& Str, float X, float Y, const FLinearColor& Col, UFont* InFont, float Scale, bool bCentreX)
{
	if (!Canvas || !InFont) return;
	FCanvasTextItem Item(FVector2D(X, Y), FText::FromString(Str), InFont, Col);
	Item.Scale = FVector2D(Scale, Scale);
	Item.bCentreX = bCentreX;
	Item.EnableShadow(FLinearColor(0.f, 0.f, 0.f, 0.85f), FVector2D(1.0, 1.0));
	Canvas->DrawItem(Item);
}

float AWHFlightHUD::TextW(const FString& Str, UFont* InFont, float Scale) const
{
	float W = 0.f, H = 0.f;
	GetTextSize(Str, W, H, InFont, Scale);
	return W;
}

void AWHFlightHUD::DrawHUD()
{
	Super::DrawHUD();
	if (bNoOverlay || !Canvas || !GEngine) return;
	UWorld* W = GetWorld();
	const UWHFlightWorldSubsystem* Sub = UWHFlightWorldSubsystem::Get(this);
	if (!W || !Sub || !Sub->bFlightMode) return;
	if (PlayerOwner && PlayerOwner->IsPaused()) return;   // the settings menu is open: keep the screen clean under it

	UiScale = FMath::Clamp(1.45f * float(Canvas->ClipY) / 1080.f, 0.8f, 4.f);   // critic r1: ~12 px text at 1080p was unreadable
	if (!Director.IsValid()) Director = AWHRescueDirector::Find(W);
	const AWHRescueDirector* Dir = Director.Get();

	FVector Hero = Sub->bHeroValid ? Sub->HeroPosCm : FVector::ZeroVector;
	if (!Sub->bHeroValid && PlayerOwner && PlayerOwner->GetPawn()) Hero = PlayerOwner->GetPawn()->GetActorLocation();

	// owner request 2026-10-16: H hides / shows the controls panel (edge on the held state; H is bound to nothing else in the project)
	if (PlayerOwner)
	{
		const bool bH = PlayerOwner->IsInputKeyDown(EKeys::H);
		if (bH && !bPrevHKey) bShowControls = !bShowControls;
		bPrevHKey = bH;
	}

	DrawControls();
	DrawPanel(Dir, Hero);
	if (Dir && Dir->IsEnabled())
	{
		DrawMarkers(Dir, Hero);
		DrawPrompt(Dir);
	}
	DrawChase(Sub, Hero);
}

// Enemy-race mini-game (owner request 2026-10-25): a red diamond over the villain (chevron at the edge when he is
// off screen), his taunt line, and the caught banner. The villain publishes into the flight world subsystem.
void AWHFlightHUD::DrawChase(const UWHFlightWorldSubsystem* Sub, const FVector& Hero)
{
	if (!Sub || Sub->VillainState == 0 || !PlayerOwner) return;
	const FLinearColor VRed(1.0f, 0.22f, 0.18f, 1.f);
	UFont* Small = GEngine->GetSmallFont();
	UFont* Med = GEngine->GetMediumFont();
	const float K = UiScale;
	const float CX = float(Canvas->ClipX) * 0.5f, CY = float(Canvas->ClipY) * 0.5f;

	if (Sub->bVillainCaught)
	{
		const double T = Sub->ChaseCaughtT - Sub->ChaseStartT;
		Text(FString::Printf(TEXT("GOT HIM -- %.0f s"), T), CX, CY - 40.f * K, VRed, Med, 1.0f, true);
		Text(TEXT("villain caught"), CX, CY - 12.f * K, White, Small, 1.2f * K, true);
		Text(TEXT("B -- chase again"), CX, CY + 8.f * K, Dim, Small, 1.1f * K, true);
	}
	else
	{
		FVector CamLoc; FRotator CamRot;
		PlayerOwner->GetPlayerViewPoint(CamLoc, CamRot);
		const FRotationMatrix CM(CamRot);
		const FVector Fwd = CM.GetScaledAxis(EAxis::X), Right = CM.GetScaledAxis(EAxis::Y), Up = CM.GetScaledAxis(EAxis::Z);
		const FVector D = Sub->VillainPosCm - CamLoc;
		const double DistM = FVector::Dist(Hero, Sub->VillainPosCm) / 100.0;
		const FString Label = FString::Printf(TEXT("VILLAIN  %.0f m"), DistM);
		const float Margin = 56.f * K;
		const bool bFront = FVector::DotProduct(D, Fwd) > 1.0;
		FVector2D Sp(CX, CY);
		bool bOnScreen = false;
		if (bFront)
		{
			// mark the point ~5 m ABOVE him: a diamond on his body hides the tiny figure (owner 2026-10-25)
			const FVector P = Canvas->Project(Sub->VillainPosCm + FVector(0, 0, 500.0));
			Sp = FVector2D(P.X, P.Y);
			bOnScreen = Sp.X > Margin && Sp.X < Canvas->ClipX - Margin && Sp.Y > Margin && Sp.Y < Canvas->ClipY - Margin;
		}
		if (bOnScreen)
		{
			const float R = 11.f * K, T = FMath::Max(1.5f, 2.5f * K);
			DrawLine(Sp.X, Sp.Y - R, Sp.X + R, Sp.Y, VRed, T);
			DrawLine(Sp.X + R, Sp.Y, Sp.X, Sp.Y + R, VRed, T);
			DrawLine(Sp.X, Sp.Y + R, Sp.X - R, Sp.Y, VRed, T);
			DrawLine(Sp.X - R, Sp.Y, Sp.X, Sp.Y - R, VRed, T);
			DrawRect(VRed, Sp.X - 2.f * K, Sp.Y - 2.f * K, 4.f * K, 4.f * K);
			Text(Label, Sp.X, Sp.Y + R + 4.f * K, VRed, Small, 1.1f * K, true);
		}
		else
		{
			FVector2D Dv = bFront ? (Sp - FVector2D(CX, CY)) : FVector2D(FVector::DotProduct(D, Right), -FVector::DotProduct(D, Up));
			if (Dv.SizeSquared() < 1e-6) Dv = FVector2D(0.0, 1.0);
			Dv.Normalize();
			const float Hx = CX - Margin, Hy = CY - Margin;
			const float Tx = FMath::Abs(Dv.X) > 1e-4 ? Hx / FMath::Abs(float(Dv.X)) : 1e9f;
			const float Ty = FMath::Abs(Dv.Y) > 1e-4 ? Hy / FMath::Abs(float(Dv.Y)) : 1e9f;
			const FVector2D Ep = FVector2D(CX, CY) + Dv * FMath::Min(Tx, Ty);
			const FVector2D Pp(-Dv.Y, Dv.X);
			const float L = 16.f * K, T = FMath::Max(2.f, 3.f * K);
			const FVector2D Tip = Ep + Dv * (L * 0.6f);
			const FVector2D A = Ep - Dv * (L * 0.4f) + Pp * L * 0.7f;
			const FVector2D B = Ep - Dv * (L * 0.4f) - Pp * L * 0.7f;
			DrawLine(A.X, A.Y, Tip.X, Tip.Y, VRed, T);
			DrawLine(B.X, B.Y, Tip.X, Tip.Y, VRed, T);
			const FVector2D Lp = Ep - Dv * (L * 1.6f + 14.f * K);
			Text(Label, Lp.X, Lp.Y - 8.f * K, VRed, Small, 1.0f * K, true);
		}
	}
	if (!Sub->VillainTaunt.IsEmpty())
		Text(Sub->VillainTaunt, CX, float(Canvas->ClipY) - 150.f * K, VRed, Small, 1.5f * K, true);
	// cutscene dialogue: bottom-centre subtitle, bigger than the taunt line
	if (!Sub->ChaseLine.IsEmpty() && PlayerOwner && PlayerOwner->GetWorld()->GetTimeSeconds() < Sub->ChaseLineUntil)
	{
		const bool bHeroLine = Sub->ChaseLine.StartsWith(TEXT("YOU"));
		Text(Sub->ChaseLine, CX, float(Canvas->ClipY) - 110.f * K, bHeroLine ? White : VRed, Med, 0.85f, true);
	}
}

void AWHFlightHUD::DrawPanel(const AWHRescueDirector* Dir, const FVector& Hero)
{
	const UWHFlightWorldSubsystem* Sub = UWHFlightWorldSubsystem::Get(this);
	UFont* Small = GEngine->GetSmallFont();
	UFont* Medium = GEngine->GetMediumFont();
	UFont* Large = GEngine->GetLargeFont();
	const float K = UiScale;
	// owner request 2026-10-16: the controls panel takes the top-left corner, so the rescue panel sits at the top-right
	const float Wd = 330.f * K, Pad = 12.f * K, Row = 26.f * K;
	const float X = FMath::Max(28.f * K, float(Canvas->ClipX) - Wd - 28.f * K), Y = 28.f * K;

	TArray<const FWHEmergency*> Active;
	if (Dir && Dir->IsEnabled())
		for (const FWHEmergency& E : Dir->GetEmergencies())
			if (E.State == EWHEmergencyState::Active) Active.Add(&E);
	const double NextWave = Dir && Dir->IsEnabled() ? Dir->GetNextWaveIn() : -1.0;
	const bool bWaveLine = Active.Num() == 0 && NextWave >= 0.0 && Dir->GetWave() > 0;

	const float H = Pad * 2.f + 64.f * K + Row + (Active.Num() > 0 || bWaveLine ? 10.f * K + Row * FMath::Max(Active.Num(), 1) : 0.f);
	DrawRect(Panel, X, Y, Wd, H);

	// lives saved (the score), lost, collateral
	float Cy = Y + Pad;
	Text(TEXT("LIVES SAVED"), X + Pad, Cy, Dim, Small, 1.2f * K);
	Text(FString::FromInt(Sub ? Sub->LivesSaved : 0), X + Pad, Cy + 16.f * K, Good, Large, 1.5f * K);
	const FString Lost = FString::Printf(TEXT("LOST %d"), Sub ? Sub->LivesLost : 0);
	Text(Lost, X + Wd - Pad - TextW(Lost, Small, 1.2f * K), Cy, (Sub && Sub->LivesLost > 0) ? Urgent : Dim, Small, 1.2f * K);
	Cy += 64.f * K;
	Text(TEXT("COLLATERAL"), X + Pad, Cy + 4.f * K, Dim, Small, 1.2f * K);
	const FString Dmg = Money(Sub ? Sub->CollateralUSD : 0.0);
	Text(Dmg, X + Wd - Pad - TextW(Dmg, Medium, 0.9f * K), Cy, White, Medium, 0.9f * K);
	Cy += Row;

	if (Active.Num() > 0 || bWaveLine)
	{
		DrawRect(FLinearColor(1.f, 1.f, 1.f, 0.18f), X + Pad, Cy + 3.f * K, Wd - 2.f * Pad, FMath::Max(1.f, 1.f * K));
		Cy += 10.f * K;
	}
	// one row per active emergency: colour tab, type, distance, rescue clock
	for (const FWHEmergency* E : Active)
	{
		const FLinearColor C = TypeColor(*E);
		DrawRect(C, X + Pad, Cy + 5.f * K, 4.f * K, Row - 10.f * K);
		Text(TypeLabel(*E), X + Pad + 12.f * K, Cy, C, Medium, 0.8f * K);
		const FString Tm = Clock(E->RemainingS);
		const FString Dist = FString::Printf(TEXT("%.0f m"), FVector::Dist(Hero, E->FocusCm) / 100.0);
		const float TmW = TextW(TEXT("0:00"), Medium, 0.8f * K);
		Text(Tm, X + Wd - Pad - TextW(Tm, Medium, 0.8f * K), Cy, E->RemainingS < 15.0 ? Urgent : White, Medium, 0.8f * K);
		Text(Dist, X + Wd - Pad - TmW - 18.f * K - TextW(Dist, Medium, 0.8f * K), Cy, Dim, Medium, 0.8f * K);
		Cy += Row;
	}
	if (bWaveLine)
	{
		Text(TEXT("NEXT CALL"), X + Pad, Cy + 4.f * K, Dim, Small, 1.2f * K);
		const FString Tm = Clock(NextWave);
		Text(Tm, X + Wd - Pad - TextW(Tm, Medium, 0.8f * K), Cy, White, Medium, 0.8f * K);
	}
}

// Owner request 2026-10-16: "put the controls on screen on the top left, small but in a way that I can see it". A compact translucent
// panel (thin border, white labels, yellow key names), one line per action. The text size is derived from a measured reference line
// (~16.5 px line = ~14 px glyphs at 1080p, scaled by ClipY / 1080) so it does not depend on the engine font's native point size.
void AWHFlightHUD::DrawControls()
{
	UFont* Font = GEngine->GetSmallFont();
	if (!Font) return;
	const float Rel = float(Canvas->ClipY) / 1080.f;
	constexpr float RefScale = 8.f;   // (the canvas reports integer sizes: measure large, divide down)
	float RefW = 0.f, RefH = 0.f;
	GetTextSize(TEXT("Ag|"), RefW, RefH, Font, RefScale);
	const bool bMeasured = RefH > RefScale;
	const float Sc = bMeasured ? FMath::Clamp(16.5f * Rel * RefScale / RefH, 0.4f, 8.f) : 0.9f * UiScale;
	const float LineH = bMeasured ? RefH * Sc / RefScale : 16.5f * Rel;
	const float Pitch = LineH * 1.06f;
	const float Pad = 8.f * Rel, Gap = 12.f * Rel, PairGap = 22.f * Rel;
	if (!bShowControls)
	{ // hidden with H: one dim hint line, so the panel can always be brought back
		Text(TEXT("H  show controls"), 16.f * Rel, 16.f * Rel, Dim, Font, Sc);
		return;
	}

	float KeyW = 0.f, LabW = 0.f;
	for (const FCtlRow& R : CtlRows)
	{
		KeyW = FMath::Max(KeyW, TextW(R.Key, Font, Sc));
		float W1 = TextW(R.Act, Font, Sc);
		if (R.Key2) W1 += PairGap + TextW(R.Key2, Font, Sc) + Gap + TextW(R.Act2, Font, Sc);
		LabW = FMath::Max(LabW, W1);
	}
	const int32 NRows = static_cast<int32>(UE_ARRAY_COUNT(CtlRows));
	const float W = Pad * 2.f + KeyW + Gap + LabW;
	const float H = Pad * 2.f + Pitch * float(NRows - 1) + LineH;
	const float X0 = 16.f * Rel, Y0 = 16.f * Rel;

	DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.46f), X0, Y0, W, H);
	const float Bt = FMath::Max(1.f, FMath::RoundToFloat(Rel));
	const FLinearColor Edge(1.f, 1.f, 1.f, 0.30f);
	DrawRect(Edge, X0, Y0, W, Bt);
	DrawRect(Edge, X0, Y0 + H - Bt, W, Bt);
	DrawRect(Edge, X0, Y0, Bt, H);
	DrawRect(Edge, X0 + W - Bt, Y0, Bt, H);

	const float LabX = X0 + Pad + KeyW + Gap;
	for (int32 i = 0; i < NRows; ++i)
	{
		const FCtlRow& R = CtlRows[i];
		const float Ty = Y0 + Pad + Pitch * float(i);
		Text(R.Key, X0 + Pad, Ty, KeyYellow, Font, Sc);
		Text(R.Act, LabX, Ty, White, Font, Sc);
		if (R.Key2)
		{
			const float K2x = LabX + TextW(R.Act, Font, Sc) + PairGap;
			Text(R.Key2, K2x, Ty, KeyYellow, Font, Sc);
			Text(R.Act2, K2x + TextW(R.Key2, Font, Sc) + Gap, Ty, White, Font, Sc);
		}
	}
}

void AWHFlightHUD::DrawMarkers(const AWHRescueDirector* Dir, const FVector& Hero)
{
	if (!PlayerOwner) return;
	FVector CamLoc; FRotator CamRot;
	PlayerOwner->GetPlayerViewPoint(CamLoc, CamRot);
	const FRotationMatrix CM(CamRot);
	const FVector Fwd = CM.GetScaledAxis(EAxis::X), Right = CM.GetScaledAxis(EAxis::Y), Up = CM.GetScaledAxis(EAxis::Z);
	UFont* Small = GEngine->GetSmallFont();
	const float K = UiScale;
	const float CX = float(Canvas->ClipX) * 0.5f, CY = float(Canvas->ClipY) * 0.5f;
	const float Margin = 56.f * K;

	for (const FWHEmergency& E : Dir->GetEmergencies())
	{
		if (E.State != EWHEmergencyState::Active) continue;
		const FLinearColor C = TypeColor(E);
		const FVector D = E.FocusCm - CamLoc;
		const FString Label = FString::Printf(TEXT("%.0f m  %s"), FVector::Dist(Hero, E.FocusCm) / 100.0, *Clock(E.RemainingS));
		const bool bFront = FVector::DotProduct(D, Fwd) > 1.0;
		FVector2D Sp(CX, CY);
		bool bOnScreen = false;
		if (bFront)
		{
			const FVector P = Canvas->Project(E.FocusCm);
			Sp = FVector2D(P.X, P.Y);
			bOnScreen = Sp.X > Margin && Sp.X < Canvas->ClipX - Margin && Sp.Y > Margin && Sp.Y < Canvas->ClipY - Margin;
		}
		if (bOnScreen)
		{
			// diamond + label
			const float R = 13.f * K, T = FMath::Max(1.5f, 2.5f * K);
			const float Pulse = (E.RemainingS < 15.0) ? 0.6f + 0.4f * FMath::Abs(FMath::Sin(float(GetWorld()->GetTimeSeconds()) * 6.f)) : 1.f;
			const FLinearColor Cp(C.R, C.G, C.B, Pulse);
			DrawLine(Sp.X, Sp.Y - R, Sp.X + R, Sp.Y, Cp, T);
			DrawLine(Sp.X + R, Sp.Y, Sp.X, Sp.Y + R, Cp, T);
			DrawLine(Sp.X, Sp.Y + R, Sp.X - R, Sp.Y, Cp, T);
			DrawLine(Sp.X - R, Sp.Y, Sp.X, Sp.Y - R, Cp, T);
			DrawRect(Cp, Sp.X - 2.f * K, Sp.Y - 2.f * K, 4.f * K, 4.f * K);
			Text(Label, Sp.X, Sp.Y + R + 4.f * K, White, Small, 1.1f * K, true);
			continue;
		}
		// off screen or behind: a chevron on the screen edge pointing toward the emergency
		FVector2D Dv = bFront ? (Sp - FVector2D(CX, CY)) : FVector2D(FVector::DotProduct(D, Right), -FVector::DotProduct(D, Up));
		if (Dv.SizeSquared() < 1e-6) Dv = FVector2D(0.0, 1.0);
		Dv.Normalize();
		const float Hx = CX - Margin, Hy = CY - Margin;
		const float Tx = FMath::Abs(Dv.X) > 1e-4 ? Hx / FMath::Abs(float(Dv.X)) : 1e9f;
		const float Ty = FMath::Abs(Dv.Y) > 1e-4 ? Hy / FMath::Abs(float(Dv.Y)) : 1e9f;
		const FVector2D Ep = FVector2D(CX, CY) + Dv * FMath::Min(Tx, Ty);
		const FVector2D Pp(-Dv.Y, Dv.X);
		const float L = 16.f * K, T = FMath::Max(2.f, 3.f * K);
		const FVector2D Tip = Ep + Dv * (L * 0.6f);
		const FVector2D A = Ep - Dv * (L * 0.4f) + Pp * L * 0.7f;
		const FVector2D B = Ep - Dv * (L * 0.4f) - Pp * L * 0.7f;
		DrawLine(A.X, A.Y, Tip.X, Tip.Y, C, T);
		DrawLine(B.X, B.Y, Tip.X, Tip.Y, C, T);
		const FVector2D Lp = Ep - Dv * (L * 1.6f + 14.f * K);
		Text(Label, Lp.X, Lp.Y - 8.f * K, White, Small, 1.0f * K, true);
	}
}

void AWHFlightHUD::DrawPrompt(const AWHRescueDirector* Dir)
{
	const FWHEmergency* Near = nullptr;
	const FWHEmergency* Carried = nullptr;
	for (const FWHEmergency& E : Dir->GetEmergencies())
	{
		if (E.bCarried) Carried = &E;
		if (E.State == EWHEmergencyState::Active && E.bHeroInRange && (!Near || E.HoldProgress > Near->HoldProgress)) Near = &E;
	}
	FString Msg;
	double Progress = -1.0;
	if (Carried) Msg = TEXT("E / TRIANGLE   SET THE LOAD DOWN");
	else if (Near)
	{
		switch (Near->Type)
		{
		case EWHEmergencyType::Fire:  Msg = FString::Printf(TEXT("HOLD E / TRIANGLE   EVACUATE  (%d TRAPPED)"), Near->LivesAtStake); Progress = Near->HoldProgress; break;
		case EWHEmergencyType::Crane: Msg = TEXT("GRAB THE LOAD"); break;
		case EWHEmergencyType::Bus:   Msg = FString::Printf(TEXT("HOLD E / TRIANGLE   PULL THE BUS BACK  (%d ABOARD)"), Near->LivesAtStake); Progress = Near->HoldProgress; break;
		}
	}
	if (Msg.IsEmpty()) return;
	UFont* Medium = GEngine->GetMediumFont();
	const float K = UiScale;
	const float CX = float(Canvas->ClipX) * 0.5f, Y = float(Canvas->ClipY) - 150.f * K;
	const float Tw = TextW(Msg, Medium, 0.8f * K);
	const float Wd = FMath::Max(Tw + 40.f * K, 320.f * K);
	DrawRect(Panel, CX - Wd * 0.5f, Y - 10.f * K, Wd, (Progress >= 0.0 ? 52.f : 40.f) * K);
	Text(Msg, CX, Y - 2.f * K, White, Medium, 0.8f * K, true);
	if (Progress >= 0.0)
	{
		const float Bw = Wd - 40.f * K, Bx = CX - Bw * 0.5f, By = Y + 28.f * K;
		DrawRect(FLinearColor(1.f, 1.f, 1.f, 0.2f), Bx, By, Bw, 5.f * K);
		DrawRect(Near ? TypeColor(*Near) : White, Bx, By, Bw * float(FMath::Clamp(Progress, 0.0, 1.0)), 5.f * K);
	}
}
