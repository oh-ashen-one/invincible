from gen_m5 import M, dump
def X(**k):
    d = dict(sky=1.5, sl=2.3, aps=4.0, fogamb=3.5, offs=0.008); d.update(k)
    return M(**d) + ["post FilmWhiteClip 0", "set Sun - Intensity 11000"]
dump('v_m8', {
    'p1': X(lo=10, hi=90, bias=-1.0),
    'p2': X(lo=10, hi=90, bias=-0.7),
    'p3': X(lo=10, hi=90, bias=-0.4),
    'p4': X(lo=20, hi=95, bias=-0.6),
    'p5': X(lo=20, hi=95, bias=-0.3),
    'p6': X(lo=40, hi=98, bias=0.0),
    'p7': X(lo=40, hi=98, bias=0.3),
    'p8': X(lo=55, hi=98, bias=0.45)})
