# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.
import logging
import os
from typing import Any, Dict, Tuple

from rope.base.project import Project
from rope.base.resources import Resource
from rope.contrib.findit import Location, find_implementations

from pylsp import hookimpl, uris

log = logging.getLogger(__name__)


@hookimpl
def pylsp_settings():
    # Default to enabled (no reason not to)
    return {"plugins": {"rope_implementation": {"enabled": True}}}


@hookimpl
def pylsp_implementations(config, workspace, document, position):
    offset = document.offset_at_position(position)
    rope_config = config.settings(document_path=document.path).get("rope", {})
    rope_project = workspace._rope_project_builder(rope_config)
    rope_resource = document._rope_resource(rope_config)

    try:
        impls = find_implementations(rope_project, rope_resource, offset)
    except Exception as e:
         log.debug("Failed to run Rope implementations finder: %s", e)
         return []

    return [
        {
            "uri": uris.uri_with(
                document.uri,
                path=os.path.join(workspace.root_path, impl.resource.path),
            ),
            "range": _rope_location_to_range(impl, rope_project),
        }
        for impl in impls
    ]


def _rope_location_to_range(
    location: Location, rope_project: Project
) -> Dict[str, Any]:
    # NOTE: This assumes the result is confined to a single line, which should
    # always be the case here because Python doesn't allow splitting up
    # identifiers across more than one line.
    start_column, end_column = _rope_region_to_columns(
        location.region, location.lineno, location.resource, rope_project
    )
    return {
        "start": {"line": location.lineno - 1, "character": start_column},
        "end": {"line": location.lineno - 1, "character": end_column},
    }


def _rope_region_to_columns(
    offsets: Tuple[int, int], line: int, rope_resource: Resource, rope_project: Project
) -> Tuple[int, int]:
    """
    Convert pair of offsets from start of file to columns within line.

    Assumes both offsets reside within the same line and will return nonsense
    for the end offset if this isn't the case.
    """
    line_start_offset = rope_project.get_pymodule(rope_resource).lines.get_line_start(
        line
    )
    return offsets[0] - line_start_offset, offsets[1] - line_start_offset
