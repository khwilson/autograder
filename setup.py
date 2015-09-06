#!/usr/bin/env python
import glob
from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand
import sys
import warnings


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name="autograder",
    version='1.0.dev0',
    url="https://github.com/khwilson/autograder",
    author="Kevin Wilson",
    author_email="khwison@gmail.com",
    license="Apache",
    packages=find_packages(),
    cmdclass={"test": PyTest},
    install_requires=open('requirements.txt', 'r').readlines(),
    tests_require=open('requirements.testing.txt', 'r').readlines(),
    description="A simple autograder library",
    entry_points="""
    [console_scripts]
    autograder=autograder.cli:cli
    """,
    long_description="\n" + open('README', 'r').read()
)
