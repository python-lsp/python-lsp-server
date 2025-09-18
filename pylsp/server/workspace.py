from __future__ import annotations

import typing as typ
from pathlib import Path

from lsprotocol.types import WorkspaceFolder
from pygls import uris, workspace
from pygls.workspace.text_document import TextDocument

from pylsp.config.config import Config

if typ.TYPE_CHECKING:
    from pygls.server import LanguageServer


class Workspace(workspace.Workspace):
    """Custom Workspace class for pylsp."""

    def __init__(self, server: LanguageServer, *args, **kwargs):
        self._server = server
        super().__init__(*args, **kwargs)
        self._config = Config(
            self._root_uri,
            self._server.lsp.initialization_options,
            self._server.process_id,
            self._server.server_capabilities,
        )

    @property
    def config(self) -> Config:
        return self._config

    def get_document_folder(self, doc_uri: str) -> WorkspaceFolder | None:
        """Get the workspace folder for a given document URI.

        Finds the folder that is the longest prefix of the document URI.

        Args:
            doc_uri (str): The document URI.

        Returns:
            WorkspaceFolder | None: The workspace folder containing the document, or
            None if not found.
        """
        best_match_len = float("inf")
        best_match = None
        document_path = Path(uris.to_fs_path(doc_uri) or "")
        for folder_uri, folder in self._folders.items():
            folder_path = Path(uris.to_fs_path(folder_uri) or "")
            if (
                match_len := len(document_path.relative_to(folder_path).parts)
                < best_match_len
            ):
                best_match_len = match_len
                best_match = folder

        return best_match

    def _create_text_document(
        self,
        doc_uri: str,
        source: str | None = None,
        version: int | None = None,
        language_id: str | None = None,
    ) -> Document:
        return Document(
            self,
            doc_uri,
            source=source,
            version=version,
            language_id=language_id,
            sync_kind=self._sync_kind,
            position_codec=self._position_codec,
        )


class Document(TextDocument):
    def __init__(self, workspace: Workspace, *args, **kwargs):
        self._workspace = workspace
        super().__init__(*args, **kwargs)

    @property
    def workspace(self) -> Workspace:
        return self._workspace

    @property
    def workspace_folder(self) -> WorkspaceFolder | None:
        return self._workspace.get_document_folder(self.uri)
