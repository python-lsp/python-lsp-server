# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.
import configparser
import logging
import os
import sys
from collections.abc import Mapping, MutableMapping
from functools import cached_property
from copy import deepcopy

from pylsp._utils import find_parents

log = logging.getLogger(__name__)


class ConfigSource:
    """Base class for implementing a config source."""

    XDG_CONFIG_HOME = os.environ.get(
        "XDG_CONFIG_HOME", os.path.expanduser("~/.config")
    )

    USER_CONFIGS = []
    """list: User config files to search for."""

    PROJECT_CONFIGS = []
    """list: Project config files to search for."""

    OPTIONS = []
    """list: Options to parse from the config files."""

    CONFIG_KEY = ""
    """str: The config section key to look for when parsing."""

    def __init__(self, root_path) -> None:
        self.root_path = root_path

    @cached_property
    def user_config(self):
        """Return user-level (i.e. home directory) configuration."""
        return self.read_config_from_files(self.USER_CONFIGS)

    def project_config(self, document_path):
        """Return project-level (i.e. workspace directory) configuration.
        """
        return self.read_config_from_files(
            find_parents(self.root_path, document_path, self.PROJECT_CONFIGS)
        )

    @classmethod
    def read_config_from_files(cls, files):
        config = configparser.RawConfigParser()
        for filename in files:
            if os.path.exists(filename) and not os.path.isdir(filename):
                config.read(filename)

        return cls.parse_config(config, cls.CONFIG_KEY, cls.OPTIONS)

    @classmethod
    def parse_config(cls, config, key, options):
        """Parse the config with the given options."""
        conf = {}
        for source, destination, opt_type in options:
            opt_value = cls._get_opt(config, key, source, opt_type)
            if opt_value is not None:
                cls._set_opt(conf, destination, opt_value)
        return conf

    @classmethod
    def _get_opt(cls, config, key, option, opt_type):
        """Get an option from a configparser with the given type."""
        for opt_key in [option, option.replace("-", "_")]:
            if not config.has_option(key, opt_key):
                continue

            if opt_type is bool:
                return config.getboolean(key, opt_key)

            if opt_type is int:
                return config.getint(key, opt_key)

            if opt_type is str:
                return config.get(key, opt_key)

            if opt_type is list:
                return cls._parse_list_opt(config.get(key, opt_key))

            raise ValueError("Unknown option type: %s" % opt_type)

    @classmethod
    def _parse_list_opt(cls, string):
        return [s.strip() for s in string.split(",") if s.strip()]

    @classmethod
    def _set_opt(cls, config_dict, path, value):
        """Set the value in the dictionary at the given path if the value is not None."""
        if value is None:
            return

        if "." not in path:
            config_dict[path] = value
            return

        key, rest = path.split(".", 1)
        if key not in config_dict:
            config_dict[key] = {}

        cls._set_opt(config_dict[key], rest, value)
