import hashlib
import os
import re
import subprocess
import sys
import winreg
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Tuple, Dict

import yaml

from precommitmatlablint.return_code import ReturnCode


@dataclass
class MatlabHandle:
    """A class to provide a simple interface to a MATLAB executable instance."""

    home_path: Path
    exe_path: Path
    checksum: str = ""
    version: str = ""
    release: str = ""
    is_initialized: bool = False

    def __post_init__(self):
        if len(self.version) == 0 and len(self.release) == 0:
            # query_version() takes a fair bit of time, so skip it if the `version` and `release` fields are populated
            self.version, self.release, _ = self.query_version()

        self.checksum = self.compute_checksum()
        self.is_initialized = (
            self.is_valid()
            and len(self.version) > 0
            and len(self.release) > 0
            and len(self.checksum) > 0
        )

    def is_valid(self) -> bool:
        return self.exe_path.exists() and self.exe_path.is_file()

    def run(self, matlab_command: str) -> Tuple[str, ReturnCode]:
        """Run a MATLAB command through this MATLAB instance.

        Parameters
        ----------
        matlab_command: str
                            A single-line MATLAB command string

        Returns
        -------
        stdout:str
                    The stdout from the MATLAB command execution
        return_code: ReturnCode
        """
        stdout: str = ""
        return_code = ReturnCode.FAIL
        if self.is_valid():
            command: List[str] = self.__construct_command(matlab_command)

            try:
                completed_process = subprocess.run(command, text=True, capture_output=True)
                completed_process.check_returncode()

                stdout = completed_process.stdout
                return_code = ReturnCode.OK
            except subprocess.SubprocessError as err:
                print(f"Failed to run MATLAB command '{matlab_command}': {str(err)}")
        return stdout, return_code

    def __construct_command(self, matlab_command: str) -> List[str]:
        """Construct the command-line command to execute the MATLAB command."""
        major, minor = self.__parse_version_string()

        command: List[str] = [str(self.exe_path), "-nosplash", "-nodesktop"]
        if sys.platform == "win32":
            # For Windows, the MATLAB executable at <home>/bin/matlab.exe exits immediately so "-wait" is needed
            command.append("-wait")
        else:
            # For Linux/macOS "-nodisplay" exists in addition to "-nodesktop"
            command.append("-nodisplay")

        # Starting with MATLAB 2019a (v9.6) the preferred command line argument for running MATLAB non-interactively is
        # "-batch"
        if major >= 9 and minor >= 6:
            command.append("-batch")
        else:
            command.append("-r")

        command.append(matlab_command)

        return command

    def __parse_version_string(self) -> Tuple[int, int]:
        """Extract the major and minor version number from the version string of the form
        <major>.<minor>.<point>.<patch>

        Returns
        -------
        major: int
        minor: int
        """

        major: int = 0
        minor: int = 0
        match = re.match(r"(?P<major>\d+)\.(?P<minor>\d+).*", self.version)
        if match:
            major = int(match.group("major"))
            minor = int(match.group("minor"))

        return major, minor

    def query_version(self) -> Tuple[str, str, ReturnCode]:
        """Query a given MATLAB instance for its version.

        Returns
        -------
        version: str
                        The version string in the form <major>.<minor>.<point>.<patch>
        release: str
                        The release name in the form R<year>[a|b]
        return_code: ReturnCode
        """

        # With this command, stdout will contain <major>.<minor>.<point>.<patch> (R<release>),
        # e.g. 9.10.0.1602886 (R2021a)
        stdout, return_code = self.run("clc;disp(version);quit")
        version: str = ""
        release: str = ""
        if ReturnCode.OK == return_code:
            match = re.match(r"(?P<version>[\d+\.]+\d+)\s*\((?P<release>R\d+\w)\).*", stdout)
            if match:
                version = match.group("version")
                release = match.group("release")

        return version, release, return_code

    def compute_checksum(self) -> str:
        hasher = hashlib.sha256()
        checksum: str = ""
        if self.is_valid():
            with self.exe_path.open("rb") as f:
                for page in iter(lambda: f.read(4096), b""):
                    hasher.update(page)

            checksum = hasher.hexdigest()
        return checksum

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)

    @classmethod
    def contruct_exe_path(cls, home_path: Path) -> Path:
        return home_path / "bin" / MatlabHandle.get_matlab_exe_name()

    @classmethod
    def from_dict(cls, input_dict: Dict[str, str]) -> "MatlabHandle":
        home_path = Path(input_dict.get("home_path", "")).absolute()
        exe_path = Path(input_dict.get("exe_path", "")).absolute()
        version = input_dict.get("version", "")
        checksum = input_dict.get("checksum", "")
        release = input_dict.get("release", "")

        return MatlabHandle(
            home_path=home_path,
            exe_path=exe_path,
            version=version,
            checksum=checksum,
            release=release,
        )

    @classmethod
    def get_arch_folder_name(cls) -> str:
        """Return the MATLAB architecture folder name."""
        arch_folders = {"win32": "win64", "darwin": "maci64", "linux": "glnxa64"}

        return arch_folders[sys.platform]

    @classmethod
    def get_matlab_exe_name(cls) -> str:
        """Return the MATLAB executable file name."""
        matlab_exe: str = "matlab.exe" if sys.platform == "win32" else "matlab"
        return matlab_exe


