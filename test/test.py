#!/usr/bin/env python

import findx
from nose.tools import raises

@raises(IOError)
def testIOError():
    raise IOError

def testHasMeta():
    f = findx.Findx()
    assert f.hasMeta("one*")
    assert not f.hasMeta("/two/three")

def testGetOptionList():
    f = findx.Findx()
    f.args = ['-type', 'f', '-print0', '-fprintf', 'myfile', '%f']
    optionList = f.getOptionList()
    assert optionList == ['-type', 'f']

    optionList = f.getOptionList()
    assert optionList == ['-print0']

    optionList = f.getOptionList()
    assert optionList == ['-fprintf', 'myfile', '%f']
    assert f.args == []

def testGetOptionListVar():
    f = findx.Findx()
    f.args = ['-exec', 'grep', '-i', ';', 'word']
    optionList = f.getOptionList()
    assert optionList == ['-exec', 'grep', '-i', ';']
    assert f.args == ['word']

@raises(findx.MissingArgumentError)
def testGetOptionListUnderflow():
    f = findx.Findx()
    f.args = ['-printf']
    optionList = f.getOptionList()

def testSimpleCmd():
    f = findx.Findx()
    f.parseCommandLine("-type f -a -print0".split())
    assert f.expression == "-type f -a -print0".split()

def testGlob():
    f = findx.Findx()
    f.parseCommandLine("*.c".split())
    assert f.expression == "-name *.c".split()

def testExclude():
    f = findx.Findx()
    f.parseCommandLine("-e -type f -name *.exe".split())
    assert f.expression == "-name *.exe".split()
    assert f.excludes == "-type f".split()

def testExclude2():
    f = findx.Findx()
    f.parseCommandLine("-print -e ( -type f -name *.exe ) -print".split())
    assert f.expression == "-print -print".split()
    assert f.excludes == "( -type f -name *.exe )".split()

def testDistributeOption():
    f = findx.Findx()
    a = f.distributeOption("-type", ['f'])
    assert a == "-type f".split()
    a = f.distributeOption("-type", ['f', 'd'])
    assert a == "( -type f -o -type d )".split()

def testFindBracedRange():
    f = findx.Findx()
    assert f.findBracedRange("hello") == (-1, -1)
    assert f.findBracedRange("{hello}") == (1, 6)
    assert f.findBracedRange("{hello}", 1) == (-1, -1)
    assert f.findBracedRange("{hel{mom}lo}", 1) == (5, 8)
    assert f.findBracedRange("[{]hel{mom}lo}") == (7, 10)

def testFindMulti():
    f = findx.Findx()
    assert f.findMulti("abcd", ["a"]) == (0, "a")
    assert f.findMulti("abcd", ["d", "c"]) == (2, "c")
    assert f.findMulti("abcd", ["b"]) == (1, "b")
    assert f.findMulti("abcd", ["z"]) == (-1, "")

def testFindCutPoints():
    f = findx.Findx()
    assert f.findCutPoints("a|b|c") == [1, 3]
    assert f.findCutPoints(",,a|b|c") == [0, 1, 3, 5]
    assert f.findCutPoints("hello") == []
    assert f.findCutPoints("one[,]two") == []
    assert f.findCutPoints("one{a,b}two") == []
    assert f.findCutPoints("one{a,b{two") == [5]

def testSplitGlobOutsideBraces():
    f = findx.Findx()
    assert f.splitGlobOutsideBraces("") == [""]
    assert f.splitGlobOutsideBraces("one") == ["one"]
    assert f.splitGlobOutsideBraces("one|two") == ["one", "two"]
    assert f.splitGlobOutsideBraces("on{e|t}wo") == ["on{e|t}wo"]

def testSplitGlob():
    f = findx.Findx()
    assert f.splitGlob("") == [""]
    assert f.splitGlob("a") == ["a"]
    assert f.splitGlob("a|b") == ["a", "b"]
    assert f.splitGlob("a,b") == ["a", "b"]
    assert f.splitGlob("*.c,?.[ch]") == ["*.c", "?.[ch]"]
    assert f.splitGlob("a[,]b") == ["a[,]b"]
    assert f.splitGlob("{a,b}") == ["a", "b"]
    assert f.splitGlob("{a|b}") == ["a", "b"]
    assert f.splitGlob("a{b,c}d") == ["abd", "acd"]
    assert f.splitGlob("a{b|c}d") == ["abd", "acd"]
    assert f.splitGlob("{a,b}{c,d}") == ["ac", "ad", "bc", "bd"]
    assert f.splitGlob("a{b,c,d}e") == ["abe", "ace", "ade"]
    assert f.splitGlob("a{b,c[}]d") == ["a{b", "c[}]d"]
    assert f.splitGlob("a{b,c{d,e}f}g") == ["abg", "acdfg", "acefg"]
    assert f.splitGlob("a{b{c|d}e}f") == ["a{bce}f", "a{bde}f"]


