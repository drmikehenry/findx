#!/usr/bin/env python3


import textwrap
import typing as T

import pytest

import findx


def make_text(s: str) -> str:
    if s.startswith("\n"):
        s = s[1:]
    return textwrap.dedent(s)


def make_lines(s: str) -> T.List[str]:
    return make_text(s).splitlines()


def test_single_quoted() -> None:
    def s(s: str) -> str:
        return s.strip()

    assert findx.single_quoted(r"") == s(r"""               ''  """)
    assert findx.single_quoted(r"hello") == s(r"""               'hello'  """)
    assert findx.single_quoted(r"hello there") == s(
        r"""               'hello there'  """
    )
    assert findx.single_quoted(r'hello "Mike"') == s(
        r"""               'hello "Mike"'  """
    )
    assert findx.single_quoted(r"hello I'm Mike") == s(
        r"""               'hello I'\''m Mike'  """
    )
    assert findx.single_quoted(r"\Windows\system32") == s(
        r"""               '\Windows\system32'  """
    )
    assert findx.single_quoted(r"\Program Files") == s(
        r"""               '\Program Files'  """
    )
    assert findx.single_quoted(r"'") == s(r"""               \'  """)
    assert findx.single_quoted(r"''") == s(r"""               \'\'  """)
    assert findx.single_quoted(r"'two''words'") == s(
        r"""               \''two'\'\''words'\'  """
    )


def test_double_quoted() -> None:
    def s(s: str) -> str:
        return s.strip()

    assert findx.double_quoted(r"") == s(r"""               ""  """)
    assert findx.double_quoted(r"hello") == s(r"""               "hello"  """)
    assert findx.double_quoted(r"hello there") == s(
        r"""               "hello there"  """
    )
    assert findx.double_quoted(r'hello "Mike"') == s(
        r"""               "hello \"Mike\""  """
    )
    assert findx.double_quoted(r"""hello I'm Mike""") == s(
        r"""                 "hello I'm Mike"  """
    )
    assert findx.double_quoted(r"""\Windows\system32""") == s(
        r"""                 "\Windows\system32"  """
    )
    assert findx.double_quoted(r"""\Program Files""") == s(
        r"""                 "\Program Files"  """
    )
    assert findx.double_quoted(r"'") == s(r"""               "'"  """)
    assert findx.double_quoted(r"''") == s(r"""               "''"  """)
    assert findx.double_quoted(r'"') == s(r"""               "\""  """)
    assert findx.double_quoted('\\"') == s('                 "\\\\\\""  ')
    assert findx.double_quoted('\\"two\\"\\"words\\"') == s(
        r"""               "\\\"two\\\"\\\"words\\\"" """
    )
    assert findx.double_quoted(r"""\ \\ \\\.""") == s(
        r"""                 "\ \\ \\\." """
    )
    assert findx.double_quoted("\\") == s(r"""              "\\" """)
    assert findx.double_quoted("\\\\") == s(r"""              "\\\\" """)
    assert findx.double_quoted(r"\\.") == s(r"""               "\\." """)


def test_quoted() -> None:
    def s(s: str) -> str:
        return s.strip()

    assert findx.quoted(r"") == s(r"""        ''  """)
    assert findx.quoted(r"hello") == s(r"""        'hello'  """)
    assert findx.quoted(r"hello there") == s(r"""        'hello there'  """)
    assert findx.quoted(r'hello "Mike"') == s(r"""        'hello "Mike"'  """)
    assert findx.quoted(r"hello I'm Mike") == s(
        r"""        "hello I'm Mike"  """
    )
    assert findx.quoted(r"\Windows\system32") == s(
        r"""        '\Windows\system32'  """
    )
    assert findx.quoted(r"\Program Files") == s(
        r"""        '\Program Files'  """
    )


def test_quote_required() -> None:
    assert findx.quote_required(r"")
    assert not findx.quote_required(r"oneword")
    assert not findx.quote_required(r"?with*punc.,but!no:space")
    assert findx.quote_required(r"two words")
    assert findx.quote_required(r"\backslash")
    assert findx.quote_required(r'"')
    assert findx.quote_required(r"'")


