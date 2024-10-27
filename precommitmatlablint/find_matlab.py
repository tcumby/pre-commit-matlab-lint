import logging
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import defusedxml.ElementTree as ElementTree  # type: ignore[import-untyped]

from precommitmatlablint.linter_handle import MatlabHandle, MatlabHandleList
from precommitmatlablint.return_code import ReturnCode


def get_matlab_root(platform: str) -> Path:
    """Return the MATLAB install root folder path, e.g. C:\\Program Files\\MATLAB on Windows

    Parameters
    ----------
    platform: str
              The value of sys.platform

    Returns
    -------
    Path
    """

    root_paths = {
        "win32": Path(os.getenv("PROGRAMFILES", "C:\\Program Files"), "MATLAB"),
        "darwin": Path("/Applications"),
        "linux": Path("/usr", "local", "MATLAB"),
    }

    return root_paths[platform]


def get_matlab_installs() -> List[Path]:
    """Return a list of all MATLAB home folder paths based on matching the release name pattern in the folder name.

    Returns
    -------
    List of Path
                 A list of all discovered MATLAB home paths
    """
    this_platform = sys.platform
    matlab_home_paths: List[Path] = []
    root_path = get_matlab_root(this_platform)
    if "win32" == this_platform:
        if root_path.exists():
            matlab_home_paths = [d for d in root_path.iterdir() if d.is_dir() and re.match(r"R\d+\w", d.stem)]
            matlab_home_paths = sorted(matlab_home_paths, reverse=True)
        matlab_home_paths = sorted(list(set(sorted(matlab_home_paths + get_matlab_registry_installs()))), reverse=True)
    elif "darwin" == this_platform:
        matlab_home_paths = [d for d in root_path.iterdir() if d.is_dir() and re.match(r"MATLAB_R\d+\w", d.stem)]
        matlab_home_paths = sorted(matlab_home_paths, reverse=True)
    elif "linux" == this_platform:
        if root_path.exists():
            matlab_home_paths = [d for d in root_path.iterdir() if d.is_dir() and re.match(r"R\d+\w", d.stem)]
            matlab_home_paths = sorted(matlab_home_paths, reverse=True)

    return matlab_home_paths


def get_matlab_registry_installs() -> List[Path]:
    import winreg

    """Get list of MATLAB home paths from the Windows registry."""
    matlab_home_paths: List[Path] = []
    hklm = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    try:
        mathworks_key = winreg.OpenKey(hklm, r"SOFTWARE\MathWorks")
        # This is how the "Mathworks" registry key and subkeys are structured
        # HKLM\SOFTWARE\Mathworks
        # |
        # --MATLAB
        #   |
        #   --<version 1>
        #   |
        #   --<version 2>
        #   ...
        #   |
        #   --<version N>
        # |
        # --<release 1>
        #   |
        #   --MATLAB <- value is <MATLAB HOME>/bin/<arch>
        # |
        # --<release 2>
        # ...
        # |
        # --<release N>

        # To retrieve the subkeys to HKLM\SOFTWARE\Mathworks, we repeatedly call EnumKey until it throws
        index = 0
        subkey_names: List[str] = []
        while True:
            try:
                subkey_names.append(winreg.EnumKey(mathworks_key, index))
                index += 1
            except OSError:
                break

        # Find the release names
        release_names: List[str] = [s for s in subkey_names if re.search(r"R\d+\w", s) is not None]
        for subkey_name in release_names:
            try:
                with winreg.OpenKey(mathworks_key, rf"{subkey_name}\MATLAB") as release_key:
                    try:
                        value, reg_type = winreg.QueryValueEx(release_key, "")
                        if isinstance(value, str):
                            # The path string stored in value is of the form
                            # "C:\\Program Files\\MATLAB\\R2021a\\bin\\win64"
                            potential_path = Path(value)
                            if potential_path.is_dir():
                                matlab_home_paths.append(potential_path.parent.parent)
                    except FileNotFoundError:
                        pass

            except FileNotFoundError:
                pass
    except FileNotFoundError:
        # Likely the Mathworks sub-key does not exist
        pass

    return sorted(matlab_home_paths)


def find_matlab(
    matlab_home_path: Optional[Path] = None,
    matlab_version: Optional[str] = None,
    matlab_release_name: Optional[str] = None,
    cache_file: Optional[Path] = None,
    logger: Optional[logging.Logger] = None,
) -> Tuple[Optional[MatlabHandle], ReturnCode]:
    """Find the path to a MATLAB executable by providing a path for validation, release name, or version.

    Note that it is only necessary to supply either one of the following: a path, a version or a release name.

    Parameters
    ----------
    matlab_home_path: Path, optional
                                            An absolute path to a MATLAB home folder to validate.
    matlab_version: str, optional
                                            The desired MATLAB version.
    matlab_release_name: str, optional

    cache_file: Path, optional

    logger: logging.Logger, optional

    Returns
    -------
    handle: MatlabHandle, optional
                    A handle to a MATLAB instance
    return_code: ReturnCode
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    handle_list: MatlabHandleList = MatlabHandleList(cache_file=cache_file, logger=logger)
    handle_list.load()
    if len(handle_list) == 0:
        # If we haven't previously cached any installs, go find all that are present on the system
        logger.info("No prior MATLAB installs have been cached.")
        handle_list.update(get_matlab_installs())

    handle: Optional[MatlabHandle] = None
    if matlab_home_path is not None:
        logger.info(f"MATLAB home path {matlab_home_path} exists")
        handle = handle_list.find_home_path(matlab_home_path)
        if handle is None:
            # This must be an installation that our search path missed. Try to contruct a MatlabHandle and if it
            # initializes, then add it to the MatlabHandleList
            logger.info("The MATLAB interpreter has not been cached previously.")
            exe_path: Path = MatlabHandle.construct_exe_path(matlab_home_path)
            base_exe_path: Path = MatlabHandle.construct_base_exe_path(matlab_home_path)
            test_handle = MatlabHandle(home_path=matlab_home_path, exe_path=exe_path, base_exe_path=base_exe_path)
            handle = test_handle if test_handle.is_initialized() else None
            if handle is not None:
                handle_list.append(handle)

    else:
        if matlab_release_name is not None:
            logger.info(f"Attempting to locate a handle to MATLAB {matlab_release_name}")
            handle = handle_list.find_release(matlab_release_name)

        if matlab_version is not None:
            logger.info(f"Attempting to locate a handle to MATLAB {matlab_version}")
            handle = handle_list.find_version(matlab_version)

    logger.info(f"Saving MATLAB handle list to {handle_list.cache_file}")
    handle_list.save()

    return_code = ReturnCode.OK if handle is not None else ReturnCode.FAIL
    logger.info(f"MATLAB handle found: {return_code.name}")
    return handle, return_code
