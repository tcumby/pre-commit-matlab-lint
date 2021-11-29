# Contributing

Pre-commit-matlab-lint is licensed under the
[MIT License](https://spdx.org/licenses/MIT.html).
[New issues](https://github.com/ty.cumby/pre-commit-matlab-lint/issues) and pull requests are welcome.
Feel free to direct a question to the authors by creating an [issue with the _question_ tag](https://github.com/ty.cumby/pre-commit-matlab-lint/issues/new?assignees=&labels=kind%3A+question&template=question.md).
Contributors are asked to abide by both the [GitHub community guidelines](https://docs.github.com/en/github/site-policy/github-community-guidelines)
and the [Contributor Code of Conduct, version 2.0](https://www.contributor-covenant.org/version/2/0/code_of_conduct/).

#### Pull requests

Please update `CHANGELOG.md` and add your name to the contributors in `pyproject.toml`
so that you’re credited. Run `poetry lock` and `tyrannosaurus sync` to sync metadata.
Feel free to make a draft pull request and solicit feedback from the authors.

#### Publishing a new version

1. Bump the version in `tool.poetry.version` in `pyproject.toml`, following
   [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
2. Run `tyrannosaurus sync` so that the Poetry lock file is up-to-date
   and metadata are synced to pyproject.toml.
3. Create a [new release](https://github.com/dmyersturnbull/tyrannosaurus/releases/new)
   with both the name and tag set to something like `v1.4.13` (keep the _v_).
4. An hour later, check that the *publish on release creation*
   [workflow](https://github.com/ty.cumby/pre-commit-matlab-lint/actions) passes
   and that the PyPi, Docker Hub, and GitHub Package versions are updated as shown in the
   shields on the readme.
5. Check for a pull request from regro-cf-autotick-bot on the
   [feedstock](https://github.com/conda-forge/pre-commit-matlab-lint-feedstock).
   *If you have not changed the dependencies or version ranges*, go ahead and merge it.
   Otherwise, [update the recipe](
   https://github.com/conda-forge/pre-commit-matlab-lint-feedstock/edit/master/recipe/meta.yaml)
   with those changes under `run:`, also updating `{% set version` and `sha256` with the
   changes from regro-cf-autotick-bot. You can alternatively re-run `tyrannosaurus recipe`
   to generate a new recipe and copy it to the feedstock.
7. Twenty minutes later, verify that the Conda-Forge shield is updated.
