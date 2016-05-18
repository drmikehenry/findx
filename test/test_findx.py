#!/usr/bin/env python2

import unittest
import findx


class TestFindx(unittest.TestCase):

    def testIOError(self):
        with self.assertRaises(IOError):
            raise IOError()

    def testHasMeta(self):
        f = findx.Findx()
        self.assertTrue(f.hasMeta('one*'))
        self.assertFalse(f.hasMeta('/two/three'))

    def testGetOptionList(self):
        f = findx.Findx()
        f.args = ['-type', 'f', '-print0', '-fprintf', 'myfile', '%f']
        optionList = f.getOptionList()
        self.assertEqual(optionList, ['-type', 'f'])

        optionList = f.getOptionList()
        self.assertEqual(optionList, ['-print0'])

        optionList = f.getOptionList()
        self.assertEqual(optionList, ['-fprintf', 'myfile', '%f'])
        self.assertEqual(f.args, [])

    def testGetOptionListVar(self):
        f = findx.Findx()
        f.args = ['-exec', 'grep', '-i', ';', 'word']
        optionList = f.getOptionList()
        self.assertEqual(optionList, ['-exec', 'grep', '-i', ';'])
        self.assertEqual(f.args, ['word'])

    def testGetOptionListUnderflow(self):
        f = findx.Findx()
        f.args = ['-printf']
        with self.assertRaises(findx.MissingArgumentError):
            f.getOptionList()

    def testNoDirs(self):
        f = findx.Findx()
        f.parseCommandLine(''.split())
        self.assertEqual(f.expression, ''.split())
        self.assertEqual(f.dirs, '.'.split())

    def testOneDir(self):
        f = findx.Findx()
        f.parseCommandLine('someDir'.split())
        self.assertEqual(f.expression, ''.split())
        self.assertEqual(f.dirs, 'someDir'.split())

    def testRootDir(self):
        f = findx.Findx()
        f.parseCommandLine('-root someRoot'.split())
        self.assertEqual(f.expression, ''.split())
        self.assertEqual(f.dirs, 'someRoot'.split())

    def testLatePath(self):
        f = findx.Findx()
        f.parseCommandLine('-print somePath anotherPath'.split())
        self.assertEqual(f.dirs, 'somePath anotherPath'.split())
        self.assertEqual(f.expression, '( -print )'.split())

    def testPrePostPathOptions(self):
        f = findx.Findx()
        f.parseCommandLine('-print somePath -L anotherPath -depth'.split())
        self.assertEqual(f.prePathOptions, '-L'.split())
        self.assertEqual(f.dirs, 'somePath anotherPath'.split())
        self.assertEqual(f.postPathOptions, '-depth'.split())
        self.assertEqual(f.expression, '( -print )'.split())

    def testSimpleCmd(self):
        f = findx.Findx()
        f.parseCommandLine('-type f -a -print0'.split())
        self.assertEqual(f.expression, '( -type f -a -print0 )'.split())

    def testGlob(self):
        f = findx.Findx()
        f.parseCommandLine('*.c'.split())
        self.assertEqual(f.expression, '( -name *.c )'.split())

    def testExclude(self):
        f = findx.Findx()
        f.parseCommandLine('-e -type f -name *.exe'.split())
        self.assertEqual(f.expression, '( -name *.exe )'.split())
        self.assertEqual(f.excludes, '-type f'.split())

    def testExclude2(self):
        f = findx.Findx()
        f.parseCommandLine('-print -e ( -type f -name *.exe ) -print'.split())
        self.assertEqual(f.expression, '( -print -print )'.split())
        self.assertEqual(f.excludes, '( -type f -name *.exe )'.split())

    def testDistributeOption(self):
        f = findx.Findx()
        a = f.distributeOption('-type', ['f'])
        self.assertEqual(a, '-type f'.split())
        a = f.distributeOption('-type', ['f', 'd'])
        self.assertEqual(a, '( -type f -o -type d )'.split())

    def testFindBracedRange(self):
        f = findx.Findx()
        self.assertEqual(f.findBracedRange('hello'), (-1, -1))
        self.assertEqual(f.findBracedRange('{hello}'), (1, 6))
        self.assertEqual(f.findBracedRange('{hello}', 1), (-1, -1))
        self.assertEqual(f.findBracedRange('{hel{mom}lo}', 1), (5, 8))
        self.assertEqual(f.findBracedRange('[{]hel{mom}lo}'), (7, 10))

    def testFindMulti(self):
        f = findx.Findx()
        self.assertEqual(f.findMulti('abcd', ['a']), (0, 'a'))
        self.assertEqual(f.findMulti('abcd', ['d', 'c']), (2, 'c'))
        self.assertEqual(f.findMulti('abcd', ['b']), (1, 'b'))
        self.assertEqual(f.findMulti('abcd', ['z']), (-1, ''))

    def testFindCutPoints(self):
        f = findx.Findx()
        self.assertEqual(f.findCutPoints('a|b|c'), [1, 3])
        self.assertEqual(f.findCutPoints(',,a|b|c'), [0, 1, 3, 5])
        self.assertEqual(f.findCutPoints('hello'), [])
        self.assertEqual(f.findCutPoints('one[,]two'), [])
        self.assertEqual(f.findCutPoints('one{a,b}two'), [])
        self.assertEqual(f.findCutPoints('one{a,b{two'), [5])

    def testSplitGlobOutsideBraces(self):
        f = findx.Findx()
        self.assertEqual(f.splitGlobOutsideBraces(''), [''])
        self.assertEqual(f.splitGlobOutsideBraces('one'), ['one'])
        self.assertEqual(f.splitGlobOutsideBraces('one|two'), ['one', 'two'])
        self.assertEqual(f.splitGlobOutsideBraces('on{e|t}wo'), ['on{e|t}wo'])

    def testSplitGlob(self):
        f = findx.Findx()
        self.assertEqual(f.splitGlob(''), [''])
        self.assertEqual(f.splitGlob('a'), ['a'])
        self.assertEqual(f.splitGlob('a|b'), ['a', 'b'])
        self.assertEqual(f.splitGlob('a,b'), ['a', 'b'])
        self.assertEqual(f.splitGlob('*.c,?.[ch]'), ['*.c', '?.[ch]'])
        self.assertEqual(f.splitGlob('a[,]b'), ['a[,]b'])
        self.assertEqual(f.splitGlob('{a,b}'), ['a', 'b'])
        self.assertEqual(f.splitGlob('{a|b}'), ['a', 'b'])
        self.assertEqual(f.splitGlob('a{b,c}d'), ['abd', 'acd'])
        self.assertEqual(f.splitGlob('a{b|c}d'), ['abd', 'acd'])
        self.assertEqual(f.splitGlob('{a,b}{c,d}'), ['ac', 'ad', 'bc', 'bd'])
        self.assertEqual(f.splitGlob('a{b,c,d}e'), ['abe', 'ace', 'ade'])
        self.assertEqual(f.splitGlob('a{b,c[}]d'), ['a{b', 'c[}]d'])
        self.assertEqual(f.splitGlob('a{b,c{d,e}f}g'),
                         ['abg', 'acdfg', 'acefg'])
        self.assertEqual(f.splitGlob('a{b{c|d}e}f'), ['a{bce}f', 'a{bde}f'])
