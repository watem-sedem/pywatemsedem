(development)=

# Development guidelines

Want to contribute code or functionalities to the `pyws` package? Great and welcome on board!

We use a number of development tools to support us in improving the code quality. No magic bullet or free
lunch, but just a set of tools as any craftsman has tools to support him/her doing a better job.

For development purposes using conda, make sure to first run `pip install -e .[develop]` environment
to prepare the development environment and install all development tools. (When using `tox -e dev` this
is already done).

When starting on the development of the `pyws` package, makes sure to be familiar with the following tools. Do
not hesitate to ask the other developers when having trouble using these tools.

Please notice, all users and contributors are expected to be __open, considerate, reasonable, and respectful__.
When in doubt, [Python Software Foundation's Code of Conduct](https://www.python.org/psf/conduct/)
is a good reference in terms of behavior guidelines.

## Tox

We use [tox](https://tox.wiki) to automate and standardize out package development in Python. Tox allows us to define
package maintenance and developing actions using a common CLI entrypoint, i.e. `tox -e <COMMAND>`. The following sections
will introduce the commands you need to develop and maintain the package.

To get an overview of all available tox commands in this project, run:

```
tox -av
```

:::{note}
Sometimes tox misses out when new dependencies are added. If you find any problems with missing dependencies
when running a command with tox, try to recreate the `tox` environment by adding the `-r` flag to the command
(e.g. `tox -e docs` becomes `tox -e -r docs`).
:::

## Pre-commit hooks

To ensure a more common code formatting/style, apply a number of code quality checks and limit the git diff, make sure to
install the [pre-commit] hooks. The required dependencies are included in the development requirements installed
when running `pip install -e .[develop]`.

:::{warning}
Install the `pre-commit` hooks before your first git commit to the package!
:::

```
pre-commit install
```

on the main level of the package (`pyws` folder, location where the file `.pre-commit-config.yaml` is located)

If you just want to run the hooks on your files to see the effect (not during a git commit),
you can use the available tox command at any time:

```
tox -e pre-commit
```

It is a good idea to update the hooks to the latest version:

```
pre-commit autoupdate
```

To check the code quality of Python projects, [flake8](https://pypi.org/project/flake8/) is used as part of
the pre-commit hook. Flake8 wraps and  combines pep8, pyflakes, and other tools to check the code quality of Python
projects. It also allows to add extensions for additional code quality checks. At the moment,
[flake8-logging](https://github.com/adamchainz/flake8-logging)  checks for issues using the standard library
logging module.

:::{note}
Some of the pre-commit hooks are added as opt-in and commented-out by default. Check the file and activate additional
sections when relevant for your project.
:::

## Unit testing with pytest

Run the test suite using the `pytest` package, from within the main package folder (`pyws`):

```
pytest
```

Or using tox (i.e. in a separate environment)

```
tox -e py
```

You will receive information on the test status and the test coverage of the unit tests. The `-e py` is to make sure the
unit tests only run in the currently active python environment.

## Documentation with sphinx

Documentation uses [Sphinx](https://www.sphinx-doc.org/en/master/) as the documentation compiler. This means that the
docs are kept in the same repository as the project code, and that any documentation update is done in the same
way was a code contribution.

Build the documentation locally with [Sphinx](https://www.sphinx-doc.org/en/master/):

```
tox -e docs
```

which will create the docs in the `docs/_build/html` folder. The `docs/_build` directory itself is
left out of version control (and we rather keep it as such ;-)).

In order to get nicely rendered online documentation, we use the `numpydoc` format. Check the documentation of the
[numpydoc](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard) for the detailed specification.
As a minimum, provide the following sections for any public method/class: `summary`, `description`, `parameters`,
`returns` and `examples`.

:::{note}
When stuck with the documentation rendering locally, use the `tox -e clean` command to remove the directories
created by Sphinx (as well as local build artifacts).
:::

## Drone CI

Apart from these tools you can run locally, we use drone continuous integration to run these checks also
on our servers. See <https://drone.fluves.net>/fluves/pyws for the results.

The drone provides reports that can be checked:

- The docstring coverage of the functions, see the `report docstring` step of the [drone output](https://drone.fluves.net/fluves/pyws).
- An [interactive unit test coverage report](https://coverage.fluves.net/pyws/) with the unit test covered code for each of the files.

For more information on the initial setup of the CI in a project, see the `README.md` file in the `ci` subfolder.

## Managing package dependencies

We use [pip-tools](https://github.com/jazzband/pip-tools) to manage and update the package dependencies and to pin the dependencies.
**You should therefore refrain from manually editing the `requirements.txt` file** and instead use the procedure below.
Don't hesitate to have a look at [pip tools documentation](https://github.com/jazzband/pip-tools) for more information.

### Adding dependencies

1. Make sure to add the necessary package to the `options` > `install_requires` section of the `setup.cfg` file.
2. Run `pip-compile` to update the pinned dependencies in `requirements.txt` file (based on the content of `setup.cfg`):

```bash
pip-compile > requirements.txt
```

3. Install the new dependencies in the development environment:

```bash
pip install -e .[develop]
```

### Drone and dependency pinning

By default, Drone will run the unit tests twice, once by compiling the most recent dependencies (`tox`) and once
with the dependencies pinned in `requirements.txt`.

:::{warning}
The pinned dependencies are used for deployment and running services, and therefore **should always work**.
:::

To run the unit tests with the pinned dependencies locally, use the `pinned` tox command:

```
tox -e pinned
```

### Security updates with renovatebot

We use [renovatebot](https://docs.renovatebot.com/) to track the package dependencies on __security risks__ of outdated
packages. To do so, renovatebot will (auto)-create a Pull Request to bump the dependency. These updates should be
handled asap. Check if all unit tests are still running and adjust if required.

See the [renovate docs](https://docs.renovatebot.com/key-concepts/how-renovate-works/) for more
information on how renovatebot works.

:::{warning}
Renovatebot will create an initial Pull request to setup the configuration. Make sure to merge this PR!
:::

## Package release

The CI will create sdist/wheels and publish these to gitea when git tags are added, making releasing
straight forward. In order to publish a new release, the following steps:

- `git checkout master, git pull origin master` (work on up to date master branch)
- Update the `CHANGELOG.rst` with the changes for this new release
- `git commit -m 'Update changelog for release X.X.X' CHANGELOG.rst`
- `git push origin master`
- Add git tags: `git tag X.X.X`
- Push the git tags: `git push X.X.X`

When all test pass, drone CI will publish a pre-release on gitea. To convert this to release:

- On the release page of the repository, draft a new release using the latest git tag
- Copy past the changes from the changelog in the dialog and publish release
