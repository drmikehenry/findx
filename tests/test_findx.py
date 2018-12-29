#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals

import unittest
import textwrap
import findx


def make_text(s):
    if s.startswith('\n'):
        s = s[1:]
    return textwrap.dedent(s)


def make_lines(s):
    return make_text(s).splitlines()


class TestFindx(unittest.TestCase):

    def test_single_quoted(self):
        def s(s):
            return s.strip()

        self.assertEqual(findx.single_quoted(r''),
                         s(r"""               ''  """))
        self.assertEqual(findx.single_quoted(r'hello'),
                         s(r"""               'hello'  """))
        self.assertEqual(findx.single_quoted(r'hello there'),
                         s(r"""               'hello there'  """))
        self.assertEqual(findx.single_quoted(r'hello "Mike"'),
                         s(r"""               'hello "Mike"'  """))
        self.assertEqual(findx.single_quoted(r"hello I'm Mike"),
                         s(r"""               'hello I'\''m Mike'  """))
        self.assertEqual(findx.single_quoted(r"\Windows\system32"),
                         s(r"""               '\Windows\system32'  """))
        self.assertEqual(findx.single_quoted(r"\Program Files"),
                         s(r"""               '\Program Files'  """))
        self.assertEqual(findx.single_quoted(r"'"),
                         s(r"""               \'  """))
        self.assertEqual(findx.single_quoted(r"''"),
                         s(r"""               \'\'  """))
        self.assertEqual(findx.single_quoted(r"'two''words'"),
                         s(r"""               \''two'\'\''words'\'  """))

    def test_double_quoted(self):
        def s(s):
            return s.strip()

        self.assertEqual(findx.double_quoted(r''),
                         s(r'''               ""  '''))
        self.assertEqual(findx.double_quoted(r'hello'),
                         s(r'''               "hello"  '''))
        self.assertEqual(findx.double_quoted(r'hello there'),
                         s(r'''               "hello there"  '''))
        self.assertEqual(findx.double_quoted(r'hello "Mike"'),
                         s(r'''               "hello \"Mike\""  '''))
        self.assertEqual(findx.double_quoted(r'''hello I'm Mike'''),
                         s(r'''                 "hello I'm Mike"  '''))
        self.assertEqual(findx.double_quoted(r'''\Windows\system32'''),
                         s(r'''                 "\Windows\system32"  '''))
        self.assertEqual(findx.double_quoted(r'''\Program Files'''),
                         s(r'''                 "\Program Files"  '''))
        self.assertEqual(findx.double_quoted(r"'"),
                         s(r'''               "'"  '''))
        self.assertEqual(findx.double_quoted(r"''"),
                         s(r'''               "''"  '''))
        self.assertEqual(findx.double_quoted(r'"'),
                         s(r'''               "\""  '''))
        self.assertEqual(findx.double_quoted(r'''\"'''),
                         s(r'''                 "\\\""  '''))
        self.assertEqual(findx.double_quoted(r'''\"two\"\"words\"'''),
                         s(r'''               "\\\"two\\\"\\\"words\\\"" '''))
        self.assertEqual(findx.double_quoted(r'''\ \\ \\\.'''),
                         s(r'''                 "\ \\ \\\." '''))
        self.assertEqual(findx.double_quoted('\\'),
                         s(r'''              "\\" '''))
        self.assertEqual(findx.double_quoted('\\\\'),
                         s(r'''              "\\\\" '''))
        self.assertEqual(findx.double_quoted(r'\\.'),
                         s(r'''               "\\." '''))

    def test_quoted(self):
        def s(s):
            return s.strip()

        self.assertEqual(findx.quoted(r''),
                         s(r"""        ''  """))
        self.assertEqual(findx.quoted(r'hello'),
                         s(r"""        'hello'  """))
        self.assertEqual(findx.quoted(r'hello there'),
                         s(r"""        'hello there'  """))
        self.assertEqual(findx.quoted(r'hello "Mike"'),
                         s(r"""        'hello "Mike"'  """))
        self.assertEqual(findx.quoted(r"hello I'm Mike"),
                         s(r"""        "hello I'm Mike"  """))
        self.assertEqual(findx.quoted(r"\Windows\system32"),
                         s(r"""        '\Windows\system32'  """))
        self.assertEqual(findx.quoted(r"\Program Files"),
                         s(r"""        '\Program Files'  """))

    def test_quote_required(self):
        self.assertTrue(findx.quote_required(r''))
        self.assertFalse(findx.quote_required(r'oneword'))
        self.assertFalse(findx.quote_required(r'?with*punc.,but!no:space'))
        self.assertTrue(findx.quote_required(r'two words'))
        self.assertTrue(findx.quote_required(r'\backslash'))
        self.assertTrue(findx.quote_required(r'"'))
        self.assertTrue(findx.quote_required(r"'"))

    def test_optionally_quoted(self):
        def s(s):
            return s.strip()

        self.assertEqual(findx.optionally_quoted(r''),
                         s(r"""                   ''  """))
        self.assertEqual(findx.optionally_quoted(r'hello'),
                         s(r"""                    hello   """))
        self.assertEqual(findx.optionally_quoted(r'hello there'),
                         s(r"""                   'hello there'  """))
        self.assertEqual(findx.optionally_quoted(r'hello "Mike"'),
                         s(r"""                   'hello "Mike"'  """))
        self.assertEqual(findx.optionally_quoted(r"hello I'm Mike"),
                         s(r"""                   "hello I'm Mike"  """))
        self.assertEqual(findx.optionally_quoted(r"\Windows\system32"),
                         s(r"""                   '\Windows\system32'  """))
        self.assertEqual(findx.optionally_quoted(r"\Program Files"),
                         s(r"""                   '\Program Files'  """))

    def test_joined_lines_empty(self):
        lines = list(findx.joined_lines(make_lines(
            """
            """)))
        self.assertEqual(lines, make_lines(
            """
            """))

    def test_joined_lines_simple(self):
        lines = list(findx.joined_lines(make_lines(
            """
            line1
            line2
            """)))
        self.assertEqual(lines, make_lines(
            """
            line1
            line2
            """))

    def test_joined_lines_continuation(self):
        lines = list(findx.joined_lines(make_lines(
            """
            line1=
              more
             continuation
               lines
            line2=
              +even more

              not continued
            """)))
        self.assertEqual(lines, make_lines(
            """
            line1= more continuation lines
            line2=even more

              not continued
            """))

    def test_joined_lines_unexpected_indent(self):
        lines = list(findx.joined_lines(make_lines(
            """
            # Comment.

              Unexpected_indent
            """)))
        self.assertEqual(lines, make_lines(
            """
            # Comment.

              Unexpected_indent
            """))

    def test_optionally_quoted_join(self):
        def s(s):
            return s.strip()

        def o_q_join(args):
            return findx.optionally_quoted_join(args)

        self.assertEqual(o_q_join([]),
                         s(r"""            """))
        self.assertEqual(o_q_join([r'']),
                         s(r"""     ''  """))
        self.assertEqual(o_q_join([r'hello']),
                         s(r"""      hello  """))
        self.assertEqual(o_q_join([r'hello', r'there']),
                         s(r"""      hello there  """))
        self.assertEqual(o_q_join([r'hello there', r"I'm Mike"]),
                         s(r"""     'hello there' "I'm Mike"  """))

    def test_quoted_split(self):
        self.assertEqual(findx.quoted_split('one two'),
                         ['one', 'two'])

    def test_quoted_split_plain_escapes(self):
        self.assertEqual(findx.quoted_split(r'one\ two'),
                         ['one two'])
        self.assertEqual(findx.quoted_split(r'   one\ two   '),
                         ['one two'])
        self.assertEqual(findx.quoted_split('one\\ two\\'),
                         ['one two\\'])

    def test_quoted_split_single_quotes(self):
        self.assertEqual(findx.quoted_split("""'one two'"""),
                         ['one two'])
        self.assertEqual(findx.quoted_split("""one'  'two"""),
                         ['one  two'])
        self.assertEqual(findx.quoted_split("""one'  '"""),
                         ['one  '])
        self.assertEqual(findx.quoted_split("""'  'two"""),
                         ['  two'])
        self.assertRaises(ValueError, findx.quoted_split, "hello' there")
        self.assertEqual(findx.quoted_split(r"""'\'"""),
                         ['\\'])

    def test_quoted_split_double_quotes(self):
        self.assertEqual(findx.quoted_split('''"one two"'''),
                         ['one two'])
        self.assertEqual(findx.quoted_split('''one"  "two'''),
                         ['one  two'])
        self.assertEqual(findx.quoted_split('''one"  "'''),
                         ['one  '])
        self.assertEqual(findx.quoted_split('''"  "two'''),
                         ['  two'])
        self.assertEqual(findx.quoted_split(r'''"\keep"'''),
                         [r'\keep'])
        self.assertEqual(findx.quoted_split(r''' "\" \\\" \\\\" '''),
                         [r'" \" \\'])
        self.assertEqual(findx.quoted_split(r'''"\\\keep \\".'''),
                         [r'\\\keep \.'])
        self.assertEqual(findx.quoted_split(r'''"\""'''),
                         [r'"'])
        self.assertRaises(ValueError, findx.quoted_split, 'hello" there')

    def test_has_meta(self):
        f = findx.Findx()
        self.assertTrue(f.has_meta('one*'))
        self.assertFalse(f.has_meta('/two/three'))

    def test_get_option_list(self):
        f = findx.Findx()
        f.args = ['-type', 'f', '-print0', '-fprintf', 'myfile', '%f']
        option_list = f.get_option_list()
        self.assertEqual(option_list, ['-type', 'f'])

        option_list = f.get_option_list()
        self.assertEqual(option_list, ['-print0'])

        option_list = f.get_option_list()
        self.assertEqual(option_list, ['-fprintf', 'myfile', '%f'])
        self.assertEqual(f.args, [])

    def test_get_option_list_var(self):
        f = findx.Findx()
        f.args = ['-exec', 'grep', '-i', ';', 'word']
        option_list = f.get_option_list()
        self.assertEqual(option_list, ['-exec', 'grep', '-i', ';'])
        self.assertEqual(f.args, ['word'])

    def test_get_option_list_underflow(self):
        f = findx.Findx()
        f.args = ['-printf']
        self.assertRaises(findx.MissingArgumentError, f.get_option_list)

    def test_no_dirs(self):
        f = findx.Findx()
        f.parse_command_line(''.split())
        self.assertEqual(f.expression, ''.split())
        self.assertEqual(f.roots, '.'.split())

    def test_one_dir(self):
        f = findx.Findx()
        f.parse_command_line('someDir'.split())
        self.assertEqual(f.expression, ''.split())
        self.assertEqual(f.roots, 'someDir'.split())

    def test_root_dir(self):
        f = findx.Findx()
        f.parse_command_line('-root someRoot'.split())
        self.assertEqual(f.expression, ''.split())
        self.assertEqual(f.roots, 'someRoot'.split())

    def test_late_path(self):
        f = findx.Findx()
        f.parse_command_line('-print somePath anotherPath'.split())
        self.assertEqual(f.roots, 'somePath anotherPath'.split())
        self.assertEqual(f.expression, '( -print )'.split())

    def test_pre_post_path_options(self):
        f = findx.Findx()
        f.parse_command_line('-print somePath -L anotherPath -depth'.split())
        self.assertEqual(f.pre_path_options, '-L'.split())
        self.assertEqual(f.roots, 'somePath anotherPath'.split())
        self.assertEqual(f.post_path_options, '-depth'.split())
        self.assertEqual(f.expression, '( -print )'.split())

    def test_simple_cmd(self):
        f = findx.Findx()
        f.parse_command_line('-type f -a -print0'.split())
        self.assertEqual(f.expression, '( -type f -a -print0 )'.split())

    def test_glob_name(self):
        f = findx.Findx()
        f.parse_command_line('*.c'.split())
        self.assertEqual(f.expression, '( -name *.c )'.split())

    def test_glob_path(self):
        f = findx.Findx()
        f.parse_command_line('*/*.c'.split())
        self.assertEqual(f.expression, '( -path */*.c )'.split())

    def test_exclude(self):
        f = findx.Findx()
        f.parse_command_line('-e -type f -name *.exe'.split())
        self.assertEqual(f.expression, '( -name *.exe )'.split())
        self.assertEqual(f.excludes, '-type f'.split())

    def test_exclude2(self):
        f = findx.Findx()
        f.parse_command_line(
            '-print -e ( -type f -name *.exe ) -print'.split())
        self.assertEqual(f.expression, '( -print -print )'.split())
        self.assertEqual(f.excludes, '( -type f -name *.exe )'.split())

    def test_distribute_option(self):
        f = findx.Findx()
        a = f.distribute_option('-type', ['f'])
        self.assertEqual(a, '-type f'.split())
        a = f.distribute_option('-type', ['f', 'd'])
        self.assertEqual(a, '( -type f -o -type d )'.split())

    def test_find_braced_range(self):
        f = findx.Findx()
        self.assertEqual(f.find_braced_range('hello'), (-1, -1))
        self.assertEqual(f.find_braced_range('{hello}'), (1, 6))
        self.assertEqual(f.find_braced_range('{hello}', 1), (-1, -1))
        self.assertEqual(f.find_braced_range('{hel{mom}lo}', 1), (5, 8))
        self.assertEqual(f.find_braced_range('[{]hel{mom}lo}'), (7, 10))

    def test_find_multi(self):
        f = findx.Findx()
        self.assertEqual(f.find_multi('abcd', ['a']), (0, 'a'))
        self.assertEqual(f.find_multi('abcd', ['d', 'c']), (2, 'c'))
        self.assertEqual(f.find_multi('abcd', ['b']), (1, 'b'))
        self.assertEqual(f.find_multi('abcd', ['z']), (-1, ''))

    def test_find_cut_points(self):
        f = findx.Findx()
        self.assertEqual(f.find_cut_points('a|b|c'), [1, 3])
        self.assertEqual(f.find_cut_points(',,a|b|c'), [0, 1, 3, 5])
        self.assertEqual(f.find_cut_points('hello'), [])
        self.assertEqual(f.find_cut_points('one[,]two'), [])
        self.assertEqual(f.find_cut_points('one{a,b}two'), [])
        self.assertEqual(f.find_cut_points('one{a,b{two'), [5])

    def test_split_glob_outside_braces(self):
        f = findx.Findx()
        self.assertEqual(f.split_glob_outside_braces(''), [''])
        self.assertEqual(f.split_glob_outside_braces('one'), ['one'])
        self.assertEqual(f.split_glob_outside_braces('one|two'),
                         ['one', 'two'])
        self.assertEqual(f.split_glob_outside_braces('on{e|t}wo'),
                         ['on{e|t}wo'])

    def test_split_glob(self):
        f = findx.Findx()
        self.assertEqual(f.split_glob(''), [''])
        self.assertEqual(f.split_glob('a'), ['a'])
        self.assertEqual(f.split_glob('a|b'), ['a', 'b'])
        self.assertEqual(f.split_glob('a,b'), ['a', 'b'])
        self.assertEqual(f.split_glob('*.c,?.[ch]'), ['*.c', '?.[ch]'])
        self.assertEqual(f.split_glob('a[,]b'), ['a[,]b'])
        self.assertEqual(f.split_glob('{a,b}'), ['a', 'b'])
        self.assertEqual(f.split_glob('{a|b}'), ['a', 'b'])
        self.assertEqual(f.split_glob('a{b,c}d'), ['abd', 'acd'])
        self.assertEqual(f.split_glob('a{b|c}d'), ['abd', 'acd'])
        self.assertEqual(f.split_glob('{a,b}{c,d}'), ['ac', 'ad', 'bc', 'bd'])
        self.assertEqual(f.split_glob('a{b,c,d}e'), ['abe', 'ace', 'ade'])
        self.assertEqual(f.split_glob('a{b,c[}]d'), ['a{b', 'c[}]d'])
        self.assertEqual(f.split_glob('a{b,c{d,e}f}g'),
                         ['abg', 'acdfg', 'acefg'])
        self.assertEqual(f.split_glob('a{b{c|d}e}f'), ['a{bce}f', 'a{bde}f'])

    def test_text_settings(self):
        ts = findx.TextSettings('name')
        ts.set_text(make_text(
            """
            line1 = something
            line2 = something
                else
            """))
        d = dict(ts.items())
        self.assertEqual(d, {
            'line1': 'something',
            'line2': 'something else',
        })

    def test_text_settings_invalid(self):
        ts = findx.TextSettings('name')
        self.assertRaises(
            findx.InvalidConfigLineError,
            ts.set_text,
            make_text(
                """
                = something
                """))
