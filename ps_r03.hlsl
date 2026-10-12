
#define NZG(uv, s) Texture2DSampleGrad(tN, tNSampler, (uv), dpx * (s), dpy * (s))
float2 p = Lag.xy; float t = T;
float3 wp = WPos * 0.01, cm = Cam * 0.01;
float3 Vv = cm - wp; float dist = length(Vv); float3 V = Vv / max(dist, 1e-3);
float2 dpx = ddx(p), dpy = ddy(p);
float foot = max(length(abs(dpx) + abs(dpy)), 1e-4);
// r03: near field (<= 150 m): two realizations per layer, the resolved wind chop, foam, contact map; beyond: one realization
float nearW = 1.0 - smoothstep(150.0 * 0.73, 150.0, dist);
float wbR = 0.70711 * nearW, waR = sqrt(1.0 - wbR * wbR);
// ---- wind gusts (broad, wind-aligned patches of rougher water). r03: wind-streak and slick terms deleted (pale comet streaks)
float2 wdir = float2(0.642788, -0.766044);
float4 nA = NZG(p / 620.0, 1.0 / 620.0), nB = NZG(p / 230.0 + float2(t * 0.0009, 0.37), 1.0 / 230.0);
float gust = saturate((nA.r * 0.62 + nB.g * 0.38 - 0.5) * 2.4 + 0.5);
float2 su = (p - float2(-6400.0, -8000.0)) / float2(12800.0, 17600.0);
float shore = (all(su > 0.0) && all(su < 1.0)) ? Texture2DSampleGrad(tS, tSSampler, su, dpx / float2(12800.0, 17600.0), dpy / float2(12800.0, 17600.0)).r * 400.0 : 400.0;
float gk = lerp(0.75, 1.25, gust);
// ---- the long Gerstner waves (waves.js waveSlope: resolved -> slope, unresolved -> slope variance)
float2 sl2 = 0; float varU = 0, h = 0, s, c, f;
sincos(0.202683 * dot(float2(0.788011, -0.615661), p) - 1.410079 * t + 0.0000, s, c); f = 1.0 - smoothstep(0.12, 0.35, foot * 0.064516); sl2 += float2(0.788011, -0.615661) * (0.012161 * c / max(1.0 - 0.016667 * s, 0.35)) * f; varU += 0.00007395 * (1.0 - f); h += 0.060000 * s;
sincos(0.380799 * dot(float2(0.469472, -0.882948), p) - 1.932780 * t + 5.1000, s, c); f = 1.0 - smoothstep(0.12, 0.35, foot * 0.121212); sl2 += float2(0.469472, -0.882948) * (0.020944 * c / max(1.0 - 0.029167 * s, 0.35)) * f; varU += 0.00021932 * (1.0 - f); h += 0.055000 * s;
sincos(0.560999 * dot(float2(0.913545, -0.406737), p) - 2.345932 * t + 1.7000, s, c); f = 1.0 - smoothstep(0.12, 0.35, foot * 0.178571); sl2 += float2(0.913545, -0.406737) * (0.036465 * c / max(1.0 - 0.037500 * s, 0.35)) * f; varU += 0.00066485 * (1.0 - f); h += 0.065000 * s;
sincos(0.795340 * dot(float2(0.121869, -0.992546), p) - 2.793257 * t + 4.1000, s, c); f = 1.0 - smoothstep(0.12, 0.35, foot * 0.253165); sl2 += float2(0.121869, -0.992546) * (0.039767 * c / max(1.0 - 0.041667 * s, 0.35)) * f; varU += 0.00079071 * (1.0 - f); h += 0.050000 * s;
sincos(1.121997 * dot(float2(0.681998, -0.731354), p) - 3.317649 * t + 2.3000, s, c); f = 1.0 - smoothstep(0.12, 0.35, foot * 0.357143); sl2 += float2(0.681998, -0.731354) * (0.047124 * c / max(1.0 - 0.045833 * s, 0.35)) * f; varU += 0.00111033 * (1.0 - f); h += 0.042000 * s;
float crest = h / 0.19160;
sl2 *= lerp(0.85, 1.1, gust); varU *= 1.2;
// ---- wind-sea spectrum layers (baked random-phase slopes, true texture gradients: what the mips drop is counted in varL)
float2 slT = 0; float varL = 0;
{ float2 qa = float2(dot(p, float2(0.743145, -0.669131)), dot(p, float2(0.669131, 0.743145))) / 21.0000 - float2(0.093527 * t, 0.0);
  float2 ga = (Texture2DSampleGrad(tW, tWSampler, qa, float2(dot(dpx, float2(0.743145, -0.669131)), dot(dpx, float2(0.669131, 0.743145))) / 21.0000, float2(dot(dpy, float2(0.743145, -0.669131)), dot(dpy, float2(0.669131, 0.743145))) / 21.0000).rg - 0.5) * 6.00;
  ga = float2(ga.x * 0.743145 - ga.y * -0.669131, ga.x * -0.669131 + ga.y * 0.743145);
  float2 g = ga * waR;
  [branch] if (nearW > 0.0) {
    float2 qb = float2(dot(p, float2(-0.121869, -0.992546)), dot(p, float2(0.992546, -0.121869))) / 18.2700 - float2(0.115027 * t, 0.0) + float2(0.37, 0.610);
    float2 gb = (Texture2DSampleGrad(tW, tWSampler, qb, float2(dot(dpx, float2(-0.121869, -0.992546)), dot(dpx, float2(0.992546, -0.121869))) / 18.2700, float2(dot(dpy, float2(-0.121869, -0.992546)), dot(dpy, float2(0.992546, -0.121869))) / 18.2700).ba - 0.5) * 6.00;
    g += float2(gb.x * -0.121869 - gb.y * -0.992546, gb.x * -0.992546 + gb.y * -0.121869) * wbR; }
  slT += g * 0.04000; varL += 0.0016000 * saturate(log2(2.0 * foot / 0.76125) / 3.0); }
{ float2 qa = float2(dot(p, float2(0.358368, -0.933580)), dot(p, float2(0.933580, 0.358368))) / 6.7000 - float2(0.165615 * t, 0.0);
  float2 ga = (Texture2DSampleGrad(tW, tWSampler, qa, float2(dot(dpx, float2(0.358368, -0.933580)), dot(dpx, float2(0.933580, 0.358368))) / 6.7000, float2(dot(dpy, float2(0.358368, -0.933580)), dot(dpy, float2(0.933580, 0.358368))) / 6.7000).rg - 0.5) * 6.00;
  ga = float2(ga.x * 0.358368 - ga.y * -0.933580, ga.x * -0.933580 + ga.y * 0.358368);
  float2 g = ga * waR;
  [branch] if (nearW > 0.0) {
    float2 qb = float2(dot(p, float2(0.978148, -0.207912)), dot(p, float2(0.207912, 0.978148))) / 5.8290 - float2(0.203688 * t, 0.0) + float2(0.37, 1.220);
    float2 gb = (Texture2DSampleGrad(tW, tWSampler, qb, float2(dot(dpx, float2(0.978148, -0.207912)), dot(dpx, float2(0.207912, 0.978148))) / 5.8290, float2(dot(dpy, float2(0.978148, -0.207912)), dot(dpy, float2(0.207912, 0.978148))) / 5.8290).ba - 0.5) * 6.00;
    g += float2(gb.x * 0.978148 - gb.y * -0.207912, gb.x * -0.207912 + gb.y * 0.978148) * wbR; }
  slT += g * 0.04500; varL += 0.0020250 * saturate(log2(2.0 * foot / 0.24287) / 3.0); }
{ float2 qa = float2(dot(p, float2(0.920505, -0.390731)), dot(p, float2(0.390731, 0.920505))) / 2.2000 - float2(0.289582 * t, 0.0);
  float2 ga = (Texture2DSampleGrad(tW, tWSampler, qa, float2(dot(dpx, float2(0.920505, -0.390731)), dot(dpx, float2(0.390731, 0.920505))) / 2.2000, float2(dot(dpy, float2(0.920505, -0.390731)), dot(dpy, float2(0.390731, 0.920505))) / 2.2000).rg - 0.5) * 6.00;
  ga = float2(ga.x * 0.920505 - ga.y * -0.390731, ga.x * -0.390731 + ga.y * 0.920505);
  float2 g = ga * waR;
  [branch] if (nearW > 0.0) {
    float2 qb = float2(dot(p, float2(0.121869, -0.992546)), dot(p, float2(0.992546, 0.121869))) / 1.9140 - float2(0.356152 * t, 0.0) + float2(0.37, 1.830);
    float2 gb = (Texture2DSampleGrad(tW, tWSampler, qb, float2(dot(dpx, float2(0.121869, -0.992546)), dot(dpx, float2(0.992546, 0.121869))) / 1.9140, float2(dot(dpy, float2(0.121869, -0.992546)), dot(dpy, float2(0.992546, 0.121869))) / 1.9140).ba - 0.5) * 6.00;
    g += float2(gb.x * 0.121869 - gb.y * -0.992546, gb.x * -0.992546 + gb.y * 0.121869) * wbR; }
  slT += g * 0.05000; varL += 0.0025000 * saturate(log2(2.0 * foot / 0.07975) / 3.0); }
