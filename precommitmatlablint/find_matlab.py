import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from return_code import ReturnCode


def get_matlab_installs() -> List[Path]:
    this_platform = sys.platform
    install_root_paths = []
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

    matches = [p for p in search_path if release in str(p)]

    if len(matches) > 0:
        matlab_root_path = matches[0]
        matlab_exe = "matlab.exe" if sys.platform == "win32" else "matlab"
        matlab_path = matlab_root_path / "bin" / matlab_exe

    return matlab_path


def find_matlab(
    potential_matlab_path: Optional[Path],
    matlab_version: Optional[str],
    matlab_release_name: Optional[str],
) -> Tuple[Path, ReturnCode]:
    return_code: ReturnCode = ReturnCode.FAIL
    matlab_path: Path

    if potential_matlab_path is not None and validate_matlab_path(potential_matlab_path):
        return_code = ReturnCode.OK
        matlab_path = potential_matlab_path
    else:
        pass

    return matlab_path, return_code
