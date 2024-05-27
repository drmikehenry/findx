******************
Maintainer's notes
******************

These notes are intended for use by the maintainer.

Building an executable with PyInstaller
=======================================

- Use the Nox ``build`` session::

    poetry run nox -s build

Making a release
================

Perform these steps on Linux.

- Verify proper ``version = "x.y.z"`` in ``pyproject.toml``.

- Verify changes are recorded in ``CHANGES.rst``.

- Run a Poetry shell::

    poetry shell

- Verify all Nox tests are passing::

    nox

- Prepare the release::

    nox -s release

- Follow on-screen instructions to complete release.

Upgrading dependencies
======================

- ``poetry upgrade``.

Updating switches for new ``find``
==================================

- ``findx`` understands the switches documented in GNU ``find --help``.  These
  are recorded in ``gnu-find-switches.txt``, along with the associated version
  number from ``find --version`` as follows::

    (find --version; find --help) > gnu-find-switches.txt

- Repeat the above with a newer version of ``find`` and compare differences to
  see what changes have been made to the switches.

- Use ``scripts/survey-switches`` to scan the manpage and the ``--help`` output
  for new switches.  The result is stored in ``doc/allswitches.txt``.