def test_optionally_quoted() -> None:
    def s(s: str) -> str:
        return s.strip()

    assert findx.optionally_quoted(r"") == s(r"""                   ''  """)
    assert findx.optionally_quoted(r"hello") == s(
        r"""                    hello   """
    )
    assert findx.optionally_quoted(r"hello there") == s(
        r"""                   'hello there'  """
    )
    assert findx.optionally_quoted(r'hello "Mike"') == s(
        r"""                   'hello "Mike"'  """
    )
    assert findx.optionally_quoted(r"hello I'm Mike") == s(
        r"""                   "hello I'm Mike"  """
    )
    assert findx.optionally_quoted(r"\Windows\system32") == s(
        r"""                   '\Windows\system32'  """
    )
    assert findx.optionally_quoted(r"\Program Files") == s(
        r"""                   '\Program Files'  """
    )


def test_joined_lines_empty() -> None:
    lines = list(
        findx.joined_lines(
            make_lines(
                """
        """
            )
        )
    )
    assert lines == make_lines(
        """
        """
    )


def test_joined_lines_simple() -> None:
    lines = list(
        findx.joined_lines(
            make_lines(
                """
        line1
        line2
        """
            )
        )
    )
    assert lines == make_lines(
        """
        line1
        line2
        """
    )


def test_joined_lines_continuation() -> None:
    lines = list(
        findx.joined_lines(
            make_lines(
                """
        line1=
          more
         continuation
           lines
        line2=
          +even more

          not continued
        """
            )
        )
    )
    assert lines == make_lines(
        """
        line1= more continuation lines
        line2=even more

          not continued
        """
    )


def test_joined_lines_unexpected_indent() -> None:
    lines = list(
        findx.joined_lines(
            make_lines(
                """
        # Comment.

          Unexpected_indent
        """
            )
        )
    )
    assert lines == make_lines(
        """
        # Comment.

          Unexpected_indent
        """
    )


def test_optionally_quoted_join() -> None:
    def s(s: str) -> str:
        return s.strip()

    def o_q_join(args: T.List[str]) -> str:
        return findx.optionally_quoted_join(args)

    assert o_q_join([]) == s(r"""            """)
    assert o_q_join([r""]) == s(r"""     ''  """)
    assert o_q_join([r"hello"]) == s(r"""      hello  """)
    assert o_q_join([r"hello", r"there"]) == s(r"""      hello there  """)
    assert o_q_join([r"hello there", r"I'm Mike"]) == s(
        r"""     'hello there' "I'm Mike"  """
    )


def test_count_run() -> None:
    assert findx.count_run("", lambda c: c == "h") == 0
    assert findx.count_run("hhhhiiii", lambda c: c == "h") == 4


def test_split_token() -> None:
    assert findx.split_token("") == ("", "")
    assert findx.split_token("x") == ("x", "")
    assert findx.split_token("xy") == ("x", "y")
    assert findx.split_token(" ") == (" ", "")
    assert findx.split_token(" x") == (" ", "x")
    assert findx.split_token(" \t") == (" \t", "")
    assert findx.split_token(" \tx") == (" \t", "x")
    assert findx.split_token("\\") == ("\\", "")
    assert findx.split_token("\\\\x") == ("\\\\", "x")
    assert findx.split_token("\\\\\\x") == ("\\\\\\", "x")


def test_found_special_backslashes() -> None:
    # Not quote mode:
    assert not findx.found_special_backslashes("x", "", "")
    assert not findx.found_special_backslashes("\\", "", "")
    assert not findx.found_special_backslashes("\\", "x", "")
    assert findx.found_special_backslashes("\\", " ", "")
    assert findx.found_special_backslashes("\\", "'", "")
    assert findx.found_special_backslashes("\\", '"', "")

    # Single-quote mode:
    assert not findx.found_special_backslashes("x", "", "'")
    assert not findx.found_special_backslashes("\\", "", "'")
    assert not findx.found_special_backslashes("\\", "x", "'")
    assert not findx.found_special_backslashes("\\", " ", "'")
    assert not findx.found_special_backslashes("\\", "'", "'")
    assert not findx.found_special_backslashes("\\", '"', "'")

    # Double-quote mode:
    assert not findx.found_special_backslashes("x", "", '"')
    assert not findx.found_special_backslashes("\\", "", '"')
    assert not findx.found_special_backslashes("\\", "x", '"')
    assert not findx.found_special_backslashes("\\", " ", '"')
    assert not findx.found_special_backslashes("\\", "'", '"')
    assert findx.found_special_backslashes("\\", '"', '"')


