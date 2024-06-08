# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

import os
import sys

import pytest

from pylsp import uris
from pylsp.plugins.workspace_symbol import pylsp_workspace_symbol

PY2 = sys.version[0] == "2"
LINUX = sys.platform.startswith("linux")
CI = os.environ.get("CI")
DOC_URI = uris.from_fs_path(__file__)


DOC1_NAME = "file1.py"
DOC2_NAME = "file2.py"

DOC1 = """class Test1():
    pass
"""

DOC2 = """from file1 import Test1

try:
    Test1()
except UnicodeError:
    pass
"""


@pytest.fixture
def tmp_workspace(temp_workspace_factory):
    return temp_workspace_factory(
        {
            DOC1_NAME: DOC1,
            DOC2_NAME: DOC2,
        }
    )


def test_symbols_empty_query(tmp_workspace):
    symbols = pylsp_workspace_symbol(tmp_workspace, "")

    assert len(symbols) == 0


def test_symbols_nonempty_query(tmp_workspace):
    symbols = pylsp_workspace_symbol(tmp_workspace, "Test")

    assert len(symbols) == 1
    assert symbols[0]["name"] == "Test1"
    assert symbols[0]["kind"] == 5  # Class
