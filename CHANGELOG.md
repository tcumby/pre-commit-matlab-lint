# Changelog for pre-commit-matlab-lint

Adheres to [Semantic Versioning 2.0](https://semver.org/spec/v2.0.0.html),
[Keep a Changelog 1.0](https://keepachangelog.com/en/1.0.0/),
and [Conventional Commits 1.0](https://www.conventionalcommits.org/en/v1.0.0/).

## [0.1.0] - 2021-11-28

### Added:

- Stub files.

## [1.0.0] - 2022-01-16

### Added:

- Linting via a detected MATLAB instance is functioning

## [1.0.1] - 2022-02-07

### Added:

- Changed how the file path to the MATLAB executables are constructed
- Changed the MATLAB info cache file to be populated in the user's HOME directory
- Changed the MATLAB info cache file's name to be more easily attributed to this pre-commit hook

## [1.0.2] - 2022-02-07

### Added:

- Minor performance improvement to only interrogate the system for all MATLAB installs if nothing is cached
