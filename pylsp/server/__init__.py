from __future__ import annotations

import asyncio
import logging
import os
import typing as typ

from lsprotocol import types as lsptyp
from pygls import server

from pylsp import PYLSP, __version__
from pylsp._utils import flatten, is_process_alive
from pylsp.server.protocol import LangageServerProtocol

if typ.TYPE_CHECKING:
    from pylsp.server.workspace import Workspace

logger = logging.getLogger(__name__)

MAX_WORKERS = 64
PARENT_PROCESS_WATCH_INTERVAL = 10  # 10 s

CONFIG_FILES = ("pycodestyle.cfg", "setup.cfg", "tox.ini", ".flake8")


class LanguageServer(server.LanguageServer):
    """Python Language Server."""

    lsp: LangageServerProtocol

    @property
    def workspace(self) -> Workspace:
        """Returns in-memory workspace."""
        return self.lsp.workspace

    def check_parent_process(self):
        """Check if the parent process is still alive."""

        async def watch_parent_process():
            ppid = os.getppid()
            while True:
                if self._stop_event is not None and self._stop_event.is_set():
                    break
                if not is_process_alive(ppid):
                    self.shutdown()
                    break
                await asyncio.sleep(PARENT_PROCESS_WATCH_INTERVAL)

        asyncio.create_task(watch_parent_process())


LSP_SERVER = LanguageServer(
    name=PYLSP,
    version=__version__,
    max_workers=MAX_WORKERS,
    protocol_cls=LangageServerProtocol,
    text_document_sync_kind=lsptyp.TextDocumentSyncKind.Incremental,
    notebook_document_sync=lsptyp.NotebookDocumentSyncOptions(
        notebook_selector=[
            lsptyp.NotebookDocumentSyncOptionsNotebookSelectorType2(
                cells=[
                    lsptyp.NotebookDocumentSyncOptionsNotebookSelectorType2CellsType(
                        language="python"
                    ),
                ],
            ),
        ],
    ),
)


@LSP_SERVER.feature(lsptyp.INITIALIZE)
async def initialize(ls: LanguageServer, params: lsptyp.InitializeParams):
    """Handle the initialization request."""
    # Call the initialization hook
    await ls.lsp.call_hook("pylsp_initialize")


@LSP_SERVER.feature(lsptyp.INITIALIZED)
async def initialized(ls: LanguageServer, params: lsptyp.InitializedParams):
    """Handle the initialized notification."""
    # Call the initialized hook
    await ls.lsp.call_hook("pylsp_initialized")


@LSP_SERVER.feature(lsptyp.WORKSPACE_DID_CHANGE_CONFIGURATION)
async def workspace_did_change_configuration(
    ls: LanguageServer, params: lsptyp.WorkspaceConfigurationParams
):
    """Handle the workspace did change configuration notification."""
    for config_item in params.items:
        ls.workspace.config.update({config_item.scope_uri: config_item.section})
    # TODO: Check configuration update is valid and supports this type of update
    await ls.lsp.call_hook("pylsp_workspace_configuration_changed")


@LSP_SERVER.feature(lsptyp.WORKSPACE_DID_CHANGE_WATCHED_FILES)
def workspace_did_change_watched_files(
    ls: LanguageServer, params: lsptyp.DidChangeWatchedFilesParams
):
    """Handle the workspace did change watched files notification."""
    for change in params.changes:
        if change.uri.endswith(CONFIG_FILES):
            ls.workspace.config.settings.cache_clear()
            break

    # TODO: check if necessary to link files not handled by textDocument/Open


@LSP_SERVER.feature(lsptyp.WORKSPACE_EXECUTE_COMMAND)
async def workspace_execute_command(
    ls: LanguageServer, params: lsptyp.ExecuteCommandParams
):
    """Handle the workspace execute command request."""
    # Call the execute command hook
    await ls.lsp.call_hook(
        "pylsp_execute_command",
        command=params.command,
        arguments=params.arguments,
        work_done_token=params.work_done_token,
    )


@LSP_SERVER.feature(lsptyp.NOTEBOOK_DOCUMENT_DID_OPEN)
async def notebook_document_did_open(
    ls: LanguageServer, params: lsptyp.DidOpenNotebookDocumentParams
):
    """Handle the notebook document did open notification."""
    await ls.lsp.lint_notebook_document(params.notebook_document.uri)


@LSP_SERVER.feature(lsptyp.NOTEBOOK_DOCUMENT_DID_CHANGE)
async def notebook_document_did_change(
    ls: LanguageServer, params: lsptyp.DidChangeNotebookDocumentParams
):
    """Handle the notebook document did change notification."""
    await ls.lsp.lint_notebook_document(params.notebook_document.uri)


