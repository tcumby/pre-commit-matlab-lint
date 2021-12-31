import re
from pathlib import Path

import pytest  # noqa: F401 # pylint: disable=unused-import

from precommitmatlablint.find_matlab import (
    get_matlab_installs,
    MatlabHandle,
)


@pytest.fixture(scope="module")
def data_folder_path(request) -> Path:
    root_dir = Path(__file__).parent
    return root_dir / "data"


class TestFindMatlab:
    def test_get_matlab_installs(self):
        install_list = get_matlab_installs()
        assert len(install_list) > 0

        # Check that what is returned are all folder paths
        assert all([s.is_dir() and s.exists() for s in install_list])

        # Check that there is a MATLAB executable in the correct sub-directory relative to the returned folder path
        assert all(
            [Path(s, "bin", MatlabHandle.get_matlab_exe_name()).exists for s in install_list]
        )

    def test_query_matlab_version(self):
        install_list = get_matlab_installs()
        assert len(install_list) > 0

        this_matlab_home = install_list[0]
        matlab_exe: Path = this_matlab_home / "bin" / MatlabHandle.get_matlab_exe_name()
        handle = MatlabHandle(home_path=this_matlab_home, exe_path=matlab_exe)
        assert handle.is_initialized is True
        version, release, return_code = handle.query_version()
        assert len(version) > 0
        match = re.match(r"\d+\.\d+", version)
        assert match is not None

    # def test_find_matlab_version(self):
    #     install_list = get_matlab_installs()
    #     assert len(install_list) > 0
    #
    #     this_matlab_home = install_list[0]
    #     matlab_exe: Path = this_matlab_home / "bin" / get_matlab_exe_name()
    #     expected_version = query_matlab_version(matlab_exe)
    #
    #     found_matlab = find_matlab_version(expected_version, install_list, handle_list)
    #     actual_version = query_matlab_version(found_matlab)
    #     assert expected_version == actual_version

    # def test_find_matlab_release(self):
    #     install_list = get_matlab_installs()
    #     assert len(install_list) > 0
    #
    #     this_matlab_home = install_list[0]
    #     matlab_exe: Path = this_matlab_home / "bin" / get_matlab_exe_name()
    #     expected_release = query_matlab_version(matlab_exe)
    #
    #     match = re.match(r"R\d+\w", this_matlab_home.stem)
    #     assert match is not None
    #     release_name = match.string
    #
    #     found_matlab = find_matlab_release(release_name, install_list, handle_list)
    #     assert found_matlab is not None
    #
    #     actual_version = query_matlab_version(found_matlab)
    #     assert expected_release == actual_version

    # def test_find_matlab_with_release(self):
    #     install_list = get_matlab_installs()
    #     assert len(install_list) > 0
    #
    #     this_matlab_home = install_list[0]
    #     matlab_exe: Path = this_matlab_home / "bin" / get_matlab_exe_name()
    #     expected_release = query_matlab_version(matlab_exe)
    #     match = re.match(r"R\d+\w", this_matlab_home.stem)
    #     assert match is not None
    #     release_name = match.string
    #
    #     found_matlab, return_code = find_matlab(matlab_release_name=release_name)
    #     assert found_matlab is not None
    #     assert return_code == ReturnCode.OK
    #
    #     actual_version = query_matlab_version(found_matlab)
    #     assert expected_release == actual_version

    # def test_find_matlab_with_version(self):
    #     install_list = get_matlab_installs()
    #     assert len(install_list) > 0
    #
    #     this_matlab_home = install_list[0]
    #     matlab_exe: Path = this_matlab_home / "bin" / get_matlab_exe_name()
    #     expected_version = query_matlab_version(matlab_exe)
    #
    #     found_matlab, return_code = find_matlab(matlab_version=expected_version)
    #     assert found_matlab is not None
    #     assert return_code == ReturnCode.OK
    #
    #     actual_version = query_matlab_version(found_matlab)
    #     assert expected_version == actual_version

    # def test_find_matlab_with_path(self):
    #     install_list = get_matlab_installs()
    #     assert len(install_list) > 0
    #
    #     this_matlab_home = install_list[0]
    #     matlab_exe: Path = this_matlab_home / "bin" / get_matlab_exe_name()
    #     expected_version = query_matlab_version(matlab_exe)
    #
    #     found_matlab, return_code = find_matlab(matlab_home_path=matlab_exe)
    #     assert found_matlab is not None
    #     assert return_code == ReturnCode.OK
    #
    #     actual_version = query_matlab_version(found_matlab)
    #     assert expected_version == actual_version

    # def test_find_matlab_with_fake_path(self):
    #     fake_matlab = Path().absolute() / "bin" / get_matlab_exe_name()
    #     found_matlab, return_code = find_matlab(matlab_home_path=fake_matlab)
    #     assert found_matlab is None
    #     assert return_code == ReturnCode.FAIL

    # def test_fake_version_find_matlab_version(self):
    #     install_list = get_matlab_installs()
    #     assert len(install_list) > 0
    #
    #     fake_version = "0.00"
    #     found_matlab = find_matlab_version(fake_version, install_list, handle_list)
    #
    #     assert found_matlab is None

    # def test_fake_release_find_matlab_release(self):
    #     install_list = get_matlab_installs()
    #     assert len(install_list) > 0
    #
    #     fake_release = "R0000a"
    #     found_matlab = find_matlab_release(fake_release, install_list, handle_list)
    #
    #     assert found_matlab is None

    # def test_fake_version_find_matlab(self):
    #     install_list = get_matlab_installs()
    #     assert len(install_list) > 0
    #
    #     fake_version = "0.00"
    #     found_matlab, return_code = find_matlab(matlab_version=fake_version)
    #
    #     assert found_matlab is None
    #     assert return_code == ReturnCode.FAIL
    #
    # def test_fake_release_find_matlab(self):
    #     install_list = get_matlab_installs()
    #     assert len(install_list) > 0
    #
    #     fake_release = "R0000a"
    #     found_matlab, return_code = find_matlab(matlab_release_name=fake_release)
    #
    #     assert found_matlab is None
    #     assert return_code == ReturnCode.FAIL

    def test_read_version_info(self, data_folder_path: Path):
        version_info_file: Path = data_folder_path / "version_info" / "VersionInfo.xml"

        assert version_info_file.exists()

        version, release = MatlabHandle.read_version_info(version_info_file)

        assert version == "1.2.3.4"
        assert release == "R1234a"
