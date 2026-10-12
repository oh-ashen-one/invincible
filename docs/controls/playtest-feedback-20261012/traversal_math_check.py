#!/usr/bin/env python3
"""Check extracted production boost math; this does not run Unreal or establish visual/control acceptance."""
from pathlib import Path
import json
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'unreal/WebHomage/Source/WebHomage/Traversal/WebTraversalComponent.cpp'


def extract_function(text, signature):
    start = text.index(signature)
    brace = text.index('{', start)
    depth = 0
    for i in range(brace, len(text)):
        depth += (text[i] == '{') - (text[i] == '}')
        if depth == 0:
            return text[start:i + 1]
    raise RuntimeError('Unclosed production function: ' + signature)


MATH_STUB = r'''
#include <algorithm>
#include <cmath>
#include <iostream>
#include <stdexcept>
struct FVector {
    double X, Y, Z;
    FVector(double x=0,double y=0,double z=0):X(x),Y(y),Z(z) {}
    FVector operator+(const FVector& b) const { return {X+b.X,Y+b.Y,Z+b.Z}; }
    FVector operator-(const FVector& b) const { return {X-b.X,Y-b.Y,Z-b.Z}; }
    FVector operator*(double k) const { return {X*k,Y*k,Z*k}; }
    double SizeSquared() const { return X*X+Y*Y+Z*Z; }
    double Size() const { return std::sqrt(SizeSquared()); }
    FVector GetSafeNormal() const { double n=Size(); return n>1e-8 ? *this*(1/n) : FVector(); }
    bool IsNearlyZero() const { return SizeSquared()<1e-8; }
    static double DotProduct(const FVector& a,const FVector& b) { return a.X*b.X+a.Y*b.Y+a.Z*b.Z; }
};
namespace FMath {
    template<class T> T Clamp(T x,T a,T b) { return std::clamp(x,a,b); }
    template<class T> T Min(T a,T b) { return std::min(a,b); }
    template<class T> T Max(T a,T b) { return std::max(a,b); }
    double Sqrt(double x) { return std::sqrt(x); }
    double Cos(double x) { return std::cos(x); }
    double Sin(double x) { return std::sin(x); }
    double Atan2(double y,double x) { return std::atan2(y,x); }
    double DegreesToRadians(double x) { return x*std::acos(-1.0)/180; }
}
const FVector ZUP(0,0,1);
void require(bool ok,const char* msg) { if (!ok) throw std::runtime_error(msg); }
'''

CHECKS = r'''
int main() {
    int directions=0, impulses=0;
    constexpr double eps=1e-7;
    for (int yaw=-180;yaw<=180;yaw+=15) {
        for (double pitch : {-89.,-70.,-45.,-20.,0.,20.,45.,70.,89.}) {
            const double y=FMath::DegreesToRadians(double(yaw)), p=FMath::DegreesToRadians(pitch);
            const FVector view(std::cos(y)*std::cos(p),std::sin(y)*std::cos(p),std::sin(p));
            const FVector d=ForwardBoostDirection(view,y);
            require(std::abs(d.Size()-1)<eps,"boost direction is not unit length");
            require(std::abs(d.Z)<=std::sqrt(.5)+eps,"boost exceeded 45-degree vertical limit");
            require(FVector::DotProduct(Flat(d).GetSafeNormal(),YawDir(y))>1-eps,"boost changed visible camera heading");
            require(std::abs(std::atan2(d.Z,HLen(d))-FMath::DegreesToRadians(std::clamp(pitch,-45.,45.)))<eps,"vertical look direction lost");
            ++directions;
            for (double x : {-60.,-45.,-12.,0.,12.,45.,60.})
            for (double yv : {-24.,0.,24.})
            for (double z : {-56.,-12.,0.,12.,56.})
            for (double strength : {0.,6.,12.}) {
                const FVector v(x,yv,z), out=ForwardBoostVelocity(v,d,strength,45.), delta=out-v;
                const double added=FVector::DotProduct(delta,d);
                require(added>=-eps && added<=strength+eps,"added impulse exceeds budget or points backward");
                require((delta-d*added).Size()<eps,"boost removed perpendicular carried momentum");
                require(out.Size()<=std::max(45.,v.Size())+eps,"boost exceeded speed budget");
                require(std::isfinite(out.X)&&std::isfinite(out.Y)&&std::isfinite(out.Z),"nonfinite boost output");
                ++impulses;
            }
        }
    }
    const FVector d(1,0,0);
    require((ForwardBoostVelocity(FVector(25,0,0),d,12,45)-FVector(37,0,0)).Size()<eps,"straight boost did not add 12m/s immediately");
    require((ForwardBoostVelocity(FVector(0,25,-12),d,12,45)-FVector(12,25,-12)).Size()<eps,"sideways/falling momentum was destroyed");
    require((ForwardBoostVelocity(FVector(60,0,0),d,12,45)-FVector(60,0,0)).Size()<eps,"fast carried velocity was capped downward");
    const FVector vertical=ForwardBoostDirection(FVector(0,0,1),FMath::DegreesToRadians(90.));
    require(vertical.Y>0.7 && vertical.Z>0.7,"vertical camera fallback did not preserve view yaw");
    std::cout << "{\"camera_direction_cases\":" << directions << ",\"impulse_cases\":" << impulses
        << ",\"passed\":true,\"evidence\":\"production-extracted math only; Unreal runtime and owner feel remain separate\"}\n";
}
'''


def main():
    source = SOURCE.read_text()
    signatures = [
        'FVector YawDir(double A)', 'double HLen(const FVector& V)', 'FVector Flat(const FVector& V)',
        'FVector ForwardBoostDirection(const FVector& ViewForward, double FallbackYaw)',
        'FVector ForwardBoostVelocity(const FVector& Velocity, const FVector& Direction, double DeltaSpeed, double SpeedLimit)',
    ]
    production = '\n'.join(extract_function(source, signature) for signature in signatures)
    with tempfile.TemporaryDirectory(prefix='wh-traversal-math-') as tmp:
        cpp, exe = Path(tmp) / 'check.cpp', Path(tmp) / 'check'
        cpp.write_text(MATH_STUB + production + CHECKS)
        subprocess.run(['xcrun', 'clang++', '-std=c++17', '-O2', str(cpp), '-o', str(exe)], check=True)
        result = subprocess.run([str(exe)], check=True, capture_output=True, text=True)
    print(json.dumps(json.loads(result.stdout), indent=2))


if __name__ == '__main__':
    main()
