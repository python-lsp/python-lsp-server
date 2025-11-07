# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence

import pluggy
from pluggy import HookImpl

log = logging.getLogger(__name__)


class PluginManager(pluggy.PluginManager):
    def __init__(self, project_name: str):
        super().__init__(project_name)

    def _hookexec(
        self,
        hook_name: str,
        methods: Sequence[HookImpl],
        kwargs: Mapping[str, object],
        firstresult: bool,
    ):
        try:
            return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
        except Exception as e:
            log.warning(f"Failed to load hook {hook_name}: {e}", exc_info=True)
            return []

