from __future__ import annotations

import typing as typ
from pathlib import Path

from collections.abc import Generator
from typing import Callable, Optional

from lsprotocol import types as lsptyp
from lsprotocol.types import WorkspaceFolder
from pygls import uris, workspace
from pygls.workspace.text_document import TextDocument

if typ.TYPE_CHECKING:
    from pygls.server import LanguageServer
    from pylsp.server.settings import ServerConfig


class Workspace(workspace.Workspace):
    """Custom Workspace class for pylsp."""

    def __init__(self, server: LanguageServer, *args, **kwargs):
        self._server = server
        super().__init__(*args, **kwargs)
        self._config = None

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

    async def save(self, doc_uri: str) -> None:
        """Save the document to disk.

        Args:
            doc_uri (str): The document URI.
        """
        document = self.get_text_document(doc_uri)
        if document is None:
            return

        path = uris.to_fs_path(doc_uri)
        if path is None:
            return

        with open(path, "w", encoding="utf-8") as f:
            f.write(document.source)

    # ---- pylsp plugin compatibility helpers ----

    @property
    def config(self) -> ServerConfig:
        return self._config

    @property
    def root_uri(self) -> str | None:
        return self._root_uri

    def attach_config(self, config: ServerConfig) -> None:
        self._config = config

    def report_progress(
        self,
        title: str,
        message: Optional[str] = None,
        percentage: Optional[int] = None,
        skip_token_initialization: bool = False,
    ) -> Generator[Callable[[str, Optional[int]], None], None, None]:
        """Context manager for progress reporting compatible with plugins."""
        token = f"pylsp:{title}"
        if not skip_token_initialization:
            try:
                self._server.window_work_done_progress_create(  # type: ignore[attr-defined]
                    lsptyp.WorkDoneProgressCreateParams(token=token)
                )
            except Exception:
                # Best-effort; some clients may not support it synchronously
                pass

        begin = lsptyp.WorkDoneProgressBegin(title=title)
        if message is not None:
            begin.message = message
        if percentage is not None:
            begin.percentage = percentage
        self._server.progress(token, begin)  # type: ignore[attr-defined]

        def _progress(msg: str, pct: Optional[int] = None) -> None:
            rep = lsptyp.WorkDoneProgressReport()
            if msg:
                rep.message = msg
            if pct is not None:
                rep.percentage = pct
            self._server.progress(token, rep)  # type: ignore[attr-defined]

        try:
            yield _progress
        finally:
            self._server.progress(token, lsptyp.WorkDoneProgressEnd())  # type: ignore[attr-defined]



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
