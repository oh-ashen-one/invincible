import json
def col(r, g, b, a=1): return "(R=%g,G=%g,B=%g,A=%g)" % (r, g, b, a)
def dump(name, variants): json.dump({'variants': variants}, open('/Users/midir/sm2-n1/_scratch/look/eval/%s.json' % name, 'w'), indent=1)
def N(extra=(), **k):
    d = dict(wt=6300, ray=(0.3, 0.4, 0.7), offs=(0.0064, 0.008, 0.0144), lamp=1.7, fog=0.0038, bias=-0.3, moon=14, sky=2.6, contrast=1.35)
    d.update(k)
    return ["post WhiteTemp %g" % d['wt'], "set SkyAtmosphere - RayleighScattering " + col(*d['ray']),
            "post ColorOffset (X=%g,Y=%g,Z=%g,W=0)" % d['offs'], "set LampSpot_* SpotLight Intensity %g" % (7000 * d['lamp']),
            "set HeightFog - FogDensity %g" % d['fog'], "post AutoExposureBias %g" % d['bias'], "set Moon - Intensity %g" % d['moon'], "set SkyLight - Intensity %g" % d['sky'],
            "post ColorContrast (X=%g,Y=%g,Z=%g,W=1)" % (d['contrast'], d['contrast'], d['contrast'])] + list(extra)
if __name__ == '__main__':
    dump('v_n1', {
        'a': N(),
        'b_bias': N(bias=-0.1),
        'c_fog': N(bias=-0.1, fog=0.006),
        'd_moon': N(bias=-0.1, fog=0.006, moon=22, sky=3.0),
        'e_lo50': N(["post AutoExposureLowPercent 50"], bias=-0.1),
        'f_lamp': N(bias=-0.3, lamp=2.4),
        'g_contrast': N(bias=-0.1, contrast=1.2),
        'h_wt6800': N(bias=-0.1, wt=6800)})
