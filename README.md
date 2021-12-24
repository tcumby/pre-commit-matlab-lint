# pre-commit-matlab-lint

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![](https://img.shields.io/badge/python-3.8%2B-blue)]()
[![Version on GitHub](https://img.shields.io/github/v/release/tcumby/pre-commit-matlab-lint?include_prereleases&label=GitHub)](https://github.com/tcumby/pre-commit-matlab-lint/releases)
[![CodeFactor](https://www.codefactor.io/repository/github/dmyersturnbull/tyrannosaurus/badge)](https://www.codefactor.io/repository/github/dmyersturnbull/tyrannosaurus)
[![Created with Tyrannosaurus](https://img.shields.io/badge/Created_with-Tyrannosaurus-0000ff.svg)](https://github.com/dmyersturnbull/tyrannosaurus)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Security Status](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A [pre-commit hook](https://pre-commit.com/) for validating MATLAB code.

## Available Hook

### lint-matlab

Validate MATLAB files by analyzing them with MATLAB's [checkcode](https://www.mathworks.com/help/matlab/ref/checkcode.html) function.

In order to use this hook, MATLAB must be installed and registered. There are three ways to specify which MATLAB instance should be used:

- Use `--matlab_path=PATH` to supply the full path to a MATLAB executable
- Use `--matlab_version=VERSION` to specify a MATLAB version to locate (e.g. "9.10")
- Use `--matlab_release_name=NAME` to specify a MATLAB release to locate (e.g. "R2021a")

Other options:

- Use `--treat_warning_as_error` to fail on linter warnings, in addition to linter errors.
- Use `--enable_cyclomaticity` to enable McCabe cyclomaticity complexity calculation display for each file.
- Use `--enable_modified_cyclomaticity` to enable modified cyclomaticity complexity calculation display for each file.
- Use `--ignore_ok_pragmas` to ignore `%#ok` checkcode suppression pragmas in files.
- Use `--checkode_config_file=FILE` to specify a settings file. For instructions detail how to create the file, see [Save and Reuse Code Analyzer Message Settings](https://www.mathworks.com/help/matlab/matlab_prog/check-code-for-errors-and-warnings.html#brqxeeu-173).

## Usage with pre-commit

Add this to your `.pre-commit-config.yaml`

```yaml
- repo: https://github.com/tcumby/pre-commit-matlab-lint
  rev: "" # Use the sha / tag you want to point at
  hooks:
    - id: lint-matlab
      args: ["--matlab_release_name=R2021a"]
```

Licensed under the terms of the [MIT License](https://spdx.org/licenses/MIT.html).
[New issues](https://github.com/tcumby/pre-commit-matlab-lint/issues) and pull requests are welcome.
Please refer to the [contributing guide](https://github.com/tcumby/pre-commit-matlab-lint/blob/main/CONTRIBUTING.md)
and [security policy](https://github.com/tcumby/pre-commit-matlab-lint/blob/main/SECURITY.md).
Generated with [Tyrannosaurus](https://github.com/dmyersturnbull/tyrannosaurus).
