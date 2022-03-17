# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

import logging
import os

from yapf.yapflib import file_resources
from yapf.yapflib.yapf_api import FormatCode

import whatthepatch

from pylsp import hookimpl
from pylsp._utils import get_eol_chars

log = logging.getLogger(__name__)


@hookimpl
def pylsp_format_document(document):
    return _format(document)


@hookimpl
def pylsp_format_range(document, range):  # pylint: disable=redefined-builtin
    # First we 'round' the range up/down to full lines only
    range['start']['character'] = 0
    range['end']['line'] += 1
    range['end']['character'] = 0

    # From Yapf docs:
    # lines: (list of tuples of integers) A list of tuples of lines, [start, end],
    #   that we want to format. The lines are 1-based indexed. It can be used by
    #   third-party code (e.g., IDEs) when reformatting a snippet of code rather
    #   than a whole file.

    # Add 1 for 1-indexing vs LSP's 0-indexing
    lines = [(range['start']['line'] + 1, range['end']['line'] + 1)]
    return _format(document, lines=lines)


def _format(document, lines=None):
    # Yapf doesn't work with CR line endings, so we replace them by '\n'
    # and restore them below.
    source = document.source
    eol_chars = get_eol_chars(source)
    if eol_chars == '\r':
        source = source.replace('\r', '\n')

    diff_txt, changed = FormatCode(
        source,
        lines=lines,
        filename=document.filename,
        print_diff=True,
        style_config=file_resources.GetDefaultStyleForDir(
            os.path.dirname(document.path)
        )
    )

    if not changed:
        return []

    patch_generator = whatthepatch.parse_patch(diff_txt)
    diff = next(patch_generator)
    patch_generator.close()

    # To keep things simple our text edits will be line based
    # and uncompacted
    textEdits = []
    # keep track of line number since additions
    # don't include the line number it's being added
    # to in diffs. lsp is 0-indexed so we'll start with -1
    prev_line_no = -1
    for change in diff.changes:
        if change.old and change.new:
            # no change
            # diffs are 1-indexed
            prev_line_no = change.old - 1
        elif change.new:
            # addition
            textEdits.append({
                'range': {
                    'start': {
                        'line': prev_line_no + 1,
                        'character': 0
                    },
                    'end': {
                        'line': prev_line_no + 1,
                        'character': 0
                    }
                },
                'newText': change.line + eol_chars
            })
        elif change.old:
            # remove
            lsp_line_no = change.old - 1
            textEdits.append({
                'range': {
                    'start': {
                        'line': lsp_line_no,
                        'character': 0
                    },
                    'end': {
                        # From LSP spec:
                        # If you want to specify a range that contains a line
                        # including the line ending character(s) then use an
                        # end position denoting the start of the next line.
                        'line': lsp_line_no + 1,
                        'character': 0
                    }
                },
                'newText': ''
            })
            prev_line_no = lsp_line_no

    return textEdits
