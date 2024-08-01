.. _dev-guidelines:

Development guidelines
=======================

Want to contribute code or functionalities to the ``pyws`` package? Great and welcome on board!

We use a number of development tools to support us in improving the code quality. No magic bullet or free
lunch, but just a set of tools as any craftman has tools to support him/her doing a better job.

For development purposes using conda, make sure to first run ``pip install -e .[develop]`` environment
to prepare the development environment and install all development tools. (When using ``tox -e dev`` this
is already done).

When starting on the development of the ``pyws`` package, makes sure to be familiar with the following tools. Do
not hesitate to ask the other developers when having trouble using these tools.

Pre-commit hooks
----------------

To ensure a more common code formatting and limit the git diff, make sure to install the pre-commit hooks. The
required dependencies are included in the development requirements installed when running ``pip install -e .[develop]``.

.. warning::
   Install the ``pre-commit`` hooks before your first git commit to the package!

::

    pre-commit install

on the main level of the package (``pyws`` folder, location where the file ``.pre-commit-config.yaml`` is located)

If you just want to run the hooks on your files to see the effect (not during a git commit),
you can use the command at any time:

::

    pre-commit run --all-files

.. _unittest:

Unit testing with pytest
-------------------------

Run the test suite using the ``pytest`` package, from within the main package
folder (`pyws`):

::

    pytest -m "not end2end"

Or using tox (i.e. in a separate environment)

::

    tox -m "not end2end"

You will receive information on the test status and the test coverage of the
unit tests. Make sure you have defined SAGA and CN-WS, see
:ref:`here <dependencies>`.

With exception of the end-to-end tests, all tests are also run in a drone. To
run the end-to-end flanders test, make sure to define the source data (see
:ref:`here <flandersdata>`) and run:

::

    pytest -m "end2end"


Documentation with sphinx
--------------------------

Build the documentation locally with Sphinx:

::

    tox -e docs

which will create the docs in the ``docs/_build/html`` folder. The ``docs/_build`` directory itself is
left out of version control (and we rather keep it as such ;-)).

Describing DataFrames in docstrings
-----------------------------------

As Numpy docstring does not provide default rules on describing a parameter or
returned variable that represents a ``Pandas.DataFrame`` or a ``dict``, we
include these as follows (equivalent for parameters versus returns section):

::

    Returns
    -------
    df_name: pandas.DataFrame
        The DataFrame ...whatever you need to say... and contains the
        following columns:

        - *colunm_name_1* (int): description 1
        - *colunm_name_2* (float): description 2
        - *colunm_name_3* (datetime): description 3

    other_returned_var : float
        Description of a none df variable

Similar for a dictionary:

::

    Returns
    -------
    df_name: dict
        The dict ...whatever you need to say... and contains:

        - *key_1* (int): description 1
        - *key_2* (float): description 2
        - *key_3* (datetime): description 3

    other_returned_var : float
        Description of a none df variable

In case it would be a dict where each element would be coming from different
landuses,... and so the datatypes of the keys/values are the same for each
item, you can use this in the docstring. E.g. a dict

::

    Returns
    -------
    df_name: dict of {str : float}
        The dict ...whatever you need to say... with the landuse classes as keys and the
        area (in ha) as values.

    other_returned_var : float
        Description of a none df variable

.. note::

    1. The empty lines are important for sphinx to convert this to a clean
       list.
    2. Detail alert: the format *variable: type* is used as constructor for
       every variable in the documention (and not *variable : type*).

CN-WS Filestructure Python
--------------------------

The  filestructure file used for postprocessing (see src/pyws/data/postprocess_files.csv)
holds an overview of all files that are used within the CNWS Python package
(either CNWS-Pascal input data, output data, intermediate processing files,
etc..). This file can be used to add files to the CNWS package. Do note that
this table is only used to define the references to files within the CN-WS
Python code. These references are saved in Python in a dictionary. Each line
holds the definition for one file:

- tag_variable & prefix_variable (str): define the dictionary key
  (e.g. ``rst_aspect``) as the filename structure defined above.
- folder, filename, argument and  extension (str): hold the dictionary value
  and defines the filename. Python string formating is used in filename to
  define the specific arguments needed to recognize the file (e.g. filename:
  `buffers_%s_s%s` and argument `catchment, scenario` will fill in the catchment
  name and scenario number in the filename).
- mandatory (int): indicates whether a file is mandatory to create/load.
- condition (str) (only postprocess): indicates the condition which is coupled
  to the existence of a file, e.g. if a ``rst_buffers`` file is loaded, then
  the option ``Include buffers`` in the model code is set to one. This option
  is only required for the postprocessing.
- default_value (int) (only postprocess): the default value given to an empty
  raster (usefull if a file was not mandatory, but if it does have to be
  loaded for merging with other scenario's).
- generate_nodata (int) (only postprocess): generate a no data file to define
  model domain (i.e. some inputfiles have 0 as nodata value for the
  modeldomain, but also have 0 in the model domain).
- postprocess (int) (only postprocess): indicate whether file has to be loaded
  within postprocessing script.

Note: the filesystem is -for now- only implemented for postprocessing.py

Example:

+-------------------+---------------+-----------+------------------------------+----------------------+---------+---------+---------------+-------------+---------------+-----------+
|   tag_variable    |prefix_variable|  folder   |           filename           |       argument       |extension|mandatory|   condition   |default_value|generate_nodata|postprocess|
+===================+===============+===========+==============================+======================+=========+=========+===============+=============+===============+===========+
|aspect             |rst            |modeloutput|AspectMap                     |NaN                   |rst      |        1|NaN            |          NaN|              0|          1|
+-------------------+---------------+-----------+------------------------------+----------------------+---------+---------+---------------+-------------+---------------+-----------+
|buffers            |rst            |modelinput |buffers_%s_s%s                |catchment, scenario      |rst      |        0|Include buffers|            0|              1|          1|
+-------------------+---------------+-----------+------------------------------+----------------------+---------+---------+---------------+-------------+---------------+-----------+
|buffers_nodata     |rst            |modelinput |buffers_%s_s%s_nodata         |catchment, scenario      |rst      |        0|Include buffers|            0|              0|          1|
+-------------------+---------------+-----------+------------------------------+----------------------+---------+---------+---------------+-------------+---------------+-----------+

Package release
===============

Before releasing, please check the pinned versions of the dependencies, and - if necessary-  adapt in the
``environment.yml``-file. The CI will create sdist/wheels and publish these to gitea when git tags are
added, making releasing straight forward. In order to publish a new release,
the following steps:

- ``git checkout master, git pull origin master`` (work on up to date master
  branch)
- Update the ``CHANGELOG.rst`` with the changes for this new release
- ``git commit -m 'Update changelog for release X.X.X' CHANGELOG.rst``
- ``git push origin master``
- Add git tags: ``git tag X.X.X``
- Push the git tags: ``git push --tags``

When all test pass, drone CI will publish a pre-release on gitea. To convert
this to release:

- On the release page of the repository, draft a new release using the latest
  git tag
- Copy past the changes from the changelog in the dialog and publish release

.. note::

    Run the flanders WS end-to-end test and validate results before creating
    a new release. To run these tests, see :ref:`here <unittest>`
