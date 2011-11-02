import os
import sys
from setuptools import setup, find_packages

try:
    here = os.path.dirname(os.path.abspath(__file__))
    description = file(os.path.join(here, 'README.txt')).read()
except IOError: 
    description = ''

version = "0.0"

dependencies = ['pyyaml']

setup(name='talos',
      version=version,
      description="A python performance testing framework that is usable on Windows, Mac and Linux.",
      long_description=description,
      classifiers=[], # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      author='Mozilla Foundation',
      author_email='tools@lists.mozilla.org',
      url='https://wiki.mozilla.org/Buildbot/Talos',
      license='MPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      package_data = {'': ['*.config',
                           '*.css',
                           '*.gif',
                           '*.htm',
                           '*.html',
                           '*.ico',
                           '*.js',
                           '*.json',
                           '*.manifest',
                           '*.php',
                           '*.png',
                           '*.rdf',
                           '*.sqlite',
                           '*.svg',
                           '*.xml',
                           '*.xul', 
                           ]},
      zip_safe=False,
      install_requires=dependencies,
      entry_points="""
      # -*- Entry points: -*-
      """,
      )

def install_pageloader():
    """
    Obtain pageloader.  The steps by hand are
    hg clone http://hg.mozilla.org/build/pageloader
    cd pageloader
    zip -r pageloader.xpi *
    mv pageloader.xpi talos/page_load_test/pageloader.xpi
    """

    # find the destination
    import talos
    dirname = os.path.dirname(talos.__file__)
    dirname = os.path.join(dirname, 'page_load_test')
    assert os.path.isdir(dirname)

    # download the extension
    import urllib2
    url = 'http://hg.mozilla.org/build/pageloader/archive/tip.zip'
    dest = os.path.join(dirname, 'pageloader.xpi')
    f = file(dest, 'w')
    pageloader = urllib2.urlopen(url)
    f.write(pageloader.read())
    pageloader.close()
    f.close()

if 'install' in sys.argv[1:] or 'develop' in sys.argv[1:]:
    install_pageloader()
