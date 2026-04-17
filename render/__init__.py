"""
render — renderers for Schwarzschild geodesics.
"""

from __future__ import annotations

import os
from importlib import import_module
from pathlib import Path
from types import ModuleType

__all__ = ["plot2d", "plot3d", "raster"]

# Avoid noisy warnings / slow imports when the default Matplotlib config dir is
# not writable (common in sandboxed environments). This runs before any of the
# Matplotlib-backed render modules are imported.
if "MPLCONFIGDIR" not in os.environ:
    mpl_config = Path("/tmp/matplotlib")
    mpl_config.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(mpl_config)


def __getattr__(name: str) -> ModuleType:
    if name in __all__:
        return import_module(f"{__name__}.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)
