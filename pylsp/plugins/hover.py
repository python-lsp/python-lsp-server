# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

import logging

from pylsp import _utils, hookimpl

log = logging.getLogger(__name__)


def _find_docstring(definitions):
    if len(definitions) != 1:
        # Either no definitions or multiple definitions
        # If we have multiple definitions the element can be multiple things and we
        # do not know which one

        # TODO(Review)
        # We could also concatenate all docstrings we find in the definitions
        # I am against this because
        # - If just one definition has a docstring, it gives a false impression of the hover element
        # - If multiple definitions have a docstring, the user will probably not realize
        #   that he can scroll to see the other options
        return ""

    # The single true definition
    definition = definitions[0]
    docstring = definition.docstring(
        raw=True
    )  # raw docstring returns only doc, without signature
    if docstring != "":
        return docstring

    # If the definition has no docstring, try to infer the type
    types = definition.infer()

    if len(types) != 1:
        # If we have multiple types the element can be multiple things and we
        # do not know which one
        return ""

    # Use the docstring of the single true type (possibly empty)
    return types[0].docstring(raw=True)


def _find_signatures(definitions, word):
    # Get the signatures of all definitions
    signatures = [
        signature.to_string()
        for definition in definitions
        for signature in definition.get_signatures()
        if signature.type not in ["module"]
    ]

    if len(signatures) != 0:
        return signatures

    # If we did not find a signature, infer the possible types of all definitions
    types = [
        t.name
        for d in sorted(definitions, key=lambda d: d.line)
        for t in sorted(d.infer(), key=lambda t: t.line)
    ]
    if len(types) == 1:
        return [types[0]]
    elif len(types) > 1:
        return [f"Union[{', '.join(types)}]"]


@hookimpl
def pylsp_hover(config, document, position):
    code_position = _utils.position_to_jedi_linecolumn(document, position)

    # TODO(Review)
    # We could also use Script.help here. It would not resolve keywords
    definitions = document.jedi_script(use_document_path=True).help(**code_position)
    word = document.word_at_position(position)

    hover_capabilities = config.capabilities.get("textDocument", {}).get("hover", {})
    supported_markup_kinds = hover_capabilities.get("contentFormat", ["markdown"])
    preferred_markup_kind = _utils.choose_markup_kind(supported_markup_kinds)

    return {
        "contents": _utils.format_docstring(
            _find_docstring(definitions),
            preferred_markup_kind,
            signatures=_find_signatures(definitions, word),
        )
    }
