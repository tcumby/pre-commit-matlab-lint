"""
Metadata for this pre-commit-matlab-lint.


"""
import logging

# If you need to support Python 3.7, change to importlib_metadata (underscore, not dot)
# and then list importlib_metadata to [tool.poetry.dependencies] and docs/requirements.txt
from importlib.metadata import PackageNotFoundError
from importlib.metadata import metadata as __load
from os import PathLike
from pathlib import Path
from typing import Union

pkg = Path(__file__).absolute().parent.name
logger = logging.getLogger(pkg)
metadata = None
try:
    metadata = __load(pkg)
    __status__ = "Development"
    __copyright__ = "Copyright 2021"
    __date__ = "2021-11-28"
    __uri__ = metadata["home-page"]
    __title__ = metadata["name"]
    __summary__ = metadata["summary"]
    __license__ = metadata["license"]
    __version__ = metadata["version"]
    __author__ = metadata["author"]
    __maintainer__ = metadata["maintainer"]
    __contact__ = metadata["maintainer"]
except PackageNotFoundError:  # pragma: no cover
    logger.error(f"Could not load package metadata for {pkg}. Is it installed?")


class PrecommitmatlablintAssets:
    """
    Utilities and resources for ${Project}.
    """

    @classmethod
    def path(cls, *nodes: Union[str, PathLike[str]]) -> Path:
        """
        Gets the ``Path`` of an asset under ``resources``.

        Args:
            nodes: Path nodes underneath ``resources``

        Returns:
            The final ``Path``

        Raises:
            FileNotFoundError: If the path does not exist
        """
        path = Path(Path(__file__).parent, "resources", *nodes)
        if not path.exists():
            raise FileNotFoundError(f"Asset {path} not found")

        return path


if __name__ == "__main__":  # pragma: no cover
    if metadata is not None:
        print(f"{pkg} (v{metadata['version']})")
    else:
        print(f"Unknown project info for {pkg}")
