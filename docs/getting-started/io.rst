
IO-module
=========
.. warning:: This module is under development

Introduction
------------
The io-module holds a number of basic functionalities for handling the io for
WaTEM/SEDEM files.

Ini-file
--------
The ini-file (see :ref:`here <pywatemsedem:inifile>`) can be modified with a Python
function available in the in ini-submodule:

.. code-block:: python

    from pywatemsedem.io import ini
    ini.modify_field("inifile.ini", "User Choices", "max kernel", 20)

It adjusts the value of 'max kernel' in the section 'User Choices' to 20.

In addition, one can add a value to a section:

.. code-block:: python

    from pywatemsedem.io import ini
    ini.add_field("inifile.ini", "User Choices", "max kernelz", 20)

The code only does error handling for non-existing key and sections, it does
not check the content.
