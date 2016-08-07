*******
History
*******

Version 0.9.10
==============

- Add configuration variables settable via configuration file, environment
  variables, or command line.  Display values of variables via new switches
  ``-show-var VAR``, ``-show-vars``, and ``-show-defaults``.

- Allow for configurable location and type of the main utilities ``find``,
  ``xargs``, and ``grep``.

- Add ``-ff`` switch for "find files following symlinks"; define ``-ffx`` as
  ``-stdx -ff``.

- Add ``-grep`` switch to imply ``: <grep> <grep_args> [ :``, where ``<grep>``
  is the configuration location for the grep utility and ``<grep_args>`` depends
  in a configurable way on the style of the grep utility being used.

- Stop requiring root paths to be directories.  POSIX allows roots to be files
  as well.  Require only that a root exist.  Also, relax the restriction that a
  path must not have a metacharacter to be considered a root in the absence of
  ``-root``.  Now it is sufficient for the path to exist as-is.  This allows
  use of shell globbing without worrying whether the globbed paths have
  metacharacters in them.

- Decompose ``-stdx`` into ``-stdxd`` (for directories) and ``-stdxf`` (for
  files).

- Define variables ``stdxd`` and ``stdxf`` for configuring the globs to exclude
  when the corresponding exclusions are active.

Version 0.9.9
=============

- Return an exit status from ``findx``, reflecting errors from ``find``,
  ``xargs``, or ``findx`` itself.  See ``findx --help`` for exit status values.

Version 0.9.8
=============

- Add support for Travis CI (thanks to John Vandenberg).

Version 0.9.7
=============

- Restore support for Python 2.6.
  Now these Python versions are supported: 2.6 2.7 3.3 3.4 3.5

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
