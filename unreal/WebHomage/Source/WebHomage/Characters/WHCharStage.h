// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// P2 Characters (round 09): the stage clock of a choreographed test map.  The capture director owns it: at BeginPlay it stores the offset between
// the world clock and its own shot clock (which starts at the sum of the shots before -WHCharShot=N), so a scripted fight is a pure function of
// this time and starting at shot 1 gives the same state as playing through shot 0.  Walkers (paths) and AnimInstances (script beats) read Now().
#pragma once
#include "CoreMinimal.h"
#include "Engine/World.h"

namespace WHStage
{
	inline double& Offset() { static double O = 0.0; return O; }
	inline float Now(const UWorld* W) { return W ? float(W->GetTimeSeconds() + Offset()) : 0.f; }
	inline float Smooth(float X) { X = FMath::Clamp(X, 0.f, 1.f); return X * X * (3.f - 2.f * X); }
}
