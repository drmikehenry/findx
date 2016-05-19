*******
History
*******

Version 0.9.6
=============

- Port unit tests from nose to Python's ``unittest`` module.

- Move change history into CHANGES.rst.

- PEP8 conformance.

- Support Python 2 and Python 3 in the same source base.

Version 0.9.5
=============

- Use ``distutils.spawn.find_executable`` to force searching of ``PATH`` on
  windows using Git-bash; otherwise, ``find`` will not be found when the Python
  interpreter is unaware of the Git-bash environment.

Version 0.9.4
=============

- Exclude ``pkgexp`` directories with ``-stdx``.

Version 0.9.3
=============

- Only use ``--no-run-if-empty`` if we have GNU xargs.  BSD xargs does not
  support the option, but implements the behavior by default.

Version 0.9.2
=============

- Fix incorrect interpretation of "pre-options".  Previously, all
  non-expression options were considered "pre" and were floated in front of any
  supplied paths.  This was incorrect; only a few of the "pre-options" belong
  before the paths, and the rest belong after the paths.

- Add support for new ``find`` switches.

- Treat ``-exec`` as an action to avoid spurious extra ``-print`` when using
  excluded files (e.g., ``findx -stdx -exec echo +`` used to have the default
  action ``-print`` appended because ``-exec`` wasn't correctly recognized as
  an action).

Version 0.9.1
=============

- For portability on BSD-based systems, added path "." to command if no path
  is specified.

- Update unit tests.
