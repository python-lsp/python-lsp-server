# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

import itertools
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


def _find_signatures_and_types(definitions):
    def _line_number(definition):
        """Helper for sorting definitions by line number (which might be None)."""
        return definition.line if definition.line is not None else 0

    def _get_signatures(definition):
        """Get the signatures of functions and classes."""
        return [
            signature.to_string()
            for signature in definition.get_signatures()
            if signature.type in ["class", "function"]
        ]

    definitions = sorted(definitions, key=_line_number)
    signatures_per_def = [_get_signatures(d) for d in definitions]
    types_per_def = [d.infer() for d in definitions]

    # a flat list with all signatures
    signatures = list(itertools.chain(*signatures_per_def))

    # We want to show the type if there is at least one type that does not
    # correspond to a signature
    if any(
        len(s) == 0 and len(t) > 0 for s, t in zip(signatures_per_def, types_per_def)
    ):
        # Get all types (also the ones that correspond to a signature)
        types = set(itertools.chain(*types_per_def))
        type_names = [t.name for t in sorted(types, key=_line_number)]

        if len(type_names) == 1:
            return [*signatures, type_names[0]]
        elif len(type_names) > 1:
            return [*signatures, f"Union[{', '.join(type_names)}]"]

    else:
        # The type does not add any information because it is already in the signatures
        return signatures


@hookimpl
def pylsp_hover(config, document, position):
    code_position = _utils.position_to_jedi_linecolumn(document, position)
    definitions = document.jedi_script(use_document_path=True).help(**code_position)

    hover_capabilities = config.capabilities.get("textDocument", {}).get("hover", {})
    supported_markup_kinds = hover_capabilities.get("contentFormat", ["markdown"])
    preferred_markup_kind = _utils.choose_markup_kind(supported_markup_kinds)

    return {
        "contents": _utils.format_docstring(
            _find_docstring(definitions),
            preferred_markup_kind,
            signatures=_find_signatures_and_types(definitions),
        )
    }