@LSP_SERVER.feature(lsptyp.NOTEBOOK_DOCUMENT_DID_SAVE)
async def notebook_document_did_save(
    ls: LanguageServer, params: lsptyp.DidSaveNotebookDocumentParams
):
    """Handle the notebook document did save notification."""
    await ls.lsp.lint_notebook_document(params.notebook_document.uri)
    await ls.workspace.save(params.notebook_document.uri)


@LSP_SERVER.feature(lsptyp.NOTEBOOK_DOCUMENT_DID_CLOSE)
async def notebook_document_did_close(
    ls: LanguageServer, params: lsptyp.DidCloseNotebookDocumentParams
):
    """Handle the notebook document did close notification."""
    await ls.lsp.cancel_tasks(params.notebook_document.uri)


@LSP_SERVER.feature(lsptyp.TEXT_DOCUMENT_DID_OPEN)
async def text_document_did_open(
    ls: LanguageServer, params: lsptyp.DidOpenTextDocumentParams
):
    """Handle the text document did open notification."""
    await ls.lsp.lint_text_document(params.text_document.uri)


@LSP_SERVER.feature(lsptyp.TEXT_DOCUMENT_DID_CHANGE)
async def text_document_did_change(
    ls: LanguageServer, params: lsptyp.DidChangeTextDocumentParams
):
    """Handle the text document did change notification."""
    await ls.lsp.lint_text_document(params.text_document.uri)


@LSP_SERVER.feature(lsptyp.TEXT_DOCUMENT_DID_SAVE)
async def text_document_did_save(
    ls: LanguageServer, params: lsptyp.DidSaveTextDocumentParams
):
    """Handle the text document did save notification."""
    await ls.lsp.lint_text_document(params.text_document.uri)
    await ls.workspace.save(params.text_document.uri)


@LSP_SERVER.feature(lsptyp.TEXT_DOCUMENT_DID_CLOSE)
async def text_document_did_close(
    ls: LanguageServer, params: lsptyp.DidCloseTextDocumentParams
):
    """Handle the text document did close notification."""
    await ls.lsp.cancel_tasks(params.text_document.uri)


@LSP_SERVER.feature(lsptyp.TEXT_DOCUMENT_CODE_ACTION)
async def text_document_code_action(
    ls: LanguageServer, params: lsptyp.CodeActionParams
) -> typ.List[lsptyp.Command | lsptyp.CodeAction] | None:
    """Handle the text document code action request."""
    actions: typ.List[lsptyp.Command | lsptyp.CodeAction] | None = flatten(
        await ls.lsp.call_hook(
            "pylsp_code_action",
            params.text_document.uri,
            range=params.range,
            context=params.context,
            work_done_token=params.work_done_token,
        )
    )
    return actions


@LSP_SERVER.feature(lsptyp.TEXT_DOCUMENT_CODE_LENS)
async def text_document_code_lens(
    ls: LanguageServer, params: lsptyp.CodeLensParams
) -> typ.List[lsptyp.CodeLens] | None:
    """Handle the text document code lens request."""
    lenses: typ.List[lsptyp.CodeLens] | None = flatten(
        await ls.lsp.call_hook(
            "pylsp_code_lens",
            params.text_document.uri,
            work_done_token=params.work_done_token,
        )
    )
    return lenses


@LSP_SERVER.feature(lsptyp.TEXT_DOCUMENT_COMPLETION)
async def text_document_completion(
    ls: LanguageServer, params: lsptyp.CompletionParams
) -> typ.List[lsptyp.CompletionItem] | None:
    """Handle the text document completion request."""
    completions: typ.List[lsptyp.CompletionItem] | None = flatten(
        await ls.lsp.call_hook(
            "pylsp_completion",
            params.text_document.uri,
            position=params.position,
            context=params.context,
            work_done_token=params.work_done_token,
        )
    )
    return completions


@LSP_SERVER.feature(lsptyp.COMPLETION_ITEM_RESOLVE)
async def completion_item_resolve(
    ls: LanguageServer, params: lsptyp.CompletionItem
) -> lsptyp.CompletionItem | None:
    """Handle the completion item resolve request."""
    item: lsptyp.CompletionItem | None = await ls.lsp.call_hook(
        "pylsp_completion_item_resolve",
        (params.data or {}).get("doc_uri"),
        completion_item=params,
    )
    return item


@LSP_SERVER.feature(lsptyp.TEXT_DOCUMENT_DEFINITION)
async def text_document_definition(
    ls: LanguageServer, params: lsptyp.DefinitionParams
) -> lsptyp.Location | None:
    """Handle the text document definition request."""
    location: lsptyp.Location | None = await ls.lsp.call_hook(
        "pylsp_definitions",
        params.text_document.uri,
        position=params.position,
        work_done_token=params.work_done_token,
    )
    return location


