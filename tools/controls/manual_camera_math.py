#!/usr/bin/env python3
"""Compile the current camera's pure orbit/input/slew math, without starting Unreal.

This extracts production functions and the chase/budget statements on each run.
The adapters supply arithmetic types, not collision, rendering or input emulation.
"""
from pathlib import Path
import argparse
import re
import subprocess
import tempfile


def function(source, name):
    start = source.index(name)
    brace = source.index("{", start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--compiler", default="clang++")
    args = parser.parse_args()
    base = args.source_root / "unreal/WebHomage/Source/WebHomage/Traversal"
    source = (base / "WebTravCamera.cpp").read_text()
    header = (base / "WebTravCamera.h").read_text()
    character = (base / "WebTravCharacter.cpp").read_text()
    # These are integration requirements outside the arithmetic-only harness.
    assert "const bool bFlipCam = false;" in source, "trick input still selects a side view"
    sky = re.search(r"const bool bSkyFloat = (.*);", source)[1]
    assert "bFlip" not in sky, "trick input still changes ordinary float framing"
    assert "FlipFrameTail = P.bFlip ? 0.5" in source, "actual flip body tail removed"
    assert "else PollLiveInput(Cast<APlayerController>(GetController()), I, float(Dt));" in character, "stick/camera hitch time steps differ"
    reset = "LookYawDelta = LookPitchDelta = AppliedLookYaw = 0.0;"
    assert source.count(reset) == 2, "reset/update must consume manual deltas"
    assert source.index("TransportManualOrbit(CamXY") < source.index("SDV(CamXY, CamXYV"), "orbit transport must precede Cartesian chase"
    accepted = re.search(r"AppliedLookYaw = LookYawDelta != 0\.0[^;]*;", source)[0]
    functions = "\n".join(function(source, name) for name in (
        "double WrapA(", "double SD(", "void SDV(", "void TransportManualOrbit(",
        "double ManualOrbitTravel(", "void FWebTravCamera::ApplyLook("))
    spring_start = source.index("SDV(CamXY, CamXYV")
    spring = source[spring_start:source.index("SD(CamZ", spring_start)]
    lm = re.search(r"const double Lm = [^;]*;", source)[0]
    mp = re.search(r"const double MP = [^;]*;", source)[0]
    my = re.search(r"const double MY = [^;]*;", source)[0]
    tunings = "\n".join(f"const double {name} = {re.search(rf'{name}\s*=\s*([0-9.]+)', header)[1]};" for name in (
        "ChaseDist", "MinHeroDist", "MaxStepPosM", "MaxStepPitchDeg", "MaxStepYawDeg", "FlipMaxStepYawDeg"))
    prefix = r'''
#include <algorithm>
#include <cmath>
#include <iostream>
#include <stdexcept>
using int32=int;
struct FVector { double X=0,Y=0,Z=0; FVector()=default; FVector(double x,double y,double z):X(x),Y(y),Z(z){}
  FVector operator+(const FVector&o)const{return {X+o.X,Y+o.Y,Z+o.Z};}
  FVector operator-(const FVector&o)const{return {X-o.X,Y-o.Y,Z-o.Z};}
  FVector operator*(double s)const{return {X*s,Y*s,Z*s};}
  FVector& operator*=(double s){X*=s;Y*=s;Z*=s;return *this;}
  double& operator[](int i){return i==0?X:i==1?Y:Z;}
  double operator[](int i)const{return i==0?X:i==1?Y:Z;}
  double Size()const{return std::sqrt(X*X+Y*Y+Z*Z);}
};
struct FVector2D { double X=0,Y=0; FVector2D(double x,double y):X(x),Y(y){} double Size()const{return std::hypot(X,Y);} };
struct FMath { static double Cos(double x){return std::cos(x);} static double Sin(double x){return std::sin(x);}
  static double Atan2(double y,double x){return std::atan2(y,x);} static double Exp(double x){return std::exp(x);}
  static double Abs(double x){return std::abs(x);} static double Max(double a,double b){return std::max(a,b);}
  static double Clamp(double x,double a,double b){return std::clamp(x,a,b);}
  static double RadiansToDegrees(double x){return x*180.0/3.14159265358979323846;}
};
struct FWebTravCamera { double Yaw=0,Pitch=.14,UserPitch=0,Sens=1,LastLook=10,LookYawDelta=0,LookPitchDelta=0,AppliedLookYaw=0;
  int LookYawDir=0; void ApplyLook(const FVector2D& Look); };
void Require(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
'''
    budget = "\n".join(("struct Budget {double pos,pitch,yaw;};", "Budget MakeBudget(double Dt,FVector LastOutPos,FVector PrevComposeHero,double AppliedLookYaw,double LookPitchDelta){", tunings,
        "const double K=Dt*60.0,Boost=1.0,FlipK=0.0,VisBoostK=0.0,EdgeK=0.0;", lm, mp, my, "return {Lm,MP,MY};}"))
    runner = r'''
int main(){try{
  int samples=0;
  for(int hz:{30,60,120}) for(double delta:{6.21/hz,.45,.9}) {
    const double Dt=1.0/hz;
    FWebTravCamera camera;
    FVector CamXY(-ChaseDist,.3,0),CamXYV,Hero,LastHero,LastVelocity;
    double PreviousOrbit=std::atan2(CamXY.Y,CamXY.X),OutputYaw=0;
    for(int frame=0;frame<hz*4;frame++){
      const double direction=frame<hz?1:frame<2*hz?0:frame<3*hz?-1:0;
      camera.ApplyLook(FVector2D(delta*direction,0));
      double LookYawDelta=camera.LookYawDelta,Yaw=camera.Yaw,YawBeforeGroundStop=Yaw,AppliedLookYaw=0;
      ACCEPTED_YAW
      if(std::abs(AppliedLookYaw)>1e-9)TransportManualOrbit(CamXY,CamXYV,LastHero,Hero,LastVelocity,FVector(),AppliedLookYaw);
      const FVector PreviousOutput=FVector(-ChaseDist*std::cos(OutputYaw)-.3*std::sin(OutputYaw),-ChaseDist*std::sin(OutputYaw)+.3*std::cos(OutputYaw),0);
      const FVector Desired(-ChaseDist*std::cos(Yaw)-.3*std::sin(Yaw),-ChaseDist*std::sin(Yaw)+.3*std::cos(Yaw),0);
      const FVector BackR(-std::cos(Yaw),-std::sin(Yaw),0);
      const double ChaseKNow=1.0,AirClose=0.0,KickK=0.0;
      CHASE_SPRING
      const double Orbit=std::atan2(CamXY.Y,CamXY.X),Step=WrapA(Orbit-PreviousOrbit);
      Require(direction==0?std::abs(Step)<1e-8:Step*direction>0,"manual orbit reverses or drifts after release");
      Require(std::abs(WrapA(Step-delta*direction))<1e-8,"orbit fails to track accepted yaw, including wrap");
      Budget b=MakeBudget(Dt,PreviousOutput,LastHero,AppliedLookYaw,camera.LookPitchDelta);
      const double Want=FMath::RadiansToDegrees(WrapA(Yaw-OutputYaw));
      const double Actual=std::clamp(Want,-b.yaw,b.yaw);
      OutputYaw+=Actual*3.14159265358979323846/180;
      Require(std::abs(WrapA(OutputYaw-Yaw))<1e-8,"aim lags deliberately transported orbit");
      Require((CamXY-PreviousOutput).Size()<=b.pos+1e-8,"position cap lags deliberately transported orbit");
      if(direction==0)Require(std::abs(b.yaw-2.0*Dt*60)<1e-9,"manual budget persists after release");
      PreviousOrbit=Orbit;LastHero=Hero;camera.LookYawDelta=camera.LookPitchDelta=camera.AppliedLookYaw=0;
      ++samples;
    }
  }
  // Closed-loop framing at its smallest radius must not activate the emergency vertical crane in empty air.
  for(double ChaseKNow:{.62,.7,1.0}) for(double AirClose:{0.0,.3,.8}) {
    const double KickK=0,Dt=1.0/60;
    const FVector Hero,BackR(-1,0,0),Desired(-ChaseDist*ChaseKNow+AirClose,.3,0);
    FVector CamXY=Desired,CamXYV;
    for(int frame=0;frame<120;frame++) {
      CHASE_SPRING
      Require((CamXY-Hero).Size()>=MinHeroDist+.0499,"framing radius triggers false emergency crane");
    }
  }
  // Translation velocity stays in world space; only spring velocity relative to the hero rotates.
  FVector at(6,2,0),velocity(12,1,0);
  TransportManualOrbit(at,velocity,FVector(10,2,0),FVector(11,4,0),FVector(10,0,0),FVector(20,3,0),1.57079632679489661923);
  Require((at-FVector(11,0,0)).Size()<1e-9,"moving pivot transport is incorrect");
  Require((velocity-FVector(19,5,0)).Size()<1e-9,"world translation velocity was rotated");
  // A ground stop rejects the entire attempted yaw. There must be no state transport or extra budget.
  {double LookYawDelta=.9,Yaw=0,YawBeforeGroundStop=.9,AppliedLookYaw=0;
   ACCEPTED_YAW
   Require(std::abs(AppliedLookYaw)<1e-12,"blocked ground input survives yaw stop");
   Budget b=MakeBudget(1.0/60,FVector(-3.8,.3,0),FVector(),AppliedLookYaw,0);
   Require(std::abs(b.pos-1.1)<1e-12 && std::abs(b.yaw-2.0)<1e-12,"blocked turn enlarges output budget");}
  // Pitch allowance follows accepted user pitch, then disappears at the user-pitch clamp and on release.
  {FWebTravCamera c;c.ApplyLook(FVector2D(0,.9));Require(std::abs(c.LookPitchDelta-.6)<1e-12,"pitch allowance ignores accepted clamp");
   c.LookYawDelta=c.LookPitchDelta=0;c.ApplyLook(FVector2D(0,.9));Require(std::abs(c.LookPitchDelta)<1e-12,"clamped pitch keeps granting budget");}
  std::cout<<"OK "<<samples<<" orbit samples: 30/60/120 Hz, max-stick equivalent, extreme mouse, stops, reversals, wrap, moving pivot, ground stop, pitch clamp, minimum distance\n";
  return 0;
}catch(const std::exception& error){std::cerr<<"FAIL "<<error.what()<<"\n";return 1;}}
'''
    runner = runner.replace("ACCEPTED_YAW", accepted).replace("CHASE_SPRING", spring)
    with tempfile.TemporaryDirectory(prefix="wh-manual-camera-math-") as tmp:
        cpp = Path(tmp) / "check.cpp"
        exe = Path(tmp) / "check"
        cpp.write_text(prefix + "\n" + functions + "\n" + tunings + "\n" + budget + "\n" + runner)
        subprocess.run([args.compiler, "-std=c++17", "-O2", str(cpp), "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)


if __name__ == "__main__":
    main()
