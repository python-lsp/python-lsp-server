from typing import TypedDict, Optional, Union, List, NewType
from .lsp import DiagnosticSeverity, DiagnosticTag

"""
Types derived from the LSP protocol
See: https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/
"""

URI = NewType('URI', str)
DocumentUri = NewType('DocumentUri', str)

NotebookCell = TypedDict('NotebookCell', {
    'kind': str,
    'document': DocumentUri,
    'metadata': Optional[dict],
    'executionSummary': Optional[dict],
})

NotebookDocument = TypedDict('NotebookDocument', {
    'uri': str,
    'notebookType': str,
    'version': int,
    'metadata': Optional[dict],
    'cells': List[NotebookCell],
})

CodeDescription = TypedDict('CodeDescription', {
    'href': URI,
})

Position = TypedDict('Position', {
    'line': int,
    'character': int,
})

Range = TypedDict('Range', {
    'start': Position,
    'end': Position,
})

Location = TypedDict('Location', {
    'uri': URI,
    'range': Range,
})

DiagnosticRelatedInformation = TypedDict('DiagnosticRelatedInformation', {
    'location': dict,
    'message': str,
})

Diagnostic = TypedDict('Diagnostic', {
    'range': dict,
    'severity': Optional[DiagnosticSeverity],
    'code': Optional[Union[int, str]],
    'codeDescription': Optional[CodeDescription],
    'source': Optional[str],
    'message': str,
    'tags': Optional[List[DiagnosticTag]],
    'relatedInformation': Optional[List[DiagnosticRelatedInformation]],
    'data': Optional[dict],
})

