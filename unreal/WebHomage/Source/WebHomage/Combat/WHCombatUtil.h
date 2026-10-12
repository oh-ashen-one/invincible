// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// Piece P5 (combat): small shared helpers (port of src/game/combat/util.js). METRES, UE axes (X fwd, Y right, Z up).
// Yaw convention everywhere in Combat/: radians, atan2(Y, X) (0 = +X, + = turning right), same as the traversal component.
// Browser yaw was atan2(dx, dz) in three.js (Y up, + = turning LEFT): left/right decisions are mirrored where noted.
#pragma once

#include "CoreMinimal.h"

namespace WHCmb
{
	inline double Clamp(double X, double A, double B) { return FMath::Clamp(X, A, B); }
	inline double Smooth(double X) { X = FMath::Clamp(X, 0.0, 1.0); return X * X * (3.0 - 2.0 * X); }
	inline double Damp(double A, double B, double Rate, double Dt) { return A + (B - A) * (1.0 - FMath::Exp(-Rate * Dt)); }
	inline double AngWrap(double A) { return FMath::Atan2(FMath::Sin(A), FMath::Cos(A)); }
	inline double DampAngle(double A, double B, double Rate, double Dt) { return A + AngWrap(B - A) * (1.0 - FMath::Exp(-Rate * Dt)); }
	inline double YawTo(const FVector& From, const FVector& To) { return FMath::Atan2(To.Y - From.Y, To.X - From.X); }
	inline double HDist(const FVector& A, const FVector& B) { return FMath::Sqrt(FMath::Square(A.X - B.X) + FMath::Square(A.Y - B.Y)); }
	inline FVector YawDir(double Yaw) { return FVector(FMath::Cos(Yaw), FMath::Sin(Yaw), 0.0); }
	inline FVector Flat(const FVector& V) { return FVector(V.X, V.Y, 0.0); }
	inline FVector FlatNorm(const FVector& V, const FVector& Fallback = FVector::ForwardVector)
	{
		FVector F(V.X, V.Y, 0.0); const double L = F.Size();
		return L > 1e-6 ? F / L : Fallback;
	}
	inline double Lerp(double A, double B, double T) { return A + (B - A) * T; }
}
