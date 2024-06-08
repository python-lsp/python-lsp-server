# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

import logging

from pylsp import hookimpl
from pylsp.lsp import SymbolKind

log = logging.getLogger(__name__)


@hookimpl
def pylsp_workspace_symbol(workspace, query):
    if not query or not workspace:
        return []

    return [
        _jedi_name_to_symbol(jedi_name)
        for jedi_name in workspace.complete_search(query)
    ]


def _jedi_name_to_symbol(jedi_name):
    return {
        "name": jedi_name.name,
        "kind": _jedi_type_to_symbol_kind(jedi_name.type),
        "location": {
            "uri": "file://" + str(jedi_name.module_path),
            "range": {
                "start": {"line": jedi_name.line - 1, "character": jedi_name.column},
                "end": {"line": jedi_name.line - 1, "character": jedi_name.column},
            },
        },
    }


def _jedi_type_to_symbol_kind(jedi_type):
    return {
        "module": SymbolKind.Module,
        "class": SymbolKind.Class,
        "function": SymbolKind.Function,
    }.get(jedi_type, SymbolKind.Variable)
