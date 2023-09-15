# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.
from __future__ import annotations
import logging
from typing import Any, Dict, List, TYPE_CHECKING
from pylsp import hookimpl, uris, _utils

if TYPE_CHECKING:
    from jedi.api import Script
    from jedi.api.classes import Name
    from pylsp.config.config import Config
    from pylsp.workspace import Document

log = logging.getLogger(__name__)


def _resolve_definition(
    maybe_defn: Name, script: Script, settings: Dict[str, Any]
) -> Name:
    while not maybe_defn.is_definition() and maybe_defn.module_path == script.path:
        defns = script.goto(
            follow_imports=settings.get("follow_imports", True),
            follow_builtin_imports=settings.get("follow_builtin_imports", True),
            line=maybe_defn.line,
            column=maybe_defn.column,
        )
        if len(defns) == 1:
            maybe_defn = defns[0]
        else:
            break
    return maybe_defn


@hookimpl
def pylsp_definitions(
    config: Config, document: Document, position: Dict[str, int]
) -> List[Dict[str, Any]]:
    settings = config.plugin_settings("jedi_definition")
    code_position = _utils.position_to_jedi_linecolumn(document, position)
    script = document.jedi_script(use_document_path=True)
    definitions = script.goto(
        follow_imports=settings.get("follow_imports", True),
        follow_builtin_imports=settings.get("follow_builtin_imports", True),
        **code_position,
    )
    definitions = [_resolve_definition(d, script, settings) for d in definitions]
    follow_builtin_defns = settings.get("follow_builtin_definitions", True)
    return [
        {
            "uri": uris.uri_with(document.uri, path=str(d.module_path)),
            "range": {
                "start": {"line": d.line - 1, "character": d.column},
                "end": {"line": d.line - 1, "character": d.column + len(d.name)},
            },
        }
        for d in definitions
        if d.is_definition() and (follow_builtin_defns or _not_internal_definition(d))
    ]


def _not_internal_definition(definition: Name) -> bool:
    return (
        definition.line is not None
        and definition.column is not None
        and definition.module_path is not None
        and not definition.in_builtin_module()
    )
