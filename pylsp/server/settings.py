from __future__ import annotations

import logging
from copy import deepcopy
import typing as typ

from lsprotocol import types as lsptyp
from pylsp.config.source import ConfigSource

if typ.TYPE_CHECKING:
    from pylsp.server.protocol import LangageServerProtocol


logger = logging.getLogger(__name__)


class ServerConfig:
    """Configuration manager with global and workspace-scoped settings.

    Exposes a subset of the legacy Config API used by plugins:
      - plugin_settings(name, document_path=None)
      - settings()
      - capabilities
    """

    def __init__(self, protocol: LangageServerProtocol, root_uri: str | None, init_options: dict[str, typ.Any]):
        self._protocol = protocol
        self._root_uri = root_uri
        # Global and per-folder runtime settings coming from client
        self._global_settings: dict[str, typ.Any] = init_options.get("pylsp", {})
        self._workspace_settings: dict[str, dict[str, typ.Any]] = {}
        self._current_folder: str | None = None
        # populated after pylsp_settings hooks
        self._config_sources: list[ConfigSource] = []

    # ---- views ----
    def with_folder(self, folder_uri: str | None) -> "ServerConfig":
        view = deepcopy(self)
        view._current_folder = folder_uri
        return view

    # ---- properties ----
    @property
    def capabilities(self) -> lsptyp.ClientCapabilities:
        return self._protocol.client_capabilities

    @property
    def disabled_plugins(self) -> set[str]:
        cfg = self.settings()
        plugins_cfg = cfg.get("plugins", {})
        disabled = set()
        for name, vals in plugins_cfg.items():
            enabled = vals.get("enabled")
            if enabled is False:
                disabled.add(name)
        return disabled

    # ---- public API used by plugins ----
    def settings(self) -> dict[str, typ.Any]:
        """Return merged settings (global overridden by workspace)."""
        if self._current_folder and self._current_folder in self._workspace_settings:
            merged = deepcopy(self._global_settings)
            merged.update(self._workspace_settings[self._current_folder])
            return merged
        return deepcopy(self._global_settings)

    def plugin_settings(self, plugin_name: str, document_path: str | None = None) -> dict[str, typ.Any]:
        """Return merged settings for a plugin.

        Merge order (lowest to highest precedence):
          1) User-level config files from plugin-provided ConfigSources
          2) Project-level config files (based on document_path)
          3) LSP settings from client: settings()['plugins'][plugin_name]
        """
        result: dict[str, typ.Any] = {}

        # Iterate collected ConfigSource instances
        for src in self._config_sources:
            try:
                # 1) user config
                _merge_into(result, src.user_config)
                # 2) project config (depends on document_path)
                if document_path:
                    proj_cfg = src.project_config(document_path)
                    _merge_into(result, proj_cfg)
            except Exception:
                logger.debug("Failed to read config via %s", src.__class__.__name__, exc_info=True)

        # 3) client-provided settings
        client_plugins = self.settings().get("plugins", {})
        client_plugin_cfg = client_plugins.get(plugin_name, {})
        _merge_into(result, client_plugin_cfg)
        return result

    # ---- updates from LSP events ----
    def update_workspace_settings(self, settings: dict[str, typ.Any] | None, folder_uri: str | None = None) -> None:
        if not settings:
            return
        # Clients usually send a top-level {"pylsp": {...}}
        payload = settings.get("pylsp", settings)
        if folder_uri:
            ws = self._workspace_settings.get(folder_uri, {})
            _merge_into(ws, payload)
            self._workspace_settings[folder_uri] = ws
        else:
            _merge_into(self._global_settings, payload)

    # ---- watchers ----
    def watcher_globs(self) -> list[str]:
        """Return glob patterns derived from collected ConfigSource PROJECT_CONFIGS."""
        globs: set[str] = set()
        for src in self._config_sources:
            try:
                for fname in getattr(src, "PROJECT_CONFIGS", []) or []:
                    globs.add(f"**/{fname}")
            except Exception:
                continue
        return sorted(globs)

    def set_config_sources(self, sources: list[ConfigSource]) -> None:
        self._config_sources = sources


def _merge_into(dst: dict[str, typ.Any], src: dict[str, typ.Any] | None) -> None:
    if not src:
        return
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _merge_into(dst[k], v)
        else:
            dst[k] = v
