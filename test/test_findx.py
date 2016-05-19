#!/usr/bin/env python

import unittest
import findx


class TestFindx(unittest.TestCase):

    def test_io_error(self):
        with self.assertRaises(IOError):
            raise IOError()

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
        with self.assertRaises(findx.MissingArgumentError):
            f.get_option_list()

    def test_no_dirs(self):
        f = findx.Findx()
        f.parse_command_line(''.split())
        self.assertEqual(f.expression, ''.split())
        self.assertEqual(f.dirs, '.'.split())

    def test_one_dir(self):
        f = findx.Findx()
        f.parse_command_line('someDir'.split())
        self.assertEqual(f.expression, ''.split())
        self.assertEqual(f.dirs, 'someDir'.split())

    def test_root_dir(self):
        f = findx.Findx()
        f.parse_command_line('-root someRoot'.split())
        self.assertEqual(f.expression, ''.split())
        self.assertEqual(f.dirs, 'someRoot'.split())

    def test_late_path(self):
        f = findx.Findx()
        f.parse_command_line('-print somePath anotherPath'.split())
        self.assertEqual(f.dirs, 'somePath anotherPath'.split())
        self.assertEqual(f.expression, '( -print )'.split())

    def test_pre_post_path_options(self):
        f = findx.Findx()
        f.parse_command_line('-print somePath -L anotherPath -depth'.split())
        self.assertEqual(f.pre_path_options, '-L'.split())
        self.assertEqual(f.dirs, 'somePath anotherPath'.split())
        self.assertEqual(f.post_path_options, '-depth'.split())
        self.assertEqual(f.expression, '( -print )'.split())

    def test_simple_cmd(self):
        f = findx.Findx()
        f.parse_command_line('-type f -a -print0'.split())
        self.assertEqual(f.expression, '( -type f -a -print0 )'.split())

    def test_glob(self):
        f = findx.Findx()
        f.parse_command_line('*.c'.split())
        self.assertEqual(f.expression, '( -name *.c )'.split())

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
