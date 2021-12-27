from pathlib import Path

import pytest  # noqa: F401 # pylint: disable=unused-import

from precommitmatlablint.find_matlab import get_matlab_exe_name, get_matlab_installs


class TestFindMatlab:
    def test_get_matlab_installs(self):
        install_list = get_matlab_installs()
        assert len(install_list) > 0

        # Check that what is returned are all folder paths
        assert all([s.is_dir() and s.exists() for s in install_list])

        # Check that there is a MATLAB executable in the correct sub-directory relative to the returned folder path
        assert all([Path(s, "bin", get_matlab_exe_name()).exists for s in install_list])
