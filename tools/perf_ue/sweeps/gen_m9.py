from gen_m5 import M, dump
def X(sun=11000, ang=2.5, extra=(), **k):
    d = dict(sky=1.5, sl=2.3, aps=4.0, fogamb=3.5, offs=0.008, lo=10, hi=90, bias=-0.7); d.update(k)
    return M(**d) + ["post FilmWhiteClip 0", "set Sun - Intensity %g" % sun, "set Sun - LightSourceAngle %g" % ang] + list(extra)
dump('v_m9', {
    'q1': X(15000),
    'q2': X(20000),
    'q3': X(26000),
    'q4': X(20000, bias=-0.8),
    'q5': X(20000, sl=1.8),
    'q6': X(26000, sl=1.8, bias=-0.9),
    'q7': X(20000, extra=["post ColorGainHighlights (X=0.92,Y=0.92,Z=0.92,W=1)"]),
    'q8': X(20000, ang=6),
    'q9': X(30000, sl=1.5, bias=-1.0, ang=4)})
