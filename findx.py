#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import re
import distutils.spawn
from subprocess import Popen, STDOUT, PIPE, check_output, CalledProcessError

__version__ = '0.9.6'

HELP_TEXT = """\
Usage: findx [OPTION | FINDOPTION | DIR | METAGLOB]*
  or:  findx [OPTION | FINDOPTION | DIR | METAGLOB]* : [XARG]+

Additional shortcut commands:

  ffx:  findx -ffx
  ffg:  findx -ffg

Provides shortcuts for the following 'find' idioms:
    find DIRLIST   EXPRESSION
    find DIRLIST ( EXPRESSION ) -print0 | xargs -0 XARGLIST

The OPTION, FINDOPTION, DIR, and METAGLOB options may be specified in any order
while in FINDX MODE.  The XARGs are kept in-order while in XARGS MODE.

OPTION      An option to findx (specified below).

FINDOPTION  A standard 'find' option to be appended to EXPRESSION.
            ('man find' or 'find --help' for details.)

DIR         A directory to be appended to DIRLIST.
            DIR must not contain METACHARACTERS.

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
            except ']' may be "quoted" via square brackets.  Examples:

            -name one|two           ( -name one -o -name two )
            -name one,two           ( -name one -o -name two )
            -name *.{c,cpp}         ( -name *.c -o -name *.cpp )
            -name quoted[,]comma    -name quoted,comma

            Extended GLOBs are recognized after the following 'find' tests:
            -ilname -iname -ipath -wholename -lname -name -path -wholename

Extensions to FINDOPTIONS

  In addition to extended GLOBs, the '-type' option is extended to accept
  multiple type characters which are logically OR'ed.  Examples:
            -type fd                ( -type f -o -type d )
            -type f                 -type f

OPTIONS

  -help, --help         print this usage help and terminate
  -version, --version   print version of findx and terminate
  -show                 show command without executing it
  -root DIR             add arbitrary DIR to DIRLIST
  -x EXCLUDE            add EXCLUDE to list of exclusions
  -i INCLUDE            add INCLUDE to list of inclusions (disable exclusions
                        by including everything via '-i *')
  -stdx                 setup standard exclusions
  -ffx                  find files with standard exclusions, following
                        symlinks; shortcut for 'findx -stdx -type f -L'
  -ffg                  grep through files; shortcut for
                        'findx -ffx : grep -H --color=auto [ :'
  :                     switch to XARGS MODE; require subsequent xarg
  ::                    permanent XARGS MODE; require subsequent xarg
  [                     switch to FINDX MODE from FINDX MODE or XARGS MODE
  ]                     switch to XARGS MODE
  ]]                    switch to XARGS MODE permanently

Note: FINDX MODE is active at start.  The '[' option does not necessitate ']'.
A bare '[' may not be used as an XARG unless XARGS MODE has been made
permanent via '::' or ']]'.

EXCLUSIONS, INCLUSIONS
  Exclusions and inclusions are arbitrary 'find' terms, not full 'find'
  expressions.  Loosely, a term extends to the next AND or OR operator
  (including the AND implied between consecutive terms).  Parenthesized
  expressions count as a term.
  If exclusions are present, they are logically OR'ed as follows:
    find ( EXCLUDE1 -o EXCLUDE2 ... ) -prune -o EXPRESSION
  Inclusions override exclusions; if both are present, the pruning becomes:
    find ( EXCLUDE1 -o EXCLUDE2 ... ) ! ( INCLUDE1 -o INCLUDE2 ... ) -prune
  An inclusion of '-i *' resets previously specified exclusions and inclusions.

  Examples:
    # Exclude *.txt, *.TXT, etc.
    -x -iname *.txt

    # Exclude anything with a '.' in the name, but include '*.txt'.
    -x -name *.* -i *.txt

    # Exclude .svn directories and files named '*.bak', but include 'f.bak'.
    # NOTE that '-i' requires '-name' because f.bak has no metacharacters.
    -x ( -type d -name .svn -o -type f -name *.bak ) -i -name f.bak

STANDARD EXCLUSIONS
  When '-stdx' is specified, a built-in list of standard exclusions applies.
  (Use '-show' to see the list.)

STANDARD ACTION
  If EXPRESSION contains no 'find' action (e.g., '-print', '-print0',
  '-delete', ...), a standard action will be appended to EXPRESSION.  The
  standard action is '-print0' when XARGS are present, and '-print' otherwise.

EXAMPLES

# Grep for 'main' in .c and .cpp files.
  findx *.{c,cpp} : grep main

# Grep for 'main' in .c and .cpp files, excluding .svn and CVS directories.
  findx *.{c,cpp} -x -name .svn,CVS : grep main

# Grep for 'main' in all files with standard exclusions.
  ffg main

# Grep for 'main' case-insensitively in all .c files under /work.
  ffg main -i [ '*.c' /work
  ffg -i [ '*.c' /work ] main
  ffg [ '*.c' /work : main -i

# Remove backup files with standard exclusions.
  ffx *~|*.bak : rm
  ffx *~|*.bak -delete

# All files and directories modified less than 1 day ago.
  findx -mtime 1

# List directories only with standard exclusions.
  findx -stdx -type d : ls -ld

# Look for directories only.
  findx -type d
  findx -type d : ls -ld

# Grep for 'main' excluding tmp directories.
  ffg main [ -x tmp

# Override pre-defined exclusions.
  findx -i '*'

# Use findx for no pre-defined exclusions, etc.
  findx -mtime -1

# Just files with standard exclusions (fails with newline in filename).
  ffx | while read i; do Something; done

"""


