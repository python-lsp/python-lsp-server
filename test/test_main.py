# Copyright 2021- Python Language Server Contributors.

import platform
import subprocess
import sys

import pytest

from pylsp._version import __version__


@pytest.mark.parametrize("flag", ["--version", "-V"])
def test_version_includes_python_runtime(flag):
    result = subprocess.run(
        [sys.executable, "-m", "pylsp", flag],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    assert f"v{__version__}" in result.stdout
    assert f"Python {platform.python_version()}" in result.stdout
    assert result.stderr == ""
