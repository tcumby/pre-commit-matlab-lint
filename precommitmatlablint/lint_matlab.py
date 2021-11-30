import argparse
from enum import IntEnum
from pathlib import Path
from typing import Optional, Sequence, List, Tuple


class ReturnCode(IntEnum):
    OK = 0
    FAIL = 1


def validate_matlab_path(path: Path) -> bool:
    return path.exists() and path.is_file()


def validate_matlab(matlab_path: Path, filenames: List[Path]) -> ReturnCode:
    pass


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
