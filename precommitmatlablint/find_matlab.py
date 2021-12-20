import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from precommitmatlablint.return_code import ReturnCode


def get_matlab_installs() -> List[Path]:
    this_platform = sys.platform
    install_root_paths: List[Path]
    if "win32" == this_platform:
        program_files: str = os.getenv("PROGRAMFILES", "C:\\Program Files")
        root_path = Path(program_files, "MATLAB")
        install_root_paths = sorted(root_path.glob(r"R\d+\w"))
    elif "darwin" == this_platform:
        root_path = Path("/Applications")
        install_root_paths = sorted(root_path.glob(r"MATLAB_R\d+\w"))
    elif "linux" == this_platform:
        root_path = Path("/usr", "local", "MATLAB")
        install_root_paths = sorted(root_path.glob(r"R\d+\w"))
    else:
        root_path = Path("/usr", "local", "MATLAB")
        install_root_paths = sorted(root_path.glob(r"R\d+\w"))

    return install_root_paths


def validate_matlab_path(path: Path) -> bool:
    return path.exists() and path.is_file()


def find_matlab_release(release: str, search_path: List[Path]) -> Optional[Path]:
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
    arch_folders = {"win32": "win64", "darwin": "maci64", "linux": "glnxa64"}

    return arch_folders[sys.platform]


def get_matlab_exe_name() -> str:
    matlab_exe: str = "matlab.exe" if sys.platform == "win32" else "matlab"
    return matlab_exe


def query_matlab_version(matlab_exe_path: Path) -> str:
    matlab_command: str = "disp(version);quit"
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
