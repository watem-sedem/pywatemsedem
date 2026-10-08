.. _contribute:

Contributing to pywatemsedem
============================

First of all, thanks for considering contributing to pywatemsedem! It's people like you
that make it rewarding for us - the project :ref:`authors` - to work on pywatemsedem.

.. _maintainers: .

pywatemsedem is an open source project, currently maintained by Fluves,
funded by the Departement Omgeving of the Vlaamse Overheid.

Code of conduct
---------------

Please note that this project is released with a :ref:`code_conduct`.
By participating in this project you agree to abide by its terms.

How you can contribute?
-----------------------

There are several ways you can contribute to this project. If you want to know
more about why and how to contribute to open source projects like this one,
see this `Open Source Guide`_.

.. _Open Source Guide: https://opensource.guide/how-to-contribute/

Share the love
^^^^^^^^^^^^^^

Think pywatemsedem is useful? Let others discover it, by telling them in person, via
social media or a blog post.

Using pywatemsedem for a paper you are writing? Consider citing it:

    TO DO: add citation information here

Ask a question
^^^^^^^^^^^^^^

Using pywatemsedem and got stuck? Browse the documentation_ to see if you
can find a solution. Still stuck? Post your question as a `new issue`_ on GitHub.
While we cannot offer user support, we'll try to do our best to address it,
as questions often lead to better documentation or the discovery of bugs.

Want to ask a question in private? Contact DOV directly by `email`_.

.. _documentation: https://watem-sedem.github.io/pywatemsedem/
.. _new issue: https://github.com/watem-sedem/pywatemsedem/issues/new
.. _email: cnws@vlaanderen.be

Propose an idea
^^^^^^^^^^^^^^^^

Have an idea for a new pywatemsedem feature? Take a look at the documentation_ and
`issue list`_ to see if it isn't included or suggested yet. If not, suggest
your idea as a `new issue`_ on GitHub. While we can't promise to implement
your idea, it helps to:

.. _documentation: https://watem-sedem.github.io/pywatemsedem/
.. _issue list: https://github.com/watem-sedem/pywatemsedem/issues
.. _new issue: https://github.com/watem-sedem/pywatemsedem/issues/new

* Explain in detail how it would work.
* Keep the scope as narrow as possible.

See below, :ref:`dev-guidelines`,  if you want to contribute code for your idea as well.

Report a bug
^^^^^^^^^^^^

Using pywatemsedem and discovered a bug? That's annoying! Don't let others have the
same experience and report it as a `new issue`_ so we can fix it. A good bug
report makes it easier for us to do so, so please include:

.. _new issue: https://github.com/watem-sedem/pywatemsedem/issues/new

* Your operating system name and version (e.g. Mac OS 10.13.6).
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Improve the documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^

Noticed a typo on the website? Think a function could use a better example?
Good documentation makes all the difference, so your help to improve it is very welcome! Maybe you've written a good
introduction tutorial or example case, these are typically very popular sections for new users.

**The website**

`This website`_ is generated with Sphinx_. That means we don't have to
write any html. Content is pulled together from documentation in the code,
notebooks, reStructuredText_ files and the package ``conf.py`` settings. If you
know your way around *Sphinx*, you can `propose a file change`_ to improve
documentation. If not, `report an issue`_ and we can point you in the right direction.

.. _This website: https://watem-sedem.github.io/pywatemsedem/
.. _Sphinx: http://www.sphinx-doc.org/en/master/
.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _propose a file change: https://help.github.com/articles/editing-files-in-another-user-s-repository/
.. _report an issue: https://github.com/watem-sedem/pywatemsedem/issues/new

For more technical details about the Sphinx setup of the pywatemsedem project, See the
:ref:`dev-guidelines` section.

**Function documentation**

Functions are described as comments near their code and translated to
documentation using the  `numpy docstring standard`_. If you want to improve a
function description:

.. _numpy docstring standard: https://numpydoc.readthedocs.io/en/latest/format.html

1. Go to ``pywatemsedem/`` directory in the `code repository`_.
2. Look for the file with the name of the function.
3. `Propose a file change`_ to update the function documentation in the docstring (in between the triple quotes).

.. _code repository: https://github.com/watem-sedem/pywatemsedem
.. _Propose a file change: https://help.github.com/articles/editing-files-in-another-user-s-repository/


Contribute code
^^^^^^^^^^^^^^^

Care to fix bugs or implement new functionality for pywatemsedem? Awesome! Have a
look at the `issue list`_ and leave a comment on the things you want
to work on.

Make sure to setup your development environment and check the :ref:`development
guidelines <dev-guidelines>` to see ow we develop the pywatemsedem package.
