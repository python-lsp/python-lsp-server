from __future__ import annotations

import os
import typing as typ
from pathlib import Path

from collections.abc import Generator
from typing import Callable, Optional

import jedi
from jedi.api import environment as jedi_environment
from lsprotocol import types as lsptyp
from lsprotocol.types import WorkspaceFolder
from pygls import uris, workspace
from pygls.workspace.text_document import TextDocument

from pylsp import _utils

if typ.TYPE_CHECKING:
    from pygls.server import LanguageServer
    from pylsp.server.settings import ServerConfig


# Default auto-import modules for Jedi
DEFAULT_AUTO_IMPORT_MODULES = ["numpy"]


class Workspace(workspace.Workspace):
    """Custom Workspace class for pylsp."""

    def __init__(self, server: LanguageServer, *args, **kwargs):
        self._server = server
        super().__init__(*args, **kwargs)
        self._config = None
        # Cache jedi environments per configured path
        self._environments: dict[str, typ.Any] = {}

    def get_document_folder(self, doc_uri: str) -> WorkspaceFolder | None:
        """Get the workspace folder for a given document URI.

        Finds the folder that is the longest prefix of the document URI.

        Args:
            doc_uri (str): The document URI.

        Returns:
            WorkspaceFolder | None: The workspace folder containing the document, or
            None if not found.
        """
        best_match_len = -1
        best_match = None
        document_path = Path(uris.to_fs_path(doc_uri) or "")
        for folder_uri, folder in self._folders.items():
            folder_path = Path(uris.to_fs_path(folder_uri) or "")
            try:
                document_path.relative_to(folder_path)
            except Exception:
                continue
            # prefer the longest matching folder
            match_len = len(str(folder_path))
            if match_len > best_match_len:
                best_match_len = match_len
                best_match = folder

        return best_match

    @property
    def config(self) -> ServerConfig | None:
        return self._config

    def attach_config(self, config: ServerConfig):
        self._config = config

    def source_roots(self, document_path: str) -> list[str]:
        """Return source roots for the given document.

        Searches for project files (setup.py, pyproject.toml) upwards and
        returns their directories, falling back to the workspace root.
        """
        files = _utils.find_parents(
            self.root_path, document_path, ["setup.py", "pyproject.toml"]
        ) or []
        roots = list({str(Path(f).parent) for f in files})
        return roots or [self.root_path]

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
        # Extra data used by some plugins during resolve steps
        self.shared_data: dict[str, typ.Any] = {}

    @property
    def workspace(self) -> Workspace:
        return self._workspace

    @property
    def workspace_folder(self) -> WorkspaceFolder | None:
        return self._workspace.get_document_folder(self.uri)

    @property
    def dot_path(self) -> str:
        return _utils.path_to_dot_name(self.path)

    # ---- Jedi helpers ----

    def jedi_names(
        self, all_scopes: bool = False, definitions: bool = True, references: bool = False
    ):
        script = self.jedi_script()
        return script.get_names(
            all_scopes=all_scopes, definitions=definitions, references=references
        )

    def jedi_script(
        self, use_document_path: bool = False
    ) -> jedi.Script:
        extra_paths: list[str] = []
        environment_path: str | None = None
        env_vars: dict[str, str] | None = None
        prioritize_extra_paths = False

        # Read Jedi-related settings
        cfg = self._workspace.config
        if cfg:
            jedi_settings = cfg.plugin_settings("jedi", document_path=self.path)
            jedi.settings.auto_import_modules = jedi_settings.get(
                "auto_import_modules", DEFAULT_AUTO_IMPORT_MODULES
            )
            environment_path = jedi_settings.get("environment")
            if environment_path and os.name != "nt":
                environment_path = os.path.expanduser(environment_path)
            extra_paths = jedi_settings.get("extra_paths") or []
            env_vars = jedi_settings.get("env_vars")
            prioritize_extra_paths = jedi_settings.get("prioritize_extra_paths", False)

        # Ensure Jedi starts without PYTHONPATH collisions
        if env_vars is None:
            env_vars = os.environ.copy()
        env_vars.pop("PYTHONPATH", None)

        environment = self.get_enviroment(environment_path, env_vars=env_vars)

        # Build sys_path: project roots + environment + configured extra paths
        sys_path = []  # type: list[str]
        sys_path.extend(self._workspace.source_roots(self.path))
        sys_path.extend(environment.get_sys_path())
        if use_document_path:
            sys_path.append(os.path.normpath(os.path.dirname(self.path)))
        if prioritize_extra_paths:
            sys_path = list(extra_paths) + sys_path
        else:
            sys_path = sys_path + list(extra_paths)

        # Determine project path
        project_path = self._workspace.root_path

        kwargs: dict[str, typ.Any] = {
            "code": self.source,
            "path": self.path,
            "environment": environment if environment_path else None,
            "project": jedi.Project(path=project_path, sys_path=sys_path),
        }

        # Position is passed to API calls (infer/complete), not Script ctor, so ignored here
        return jedi.Script(**kwargs)

    def get_enviroment(
        self, environment_path: str | None = None, env_vars: dict[str, str] | None = None
    ):
        """Return a cached Jedi environment or create a new one.

        Note: keep method name for backward compatibility (typo preserved).
        """
        if environment_path is None:
            return jedi_environment.get_cached_default_environment()
        if environment_path in self._workspace._environments:
            return self._workspace._environments[environment_path]
        env = jedi_environment.create_environment(
            path=environment_path, safe=False, env_vars=env_vars
        )
        self._workspace._environments[environment_path] = env
        return env
