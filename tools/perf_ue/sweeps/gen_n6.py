import json
def dump(name, variants): json.dump({'variants': variants}, open('/Users/midir/sm2-n1/_scratch/look/eval/%s.json' % name, 'w'), indent=1)
def Q(wt=6300, moon=14, sky=2.3, bias=-0.25, fillk=0.65):
    return ["post WhiteTemp %g" % wt, "set Moon - Intensity %g" % moon, "set SkyLight - Intensity %g" % sky, "post AutoExposureBias %g" % bias,
            "set CityGlowWest - Intensity %g" % (4.0 * fillk), "set CityGlowNorth - Intensity %g" % (0.9 * fillk), "set CityGlowSouth - Intensity %g" % (0.9 * fillk), "set CityGlowEast - Intensity %g" % (0.6 * fillk)]
dump('v_n6', {
    'y0': Q(),
    'y1_moon17': Q(moon=17, sky=2.6),
    'y2_moon17_wt61': Q(moon=17, sky=2.6, wt=6100),
    'y3_bias15_wt61': Q(bias=-0.15, wt=6100),
    'y4_fills1': Q(moon=16, sky=2.5, wt=6100, fillk=1.0),
    'y5_moon20': Q(moon=20, sky=2.8, wt=6000, bias=-0.3)})
