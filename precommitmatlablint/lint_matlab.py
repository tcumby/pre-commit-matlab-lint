import argparse
import json
import subprocess
import sys
from pathlib import Path
from subprocess import run
from typing import Any, Dict, List, Optional, Sequence, Union

from precommitmatlablint.find_matlab import find_matlab
from precommitmatlablint.return_code import ReturnCode


def construct_matlab_script(filenames: List[Path], fail_warnings: bool) -> str:
    string_list = [f"'{str(f)}'" for f in filenames]

    file_list_command = ", ".join(string_list)
    level_option = "-m0" if fail_warnings else "-m2"

    return f"clc;disp(jsonencode(checkcode({level_option},'-struct',{file_list_command})));"


def validate_matlab(matlab_path: Path, filenames: List[Path], fail_warnings: bool) -> ReturnCode:
    command: List[str] = [str(matlab_path), "-nosplash"]

    return_code = ReturnCode.OK

    if "win32" == sys.platform:
        command.append("-wait")

    command.append("-batch")
    command.append(construct_matlab_script(filenames, fail_warnings))

    completed_process: subprocess.CompletedProcess = run(command, text=True, capture_output=True)

    try:
        linter_results: Union[Dict[str, Any], List[Dict[str, Any]]] = json.loads(
            completed_process.stdout
        )
        if len(filenames) == 1:
            this_file = filenames[0]
            this_linter_result = linter_results
            if len(this_linter_result) > 0:
                return_code = ReturnCode.FAIL
                print_linter_result(this_file, this_linter_result)

        elif len(filenames) > 1:
            for index, this_file in enumerate(filenames):
                this_linter_result = linter_results[index]
                if len(this_linter_result) > 0:
                    return_code = ReturnCode.FAIL
                    print_linter_result(this_file, this_linter_result)

    except json.JSONDecodeError as err:
        return_code = ReturnCode.FAIL
        print(f"Unable to parse the JSON returned by MATLAB: {str(err)}")

    return return_code


def print_linter_result(this_file, this_linter_result):
    print(f"checkcode found issues in {this_file}:")
    for issue in this_linter_result:
        line_number: int = issue["line"]
        column_range: List[int] = issue["column"]
        message: str = issue["message"]
        print(f"\tLine {line_number} (Column [{column_range[0]}-{column_range[1]}]): {message}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
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
    parser.add_argument(
        "--treat_warning_as_error", action="store_true", help="Treat all warnings as errors"
    )
    parser.add_argument("filenames", nargs="*", type=Path)
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

    fail_warnings: bool = args.treat_warning_as_error
    matlab_path, return_code = find_matlab(
        potential_matlab_path=potential_matlab_path,
        matlab_version=matlab_version,
        matlab_release_name=matlab_release_name,
    )

    if ReturnCode.FAIL == return_code or matlab_path is None or not matlab_path.exists():
        print("Unable to find MATLAB")
        return return_code
    else:
        return validate_matlab(matlab_path, filenames, fail_warnings)


if __name__ == "__main__":
    SystemExit(main())
