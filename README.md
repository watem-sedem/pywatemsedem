# pyws

[![status_badge](https://drone.fluves.net/api/badges/fluves/pyws/status.svg)](https://drone.fluves.net/fluves/pyws) [![coverage_badge](https://coverage.fluves.net/pyws/coverage.svg)](https://coverage.fluves.net/pyws/)

This is the documentation of **pyws**, a Fluves package to ...

For more information, see the [pyws documentation website](https://docs.fluves.net/pyws/).

## Installation

To use the package, you can either install the latest release from the
[Fluves repo](https://repo.fluves.net/fluves/) using pip OR install the latest version in as development
installation 'from source' to get continuous updates of the current master.

### Latest release

:::{warning}
Installing the latest release using this method is only possible within the
Fluves/Marlinks network. If you are working from outside the network (or VPN), you should have access to git and
install the package from source.
:::

Make sure to setup an environment (venv, conda ...) first with pip available. To install the package,
run the following command:

```
pip install --upgrade pip
pip install --extra-index-url https://repo.fluves.net/fluves --extra-index-url https://repo.fluves.net/marlinks fluves.pyws
```

:::{note}
We use `fluves.pyws` instead of `pyws` to comply to
[PEP423](https://peps.python.org/pep-0423/#private-including-closed-source-projects-use-a-namespace) and use a
_namespaced_ package name according to [PEP420](https://peps.python.org/pep-0420/). The main difference is that you
need to install the package as `fluves.pyws` and the import is from `fluves`,
e.g. `from fluves import pyws`.
:::

When all goes well, you have the package installed and ready to use.

### Install from source

To keep track of the continuous development on the package beyond the major releases, `git clone` the
repository somewhere and install the code from source.

Make sure to setup a new environment using venv (using tox) or conda:

#### Using venv

Run the `dev` tox command, which will create a `venv` with a development install of the package and it will register
the environment as a ipykernel (for usage inside jupyter notebook):

```
tox -e dev
```

## Development

Please check the [development guidelines](development) to start working on the code.

## Project layout

```
├── ci                      <- Docker containers and info used by the drone CI.
├── docs                    <- Directory for Sphinx documentation in md.
├── src
│   └── fluves            <- namespace of the package
|       └── pyws           <- Actual Python package where the main functionality goes.
├── tests                   <- Unit tests which can be run with `tox`.
├── .coveragerc             <- Configuration for coverage reports of unit tests.
├── .drone.yml              <- Configuration for Drone CI/CD configuration.
├── .gitignore              <- Ignore files from git version control
├── .isort.cfg              <- Configuration for git hook that sorts imports.
├── .pre-commit-config.yaml <- Configuration of pre-commit git hooks.
├── AUTHORS.md              <- List of developers and maintainers.
├── CHANGELOG.md            <- Changelog to keep track of new features and fixes.
├── LICENSE.txt             <- License as chosen on the command-line.
├── MANIFEST.in             <- Add or remove files from the sdist package build.
├── README.md               <- The top-level README for developers.
├── environment.yml         <- The conda environment file for reproducibility.
├── pyproject.toml          <- Build system configuration. Do not change!
├── setup.cfg               <- Declarative configuration of your project.
├── setup.py                <- Use `pip install -e .` to install for development or
│                              or create a distribution with `tox -e build`.
└── tox.ini                 <- Configuration  to automate and standardize Python package actions (tests, docs,...)

```

(pyscaffold-notes)=
## Note

This project has been set up using PyScaffold 4.0.1 and the fluves-extension. For details and usage
information on PyScaffold see <https://pyscaffold.org/> and the Fluves extension
see <https://git.fluves.net/fluves/pyscaffoldext-fluves/>.

[conda]: https://docs.conda.io/
[pre-commit]: http://pre-commit.com/
[Jupyter]: https://jupyter.org/
[nbstripout]: https://github.com/kynan/nbstripout
[PyScaffold]: https://pyscaffold.org/
