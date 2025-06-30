# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

"""Some Language Server Protocol constants

https://github.com/Microsoft/language-server-protocol/blob/master/protocol.md
"""

from enum import Enum
from typing import NamedTuple


class CompletionItemKind:
    Text = 1
    Method = 2
    Function = 3
    Constructor = 4
    Field = 5
    Variable = 6
    Class = 7
    Interface = 8
    Module = 9
    Property = 10
    Unit = 11
    Value = 12
    Enum = 13
    Keyword = 14
    Snippet = 15
    Color = 16
    File = 17
    Reference = 18
    Folder = 19
    EnumMember = 20
    Constant = 21
    Struct = 22
    Event = 23
    Operator = 24
    TypeParameter = 25


class DocumentHighlightKind:
    Text = 1
    Read = 2
    Write = 3


class DiagnosticSeverity:
    Error = 1
    Warning = 2
    Information = 3
    Hint = 4


class DiagnosticTag:
    Unnecessary = 1
    Deprecated = 2


class InsertTextFormat:
    PlainText = 1
    Snippet = 2


class MessageType:
    Error = 1
    Warning = 2
    Info = 3
    Log = 4


class SymbolKind:
    File = 1
    Module = 2
    Namespace = 3
    Package = 4
    Class = 5
    Method = 6
    Property = 7
    Field = 8
    Constructor = 9
    Enum = 10
    Interface = 11
    Function = 12
    Variable = 13
    Constant = 14
    String = 15
    Number = 16
    Boolean = 17
    Array = 18


class SemanticToken(NamedTuple):
    value: int
    name: str


class SemanticTokenType(Enum):
    Namespace = SemanticToken(0, "namespace")
    # represents a generic type. acts as a fallback for types which
    # can't be mapped to a specific type like class or enum.
    Type = SemanticToken(1, "type")
    Class = SemanticToken(2, "class")
    Enum = SemanticToken(3, "enum")
    Interface = SemanticToken(4, "interface")
    Struct = SemanticToken(5, "struct")
    TypeParameter = SemanticToken(6, "typeParameter")
    Parameter = SemanticToken(7, "parameter")
    Variable = SemanticToken(8, "variable")
    Property = SemanticToken(9, "property")
    EnumMember = SemanticToken(10, "enumMember")
    Event = SemanticToken(11, "event")
    Function = SemanticToken(12, "function")
    Method = SemanticToken(13, "method")
    Macro = SemanticToken(14, "macro")
    Keyword = SemanticToken(15, "keyword")
    Modifier = SemanticToken(16, "modifier")
    Comment = SemanticToken(17, "comment")
    String = SemanticToken(18, "string")
    Number = SemanticToken(19, "number")
    Regexp = SemanticToken(20, "regexp")
    Operator = SemanticToken(21, "operator")
    Decorator = SemanticToken(22, "decorator")  # @since 3.17.0


class SemanticTokenModifier(Enum):
    Declaration = SemanticToken(0, "declaration")
    Definition = SemanticToken(1, "definition")
    Readonly = SemanticToken(2, "readonly")
    Static = SemanticToken(3, "static")
    Deprecated = SemanticToken(4, "deprecated")
    Abstract = SemanticToken(5, "abstract")
    Async = SemanticToken(6, "async")
    Modification = SemanticToken(7, "modification")
    Documentation = SemanticToken(8, "documentation")
    DefaultLibrary = SemanticToken(9, "defaultLibrary")


class TextDocumentSyncKind:
    NONE = 0
    FULL = 1
    INCREMENTAL = 2


class NotebookCellKind:
    Markup = 1
    Code = 2


# https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#errorCodes
class ErrorCodes:
    ParseError = -32700
    InvalidRequest = -32600
    MethodNotFound = -32601
    InvalidParams = -32602
    InternalError = -32603
    jsonrpcReservedErrorRangeStart = -32099
    ServerNotInitialized = -32002
    UnknownErrorCode = -32001
    jsonrpcReservedErrorRangeEnd = -32000
    lspReservedErrorRangeStart = -32899
    ServerCancelled = -32802
    ContentModified = -32801
    RequestCancelled = -32800
    lspReservedErrorRangeEnd = -32800
