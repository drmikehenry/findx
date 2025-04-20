#!/usr/bin/env python

import importlib.metadata
import os
import re
import shutil
import signal
import sys
import traceback
import typing as T
from subprocess import PIPE, Popen, STDOUT

project_name = "findx"

HELP_TEXT = r"""
Usage: findx [OPTION | FINDOPTION | ROOT | METAGLOB]*
  or:  findx [OPTION | FINDOPTION | ROOT | METAGLOB]* : [XARG]+

Additional shortcut commands:

  ffx:  findx -ffx
  ffg:  findx -ffg

**NOTE** Examples below include POSIX shell quoting to protect special
characters from the shell.

Provides shortcuts for the following 'find' idioms:
    find [...]
    find [...] -print0 | xargs -0 [XARG]+

The OPTION, FINDOPTION, ROOT, and METAGLOB options may be specified in any
order while in FINDX MODE.  The XARGs are kept in-order while in XARGS MODE.

OPTION      An option to findx (specified below).

FINDOPTION  A standard 'find' option to be appended to EXPRESSION.
            ('man find' or 'find --help' for details.)

ROOT        A directory or file to be appended to ROOTS.
            ROOT must not contain METACHARACTERS.

METAGLOB    A GLOB containing one or more METACHARACTERS.
            Shortcut for -name METAGLOB.

XARG        Appended to XARGLIST for second 'xargs' stage of pipeline.
            If XARGLIST is empty, the 'xargs' stage is not used.  When xargs
            are present, the 'find' action '-print0' is used in combination
            with the 'xargs' option '-0'.  'xargs' is always run with the
            option '--no-run-if-empty' to prevent execution without filenames,
            if GNU xargs is detected.  BSD xargs implements this behavior by
            default.

GLOB        An extended-syntax filename glob reducing to one or more logically
            OR'ed 'find'-style globs containing '*', '?', and '[]'.  OR'ing
            occurs at '|' and ',' characters.  Bash-like braces may be used to
            constrain expansion; braces may be nested.  All metacharacters
            except ']' may be "quoted" via square brackets.  Globs containing
            shell metacharacters should be escaped.  Examples:

            -name 'one|two'         \( -name one -o -name two \)
            -name one,two           \( -name one -o -name two \)
            -name '*.{c,cpp}'       \( -name '*.c' -o -name '*.cpp' \)
            -name 'quoted[,]comma'  -name 'quoted,comma'

            Extended GLOBs are recognized after the following 'find' tests:
            -ilname -iname -ipath -wholename -lname -name -path -wholename

Extensions to FINDOPTIONS

  In addition to extended GLOBs, the '-type' option is extended to accept
  multiple type characters which are logically OR'ed.  Examples:
            -type fd                \( -type f -o -type d \)
            -type f                 -type f

OPTIONS

  -help, --help         print this usage help and terminate
  -version, --version   print version of findx and terminate
  -readme,--readme      print findx README.rst
  -show                 show command without executing it
  -show-var VAR         show current value of variable VAR
  -show-vars            show values of all variables
  -show-defaults        show default values of all variables
  -root ROOT            add arbitrary ROOT (directory or file) to ROOTS
  -x EXCLUDE            add EXCLUDE to list of exclusions
  -i INCLUDE            add INCLUDE to list of inclusions (disable exclusions
                        by including everything via '-i \*')
  -stdxf                use standard exclusions for files (configured by
                        the 'stdxf' variable)
  -stdxd                use standard exclusions for directories (configured
                        by the 'stdxd' variable)
  -stdx                 use standard exclusions; short for '-stdxd -stdxf'
  -ff                   find files following symlinks; short for 'type -f -L'
  -ffx                  find files with standard exclusions, following
                        symlinks; short for '-stdx -ff'
  -ffg                  grep through files; short for '-ffx -grep'
  :                     switch to XARGS MODE; require subsequent xarg
  ::                    permanent XARGS MODE; require subsequent xarg
  [                     switch to FINDX MODE from FINDX MODE or XARGS MODE
  ]                     switch to XARGS MODE
  ]]                    switch to XARGS MODE permanently
  -grep                 short for ': <grep> <grep_args> [ :' where
                        <grep> and <grep_args> come from the variables
                        'grep_path' and '<grep_style>_grep_args'

Note: FINDX MODE is active at start.  The '[' option does not necessitate ']'.
A bare '[' may not be used as an XARG unless XARGS MODE has been made
permanent via '::' or ']]'.

EXCLUSIONS, INCLUSIONS
  Exclusions and inclusions are arbitrary 'find' terms, not full 'find'
  expressions.  Loosely, a term extends to the next AND or OR operator
  (including the AND implied between consecutive terms).  Parenthesized
  expressions count as a term.
  If exclusions are present, they are logically OR'ed as follows:
    find \( EXCLUDE1 -o EXCLUDE2 ... \) -prune -o EXPRESSION
  Inclusions override exclusions; if both are present, the pruning becomes:
    find \( EXCLUDE1 -o EXCLUDE2 ... \) ! \( INCLUDE1 -o INCLUDE2 ... \) -prune
  An inclusion of '-i \*' resets previously specified exclusions and
  inclusions.

  Examples:
    # Exclude *.txt, *.TXT, etc.
    -x -iname '*.txt'

    # Exclude anything with a '.' in the name, but include '*.txt'.
    -x -name '*.*' -i '*.txt'

    # Exclude .svn directories and files named '*.bak', but include 'f.bak'.
    # NOTE that '-i' requires '-name' because f.bak has no metacharacters.
    -x \( -type d -name .svn -o -type f -name '*.bak' \) -i -name f.bak

STANDARD EXCLUSIONS
  When '-stdx' is specified, a built-in list of standard exclusions applies.
  (Use '-show' to see the list.)

STANDARD ACTION
  If EXPRESSION contains no 'find' action (e.g., '-print', '-print0',
  '-delete', ...), a standard action will be appended to EXPRESSION.  The
  standard action is '-print0' when XARGS are present, and '-print' otherwise.

EXIT STATUS
  0         full success
  1         'findx' syntax error (e.g., invalid command-line option)
  2         'findx' runtime error (e.g., missing 'xargs' command)
  3         'findx' uncaught exception (if seen, please submit a bug report)
  4..99     reserved
  100       multiple pipeline failures ('find' and 'xargs' both non-zero)

  101..119  'find' returned 1..19
  120       'find' returned 20..127

  121       'xargs' returned 1
  122       'xargs' returned 2..122
  123..127  'xargs' returned 123..127

  128+n     'findx' or other program terminated on signal n

  Returning 128+n takes precedence over returning 100.  If any of 'findx',
  'find', or 'xargs' are terminated by a signal, the overall exit status
  will reflect one of their individual exit statuses rather than a combined
  code of 100.

EXAMPLES

# Grep for 'main' in .c and .cpp files.
  findx '*.{c,cpp}' : grep main

# Grep for 'main' in .c and .cpp files, excluding .svn and CVS directories.
  findx '*.{c,cpp}' -x -name .svn,CVS : grep main

# Grep for 'main' in all files with standard exclusions.
  ffg main

# Grep for 'main' case-insensitively in all .c files under /work.
  ffg main -i [ '*.c' /work
  ffg -i [ '*.c' /work ] main
  ffg [ '*.c' /work : main -i

# Remove backup files with standard exclusions.
  ffx '*~|*.bak' : rm
  ffx '*~|*.bak' -delete

# All files and directories modified less than 1 day ago.
  findx -mtime 1

# List directories only with standard exclusions.
  findx -stdx -type d : ls -ld

# Look for directories only.
  findx -type d
  findx -type d : ls -ld

# Grep for 'main' excluding tmp directories; the use of '-name' can be avoided
# by adding a comma to 'tmp', making it into an extended glob.
  ffg main [ -x -name tmp
  ffg main [ -x tmp,

# Override pre-defined exclusions.
  findx -i '*'

# Use findx for no pre-defined exclusions, etc.
  findx -mtime -1

# Just files with standard exclusions (fails with newline in filename).
  ffx | while read i; do Something; done

CONFIGURING FINDX

findx uses configuration variable to control its behavior.  Each variable has a
value that is a list of zero or more strings generally delimited by whitespace
(subject to the quoting rules described later).

Variables are named in lower_case_separated_by_underscores.

A "normal assignment" replaces the variable with the value given:

  variable_name = value

However, if the value begins with an "assignment mode" special character, it
may be merged with the variable's previous value:

  variable_name = +values to append
  variable_name = ^values to prepend
  variable_name = -values to remove

Use the special character '=' to force normal assignment of arbitrary values;
all characters after the '=' are taken literally:

  variable_name = =+literal_value_starts_with_plus
  variable_name = =^literal_value_starts_with_caret
  variable_name = =-literal_value_starts_with_minus

CONFIG FILE

A configuration file consists of blank lines, comments, and variable
assignments.  For example:

  # This is a comment.
  variable_name = first_element second_element third_element

  # Consecutive indented lines are merged with the assignment line, with
  # the intervening whitespace replaced by a single space:
  variable_name = first_element
    second_element
    third_element

  # To avoid the space, begin the continuation lines with '+':
  variable_name = first_
    +element second_
    +element third_element

Errors in a configuration file will prevent findx from running; however, it is
not an error for a configuration file to be missing.  A file is read and parsed
only when it is first needed.

QUOTING RULES

A run of backslashes is generally treated literally, but may at times be
treated specially.  If the run is treated specially, each pair of backslashes
in the run is treated as a single escaped backslash; then if an unpaired
backslash remains, it escapes the character following the run.

Inside single quotes, all characters are treated literally until the closing
single quote.

Inside double quotes, almost all characters are treated literally, but a run of
backslashes is treated specially if followed by a double-quote.

Outside of quotes, a run of backslashes is special if it precedes one of the
following characters:

    '  "  (whitespace)

With future extensions, more characters may require quoting or escaping.  To
future-proof your configuration files, quote anything other than the following
characters that will never be special:

    (letters) (digits) _ - / .

Quote characters must be paired and must not cross line boundaries.

SETTING CONFIGURATION VARIABLES

Each variable has a default value built into findx.  This value may be modified
or replaced by any of the following mechanisms taken in this order (later
choices have higher precedence):

- Configuration file(s)
- Environment variable
- Command-line switch

For environment variables, the variable name is converted to uppercase and
'FINDX_' is prepended.  On the command line, the name's underscores are
converted to hyphens and '--' is prepended.  For example, the variable
'config_files' would become 'FINDX_CONFIG_FILES' as an environment variable and
'--config-files' on the command line.  An assignment appending the file
'new_config_file' could be done any of the following ways::

  # In a config file:
  config_files = +new_config_file

  # In an environment variable:
  FINDX_CONFIG_FILES=+new_config_file

  # On the command line:
  --config-files +new_config_file

CONFIGURATION VARIABLES

__DEFAULT_CONFIG_TEXT__
""".strip()

