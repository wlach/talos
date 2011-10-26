import os
from setuptools import setup, find_packages

try:
    here = os.path.dirname(os.path.abspath(__file__))
    description = file(os.path.join(here, 'README.txt')).read()
except IOError: 
    description = ''

version = "0.0"

dependencies = []

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
      

