from tempfile import TemporaryDirectory

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
        matlab_folder_path,
        handle_list,
        enable_cyc,
        enable_mod_cyc,
        ignore_ok_pragmas,
        fail_warnings,
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
