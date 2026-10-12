"""Minimal ctypes driver for UE's bundled DXC (ShaderConductor/Mac/libdxcompiler.dylib has no dxc executable): compile(source, args) -> (ok, messages)."""
import ctypes as C
import os

LIB = os.environ.get('SM2_DXC_LIB', '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/ShaderConductor/Mac/libdxcompiler.dylib')


class GUID(C.Structure):
    _fields_ = [('d1', C.c_uint32), ('d2', C.c_uint16), ('d3', C.c_uint16), ('d4', C.c_uint8 * 8)]


def guid(s):
    p = s.split('-')
    g = GUID(int(p[0], 16), int(p[1], 16), int(p[2], 16))
    t = bytes.fromhex(p[3] + p[4])
    for i in range(8):
        g.d4[i] = t[i]
    return g


CLSID_COMPILER = guid('73e22d93-e6ce-47f3-b5bf-f0664f39c1b0')
IID_COMPILER3 = guid('228b4687-5a6a-4730-900c-9702b2203f54')
IID_OPRESULT = guid('cedb484a-d4e9-445a-b991-ca21ca157dc2')


class DxcBuffer(C.Structure):
    _fields_ = [('Ptr', C.c_void_p), ('Size', C.c_size_t), ('Encoding', C.c_uint32)]


def _fn(obj, idx, restype, *argtypes):
    vtbl = C.cast(obj, C.POINTER(C.POINTER(C.c_void_p)))[0]
    return C.CFUNCTYPE(restype, C.c_void_p, *argtypes)(vtbl[idx])


class Dxc:
    def __init__(self):
        self.lib = C.CDLL(LIB)
        create = self.lib.DxcCreateInstance
        create.argtypes = [C.POINTER(GUID), C.POINTER(GUID), C.POINTER(C.c_void_p)]
        create.restype = C.c_int32
        self.comp = C.c_void_p()
        hr = create(C.byref(CLSID_COMPILER), C.byref(IID_COMPILER3), C.byref(self.comp))
        if hr != 0:
            raise RuntimeError('DxcCreateInstance failed: 0x%x' % (hr & 0xffffffff))

    def compile(self, source, args):
        src = source.encode('utf-8')
        buf = DxcBuffer(C.cast(C.c_char_p(src), C.c_void_p), len(src), 65001)
        wargs = (C.c_wchar_p * len(args))(*args)
        res = C.c_void_p()
        compile_ = _fn(self.comp, 3, C.c_int32, C.POINTER(DxcBuffer), C.POINTER(C.c_wchar_p), C.c_uint32, C.c_void_p, C.POINTER(GUID), C.POINTER(C.c_void_p))
        hr = compile_(self.comp, C.byref(buf), wargs, len(args), None, C.byref(IID_OPRESULT), C.byref(res))
        if hr != 0:
            return False, 'Compile call failed: 0x%x' % (hr & 0xffffffff)
        status = C.c_int32()
        _fn(res, 3, C.c_int32, C.POINTER(C.c_int32))(res, C.byref(status))
        err = C.c_void_p()
        _fn(res, 5, C.c_int32, C.POINTER(C.c_void_p))(res, C.byref(err))
        msg = ''
        if err.value:
            ptr = _fn(err, 3, C.c_void_p)(err)
            size = _fn(err, 4, C.c_size_t)(err)
            msg = C.string_at(ptr, size).decode('utf-8', 'replace') if size else ''
        return status.value >= 0, msg
