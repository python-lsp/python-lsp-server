# Python Language Server

[![image](https://github.com/python-ls/python-ls/workflows/Linux%20tests/badge.svg)](https://github.com/python-ls/python-ls/actions?query=workflow%3A%22Linux+tests%22) [![image](https://github.com/python-ls/python-ls/workflows/Mac%20tests/badge.svg)](https://github.com/python-ls/python-ls/actions?query=workflow%3A%22Mac+tests%22) [![image](https://github.com/python-ls/python-ls/workflows/Windows%20tests/badge.svg)](https://github.com/python-ls/python-ls/actions?query=workflow%3A%22Windows+tests%22) [![image](https://img.shields.io/github/license/python-ls/python-ls.svg)](https://github.com/python-ls/python-ls/blob/master/LICENSE)

A Python 2.7 and 3.5+ implementation of the [Language Server Protocol](https://github.com/Microsoft/language-server-protocol).

## Installation

The base language server requires [Jedi](https://github.com/davidhalter/jedi) to provide Completions, Definitions, Hover, References, Signature Help, and Symbols:

```
pip install python-language-server
```

If the respective dependencies are found, the following optional providers will be enabled:
- [Rope](https://github.com/python-rope/rope) for Completions and renaming
- [Pyflakes](https://github.com/PyCQA/pyflakes) linter to detect various errors
- [McCabe](https://github.com/PyCQA/mccabe) linter for complexity checking
- [pycodestyle](https://github.com/PyCQA/pycodestyle) linter for style checking
- [pydocstyle](https://github.com/PyCQA/pydocstyle) linter for docstring style checking (disabled by default)
- [autopep8](https://github.com/hhatto/autopep8) for code formatting
- [YAPF](https://github.com/google/yapf) for code formatting (preferred over autopep8)

Optional providers can be installed using the `extras` syntax. To install [YAPF](https://github.com/google/yapf) formatting for example:

```
pip install 'python-language-server[yapf]'
```

All optional providers can be installed using:

```
pip install 'python-language-server[all]'
```

If you get an error similar to `'install_requires' must be a string or list of strings` then please upgrade setuptools before trying again.

```
pip install -U setuptools
```

### 3rd Party Plugins

Installing these plugins will add extra functionality to the language server:

- [pyls-mypy](https://github.com/tomv564/pyls-mypy) Mypy type checking for Python 3
- [pyls-isort](https://github.com/paradoxxxzero/pyls-isort) Isort import sort code formatting
- [pyls-black](https://github.com/rupert/pyls-black) for code formatting using [Black](https://github.com/ambv/black)
- [pyls-memestra](https://github.com/QuantStack/pyls-memestra) for detecting the use of deprecated APIs

Please see the above repositories for examples on how to write plugins for the Python Language Server. Please file an issue if you require assistance writing a plugin.

## Configuration

Configuration is loaded from zero or more configuration sources.  Currently implemented are:

- pycodestyle: discovered in `~/.config/pycodestyle`, `setup.cfg`, `tox.ini` and `pycodestyle.cfg`.
- flake8: discovered in `~/.config/flake8`, `setup.cfg`, `tox.ini` and `flake8.cfg`

The default configuration source is pycodestyle. Change the `pylsp.configurationSources` setting to `['flake8']` in order to respect flake8 configuration instead.

Overall configuration is computed first from user configuration (in home directory), overridden by configuration passed in by the language client, and then overriden by configuration discovered in the workspace.

To enable pydocstyle for linting docstrings add the following setting in your LSP configuration:
`\` "pylsp.plugins.pydocstyle.enabled": true \``

See [vscode-client/package.json](vscode-client/package.json) for the full set of supported configuration options.

## Language Server Features

Auto Completion:

![image](https://raw.githubusercontent.com/python-ls/python-ls/develop/resources/auto-complete.gif)

Code Linting with pycodestyle and pyflakes:

![image](https://raw.githubusercontent.com/python-ls/python-ls/develop/resources/linting.gif)

Signature Help:

![image](https://raw.githubusercontent.com/python-ls/python-ls/develop/resources/signature-help.gif)

Go to definition:

![image](https://raw.githubusercontent.com/python-ls/python-ls/develop/resources/goto-definition.gif)

Hover:

![image](https://raw.githubusercontent.com/python-ls/python-ls/develop/resources/hover.gif)

Find References:

![image](https://raw.githubusercontent.com/python-ls/python-ls/develop/resources/references.gif)

Document Symbols:

![image](https://raw.githubusercontent.com/python-ls/python-ls/develop/resources/document-symbols.gif)

Document Formatting:

![image](https://raw.githubusercontent.com/python-ls/python-ls/develop/resources/document-format.gif)

## Development

To run the test suite:

```
pip install .[test] && pytest
```

# Develop against VS Code

The Python language server can be developed against a local instance of
Visual Studio Code.

Install [VSCode](https://code.visualstudio.com/download)

```bash
# Setup a virtual env
virtualenv env
. env/bin/activate

# Install pylsp
pip install .

# Install the vscode-client extension
cd vscode-client
yarn install

# Run VSCode which is configured to use pylsp
# See the bottom of vscode-client/src/extension.ts for info
yarn run vscode -- $PWD/../
```

Then to debug, click View -> Output and in the dropdown will be pylsp.
To refresh VSCode, press `Cmd + r`

## License

This project is made available under the MIT License.
