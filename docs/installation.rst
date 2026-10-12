.. _installation:

============
Installation
============

Install from source
===================
To keep track of the continuous development on the package beyond the major
releases, ``git clone`` the repository somewhere and install the code from
source.

Make sure to setup a new environment in either conda or venv (using tox):

Using conda
-----------

When using conda, you can setup the environment using the ``requirements.txt``
file included in this repository.

.. code-block:: bash

    conda create --name pywatemsedem python=3.13

    conda activate pywatemsedem

    pip install -r requirements.txt

Next, install the package from within the ``pywatemsedem`` folder in the terminal
and with the (conda/virtualenv) environment activated:

::

    pip install --no-deps -e .

Or for development purposes of this package, run following code to install
developer dependencies as well (using pip):

::

    pip install -e .[develop]

.. note::

    The `-no-deps` option does not search for the dependencies from pip, but
    only installs the package itself for development and assumes you already
    have the dependencies installed yourself with the requirements.txt file. This
    option is preferred as it avoids to use the package with versions of dependencies
    that are not tested with the package.

.. note::

    If you wish to make use of hvplot, please manually install
    `hvplot <https://hvplot.holoviz.org/>`_ with conda and/or pip.

Using venv
----------

Run the ``dev`` tox command, which will create a ``venv`` with a development
install of the package and it will register the environment as a ipykernel
(for usage inside jupyter notebook):

::

    tox -e dev

.. note::

    Make sure you have a later python version installed than the one specified
    in the ``environment.yml``-file in the environment from where tox is run.

.. note::

    If you wish to make use of hvplot, please manually install
    `hvplot <https://hvplot.holoviz.org/>`_ with pip.

.. _dependencies:

Dependencies
============
The pywatemsedem package has two external dependencies (outside the python
dependencies):

- WaTEM/SEDEM: `WaTEM/SEDEM Pascal <https://watem-sedem.github.io/watem-sedem/>`_
- GIS-processing with SAGA: `SAGA-WATEM <https://github.com/DOV-Vlaanderen/saga-watem/releases>`_

Ensure you:

- Pick up the supported exe of the WaTEM/SEDEM Pascal model from the
  `GitHub <https://watem-sedem.github.io/watem-sedem/releases>`_. and follow
  `the installation instructions of WaTEM/SEDEM <https://watem-sedem.github.io/watem-sedem/installation.html>`_
- Pick up the supported version of SAGA-WaTEM:
  https://github.com/DOV-Vlaanderen/saga-watem/releases., and follow
  `the installation instructions of SAGA-WaTEM <https://dov-vlaanderen.github.io/saga-watem/installation.html>`_

Note that the required version of WaTEM/SEDEM and SAGA are mentioned in the
release page and Changelog.

Once you have downloaded both SAGA-WaTEM and WaTEM/SEDEM, pywatemsdem must
know the locations of these binaries. This can be done in two ways:

The first way is to add the locations of the binaries to the environment variable PATH of your system.
This method has the advantage that you will be able to use these software packages
in a terminal in every directory. However, you might need admin rights to do this.

A second way, it to define the locations of the binaries of saga and WaTEM/SEDEM
by adding a path to these executables in a ``.env``-file in the locations main folder of this repo:

::

    WATEMSEDEM = $YOUR_PATH/watem-sedem/watem_sedem #folder reference
    SAGA = $YOUR_PATH/saga-9.3.1_x64 #folder reference

In your scripts/notebooks, add following before importing pywatemsedem:

::

    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())

When importing pywatemsedem, it will add the directories of saga and watem-sedem
to your PATH envrionment variable.

The python dependencies are listed in the ``requirements.txt`` file. The CI system
tests the package with the pinned versions of the dependencies in this file.
We recommend to install the dependencies from this file, or to use the ``tox -e dev``
command which will create a virtual environment with the pinned dependencies installed.