// ---- r03 resolved wind chop 0.15-0.5 m: two realizations, two scroll directions (near field only; beyond, all of it is sub-pixel variance)
float2 slC = 0; float lostC = 1.0;
[branch] if (nearW > 0.0) {
    lostC = 0.0;
    { float2 q = float2(dot(p, float2(0.927184, -0.374607)), dot(p, float2(0.374607, 0.927184))) / 1.5000 - float2(0.435884 * t, 0.290);
    float2 g = (Texture2DSampleGrad(tK, tKSampler, q, float2(dot(dpx, float2(0.927184, -0.374607)), dot(dpx, float2(0.374607, 0.927184))) / 1.5000, float2(dot(dpy, float2(0.927184, -0.374607)), dot(dpy, float2(0.374607, 0.927184))) / 1.5000).rg - 0.5) * 6.00;
    slC += float2(g.x * 0.927184 - g.y * -0.374607, g.x * -0.374607 + g.y * 0.927184); lostC += 0.5 * saturate(log2(2.0 * foot / 0.15000) / 1.74); }
    { float2 q = float2(dot(p, float2(0.069756, -0.997564)), dot(p, float2(0.997564, 0.069756))) / 1.1700 - float2(0.558406 * t, 0.580);
    float2 g = (Texture2DSampleGrad(tK, tKSampler, q, float2(dot(dpx, float2(0.069756, -0.997564)), dot(dpx, float2(0.997564, 0.069756))) / 1.1700, float2(dot(dpy, float2(0.069756, -0.997564)), dot(dpy, float2(0.997564, 0.069756))) / 1.1700).ba - 0.5) * 6.00;
    slC += float2(g.x * 0.069756 - g.y * -0.997564, g.x * -0.997564 + g.y * 0.069756); lostC += 0.5 * saturate(log2(2.0 * foot / 0.11700) / 1.74); }
    slC *= nearW * 0.70711;
    lostC = lerp(1.0, lostC, nearW);
}
float ck = ChopK * gk, mk = ChopK * MicroK * gk * 0.0650;
slT *= ck; varL *= ck * ck;
float2 slope = sl2 + slT + slC * mk;
float varF = varL + lostC * mk * mk;      // per-axis slope variance the shading cannot resolve
// ---- foam (near field only, faded to zero by 150 m): contact (the water line against anything below it), rare whitecaps
float cf = 0.0, wf = 0.0;
[branch] if (nearW > 0.0) {
    float fn = NZG(p / 7.0 + float2(t * 0.01, -t * 0.007), 1.0 / 7.0).b;
    float lap = 0.55 + 0.225 * sin(dot(p, float2(0.11, -0.17)) + t * 1.1) + 0.35 * crest + 0.15 * (slT.x - slT.y);
    float dnw = max(DNW - PD, 0.0) * 0.01;
    float lr = dnw / max(dot(-V, View.ViewForward), 0.2);
    cf = 1.0 - smoothstep(0.04, 0.25 + 1.1 * fn + 0.6 * lap, lr);
    float2 cu = (p - float2(-1203.70, -3688.98)) / float2(2344.33, 7316.09);
    float cdm = (all(cu > 0.0) && all(cu < 1.0)) ? Texture2DSampleLevel(tC, tCSampler, cu, 0).r * 32.0 : 32.0;
    cf = max(cf, 1.0 - smoothstep(0.12, 0.45 + 1.5 * fn + 0.9 * lap, cdm));
    float foam = cf * (0.4 + 0.45 * lap) * smoothstep(0.25, 0.6, NZG(p / 3.1 + float2(-t * 0.02, t * 0.013), 1.0 / 3.1).r + 0.25 * lap) * FoamK;
    foam = max(foam, smoothstep(0.8, 1.0, crest) * smoothstep(0.55, 0.9, gust) * 0.2);
    float cov = saturate(foam);
    float pat = NZG(p / 1.9 + float2(t * 0.004, 0.0), 1.0 / 1.9).r * 0.62 + NZG(p / 0.63 + float2(0.0, t * 0.006), 1.0 / 0.63).g * 0.5;
    wf = saturate(smoothstep(1.05 - cov, 1.3 - cov, pat) * smoothstep(0.0, 0.25, cov)) * nearW;
}
// ---- normal / roughness. Near field: GGX alpha from RoughN only (<= 0.08: the resolved facets carry the slope variance);
//      beyond: + the unresolved variance x FarVarK (Cox-Munk alpha^2 = 2 sigma^2 per axis)
float3 N = normalize(float3(-slope.x, -slope.y, 1.0));
{ float3 Rr = reflect(-V, N); float wl = saturate((0.05 - Rr.z) * 8.0); N = normalize(lerp(N, float3(0, 0, 1), wl * BendK));
  Rr = reflect(-V, N); wl = saturate((0.03 - Rr.z) * 12.0); N = normalize(lerp(N, float3(0, 0, 1), wl * BendK)); }
