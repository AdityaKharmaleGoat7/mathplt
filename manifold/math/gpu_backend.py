"""
GPU / CPU backend abstraction for Manifold.

Auto-detects CuPy (NVIDIA CUDA) at import time.
Every array operation goes through the module returned by ``get_xp()``,
which is either ``cupy`` or ``numpy`` — their APIs are near-identical.

If no GPU is found, everything falls back to NumPy silently.
"""

from __future__ import annotations

import numpy as np

_GPU_AVAILABLE: bool = False
_cp = None

try:
    import cupy as _cp_module  # type: ignore[import-untyped]

    if _cp_module.cuda.runtime.getDeviceCount() > 0:
        _GPU_AVAILABLE = True
        _cp = _cp_module
except Exception:
    pass


def gpu_available() -> bool:
    """Return True if a CUDA-capable GPU is reachable via CuPy."""
    return _GPU_AVAILABLE


def get_xp(force_cpu: bool = False):
    """Return the active array module — ``cupy`` when a GPU is present, else ``numpy``."""
    if force_cpu or not _GPU_AVAILABLE:
        return np
    return _cp


def to_numpy(arr) -> np.ndarray:
    """Guarantee a host-side NumPy array (no-op if already NumPy)."""
    if _GPU_AVAILABLE and _cp is not None and isinstance(arr, _cp.ndarray):
        return _cp.asnumpy(arr)
    return np.asarray(arr)


def to_device(arr, force_cpu: bool = False):
    """Move *arr* to the active compute device (GPU or CPU)."""
    xp = get_xp(force_cpu)
    if xp is np:
        return np.asarray(arr)
    return _cp.asarray(arr)
