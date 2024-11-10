import hashlib
import json
import logging
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Protocol, List, Tuple, Dict

import yaml
from defusedxml import ElementTree as ElementTree

from precommitmatlablint.linter_results import LinterReport, LinterRecord
from precommitmatlablint.return_code import ReturnCode
from precommitmatlablint.utility import construct_matlab_script


@dataclass(frozen=True)
class LinterOptions:
    fail_warnings: bool
    enable_cyc: bool
    enable_mod_cyc: bool
    ignore_ok_pragmas: bool
    use_factory_default: bool
    checkcode_config_file: Optional[Path] = None


class Linter(Protocol):
    def lint(self, filepaths: List[Path], options: LinterOptions) -> List[LinterReport]:
        pass


@dataclass(frozen=True)
class MLintHandle(Linter):
    exe_path: Path

    def is_valid(self) -> bool:
        return self.exe_path.exists()

    def lint(self, filepaths: List[Path], options: LinterOptions) -> List[LinterReport]:
        linter_reports: List[LinterReport]

        command = [str(self.exe_path)]
        arguments = MLintHandle.construct_command_arguments(
            filepaths=filepaths,
            options=options,
        )

        command = command + arguments

        completed_process = subprocess.run(command, capture_output=True, text=True)

        stderr = completed_process.stderr

        linter_reports = self.parse_mlint_output(stderr, filepaths)

        return linter_reports

    @classmethod
    def parse_mlint_output(cls, stdout: str, file_list: List[Path]) -> List[LinterReport]:
        linter_reports: List[LinterReport] = []
        if len(stdout) > 0:
            lines: List[str] = stdout.splitlines()
            lines = [line.strip() for line in lines]

            if len(file_list) == 1:
                this_report = LinterReport(source_file=file_list[0])
                for line in lines:
                    this_report.records.append(LinterRecord.from_mlint(mlint_message=line))
                linter_reports.append(this_report)
            elif len(file_list) > 1:
                boundary_indeces = [idx for (idx, line) in enumerate(lines) if line.startswith("===")]

                for idx, boundary_index in enumerate(boundary_indeces):
                    # Each boundary line is of the form '============ <file path> ============'
                    file_path: str = lines[boundary_index].strip("=").strip()
                    this_report = LinterReport(source_file=Path(file_path))

                    start_index = boundary_index + 1
                    end_index = len(lines) if idx == len(boundary_indeces) - 1 else boundary_indeces[idx + 1]

                    has_records = (end_index - start_index + 1) > 0
                    if has_records:
                        # There is linter output for this file
                        for line_index in range(start_index, end_index):
                            this_report.records.append(LinterRecord.from_mlint(mlint_message=lines[line_index]))

                    linter_reports.append(this_report)

        return linter_reports

    @classmethod
    def construct_command_arguments(cls, filepaths: List[Path], options: LinterOptions) -> List[str]:

        level_option = "-m0" if options.fail_warnings else "-m2"
        arguments: List = [level_option, "-id"]
        if options.enable_cyc:
            arguments.append("-cyc")

        if options.enable_mod_cyc:
            arguments.append("-modcyc")

        if options.ignore_ok_pragmas:
            arguments.append("-notok")

        if options.use_factory_default:
            arguments.append("-config=factory")
        elif options.checkcode_config_file:
            arguments.append(f"-config={str(options.checkcode_config_file)}")

        arguments = arguments + filepaths

        return arguments


