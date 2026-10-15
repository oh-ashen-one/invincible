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

	UiScale = FMath::Clamp(float(Canvas->ClipY) / 1080.f, 0.6f, 3.f);
	if (!Director.IsValid()) Director = AWHRescueDirector::Find(W);
	const AWHRescueDirector* Dir = Director.Get();

	FVector Hero = Sub->bHeroValid ? Sub->HeroPosCm : FVector::ZeroVector;
	if (!Sub->bHeroValid && PlayerOwner && PlayerOwner->GetPawn()) Hero = PlayerOwner->GetPawn()->GetActorLocation();

	DrawPanel(Dir, Hero);
	if (Dir && Dir->IsEnabled())
	{
		DrawMarkers(Dir, Hero);
		DrawPrompt(Dir);
	}
}

void AWHFlightHUD::DrawPanel(const AWHRescueDirector* Dir, const FVector& Hero)
{
	const UWHFlightWorldSubsystem* Sub = UWHFlightWorldSubsystem::Get(this);
	UFont* Small = GEngine->GetSmallFont();
	UFont* Medium = GEngine->GetMediumFont();
	UFont* Large = GEngine->GetLargeFont();
	const float K = UiScale;
	const float X = 28.f * K, Y = 28.f * K, Wd = 330.f * K, Pad = 12.f * K, Row = 26.f * K;

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
