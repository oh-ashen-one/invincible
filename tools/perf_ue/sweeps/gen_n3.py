from gen_n1 import N, dump
def Z(shop=2000, extra=(), **k):
    d = dict(bias=-0.5, moon=22, sky=3.0, fog=0.006, lamp=2.0, offs=(0.008, 0.01, 0.016)); d.update(k)
    return N(["set LampHalo_* PointLight Intensity 120", "set CarHead_* SpotLight Intensity 2000", "set Shop_* SpotLight Intensity %g" % shop] + list(extra), **d)
CONE = ["set LampSpot_* SpotLight OuterConeAngle 60", "set LampSpot_* SpotLight InnerConeAngle 25"]
dump('v_n3', {
    's1': Z(),
    's2': Z(4000),
    's3': Z(6000, ["set CarHead_* SpotLight Intensity 3000"]),
    's4': Z(2000, CONE),
    's5': Z(4000, CONE),
    's6': Z(4000, CONE, contrast=1.5),
    's7': Z(4000, CONE + ["post IndirectLightingIntensity 2.4"]),
    's8': Z(4000, CONE, lamp=2.6, bias=-0.7)})