@dataclass
class MatlabHandle(Linter):
    """A class to provide a simple interface to a MATLAB executable instance."""

    home_path: Path
    exe_path: Path
    base_exe_path: Path
    checksum: str = ""
    version: str = ""
    release: str = ""

    def __post_init__(self):
        if len(self.version) == 0 and len(self.release) == 0:
            # query_version() takes a fair bit of time, so skip it if the `version` and `release` fields are populated
            self.version, self.release = MatlabHandle.read_version_info(self.get_version_info_file())

        if len(self.version) == 0 and len(self.release) == 0:
            # Try to get the version and release name from a product info XML file at <MATLAB home>/appdata/products
            self.version, self.release = MatlabHandle.read_product_info(self.get_product_info_file())

        if len(self.version) == 0 and len(self.release) == 0:
            # query_version() takes a fair bit of time, so skip it if the `version` and `release` fields are populated
            self.version, self.release, _ = self.query_version()

        self.checksum = self.compute_checksum()

    def get_version_info_file(self) -> Path:
        return self.home_path / "VersionInfo.xml"

    def get_product_info_file(self) -> Optional[Path]:
        info_file: Optional[Path] = None
        products_folder = self.home_path / "appdata" / "products"
        arch: str = MatlabHandle.get_architecture_folder_name()
        files = [
            f for f in products_folder.glob("MATLAB*.xml") if re.match(rf"MATLAB\s*\d+\.\d+\s*{arch}.*.xml", f.name)
        ]
        if len(files) > 0:
            info_file = files[0]

        return info_file

    def get_mlint_handle(self) -> MLintHandle:
        return MLintHandle(
            exe_path=Path(
                self.home_path,
                "bin",
                self.get_architecture_folder_name(),
                "mlint.exe" if sys.platform == "win32" else "mlint",
            )
        )

    def is_initialized(self) -> bool:
        return self.is_valid() and len(self.version) > 0 and len(self.release) > 0 and len(self.checksum) > 0

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
            command: List[str] = self._construct_command(matlab_command)

            try:
                completed_process = subprocess.run(command, text=True, capture_output=True)
                completed_process.check_returncode()

                stdout = completed_process.stdout
                return_code = ReturnCode.OK
            except subprocess.SubprocessError as err:
                print(f"Failed to run MATLAB command '{matlab_command}': {str(err)}")
        return stdout, return_code

    def _construct_command(self, matlab_command: str) -> List[str]:
        """Construct the command-line command to execute the MATLAB command."""
        major, minor = self._parse_version_string()

        command: List[str] = [str(self.exe_path), "-nosplash", "-nodesktop"]
        if sys.platform == "win32":
            # For Windows, the MATLAB executable at <home>/bin/matlab.exe exits immediately so "-wait" is needed
            command.append("-wait")
            command.append("-minimize")
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

    def _parse_version_string(self) -> Tuple[int, int]:
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
            release, version = self.extract_release_version_from_output(stdout)
            if len(release) == 0 and len(version) == 0:
                # This MATLAB instance is not returning info to stdout, so output to file instead
                print(f"This MATLAB instance {self.home_path} failed to return anything via stdout.")
                with TemporaryDirectory() as base_path:
                    matlab_log_file = Path(base_path) / "MATLAB_output.txt"
                    _, return_code = self.run(
                        f"clc;fid=fopen('{str(matlab_log_file)}', 'w');fprintf(fid, '%s', version);fclose(fid);quit;"
                    )
                    with matlab_log_file.open() as output:
                        text = output.read()
                        release, version = self.extract_release_version_from_output(text)

                    matlab_log_file.unlink()

        return version, release, return_code

    def lint(self, filepaths: List[Path], options: LinterOptions) -> List[LinterReport]:
        linter_reports: List[LinterReport] = []

        matlab_script: str = construct_matlab_script(
            filepaths,
            options.fail_warnings,
            options.enable_cyc,
            options.enable_mod_cyc,
            options.ignore_ok_pragmas,
            options.use_factory_default,
            options.checkcode_config_file,
        )

        print(f"Validating MATLAB files using {str(self.exe_path)}")
        stdout, return_code = self.run(matlab_script)

        checkcode_data = json.loads(stdout)

        if len(filepaths) == 1:
            this_report = LinterReport(source_file=filepaths[0])
            for issue in checkcode_data:
                this_record = LinterRecord(
                    id=issue["id"], line=issue["line"], columns=issue["column"], message=issue["message"]
                )
                this_report.records.append(this_record)

            linter_reports.append(this_report)
        else:
            for index, this_file in enumerate(filepaths):
                this_report = LinterReport(source_file=this_file)
                this_linter_results = checkcode_data[index]
                for issue in this_linter_results:
                    this_record = LinterRecord(
                        id=issue["id"], line=issue["line"], columns=issue["column"], message=issue["message"]
                    )
                    this_report.records.append(this_record)

                linter_reports.append(this_report)

        return linter_reports

    @staticmethod
    def extract_release_version_from_output(stdout) -> Tuple[str, str]:
        release: str = ""
        version: str = ""
        match = re.match(r"(?P<version>[\d+.]+\d+)\s*\((?P<release>R\d+\w)\).*", stdout)
        if match:
            version = match.group("version")
            release = match.group("release")
        return release, version

    def compute_checksum(self) -> str:
        """Compute the sha256 hash of the MATLAB executable.
        Returns
        -------
        str
            The sha256 hash, if the executable exists, an empty string otherwise
        """

        hasher = hashlib.sha256()
        checksum: str = ""
        if self.is_valid():
            with self.exe_path.open("rb") as f:
                for page in iter(lambda: f.read(4096), b""):
                    hasher.update(page)

            checksum = hasher.hexdigest()
        return checksum

    def to_dict(self) -> Dict[str, str]:
        output: Dict[str, str] = asdict(self)
        for _, (key, value) in enumerate(output.items()):
            if isinstance(value, Path):
                output[key] = str(value)
        return output

    def refresh(self) -> None:
        if self.is_valid():
            self.checksum: str = self.compute_checksum()
            version_info_file: Path = self.get_version_info_file()
            if version_info_file.exists():
                self.version, self.release = MatlabHandle.read_version_info(self.get_version_info_file())

    @classmethod
    def construct_base_exe_path(cls, home_path: Path) -> Path:
        return home_path / "bin" / MatlabHandle.get_architecture_folder_name() / MatlabHandle.get_matlab_exe_name()

    @classmethod
    def construct_exe_path(cls, home_path: Path) -> Path:
        return home_path / "bin" / MatlabHandle.get_matlab_exe_name()

    @classmethod
    def read_version_info(cls, version_info_path: Path) -> Tuple[str, str]:
        version: str = ""
        release: str = ""

        if version_info_path.exists():
            tree = ElementTree.parse(version_info_path)
            root = tree.getroot()
            version = root.find("version").text
            release = root.find("release").text

        return version, release

    @classmethod
    def read_product_info(cls, product_info_path: Optional[Path]) -> Tuple[str, str]:
        version: str = ""
        release: str = ""

        if product_info_path is not None and product_info_path.exists():
            tree = ElementTree.parse(product_info_path)
            root = tree.getroot()

            version = root.find("productVersion").text
            release = root.find("releaseFamily").text

        return version, release

    @classmethod
    def from_dict(cls, input_dict: Dict[str, str]) -> "MatlabHandle":
        home_path = Path(input_dict.get("home_path", "")).absolute()
        exe_path = Path(input_dict.get("exe_path", "")).absolute()
        base_exe_path = Path(input_dict.get("base_exe_path", "")).absolute()
        version = input_dict.get("version", "")
        checksum = input_dict.get("checksum", "")
        release = input_dict.get("release", "")

        return MatlabHandle(
            home_path=home_path,
            exe_path=exe_path,
            base_exe_path=base_exe_path,
            version=version,
            checksum=checksum,
            release=release,
        )

    @classmethod
    def get_matlab_exe_name(cls) -> str:
        """Return the MATLAB executable file name."""
        matlab_exe: str = "matlab.exe" if sys.platform == "win32" else "matlab"
        return matlab_exe

    @classmethod
    def get_architecture_folder_name(cls) -> str:
        """Return the architecture folder name used by Mathworks"""
        arch_folder_names = {"win32": "win64", "darwin": "maci64", "linux": "glnxa64"}
        return arch_folder_names.get(sys.platform, "")


