from pylsp import lsp, uris
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
    com_position = {"line": 0, "character": 2}
    workspace.put_document(DOC_URI, source=AUTOIMPORT_DOC)
    doc = workspace.get_document(DOC_URI)
    items = pylsp_autoimport_completions(config, workspace, doc, com_position)

    assert items
    assert check_dict(
        {"label": "pathlib", "kind": lsp.CompletionItemKind.Module}, items
    )
