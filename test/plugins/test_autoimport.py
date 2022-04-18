from pylsp import lsp, uris
from pylsp.plugins.rope_autoimport import _sort_import
from pylsp.plugins.rope_autoimport import \
    pylsp_completions as pylsp_autoimport_completions

DOC_URI = uris.from_fs_path(__file__)
from typing import Dict, List


def check_dict(query: Dict, results: List[Dict]) -> bool:
    for result in results:
        if all(result[key] == query[key] for key in query.keys()):
            return True
    return False


def test_autoimport_completion(config, workspace):
    AUTOIMPORT_DOC = """pathli"""
    # Over 'i' in os.path.isabs(...)
    com_position = {"line": 0, "character": 6}
    workspace.put_document(DOC_URI, source=AUTOIMPORT_DOC)
    doc = workspace.get_document(DOC_URI)
    items = pylsp_autoimport_completions(config, workspace, doc, com_position)

    assert items
    assert check_dict(
        {"label": "pathlib", "kind": lsp.CompletionItemKind.Module}, items
    )


def test_autoimport_import(config, workspace):
    AUTOIMPORT_DOC = """import"""
    # Over 'i' in os.path.isabs(...)
    com_position = {"line": 0, "character": 6}
    workspace.put_document(DOC_URI, source=AUTOIMPORT_DOC)
    doc = workspace.get_document(DOC_URI)
    items = pylsp_autoimport_completions(config, workspace, doc, com_position)

    assert len(items) == 0


def test_autoimport_dot(config, workspace):
    AUTOIMPORT_DOC = """str."""
    # Over 'i' in os.path.isabs(...)
    com_position = {"line": 0, "character": 4}
    workspace.put_document(DOC_URI, source=AUTOIMPORT_DOC)
    doc = workspace.get_document(DOC_URI)
    items = pylsp_autoimport_completions(config, workspace, doc, com_position)

    assert len(items) == 0


def test_autoimport_comment(config, workspace):
    AUTOIMPORT_DOC = """#"""
    # Over 'i' in os.path.isabs(...)
    com_position = {"line": 0, "character": 0}
    workspace.put_document(DOC_URI, source=AUTOIMPORT_DOC)
    doc = workspace.get_document(DOC_URI)
    items = pylsp_autoimport_completions(config, workspace, doc, com_position)

    assert len(items) == 0

def test_autoimport_from(config, workspace):
    AUTOIMPORT_DOC = """from"""
    # Over 'i' in os.path.isabs(...)
    com_position = {"line": 0, "character": 6}
    workspace.put_document(DOC_URI, source=AUTOIMPORT_DOC)
    doc = workspace.get_document(DOC_URI)
    items = pylsp_autoimport_completions(config, workspace, doc, com_position)


    assert len(items) == 0


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