float farW = smoothstep(150.0 * 0.4, 150.0, dist);
float r4 = RoughN * RoughN; r4 *= r4;
float a2 = r4 + 1.200 * FarVarK * farW * (varU + 2.0 * varF);
float rcap = lerp(0.08, 0.7, smoothstep(150.0, 150.0 * 2.7, dist));
Rough = lerp(clamp(pow(a2, 0.25), 0.03, rcap), 0.6, wf);
NormalW = normalize(lerp(N, float3(0, 0, 1), wf * 0.6));
Spec = 0.25 * SpecK;     // F0 = 0.02 (IOR 1.333) x SpecK
Opac = wf * 0.92;
// ---- turbid river optics (per cm): olive-grey Hudson body (ScatK), siltier / browner along the bulkheads
float silt = (1.0 - smoothstep(10.0, 120.0, shore)) * 0.75;
float turb = 0.85 + 0.3 * NZG(p / 900.0 + float2(0.0, t * 0.0015), 1.0 / 900.0).r;
float3 sS = float3(0.0700, 0.0900, 0.0780) * ScatK * turb * (1.0 + float3(0.9, 0.6, 0.3) * silt);
float3 sA = float3(0.5000, 0.3400, 0.5600) * (1.0 + float3(0.1, 0.2, 0.5) * silt);
Scat = sS * 0.01; Abs = sA * 0.01;
// ---- sun glitter: sparse facets that face the sun get their normal tilted onto the sun half-vector (beyond 25 m; the near field glints
//      off its own resolved facets with the sharp GGX lobe)
float3 Ls = normalize(SunDir);
float3 Hh = normalize(Ls + V);
float gw = 0.0;
[branch] if (dist < 900.0 && dist > 20.0 && Ls.z > 0.0) {
    float2 gn = (NZG(p / 2.3 + float2(t * 0.05, t * 0.034), 1.0 / 2.3).ga - 0.5) * 2.0 + 0.8 * (NZG(float2(-p.y, p.x) / 3.7 + float2(-t * 0.041, t * 0.02), 1.0 / 3.7).ga - 0.5) * 2.0;
    float3 nG = normalize(N + float3(gn * 0.22, 0.0));
    float gl = pow(saturate(dot(nG, Hh)), 700.0);
    float spark = smoothstep(0.62, 0.9, NZG(p / 5.0 + float2(t * 0.02, 0.0), 1.0 / 5.0).r);
    gw = saturate(gl * spark * (1.0 - smoothstep(600.0, 900.0, dist)) * smoothstep(20.0, 40.0, dist) * (1.0 - wf) * saturate(Ls.z * 8.0) * 3.0 * GlitterK);
}
NormalW = normalize(lerp(NormalW, Hh, gw));
Rough = lerp(Rough, 0.06, gw);
Emis = 0;
if (Dbg > 0.5) { float3 dv = Dbg < 1.5 ? float3(frac(p / 10.0), 0.0) : (Dbg < 2.5 ? N * 0.5 + 0.5 : (Dbg < 3.5 ? Rough.xxx : (Dbg < 4.5 ? float3(wf, cf, gust) : Lag.zzz))); Emis = 0; Opac = 1.0; return dv; }
return float3(0.62, 0.6, 0.55);   // r03: cream foam albedo (r02 0.74 clipped at the seawall in the golden key)
#undef NZG