DEFAULT_CONFIG_TEXT = r"""
# Configuration files to use in order of increasing priority.
config_files =
    /etc/findx/config
    ~/.config/findx/config

# Names and/or absolute paths for the 'find' utility.  The first-found
# choice will be used (must not be empty).
find_path = gnufind find

# Style of find utility: probe, gnu, bsd, posix
find_style = probe

# Names and/or absolute paths for the 'xargs' utility.  The first-found
# choice will be used (must not be empty).
xargs_path = gnuxargs xargs

# Style of xargs utility: probe, gnu, bsd, posix
xargs_style = probe

# Names and/or absolute paths for the 'grep' utility.  The first-found
# choice will be used (must not be empty).
grep_path = gnugrep grep

# Style of grep utility: probe, gnu, bsd, posix
grep_style = probe

# Extra grep arguments for use when grep_style = gnu.
gnu_grep_args = '-H' '--color=auto'

# Extra grep arguments for use when grep_style = bsd.
bsd_grep_args = '-H' '--color=auto'

# Extra grep arguments for use when grep_style = posix.
posix_grep_args =

# Directory globs excluded by '-stdxd'.
stdxd =
    .svn .git .bzr .hg .undo build *export pkgexp
    bak *.egg-info *.egg .mypy_cache .tox .nox htmlcov .ruff_cache
    venv .venv

# File globs excluded by '-stdxf'.
stdxf =
    *.bak *~ *.tmp
    *.o *.a *.so *.ds *.os *.sbr *.pch *.pdb *.pyc *.pyo
    *.zip *.tar *.gz *.bz2
    *.bin *.elf *.exe *.obj *.dll *.lib *.suo
    *.bmp *.ico *.gif *.jpg *.png
    *.pdf
    .*.sw? tags
""".strip()


