import argparse
import json
import subprocess
import sys
from pathlib import Path
from subprocess import run
from typing import Any, Dict, List, Optional, Sequence

from precommitmatlablint.find_matlab import find_matlab
from precommitmatlablint.return_code import ReturnCode


def is_existent_file(potential_file: Path) -> bool:
    """Assess if a Path points to a file that exists."""
    return potential_file.exists() and potential_file.is_file()


def extract_file_path_option(file_path_string: str) -> Optional[Path]:
    """Return a file Path from a supplied string, or None if the supplied string does not map to an existing file."""
    potential_file = Path(file_path_string).absolute()
    return potential_file if is_existent_file(potential_file) else None


def construct_matlab_script(
    filepaths: List[Path],
    fail_warnings: bool,
    enable_cyc: bool,
    enable_mod_cyc: bool,
    ignore_ok_pragmas: bool,
    use_factory_default: bool,
    checkcode_config_file: Optional[Path] = None,
) -> str:
    """Return the inline MATLAB script to run on the MATLAB instance.

    Parameters
    ----------

    use_factory_default
    filepaths: list of Path
                            List of all filepaths to validate through MATLAB's checkcode function
    fail_warnings: bool
                            Whether to treat warnings as errors
    enable_mod_cyc: bool
                            Enable display of modified cyclomaticity complexity calculations for each file.
    enable_cyc: bool
                            Enable display of McCabe cyclomaticity camplexity calculations for each file.
    ignore_ok_pragmas: bool
                            Ignore %#ok checkcode suppression pragmas
    use_factory_default: bool
                            Ignore any checkcode config files and use factory defaults
    checkcode_config_file: Path, optional
                            An absolute path to a checkcode config file
    Returns
    -------
    str
        The MATLAB script to run on the MATLAB instance
    """
    file_list = [f"'{str(f)}'" for f in filepaths]

    level_option = "-m0" if fail_warnings else "-m2"
    command: List = [level_option, "-id", "-struct"]
    if enable_cyc:
        command.append("-cyc")

    if enable_mod_cyc:
        command.append("-modcyc")

    if ignore_ok_pragmas:
        command.append("-notok")

    if use_factory_default:
        command.append("-config=factory")
    elif checkcode_config_file:
        command.append(f"-config={str(checkcode_config_file)}")

    command = command + file_list
    command_string: str = ", ".join(command)
    return f"clc;disp(jsonencode(checkcode({command_string})));"


def validate_matlab(
    matlab_path: Path,
    filepaths: List[Path],
    fail_warnings: bool,
    enable_cyc: bool,
    enable_mod_cyc: bool,
    ignore_ok_pragmas: bool,
    use_factory_default: bool,
    checkcode_config_file: Optional[Path] = None,
) -> ReturnCode:
    """Validate a list of MATLAB source files using MATLAB's checkcode function.

    Parameters
    ----------

    matlab_path: Path
                            The absolute path to the MATLAB executable
    filepaths: list of Path
                            The list of m-file file paths
    fail_warnings: bool
                            Whether to treat warnings as errors
    enable_mod_cyc: bool
                            Enable display of modified cyclomaticity complexity calculations for each file.
    enable_cyc: bool
                            Enable display of McCabe cyclomaticity camplexity calculations for each file.
    ignore_ok_pragmas: bool
                            Ignore %#ok checkcode suppression pragmas
    use_factory_default: bool
                            Ignore any checkcode config files and use factory defaults
    checkcode_config_file: Path, optional
                            An absolute path to a checkcode config file

    Returns
    -------
    ReturnCode
    """
    return_code = ReturnCode.OK

    command: List[str] = [str(matlab_path)]
    if "win32" == sys.platform:
        command.append("-wait")
    command.append("-batch")
    command.append(
        construct_matlab_script(
            filepaths,
            fail_warnings,
            enable_cyc,
            enable_mod_cyc,
            ignore_ok_pragmas,
            use_factory_default,
            checkcode_config_file,
        )
    )

    print(f"Validating MATLAB files using {str(matlab_path)}")
    completed_process: subprocess.CompletedProcess = run(command, text=True, capture_output=True)

    try:
        if len(filepaths) == 1:
            this_file = filepaths[0]
            linter_results: List[Dict[str, Any]] = json.loads(completed_process.stdout)
            return_code = inspect_linter_result(linter_results)
            print_linter_result(this_file, linter_results)

        elif len(filepaths) > 1:
            linter_results_list: List[List[Dict[str, Any]]] = json.loads(completed_process.stdout)
            for index, this_file in enumerate(filepaths):
                this_linter_results = linter_results_list[index]
                return_code = inspect_linter_result(this_linter_results)
                print_linter_result(this_file, this_linter_results)

    except json.JSONDecodeError as err:
        return_code = ReturnCode.FAIL
        print(f"Unable to parse the JSON returned by MATLAB: {str(err)}")

    return return_code


