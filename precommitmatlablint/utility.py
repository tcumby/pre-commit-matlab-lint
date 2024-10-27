from pathlib import Path
from typing import List, Optional


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

    level_option = "'-m0'" if fail_warnings else "'-m2'"
    command: List = [level_option, "'-id'", "'-struct'"]
    if enable_cyc:
        command.append("'-cyc'")

    if enable_mod_cyc:
        command.append("'-modcyc'")

    if ignore_ok_pragmas:
        command.append("'-notok'")

    if use_factory_default:
        command.append("'-config=factory'")
    elif checkcode_config_file:
        command.append(f"'-config={str(checkcode_config_file)}'")

    command = command + file_list
    command_string: str = ", ".join(command)
    return f"clc;disp(jsonencode(checkcode({command_string})));quit;"
