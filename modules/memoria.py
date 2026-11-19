"""Medición del pico de memoria del proceso (RNF-07) sin dependencias externas."""

import sys


def pico_memoria_mb() -> float | None:
    """Pico de memoria residente del proceso en MB, o None si no se puede medir."""
    try:
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes

            class _Contadores(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            kernel32, psapi = ctypes.windll.kernel32, ctypes.windll.psapi
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(_Contadores), wintypes.DWORD]
            c = _Contadores()
            c.cb = ctypes.sizeof(_Contadores)
            if psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(c), c.cb):
                return c.PeakWorkingSetSize / 1_048_576
            return None
        import resource
        pico = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return pico / 1_048_576 if sys.platform == "darwin" else pico / 1024  # macOS: bytes; Linux: KB
    except Exception:
        return None


def informar_memoria(paso: str) -> None:
    pico = pico_memoria_mb()
    texto = f"{pico:,.0f} MB" if pico is not None else "no disponible"
    print(f"  [{paso}] pico de memoria: {texto}")
