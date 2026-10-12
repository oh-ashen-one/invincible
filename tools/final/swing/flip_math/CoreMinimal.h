// Minimal adapters for the standalone pure-algorithm test; no engine/runtime emulation.
// FRandomStream fraction matches the installed UE 5.8 RandomStream.h (Seed >> 9).
#pragma once
#include <cmath>
#include <algorithm>
#include <vector>
#include <map>
#include <string>
#include <cstdint>
#include <cstring>
using int32=int32_t;using uint32=uint32_t;using uint8=uint8_t;using TCHAR=char;
#define TEXT(x) x
#define UE_ARRAY_COUNT(x) (sizeof(x)/sizeof(x[0]))
constexpr float PI=3.14159265358979323846f;
struct FName { std::string v; FName(){} FName(const char*x):v(x){} bool operator==(const FName&x)const{return v==x.v;} bool operator!=(const FName&x)const{return v!=x.v;} };
const FName NAME_None;
template<class T>struct TArray:std::vector<T>{ using std::vector<T>::vector; TArray()=default; TArray(std::initializer_list<T> x):std::vector<T>(x){} TArray& operator=(std::initializer_list<T>x){std::vector<T>::operator=(x);return *this;} int32 Num()const{return this->size();} void Add(const T&x){this->push_back(x);} T& Last(){return this->back();} const T& Last()const{return this->back();} void SetNum(int32 n){this->resize(n);} void SetNumZeroed(int32 n){this->resize(n);} };
template<class K,class V>struct TMap:std::map<K,V>{V* Find(const K&k){auto i=this->find(k);return i==this->end()?nullptr:&i->second;} V& Add(const K&k,const V&v){return (*this)[k]=v;} };
struct FMath { static double DegreesToRadians(double x){return x*3.14159265358979323846/180.;}  template<class T>static T Clamp(T x,T a,T b){return std::clamp(x,a,b);} template<class T>static T Max(T a,T b){return std::max(a,b);} template<class T>static T Min(T a,T b){return std::min(a,b);} template<class T,class U>static auto Lerp(T a,T b,U w){return a+(b-a)*w;} static float Abs(float x){return std::abs(x);} static float Sqrt(float x){return std::sqrt(x);} static int32 FloorToInt(float x){return std::floor(x);} static int32 CeilToInt(float x){return std::ceil(x);} static float Cos(float x){return std::cos(x);} static float Fmod(float x,float y){return std::fmod(x,y);} };
struct FRandomStream{uint32 seed; explicit FRandomStream(int32 x):seed(x){} float FRand(){seed=seed*196314165U+907633515U;uint32 u=0x3F800000U|(seed >> 9);float f;std::memcpy(&f,&u,4);return f-1.f;} };
struct FParse{static bool Value(const char*,const char*,int32&){return false;} };struct FCommandLine{static const char*Get(){return "";} };

struct FVector {double X=0,Y=0,Z=0; FVector()=default;FVector(double x,double y,double z):X(x),Y(y),Z(z){} FVector operator+(const FVector&v)const{return {X+v.X,Y+v.Y,Z+v.Z};} FVector operator-(const FVector&v)const{return {X-v.X,Y-v.Y,Z-v.Z};} FVector operator*(double f)const{return {X*f,Y*f,Z*f};} double Size()const{return std::sqrt(X*X+Y*Y+Z*Z);} FVector Unit()const{double n=Size();return {X/n,Y/n,Z/n};} static double Dot(const FVector&a,const FVector&b){return a.X*b.X+a.Y*b.Y+a.Z*b.Z;} static FVector Cross(const FVector&a,const FVector&b){return {a.Y*b.Z-a.Z*b.Y,a.Z*b.X-a.X*b.Z,a.X*b.Y-a.Y*b.X};}};
struct FQuat {double X=0,Y=0,Z=0,W=1;FQuat()=default;FQuat(double x,double y,double z,double w):X(x),Y(y),Z(z),W(w){} FQuat(FVector a,double r){double f=std::sin(r*.5);X=a.X*f;Y=a.Y*f;Z=a.Z*f;W=std::cos(r*.5);} static const FQuat Identity; FQuat GetNormalized()const{return Norm();} FQuat Norm()const{double n=std::sqrt(X*X+Y*Y+Z*Z+W*W);return {X/n,Y/n,Z/n,W/n};} FQuat operator*(const FQuat&q)const{return {W*q.X+X*q.W+Y*q.Z-Z*q.Y,W*q.Y-X*q.Z+Y*q.W+Z*q.X,W*q.Z+X*q.Y-Y*q.X+Z*q.W,W*q.W-X*q.X-Y*q.Y-Z*q.Z};} FVector RotateVector(FVector v)const{FQuat p=*this*FQuat(v.X,v.Y,v.Z,0)*FQuat(-X,-Y,-Z,W);return {p.X,p.Y,p.Z};} static FQuat FindBetweenNormals(FVector a,FVector b){FVector c=FVector::Cross(a,b);return FQuat(c.X,c.Y,c.Z,1+FVector::Dot(a,b)).Norm();} static FQuat Slerp(FQuat a,FQuat b,double f){double d=a.X*b.X+a.Y*b.Y+a.Z*b.Z+a.W*b.W;if(d<0){b={-b.X,-b.Y,-b.Z,-b.W};d=-d;} double p=1-f,q=f;if(d<.9995){double t=std::acos(d),st=std::sin(t);p=std::sin((1-f)*t)/st;q=std::sin(f*t)/st;}return FQuat(a.X*p+b.X*q,a.Y*p+b.Y*q,a.Z*p+b.Z*q,a.W*p+b.W*q).Norm();}};
inline const FQuat FQuat::Identity={};