def test_quoted_split() -> None:
    assert findx.quoted_split("one two") == ["one", "two"]


def test_quoted_split_plain_escapes() -> None:
    assert findx.quoted_split(r"one\ two") == ["one two"]
    assert findx.quoted_split(r"   one\ two   ") == ["one two"]
    assert findx.quoted_split("one\\ two\\") == ["one two\\"]


def test_quoted_split_single_quotes() -> None:
    assert findx.quoted_split("""'one two'""") == ["one two"]
    assert findx.quoted_split("""one'  'two""") == ["one  two"]
    assert findx.quoted_split("""one'  '""") == ["one  "]
    assert findx.quoted_split("""'  'two""") == ["  two"]
    with pytest.raises(ValueError):
        findx.quoted_split("hello' there")
    assert findx.quoted_split(r"""'\'""") == ["\\"]


def test_quoted_split_double_quotes() -> None:
    assert findx.quoted_split('"one two"') == ["one two"]
    assert findx.quoted_split("""one"  "two""") == ["one  two"]
    assert findx.quoted_split('one"  "') == ["one  "]
    assert findx.quoted_split(""""  "two""") == ["  two"]
    assert findx.quoted_split('"\\keep"') == ["\\keep"]
    assert findx.quoted_split(r""" "\" \\\" \\\\" """) == [r'" \" \\']
    assert findx.quoted_split(r""""\\\keep \\".""") == [r"\\\keep \."]
    assert findx.quoted_split('"\\""') == ['"']
    with pytest.raises(ValueError):
        findx.quoted_split('hello" there')


def test_has_meta() -> None:
    f = findx.Findx()
    assert f.has_meta("one*")
    assert not f.has_meta("/two/three")


def test_get_option_list() -> None:
    f = findx.Findx()
    f.args = ["-type", "f", "-print0", "-fprintf", "myfile", "%f"]
    option_list = f.get_option_list()
    assert option_list == ["-type", "f"]

    option_list = f.get_option_list()
    assert option_list == ["-print0"]

    option_list = f.get_option_list()
    assert option_list == ["-fprintf", "myfile", "%f"]
    assert f.args == []


def test_get_option_list_var() -> None:
    f = findx.Findx()
    f.args = ["-exec", "grep", "-i", ";", "word"]
    option_list = f.get_option_list()
    assert option_list == ["-exec", "grep", "-i", ";"]
    assert f.args == ["word"]


def test_get_option_list_underflow() -> None:
    f = findx.Findx()
    f.args = ["-printf"]
    with pytest.raises(findx.MissingArgumentError):
        f.get_option_list()


def test_no_dirs() -> None:
    f = findx.Findx()
    f.parse_command_line("".split())
    assert f.expression == "".split()
    assert f.roots == ".".split()


def test_one_dir() -> None:
    f = findx.Findx()
    f.parse_command_line("someDir".split())
    assert f.expression == "".split()
    assert f.roots == "someDir".split()


def test_root_dir() -> None:
    f = findx.Findx()
    f.parse_command_line("-root someRoot".split())
    assert f.expression == "".split()
    assert f.roots == "someRoot".split()


def test_late_path() -> None:
    f = findx.Findx()
    f.parse_command_line("-print somePath anotherPath".split())
    assert f.roots == "somePath anotherPath".split()
    assert f.expression == "( -print )".split()


def test_pre_post_path_options() -> None:
    f = findx.Findx()
    f.parse_command_line("-print somePath -L anotherPath -depth".split())
    assert f.pre_path_options == "-L".split()
    assert f.roots == "somePath anotherPath".split()
    assert f.post_path_options == "-depth".split()
    assert f.expression == "( -print )".split()


def test_simple_cmd() -> None:
    f = findx.Findx()
    f.parse_command_line("-type f -a -print0".split())
    assert f.expression == "( -type f -a -print0 )".split()


def test_glob_name() -> None:
    f = findx.Findx()
    f.parse_command_line("*.c".split())
    assert f.expression == "( -name *.c )".split()


