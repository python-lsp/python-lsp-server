import logging
from collections import OrderedDict
from typing import TypedDict

from rope.contrib.autoimport import AutoImport

from pylsp import hookimpl, lsp
from pylsp.config.config import Config
from pylsp.workspace import Workspace

log = logging.getLogger(__name__)


@hookimpl
def pylsp_settings():
    # Default rope_completion to disabled
    return {"plugins": {"rope_autoimport": {"enabled": True}}}


def deduplicate(input):
    return list(OrderedDict.fromkeys(input))


@hookimpl
def pylsp_completions(config: Config, workspace: Workspace, document, position):
    word = document.word_at_position(position)
    if "." in word:
        return []
    rope_config = config.settings(document_path=document.path).get("rope", {})
    rope_project = workspace._rope_project_builder(rope_config)
    autoimport = AutoImport(rope_project, memory=False)
    autoimport.generate_modules_cache()
    suggestions = deduplicate(autoimport.search_module(word))
    suggestions.extend(deduplicate(autoimport.search_name(word)))
    results = []
    for import_statement, name, source, itemkind in suggestions:
        item = {
            "label": name,
            "kind": itemkind,
            "sortText": _sort_import(source, import_statement, name, word),
            "data": {"doc_uri": document.uri},
            "documentation": _document(import_statement),
        }
        results.append(item)
    autoimport.close()
    return results


def _document(import_statement: str) -> str:
    return import_statement


def _sort_import(
    source: int, full_statement: str, suggested_name: str, desired_name
) -> int:
    import_length = len("import")
    full_statement_score = 2 * (len(full_statement) - import_length)
    suggested_name_score = 5 * (len(suggested_name) - len(desired_name))
    source_score = 20 * source
    return source_score + suggested_name_score + full_statement_score


@hookimpl
def pylsp_initialize(config: Config, workspace: Workspace):
    rope_config = config.settings().get("rope", {})
    rope_project = workspace._rope_project_builder(rope_config)
    autoimport = AutoImport(rope_project, memory=False)
    autoimport.generate_modules_cache()
    autoimport.close()
