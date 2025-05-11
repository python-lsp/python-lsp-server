# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.
import logging
import os

from rope.contrib.findit import find_implementations

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

    impls = find_implementations(rope_project, rope_resource, offset)

    return [
        {
            "uri": uris.uri_with(
                document.uri,
                path=os.path.join(workspace.root_path, impl.resource.path),
            ),
            "range": {
                # TODO: `impl.region` seems to be from the start of the file
                # and offsets from the start of the line difficult to obtain,
                # so we just return the whole line for now:
                "start": {"line": impl.lineno - 1, "character": 0},
                "end": {"line": impl.lineno - 1, "character": 999},
            },
        }
        for impl in impls
    ]
