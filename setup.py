#!/usr/bin/env python

# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

import sys
from setuptools import find_packages, setup
from pylsp import __version__


README = open('README.md', 'r').read()

install_requires = [
        'configparser; python_version<"3.0"',
        'future>=0.14.0; python_version<"3"',
        'backports.functools_lru_cache; python_version<"3.2"',
        'jedi>=0.17.2,<0.19.0',
        'python-jsonrpc-server>=0.4.0',
        'pluggy',
        'ujson<=2.0.3 ; platform_system!="Windows" and python_version<"3.0"',
        'ujson>=3.0.0 ; python_version>"3"']

setup(
    name='python-lsp-server',
    version=__version__,
    description='Python Language Server for the Language Server Protocol',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/python-ls/python-ls',
    author='Python Language Server Contributors',
    packages=find_packages(exclude=['contrib', 'docs', 'test', 'test.*']),
    install_requires=install_requires,
    extras_require={
        'all': [
            'autopep8',
            'flake8>=3.8.0',
            'mccabe>=0.6.0,<0.7.0',
            'pycodestyle>=2.6.0,<2.7.0',
            'pydocstyle>=2.0.0',
            'pyflakes>=2.2.0,<2.3.0',
            # pylint >= 2.5.0 is required for working through stdin and only
            # available with python3
            'pylint>=2.5.0' if sys.version_info.major >= 3 else 'pylint',
            'rope>=0.10.5',
            'yapf',
        ],
        'autopep8': ['autopep8'],
        'flake8': ['flake8>=3.8.0'],
        'mccabe': ['mccabe>=0.6.0,<0.7.0'],
        'pycodestyle': ['pycodestyle>=2.6.0,<2.7.0'],
        'pydocstyle': ['pydocstyle>=2.0.0'],
        'pyflakes': ['pyflakes>=2.2.0,<2.3.0'],
        'pylint': [
            'pylint>=2.5.0' if sys.version_info.major >= 3 else 'pylint'],
        'rope': ['rope>0.10.5'],
        'yapf': ['yapf'],
        'test': ['versioneer',
                 'pylint>=2.5.0' if sys.version_info.major >= 3 else 'pylint',
                 'pytest', 'mock', 'pytest-cov', 'coverage', 'numpy', 'pandas',
                 'matplotlib', 'pyqt5;python_version>="3"', 'flaky'],
    },
    entry_points={
        'console_scripts': [
            'pylsp = pylsp.__main__:main',
        ],
        'pylsp': [
            'autopep8 = pylsp.plugins.autopep8_format',
            'folding = pylsp.plugins.folding',
            'flake8 = pylsp.plugins.flake8_lint',
            'jedi_completion = pylsp.plugins.jedi_completion',
            'jedi_definition = pylsp.plugins.definition',
            'jedi_hover = pylsp.plugins.hover',
            'jedi_highlight = pylsp.plugins.highlight',
            'jedi_references = pylsp.plugins.references',
            'jedi_rename = pylsp.plugins.jedi_rename',
            'jedi_signature_help = pylsp.plugins.signature',
            'jedi_symbols = pylsp.plugins.symbols',
            'mccabe = pylsp.plugins.mccabe_lint',
            'preload = pylsp.plugins.preload_imports',
            'pycodestyle = pylsp.plugins.pycodestyle_lint',
            'pydocstyle = pylsp.plugins.pydocstyle_lint',
            'pyflakes = pylsp.plugins.pyflakes_lint',
            'pylint = pylsp.plugins.pylint_lint',
            'rope_completion = pylsp.plugins.rope_completion',
            'rope_rename = pylsp.plugins.rope_rename',
            'yapf = pylsp.plugins.yapf_format'
        ]
    },
)
