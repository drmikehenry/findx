findx - an extended ``find`` command.
=====================================

Overview
--------

``findx`` is an extended version of the Unix ``find`` command written in the
Python language as a wrapper around ``find`` and other Unix tools.  ``find`` is
a very powerful tool, but by itself there are a large number of arguments
required for a typical invocation.  ``findx`` provides convenient shortcuts for
invoking ``find`` without so much typing.

As a quick example, imagine using ``find``, ``xargs`` and ``grep`` to search
through a tree of files.  A simple invocation might be::

  find -type f | xargs grep PATTERN

But the above invocation won't correctly handle file with spaces or unusual
characters; handling that grows the command to::

  find -type f -print0 | xargs -0 grep PATTERN

Filenames are handled correctly now, but the command probably searches through
some uninteresting files.  It also misses on a couple of boundary cases.  You'd
probably like to include ``xargs --no-run-if-empty`` to ensure ``grep`` isn't
invoked when no files are found; you might want to follow symbolic links as well
as files; and you might want to skip over ``.git`` directories (for example).
Adding those into the above command grows things considerably::

  find -L -name .git -prune -o -type f -print0 |
    xargs -0 --no-run-if-empty grep PATTERN

After excluding additional files and directories and perhaps adding
``--color=auto`` to the ``grep`` invocation, things are getting out of hand.
``findx`` exists to make such invocations simpler.  First, ``findx`` knows about
the need for ``-print0`` and ``xargs -0 --no-run-if-empty``; using ``:`` implies
all of the standard protocol for using ``xargs`` correctly, reducing the above
to::

  findx -L -name .git -prune -o -type f : grep PATTERN

Standard paths to ignore are requested via ``-stdx``::

  findx -L -stdx -type f : grep PATTERN

Following symlinks to files and producing only files is another common
requirement; the switch ``-ffx`` implies finding files (following symlinks)
while excluding a predefined set of directories and files::

  findx -ffx : grep PATTERN

Piping filenames into ``grep`` is such a common pattern that the ``-ffg`` switch
is the same as ``-ffx : grep``, reducing things to::

  findx -ffg PATTERN

In addition, ``ffx`` and ``ffg`` are to additional entry points into ``findx``
that reduce things even further::

  ffx = findx -ffx
  ffg = findx -ffg

In the most common case, searching a file tree thus reduces to::

  ffg PATTERN

See ``findx --help`` or read the top of ``findx.py`` for more details.

Installation
------------

From PyPI, installation is the usual::

  pip install findx

From the source tree, install via::

  python setup.py install

Running the tests
-----------------

Invoke the tests via the ``Makefile``::

  make

Or manually via::

  python -m unittest discover

Changes
-------

See CHANGES.rst for a history of changes.

License
-------

``findx`` is distributed under the terms of the MIT license; see LICENSE.rst
for details.
