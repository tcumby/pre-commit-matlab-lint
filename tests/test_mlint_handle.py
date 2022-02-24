from tempfile import TemporaryDirectory
from typing import List

import pytest  # noqa: F401 # pylint: disable=unused-import
from pathlib import Path

from precommitmatlablint.find_matlab import (
    MatlabHandleList,
    get_matlab_installs,
    MatlabHandle,
    MLintHandle,
    LinterRecord,
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

        linter_records: List[LinterRecord] = mlint_handle.parse_mlint_output(
            stdout=mlint_message, file_list=[test_file]
        )

        assert len(linter_records) == 1

        record = linter_records[0]

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
        linter_records: List[LinterRecord] = mlint_handle.parse_mlint_output(
            stdout=mlint_message, file_list=[test_file]
        )

        assert len(linter_records) == 4
        expected_lines = [3681, 3696, 3757, 3924]
        for idx, record in enumerate(linter_records):
            assert record.line == expected_lines[idx], "Line is incorrect"
            assert record.source_file == test_file, "File is correct"
            assert record.id == "GVMIS", "ID is incorrect"
            assert len(record.columns) == 2, "Columns array is incorrect size"
            assert record.columns[0] == 1, "Column start is incorrect"
            assert record.columns[1] == 6, "Column end is incorrect"
            assert (
                "Global variables are inefficient and make errors difficult to diagnose. Use a function with input variables instead."
                == record.message
            ), "Message is wrong"
