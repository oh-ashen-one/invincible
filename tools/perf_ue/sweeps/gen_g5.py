from gen_g3 import G, dump, col
CGH = lambda v: "post ColorGainHighlights (X=%g,Y=%g,Z=%g,W=1)" % (v, v, v)
def B(**k):
    d = dict(aniso=0.7, shoulder=0.2); d.update(k)
    return G(**d) + [CGH(0.8)]
dump('v_g5', {
    'x0': B(),
    'x1_slf8': B(slf=(0.8, 0.8, 0.8)),
    'x2_slf65': B(slf=(0.65, 0.65, 0.65)),
    'x3_slf65b': B(slf=(0.65, 0.7, 0.85)),
    'x4_slf65b_bias': B(slf=(0.65, 0.7, 0.85), bias=1.15),
    'x5_mie15': B(mie=0.015),
    'x6_sun36': B(sun=36000, ang=2.0),
    'x7_combo': B(slf=(0.65, 0.7, 0.85), mie=0.02, bias=1.05)})
