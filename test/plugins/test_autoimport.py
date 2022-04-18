from typing import Dict, List

from pylsp import lsp, uris
from pylsp.plugins.rope_autoimport import _sort_import
from pylsp.plugins.rope_autoimport import \
    pylsp_completions as pylsp_autoimport_completions

DOC_URI = uris.from_fs_path(__file__)


def check_dict(query: Dict, results: List[Dict]) -> bool:
    for result in results:
        if all(result[key] == query[key] for key in query.keys()):
            return True
    return False


def test_autoimport_completion(config, workspace):
    AUTOIMPORT_DOC = """pathli"""
    com_position = {"line": 0, "character": 6}
    workspace.put_document(DOC_URI, source=AUTOIMPORT_DOC)
    doc = workspace.get_document(DOC_URI)
    items = pylsp_autoimport_completions(config, workspace, doc, com_position)

    assert items
    assert check_dict(
        {"label": "pathlib", "kind": lsp.CompletionItemKind.Module}, items
    )


def test_autoimport_import(config, workspace):
    AUTOIMPORT_DOC = """import """
    com_position = {"line": 0, "character": 7}
    workspace.put_document(DOC_URI, source=AUTOIMPORT_DOC)
    doc = workspace.get_document(DOC_URI)
    items = pylsp_autoimport_completions(config, workspace, doc, com_position)

    assert len(items) == 0


def test_autoimport_function(config, workspace):
    AUTOIMPORT_DOC = """def func(s"""
    com_position = {"line": 0, "character": 10}
    workspace.put_document(DOC_URI, source=AUTOIMPORT_DOC)
    doc = workspace.get_document(DOC_URI)
    items = pylsp_autoimport_completions(config, workspace, doc, com_position)

    assert len(items) == 0


def test_autoimport_function_typing(config, workspace):
    AUTOIMPORT_DOC = """def func(s : Lis """
    com_position = {"line": 0, "character": 16}
    workspace.put_document(DOC_URI, source=AUTOIMPORT_DOC)
    doc = workspace.get_document(DOC_URI)
    items = pylsp_autoimport_completions(config, workspace, doc, com_position)

    assert len(items) > 0

    assert check_dict({"label": "List"}, items)

def test_autoimport_function_typing_complete(config, workspace):
    AUTOIMPORT_DOC = """def func(s : Lis ):"""
    com_position = {"line": 0, "character": 16}
    workspace.put_document(DOC_URI, source=AUTOIMPORT_DOC)
    doc = workspace.get_document(DOC_URI)
    items = pylsp_autoimport_completions(config, workspace, doc, com_position)

    assert len(items) > 0

    assert check_dict({"label": "List"}, items)

def test_autoimport_function_typing_return(config, workspace):
    AUTOIMPORT_DOC = """def func(s : Lis ) -> Generat:"""
    com_position = {"line": 0, "character": 29}
    workspace.put_document(DOC_URI, source=AUTOIMPORT_DOC)
    doc = workspace.get_document(DOC_URI)
    items = pylsp_autoimport_completions(config, workspace, doc, com_position)

    assert len(items) > 0

    assert check_dict({"label": "Generator"}, items)
def test_autoimport_dot(config, workspace):
    AUTOIMPORT_DOC = """str."""
    com_position = {"line": 0, "character": 4}
    workspace.put_document(DOC_URI, source=AUTOIMPORT_DOC)
    doc = workspace.get_document(DOC_URI)
    items = pylsp_autoimport_completions(config, workspace, doc, com_position)

    assert len(items) == 0


def test_autoimport_comment(config, workspace):
    AUTOIMPORT_DOC = """#"""
    com_position = {"line": 0, "character": 1}
    workspace.put_document(DOC_URI, source=AUTOIMPORT_DOC)
    doc = workspace.get_document(DOC_URI)
    items = pylsp_autoimport_completions(config, workspace, doc, com_position)

    assert len(items) == 0


def test_autoimport_comment_indent(config, workspace):
    AUTOIMPORT_DOC = """    # """
    com_position = {"line": 0, "character": 5}
    workspace.put_document(DOC_URI, source=AUTOIMPORT_DOC)
    doc = workspace.get_document(DOC_URI)
    items = pylsp_autoimport_completions(config, workspace, doc, com_position)

    assert len(items) == 0


def test_autoimport_from(config, workspace):
    AUTOIMPORT_DOC = """from """
    com_position = {"line": 0, "character": 5}
    workspace.put_document(DOC_URI, source=AUTOIMPORT_DOC)
    doc = workspace.get_document(DOC_URI)
    items = pylsp_autoimport_completions(config, workspace, doc, com_position)

    assert len(items) == 0


def test_autoimport_from_(config, workspace):
    AUTOIMPORT_DOC = """from """
    com_position = {"line": 0, "character": 4}
    workspace.put_document(DOC_URI, source=AUTOIMPORT_DOC)
    doc = workspace.get_document(DOC_URI)
    items = pylsp_autoimport_completions(config, workspace, doc, com_position)

    assert len(items) > 0


def test_sort_sources():
    result1 = _sort_import(1, "import pathlib", "pathlib", "pathli")
    result2 = _sort_import(2, "import pathlib", "pathlib", "pathli")
    assert result1 < result2


def test_sort_statements():
    result1 = _sort_import(
        2, "from importlib_metadata import pathlib", "pathlib", "pathli"
    )
    result2 = _sort_import(2, "import pathlib", "pathlib", "pathli")
    assert result1 > result2


def test_sort_both():
    result1 = _sort_import(
        3, "from importlib_metadata import pathlib", "pathlib", "pathli"
    )
    result2 = _sort_import(2, "import pathlib", "pathlib", "pathli")
    assert result1 > result2
