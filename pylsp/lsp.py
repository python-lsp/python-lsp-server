# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

"""Some Language Server Protocol constants

https://github.com/Microsoft/language-server-protocol/blob/master/protocol.md
"""


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


-1


class SemanticTokenKind:
    Namespace = 0
    # represents a generic type. acts as a fallback for types which
    # can't be mapped to a specific type like class or enum.
    Type = 1
    Class = 2
    Enum = 3
    Interface = 4
    Struct = 5
    TypeParameter = 6
    Parameter = 7
    Variable = 8
    Property = 9
    EnumMember = 10
    Event = 11
    Function = 12
    Method = 13
    Macro = 14
    Keyword = 15
    Modifier = 16
    Comment = 17
    String = 18
    Number = 19
    Regexp = 20
    Operator = 21
    Decorator = 22  # @since 3.17.0


class SemanticTokenModifierKind:
    Declaration = 0
    Definition = 1
    Readonly = 2
    Static = 3
    Deprecated = 4
    Abstract = 5
    Async = 6
    Modification = 7
    Documentation = 8
    DefaultLibrary = 9


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
