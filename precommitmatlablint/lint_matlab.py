import argparse
import subprocess
import sys
from enum import IntEnum
from pathlib import Path
from subprocess import run
from typing import List, Optional, Sequence, Tuple


class ReturnCode(IntEnum):
    OK = 0
    FAIL = 1


def validate_matlab_path(path: Path) -> bool:
    return path.exists() and path.is_file()


def construct_matlab_script(filenames: List[Path]) -> str:
    string_list = [f"'{str(f)}'" for f in filenames]

    file_list_command = ", ".join(string_list)

    return f"disp(jsonencode(checkcode('-struct', {file_list_command})));"


def validate_matlab(matlab_path: Path, filenames: List[Path]) -> ReturnCode:
    command: List[str] = [str(matlab_path), "-nosplash"]

    if "win32" == sys.platform:
        command.append("-wait")

    command.append("-batch", construct_matlab_script(filenames))

    completed_process: subprocess.CompletedProcess = run(command, text=True, capture_output=True)


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


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*", type=Path)
    parser.add_argument(
        "--matlab_path",
        action="store",
        type=str,
        default="",
        help="File path to the MATLAB executable.",
    )

    parser.add_argument(
        "--matlab_version",
        action="store",
        type=str,
        default="",
        help="The version of MATLAB to use.",
    )

    parser.add_argument(
        "--matlab_release_name",
        action="store",
        type=str,
        default="",
        help="The release name of MATLAB to use.",
    )
    args = parser.parse_args(argv)

    filenames: List[Path] = []
    if args.filenames:
        filenames = args.filenames

    potential_matlab_path: Optional[Path] = None
    if len(args.matlab_path) > 0:
        potential_matlab_path = Path(args.matlab_path)

    matlab_version: Optional[str] = None
    if len(args.matlab_version) > 0:
        matlab_version = args.matlab_version

    matlab_release_name: Optional[str] = None
    if len(args.matlab_release_name) > 0:
        matlab_release_name = args.matlab_release_name

    matlab_path, return_code = find_matlab(
        potential_matlab_path=potential_matlab_path,
        matlab_version=matlab_version,
        matlab_release_name=matlab_release_name,
    )

    if ReturnCode.FAIL == return_code:
        return return_code
    else:
        return validate_matlab(matlab_path, filenames)


if __name__ == "__main__":
    SystemExit(main())
