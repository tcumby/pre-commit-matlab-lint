import re
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest  # noqa: F401 # pylint: disable=unused-import

from precommitmatlablint.find_matlab import (
    get_matlab_installs,
    MatlabHandle,
    MatlabHandleList,
    find_matlab,
)
from precommitmatlablint.return_code import ReturnCode


@pytest.fixture(scope="module")
def data_folder_path(request) -> Path:
    root_dir = Path(__file__).parent
    return root_dir / "data"


@pytest.fixture(scope="module")
def cleanup_default_cache_file(request):
    handle_list = MatlabHandleList()
    handle_list.cache_file.unlink(missing_ok=True)
    yield None
    handle_list.cache_file.unlink(missing_ok=True)


@pytest.fixture(scope="module")
def handle_list(request):
    with TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "cache_file.yaml"
        handle_list = MatlabHandleList(cache_file)
        yield handle_list


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

    def test_refresh(self):
        install_list = get_matlab_installs()
        assert len(install_list) > 0

        this_matlab_home = install_list[0]
        matlab_exe: Path = MatlabHandle.construct_exe_path(this_matlab_home)
        handle = MatlabHandle(home_path=this_matlab_home, exe_path=matlab_exe)
        assert handle.is_initialized()

        # save the current values
        expected_version = handle.version
        expected_release = handle.release
        expected_checksum = handle.checksum

        # change the values
        handle.version = ""
        handle.release = ""
        handle.checksum = ""

        handle.refresh()

        assert expected_checksum == handle.checksum
        assert expected_version == handle.version
        assert expected_release == handle.release

    def test_cache_file_creation(self, handle_list):
        install_list = get_matlab_installs()
        assert len(install_list) > 0
        handle_list.update(install_list)
        handle_list.save()

        assert handle_list.cache_file.exists()

        handle_list2 = MatlabHandleList(handle_list.cache_file)
        handle_list2.load()
        assert len(handle_list2) > 0

    def test_handle_list_prune(self, handle_list):
        install_list = get_matlab_installs()
        assert len(install_list) > 0
        handle_list.update(install_list)

        expected_length = len(handle_list)

        # create a bogus MatlabHandle
        fake_home = Path().absolute()
        fake_exe = MatlabHandle.construct_exe_path(fake_home)
        fake_handle = MatlabHandle(home_path=fake_home, exe_path=fake_exe)

        handle_list.append(fake_handle)

        assert len(handle_list) > expected_length

        handle_list.prune()

        assert expected_length == len(handle_list)
        assert handle_list.has_changes

    def test_query_matlab_version(self):
        install_list = get_matlab_installs()
        assert len(install_list) > 0

        this_matlab_home = install_list[0]
        matlab_exe: Path = MatlabHandle.construct_exe_path(this_matlab_home)
        handle = MatlabHandle(home_path=this_matlab_home, exe_path=matlab_exe)
        assert handle.is_initialized() is True
        version, release, return_code = handle.query_version()
        assert len(version) > 0
        match = re.match(r"\d+\.\d+", version)
        assert match is not None

    def test_find_matlab_version(self, handle_list):
        install_list = get_matlab_installs()
        assert len(install_list) > 0
        handle_list.update(install_list)

        this_matlab_home = install_list[0]
        version_info_file = this_matlab_home / "VersionInfo.xml"
        expected_version, expected_release = MatlabHandle.read_version_info(version_info_file)

        matlab_handle = handle_list.find_version(expected_version)
        assert matlab_handle is not None

        assert expected_version == matlab_handle.version
        assert expected_release == matlab_handle.release

    def test_find_matlab_release(self, handle_list):
        install_list = get_matlab_installs()
        assert len(install_list) > 0
        handle_list.update(install_list)

        this_matlab_home = install_list[0]
        version_info_file = this_matlab_home / "VersionInfo.xml"
        expected_version, expected_release = MatlabHandle.read_version_info(version_info_file)

        matlab_handle = handle_list.find_release(expected_release)
        assert matlab_handle is not None

        assert expected_version == matlab_handle.version
        assert expected_release == matlab_handle.release

    def test_find_matlab_with_release(self, cleanup_default_cache_file, handle_list):
        install_list = get_matlab_installs()
        assert len(install_list) > 0
        handle_list.update(install_list)

        this_matlab_home = install_list[0]
        version_info_file = this_matlab_home / "VersionInfo.xml"
        expected_version, expected_release = MatlabHandle.read_version_info(version_info_file)

        found_matlab, return_code = find_matlab(matlab_release_name=expected_release)
        assert found_matlab is not None
        assert return_code == ReturnCode.OK

        assert expected_release == found_matlab.release
        assert expected_version == found_matlab.version

    def test_find_matlab_with_version(self, cleanup_default_cache_file, handle_list):
        install_list = get_matlab_installs()
        assert len(install_list) > 0
        handle_list.update(install_list)

        this_matlab_home = install_list[0]
        version_info_file = this_matlab_home / "VersionInfo.xml"
        expected_version, expected_release = MatlabHandle.read_version_info(version_info_file)

        found_matlab, return_code = find_matlab(matlab_version=expected_version)
        assert found_matlab is not None
        assert return_code == ReturnCode.OK

        assert expected_version == found_matlab.version

    def test_find_matlab_with_path(self, cleanup_default_cache_file, handle_list):
        install_list = get_matlab_installs()
        assert len(install_list) > 0
        handle_list.update(install_list)

        this_matlab_home = install_list[0]
        version_info_file = this_matlab_home / "VersionInfo.xml"
        expected_version, expected_release = MatlabHandle.read_version_info(version_info_file)

        found_matlab, return_code = find_matlab(matlab_home_path=this_matlab_home)
        assert found_matlab is not None
        assert return_code == ReturnCode.OK

        assert expected_version == found_matlab.version

    def test_find_matlab_with_fake_path(self, cleanup_default_cache_file):
        fake_matlab = Path().absolute()
        found_matlab, return_code = find_matlab(matlab_home_path=fake_matlab)
        assert found_matlab is None
        assert return_code == ReturnCode.FAIL

    def test_fake_version_find_matlab_version(self, cleanup_default_cache_file, handle_list):
        install_list = get_matlab_installs()
        assert len(install_list) > 0
        handle_list.update(install_list)

        fake_version = "0.00"
        found_matlab = handle_list.find_version(fake_version)

        assert found_matlab is None

    def test_fake_release_find_matlab_release(self, handle_list):
        install_list = get_matlab_installs()
        assert len(install_list) > 0
        handle_list.update(install_list)

        fake_release = "R0000a"
        found_matlab = handle_list.find_release(fake_release)

        assert found_matlab is None

    def test_fake_version_find_matlab(self, cleanup_default_cache_file):
        fake_version = "0.00"
        found_matlab, return_code = find_matlab(matlab_version=fake_version)

        assert found_matlab is None
        assert return_code == ReturnCode.FAIL

    def test_fake_release_find_matlab(self, cleanup_default_cache_file):
        fake_release = "R0000a"
        found_matlab, return_code = find_matlab(matlab_release_name=fake_release)

        assert found_matlab is None
        assert return_code == ReturnCode.FAIL

    def test_read_version_info(self, data_folder_path: Path):
        version_info_file: Path = data_folder_path / "version_info" / "VersionInfo.xml"

        assert version_info_file.exists()

        version, release = MatlabHandle.read_version_info(version_info_file)

        assert version == "1.2.3.4"
        assert release == "R1234a"
