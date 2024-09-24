.. _dev-guidelines:

Development guidelines
=======================

Want to contribute code or functionalities to the ``pywatemsedem`` package? Great and welcome on board!

We use a number of development tools to support us in improving the code quality. No magic bullet or free
lunch, but just a set of tools as any craftman has tools to support him/her doing a better job.

For development purposes using conda, make sure to first run ``pip install -e .[develop]`` environment
to prepare the development environment and install all development tools. (When using ``tox -e dev`` this
is already done).

When starting on the development of the ``pywatemsedem`` package, makes sure to be familiar with the following tools. Do
not hesitate to ask the other developers when having trouble using these tools.

Pre-commit hooks
----------------

To ensure a more common code formatting and limit the git diff, make sure to install the pre-commit hooks. The
required dependencies are included in the development requirements installed when running ``pip install -e .[develop]``.

.. warning::
   Install the ``pre-commit`` hooks before your first git commit to the package!

::

    pre-commit install

on the main level of the package (``pywatemsedem`` folder, location where the file ``.pre-commit-config.yaml`` is located)

If you just want to run the hooks on your files to see the effect (not during a git commit),
you can use the command at any time:

::

    pre-commit run --all-files

.. _unittest:

Unit testing with pytest
-------------------------

Run the test suite using the ``pytest`` package, from within the main package
folder (`pywatemsedem`):

::

    pytest

Or using tox (i.e. in a separate environment)

::

    tox --

You will receive information on the test status and the test coverage of the
unit tests. Make sure you have defined SAGA and WaTEM/SEDEM, see
:ref:`here <dependencies>`.

Documentation with sphinx
--------------------------

Build the documentation locally with Sphinx (tox):

::

    tox -e docs

which will create the docs in the ``docs/_build/html`` folder. The ``docs/_build`` directory itself is
left out of version control (and we rather keep it as such ;-)).

Github actions
--------------

Apart from these tools you can run locally, we use github actions to run these tests also on the cloud.
You can see the results at https://github.com/watem-sedem/pywatemsedem/actions

Git LFS
-------

Git LFS, or large file support, is used in this repository to store gis files in
the repository. To use this functionality you need to install git lfs. See
https://git-lfs.github.com/ for instructions and more information.

The ``.gitattributes``-file in the root folder contains the file extensions wich are
stored under LFS. For now, only files within the test folder are stored under
LFS.

Naming things
-------------

To provide structure in the naming of methods, functions, classes,... we propose
to conform the following guidelines.

Class, function/methods names follow the standard naming conventions as defined
in the `PEP8`_ guidelines. Additionaly, methods/functions start - whenever
possible - with an active verb on the action they perform (``does_something()``)
, e.g. ``load_raster()``, ``clip_shape()``, ``transform_rasterprop()``

Variable names follow the `PEP8`_ guidelines, but provide additional context:

- vectorfiles (incl. shapefiles etc):  ``vct_variable``
- rasterfiles: ``rst_raster``
- raw tekstfiles (txt): ``txt_variable``
- numpy array: ``arr_variable``
- pandas: ``df_variable``
- geopandas df: ``gdf_variable``
- files: ```fname_variable``

.. _PEP8: https://www.python.org/dev/peps/pep-0008/#naming-conventions

.. note:

    1. fname states that any extension can be used, checks within code should
       be implemented to verify whether they are valid!
    2. The use of "_" in a variable name is only accepted twice, to avoid long
       and confusing names. For example, naming ``dict_df_variable`` is not
       encouraged, but accepted. The name ``lst_dict_df_variable`` is not
       accepted, please think about another structure.

Utilities
---------

- Load raster: load rasters as numpy arrays. The ``profile`` raster metadata
  holds all metedata that geograpical defines the array. See
  :func:`pywatemsedem.core.utils.load_raster`:

::

    from pywatemsedem.core.utils import load_raster
    rst = "landuse.tif" # can be any raster extension supported by GDAL
    arr,profile = load_raster(rst)

- Write raster: write numpy arrays to rasters. See
  :func:`pywatemsedem.core.utils.write_arr_as_rst`:

::

    from pywatemsedem.core.utils import write_arr_as_rst
    rst_out = "landuse_int64.tif"
    write_arr_as_rst(arr, rst_out, "int64", profile):


The dtype of the array and output raster is a required function input
parameter, and can be used to save disk memory (i.e. use int64 instead of
float64).


Guideline for unified coding style
----------------------------------

A number of guidelines are given in order to obtain a degree of unified style
in the pywatemsedem code. Following guidelines are given:

 - Pandas: access columns via ``df["test"]`` rather than ``df.test``.
 - Use Pandas dataframes to transfer non-raster data between modules/functions,
   use numpy arrays to perform numerical operations. In case of numerical
   operations (> 1 operation), write independent functions which use numpy
   arrays as input and output numpy arrays that can be stored in a dataframe.

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
       every variable in the documentation (and not *variable : type*).

Postprocess file structure
--------------------------

The postprocess filestructure file `src/pywatemsedem/data/postprocess_files.csv`
holds an overview of all files that are used within postprocessing
(either WaTEM/SEDEM input data, output data, intermediate processing files,
etc..). This file can be used to add files to the WaTEM/SEDEM package. Do note that
this table is only used to define the references to files within the WaTEM/SEDEM
Python code. These references are saved in Python in a dictionary. Each line
holds the definition for one file:

- tag_variable & prefix_variable (str): define the dictionary key
  (e.g. ``rst_aspect``) as the filename structure defined above.
- folder, filename, argument and  extension (str): hold the dictionary value
  and defines the filename. Python string formating is used in filename to
  define the specific arguments needed to recognize the file (e.g. filename:
  `buffers_%s_s%s` and argument `bekken, scenario` will fill in the catchment
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
