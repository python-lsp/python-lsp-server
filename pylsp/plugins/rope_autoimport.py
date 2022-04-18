import logging
from collections import OrderedDict
from typing import Generator, List

import parso
from parso.python import tree
from parso.tree import NodeOrLeaf
from rope.contrib.autoimport import AutoImport

from pylsp import hookimpl
from pylsp.config.config import Config
from pylsp.workspace import Document, Workspace

log = logging.getLogger(__name__)


@hookimpl
def pylsp_settings():
    # Default rope_completion to disabled
    return {"plugins": {"rope_autoimport": {"enabled": True}}}


def deduplicate(input_list):
    """Remove duplicates from list."""
    return list(OrderedDict.fromkeys(input_list))


def should_insert(expr: tree.BaseNode, word_node: tree.Leaf) -> bool:
    if len(expr.children) > 0:
        first_child = expr.children[0]
        if isinstance(first_child, tree.EndMarker):
            if "#" in first_child.prefix:
                return False
        if isinstance(
            first_child,
            (
                tree.PythonLeaf,
                tree.PythonErrorLeaf,
            ),
        ):
            if first_child.value in ("import", "from") and first_child != word_node:
                return False
        if isinstance(first_child, (tree.PythonErrorNode)):
            return should_insert(first_child, word_node)
        if isinstance(first_child, tree.Keyword):
            if first_child.value == "def":
                return _should_import_function(word_node, expr)
    return True


def _should_import_function(word_node: tree.Leaf, expr: tree.BaseNode) -> bool:
    prev_node = None
    for node in expr.children:
        if _handle_argument(node, word_node):
            return True
        if isinstance(prev_node, tree.Operator):
            if prev_node.value == "->":
                if node == word_node:
                    return True
        prev_node = node
    return False


def _handle_argument(node: NodeOrLeaf, word_node: tree.Leaf):
    if isinstance(node, tree.PythonNode):
        if node.type == "tfpdef":
            if node.children[2] == word_node:
                return True
        if node.type == "parameters":
            for parameter in node.children:
                if _handle_argument(parameter, word_node):
                    return True
    return False


def _process_statements(suggestions: List, doc_uri: str, word: str) -> Generator:
    for import_statement, name, source, itemkind in suggestions:
        # insert_line = autoimport.find_insertion_line(document)
        # TODO: use isort to handle insertion line correctly
        insert_line = 0
        start = {"line": insert_line, "character": 0}
        edit_range = {"start": start, "end": start}
        edit = {"range": edit_range, "newText": import_statement + "\n"}
        yield {
            "label": name,
            "kind": itemkind,
            "sortText": _sort_import(source, import_statement, name, word),
            "data": {"doc_uri": doc_uri},
            "documentation": _document(import_statement),
            "additionalTextEdits": [edit],
        }


@hookimpl
def pylsp_completions(
    config: Config, workspace: Workspace, document: Document, position
):
    line = document.lines[position["line"]]
    expr = parso.parse(line)
    word_node = expr.get_leaf_for_position((1, position["character"]))
    if not should_insert(expr, word_node):
        return []
    word = word_node.value
    rope_config = config.settings(document_path=document.path).get("rope", {})
    rope_project = workspace._rope_project_builder(rope_config)
    autoimport = AutoImport(rope_project, memory=False)
    # TODO: update cache
    suggestions = deduplicate(autoimport.search_module(word))
    suggestions.extend(deduplicate(autoimport.search_name(word)))
    autoimport.close()
    return list(_process_statements(suggestions, document.uri, word))


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
