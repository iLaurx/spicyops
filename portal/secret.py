"""La versión Windows protege la clave de instalación con DPAPI del usuario."""
import ctypes
from ctypes import wintypes

class Blob(ctypes.Structure):
    _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]

def dpapi(data, decrypt=False):
    buffer=ctypes.create_string_buffer(data)
    source=Blob(len(data),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)))
    output=Blob()
    crypt=ctypes.WinDLL('crypt32',use_last_error=True)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    function=crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    result=function(ctypes.byref(source),None,None,None,None,1,ctypes.byref(output))
    if not result:raise OSError('No se pudo abrir el almacén privado de esta cuenta Windows.')
    try:return ctypes.string_at(output.data,output.size)
    finally:
        kernel.LocalFree.argtypes=[ctypes.c_void_p]
        kernel.LocalFree.restype=ctypes.c_void_p
        kernel.LocalFree(output.data)
