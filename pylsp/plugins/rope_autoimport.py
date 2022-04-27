import logging
from collections import OrderedDict
from functools import lru_cache
from typing import Generator, List, Set

import parso
from parso.python import tree
from parso.tree import NodeOrLeaf
from rope.base.resources import Resource
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
        if first_child == word_node:
            return True
        if isinstance(first_child, tree.Import):
            return False
        if len(expr.children) > 1:
            if expr.children[1].type == "trailer":
                return False
        if isinstance(
            first_child,
            (
                tree.PythonLeaf,
                tree.PythonErrorLeaf,
            ),
        ):
            if first_child.value in ("import", "from"):
                return False
        if isinstance(first_child, (tree.PythonErrorNode, tree.PythonNode)):
            return should_insert(first_child, word_node)
        if isinstance(first_child, tree.Keyword):
            if first_child.value == "def":
                return _should_import_function(word_node, expr)
            if first_child.value == "class":
                return _should_import_class(word_node, expr)
    return True


def _should_import_class(word_node: tree.Leaf, expr: tree.BaseNode) -> bool:
    prev_node = None
    for node in expr.children:
        if isinstance(node, tree.Name):
            if isinstance(prev_node, tree.Operator):
                if node == word_node and prev_node.value == "(":
                    return True
        prev_node = node

    return False


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
        score = _get_score(source, import_statement, name, word)
        if score > 1000:
            continue
        yield {
            "label": name,
            "kind": itemkind,
            "sortText": _sort_import(score),
            "data": {"doc_uri": doc_uri},
            "detail": _document(import_statement),
            "additionalTextEdits": [edit],
        }


def _get_names_from_import(node: tree.Import) -> Generator[str, None, None]:
    if not node.is_star_import():
        for name in node.children:
            if isinstance(name, tree.PythonNode):
                for sub_name in name.children:
                    if isinstance(sub_name, tree.Name):
                        yield sub_name.value
            elif isinstance(name, tree.Name):
                yield name.value


@lru_cache(maxsize=100)
def get_names(file: str) -> Generator[str, None, None]:
    """Gets all names to ignore from the current file."""
    expr = parso.parse(file)
    for item in expr.children:
        if isinstance(item, tree.PythonNode):
            for child in item.children:
                if isinstance(child, (tree.ImportFrom, tree.ExprStmt)):
                    for name in child.get_defined_names():
                        yield name.value
                elif isinstance(child, tree.Import):
                    for name in _get_names_from_import(child):
                        yield name

        if isinstance(item, (tree.Function, tree.Class)):
            yield item.name.value


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
    ignored_names: Set[str] = set(get_names(document.source))
    autoimport = AutoImport(rope_project, memory=False)
    # TODO: update cache
    suggestions = list(autoimport.search_full(word, ignored_names=ignored_names))
    autoimport.close()
    results = list(
        sorted(
            _process_statements(suggestions, document.uri, word),
            key=lambda statement: statement["sortText"],
        )
    )
    if len(results) > 25:
        results = results[:25]
    return  results


def _document(import_statement: str) -> str:
    return "__autoimport__\n" + import_statement


def _get_score(
    source: int, full_statement: str, suggested_name: str, desired_name
) -> int:
    import_length = len("import")
    full_statement_score = (len(full_statement) - import_length) ** 2
    suggested_name_score = ((len(suggested_name) - len(desired_name))) ** 2
    source_score = 20 * source
    return source_score + suggested_name_score + full_statement_score


def _sort_import(score: int) -> str:
    pow = 5
    score = max(min(score, (10**pow) - 1), 0)
    # Since we are using ints, we need to pad them.
    # We also want to prioritize autoimport behind everything since its the last priority.
    # The minimum is to prevent score from overflowing the pad
    return "[z" + str(score).rjust(pow, "0")


@hookimpl
def pylsp_initialize(config: Config, workspace: Workspace):
    """Initialize AutoImport. Generates the cache for local and global items."""
    rope_config = config.settings().get("rope", {})
    rope_project = workspace._rope_project_builder(rope_config)
    autoimport = AutoImport(rope_project, memory=False)
    autoimport.generate_modules_cache()
    autoimport.generate_cache()
    autoimport.close()


@hookimpl
def pylsp_document_did_save(config: Config, workspace: Workspace, document: Document):
    """Update the names associated with this document. Doesn't work because this hook isn't called."""
    rope_config = config.settings().get("rope", {})
    rope_doucment: Resource = document._rope_resource(rope_config)
    rope_project = workspace._rope_project_builder(rope_config)
    autoimport = AutoImport(rope_project, memory=False)
    autoimport.generate_cache(resources=[rope_doucment])
    autoimport.generate_modules_cache()
    autoimport.close()
