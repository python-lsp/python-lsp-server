from __future__ import annotations

import json
import logging
import typing as typ
from functools import partial

from lsprotocol import types as typlsp
from lsprotocol.types import (
    INITIALIZE,
    InitializeParams,
    InitializeResult,
    TraceValues,
)
from pygls import protocol
from pygls.capabilities import ServerCapabilitiesBuilder
from pygls.uris import from_fs_path

from pylsp import PYLSP, hookspecs
from pylsp.config.config import PluginManager
from pylsp.server.workspace import Workspace

logger = logging.getLogger(__name__)


class LangageServerProtocol(protocol.LanguageServerProtocol):
    """Custom features implementation for the Python Language Server."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pm = PluginManager(PYLSP)
        if logger.level <= logging.DEBUG:
            self._pm.trace.root.setwriter(logger.debug)
            self._pm.enable_tracing()
        self._pm.add_hookspecs(hookspecs)

    @property
    def plugin_manager(self) -> PluginManager:
        """Returns the plugin manager."""
        return self._pm

    @property
    def workspace(self) -> Workspace:
        if self._workspace is None:
            raise RuntimeError(
                "The workspace is not available - has the server been initialized?"
            )

        return typ.cast(Workspace, self._workspace)

    @protocol.lsp_method(INITIALIZE)
    def lsp_initialize(self, params: InitializeParams) -> InitializeResult:
        """Method that initializes language server.
        It will compute and return server capabilities based on
        registered features.
        """
        logger.info("Language server initialized %s", params)

        self._server.process_id = params.process_id
        self.initialization_options = params.initialization_options or {}

        text_document_sync_kind = self._server._text_document_sync_kind
        notebook_document_sync = self._server._notebook_document_sync

        # Initialize server capabilities
        self.client_capabilities = params.capabilities
        self.server_capabilities = ServerCapabilitiesBuilder(
            self.client_capabilities,
            set({**self.fm.features, **self.fm.builtin_features}.keys()),
            self.fm.feature_options,
            list(self.fm.commands.keys()),
            text_document_sync_kind,
            notebook_document_sync,
        ).build()
        logger.debug(
            "Server capabilities: %s",
            json.dumps(self.server_capabilities, default=self._serialize_message),
        )

        root_path = params.root_path
        root_uri = params.root_uri
        if root_path is not None and root_uri is None:
            root_uri = from_fs_path(root_path)

        # Initialize the workspace
        workspace_folders = params.workspace_folders or []
        self._workspace = Workspace(
            self._server,
            root_uri,
            text_document_sync_kind,
            workspace_folders,
            self.server_capabilities.position_encoding,
        )

        self.trace = TraceValues.Off

        return InitializeResult(
            capabilities=self.server_capabilities,
            server_info=self.server_info,
        )

    async def call_hook(
        self,
        hook_name: str,
        doc_uri: str | None = None,
        work_done_token: typlsp.ProgressToken | None = None,
        **kwargs,
    ):
        """Calls hook_name and returns a list of results from all registered handlers.

        Args:
            hook_name (str): The name of the hook to call.
            doc_uri (str | None): The document URI to pass to the hook.
            work_done_token (ProgressToken | None): The progress token to use for reporting progress.
            **kwargs: Additional keyword arguments to pass to the hook.
        """
        if doc_uri:
            doc = self.workspace.get_text_document(doc_uri)
        else:
            doc = None

        workspace_folder = (
            self.workspace.get_document_folder(doc_uri) if doc_uri else None
        )

        folder_uri = (
            workspace_folder.uri if workspace_folder else self.workspace._root_uri
        )

        hook_handlers_caller = self.plugin_manager.subset_hook_caller(
            hook_name, self.workspace.config.disabled_plugins
        )

        if work_done_token is not None:
            await self.progress.create_async(work_done_token)

        return await self._server.loop.run_in_executor(
            self._server.thread_pool_executor,
            partial(
                hook_handlers_caller,
                lsp=self,
                workspace=folder_uri,
                document=doc,
                **kwargs,
            ),
        )
