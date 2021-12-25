import os
import re
import subprocess
import sys
import winreg
from pathlib import Path
from typing import List, Optional, Tuple

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
        matlab_home_paths = sorted(root_path.glob(r"R\d+\w"))
        matlab_home_paths = list(set(sorted(matlab_home_paths + get_matlab_registry_installs())))
    elif "darwin" == this_platform:
        matlab_home_paths = sorted(root_path.glob(r"MATLAB_R\d+\w"))
    elif "linux" == this_platform:
        matlab_home_paths = sorted(root_path.glob(r"R\d+\w"))

    return matlab_home_paths


def get_matlab_registry_installs() -> List[Path]:
    """Get list of MATLAB home paths from the Windows registry."""
    matlab_home_paths: List[Path] = []
    hklm = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
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
                        # The path string stored in value is of the form "C:\\Program Files\\MATLAB\\R2021a\\bin\\win64"
                        potential_path = Path(value)
                        if potential_path.is_dir():
                            matlab_home_paths.append(potential_path.parent.parent)
                except FileNotFoundError:
                    pass

        except FileNotFoundError:
            pass

    return sorted(matlab_home_paths)


def validate_matlab_path(path: Path) -> bool:
    """Validate whether a potential MATLAB executable path is legitimate or not."""
    return path.exists() and path.is_file()


def find_matlab_release(release: str, search_path: List[Path]) -> Optional[Path]:
    """Find the path to a MATLAB executable specified by the release name (e.g. R2021a).

    Parameters
    ----------
    release: str
                The desired MATLAB release name
    search_path: list of Path
                 The list of MATLAB home paths to search through

    Returns
    -------
    Path, optional
                   The full path to the MATLAB executable, if found"""
    matlab_path: Optional[Path] = None

    # The MATLAB folder path contains the release name in the root folder,
    # e.g C:/Program Files/MATLAB/R2021a on Windows, /Applications/MATLAB_R2021a.app on macOS, /usr/local/MATLAB/R2021a
    # on Linux
    matches = [p for p in search_path if release in str(p)]

    if len(matches) > 0:
        matlab_root_path = matches[0]
        matlab_path = matlab_root_path / "bin" / get_matlab_exe_name()

    return matlab_path


def get_arch_folder_name() -> str:
    """Return the MATLAB architecture folder name."""
    arch_folders = {"win32": "win64", "darwin": "maci64", "linux": "glnxa64"}

    return arch_folders[sys.platform]


def get_matlab_exe_name() -> str:
    """Return the MATLAB executable file name."""
    matlab_exe: str = "matlab.exe" if sys.platform == "win32" else "matlab"
    return matlab_exe


def query_matlab_version(matlab_exe_path: Path) -> str:
    """Query a given MATLAB instance for its version."""
    matlab_command: str = "clc;disp(version);quit"
    version_string: str = ""
    command: List[str] = [str(matlab_exe_path), "-nosplash", "-nodesktop"]
    if sys.platform == "win32":
        command.append("-wait")
    command.append("-batch")
    command.append(matlab_command)

    try:
        completed_process = subprocess.run(command, text=True, capture_output=True)
        completed_process.check_returncode()
        # With this command, stdout will contain <major>.<minor>.<point>.<patch> (R<release>),
        # e.g. 9.10.0.1602886 (R2021a)
        version_string = completed_process.stdout
    except subprocess.SubprocessError as err:
        print(f"Failed to query MATLAB version: {str(err)}")

    return version_string


def find_matlab_version(target_version: str, search_path: List[Path]) -> Optional[Path]:
    """Find the path to a MATLAB executable specified by its version number.

    Parameters
    __________
    target_version: str
                        The desired MATLAB version (e.g. 9.10)
    search_path: list of Path
                        The list of all MATLAB home folder paths

    Returns
    _______
    Path, optional
                   The absolute file path to the MATLAB executable, if found"""
    matlab_path: Optional[Path] = None
    matlab_exe_name = get_matlab_exe_name()

    for install_root in search_path:
        potential_path = install_root / "bin" / matlab_exe_name

        this_version = query_matlab_version(potential_path)
        if target_version in this_version:
            matlab_path = potential_path
            break

    return matlab_path


def find_matlab(
    potential_matlab_path: Optional[Path],
    matlab_version: Optional[str],
    matlab_release_name: Optional[str],
) -> Tuple[Optional[Path], ReturnCode]:
    """Find the path to a MATLAB executable by providing a path for validation, release name, or version.

    Note that it is only necessary to supply either one of the following: a path, a version or a release name.

    Parameters
    ----------
    potential_matlab_path: Path, optional
                                            An absolute path to a MATLAB executable to validate.
    matlab_version: str, optional
                                            The desired MATLAB version.
    matlab_release_name: str, optional

    Returns
    -------
    matlab_path: Path, optional
                    The absolute path to the MATLAB executable
    return_code: ReturnCode
    """

    return_code: ReturnCode = ReturnCode.FAIL
    matlab_path: Optional[Path] = None

    if potential_matlab_path is not None and validate_matlab_path(potential_matlab_path):
        return_code = ReturnCode.OK
        matlab_path = potential_matlab_path
    else:
        if matlab_release_name is not None:
            matlab_path = find_matlab_release(matlab_release_name, get_matlab_installs())
            if matlab_path is not None:
                return_code = ReturnCode.OK

        if matlab_version is not None:
            matlab_path = find_matlab_version(matlab_version, get_matlab_installs())
            if matlab_path is not None:
                return_code = ReturnCode.OK

    return matlab_path, return_code
