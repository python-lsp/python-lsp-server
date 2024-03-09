"""
Cases to consider
- Treesitter highlighting infers class, variable, function by casing and local context.
  e.g. if a class is declared as ``class dingus`` and later referenced as
  1. ``dingus``
  2. ``dingus()``
  then the declaration will be highlighted in the class color, 1. in a variable color,
  and 2. in a function color.
- Parameter highlighting. Params in the signature of a function and usage of a function
  should be highlighted the same color (turn of hlargs plugin to verify)
- Builtins?
- Dunders? "real" builtin dunders vs something the coder just put dunders around
"""

# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

import logging

from jedi.api.classes import Name

from pylsp import _utils, hookimpl
from pylsp.config.config import Config
from pylsp.lsp import SemanticTokenModifier, SemanticTokenType
from pylsp.workspace import Document

log = logging.getLogger(__name__)

# Valid values for type are ``module``, ``class``, ``instance``, ``function``,
# ``param``, ``path``, ``keyword``, ``property`` and ``statement``.
TYPE_MAP = {
    "module": SemanticTokenType.Namespace.value.value,
    "class": SemanticTokenType.Class.value.value,
    # "instance": SemanticTokenType.Type.value.value,
    "function": SemanticTokenType.Function.value.value,
    "param": SemanticTokenType.Parameter.value.value,
    # "path": SemanticTokenType.Type.value.value,
    # "keyword": SemanticTokenType.Type.value.value,
    "property": SemanticTokenType.Property.value.value,
    # "statement": SemanticTokenType.Type.value.value,
}


def _semantic_token(d: Name) -> tuple[int, int, int, int, int] | None:
    parent_defs = d.goto(
        follow_imports=True,
        follow_builtin_imports=True,
        only_stubs=False,
        prefer_stubs=False,
    )
    if not parent_defs:
        log.info("DOEKE! NO PARENT DEFS")
        return None
    if len(parent_defs) > 1:
        log.info("DOEKE! MORE THAN ONE PARENT DEF")
    parent_def, *_ = parent_defs
    log.info("DOEKE! PARENT DEF DESCRIPTION %s", parent_def.description)
    log.info("DOEKE! PARENT DEF TYPE %s", parent_def.type)
    if (parent_type := TYPE_MAP.get(parent_def.type, None)) is None:
        return None
    # if d.name == "self":
    #     modifier = 2**SemanticTokenModifier.Readonly.value.value
    # else:
    #     modifier = 0
    return (d.line - 1, d.column, len(d.name), parent_type, 0)


@hookimpl
def pylsp_semantic_tokens(config: Config, document: Document):
    log.info("DOEKE! semantic_tokens.pylsp_semantic_tokens")
    log.info("DOEKE! %s %s", type(config), type(document))

    symbols_settings = config.plugin_settings("semantic_tokens")
    definitions = document.jedi_names(
        all_scopes=True, definitions=True, references=True
    )
    data = []
    line, start_char = 0, 0
    for d in definitions:
        log.info("DOEKE! %s (%s) %s:%s", d.description, d.type, d.line, d.column)
        raw_token = _semantic_token(d)
        # log.info("DOEKE! raw token %s", raw_token)
        if raw_token is None:
            continue
        t_line, t_start_char, t_length, t_type, t_mod = raw_token
        delta_start_char, start_char = (
            (t_start_char - start_char, t_start_char)
            if t_line == line
            else (t_start_char, t_start_char)
        )
        delta_line, line = t_line - line, t_line
        new_token = [delta_line, delta_start_char, t_length, t_type, t_mod]
        log.info("DOEKE! diff token %s", new_token)
        data.extend(new_token)

    return {"data": data}
