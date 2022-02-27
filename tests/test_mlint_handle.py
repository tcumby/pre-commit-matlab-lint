from tempfile import TemporaryDirectory
from typing import List

import pytest  # noqa: F401 # pylint: disable=unused-import
from pathlib import Path, PureWindowsPath

from precommitmatlablint.find_matlab import (
    MatlabHandleList,
    get_matlab_installs,
    MatlabHandle,
    MLintHandle,
    LinterRecord,
    LinterReport,
)


@pytest.fixture(scope="module")
def matlab_folder_path(request) -> Path:
    root_dir = Path(__file__).parent
    return root_dir / "data" / "matlab"


@pytest.fixture(scope="module")
def handle_list(request):
    with TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "cache_file.yaml"
        handle_list = MatlabHandleList(cache_file)
        yield handle_list


class TestMLintHandle:
    def test_parse_mlint_output(self, matlab_folder_path):
        test_file = matlab_folder_path / "invalid_char.m"
        assert test_file.exists()

        install_list = get_matlab_installs()
        if len(install_list) == 0:
            pytest.skip("No Matlab installations found.")

        this_matlab_home = install_list[0]
        matlab_exe: Path = MatlabHandle.construct_exe_path(this_matlab_home)
        base_matlab_exe: Path = MatlabHandle.construct_base_exe_path(this_matlab_home)
        handle = MatlabHandle(
            home_path=this_matlab_home, exe_path=matlab_exe, base_exe_path=base_matlab_exe
        )
        assert handle.is_initialized()

        mlint_handle: MLintHandle = handle.get_mlint_handle()

        mlint_message = "L 6402 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead."

        linter_reports: List[LinterReport] = mlint_handle.parse_mlint_output(
            stdout=mlint_message, file_list=[test_file]
        )

        assert len(linter_reports) == 1
        assert len(linter_reports[0].records) == 1
        record = linter_reports[0].records[0]

        assert record.line == 6402, "Line is incorrect"
        assert record.id == "GVMIS", "ID is incorrect"
        assert len(record.columns) == 2, "Columns array is incorrect size"
        assert record.columns[0] == 1, "Column start is incorrect"
        assert record.columns[1] == 6, "Column end is incorrect"
        assert (
            "Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead."
            == record.message
        ), "Message is wrong"

    def test_parse_mlint_multiple_output(self, matlab_folder_path):
        test_file = matlab_folder_path / "invalid_char.m"
        assert test_file.exists()

        install_list = get_matlab_installs()
        if len(install_list) == 0:
            pytest.skip("No Matlab installations found.")

        this_matlab_home = install_list[0]
        matlab_exe: Path = MatlabHandle.construct_exe_path(this_matlab_home)
        base_matlab_exe: Path = MatlabHandle.construct_base_exe_path(this_matlab_home)
        handle = MatlabHandle(
            home_path=this_matlab_home, exe_path=matlab_exe, base_exe_path=base_matlab_exe
        )
        assert handle.is_initialized()

        mlint_handle: MLintHandle = handle.get_mlint_handle()

        mlint_message = """L 3681 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
L 3696 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
L 3757 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
L 3924 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead."""
        linter_reports: List[LinterReport] = mlint_handle.parse_mlint_output(
            stdout=mlint_message, file_list=[test_file]
        )
        assert len(linter_reports) == 1
        linter_records: List[LinterRecord] = linter_reports[0].records
        assert len(linter_records) == 4
        expected_lines = [3681, 3696, 3757, 3924]
        for idx, record in enumerate(linter_records):
            assert record.line == expected_lines[idx], "Line is incorrect"
            assert record.id == "GVMIS", "ID is incorrect"
            assert len(record.columns) == 2, "Columns array is incorrect size"
            assert record.columns[0] == 1, "Column start is incorrect"
            assert record.columns[1] == 6, "Column end is incorrect"
            assert (
                "Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead."
                == record.message
            ), "Message is wrong"

    def test_parse_mlint_two_clean_files(self):
        install_list = get_matlab_installs()
        if len(install_list) == 0:
            pytest.skip("No Matlab installations found.")

        this_matlab_home = install_list[0]
        matlab_exe: Path = MatlabHandle.construct_exe_path(this_matlab_home)
        base_matlab_exe: Path = MatlabHandle.construct_base_exe_path(this_matlab_home)
        handle = MatlabHandle(
            home_path=this_matlab_home, exe_path=matlab_exe, base_exe_path=base_matlab_exe
        )
        assert handle.is_initialized()

        mlint_handle: MLintHandle = handle.get_mlint_handle()

        file_list = [
            PureWindowsPath(r"F:\working_copies\imatest\gui\imatest.m"),
            PureWindowsPath(r"F:\working_copies\imatest\gui\plot2svg.m"),
        ]
        mlint_message = r"""========== F:\working_copies\imatest\gui\imatest.m ==========
========== F:\working_copies\imatest\gui\plot2svg.m =========="""

        linter_reports = mlint_handle.parse_mlint_output(stdout=mlint_message, file_list=file_list)

        assert len(linter_reports) == 2
        assert all(not r.has_records() for r in linter_reports)

    def test_parse_mlint_two_dirty_files(self):
        install_list = get_matlab_installs()
        if len(install_list) == 0:
            pytest.skip("No Matlab installations found.")

        this_matlab_home = install_list[0]
        matlab_exe: Path = MatlabHandle.construct_exe_path(this_matlab_home)
        base_matlab_exe: Path = MatlabHandle.construct_base_exe_path(this_matlab_home)
        handle = MatlabHandle(
            home_path=this_matlab_home, exe_path=matlab_exe, base_exe_path=base_matlab_exe
        )
        assert handle.is_initialized()

        mlint_handle: MLintHandle = handle.get_mlint_handle()

        file_list = [
            PureWindowsPath(r"F:\working_copies\imatest\gui\imatest.m"),
            PureWindowsPath(r"F:\working_copies\imatest\gui\plot2svg.m"),
        ]
        mlint_message = r"""========== F:\working_copies\imatest\gui\imatest.m ==========
        L 46 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 81 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 1012 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 1136 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 1219 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 1879 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 1930 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 2030 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 2318 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 2341 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 2432 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 2593 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 2629 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 2986 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 3070 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 3252 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 3297 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 3513 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 3681 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 3696 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 3757 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 3924 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 3942 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 3960 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 3979 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 3997 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 4015 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 4048 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 4261 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 4272 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 4298 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 4582 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 4853 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 4868 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 4943 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 5004 (C 59-65): INUSL: Input argument 'helpUrl' might be unused, although a later one is used. Consider replacing it by ~.
        L 5007 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 5286 (C 15-21): ASGLU: The value assigned here to 'message' appears to be unused. Consider replacing it by ~.
        L 5352 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 5382 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 5805 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 5863 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 6402 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        ========== F:\working_copies\imatest\gui\plot2svg.m ==========
        L 24 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 25 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 720 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 721 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 930 (C 25-26): IFBDUP: This condition has no effect because all blocks in this if statement are identical. Remove the condition or change the code blocks.
        L 1059 (C 25-26): IFBDUP: This condition has no effect because all blocks in this if statement are identical. Remove the condition or change the code blocks.
        L 1129 (C 16-20): ISMAT: When checking if a variable is a matrix consider using ISMATRIX.
        L 1142 (C 16-20): ISMAT: When checking if a variable is a matrix consider using ISMATRIX.
        L 1168 (C 12-16): ISMAT: When checking if a variable is a matrix consider using ISMATRIX.
        L 1278 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 1411 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead.
        L 1579 (C 4-12): ISCLSTR: To support string in addition to cellstr, include a call to 'isstring'.
        L 1580 (C 11-17): DSTRVCT: 'strvcat' is not recommended. With appropriate code changes, use 'char' instead.
        L 1783 (C 1-6): GVMIS: Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead."""

        linter_reports = mlint_handle.parse_mlint_output(stdout=mlint_message, file_list=file_list)

        assert len(linter_reports) == 2
        assert all(r.has_records() for r in linter_reports)

        assert len(linter_reports[0].records) == 43
        assert len(linter_reports[1].records) == 14
