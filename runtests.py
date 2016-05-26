import sys


pyver_major = sys.version_info[0]
pyver_minor = sys.version_info[1]
pyver = (pyver_major, pyver_minor)
pyver_str = '%d.%d' % pyver

if pyver < (2, 6) or (pyver_major == 3 and pyver < (3, 3)):
    print('Python version %s too old' % pyver_str)
    sys.exit(2)

else:
    import subprocess
    if pyver < (2, 7):
        subprocess.call(['python', '-m', 'discover'])
    else:
        subprocess.call(['python', '-m', 'unittest', 'discover'])
