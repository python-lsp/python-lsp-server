# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

import logging

from jedi.api.classes import Name

from pylsp import hookimpl
from pylsp.config.config import Config
from pylsp.lsp import SemanticTokenType
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
    "keyword": SemanticTokenType.Keyword.value.value,
    "property": SemanticTokenType.Property.value.value,
    # "statement": SemanticTokenType.Variable.value.value,
}


def _raw_semantic_token(n: Name) -> list[int] | None:
    """Find an appropriate semantic token for the name.

    This works by looking up the definition (using jedi ``goto``) of the name and
    matching the definition's type to one of the availabile semantic tokens. Further
    improvements are possible by inspecting context, e.g. semantic token modifiers such
    as ``abstract`` or ``async`` or even different tokens, e.g. ``property`` or
    ``method``. Dunder methods may warrant special treatment/modifiers as well.

    The return is a "raw" semantic token rather than a "diff." This is in the form of a
    length 5 array of integers where the elements are the line number, starting
    character, length, token index, and modifiers (as an integer whose binary
    representation has bits set at the indices of all applicable modifiers).
    """
    definitions = n.goto(
        follow_imports=True,
        follow_builtin_imports=True,
        only_stubs=False,
        prefer_stubs=False,
    )
    if not definitions:
        log.debug(
            "no definitions found for name %s (%s:%s)", n.description, n.line, n.column
        )
        return None
    if len(definitions) > 1:
        log.debug(
            "multiple definitions found for name %s (%s:%s)",
            n.description,
            n.line,
            n.column,
        )
    definition, *_ = definitions
    if (definition_type := TYPE_MAP.get(definition.type, None)) is None:
        log.debug(
            "no matching semantic token for name %s (%s:%s)",
            n.description,
            n.line,
            n.column,
        )
        return None
    return [n.line - 1, n.column, len(n.name), definition_type, 0]


def _diff_position(
    token_line: int, token_start_char: int, current_line: int, current_start_char: int
) -> tuple[int, int, int, int]:
    """Compute the diff position for a semantic token.

    This returns the delta line and column as well as what should be considered the
    "new" current line and column.
    """
    delta_start_char = (
        token_start_char - current_start_char
        if token_line == current_line
        else token_start_char
    )
    delta_line = token_line - current_line
    return (delta_line, delta_start_char, token_line, token_start_char)


@hookimpl
def pylsp_semantic_tokens(config: Config, document: Document):
    # Currently unused, but leaving it here for easy adding of settings.
    symbols_settings = config.plugin_settings("semantic_tokens")

    names = document.jedi_names(all_scopes=True, definitions=True, references=True)
    data = []
    line, start_char = 0, 0
    for n in names:
        token = _raw_semantic_token(n)
        log.debug(
            "raw token for name %s (%s:%s): %s", n.description, n.line, n.column, token
        )
        if token is None:
            continue
        token[0], token[1], line, start_char = _diff_position(
            token[0], token[1], line, start_char
        )
        log.debug(
            "diff token for name %s (%s:%s): %s", n.description, n.line, n.column, token
        )
        data.extend(token)

    return {"data": data}