@LSP_SERVER.feature(lsptyp.TEXT_DOCUMENT_TYPE_DEFINITION)
async def text_document_type_definition(
    ls: LanguageServer, params: lsptyp.TypeDefinitionParams
) -> lsptyp.Location | None:
    """Handle the text document type definition request."""
    location: lsptyp.Location | None = await ls.lsp.call_hook(
        "pylsp_type_definition",
        params.text_document.uri,
        position=params.position,
        work_done_token=params.work_done_token,
    )
    return location


@LSP_SERVER.feature(lsptyp.TEXT_DOCUMENT_DOCUMENT_HIGHLIGHT)
async def text_document_document_highlight(
    ls: LanguageServer, params: lsptyp.DocumentHighlightParams
) -> typ.List[lsptyp.DocumentHighlight] | None:
    """Handle the text document document highlight request."""
    highlights: typ.List[lsptyp.DocumentHighlight] | None = flatten(
        await ls.lsp.call_hook(
            "pylsp_document_highlight",
            params.text_document.uri,
            position=params.position,
            work_done_token=params.work_done_token,
        )
    )
    return highlights


@LSP_SERVER.feature(lsptyp.TEXT_DOCUMENT_HOVER)
async def text_document_hover(
    ls: LanguageServer, params: lsptyp.HoverParams
) -> lsptyp.Hover | None:
    """Handle the text document hover request."""
    hover: lsptyp.Hover = await ls.lsp.call_hook(
        "pylsp_hover",
        params.text_document.uri,
        position=params.position,
        work_done_token=params.work_done_token,
    )
    return hover


@LSP_SERVER.feature(lsptyp.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
async def text_document_document_symbol(
    ls: LanguageServer, params: lsptyp.DocumentSymbolParams
) -> typ.List[lsptyp.DocumentSymbol] | None:
    """Handle the text document document symbol request."""
    symbols: typ.List[lsptyp.DocumentSymbol] | None = flatten(
        await ls.lsp.call_hook(
            "pylsp_document_symbols",
            params.text_document.uri,
            work_done_token=params.work_done_token,
        )
    )
    return symbols


@LSP_SERVER.feature(lsptyp.TEXT_DOCUMENT_FORMATTING)
async def text_document_formatting(
    ls: LanguageServer, params: lsptyp.DocumentFormattingParams
) -> typ.List[lsptyp.TextEdit] | None:
    """Handle the text document formatting request."""
    edits: typ.List[lsptyp.TextEdit] | None = flatten(
        await ls.lsp.call_hook(
            "pylsp_format_document",
            params.text_document.uri,
            options=params.options,
        )
    )
    return edits


@LSP_SERVER.feature(lsptyp.TEXT_DOCUMENT_RANGE_FORMATTING)
async def text_document_range_formatting(
    ls: LanguageServer, params: lsptyp.DocumentRangeFormattingParams
) -> typ.List[lsptyp.TextEdit] | None:
    """Handle the text document range formatting request."""
    edits: typ.List[lsptyp.TextEdit] | None = flatten(
        await ls.lsp.call_hook(
            "pylsp_format_range",
            params.text_document.uri,
            range=params.range,
            options=params.options,
        )
    )
    return edits


@LSP_SERVER.feature(lsptyp.TEXT_DOCUMENT_FOLDING_RANGE)
async def text_document_folding_range(
    ls: LanguageServer, params: lsptyp.FoldingRangeParams
) -> typ.List[lsptyp.FoldingRange] | None:
    """Handle the text document folding range request."""
    ranges: typ.List[lsptyp.FoldingRange] | None = flatten(
        await ls.lsp.call_hook(
            "pylsp_folding_range",
            params.text_document.uri,
            work_done_token=params.work_done_token,
        )
    )
    return ranges


@LSP_SERVER.feature(lsptyp.TEXT_DOCUMENT_REFERENCES)
async def text_document_references(
    ls: LanguageServer, params: lsptyp.ReferenceParams
) -> typ.List[lsptyp.Location] | None:
    """Handle the text document references request."""
    locations: typ.List[lsptyp.Location] | None = flatten(
        await ls.lsp.call_hook(
            "pylsp_references",
            params.text_document.uri,
            position=params.position,
            context=params.context,
        )
    )
    return locations


@LSP_SERVER.feature(lsptyp.TEXT_DOCUMENT_SIGNATURE_HELP)
async def text_document_signature_help(
    ls: LanguageServer, params: lsptyp.SignatureHelpParams
) -> lsptyp.SignatureHelp | None:
    """Handle the text document signature help request."""
    signature_help: lsptyp.SignatureHelp | None = await ls.lsp.call_hook(
        "pylsp_signature_help",
        params.text_document.uri,
        position=params.position,
        work_done_token=params.work_done_token,
    )
    return signature_help
