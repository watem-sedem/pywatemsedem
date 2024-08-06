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

When using conda, you can setup the environment using the ``environment.yml``
file included in this repository:

.. code-block:: bash

    conda env create -f environment.yml

    conda activate pywatemsedem

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
    have the dependencies installed yourself.

.. note::

    If you wish to make use of hvplot, please manually install
    `hvplot <https://hvplot.holoviz.org/>`_ with conda.

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

- Pick up the latest exe of the WaTEM/SEDEM Pascal model from the
  `GitHub <https://watem-sedem.github.io/watem-sedem/releases>`_.
- Pick up the latest exe of the SAGA-GIS with **WaTEM**:
  https://github.com/DOV-Vlaanderen/saga-watem/releases.

Note that the required version of WaTEM/SEDEM and SAGA are mentioned in the
release page. Define the saga and WaTEM/SEDEM version by adding a path to the
executables in a ``.env``-file in the locations main folder of this repo:

::

    WATEMSEDEM = $YOUR_PATH/watem-sedem/watem-sedem/watem-sedem #executable reference
    SAGA = $YOUR_PATH/2022.12.8/saga #folder reference

In your scripts/notebooks, add following:

::

    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
    # setting SAGA GIS with WaTEM
    os.environ["SAGA_TLB"]=os.environ.get("SAGA")
    # setting WaTEM/SEDEM
    watemsedem = Path(os.environ.get("WATEMSEDEM"))
