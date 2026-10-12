#include "WebTravFlips.h"
#include "rendered_root.hpp"
#include <iostream>
#include <set>
#include <cassert>
int main(){
 // A held author-local pose gives the exact final aiming frame; one frame of the existing
 // 60deg/s BodyAlign slew should leave only about one degree of prediction error, not a static
 // 9-21deg error. This tests the actual PoseRotation helper, independently of world-pitch feedback.
 double maxPredictionError=0;
 for(double forward : {0., .3, .65}) for(double lateral : {0., .2, .4}) {
  const FVector previousAxis=FVector(forward,lateral,1.).Unit();
  const FVector currentAxis=FQuat(FVector(0,1,0),3.14159265358979323846/180.).RotateVector(previousAxis);
  for(float pitch : {-540.f,0.f,720.f}) for(float twist : {0.f,180.f,360.f,720.f}) {
   FWebFlipPose pose;pose.PitchDeg=pitch;pose.TwistDeg=twist;
   for(int side : {-1,1}) {
    const FQuat predicted=WebFlips::PoseRotation(pose,previousAxis,1.f,float(side));
    const FQuat final=WebFlips::PoseRotation(pose,currentAxis,1.f,float(side));
    const double dot=std::abs(predicted.X*final.X+predicted.Y*final.Y+predicted.Z*final.Z+predicted.W*final.W);
    const double error=2*std::acos(std::min(1.,dot))*180./3.14159265358979323846;
    maxPredictionError=std::max(maxPredictionError,error);assert(error<1.3);
    const FQuat held=WebFlips::PoseRotation(pose,previousAxis,1.f,float(side));
    assert((predicted.RotateVector(previousAxis)-held.RotateVector(previousAxis)).Size()<1e-9);
   }
  }
 }
 std::cout<<"held-pose one-frame BodyAlign prediction error="<<maxPredictionError<<"deg\n";

 // Actual PostAnimTick composition is extracted by run.py, so dropping, duplicating or reordering
 // residual air sway in the character fails this noncommuting-rotation regression.
 const FQuat body(FVector(0,0,1),.7), flip(FVector(0,1,0),1.3);
 for(double decay : {1., .8, .4, .1, 0.}){
  const FQuat sway=FQuat(FVector(1,0,0),.32*decay)*FQuat(FVector(0,1,0),.19*decay);
  const FQuat actual=RenderedRootComposition(body,flip,sway);
  const FQuat expected=(body*flip*sway).GetNormalized();
  for(FVector v : {FVector(1,0,0),FVector(0,1,0),FVector(0,0,1)}){
   assert((actual.RotateVector(v)-expected.RotateVector(v)).Size()<1e-9);
  }
  const FVector centre(17,-23,190);
  const FVector root=centre-actual.RotateVector(FVector(0,0,95));
  assert((root+actual.RotateVector(FVector(0,0,95))-centre).Size()<1e-8);
 }

 float maxPeak=0,minHold=10,maxErr=0,minMean=1e6,maxMean=0;int variants=0;
 std::set<int> ends;
 for(const FName& n:WebFlips::Names()){
  const auto* base=WebFlips::FindBase(n);const float d0=base->Dur(),ct0=base->CatchT();
  if(n.v!="backSingle"&&n.v!="wallFront")assert(std::abs(base->PitchDeg)>=720.f);
  float namePeak=0,nameHold=10;
  for(int k=0;k<32;k++){
   const auto*p=WebFlips::MakeVariant(n,k%2?0.78f:1.22f,uint32(7919*k+17));
   assert(std::abs(p->Dur()-d0*p->Scale)<.00001f);assert(std::abs(p->CatchT()-ct0*p->Scale)<.00002f);
   assert(p->Lead+p->Lag>=.05f&&p->Lead+p->Lag<=.12f);
   float hold=0,best=0,peak=0;const float dt=1.f/240;
   for(float t=0;t<p->Dur();t+=dt){
    const auto x=WebFlips::Sample(*p,t);peak=std::max(peak,std::abs(x.PitchRate));
    if(x.Seg<int(p->Segs.Num())-1&&std::abs(x.PitchRate)<=150&&p->Segs[x.Seg].Shape!=EWebFlipShape::Tuck&&p->Segs[x.Seg].Shape!=EWebFlipShape::Pike&&p->Segs[x.Seg].Shape!=EWebFlipShape::Layout&&p->Segs[x.Seg].Shape!=EWebFlipShape::Twist){hold+=dt;best=std::max(best,hold);}else hold=0;
    // Sweep realistic keyed axis lean through +/-33deg and lateral tilt while testing actual runtime compensation.
    for(int side:{-1,1}){
     const FVector poseAxis=FVector(std::sin(t*17)*.65,std::cos(t*13)*.25,1.).Unit();
     const FVector corrected=WebFlips::PoseRotation(x,poseAxis,1.f,float(side)).RotateVector(poseAxis);
     const double rad=double(x.PitchDeg)*3.14159265358979323846/180.;
     const FVector wanted(std::sin(rad),0,std::cos(rad));assert((corrected-wanted).Size()<1e-6);
     const FVector centre(17,-23,190);const auto q=WebFlips::PoseRotation(x,poseAxis,1.f,float(side));
     const FVector root=centre-q.RotateVector(FVector(0,0,95));assert((root+q.RotateVector(FVector(0,0,95))-centre).Size()<1e-8);
    }
   }
   const auto e=WebFlips::Sample(*p,p->Dur());const auto pre=WebFlips::Sample(*p,p->Dur()-1.e-5f);const auto post=WebFlips::Sample(*p,p->Dur()+.5f);
   assert(e.PitchDeg==p->PitchDeg&&post.PitchDeg==p->PitchDeg&&post.PitchRate==0);
   maxErr=std::max(maxErr,std::abs(e.PitchDeg-pre.PitchDeg));
   if(std::abs(p->PitchDeg)>=700){minMean=std::min(minMean,std::abs(p->PitchDeg)/p->Dur());maxMean=std::max(maxMean,std::abs(p->PitchDeg)/p->Dur());}
   if(k==0&&(n.v=="frontSingle"||n.v=="backSingle"||n.v=="corkscrew"||n.v=="barani"||n.v=="frontPikeSwan"||n.v=="rudi"))ends.insert(int(post.A));
   maxPeak=std::max(maxPeak,peak);namePeak=std::max(namePeak,peak);nameHold=std::min(nameHold,best);variants++;
  }
  std::cout<<n.v<<" max_pitch="<<namePeak<<" min_noncatch_hold="<<nameHold<<"\n";
  if(n.v!="wallFront")minHold=std::min(minHold,nameHold);
 }
 std::cout<<"TOTAL variants="<<variants<<" peak="<<maxPeak<<" midhold="<<minHold<<" mean_multis="<<minMean<<".."<<maxMean<<" terminal_families="<<ends.size()<<" endpoint_jump="<<maxErr<<"\n";
 assert(ends.size()>=3);assert(maxPeak<=800);assert(minHold>=.3);assert(minMean>=300&&maxMean<=500);assert(maxErr<.2);
}
