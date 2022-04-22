from typing import Dict, List

import pytest

from pylsp import lsp, uris
from pylsp.plugins.rope_autoimport import _sort_import, get_names
from pylsp.plugins.rope_autoimport import (
    pylsp_completions as pylsp_autoimport_completions,
)

DOC_URI = uris.from_fs_path(__file__)


@pytest.fixture
def completions(config, workspace, request):
    document, position = request.param
    com_position = {"line": 0, "character": position}
    workspace.put_document(DOC_URI, source=document)
    doc = workspace.get_document(DOC_URI)
    yield pylsp_autoimport_completions(config, workspace, doc, com_position)
    workspace.rm_document(DOC_URI)


def check_dict(query: Dict, results: List[Dict]) -> bool:
    for result in results:
        if all(result[key] == query[key] for key in query.keys()):
            return True
    return False


@pytest.mark.parametrize("completions", [("""pathli """, 6)], indirect=True)
def test_autoimport_completion(completions):
    assert completions
    assert check_dict(
        {"label": "pathlib", "kind": lsp.CompletionItemKind.Module}, completions
    )


@pytest.mark.parametrize("completions", [("""import """, 7)], indirect=True)
def test_autoimport_import(completions):
    assert len(completions) == 0


@pytest.mark.parametrize("completions", [("""def func(s""", 10)], indirect=True)
def test_autoimport_function(completions):

    assert len(completions) == 0


@pytest.mark.parametrize("completions", [("""def func(s:Lis""", 12)], indirect=True)
def test_autoimport_function_typing(completions):
    assert len(completions) > 0
    assert check_dict({"label": "List"}, completions)


@pytest.mark.parametrize(
    "completions", [("""def func(s : Lis ):""", 16)], indirect=True
)
def test_autoimport_function_typing_complete(completions):
    assert len(completions) > 0
    assert check_dict({"label": "List"}, completions)


@pytest.mark.parametrize(
    "completions", [("""def func(s : Lis ) -> Generat:""", 29)], indirect=True
)
def test_autoimport_function_typing_return(completions):
    assert len(completions) > 0
    assert check_dict({"label": "Generator"}, completions)


def test_autoimport_defined_name(config, workspace):
    document = """List = "hi"\nLis"""
    com_position = {"line": 1, "character": 3}
    workspace.put_document(DOC_URI, source=document)
    doc = workspace.get_document(DOC_URI)
    completions = pylsp_autoimport_completions(config, workspace, doc, com_position)
    workspace.rm_document(DOC_URI)
    assert not check_dict({"label": "List"}, completions)


@pytest.mark.parametrize("completions", [("""str.""", 4)], indirect=True)
def test_autoimport_dot(completions):

    assert len(completions) == 0


@pytest.mark.parametrize("completions", [("""#""", 1)], indirect=True)
def test_autoimport_comment(completions):
    assert len(completions) == 0


@pytest.mark.parametrize("completions", [("""    # """, 5)], indirect=True)
def test_autoimport_comment_indent(completions):

    assert len(completions) == 0


@pytest.mark.parametrize("completions", [("""from """, 5)], indirect=True)
def test_autoimport_from(completions):
    assert len(completions) == 0


@pytest.mark.parametrize("completions", [("""from """, 4)], indirect=True)
def test_autoimport_from_(completions):
    assert len(completions) > 0


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


def test_get_names():
    source = """
    from a import s as e
    import blah, bleh
    hello = "str"
    a, b = 1, 2
    def someone(): 
        soemthing
    class sfa:
        sfiosifo
    """
    results = set(get_names(source))
    assert results == set(["blah", "bleh", "e", "hello", "someone", "sfa", "a", "b"])
