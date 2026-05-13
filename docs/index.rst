.. _changes:

Welcome to pywatemsedem's documentation!
========================================

.. image:: https://github.com/watem-sedem/pywatemsedem/actions/workflows/ci.yml/badge.svg?branch=master
    :target: https://github.com/watem-sedem/pywatemsedem

A Python wrapper for WaTEM/SEDEM.

* Free software: MIT license
* Documentation: https://watem-sedem.github.io/pywatemsedem/

Introduction
------------

The pywatemsedem package is a Python wrapper for `WaTEM/SEDEM <https://watem-sedem.github.io/watem-sedem/>`_.

The goal of pywatemsedem is to make it easier to produce and process the input and output of WaTEM/SEDEM.
The package provides tools to interact with WaTEM/SEDEM, such as running the model and processing the output.

Pywatemsedem is developed to facilitate standardized and reproducible
applications of the WaTEM/SEDEM model.
The package provides a user-friendly interface to set up and run the model,
as well as tools for visualizing and analyzing the model output.

The python package is developed and maintained by Fluves, funded by the
Departement Omgeving of the Vlaamse Overheid, but everyone is welcome to
contribute.

The package is implemented in Python and best used with the tutorial
notebooks available in this documentation.

Getting started
---------------

After :ref:`installation` you can start using the package with the tutorial notebooks
available in this documentation:

- A quick start to get to know the basic api  <getting-started/api.ipynb>



.. toctree::
   :caption: pywatemsedem
   :maxdepth: 2

   Home <self>
   Installation <installation>

.. toctree::
   :caption: Getting started
   :maxdepth: 1

   User Guide <getting-started/api.ipynb>
   How to use the User Choices <getting-started/userchoices.rst>
   Calibrating WaTEM/SEDEM <getting-started/calibrate.ipynb>

.. toctree::
   :caption: Advanced guide
   :maxdepth: 1
   Processing rasters and vector <getting-started/geo.rst>
   IO <getting-started/io.rst>
   Module Reference <api/modules>

.. toctree::
   :caption: Developer guide
   :maxdepth: 1

   Contributing <contributing>
   Development <development>
   API Reference <api/modules>
   Changelog <changelog>
   License <license>
   Authors <authors>
   Code of conduct <codeofconduct>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _toctree: http://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html
.. _reStructuredText: http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
.. _references: http://www.sphinx-doc.org/en/stable/markup/inline.html
.. _Python domain syntax: http://sphinx-doc.org/domains.html#the-python-domain
.. _Sphinx: http://www.sphinx-doc.org/
.. _Python: http://docs.python.org/
.. _Numpy: http://docs.scipy.org/doc/numpy
.. _SciPy: http://docs.scipy.org/doc/scipy/reference/
.. _matplotlib: https://matplotlib.org/contents.html#
.. _Pandas: http://pandas.pydata.org/pandas-docs/stable
.. _Scikit-Learn: http://scikit-learn.org/stable
.. _autodoc: http://www.sphinx-doc.org/en/stable/ext/autodoc.html
.. _Google style: https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings
.. _NumPy style: https://numpydoc.readthedocs.io/en/latest/format.html
.. _classical style: http://www.sphinx-doc.org/en/stable/domains.html#info-field-lists


Acknowledgements
================

Part of project is based on the `cookiecutter data science template <https://drivendata.github.io/cookiecutter-data-science>`_
