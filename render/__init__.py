"""
render — renderers for Schwarzschild geodesics.
"""

from __future__ import annotations

import os
import tempfile
from importlib import import_module
from pathlib import Path
from types import ModuleType

__all__ = ["plot2d", "plot3d", "style", "avoid_matplotlib_warning"]

# Avoid noisy warnings / slow imports when the default Matplotlib config dir is
# not writable (common in sandboxed environments). This runs before any of the
# Matplotlib-backed render modules are imported.
def avoid_matplotlib_warning():
    if "MPLCONFIGDIR" not in os.environ:
        mpl_config = Path(tempfile.gettempdir()) / "matplotlib_cfg"
        mpl_config.mkdir(parents=True, exist_ok=True)
        os.environ["MPLCONFIGDIR"] = str(mpl_config)


avoid_matplotlib_warning()


def __getattr__(name: str) -> ModuleType:
    if name in __all__:
        return import_module(f"{__name__}.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)
