from setuptools import setup

import sys
from setuptools.command.test import test as TestCommand

class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


def readme():
    with open('README.md') as f:
        return f.read()

setup( name             = 'pyop'
     , version          = '0.1.1'
     , description      = 'Matrix free linear transformations'
     , long_description = readme()
     , keywords         = [ 'Linear Algebra', 'Linear Transformations']
     , author           = 'Ryan Orendorff and Daniel Hensley'
     , author_email     = 'ryan@orendorff.io'
     , license          = 'BSD'
     , classifiers      =
        [ 'Development Status :: 1 - Planning'
        , 'Intended Audience :: Science/Research'
        , 'License :: OSI Approved :: BSD License'
        , 'Programming Language :: Python'
        , 'Topic :: Scientific/Engineering :: Mathematics'
        , 'Topic :: Software Development :: Libraries :: Python Modules'
        ]
     , packages         = ['pyop', 'pyop.operators']
     , install_requires =
        [ 'six >= 1.6'
        , 'numpy >= 1.8'
        , 'scipy >= 0.14.0'
        ]
     , zip_safe         = True
     , tests_require    = ['pytest']
     , cmdclass         = {'test': PyTest}
     )

