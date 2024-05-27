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
