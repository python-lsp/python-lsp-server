# Copyright 2025- Python Language Server Contributors.

import os
import sys

import pycodestyle

from pylsp import hookimpl
from pylsp.config.source import ConfigSource


class Flake8Config(ConfigSource):
    """Parse flake8 configurations."""

    CONFIG_KEY = "flake8"
    PROJECT_CONFIGS = [".flake8", "setup.cfg", "tox.ini"]
    USER_CONFIGS = (
        [os.path.expanduser("~\\.flake8")]
        if sys.platform == "win32" else [os.path.join(ConfigSource.XDG_CONFIG_HOME, "flake8")]
    )

    OPTIONS = [
        # mccabe
        ("max-complexity", "plugins.mccabe.threshold", int),
        # pycodestyle
        ("exclude", "plugins.pycodestyle.exclude", list),
        ("filename", "plugins.pycodestyle.filename", list),
        ("hang-closing", "plugins.pycodestyle.hangClosing", bool),
        ("ignore", "plugins.pycodestyle.ignore", list),
        ("max-line-length", "plugins.pycodestyle.maxLineLength", int),
        ("indent-size", "plugins.pycodestyle.indentSize", int),
        ("select", "plugins.pycodestyle.select", list),
        # flake8
        ("exclude", "plugins.flake8.exclude", list),
        ("extend-ignore", "plugins.flake8.extendIgnore", list),
        ("extend-select", "plugins.flake8.extendSelect", list),
        ("filename", "plugins.flake8.filename", list),
        ("hang-closing", "plugins.flake8.hangClosing", bool),
        ("ignore", "plugins.flake8.ignore", list),
        ("max-complexity", "plugins.flake8.maxComplexity", int),
        ("max-line-length", "plugins.flake8.maxLineLength", int),
        ("indent-size", "plugins.flake8.indentSize", int),
        ("select", "plugins.flake8.select", list),
        ("per-file-ignores", "plugins.flake8.perFileIgnores", list),
    ]

    @classmethod
    def _parse_list_opt(cls, string):
        if string.startswith("\n"):
            return [s.strip().rstrip(",") for s in string.split("\n") if s.strip()]
        return [s.strip() for s in string.split(",") if s.strip()]


class PyCodeStyleConfig(ConfigSource):
    CONFIG_KEY = "pycodestyle"
    USER_CONFIGS = [pycodestyle.USER_CONFIG] if pycodestyle.USER_CONFIG else []
    PROJECT_CONFIGS = ["pycodestyle.cfg", "setup.cfg", "tox.ini"]

    OPTIONS = [
        ("exclude", "plugins.pycodestyle.exclude", list),
        ("filename", "plugins.pycodestyle.filename", list),
        ("hang-closing", "plugins.pycodestyle.hangClosing", bool),
        ("ignore", "plugins.pycodestyle.ignore", list),
        ("max-line-length", "plugins.pycodestyle.maxLineLength", int),
        ("indent-size", "plugins.pycodestyle.indentSize", int),
        ("select", "plugins.pycodestyle.select", list),
        ("aggressive", "plugins.pycodestyle.aggressive", int),
    ]


# ---- pylsp_settings hook implementation (new architecture) ----
@hookimpl
def pylsp_settings():  # noqa: ARG001 (config not used yet)
    """Provide configuration source classes to the server.

    The server will instantiate each returned class with the workspace root.
    Returning classes (not instances) matches the new ServerConfig collection flow.
    """
    return [Flake8Config, PyCodeStyleConfig]
