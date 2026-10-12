import json
def col(r, g, b, a=1): return "(R=%g,G=%g,B=%g,A=%g)" % (r, g, b, a)
def dump(name, variants): json.dump({'variants': variants}, open('/Users/midir/sm2-n1/_scratch/look/eval/%s.json' % name, 'w'), indent=1)
def G(**k):
    d = dict(wt=7800, mie_col=(1.0, 0.72, 0.45), mie=0.03, aps=5.0, fog_den=0.0052, fog_col=(0.26, 0.2, 0.2), dir_col=(0.3, 0.15, 0.06), bias=0.95, shoulder=0.3, sun=44000, wclip=0.0,
             lo=70, hi=98, slf=(1, 1, 1), aniso=0.82, ang=0.6)
    d.update(k)
    return ["set SkyAtmosphere - MieScattering " + col(*d['mie_col']), "set SkyAtmosphere - MieScatteringScale %g" % d['mie'], "set SkyAtmosphere - MieAnisotropy %g" % d['aniso'],
            "set SkyAtmosphere - AerialPespectiveViewDistanceScale %g" % d['aps'], "set SkyAtmosphere - SkyLuminanceFactor " + col(*d['slf']),
            "set HeightFog - FogDensity %g" % d['fog_den'], "set HeightFog - FogInscatteringLuminance " + col(*d['fog_col']),
            "set HeightFog - DirectionalInscatteringLuminance " + col(*d['dir_col']),
            "post WhiteTemp %g" % d['wt'], "post AutoExposureBias %g" % d['bias'], "post FilmShoulder %g" % d['shoulder'], "post FilmWhiteClip %g" % d['wclip'],
            "post AutoExposureLowPercent %g" % d['lo'], "post AutoExposureHighPercent %g" % d['hi'],
            "set Sun - Intensity %g" % d['sun'], "set Sun - LightSourceAngle %g" % d['ang']]
SLF = (0.9, 0.95, 1.1)
if __name__ == '__main__':
    dump('v_g3', {
        'v1': G(),
        'v2_aniso7': G(aniso=0.7),
        'v3_aniso6': G(aniso=0.6, mie=0.04),
        'v4_slf': G(slf=SLF),
        'v5_dir': G(aniso=0.7, dir_col=(0.15, 0.075, 0.03)),
        'v6_hi_slf': G(hi=99.5, slf=SLF),
        'v7_sun30': G(sun=30000, bias=1.05),
        'v8_combo': G(bias=0.85, hi=99.5, aniso=0.7, slf=SLF)})
