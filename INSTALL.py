#!/usr/bin/env python

"""
installation script for talos
"""

import os
import re
import shutil
import string
import subprocess
import sys
import urllib2
import zipfile
from StringIO import StringIO
try:
    from subprocess import check_call as call
except:
    from subprocess import call

REPO='http://hg.mozilla.org/build/talos'
ZIPFILE='http://hg.mozilla.org/build/talos/archive/tip.zip'
DEST='talos'
VIRTUALENV='https://raw.github.com/pypa/virtualenv/develop/virtualenv.py'

def which(binary, path=os.environ['PATH']):
    dirs = path.split(os.pathsep)
    for dir in dirs:
        if os.path.isfile(os.path.join(dir, path)):
            return os.path.join(dir, path)
        if os.path.isfile(os.path.join(dir, path + ".exe")):
            return os.path.join(dir, path + ".exe")

def main(args=sys.argv[1:]):

    # wipe vestiges
    if os.path.exists(DEST):
       shutil.rmtree(DEST) 

    # create a virtualenv
    virtualenv = which('virtualenv') or which('virtualenv.py')
    if virtualenv:
        call([virtualenv, DEST])
    else:
        process = subprocess.Popen([sys.executable, '-', DEST], stdin=subprocess.PIPE)
        stdout, stderr = process.communicate(input=urllib2.urlopen(VIRTUALENV).read())

    # create a src directory
    src = os.path.join(DEST, 'src')
    os.mkdir(src)

    # get talos
    hg = which('hg')
    if hg:
        call([hg, 'clone', REPO], cwd=src)
        talosdir = os.path.join(src, 'talos')
    else:
        buffer = StringIO()
        buffer.write(urllib2.urlopen(ZIPFILE).read())
        zip = zipfile.ZipFile(buffer)
        zip.extractall(path=src)
        # the archive directory gets labeled as e.g. talos-214df9ee2ea7
        # we need to figure out the prefix
        member = zip.namelist()[0]
        regex = re.compile(r'(talos-[' + string.hexdigits + r']+).*')
        match = regex.match(member)
        assert match
        talosdir = os.path.join(src, match.groups()[0])

    # find the correct python
    for i in ('bin', 'Scripts'):
        bindir = os.path.join(DEST, i)
        if os.path.exists(bindir):
            break
    else:
        raise AssertionError('virtualenv binary directory not found')
    for i in ('python', 'python.exe'):
        virtualenv_python = os.path.join(bindir, i)
        if os.path.exists(virtualenv_python):
            break
    else:
        raise AssertionError('virtualenv python not found')

    # install talos into the virtualenv
    call([os.path.abspath(virtualenv_python), 'setup.py', 'develop'], cwd=talosdir)

if __name__ == '__main__':
    main()