def inspect_linter_result(linter_results: List[Dict[str, Any]]) -> ReturnCode:
    """Inspect a given linter result to determine if it indicates a failure.
    Parameters
    ----------
    linter_results: list of dict
                                 The list of linter result dictionaries
    Returns
    -------
    ReturnCode
    """
    return_code: ReturnCode = ReturnCode.OK

    # Let's not fail if any of the linter McCabe cyclomaticity IDs are present.
    allowed_ids = ["CABE", "MCABE"]
    return_codes: List[ReturnCode] = []
    if len(linter_results) > 0:
        for result in linter_results:
            this_return_code = ReturnCode.FAIL if result["id"] not in allowed_ids else ReturnCode.OK
            return_codes.append(this_return_code)

        return_code = (
            ReturnCode.FAIL if any([r == ReturnCode.FAIL for r in return_codes]) else ReturnCode.OK
        )

    return return_code


def print_linter_result(filepath: Path, linter_result: List[Dict[str, Any]]):
    """Print any discovered issues."""
    if len(linter_result) > 0:
        print(f"checkcode found issues in {filepath}:")
        for issue in linter_result:
            line_number: int = issue["line"]
            column_range: List[int] = issue["column"]
            message: str = issue["message"]
            print(f"\tLine {line_number} (Column [{column_range[0]}-{column_range[1]}]): {message}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Parse commandline arguments and validate the supplied files through MATLAB's checkcode function."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--matlab-path",
        action="store",
        type=str,
        default="",
        help="File path to the MATLAB executable.",
    )

    parser.add_argument(
        "--matlab-version",
        action="store",
        type=str,
        default=None,
        help="The version of MATLAB to use.",
    )

    parser.add_argument(
        "--matlab-release-name",
        action="store",
        type=str,
        default=None,
        help="The release name of MATLAB to use.",
    )
    parser.add_argument(
        "--treat-warning-as-error", action="store_true", help="Treat all warnings as errors"
    )

    parser.add_argument(
        "--enable-modified-cyclomaticity",
        action="store_true",
        help="Enable the display of modified cyclomaticity complexity calculation for each file.",
    )
    parser.add_argument(
        "--enable-cyclomaticity",
        action="store_true",
        help="Enable the display of McCabe cyclomaticity calculation complexity.",
    )
    parser.add_argument(
        "--ignore-ok-pragmas", action="store_true", help="Ignore %#ok checkcode suppression pragmas"
    )
    parser.add_argument(
        "--checkcode-config-file",
        action="store",
        type=str,
        default="",
        help="File path to a checkcode config file.",
    )
    parser.add_argument(
        "--use-default-checkcode-config",
        action="store_true",
        help="Ignore any checkcode config file and use factory default settings",
    )
    parser.add_argument("filepaths", nargs="*", type=Path)
    args = parser.parse_args(argv)

    filepaths: List[Path] = []
    if args.filenames:
        filepaths = args.filenames

    potential_matlab_path: Optional[Path] = extract_file_path_option(args.matlab_path)

    matlab_version: Optional[str] = args.matlab_version

    matlab_release_name: Optional[str] = args.matlab_release_name

    checkcode_config_file: Optional[Path] = extract_file_path_option(args.checkcode_config_file)

    enable_mod_cyc: bool = args.enable_modified_cyclomaticity
    enable_cyc: bool = args.enable_cyclomaticity
    ignore_ok_pragmas: bool = args.ignore_ok_pragmas
    fail_warnings: bool = args.treat_warning_as_error
    use_factory_default: bool = args.use_default_checkcode_config

    matlab_path, return_code = find_matlab(
        potential_matlab_path=potential_matlab_path,
        matlab_version=matlab_version,
        matlab_release_name=matlab_release_name,
    )

    if ReturnCode.FAIL == return_code or matlab_path is None or not matlab_path.exists():
        print("Unable to find MATLAB")
        return return_code
    else:
        return validate_matlab(
            matlab_path,
            filepaths,
            fail_warnings,
            enable_cyc,
            enable_mod_cyc,
            ignore_ok_pragmas,
            use_factory_default,
            checkcode_config_file,
        )


if __name__ == "__main__":
    SystemExit(main())
