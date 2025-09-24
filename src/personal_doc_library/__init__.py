"""Personal Document Library package."""

from importlib import metadata

__all__ = ["__version__"]


def __getattr__(name: str):
    if name == "__version__":
        try:
            return metadata.version("personal-doc-library")
        except metadata.PackageNotFoundError:
            return "0.0.0"
    raise AttributeError(name)
