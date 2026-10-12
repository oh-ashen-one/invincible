import json, sys
def col(r, g, b, a=1): return "(R=%g,G=%g,B=%g,A=%g)" % (r, g, b, a)
def M(**k):
    d = dict(ray_col=(0.5, 0.5, 0.5), ray=0.03, mie=0.15, mieg=0.6, sky=1.2, sl=2.0, fogamb=3.0, hfc=1.0, aps=3.0, bias=0.7, offs=0.004, fog_den=0.0032, lo=70, hi=98)
    d.update(k)
    return ["exec showflag.fog 1", "exec showflag.volumetricfog 1", "exec showflag.atmosphere 1", "set Clouds VolumetricCloud bHiddenInGame False",
            "set SkyAtmosphere - RayleighScattering " + col(*d['ray_col']),
            "set SkyAtmosphere - RayleighScatteringScale %g" % d['ray'], "set SkyAtmosphere - MieScatteringScale %g" % d['mie'], "set SkyAtmosphere - MieAnisotropy %g" % d['mieg'],
            "set SkyAtmosphere - SkyLuminanceFactor " + col(d['sky'], d['sky'], d['sky']),
            "set SkyAtmosphere - HeightFogContribution %g" % d['hfc'], "set SkyAtmosphere - AerialPespectiveViewDistanceScale %g" % d['aps'],
            "set SkyLight - Intensity %g" % d['sl'],
            "set HeightFog - SkyAtmosphereAmbientContributionColorScale " + col(d['fogamb'], d['fogamb'], d['fogamb']),
            "set HeightFog - FogDensity %g" % d['fog_den'],
            "post AutoExposureBias %g" % d['bias'],
            "post ColorOffset (X=%g,Y=%g,Z=%g,W=0)" % (d['offs'], d['offs'] * 1.05, d['offs'] * 1.15),
            "post AutoExposureLowPercent %g" % d['lo'], "post AutoExposureHighPercent %g" % d['hi']]
def dump(name, variants): json.dump({'variants': variants}, open('/Users/midir/sm2-n1/_scratch/look/eval/%s.json' % name, 'w'), indent=1)
if __name__ == '__main__':
    dump('v_m5', {
        'a': M(),
        'b': M(bias=0.9),
        'c': M(bias=0.9, sky=1.0),
        'd': M(bias=0.9, sky=0.9, offs=0.008),
        'e': M(bias=1.0, sky=0.8, offs=0.008),
        'f': M(bias=0.8, sky=1.0, offs=0.008)})