VALID_VARS = re.findall(r"^\w+", DEFAULT_CONFIG_TEXT, re.MULTILINE)


HELP_TEXT = HELP_TEXT.replace("__DEFAULT_CONFIG_TEXT__", DEFAULT_CONFIG_TEXT)


def warn(message: str) -> None:
    print(f"{project_name}: {message}", file=sys.stderr)


def single_quoted(s: str) -> str:
    if s == "":
        return "''"
    parts = ["" if p == "" else ("'%s'" % p) for p in s.split("'")]
    return "\\'".join(parts)


def double_quoted(s: str) -> str:
    bslash = "\\"
    bslash_count = 0
    parts = []
    for c in s:
        if c == bslash:
            bslash_count += 1
        else:
            if c == '"':
                bslash_count = 2 * bslash_count + 1
            parts.append(bslash * bslash_count + c)
            bslash_count = 0
    parts.append(bslash * bslash_count * 2)
    return '"%s"' % ("".join(parts))


def quoted(s: str) -> str:
    if "'" not in s:
        return single_quoted(s)
    else:
        return double_quoted(s)


def quoted_join(args: T.List[str]) -> str:
    return " ".join(quoted(arg) for arg in args)


def quote_required(arg: str) -> bool:
    if arg == "":
        required = True
    else:
        required = False
        for c in arg:
            if c.isspace() or c in ["\\", '"', "'"]:
                required = True
                break
    return required


def optionally_quoted(s: str) -> str:
    if quote_required(s):
        return quoted(s)
    else:
        return s


def optionally_quoted_join(args: T.List[str]) -> str:
    return " ".join(optionally_quoted(arg) for arg in args)


def count_run(s: str, pred: T.Callable[[str], bool]) -> int:
    run_length = 0
    for c in s:
        if pred(c):
            run_length += 1
        else:
            break
    return run_length


def split_token(s: str) -> T.Tuple[str, str]:
    """
    Return (token, rest), where token is:
    - a maximal run of backslashes
    - a maximal run of whitespace
    - any other single character
    - empty string (only when s was empty)
    """
    if not s:
        return "", ""

    split_at = (
        count_run(s, lambda c: c == "\\")
        or count_run(s, lambda c: c.isspace())
        or 1
    )

    return s[:split_at], s[split_at:]


def found_special_backslashes(token: str, value: str, quote: str) -> bool:
    special = False
    if token[0] == "\\" and value != "":
        if quote == '"':
            special = value[0] == quote
        elif not quote:
            special = value[0] in ("'", '"') or value[0].isspace()
    return special