class MatlabHandleList:
    handles: List[MatlabHandle]
    cache_file: Path
    has_changes: bool
    _logger: logging.Logger

    def __init__(self, cache_file: Optional[Path] = None, logger: Optional[logging.Logger] = None):
        self.handles = []
        if cache_file:
            self.cache_file = cache_file
        else:
            self.cache_file = Path(Path.home(), ".pre-commit-matlab-lint.matlab-info-cache.yaml")

        self.has_changes = False
        if logger:
            self._logger = logger
        else:
            self._logger = logging.getLogger(__name__)

    def __len__(self) -> int:
        return len(self.handles)

    def set_logger(self, logger: logging.Logger):
        self._logger = logger

    def save(self) -> None:
        if self.has_changes:
            data: List[Dict[str, str]] = [h.to_dict() for h in self.handles]

            with self.cache_file.open("w") as f:
                self._logger.debug(f"Saving MATLAB handle list to {self.cache_file}")
                yaml.safe_dump(data, f)
                self.has_changes = False

    def load(self) -> None:
        if self.cache_file.exists():
            self._logger.debug(f"Cache file {self.cache_file} exists.")
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
                self._logger.info(f"Found new MATLAB installation at {home_path}")
                exe_path = MatlabHandle.construct_exe_path(home_path)
                base_exe_path = MatlabHandle.construct_base_exe_path(home_path)
                handle = MatlabHandle(home_path=home_path, exe_path=exe_path, base_exe_path=base_exe_path)
                self.append(handle)

    def prune(self) -> None:
        """Remove handles to MATLAB installs that no longer exist on the machine"""
        remove_list: List[MatlabHandle] = [h for h in self.handles if not h.is_valid()]
        if len(remove_list) > 0:
            self.has_changes = True

        for handle in remove_list:
            self.remove(handle)

    def append(self, handle: MatlabHandle):
        self._logger.debug(f"Adding the MATLAB handle for home path {handle.home_path}")
        self.handles.append(handle)
        self.has_changes = True

    def remove(self, handle: MatlabHandle):
        self._logger.debug(f"Removing the MATLAB handle for home path {handle.home_path}")
        self.handles.remove(handle)
        self.has_changes = True

    def insert(self, index: int, handle: MatlabHandle) -> None:
        self._logger.debug(f"Inserting the MATLAB handle for home path {handle.home_path}")
        self.handles.insert(index, handle)
        self.has_changes = True

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
            self._logger.info(f"Handle for MATLAB release {release_name} found.")
        else:
            # TODO search for MATLAB if not found
            self._logger.warning(f"Handle for MATLAB release name {release_name} not found.")

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
            self._logger.info(f"Handle for MATLAB version {version} found.")
        else:
            # TODO search for MATLAB if not found
            self._logger.warning(f"Handle for MATLAB version {version} not found.")

        return handle

    def find_home_path(self, matlab_home_path: Path) -> Optional[MatlabHandle]:
        """Find the MatlabHandle corresponding to the supplied MATLAB home path

        Parameters
        __________
        matlab_home_path: Path
                                A folder path to a MATLAB install home path (e.g.
                                C:\\Program Files\\MATLAB\\R2021a)

        Returns
        _______
        MatlabHandle, optional
                       A handle to the MATLAB executable, if found"""
        handle: Optional[MatlabHandle] = None

        matches = [h for h in self.handles if matlab_home_path == h.home_path]
        if len(matches) > 0:
            handle = matches[0]
            self._logger.info(f"Handle for MATLAB at {matlab_home_path} found.")
        else:
            # TODO search for MATLAB if not found
            self._logger.warning(f"Handle for MATLAB at {matlab_home_path} not found")

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
            self._logger.info(f"Handle for MATLAB at {matlab_exe_path} found.")
        else:
            # TODO search for MATLAB if not found
            self._logger.warning(f"Handle for MATLAB at {matlab_exe_path} not found.")

        return handle
