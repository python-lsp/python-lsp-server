import logging
from collections import OrderedDict
from typing import TypedDict

from rope.contrib.autoimport import AutoImport

from pylsp import hookimpl, lsp
from pylsp.config.config import Config
from pylsp.workspace import Document, Workspace

log = logging.getLogger(__name__)


@hookimpl
def pylsp_settings():
    # Default rope_completion to disabled
    return {"plugins": {"rope_autoimport": {"enabled": True}}}


def deduplicate(input):
    """Remove duplicates from list."""
    return list(OrderedDict.fromkeys(input))


@hookimpl
def pylsp_completions(
    config: Config, workspace: Workspace, document: Document, position
):
    first_word = document.word_at_position(
        position={"line": position["line"], "character": 0}
    )
    word = document.word_at_position(position)
    if first_word in ("import", "from", "#") or "." in word:
        return []
    rope_config = config.settings(document_path=document.path).get("rope", {})
    rope_project = workspace._rope_project_builder(rope_config)
    autoimport = AutoImport(rope_project, memory=False)
    # TODO: update cache
    suggestions = deduplicate(autoimport.search_module(word))
    suggestions.extend(deduplicate(autoimport.search_name(word)))
    autoimport.close()
    results = []
    for import_statement, name, source, itemkind in suggestions:
        # insert_line = autoimport.find_insertion_line(document)
        # TODO: use isort to handle insertion line correctly
        insert_line = 0
        start = {"line": insert_line, "character": 0}
        range = {"start": start, "end": start}
        edit = {"range": range, "newText": import_statement + "\n"}
        item = {
            "label": name,
            "kind": itemkind,
            "sortText": _sort_import(source, import_statement, name, word),
            "data": {"doc_uri": document.uri},
            "documentation": _document(import_statement),
            "additionalTextEdits": [edit],
        }
        results.append(item)
    return results


def _document(import_statement: str) -> str:
    return "__autoimport__\n" + import_statement


def _sort_import(
    source: int, full_statement: str, suggested_name: str, desired_name
) -> str:
    import_length = len("import")
    full_statement_score = 2 * (len(full_statement) - import_length)
    suggested_name_score = 5 * (len(suggested_name) - len(desired_name))
    source_score = 20 * source
    score: int = source_score + suggested_name_score + full_statement_score
    # Since we are using ints, we need to pad them.
    # We also want to prioritize autoimport behind everything since its the last priority.
    return "zz" + str(score).rjust(10, "0")


@hookimpl
def pylsp_initialize(config: Config, workspace: Workspace):
    rope_config = config.settings().get("rope", {})
    rope_project = workspace._rope_project_builder(rope_config)
    autoimport = AutoImport(rope_project, memory=False)
    autoimport.generate_modules_cache()
    autoimport.generate_cache()
    autoimport.close()
