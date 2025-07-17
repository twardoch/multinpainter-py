import sys

if sys.version_info[:2] >= (3, 8):
    # TODO: Import directly (no need for conditional) when `python_requires = >= 3.8`
    from importlib.metadata import PackageNotFoundError  # pragma: no cover
    from importlib.metadata import version
else:
    from importlib_metadata import PackageNotFoundError  # pragma: no cover
    from importlib_metadata import version

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

# Try to read from setuptools_scm generated version file
try:
    from ._version import __version__
except ImportError:
    pass

from .multinpainter import DESCRPTION_MODEL, Multinpainter_OpenAI

__all__ = ["Multinpainter_OpenAI", "DESCRPTION_MODEL"]