class MatlabHandleList:
    handles: List[MatlabHandle]
    cache_file: Path
    has_changes: bool

    def __init__(self, cache_file: Optional[Path] = None):
        self.handles = []
        if cache_file:
            self.cache_file = cache_file
        else:
            self.cache_file = Path("matlab_info_cache.yaml")

        self.has_changes = False

    def save(self):
        if self.has_changes:
            data: List[Dict[str, str]] = [h.to_dict() for h in self.handles]

            with self.cache_file.open("w") as f:
                yaml.safe_dump(data, f)

    def load(self):
        self.clear()
        with self.cache_file.open("r") as f:
            data = yaml.safe_load(f)
            for element in data:
                self.append(MatlabHandle.from_dict(element))

            self.has_changes = False

    def update(self, search_list: List[Path]) -> None:
        """Add handles to new MATLAB installs"""
        for home_path in search_list:
            if self.find_home_path(home_path) is None:
                exe_path = MatlabHandle.contruct_exe_path(home_path)
                handle = MatlabHandle(home_path=home_path, exe_path=exe_path)
                self.append(handle)

    def prune(self) -> None:
        """Remove handles to MATLAB installs that no longer exist on the machine"""
        remove_list: List[MatlabHandle] = [h for h in self.handles if not h.is_valid()]
        for handle in remove_list:
            self.remove(handle)

    def append(self, handle: MatlabHandle):
        self.handles.append(handle)
        self.has_changes = True

    def remove(self, handle: MatlabHandle):
        self.handles.remove(handle)
        self.has_changes = True

    def insert(self, index: int, handle: MatlabHandle) -> None:
        self.handles.insert(index, handle)
        self.has_changes = True

    def len(self) -> int:
        return len(self.handles)

    def clear(self) -> None:
        self.handles.clear()

    def find_release(self, release_name: str) -> Optional[MatlabHandle]:
        """Find the path to a MATLAB executable specified by the release name (e.g. R2021a).

        Parameters
        ----------
        release_name: str
                    The desired MATLAB release name

        Returns
        -------
        MatlabHandle, optional
                       A handle MATLAB executable, if found"""
        handle: Optional[MatlabHandle] = None

        matches = [h for h in self.handles if release_name.lower() == h.release.lower()]
        if len(matches) > 0:
            handle = matches[0]

        return handle

    def find_version(self, version: str) -> Optional[MatlabHandle]:
        """Find the path to a MATLAB executable specified by its version number.

        Parameters
        __________
        target_version: str
                            The desired MATLAB version (e.g. 9.10)

        Returns
        _______
        MatlabHandle, optional
                       A handle to the MATLAB executable, if found"""

        handle: Optional[MatlabHandle] = None

        matches = [h for h in self.handles if version in h.version]
        if len(matches) > 0:
            handle = matches[0]

        return handle

    def find_home_path(self, matlab_home_path: Path) -> Optional[MatlabHandle]:
        r"""Find the path to a MATLAB executable specified by its home path.

        Parameters
        __________
        matlab_home_path: Path
                                A folder path to a MATLAB install home path (e.g.
                                C:\Program Files\MATLAB\R2021a)

        Returns
        _______
        MatlabHandle, optional
                       A handle to the MATLAB executable, if found"""
        handle: Optional[MatlabHandle] = None

        matches = [h for h in self.handles if matlab_home_path == h.home_path]
        if len(matches) > 0:
            handle = matches[0]

        return handle

    def find_exe_path(self, matlab_exe_path: Path) -> Optional[MatlabHandle]:
        """Find the path to a MATLAB executable specified by its path.

        Parameters
        __________
        matlab_home_path: Path
                                A file path to a MATLAB executable (e.g.
                                C:\\Program Files\\MATLAB\\R2021a\bin\\matlab.exe)

        Returns
        _______
        MatlabHandle, optional
                       A handle to the MATLAB executable, if found"""
        handle: Optional[MatlabHandle] = None

        matches = [h for h in self.handles if matlab_exe_path == h.exe_path]
        if len(matches) > 0:
            handle = matches[0]

        return handle


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
        matlab_home_paths = sorted(root_path.glob(r"R\d+\w"), reverse=True)
        matlab_home_paths = sorted(
            list(set(sorted(matlab_home_paths + get_matlab_registry_installs()))), reverse=True
        )
    elif "darwin" == this_platform:
        matlab_home_paths = sorted(root_path.glob(r"MATLAB_R\d+\w"), reverse=True)
    elif "linux" == this_platform:
        matlab_home_paths = sorted(root_path.glob(r"R\d+\w"), reverse=True)

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
                        # The path string stored in value is of the form "C:\\Program Files\\MATLAB\\R2021a\\bin\\win64"
                        potential_path = Path(value)
                        if potential_path.is_dir():
                            matlab_home_paths.append(potential_path.parent.parent)
                except FileNotFoundError:
                    pass

        except FileNotFoundError:
            pass

    return sorted(matlab_home_paths)