class FindxError(Exception):

    def __str__(self):
        try:
            msg = self.msg
        except AttributeError:
            msg = self.__class__.__name__
        return msg + ' ' + ', '.join(map(repr, self.args))


class MissingArgumentError(FindxError):
    msg = 'Error: Missing argument'


class MissingXargError(FindxError):
    msg = 'Error: Missing required xarg'


class InvalidOptionError(FindxError):
    msg = 'Error: Invalid option'


class InvalidDirectoryError(FindxError):
    msg = 'Error: Invalid directory'


class PrintWithXargsError(FindxError):
    msg = """Error: Cannot mix '-print' with XARGS"""


class ExecutableNotFoundError(FindxError):
    msg = 'Error: Executable not found'


def must_find_executable(name):
    executable_abs_path = distutils.spawn.find_executable(name)
    if executable_abs_path is None:
        raise ExecutableNotFoundError(name)
    return executable_abs_path


class Findx(object):
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
        -D
        """.split()
    OPTIONS_1.extend(PRE_PATH_OPTIONS_1)

    PRE_PATH_OPTIONS = PRE_PATH_OPTIONS_0 + PRE_PATH_OPTIONS_1

    # POST_PATH_OPTIONS must come immediately after any paths.
    POST_PATH_OPTIONS_0 = """
        -d -depth --help -help -ignore_readdir_race -mount
        -noignore_readdir_race -noleaf -nowarn --version --version -warn
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
    ref_types = 'aBcmt'
    for x in ref_types:
        for y in ref_types:
            TESTS_1.append('-newer%s%s' % (x, y))
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

    RESERVED_WORDS = OPTIONS + OPERATORS + ['(', ')']

    META_CHARS = '*?|,'

    META_PAIRS = '[]{}'

    STDX_DIR_GLOB = '|'.join("""
        .svn
        .git
        .bzr
        .hg
        .undo
        build
        *export
        pkgexp
        bak
        *.egg-info
        *.egg
        """.split())

    STDX_FILE_GLOB = '|'.join("""
        .*.sw?
        *.o
        *.a
        *.so
        *.ds
        *.os
        *.sbr
        *.pch
        *.pdb
        *.pyc
        *.pyo
        *.gz
        *.bin
        *.elf
        *.exe
        *.zip
        *.bmp
        *.ico
        *.gif
        *.jpg
        *.png
        *.pdf
        tags
        """.split())

    def __init__(self):
        self.pre_path_options = []
        self.post_path_options = []
        self.dirs = []
        self.excludes = []
        self.includes = []
        self.saw_action = False
        self.saw_print = False

        self.expression = []
        self.in_xargs = False
        self.locked_in_xargs = False
        self.need_xarg = False
        self.xargs = []
        self.find_pipe_args = []
        self.xargs_pipe_args = []
        self.show = False
        self.show_help = False
        self.show_version = False

        self.check_xargs()

    def check_xargs(self):
        try:
            output = check_output(['xargs', '--version'], stderr=STDOUT)

            # If --version is accepted, we probably already know in GNU grep,
            # but let's check and make sure.
            if b'GNU' in output:
                self.is_gnu_xargs = True
            else:
                self.is_gnu_xargs = False
        except CalledProcessError:
            self.is_gnu_xargs = False

    def has_meta(self, s):
        for c in self.META_CHARS:
            if c in s:
                return True
        # Paired characters cannot match one-character string.
        if len(s) > 1:
            for c in self.META_PAIRS:
                if c in s:
                    return True
        return False

    def matches_dir(self, s):
        return (not self.has_meta(s) and
                s not in self.RESERVED_WORDS and
                not s.startswith('-'))

    def push_arg(self, arg):
        self.args.insert(0, arg)

    def push_arg_list(self, arg_list):
        self.args[:0] = arg_list

    def peek_arg(self):
        try:
            return self.args[0]
        except IndexError:
            raise MissingArgumentError()

    def pop_arg(self):
        try:
            return self.args.pop(0)
        except IndexError:
            raise MissingArgumentError()

    def pop_required_arg(self, literal):
        arg = self.pop_arg()
        if arg != literal:
            raise MissingArgumentError(literal)
        return arg

    def launder_char_class(self, s):
        return re.sub(r'\[[^]]*?\]', lambda m: '\x00' * len(m.group(0)), s)

    def find_multi(self, s, hit_list, start=0, end=None):
        """Return (hit_pos, hit_string) for first hit_string in hit_list found.

        Returns (-1, '') if no match.
        """

        hit_pos = -1
        hit_string = ''
        if end is None:
            end = len(s)
        for h in hit_list:
            i = s.find(h, start, end)
            if i >= 0 and (hit_pos < 0 or i < hit_pos):
                hit_pos = i
                hit_string = h
        return hit_pos, hit_string

    def find_braced_range(self, s, start=0):
        """Return range (start, end) inside outermost braces."""

        clean_str = self.launder_char_class(s)
        while start < len(clean_str):
            c = clean_str[start]
            start += 1
            if c == '{':
                end = start
                depth = 1
                while end < len(clean_str):
                    if clean_str[end] == '{':
                        depth += 1
                    elif clean_str[end] == '}':
                        depth -= 1
                        if depth == 0:
                            return (start, end)
                    end += 1
        return (-1, -1)

    def launder_char_class_and_braces(self, s):
        s = self.launder_char_class(s)
        start = 0
        while True:
            start, end = self.find_braced_range(s, start)
            if start >= 0:
                s = s[:start] + '\x00' * (end - start) + s[end:]
                start = end
            else:
                break
        return s

    def find_cut_points(self, s):
        """
        Scan for ',' or '|' outside of all brackets and braces,
        return list of indices of all such commas and pipes.
        """

        clean_s = self.launder_char_class_and_braces(s)
        start = 0
        cut_points = []
        while start < len(clean_s):
            hit_pos, hit_string = self.find_multi(clean_s, ['|', ','], start)
            if hit_string:
                cut_points.append(hit_pos)
                start = hit_pos + 1
            else:
                break
        return cut_points

    def split_glob_outside_braces(self, glob):
        cut_points = self.find_cut_points(glob)
        pieces = []
        start = 0
        for p in cut_points + [len(glob)]:
            pieces.append(glob[start:p])
            start = p + 1
        return pieces

    def split_glob(self, glob):
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
                    pre = glob[:start - 1]
                    post = glob[end + 1:]
                    input_hopper[:0] = [pre + mid + post for mid in middles]
                    break
        if not output_hopper:
            output_hopper.append('')
        return output_hopper

    def distribute_option(self, option, params):
        if len(params) <= 1:
            option_list = [option] + params
        else:
            option_list = []
            for p in params:
                if option_list:
                    option_list.append('-o')
                option_list.extend([option, p])
            option_list = ['('] + option_list + [')']
        return option_list

    def expand_test_with_glob(self, test, glob):
        return self.distribute_option(test, self.split_glob(glob))

    def get_option_list(self):
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
                if option_list[-1] in [';', '+']:
                    break
        elif option not in self.OPTIONS_0:
            raise InvalidOptionError(option)
        return option_list

    def get_optional_term(self):
        arg = self.peek_arg()
        if arg == '(':
            term = [self.pop_arg()]
            term.extend(self.get_expression())
            term.append(self.pop_required_arg(')'))
        elif arg in self.UNARY_OPERATORS:
            term = [self.pop_arg()]
            term.extend(self.get_term())
        elif arg in self.PRE_EXPR_OPTIONS:
            term = []
        elif arg in self.OPTIONS:
            term = self.get_option_list()
        elif self.has_meta(arg):
            term = ['-name', self.pop_arg()]
        else:
            term = []
        if term:
            if term[0] == '-type':
                # Convert '-type ab' to '( -type a -o -type b )'.
                term = self.distribute_option(term[0], list(term[1]))
            elif term[0] in self.TESTS_WITH_GLOB:
                term = self.expand_test_with_glob(*term)
            elif term[0] in self.ACTIONS:
                self.saw_action = True
                if term[0] == '-print':
                    self.saw_print = True
        return term

    def get_term(self):
        term = self.get_optional_term()
        if not term:
            if self.args:
                raise InvalidOptionError(self.peek_arg())
            else:
                raise MissingArgumentError()
        return term

    def get_expression(self):
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

    def or_extend(self, base, extension):
        if base:
            base.append('-o')
        base.extend(extension)

    def parse_include_exclude(self, include_exclude):
        self.or_extend(include_exclude, self.get_term())

    def parse_findx_args(self):
        arg = self.pop_arg()
        if arg in ['-help', '--help']:
            self.show_help = True
        elif arg in ['-version', '--version']:
            self.show_version = True
        elif arg == '-show':
            self.show = True
        elif arg == '-root':
            self.dirs.append(self.pop_arg())
        elif arg == '-stdx':
            self.push_arg_list(
                ['-x', '(', '-type', 'd', '-iname', self.STDX_DIR_GLOB, '-o',
                 '-not', '-type', 'd', '-iname', self.STDX_FILE_GLOB, ')'])
        elif arg == '-ffx':
            self.push_arg_list(['-stdx', '-L', '-type', 'f'])
        elif arg == '-ffg':
            self.push_arg_list(['-ffx', ':', 'grep', '-H', '--color=auto',
                                '[', ':'])
        elif arg in ['-e', '-x']:
            self.parse_include_exclude(self.excludes)
        elif arg == '-i':
            if self.peek_arg() == '*':
                self.pop_arg()
                self.includes = []
                self.excludes = []
            else:
                self.parse_include_exclude(self.includes)
        elif arg in self.PRE_PATH_OPTIONS:
            self.push_arg(arg)
            self.pre_path_options.extend(self.get_option_list())
        elif arg in self.POST_PATH_OPTIONS:
            self.push_arg(arg)
            self.post_path_options.extend(self.get_option_list())
        elif self.matches_dir(arg):
            self.dirs.append(arg)
        else:
            self.push_arg(arg)
            self.expression.extend(self.get_expression())

    def parse_command_line(self, args):
        self.args = list(args)
        while self.args:
            arg = self.pop_arg()
            if arg == '[' and not self.locked_in_xargs:
                self.in_xargs = False
            elif self.in_xargs:
                self.xargs.append(arg)
                self.need_xarg = False
            elif arg == ']':
                self.in_xargs = True
            elif arg == ']]':
                self.in_xargs = True
                self.locked_in_xargs = True
            elif arg == ':':
                self.in_xargs = True
                self.need_xarg = True
            elif arg == '::':
                self.in_xargs = True
                self.need_xarg = True
                self.locked_in_xargs = True
            else:
                self.push_arg(arg)
                self.parse_findx_args()
        if self.need_xarg:
            raise MissingXargError()

        if self.saw_print and self.xargs:
            raise PrintWithXargsError()

        if not self.dirs:
            self.dirs.append('.')

        self.find_pipe_args = (
            ['find'] +
            self.pre_path_options +
            self.dirs +
            self.post_path_options)
        if self.excludes:
            self.find_pipe_args.extend(['('] + self.excludes + [')'])
            if self.includes:
                self.find_pipe_args.extend(['!', '('] + self.includes + [')'])
            self.find_pipe_args.append('-prune')
            self.find_pipe_args.append('-o')
        if self.expression:
            self.expression.insert(0, '(')
            self.expression.append(')')
        self.find_pipe_args.extend(self.expression)
        if not self.saw_action:
            if self.xargs:
                self.find_pipe_args.append('-print0')
            elif self.excludes:
                self.find_pipe_args.append('-print')
        if self.xargs:
            self.xargs_pipe_args = ['xargs', '-0']
            if self.is_gnu_xargs:
                self.xargs_pipe_args.append('--no-run-if-empty')
            self.xargs_pipe_args.extend(self.xargs)
        else:
            self.xargs_pipe_args = []

    def run(self):
        if self.show_help:
            self.help()
        elif self.show_version:
            print('findx version %s' % __version__)
        elif self.show:
            s = ' '.join(self.find_pipe_args)
            if self.xargs_pipe_args:
                s += ' | ' + ' '.join(self.xargs_pipe_args)
            print(s)
        else:
            for d in self.dirs:
                if not os.path.isdir(d):
                    raise InvalidDirectoryError(d)
            find_abs_path = must_find_executable(self.find_pipe_args[0])
            if self.xargs_pipe_args:
                xargs_abs_path = must_find_executable(self.xargs_pipe_args[0])
                find_proc = Popen(self.find_pipe_args, stdout=PIPE,
                                  executable=find_abs_path)
                xargs_proc = Popen(self.xargs_pipe_args,
                                   stdin=find_proc.stdout,
                                   executable=xargs_abs_path)
                find_proc.wait()
                xargs_proc.wait()
            else:
                find_proc = Popen(self.find_pipe_args,
                                  executable=find_abs_path)
                find_proc.wait()

    def help(self):
        print(HELP_TEXT)


def main():
    f = Findx()
    try:
        f.parse_command_line(sys.argv[1:])
        f.run()
    except FindxError as e:
        print(e)
    except KeyboardInterrupt as e:
        print('<break>')


def ffx():
    sys.argv.insert(1, '-ffx')
    main()


def ffg():
    sys.argv.insert(1, '-ffg')
    main()

if __name__ == '__main__':
    main()
