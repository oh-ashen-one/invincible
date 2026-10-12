from gen_n1 import N, dump
from gen_n3 import Z, CONE
def V(moon, sky, fillk, bias, extra=()):
    f = ["set CityGlowWest - Intensity %g" % (4.0 * fillk), "set CityGlowNorth - Intensity %g" % (0.9 * fillk), "set CityGlowSouth - Intensity %g" % (0.9 * fillk), "set CityGlowEast - Intensity %g" % (0.6 * fillk)]
    return Z(4000, CONE + f + list(extra), fog=0.012, moon=moon, sky=sky, bias=bias)
dump('v_n5', {
    'u0': V(22, 3.0, 1.0, -0.5),
    'u1': V(12, 2.0, 1.0, -0.5),
    'u2': V(12, 2.0, 0.5, -0.5),
    'u3': V(12, 2.0, 0.5, -0.3),
    'u4': V(6, 1.2, 0.5, -0.3),
    'u5': V(6, 1.2, 0.5, -0.1),
    'u6': V(12, 1.5, 0.3, -0.2)})