def find_matlab(
    matlab_home_path: Optional[Path] = None,
    matlab_version: Optional[str] = None,
    matlab_release_name: Optional[str] = None,
    cache_file: Optional[Path] = None,
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
    Returns
    -------
    handle: MatlabHandle, optional
                    A handle to a MATLAB instance
    return_code: ReturnCode
    """

    handle_list: MatlabHandleList = MatlabHandleList(cache_file)
    handle_list.load()
    handle_list.update(get_matlab_installs())

    handle: Optional[MatlabHandle] = None
    if matlab_home_path is not None:
        handle = handle_list.find_home_path(matlab_home_path)
        if handle is None:
            # This must be an installation that our search path missed. Try to contruct a MatlabHandle and if it
            # initializes, then add it to the MatlabHandleList
            exe_path: Path = MatlabHandle.contruct_exe_path(matlab_home_path)
            test_handle = MatlabHandle(home_path=matlab_home_path, exe_path=exe_path)
            handle = test_handle if test_handle.is_initialized else None
            if handle is not None:
                handle_list.append(handle)

    else:
        if matlab_release_name is not None:
            handle = handle_list.find_release(matlab_release_name)

        if matlab_version is not None:
            handle = handle_list.find_version(matlab_version)

    handle_list.save()

    return_code = ReturnCode.OK if handle is not None else ReturnCode.FAIL

    return handle, return_code
