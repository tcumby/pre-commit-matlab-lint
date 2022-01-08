from tempfile import TemporaryDirectory
from typing import List

import pytest  # noqa: F401 # pylint: disable=unused-import
from pathlib import Path

from precommitmatlablint.find_matlab import MatlabHandleList, get_matlab_installs, MatlabHandle
from precommitmatlablint.lint_matlab import validate_matlab
from precommitmatlablint.return_code import ReturnCode


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


class TestLintMatlab:
    @pytest.mark.parametrize("enable_cyc", [True, False])
    @pytest.mark.parametrize("enable_mod_cyc", [True, False])
    @pytest.mark.parametrize("ignore_ok_pragmas", [True, False])
    @pytest.mark.parametrize("fail_warnings", [True, False])
    def test_clean_function(
        self,
        matlab_folder_path: Path,
        handle_list,
        enable_cyc: bool,
        enable_mod_cyc: bool,
        ignore_ok_pragmas: bool,
        fail_warnings: bool,
    ):
        test_file = matlab_folder_path / "clean_function.m"
        assert test_file.exists()

        install_list = get_matlab_installs()
        assert len(install_list) > 0

        this_matlab_home = install_list[0]
        matlab_exe: Path = MatlabHandle.construct_exe_path(this_matlab_home)
        handle = MatlabHandle(home_path=this_matlab_home, exe_path=matlab_exe)
        assert handle.is_initialized()

        return_code: ReturnCode = validate_matlab(
            matlab_handle=handle,
            filepaths=[test_file],
            fail_warnings=fail_warnings,
            enable_cyc=enable_cyc,
            enable_mod_cyc=enable_mod_cyc,
            ignore_ok_pragmas=ignore_ok_pragmas,
            use_factory_default=False,
        )

        assert ReturnCode.OK == return_code

    @pytest.mark.parametrize("enable_cyc", [True, False])
    @pytest.mark.parametrize("enable_mod_cyc", [True, False])
    @pytest.mark.parametrize("ignore_ok_pragmas", [True, False])
    @pytest.mark.parametrize("fail_warnings", [True, False])
    def test_clean_function_multiple_files(
        self,
        matlab_folder_path: Path,
        handle_list,
        enable_cyc: bool,
        enable_mod_cyc: bool,
        ignore_ok_pragmas: bool,
        fail_warnings: bool,
    ):
        test_file = matlab_folder_path / "clean_function.m"
        assert test_file.exists()

        install_list = get_matlab_installs()
        assert len(install_list) > 0

        this_matlab_home = install_list[0]
        matlab_exe: Path = MatlabHandle.construct_exe_path(this_matlab_home)
        handle = MatlabHandle(home_path=this_matlab_home, exe_path=matlab_exe)
        assert handle.is_initialized()

        return_code: ReturnCode = validate_matlab(
            matlab_handle=handle,
            filepaths=[test_file] * 10,
            fail_warnings=fail_warnings,
            enable_cyc=enable_cyc,
            enable_mod_cyc=enable_mod_cyc,
            ignore_ok_pragmas=ignore_ok_pragmas,
            use_factory_default=False,
        )

        assert ReturnCode.OK == return_code

    @pytest.mark.parametrize("enable_cyc", [True, False])
    @pytest.mark.parametrize("enable_mod_cyc", [True, False])
    @pytest.mark.parametrize("ignore_ok_pragmas", [True, False])
    @pytest.mark.parametrize("fail_warnings", [True, False])
    def test_invalid_char(
        self,
        matlab_folder_path: Path,
        handle_list,
        enable_cyc: bool,
        enable_mod_cyc: bool,
        ignore_ok_pragmas: bool,
        fail_warnings: bool,
    ):
        test_file = matlab_folder_path / "invalid_char.m"
        assert test_file.exists()

        install_list = get_matlab_installs()
        assert len(install_list) > 0

        this_matlab_home = install_list[0]
        matlab_exe: Path = MatlabHandle.construct_exe_path(this_matlab_home)
        handle = MatlabHandle(home_path=this_matlab_home, exe_path=matlab_exe)
        assert handle.is_initialized()

        return_code: ReturnCode = validate_matlab(
            matlab_handle=handle,
            filepaths=[test_file],
            fail_warnings=fail_warnings,
            enable_cyc=enable_cyc,
            enable_mod_cyc=enable_mod_cyc,
            ignore_ok_pragmas=ignore_ok_pragmas,
            use_factory_default=False,
        )

        assert ReturnCode.FAIL == return_code

    @pytest.mark.parametrize("enable_cyc", [True, False])
    @pytest.mark.parametrize("enable_mod_cyc", [True, False])
    @pytest.mark.parametrize("ignore_ok_pragmas", [True, False])
    @pytest.mark.parametrize("fail_warnings", [True, False])
    def test_invalid_char_multiple_files(
        self,
        matlab_folder_path: Path,
        handle_list,
        enable_cyc: bool,
        enable_mod_cyc: bool,
        ignore_ok_pragmas: bool,
        fail_warnings: bool,
    ):
        test_file = matlab_folder_path / "invalid_char.m"
        assert test_file.exists()

        install_list = get_matlab_installs()
        assert len(install_list) > 0

        this_matlab_home = install_list[0]
        matlab_exe: Path = MatlabHandle.construct_exe_path(this_matlab_home)
        handle = MatlabHandle(home_path=this_matlab_home, exe_path=matlab_exe)
        assert handle.is_initialized()

        return_code: ReturnCode = validate_matlab(
            matlab_handle=handle,
            filepaths=[test_file] * 10,
            fail_warnings=fail_warnings,
            enable_cyc=enable_cyc,
            enable_mod_cyc=enable_mod_cyc,
            ignore_ok_pragmas=ignore_ok_pragmas,
            use_factory_default=False,
        )

        assert ReturnCode.FAIL == return_code

    @pytest.mark.parametrize("enable_cyc", [True, False])
    @pytest.mark.parametrize("enable_mod_cyc", [True, False])
    @pytest.mark.parametrize("ignore_ok_pragmas", [True, False])
    @pytest.mark.parametrize("fail_warnings", [True, False])
    @pytest.mark.parametrize(
        "filename_list",
        [
            ["invalid_char.m", "clean_function.m", "clean_function.m"],
            ["clean_function.m", "invalid_char.m", "clean_function.m"],
            ["clean_function.m", "clean_function.m", "invalid_char.m"],
        ],
    )
    def one_bad_file(
        self,
        matlab_folder_path: Path,
        handle_list,
        enable_cyc: bool,
        enable_mod_cyc: bool,
        ignore_ok_pragmas: bool,
        fail_warnings: bool,
        filename_list: List[str],
    ):

        assert matlab_folder_path.exists()
        filepaths: List[Path] = [matlab_folder_path / s for s in filename_list]
        assert all([s.exists() for s in filepaths])

        install_list = get_matlab_installs()
        assert len(install_list) > 0

        this_matlab_home = install_list[0]
        matlab_exe: Path = MatlabHandle.construct_exe_path(this_matlab_home)
        handle = MatlabHandle(home_path=this_matlab_home, exe_path=matlab_exe)
        assert handle.is_initialized()

        return_code: ReturnCode = validate_matlab(
            matlab_handle=handle,
            filepaths=filepaths,
            fail_warnings=fail_warnings,
            enable_cyc=enable_cyc,
            enable_mod_cyc=enable_mod_cyc,
            ignore_ok_pragmas=ignore_ok_pragmas,
            use_factory_default=False,
        )

        assert ReturnCode.FAIL == return_code

    @pytest.mark.parametrize("enable_cyc", [True, False])
    @pytest.mark.parametrize("enable_mod_cyc", [True, False])
    @pytest.mark.parametrize("ignore_ok_pragmas", [True, False])
    @pytest.mark.parametrize("fail_warnings", [True, False])
    @pytest.mark.parametrize(
        "filename_list",
        [
            ["invalid_char.m", "invalid_char.m", "clean_function.m"],
            ["clean_function.m", "invalid_char.m", "invalid_char.m"],
            ["invalid_char.m", "clean_function.m", "invalid_char.m"],
        ],
    )
    def one_good_file(
        self,
        matlab_folder_path: Path,
        handle_list,
        enable_cyc: bool,
        enable_mod_cyc: bool,
        ignore_ok_pragmas: bool,
        fail_warnings: bool,
        filename_list: List[str],
    ):
        assert matlab_folder_path.exists()
        filepaths: List[Path] = [matlab_folder_path / s for s in filename_list]
        assert all([s.exists() for s in filepaths])

        install_list = get_matlab_installs()
        assert len(install_list) > 0

        this_matlab_home = install_list[0]
        matlab_exe: Path = MatlabHandle.construct_exe_path(this_matlab_home)
        handle = MatlabHandle(home_path=this_matlab_home, exe_path=matlab_exe)
        assert handle.is_initialized()

        return_code: ReturnCode = validate_matlab(
            matlab_handle=handle,
            filepaths=filepaths,
            fail_warnings=fail_warnings,
            enable_cyc=enable_cyc,
            enable_mod_cyc=enable_mod_cyc,
            ignore_ok_pragmas=ignore_ok_pragmas,
            use_factory_default=False,
        )

        assert ReturnCode.FAIL == return_code
