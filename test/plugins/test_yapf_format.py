# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

import pytest

from pylsp import uris
from pylsp.plugins.yapf_format import pylsp_format_document, pylsp_format_range
from pylsp.text_edit import apply_text_edits
from pylsp.workspace import Document

DOC_URI = uris.from_fs_path(__file__)
DOC = """A = [
    'h',   'w',

    'a'
      ]

B = ['h',


'w']
"""

GOOD_DOC = """A = ['hello', 'world']\n"""
FOUR_SPACE_DOC = """def hello():
    pass
"""


def test_format(workspace) -> None:
    doc = Document(uri=DOC_URI, workspace=workspace, source=DOC)
    res = pylsp_format_document(workspace=workspace, document=doc, options=None)

    assert apply_text_edits(doc=doc, text_edits=res) == "A = ['h', 'w', 'a']\n\nB = ['h', 'w']\n"


def test_range_format(workspace) -> None:
    doc = Document(uri=DOC_URI, workspace=workspace, source=DOC)

    def_range = {
        "start": {"line": 0, "character": 0},
        "end": {"line": 4, "character": 10},
    }
    res = pylsp_format_range(document=doc, range=def_range, options=None)

    # Make sure B is still badly formatted
    assert apply_text_edits(doc=doc, text_edits=res) == "A = ['h', 'w', 'a']\n\nB = ['h',\n\n\n'w']\n"


def test_no_change(workspace) -> None:
    doc = Document(uri=DOC_URI, workspace=workspace, source=GOOD_DOC)
    assert not pylsp_format_document(workspace=workspace, document=doc, options=None)


def test_config_file(tmpdir, workspace) -> None:
    # a config file in the same directory as the source file will be used
    conf = tmpdir.join(".style.yapf")
    conf.write("[style]\ncolumn_limit = 14")
    src = tmpdir.join("test.py")
    doc = Document(uri=uris.from_fs_path(src.strpath), workspace=workspace, source=DOC)

    res = pylsp_format_document(workspace=workspace, document=doc, options=None)

    # A was split on multiple lines because of column_limit from config file
    assert (
        apply_text_edits(doc=doc, text_edits=res)
        == "A = [\n    'h', 'w',\n    'a'\n]\n\nB = ['h', 'w']\n"
    )


@pytest.mark.parametrize("newline", ["\r\n"])
def test_line_endings(workspace, newline) -> None:
    doc = Document(uri=DOC_URI, workspace=workspace, source=f"import os;import sys{2 * newline}dict(a=1)")
    res = pylsp_format_document(workspace=workspace, document=doc, options=None)

    assert (
        apply_text_edits(doc=doc, text_edits=res)
        == f"import os{newline}import sys{2 * newline}dict(a=1){newline}"
    )


def test_format_with_tab_size_option(workspace) -> None:
    doc = Document(uri=DOC_URI, workspace=workspace, source=FOUR_SPACE_DOC)
    res = pylsp_format_document(workspace=workspace, document=doc, options={"tabSize": "8"})

    assert apply_text_edits(doc=doc, text_edits=res) == FOUR_SPACE_DOC.replace("    ", "        ")


def test_format_with_insert_spaces_option(workspace) -> None:
    doc = Document(uri=DOC_URI, workspace=workspace, source=FOUR_SPACE_DOC)
    res = pylsp_format_document(workspace=workspace, document=doc, options={"insertSpaces": False})

    assert apply_text_edits(doc=doc, text_edits=res) == FOUR_SPACE_DOC.replace("    ", "\t")


def test_format_with_yapf_specific_option(workspace) -> None:
    doc = Document(uri=DOC_URI, workspace=workspace, source=FOUR_SPACE_DOC)
    res = pylsp_format_document(workspace=workspace, document=doc, options={"USE_TABS": True})

    assert apply_text_edits(doc=doc, text_edits=res) == FOUR_SPACE_DOC.replace("    ", "\t")


def test_format_returns_text_edit_per_line(workspace) -> None:
    single_space_indent = """def wow():
 log("x")
 log("hi")"""
    doc = Document(uri=DOC_URI, workspace=workspace, source=single_space_indent)
    res = pylsp_format_document(workspace=workspace, document=doc, options=None)

    # two removes and two adds
    assert len(res) == 4
    assert res[0]["newText"] == ""
    assert res[1]["newText"] == ""
    assert res[2]["newText"] == '    log("x")\n'
    assert res[3]["newText"] == '    log("hi")\n'
