#!/usr/bin/env python2

__VERSION__ = '0.9.6'

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
                        symlinks; shortcut for "findx -stdx -type f -L"
  -ffg                  grep through files; shortcut for
                        "findx -ffx : grep -H --color=auto [ :"
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

import os
import sys
import re
import distutils.spawn
from subprocess import Popen, STDOUT, PIPE, check_output, CalledProcessError

class FindxError(Exception):
    def __str__(self):
        try:
            msg = self.msg
        except AttributeError:
            msg = self.__class__.__name__
        return msg + " " + ", ".join(map(repr, self.args))

class MissingArgumentError(FindxError):
    msg = "Error: Missing argument"

class MissingXargError(FindxError):
    msg = "Error: Missing required xarg"

class InvalidOptionError(FindxError):
    msg = "Error: Invalid option"

class InvalidDirectoryError(FindxError):
    msg = "Error: Invalid directory"

class PrintWithXargsError(FindxError):
    msg = "Error: Cannot mix '-print' with XARGS"

class ExecutableNotFoundError(FindxError):
    msg = "Error: Executable not found"

def mustFindExecutable(name):
    executableAbsPath = distutils.spawn.find_executable(name)
    if executableAbsPath is None:
        raise ExecutableNotFoundError(name)
    return executableAbsPath

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
    refTypes = "aBcmt"
    TESTS_1.extend(["-newer%s%s" % (x, y) for x in refTypes for y in refTypes])
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

    STDX_DIR_GLOB = "|".join("""
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

    STDX_FILE_GLOB = "|".join("""
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
        self.prePathOptions = []
        self.postPathOptions = []
        self.dirs = []
        self.excludes = []
        self.includes = []
        self.sawAction = False
        self.sawPrint = False

        self.expression = []
        self.inXargs = False
        self.lockedInXargs = False
        self.needXarg = False
        self.xargs = []
        self.findPipeArgs = []
        self.xargsPipeArgs = []
        self.show = False
        self.showHelp = False
        self.showVersion = False

        self.checkXargs()

    def checkXargs(self):
        try:
            output = check_output(['xargs', '--version'], stderr=STDOUT)

            # If --version is accepted, we probably already know in GNU grep,
            # but let's check and make sure.
            if 'GNU' in output:
                self.isGnuXargs = True
            else:
                self.isGnuXargs = False
        except CalledProcessError:
            self.isGnuXargs = False

    def hasMeta(self, s):
        for c in self.META_CHARS:
            if c in s:
                return True
        # Paired characters cannot match one-character string.
        if len(s) > 1:
            for c in self.META_PAIRS:
                if c in s:
                    return True
        return False

    def matchesDir(self, s):
        return (not self.hasMeta(s) and
                s not in self.RESERVED_WORDS and
                not s.startswith("-"))

    def pushArg(self, arg):
        self.args.insert(0, arg)

    def pushArgList(self, argList):
        self.args[:0] = argList

    def peekArg(self):
        try:
            return self.args[0]
        except IndexError:
            raise MissingArgumentError()

    def popArg(self):
        try:
            return self.args.pop(0)
        except IndexError:
            raise MissingArgumentError()

    def popRequiredArg(self, literal):
        arg = self.popArg()
        if arg != literal:
            raise MissingArgumentError(literal)
        return arg

    def launderCharClass(self, s):
        return re.sub(r"\[[^]]*?\]", lambda m: "\x00" * len(m.group(0)), s)

    def findMulti(self, s, hitList, start=0, end=None):
        """Return (hitPos, hitString) for first hitString in hitList found.

        Returns (-1, "") if no match.
        """

        hitPos = -1
        hitString = ""
        if end is None:
            end = len(s)
        for h in hitList:
            i = s.find(h, start, end)
            if i >= 0 and (hitPos < 0 or i < hitPos):
                hitPos = i
                hitString = h
        return hitPos, hitString

    def findBracedRange(self, s, start = 0):
        """Return range (start, end) inside outermost braces."""

        cleanStr = self.launderCharClass(s)
        while start < len(cleanStr):
            c = cleanStr[start]
            start += 1
            if c == "{":
                end = start
                depth = 1
                while end < len(cleanStr):
                    if cleanStr[end] == "{":
                        depth += 1
                    elif cleanStr[end] == "}":
                        depth -= 1
                        if depth == 0:
                            return (start, end)
                    end += 1
        return (-1, -1)

    def launderCharClassAndBraces(self, s):
        s = self.launderCharClass(s)
        start = 0
        while True:
            start, end = self.findBracedRange(s, start)
            if start >= 0:
                s = s[:start] + "\x00" * (end - start) + s[end:]
                start = end
            else:
                break
        return s

    def findCutPoints(self, s):
        """
        Scan for "," or "|" outside of all brackets and braces,
        return list of indices of all such commas and pipes.
        """

        cleanS = self.launderCharClassAndBraces(s)
        start = 0
        cutPoints = []
        while start < len(cleanS):
            hitPos, hitString = self.findMulti(cleanS, ["|", ","], start)
            if hitString:
                cutPoints.append(hitPos)
                start = hitPos + 1
            else:
                break
        return cutPoints

    def splitGlobOutsideBraces(self, glob):
        cutPoints = self.findCutPoints(glob)
        pieces = []
        start = 0
        for p in cutPoints + [len(glob)]:
            pieces.append(glob[start:p])
            start = p + 1
        return pieces

    def splitGlob(self, glob):
        outputHopper = []
        inputHopper = self.splitGlobOutsideBraces(glob)
        while inputHopper:
            glob = inputHopper.pop(0)
            start = 0
            while True:
                start, end = self.findBracedRange(glob, start)
                if start < 0:
                    if glob:
                        outputHopper.append(glob)
                    break
                middles = self.splitGlobOutsideBraces(glob[start:end])
                if len(middles) > 1:
                    pre = glob[:start - 1]
                    post = glob[end + 1:]
                    inputHopper[:0] = [pre + mid + post for mid in middles]
                    break
        if not outputHopper:
            outputHopper.append('')
        return outputHopper

    def distributeOption(self, option, params):
        if len(params) <= 1:
            optionList = [option] + params
        else:
            optionList = []
            for p in params:
                if optionList:
                    optionList.append("-o")
                optionList.extend([option, p])
            optionList = ["("] + optionList + [")"]
        return optionList

    def expandTestWithGlob(self, test, glob):
        return self.distributeOption(test, self.splitGlob(glob))

    def getOptionList(self):
        option = self.popArg()
        optionList = [option]
        if option in self.OPTIONS_1:
            optionList.append(self.popArg())
        elif option in self.OPTIONS_2:
            optionList.append(self.popArg())
            optionList.append(self.popArg())
        elif option in self.OPTIONS_VAR:
            while True:
                optionList.append(self.popArg())
                if optionList[-1] in [";", "+"]:
                    break
        elif option not in self.OPTIONS_0:
            raise InvalidOptionError(option)
        return optionList

    def getOptionalTerm(self):
        arg = self.peekArg()
        if arg == "(":
            term = [self.popArg()]
            term.extend(self.getExpression())
            term.append(self.popRequiredArg(")"))
        elif arg in self.UNARY_OPERATORS:
            term = [self.popArg()]
            term.extend(self.getTerm())
        elif arg in self.PRE_EXPR_OPTIONS:
            term = []
        elif arg in self.OPTIONS:
            term = self.getOptionList()
        elif self.hasMeta(arg):
            term = ["-name", self.popArg()]
        else:
            term = []
        if term:
            if term[0] == "-type":
                # Convert "-type ab" to "( -type a -o -type b )".
                term = self.distributeOption(term[0], list(term[1]))
            elif term[0] in self.TESTS_WITH_GLOB:
                term = self.expandTestWithGlob(*term)
            elif term[0] in self.ACTIONS:
                self.sawAction = True
                if term[0] == "-print":
                    self.sawPrint = True
        return term

    def getTerm(self):
        term = self.getOptionalTerm()
        if not term:
            if self.args:
                raise InvalidOptionError(self.peekArg())
            else:
                raise MissingArgumentError()
        return term

    def getExpression(self):
        expr = self.getTerm()
        while self.args:
            if self.peekArg() in self.BINARY_OPERATORS:
                expr.append(self.popArg())
                expr.extend(self.getTerm())
            else:
                optTerm = self.getOptionalTerm()
                if optTerm:
                    expr.extend(optTerm)
                else:
                    break
        return expr

    def orExtend(self, base, extension):
        if base:
            base.append("-o")
        base.extend(extension)

    def parseIncludeExclude(self, includeExclude):
        self.orExtend(includeExclude, self.getTerm())

    def parseFindxArgs(self):
        arg = self.popArg()
        if arg in ["-help", "--help"]:
            self.showHelp = True
        elif arg in ["-version", "--version"]:
            self.showVersion = True
        elif arg == "-show":
            self.show = True
        elif arg == "-root":
            self.dirs.append(self.popArg())
        elif arg == "-stdx":
            self.pushArgList(["-x", "(",
                "-type", "d", "-iname", self.STDX_DIR_GLOB,
                "-o",
                "-not", "-type", "d", "-iname", self.STDX_FILE_GLOB,
                ")"])
        elif arg == "-ffx":
            self.pushArgList(["-stdx", "-L", "-type", "f"])
        elif arg == "-ffg":
            self.pushArgList(["-ffx", ":", "grep", "-H", "--color=auto",
                "[", ":"])
        elif arg in ["-e", "-x"]:
            self.parseIncludeExclude(self.excludes)
        elif arg == "-i":
            if self.peekArg() == "*":
                self.popArg()
                self.includes = []
                self.excludes = []
            else:
                self.parseIncludeExclude(self.includes)
        elif arg in self.PRE_PATH_OPTIONS:
            self.pushArg(arg)
            self.prePathOptions.extend(self.getOptionList())
        elif arg in self.POST_PATH_OPTIONS:
            self.pushArg(arg)
            self.postPathOptions.extend(self.getOptionList())
        elif self.matchesDir(arg):
            self.dirs.append(arg)
        else:
            self.pushArg(arg)
            self.expression.extend(self.getExpression())

    def parseCommandLine(self, args):
        self.args = list(args)
        while self.args:
            arg = self.popArg()
            if arg == "[" and not self.lockedInXargs:
                self.inXargs = False
            elif self.inXargs:
                self.xargs.append(arg)
                self.needXarg = False
            elif arg == "]":
                self.inXargs = True
            elif arg == "]]":
                self.inXargs = True
                self.lockedInXargs = True
            elif arg == ":":
                self.inXargs = True
                self.needXarg = True
            elif arg == "::":
                self.inXargs = True
                self.needXarg = True
                self.lockedInXargs = True
            else:
                self.pushArg(arg)
                self.parseFindxArgs()
        if self.needXarg:
            raise MissingXargError()

        if self.sawPrint and self.xargs:
            raise PrintWithXargsError()

        if not self.dirs:
            self.dirs.append(".")

        self.findPipeArgs = (
                ["find"] +
                self.prePathOptions +
                self.dirs +
                self.postPathOptions)
        if self.excludes:
            self.findPipeArgs.extend(["("] + self.excludes + [")"])
            if self.includes:
                self.findPipeArgs.extend(["!", "("] + self.includes + [")"])
            self.findPipeArgs.append("-prune")
            self.findPipeArgs.append("-o")
        if self.expression:
            self.expression.insert(0, "(")
            self.expression.append(")")
        self.findPipeArgs.extend(self.expression)
        if not self.sawAction:
            if self.xargs:
                self.findPipeArgs.append("-print0")
            elif self.excludes:
                self.findPipeArgs.append("-print")
        if self.xargs:
            self.xargsPipeArgs = ["xargs", "-0"]
            if self.isGnuXargs:
                self.xargsPipeArgs.append("--no-run-if-empty")
            self.xargsPipeArgs.extend(self.xargs)
        else:
            self.xargsPipeArgs = []

    def run(self):
        if self.showHelp:
            self.help()
        elif self.showVersion:
            print 'findx version', __VERSION__
        elif self.show:
            s = " ".join(self.findPipeArgs)
            if self.xargsPipeArgs:
                s += " | " + " ".join(self.xargsPipeArgs)
            print s
        else:
            for d in self.dirs:
                if not os.path.isdir(d):
                    raise InvalidDirectoryError(d)
            findAbsPath = mustFindExecutable(self.findPipeArgs[0])
            if self.xargsPipeArgs:
                xargsAbsPath = mustFindExecutable(self.xargsPipeArgs[0])
                findProc = Popen(self.findPipeArgs, stdout=PIPE,
                                 executable=findAbsPath)
                xargsProc = Popen(self.xargsPipeArgs, stdin=findProc.stdout,
                                 executable=xargsAbsPath)
                findProc.wait()
                xargsProc.wait()
            else:
                findProc = Popen(self.findPipeArgs, executable=findAbsPath)
                findProc.wait()

    def help(self):
        print HELP_TEXT

def main():
    f = Findx()
    try:
        f.parseCommandLine(sys.argv[1:])
        f.run()
    except FindxError, e:
        print e
    except KeyboardInterrupt, e:
        print "<break>"

def ffx():
    sys.argv.insert(1, "-ffx")
    main()

def ffg():
    sys.argv.insert(1, "-ffg")
    main()

if __name__ == "__main__":
    main()