def quoted_split(value: str) -> T.List[str]:
    args = []
    quote = ""
    this_arg = []

    def keep(c: str) -> None:
        this_arg.append(c)

    def finish_arg() -> None:
        if this_arg:
            args.append("".join(this_arg))
            this_arg[:] = []

    while value:
        token, value = split_token(value)
        first_token_char = token[0]
        if found_special_backslashes(token, value, quote):
            # Backslashes are special; keep half of them.
            keep("\\" * (len(token) // 2))
            if len(token) % 2:
                # Odd number of backslashes escape value[0].
                keep(value[0])
                value = value[1:]
        elif quote:
            if first_token_char == quote:
                # Found closing quote.
                quote = ""
            else:
                keep(token)
        elif first_token_char in ("'", '"'):
            quote = token
            # Keep an empty string to ensure we're in an arg.
            keep("")
        elif first_token_char.isspace():
            finish_arg()
        else:
            keep(first_token_char)
    if quote:
        raise ValueError("No closing quotation in %s" % repr(value))
    finish_arg()
    return args


def split_leading_whitespace(s: str) -> T.Tuple[str, str]:
    rest = s.lstrip()
    leading_whitespace = s[: -len(rest)]
    return leading_whitespace, rest


def joined_lines(lines: T.List[str]) -> T.Iterator[str]:
    current_line = None
    for line in lines:
        line = line.rstrip()
        leading_whitespace, rest = split_leading_whitespace(line)
        if current_line and leading_whitespace:
            if rest.startswith("+"):
                current_line += rest[1:]
            else:
                current_line += " " + rest
        else:
            if current_line is not None:
                yield current_line
            current_line = line
    if current_line is not None:
        yield current_line


class FindxError(Exception):
    """The base exception class for all findx errors."""


class FindxInternalError(FindxError):
    """Indicates buggy code within findx."""


class FindxSyntaxError(FindxError):
    """An invocation error (typically caused by bad user-supplied data)."""


class FindxRuntimeError(FindxError):
    """A runtime error."""


class MissingArgumentError(FindxSyntaxError):
    def __init__(self) -> None:
        super().__init__("Missing command-line argument")


class UnexpectedArgumentError(FindxSyntaxError):
    def __init__(self, arg: str, expected_arg: str) -> None:
        super().__init__(
            f"Got argument {repr(arg)}, expected {repr(expected_arg)}"
        )


class MissingXargError(FindxSyntaxError):
    def __init__(self) -> None:
        super().__init__("Missing required xarg")


class InvalidOptionError(FindxSyntaxError):
    def __init__(self, bad_option: str) -> None:
        super().__init__("Invalid command-line option %s" % repr(bad_option))


class PrintWithXargsError(FindxSyntaxError):
    def __init__(self) -> None:
        super().__init__("Cannot mix '-print' with XARGS")


class InvalidConfigLineError(FindxSyntaxError):
    def __init__(self, source: str, line: str, reason: str) -> None:
        super().__init__(f"In {source} for line {repr(line)}: {reason}")


class InvalidConfigVarError(FindxSyntaxError):
    def __init__(self, source: str, var: str) -> None:
        super().__init__(f"In {source} variable {repr(var)} is invalid")


class InvalidConfigValueError(FindxSyntaxError):
    def __init__(self, source: str, var: str, reason: Exception) -> None:
        super().__init__(f"In {source} for variable {repr(var)}: {reason}")


class InvalidEmptyConfigVarError(FindxSyntaxError):
    def __init__(self, var: str) -> None:
        super().__init__("Variable %s must not be empty" % (repr(var)))


class InvalidScalarConfigVarError(FindxSyntaxError):
    def __init__(self, var: str) -> None:
        super().__init__("Variable %s must be a single value" % (repr(var)))


class InvalidChoiceConfigVarError(FindxSyntaxError):
    def __init__(self, var: str, choices: T.List[str]) -> None:
        super().__init__(
            "Variable {} must be one of: {}".format(
                repr(var), ", ".join(choices)
            )
        )


class ConfigFilesUnstableError(FindxSyntaxError):
    def __init__(self) -> None:
        super().__init__("'config_files' setting does not stabilize")


class InvalidRootError(FindxRuntimeError):
    def __init__(self, root: str) -> None:
        super().__init__("Invalid root path %s" % repr(root))


class ExecutableNotFoundError(FindxRuntimeError):
    def __init__(self, executable: str) -> None:
        super().__init__("Executable %s not found" % repr(executable))


def must_find_executable(name: str) -> str:
    executable_abs_path = shutil.which(name)
    if executable_abs_path is None:
        raise ExecutableNotFoundError(name)
    return executable_abs_path


def map_find_status(find_status: int) -> int:
    if 1 <= find_status <= 19:
        return 100 + find_status
    elif 20 <= find_status <= 127:
        return 120
    else:
        return find_status


def map_xargs_status(xargs_status: int) -> int:
    if xargs_status == 1:
        return 121
    elif 2 <= xargs_status <= 122:
        return 122
    else:
        return xargs_status


def merge_find_xargs_status(find_status: int, xargs_status: int) -> int:
    if find_status >= 128:
        exit_status = find_status
    elif xargs_status >= 128:
        exit_status = xargs_status
    elif find_status != 0 and xargs_status != 0:
        exit_status = 100
    elif find_status != 0:
        exit_status = map_find_status(find_status)
    else:
        exit_status = map_xargs_status(xargs_status)
    return exit_status


def parse_raw_value(raw_value: str) -> T.Tuple[str, T.List[str]]:
    if raw_value.startswith(("+", "-", "^", "=")):
        op = raw_value[0]
        raw_value = raw_value[1:]
    else:
        op = "="
    value = quoted_split(raw_value)
    return op, value


# For Python 3.10+.
# This fails on Python 3.8 and 3.9 for `pip install`.
# It works, however, for PyInstaller builds for Python 3.8+.
def readme_from_importlib() -> str:
    meta = importlib.metadata.metadata(project_name)
    text = meta["Description"] or ""
    return text.strip()


# Required on Python 3.8 and 3.9 for `pip install`.
def readme_from_pkg_resources() -> str:
    import email
    import textwrap

    try:
        # `pkg_resources` comes from `setuptools` which might not be installed.
        # It is also deprecated. so we squelch warnings during import.
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import pkg_resources
    except ImportError:
        return ""

    try:
        dist = pkg_resources.get_distribution(project_name)
        meta = dist.get_metadata(dist.PKG_INFO)
    except (pkg_resources.DistributionNotFound, FileNotFoundError):
        return ""
    msg = email.message_from_string(meta)
    desc = msg.get("Description", "").strip()
    payload = msg.get_payload()
    if not desc and isinstance(payload, str):
        desc = payload.strip()
    if "\n" in desc:
        first, rest = desc.split("\n", 1)
        desc = "\n".join([first, textwrap.dedent(rest)])
    return desc


def readme() -> None:
    desc = readme_from_importlib()
    if not desc:
        desc = readme_from_pkg_resources()
    if not desc:
        desc = "README.rst is not available."
    print(desc)


class Settings(T.MutableMapping[str, str]):
    def __init__(self, name: str) -> None:
        self._name = name

    def __setitem__(self, key: str, val: str) -> None:
        raise ValueError("non-mutable Settings() class")

    def __delitem__(self, key: str) -> None:
        raise ValueError("non-mutable Settings() class")

    @property
    def name(self) -> str:
        return self._name


class CommandLineSettings(Settings):
    def __getitem__(self, key: str) -> str:
        return self._dict[key]

    def __len__(self) -> int:
        return len(self._dict)

    def __iter__(self) -> T.Iterator[str]:
        yield from self._dict

    def __setitem__(self, key: str, val: str) -> None:
        self._dict[key] = val

    def __delitem__(self, key: str) -> None:
        del self._dict[key]

    def __init__(self) -> None:
        super().__init__("[command line]")
        self._dict: T.Dict[str, str] = {}


class EnvVarSettings(Settings):
    _prefix = "FINDX_"

    def __getitem__(self, key: str) -> str:
        env_var = self._prefix + key.upper()
        return os.environ[env_var]

    def __len__(self) -> int:
        return len(list(self.__iter__()))

    def __iter__(self) -> T.Iterator[str]:
        for var in os.environ:
            if var.startswith(self._prefix):
                yield var[len(self._prefix) :].lower()

    def __init__(self) -> None:
        super().__init__("[Environment]")


class TextSettings(Settings):
    def __getitem__(self, key: str) -> str:
        return self._dict[key]

    def __len__(self) -> int:
        return len(self._dict)

    def __iter__(self) -> T.Iterator[str]:
        yield from self._dict

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._dict: T.Dict[str, str] = {}

    def set_text(self, text: str) -> None:
        for line in joined_lines(text.splitlines()):
            leading_whitespace, rest = split_leading_whitespace(line)
            if line.startswith("#") or not line:
                # Comment or blank line.
                pass
            elif leading_whitespace:
                raise InvalidConfigLineError(
                    self.name, line, "Unexpected indentation"
                )
            elif "=" in line:
                var, value = line.split("=", 1)
                var = var.rstrip()
                value = value.lstrip()
                if not var:
                    raise InvalidConfigLineError(
                        self.name, line, "Missing variable name"
                    )
                elif var in self._dict:
                    raise InvalidConfigLineError(
                        self.name, line, "Duplicate assignment"
                    )
                else:
                    self._dict[var] = value
            else:
                raise InvalidConfigLineError(self.name, line, "Missing '='")


class FileSettings(TextSettings):
    def __init__(self, path: str) -> None:
        super().__init__("config file %s" % repr(path))
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            with open(expanded_path) as f:
                self.set_text(f.read())


class Config:
    def __init__(self, valid_vars: T.List[str]) -> None:
        self._command_line_settings = CommandLineSettings()
        self._env_var_settings = EnvVarSettings()
        self._default_settings = TextSettings("[Default Settings]")
        self._default_settings.set_text(DEFAULT_CONFIG_TEXT)
        self._all_settings_files: T.Dict[str, FileSettings] = {}
        self._config_files: T.List[str] = []
        self._config_files_stable = False
        self._valid_vars = valid_vars

    def _sources(self) -> T.Iterator[Settings]:
        yield self._command_line_settings
        yield self._env_var_settings
        if not self._config_files_stable:
            self._config_files_stable = True
            for i in range(10):
                config_files = self.get("config_files")
                if config_files == self._config_files:
                    break
                self._config_files = config_files
            else:
                raise ConfigFilesUnstableError()
        for config_file in self._config_files:
            yield self._settings_file(config_file)
        yield self._default_settings

    def _settings_file(self, path: str) -> FileSettings:
        if path not in self._all_settings_files:
            settings = FileSettings(path)
            for var, raw_value in settings.items():
                if var not in self._valid_vars:
                    raise InvalidConfigVarError(settings.name, var)
                    try:
                        op, value = parse_raw_value(raw_value)
                    except ValueError as e:
                        raise InvalidConfigValueError(settings.name, var, e)
            self._all_settings_files[path] = settings
        return self._all_settings_files[path]

    def _merge_values(
        self, parent_value: T.List[str], op: str, value: T.List[str]
    ) -> T.List[str]:
        if op == "+":
            merged_value = parent_value + value
        elif op == "^":
            merged_value = value + parent_value
        elif op == "-":
            merged_value = parent_value[:]
            for v in value:
                if v in merged_value:
                    merged_value.remove(v)
        else:
            raise FindxInternalError("Invalid op %s" % repr(op))
        return merged_value

    def _get(
        self,
        var: str,
        sources: T.Iterable[Settings],
        op: str,
        value: T.List[str],
    ) -> T.List[str]:
        if op == "=":
            return value[:]
        for source in sources:
            if var in source:
                try:
                    source_op, source_value = parse_raw_value(source[var])
                except ValueError as e:
                    raise InvalidConfigValueError(source.name, var, e)
                parent_value = self._get(var, sources, source_op, source_value)
                break
        else:
            parent_value = []
        return self._merge_values(parent_value, op, value)

    def get(
        self, var: str, op: str = "+", value: T.List[str] = []
    ) -> T.List[str]:
        return self._get(var, self._sources(), op, value)

    def set(self, var: str, op: str, value: T.List[str]) -> None:
        list_value = self.get(var, op, value)
        self._command_line_settings[var] = quoted_join(list_value)
        if var == "config_files":
            self._config_files_stable = False


class Findx:
    OPTIONS_0 = []
    OPTIONS_1 = []
    OPTIONS_2 = []
    OPTIONS_VAR = []

    # PRE_PATH_OPTIONS must come before any paths.
    PRE_PATH_OPTIONS_0 = """
        -H -L -P -O0 -O1 -O2 -O3
        """.split()
    OPTIONS_0.extend(PRE_PATH_OPTIONS_0)

    PRE_PATH_OPTIONS_1 = """
        -D --files0-from
        """.split()
    OPTIONS_1.extend(PRE_PATH_OPTIONS_1)

    PRE_PATH_OPTIONS = PRE_PATH_OPTIONS_0 + PRE_PATH_OPTIONS_1

    # POST_PATH_OPTIONS must come immediately after any paths.
    POST_PATH_OPTIONS_0 = """
        -d -depth --help -help -ignore_readdir_race -mount
        -noignore_readdir_race -noleaf -nowarn -version --version -warn
        -xautofs -xdev
        """.split()
    OPTIONS_0.extend(POST_PATH_OPTIONS_0)

    POST_PATH_OPTIONS_1 = """
        -maxdepth -mindepth
        """.split()
    OPTIONS_1.extend(POST_PATH_OPTIONS_1)

    POST_PATH_OPTIONS = POST_PATH_OPTIONS_0 + POST_PATH_OPTIONS_1

    # Options that go before the expression.
    PRE_EXPR_OPTIONS = PRE_PATH_OPTIONS + POST_PATH_OPTIONS

    # Action options.
    ACTIONS_VAR = """
        -exec -execdir -ok -okdir
        """.split()
    OPTIONS_VAR.extend(ACTIONS_VAR)

    ACTIONS_0 = """
        -delete -ls -print -print0 -quit
        """.split()
    OPTIONS_0.extend(ACTIONS_0)

    ACTIONS_1 = """
        -fls -fprint -fprint0 -printf
        """.split()
    OPTIONS_1.extend(ACTIONS_1)

    ACTIONS_2 = """
        -fprintf
        """.split()
    OPTIONS_2.extend(ACTIONS_2)

    ACTIONS = ACTIONS_VAR + ACTIONS_0 + ACTIONS_1 + ACTIONS_2

    # Test options.
    TESTS_0 = """
        -daystart -empty -executable -false -follow -nogroup -nouser -prune
        -readable -true -writable
        """.split()
    OPTIONS_0.extend(TESTS_0)

    TESTS_1 = """
        -amin -anewer -atime -cmin -cnewer -context -ctime -fstype -gid -group
        -inum -iregex -links -mmin -mtime -newer -perm -regex -regextype
        -samefile -size -type -uid -used -user -xtype
        """.split()
    ref_types = "aBcmt"
    for x in ref_types:
        for y in ref_types:
            TESTS_1.append(f"-newer{x}{y}")
    OPTIONS_1.extend(TESTS_1)

    TESTS_WITH_GLOB = """
        -ilname -iname -ipath -iwholename -lname -name -path -wholename
        """.split()
    OPTIONS_1.extend(TESTS_WITH_GLOB)

    TESTS = TESTS_0 + TESTS_1 + TESTS_WITH_GLOB

    # All possible options.
    OPTIONS = OPTIONS_0 + OPTIONS_1 + OPTIONS_2 + OPTIONS_VAR

    UNARY_OPERATORS = """
        ! -not
        """.split()

    BINARY_OPERATORS = """
        , -a -and -o -or
        """.split()

    OPERATORS = UNARY_OPERATORS + BINARY_OPERATORS

    RESERVED_WORDS = OPTIONS + OPERATORS + ["(", ")"]

    META_CHARS = "*?|,"

    META_PAIRS = "[]{}"

    def __init__(self) -> None:
        self.pre_path_options: T.List[str] = []
        self.post_path_options: T.List[str] = []
        self.roots: T.List[str] = []
        self.excludes: T.List[str] = []
        self.includes: T.List[str] = []
        self.saw_action = False
        self.saw_print = False

        self.expression: T.List[str] = []
        self.in_xargs = False
        self.locked_in_xargs = False
        self.need_xarg = False
        self.xargs: T.List[str] = []
        self.find_pipe_args: T.List[str] = []
        self.xargs_pipe_args: T.List[str] = []
        self.show = False
        self.show_help = False
        self.show_version = False
        self.show_readme = False
        self.shown = False
        self.pipe_status: T.Optional[T.Tuple[int, ...]] = None
        self.config = Config(VALID_VARS)
        self.stdxd = False
        self.stdxf = False

    def get_var(self, var: str) -> T.List[str]:
        return self.config.get(var)

    def get_non_empty_var(self, var: str) -> T.List[str]:
        value = self.get_var(var)
        if not value:
            raise InvalidEmptyConfigVarError(var)
        return value

    def get_scalar_var(self, var: str) -> str:
        value = self.get_var(var)
        if len(value) != 1:
            raise InvalidScalarConfigVarError(var)
        return value[0]

    def get_choice_var(self, var: str, choices: T.List[str]) -> str:
        value = self.get_scalar_var(var)
        if value not in choices:
            raise InvalidChoiceConfigVarError(var, choices)
        return value

    def expand_path_var(self, path_var: str) -> T.List[str]:
        locations = self.get_non_empty_var(path_var)
        return [os.path.expanduser(p) for p in locations]

    def resolve_path_var(self, path_var: str) -> str:
        locations = self.expand_path_var(path_var)
        for tool in locations:
            if shutil.which(tool):
                return tool
        # Not found; fall back to first configured location.
        return locations[0]

    def run_args(self, args: T.List[str]) -> T.Tuple[int, bytes]:
        with open(os.devnull) as stdin:
            try:
                p = Popen(args, stdin=stdin, stdout=PIPE, stderr=STDOUT)
                output = p.communicate()[0]
                retcode = p.poll()
                if retcode is None:
                    retcode = 1
            except OSError:
                retcode = 1
                output = b""
            return retcode, output

    def probe_gnu_style(self, tool: str) -> str:
        retcode, output = self.run_args([tool, "--version"])
        if retcode == 0 and b"GNU" in output:
            style = "gnu"
        else:
            style = "bsd"
        return style

    def resolve_xargs_style(self, xargs_tool: str) -> str:
        choices = ["probe", "gnu", "bsd", "posix"]
        style = self.get_choice_var("xargs_style", choices)
        if style == "probe":
            style = self.probe_gnu_style(xargs_tool)
        return style

    def resolve_find_style(self, find_tool: str) -> str:
        choices = ["probe", "gnu", "bsd", "posix"]
        style = self.get_choice_var("find_style", choices)
        if style == "probe":
            style = self.probe_gnu_style(find_tool)
        return style

    def resolve_grep_style(self, grep_tool: str) -> str:
        choices = ["probe", "gnu", "bsd", "posix"]
        style = self.get_choice_var("grep_style", choices)
        if style == "probe":
            style = self.probe_gnu_style(grep_tool)
        return style

    def has_meta(self, s: str) -> bool:
        for c in self.META_CHARS:
            if c in s:
                return True
        # Paired characters cannot match one-character string.
        if len(s) > 1:
            for c in self.META_PAIRS:
                if c in s:
                    return True
        return False

    def matches_root(self, s: str) -> bool:
        return (
            s not in self.RESERVED_WORDS
            and not s.startswith("-")
            and (not self.has_meta(s) or os.path.exists(s))
        )

    def push_arg(self, arg: str) -> None:
        self.args.insert(0, arg)

    def push_arg_list(self, arg_list: T.List[str]) -> None:
        self.args[:0] = arg_list

    def peek_arg(self) -> str:
        try:
            return self.args[0]
        except IndexError:
            raise MissingArgumentError()

    def pop_arg(self) -> str:
        try:
            return self.args.pop(0)
        except IndexError:
            raise MissingArgumentError()

    def pop_expected_arg(self, expected_arg: str) -> str:
        arg = self.pop_arg()
        if arg != expected_arg:
            raise UnexpectedArgumentError(arg, expected_arg)
        return arg

    def launder_char_class(self, s: str) -> str:
        return re.sub(r"\[[^]]*?\]", lambda m: "\x00" * len(m.group(0)), s)

    def find_multi(
        self,
        s: str,
        hit_list: T.List[str],
        start: int = 0,
        end: T.Optional[int] = None,
    ) -> T.Tuple[int, str]:
        """Return (hit_pos, hit_string) for first hit_string in hit_list found.

        Returns (-1, '') if no match.
        """

        hit_pos = -1
        hit_string = ""
        if end is None:
            end = len(s)
        for h in hit_list:
            i = s.find(h, start, end)
            if i >= 0 and (hit_pos < 0 or i < hit_pos):
                hit_pos = i
                hit_string = h
        return hit_pos, hit_string

    def find_braced_range(self, s: str, start: int = 0) -> T.Tuple[int, int]:
        """Return range (start, end) inside outermost braces."""

        clean_str = self.launder_char_class(s)
        while start < len(clean_str):
            c = clean_str[start]
            start += 1
            if c == "{":
                end = start
                depth = 1
                while end < len(clean_str):
                    if clean_str[end] == "{":
                        depth += 1
                    elif clean_str[end] == "}":
                        depth -= 1
                        if depth == 0:
                            return (start, end)
                    end += 1
        return (-1, -1)

    def launder_char_class_and_braces(self, s: str) -> str:
        s = self.launder_char_class(s)
        start = 0
        while True:
            start, end = self.find_braced_range(s, start)
            if start >= 0:
                s = s[:start] + "\x00" * (end - start) + s[end:]
                start = end
            else:
                break
        return s

    def find_cut_points(self, s: str) -> T.List[int]:
        """
        Scan for ',' or '|' outside of all brackets and braces,
        return list of indices of all such commas and pipes.
        """

        clean_s = self.launder_char_class_and_braces(s)
        start = 0
        cut_points = []
        while start < len(clean_s):
            hit_pos, hit_string = self.find_multi(clean_s, ["|", ","], start)
            if hit_string:
                cut_points.append(hit_pos)
                start = hit_pos + 1
            else:
                break
        return cut_points

    def split_glob_outside_braces(self, glob: str) -> T.List[str]:
        cut_points = self.find_cut_points(glob)
        pieces = []
        start = 0
        for p in cut_points + [len(glob)]:
            pieces.append(glob[start:p])
            start = p + 1
        return pieces

    def split_glob(self, glob: str) -> T.List[str]:
        output_hopper = []
        input_hopper = self.split_glob_outside_braces(glob)
        while input_hopper:
            glob = input_hopper.pop(0)
            start = 0
            while True:
                start, end = self.find_braced_range(glob, start)
                if start < 0:
                    if glob:
                        output_hopper.append(glob)
                    break
                middles = self.split_glob_outside_braces(glob[start:end])
                if len(middles) > 1:
                    pre = glob[: start - 1]
                    post = glob[end + 1 :]
                    input_hopper[:0] = [pre + mid + post for mid in middles]
                    break
        if not output_hopper:
            output_hopper.append("")
        return output_hopper

    def distribute_option(
        self, option: str, params: T.List[str]
    ) -> T.List[str]:
        if len(params) <= 1:
            option_list = [option] + params
        else:
            option_list = []
            for p in params:
                if option_list:
                    option_list.append("-o")
                option_list.extend([option, p])
            option_list = ["("] + option_list + [")"]
        return option_list

    def expand_test_with_glob(self, test: str, glob: str) -> T.List[str]:
        return self.distribute_option(test, self.split_glob(glob))

    def get_option_list(self) -> T.List[str]:
        option = self.pop_arg()
        option_list = [option]
        if option in self.OPTIONS_1:
            option_list.append(self.pop_arg())
        elif option in self.OPTIONS_2:
            option_list.append(self.pop_arg())
            option_list.append(self.pop_arg())
        elif option in self.OPTIONS_VAR:
            while True:
                option_list.append(self.pop_arg())
                if option_list[-1] in [";", "+"]:
                    break
        elif option not in self.OPTIONS_0:
            raise InvalidOptionError(option)
        return option_list

    def get_optional_term(self) -> T.List[str]:
        arg = self.peek_arg()
        if arg == "(":
            term = [self.pop_arg()]
            term.extend(self.get_expression())
            term.append(self.pop_expected_arg(")"))
        elif arg in self.UNARY_OPERATORS:
            term = [self.pop_arg()]
            term.extend(self.get_term())
        elif arg in self.PRE_EXPR_OPTIONS:
            term = []
        elif arg in self.OPTIONS:
            term = self.get_option_list()
        elif self.has_meta(arg):
            term = ["-path" if "/" in arg else "-name", self.pop_arg()]
        else:
            term = []
        if term:
            if term[0] == "-type":
                # Convert '-type ab' to '( -type a -o -type b )'.
                term = self.distribute_option(term[0], list(term[1]))
            elif term[0] in self.TESTS_WITH_GLOB:
                term = self.expand_test_with_glob(*term)
            elif term[0] in self.ACTIONS:
                self.saw_action = True
                if term[0] == "-print":
                    self.saw_print = True
        return term

    def get_term(self) -> T.List[str]:
        term = self.get_optional_term()
        if not term:
            if self.args:
                raise InvalidOptionError(self.peek_arg())
            else:
                raise MissingArgumentError()
        return term

    def get_expression(self) -> T.List[str]:
        expr = self.get_term()
        while self.args:
            if self.peek_arg() in self.BINARY_OPERATORS:
                expr.append(self.pop_arg())
                expr.extend(self.get_term())
            else:
                opt_term = self.get_optional_term()
                if opt_term:
                    expr.extend(opt_term)
                else:
                    break
        return expr

    def or_extend(self, base: T.List[str], extension: T.List[str]) -> None:
        if base and extension:
            base.append("-o")
        base.extend(extension)

    def parse_include_exclude(self, include_exclude: T.List[str]) -> None:
        self.or_extend(include_exclude, self.get_term())

    def switch_to_var(self, switch: str) -> str:
        return switch.lstrip("-").replace("-", "_")

    def _make_setting(self, var: str, value: T.List[str]) -> str:
        quoted_value = quoted_join(value)
        if quoted_value:
            quoted_value = " " + quoted_value
        return f"{var} ={quoted_value}"

    def parse_findx_arg_show(self, arg: str) -> bool:
        parsed = True
        if arg in ["-help", "--help"]:
            self.show_help = True
        elif arg in ["-version", "--version"]:
            self.show_version = True
        elif arg in ["-readme", "--readme"]:
            self.show_readme = True
        elif arg == "-show":
            self.show = True
        elif arg == "-show-var":
            var = self.pop_arg()
            print(self._make_setting(var, self.config.get(var)))
            self.shown = True
        elif arg == "-show-vars":
            for var in VALID_VARS:
                print(self._make_setting(var, self.config.get(var)))
            self.shown = True
        elif arg == "-show-defaults":
            print(DEFAULT_CONFIG_TEXT)
            self.shown = True
        else:
            parsed = False
        return parsed

    def parse_findx_arg_abbrev(self, arg: str) -> bool:
        parsed = True
        if arg == "-stdx":
            self.push_arg_list(["-stdxd", "-stdxf"])
        elif arg == "-ff":
            self.push_arg_list(["-L", "-type", "f"])
        elif arg == "-ffx":
            self.push_arg_list(["-stdx", "-ff"])
        elif arg == "-ffg":
            self.push_arg_list(["-ffx", "-grep"])
        else:
            parsed = False
        return parsed

    def parse_findx_arg_exclude(self, arg: str) -> bool:
        parsed = True
        if arg == "-stdxd":
            self.stdxd = True
        elif arg == "-stdxf":
            self.stdxf = True
        elif arg in ["-e", "-x"]:
            self.parse_include_exclude(self.excludes)
        elif arg == "-i":
            if self.peek_arg() == "*":
                self.pop_arg()
                self.includes = []
                self.excludes = []
                self.stdxd = False
                self.stdxf = False
            else:
                self.parse_include_exclude(self.includes)
        else:
            parsed = False
        return parsed

    def parse_findx_arg(self, arg: str) -> None:
        if self.parse_findx_arg_show(arg):
            pass
        elif self.parse_findx_arg_abbrev(arg):
            pass
        elif self.parse_findx_arg_exclude(arg):
            pass
        elif arg == "-root":
            self.roots.append(self.pop_arg())
        elif arg == "-grep":
            grep_tool = self.resolve_path_var("grep_path")
            grep_style = self.resolve_grep_style(grep_tool)
            grep_args = self.get_var(grep_style + "_grep_args")
            self.push_arg_list([":", grep_tool] + grep_args + ["[", ":"])
        elif arg in self.PRE_PATH_OPTIONS:
            self.push_arg(arg)
            self.pre_path_options.extend(self.get_option_list())
        elif arg in self.POST_PATH_OPTIONS:
            self.push_arg(arg)
            self.post_path_options.extend(self.get_option_list())
        elif self.matches_root(arg):
            self.roots.append(arg)
        elif arg.startswith("--"):
            var = self.switch_to_var(arg[len("--") :])
            if var not in VALID_VARS:
                raise InvalidOptionError(arg)
            raw_value = self.pop_arg()
            try:
                op, value = parse_raw_value(raw_value)
            except ValueError as e:
                raise InvalidConfigValueError("Command line", var, e)
            self.config.set(var, op, value)
        else:
            self.push_arg(arg)
            self.expression.extend(self.get_expression())

    def iname_globs(self, globs: T.List[str]) -> T.List[str]:
        expr = []
        for g in globs:
            expr.extend(self.split_glob(g))
        if expr:
            expr = self.distribute_option("-iname", expr)
        return expr

    def parse_findx_args(self, args: T.List[str]) -> None:
        self.args = list(args)
        while self.args:
            arg = self.pop_arg()
            if arg == "[" and not self.locked_in_xargs:
                self.in_xargs = False
            elif self.in_xargs:
                self.xargs.append(arg)
                self.need_xarg = False
            elif arg == "]":
                self.in_xargs = True
            elif arg == "]]":
                self.in_xargs = True
                self.locked_in_xargs = True
            elif arg == ":":
                self.in_xargs = True
                self.need_xarg = True
            elif arg == "::":
                self.in_xargs = True
                self.need_xarg = True
                self.locked_in_xargs = True
            else:
                self.parse_findx_arg(arg)
        if self.need_xarg:
            raise MissingXargError()

        if self.saw_print and self.xargs:
            raise PrintWithXargsError()

        if not self.roots:
            self.roots.append(".")

    def parse_command_line(self, args: T.List[str]) -> None:
        self.parse_findx_args(args)
        find_tool = self.resolve_path_var("find_path")
        find_style = self.resolve_find_style(find_tool)
        have_print_zero = find_style in ["gnu", "bsd"]
        self.find_pipe_args = (
            [find_tool]
            + self.pre_path_options
            + self.roots
            + self.post_path_options
        )

        std_excludes: T.List[str] = []
        if self.stdxd:
            expr = self.iname_globs(self.get_var("stdxd"))
            if expr:
                self.or_extend(std_excludes, ["-type", "d"] + expr)
        if self.stdxf:
            expr = self.iname_globs(self.get_var("stdxf"))
            if expr:
                self.or_extend(std_excludes, ["-not", "-type", "d"] + expr)
        self.or_extend(std_excludes, self.excludes)
        self.excludes = std_excludes

        if self.excludes:
            self.find_pipe_args.extend(["("] + self.excludes + [")"])
            if self.includes:
                self.find_pipe_args.extend(["!", "("] + self.includes + [")"])
            self.find_pipe_args.append("-prune")
            self.find_pipe_args.append("-o")
        if self.expression:
            self.expression.insert(0, "(")
            self.expression.append(")")
        self.find_pipe_args.extend(self.expression)
        need_print = not self.saw_action and (self.xargs or self.excludes)
        print_action = "-print"
        if self.xargs:
            xargs_tool = self.resolve_path_var("xargs_path")
            xargs_style = self.resolve_xargs_style(xargs_tool)
            self.xargs_pipe_args = [xargs_tool]
            have_dash_zero = xargs_style in ["gnu", "bsd"]
            if have_dash_zero and have_print_zero:
                self.xargs_pipe_args.append("-0")
                print_action = "-print0"
            if xargs_style == "gnu":
                self.xargs_pipe_args.append("--no-run-if-empty")
            self.xargs_pipe_args.extend(self.xargs)
        else:
            self.xargs_pipe_args = []
        if need_print:
            self.find_pipe_args.append(print_action)

    def run(self) -> int:
        self.pipe_status = None
        exit_status = 0
        if self.show_help:
            self.help()
        elif self.show_version:
            print(
                "%s version %s"
                % (project_name, importlib.metadata.version(project_name))
            )
        elif self.show_readme:
            readme()
        elif self.show:
            s = " ".join(self.find_pipe_args)
            if self.xargs_pipe_args:
                s += " | " + " ".join(self.xargs_pipe_args)
            print(s)
        elif not self.shown:
            for d in self.roots:
                if not os.path.exists(d):
                    raise InvalidRootError(d)
            find_abs_path = must_find_executable(self.find_pipe_args[0])
            if self.xargs_pipe_args:
                xargs_abs_path = must_find_executable(self.xargs_pipe_args[0])
                find_proc = Popen(
                    self.find_pipe_args, stdout=PIPE, executable=find_abs_path
                )
                xargs_proc = Popen(
                    self.xargs_pipe_args,
                    stdin=find_proc.stdout,
                    executable=xargs_abs_path,
                )
                find_proc.wait()
                xargs_proc.wait()
                find_status = find_proc.returncode
                xargs_status = xargs_proc.returncode
                self.pipe_status = (find_status, xargs_status)
                exit_status = merge_find_xargs_status(
                    find_status, xargs_status
                )
            else:
                find_proc = Popen(
                    self.find_pipe_args, executable=find_abs_path
                )
                find_proc.wait()
                find_status = find_proc.returncode
                self.pipe_status = (find_status,)
                exit_status = merge_find_xargs_status(find_status, 0)
        return exit_status

    def help(self) -> None:
        print(HELP_TEXT)


def main() -> int:
    try:
        f = Findx()
        try:
            f.parse_command_line(sys.argv[1:])
            exit_status = f.run()
        except FindxSyntaxError as e:
            warn("Error: " + str(e))
            exit_status = 1
        except FindxRuntimeError as e:
            warn("Error: " + str(e))
            exit_status = 2
        except KeyboardInterrupt:
            exit_status = 128 + signal.SIGINT
    except Exception:
        warn("uncaught exception:")
        traceback.print_exc()
        exit_status = 3
    return exit_status


def ffx() -> int:
    sys.argv.insert(1, "-ffx")
    return main()


def ffg() -> int:
    sys.argv.insert(1, "-ffg")
    return main()


if __name__ == "__main__":
    sys.exit(main())