def test_glob_path() -> None:
    f = findx.Findx()
    f.parse_command_line("*/*.c".split())
    assert f.expression == "( -path */*.c )".split()


def test_exclude() -> None:
    f = findx.Findx()
    f.parse_command_line("-e -type f -name *.exe".split())
    assert f.expression == "( -name *.exe )".split()
    assert f.excludes == "-type f".split()


def test_exclude2() -> None:
    f = findx.Findx()
    f.parse_command_line("-print -e ( -type f -name *.exe ) -print".split())
    assert f.expression == "( -print -print )".split()
    assert f.excludes == "( -type f -name *.exe )".split()


def test_distribute_option() -> None:
    f = findx.Findx()
    a = f.distribute_option("-type", ["f"])
    assert a == "-type f".split()
    a = f.distribute_option("-type", ["f", "d"])
    assert a == "( -type f -o -type d )".split()


def test_find_braced_range() -> None:
    f = findx.Findx()
    assert f.find_braced_range("hello") == (-1, -1)
    assert f.find_braced_range("{hello}") == (1, 6)
    assert f.find_braced_range("{hello}", 1) == (-1, -1)
    assert f.find_braced_range("{hel{mom}lo}", 1) == (5, 8)
    assert f.find_braced_range("[{]hel{mom}lo}") == (7, 10)


def test_find_multi() -> None:
    f = findx.Findx()
    assert f.find_multi("abcd", ["a"]) == (0, "a")
    assert f.find_multi("abcd", ["d", "c"]) == (2, "c")
    assert f.find_multi("abcd", ["b"]) == (1, "b")
    assert f.find_multi("abcd", ["z"]) == (-1, "")


def test_find_cut_points() -> None:
    f = findx.Findx()
    assert f.find_cut_points("a|b|c") == [1, 3]
    assert f.find_cut_points(",,a|b|c") == [0, 1, 3, 5]
    assert f.find_cut_points("hello") == []
    assert f.find_cut_points("one[,]two") == []
    assert f.find_cut_points("one{a,b}two") == []
    assert f.find_cut_points("one{a,b{two") == [5]


def test_split_glob_outside_braces() -> None:
    f = findx.Findx()
    assert f.split_glob_outside_braces("") == [""]
    assert f.split_glob_outside_braces("one") == ["one"]
    assert f.split_glob_outside_braces("one|two") == ["one", "two"]
    assert f.split_glob_outside_braces("on{e|t}wo") == ["on{e|t}wo"]


def test_split_glob() -> None:
    f = findx.Findx()
    assert f.split_glob("") == [""]
    assert f.split_glob("a") == ["a"]
    assert f.split_glob("a|b") == ["a", "b"]
    assert f.split_glob("a,b") == ["a", "b"]
    assert f.split_glob("*.c,?.[ch]") == ["*.c", "?.[ch]"]
    assert f.split_glob("a[,]b") == ["a[,]b"]
    assert f.split_glob("{a,b}") == ["a", "b"]
    assert f.split_glob("{a|b}") == ["a", "b"]
    assert f.split_glob("a{b,c}d") == ["abd", "acd"]
    assert f.split_glob("a{b|c}d") == ["abd", "acd"]
    assert f.split_glob("{a,b}{c,d}") == ["ac", "ad", "bc", "bd"]
    assert f.split_glob("a{b,c,d}e") == ["abe", "ace", "ade"]
    assert f.split_glob("a{b,c[}]d") == ["a{b", "c[}]d"]
    assert f.split_glob("a{b,c{d,e}f}g") == ["abg", "acdfg", "acefg"]
    assert f.split_glob("a{b{c|d}e}f") == ["a{bce}f", "a{bde}f"]


def test_text_settings() -> None:
    ts = findx.TextSettings("name")
    ts.set_text(
        make_text(
            """
        line1 = something
        line2 = something
            else
        """
        )
    )
    d = dict(ts.items())
    assert d == {"line1": "something", "line2": "something else"}


def test_text_settings_invalid() -> None:
    ts = findx.TextSettings("name")
    with pytest.raises(findx.InvalidConfigLineError):
        ts.set_text(
            make_text(
                """
            = something
            """
            )
        )
