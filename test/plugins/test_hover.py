# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

import os

from pylsp import uris
from pylsp.plugins.hover import pylsp_hover
from pylsp.workspace import Document

DOC_URI = uris.from_fs_path(__file__)
DOC = """

def main(a: float, b: float):
    \"\"\"hello world\"\"\"
    pass
"""

NUMPY_DOC = """

import numpy as np
np.sin

"""


def test_numpy_hover(workspace) -> None:
    # Over the blank line
    no_hov_position = {"line": 1, "character": 0}
    # Over 'numpy' in import numpy as np
    numpy_hov_position_1 = {"line": 2, "character": 8}
    # Over 'np' in import numpy as np
    numpy_hov_position_2 = {"line": 2, "character": 17}
    # Over 'np' in np.sin
    numpy_hov_position_3 = {"line": 3, "character": 1}
    # Over 'sin' in np.sin
    numpy_sin_hov_position = {"line": 3, "character": 4}

    doc = Document(DOC_URI, workspace, NUMPY_DOC)

    contents = ""
    assert contents in pylsp_hover(doc._config, doc, no_hov_position)["contents"]

    hover_res = pylsp_hover(doc._config, doc, numpy_hov_position_1)
    if hover_res["contents"] == "":
        import pytest
        pytest.skip("Jedi was unable to find hover information for numpy")

    contents = "NumPy\n=====\n\nProvides\n"
    if isinstance(hover_res["contents"], dict) and "value" in hover_res["contents"]:
        assert contents in hover_res["contents"]["value"]
    else:
        assert contents in hover_res["contents"]

    contents = "NumPy\n=====\n\nProvides\n"
    hover_res = pylsp_hover(doc._config, doc, numpy_hov_position_2)
    if isinstance(hover_res["contents"], dict) and "value" in hover_res["contents"]:
        assert contents in hover_res["contents"]["value"]
    else:
        assert contents in hover_res["contents"]

    contents = "NumPy\n=====\n\nProvides\n"
    hover_res = pylsp_hover(doc._config, doc, numpy_hov_position_3)
    if isinstance(hover_res["contents"], dict) and "value" in hover_res["contents"]:
        assert contents in hover_res["contents"]["value"]
    else:
        assert contents in hover_res["contents"]

    # https://github.com/davidhalter/jedi/issues/1746
    import numpy as np

    if np.lib.NumpyVersion(np.__version__) < "1.20.0":
        contents = "Trigonometric sine, element-wise.\n\n"
        hover_res = pylsp_hover(doc._config, doc, numpy_sin_hov_position)
        if isinstance(hover_res["contents"], dict) and "value" in hover_res["contents"]:
            assert contents in hover_res["contents"]["value"]
        else:
            assert contents in hover_res["contents"]


def test_hover(workspace) -> None:
    # Over 'main' in def main():
    hov_position = {"line": 2, "character": 6}
    # Over the blank second line
    no_hov_position = {"line": 1, "character": 0}

    doc = Document(DOC_URI, workspace, DOC)

    contents = {
        "kind": "markdown",
        "value": "```python\nmain(a: float, b: float)\n```\n\n\nhello world",
    }

    assert {"contents": contents} == pylsp_hover(doc._config, doc, hov_position)

    assert {"contents": ""} == pylsp_hover(doc._config, doc, no_hov_position)


def test_hover_signature_formatting(workspace) -> None:
    # Over 'main' in def main():
    hov_position = {"line": 2, "character": 6}

    doc = Document(DOC_URI, workspace, DOC)
    # setting low line length should trigger reflow to multiple lines
    doc._config.update({"signature": {"line_length": 10}})

    contents = {
        "kind": "markdown",
        "value": "```python\nmain(\n    a: float,\n    b: float,\n)\n```\n\n\nhello world",
    }

    assert {"contents": contents} == pylsp_hover(doc._config, doc, hov_position)


def test_hover_signature_formatting_opt_out(workspace) -> None:
    # Over 'main' in def main():
    hov_position = {"line": 2, "character": 6}

    doc = Document(DOC_URI, workspace, DOC)
    doc._config.update({"signature": {"line_length": 10, "formatter": None}})

    contents = {
        "kind": "markdown",
        "value": "```python\nmain(a: float, b: float)\n```\n\n\nhello world",
    }

    assert {"contents": contents} == pylsp_hover(doc._config, doc, hov_position)


def test_document_path_hover(workspace_other_root_path, tmpdir) -> None:
    # Create a dummy module out of the workspace's root_path and try to get
    # a definition on it in another file placed next to it.
    module_content = '''
def foo():
    """A docstring for foo."""
    pass
'''

    p = tmpdir.join("mymodule.py")
    p.write(module_content)

    # Content of doc to test definition
    doc_content = """from mymodule import foo
foo"""
    doc_path = str(tmpdir) + os.path.sep + "myfile.py"
    doc_uri = uris.from_fs_path(doc_path)
    doc = Document(doc_uri, workspace_other_root_path, doc_content)

    cursor_pos = {"line": 1, "character": 3}
    contents = pylsp_hover(doc._config, doc, cursor_pos)["contents"]

    assert "A docstring for foo." in contents["value"]


def test_hover_without_docstring(workspace_with_signature_docstring_disabled) -> None:
    # Over 'main' in def main():
    hov_position = {"line": 2, "character": 6}

    doc = Document(DOC_URI, workspace_with_signature_docstring_disabled, DOC)

    contents = {
        "kind": "markdown",
        "value": "```python\nmain(a: float, b: float)\n```\n",
    }

    assert {"contents": contents} == pylsp_hover(doc._config, doc, hov_position)
