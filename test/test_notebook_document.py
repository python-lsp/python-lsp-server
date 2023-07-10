# Copyright 2021- Python Language Server Contributors.

import os
import time
from threading import Thread
from unittest.mock import patch, call

import pytest

from pylsp.python_lsp import PythonLSPServer
from pylsp.lsp import NotebookCellKind

CALL_TIMEOUT = 10


def wait_for_condition(condition, timeout=CALL_TIMEOUT):
    """Wait for a condition to be true, or timeout."""
    start_time = time.time()
    while not condition():
        time.sleep(0.1)
        if time.time() - start_time > timeout:
            raise TimeoutError("Timeout waiting for condition")


def start(obj):
    obj.start()


class ClientServerPair:
    """A class to setup a client/server pair"""

    def __init__(self):
        # Client to Server pipe
        csr, csw = os.pipe()
        # Server to client pipe
        scr, scw = os.pipe()

        self.server = PythonLSPServer(os.fdopen(csr, "rb"), os.fdopen(scw, "wb"))
        self.server_thread = Thread(target=start, args=[self.server])
        self.server_thread.start()

        self.client = PythonLSPServer(os.fdopen(scr, "rb"), os.fdopen(csw, "wb"))
        self.client_thread = Thread(target=start, args=[self.client])
        self.client_thread.start()


@pytest.fixture
def client_server_pair():
    """A fixture that sets up a client/server pair and shuts down the server"""
    client_server_pair_obj = ClientServerPair()

    yield (client_server_pair_obj.client, client_server_pair_obj.server)

    shutdown_response = client_server_pair_obj.client._endpoint.request("shutdown").result(
        timeout=CALL_TIMEOUT
    )
    assert shutdown_response is None
    client_server_pair_obj.client._endpoint.notify("exit")


def test_initialize(client_server_pair):  # pylint: disable=redefined-outer-name
    client, server = client_server_pair
    response = client._endpoint.request(
        "initialize",
        {
            "processId": 1234,
            "rootPath": os.path.dirname(__file__),
            "initializationOptions": {},
        },
    ).result(timeout=CALL_TIMEOUT)
    assert server.workspace is not None
    assert "capabilities" in response
    # TODO: assert that notebook capabilities are in response


def test_notebook_document__did_open(client_server_pair):  # pylint: disable=redefined-outer-name
    client, server = client_server_pair
    client._endpoint.request(
        "initialize",
        {
            "processId": 1234,
            "rootPath": os.path.dirname(__file__),
            "initializationOptions": {},
        },
    ).result(timeout=CALL_TIMEOUT)

    with patch.object(server._endpoint, "notify") as mock_notify:
        client._endpoint.notify(
            "notebookDocument/didOpen",
            {
                "notebookDocument": {
                    "uri": "notebook_uri",
                    "notebookType": "jupyter-notebook",
                    "cells": [
                        {
                            "kind": NotebookCellKind.Code,
                            "document": "cell_1_uri",
                        },
                        {
                            "kind": NotebookCellKind.Code,
                            "document": "cell_2_uri",
                        },
                    ],
                },
                "cellTextDocuments": [
                    {
                        "uri": "cell_1_uri",
                        "languageId": "python",
                        "text": "import sys",
                    },
                    {
                        "uri": "cell_2_uri",
                        "languageId": "python",
                        "text": "x = 1",
                    },
                ],
            },
        )
        wait_for_condition(lambda: mock_notify.call_count >= 2)
        expected_call_args = [
            call(
                "textDocument/publishDiagnostics",
                params={
                    "uri": "cell_1_uri",
                    "diagnostics": [
                        {
                            "source": "pyflakes",
                            "range": {
                                "start": {"line": 0, "character": 0},
                                "end": {"line": 0, "character": 11},
                            },
                            "message": "'sys' imported but unused",
                            "severity": 2,
                        }
                    ],
                },
            ),
            call(
                "textDocument/publishDiagnostics",
                params={
                    "uri": "cell_2_uri",
                    "diagnostics": [
                        {
                            "source": "pycodestyle",
                            "range": {
                                "start": {"line": 0, "character": 5},
                                "end": {"line": 0, "character": 5},
                            },
                            "message": "W292 no newline at end of file",
                            "code": "W292",
                            "severity": 2,
                        }
                    ],
                },
            ),
        ]
        mock_notify.assert_has_calls(expected_call_args)


def test_notebook_document__did_change(client_server_pair):  # pylint: disable=redefined-outer-name
    client, server = client_server_pair
    client._endpoint.request(
        "initialize",
        {
            "processId": 1234,
            "rootPath": os.path.dirname(__file__),
            "initializationOptions": {},
        },
    ).result(timeout=CALL_TIMEOUT)

    # Open notebook
    with patch.object(server._endpoint, "notify") as mock_notify:
        client._endpoint.notify(
            "notebookDocument/didOpen",
            {
                "notebookDocument": {
                    "uri": "notebook_uri",
                    "notebookType": "jupyter-notebook",
                    "cells": [
                        {
                            "kind": NotebookCellKind.Code,
                            "document": "cell_1_uri",
                        },
                        {
                            "kind": NotebookCellKind.Code,
                            "document": "cell_2_uri",
                        },
                    ],
                },
                "cellTextDocuments": [
                    {
                        "uri": "cell_1_uri",
                        "languageId": "python",
                        "text": "import sys",
                    },
                    {
                        "uri": "cell_2_uri",
                        "languageId": "python",
                        "text": "",
                    },
                ],
            },
        )
        wait_for_condition(lambda: mock_notify.call_count >= 2)
        assert len(server.workspace.documents) == 3
        for uri in ["cell_1_uri", "cell_2_uri", "notebook_uri"]:
            assert uri in server.workspace.documents
        assert len(server.workspace.get_document("notebook_uri").cells) == 2
        expected_call_args = [
            call(
                "textDocument/publishDiagnostics",
                params={
                    "uri": "cell_1_uri",
                    "diagnostics": [
                        {
                            "source": "pyflakes",
                            "range": {
                                "start": {"line": 0, "character": 0},
                                "end": {"line": 0, "character": 11},
                            },
                            "message": "'sys' imported but unused",
                            "severity": 2,
                        }
                    ],
                },
            ),
            call(
                "textDocument/publishDiagnostics",
                params={"uri": "cell_2_uri", "diagnostics": []},
            ),
        ]
        mock_notify.assert_has_calls(expected_call_args)

    # Remove second cell
    with patch.object(server._endpoint, "notify") as mock_notify:
        client._endpoint.notify(
            "notebookDocument/didChange",
            {
                "notebookDocument": {
                    "uri": "notebook_uri",
                },
                "change": {
                    "cells": {
                        "structure": {
                            "array": {
                                "start": 1,
                                "deleteCount": 1,
                            },
                            "didClose": [
                                {
                                    "uri": "cell_2_uri",
                                }
                            ],
                        },
                    }
                },
            },
        )
        wait_for_condition(lambda: mock_notify.call_count >= 1)
        assert len(server.workspace.documents) == 2
        assert "cell_2_uri" not in server.workspace.documents
        assert len(server.workspace.get_document("notebook_uri").cells) == 1
        expected_call_args = [
            call(
                "textDocument/publishDiagnostics",
                params={
                    "uri": "cell_1_uri",
                    "diagnostics": [
                        {
                            "source": "pyflakes",
                            "range": {
                                "start": {"line": 0, "character": 0},
                                "end": {"line": 0, "character": 10},
                            },
                            "message": "'sys' imported but unused",
                            "severity": 2,
                        }
                    ],
                },
            )
        ]
        mock_notify.assert_has_calls(expected_call_args)

    # Add second cell
    with patch.object(server._endpoint, "notify") as mock_notify:
        client._endpoint.notify(
            "notebookDocument/didChange",
            {
                "notebookDocument": {
                    "uri": "notebook_uri",
                },
                "change": {
                    "cells": {
                        "structure": {
                            "array": {
                                "start": 1,
                                "deleteCount": 0,
                                "cells": [
                                    {
                                        "kind": NotebookCellKind.Code,
                                        "document": "cell_3_uri",
                                    }
                                ],
                            },
                            "didOpen": [
                                {
                                    "uri": "cell_3_uri",
                                    "languageId": "python",
                                    "text": "x",
                                }
                            ],
                        },
                    }
                },
            },
        )
        wait_for_condition(lambda: mock_notify.call_count >= 2)
        assert len(server.workspace.documents) == 3
        assert "cell_3_uri" in server.workspace.documents
        assert len(server.workspace.get_document("notebook_uri").cells) == 2
        expected_call_args = [
            call(
                "textDocument/publishDiagnostics",
                params={
                    "uri": "cell_1_uri",
                    "diagnostics": [
                        {
                            "source": "pyflakes",
                            "range": {
                                "start": {"line": 0, "character": 0},
                                "end": {"line": 0, "character": 11},
                            },
                            "message": "'sys' imported but unused",
                            "severity": 2,
                        }
                    ],
                },
            ),
            call(
                "textDocument/publishDiagnostics",
                params={
                    "uri": "cell_3_uri",
                    "diagnostics": [
                        {
                            "source": "pyflakes",
                            "range": {
                                "start": {"line": 0, "character": 0},
                                "end": {"line": 0, "character": 1},
                            },
                            "message": "undefined name 'x'",
                            "severity": 1,
                        }
                    ],
                },
            ),
        ]
        mock_notify.assert_has_calls(expected_call_args)

    # Edit second cell
    with patch.object(server._endpoint, "notify") as mock_notify:
        client._endpoint.notify(
            "notebookDocument/didChange",
            {
                "notebookDocument": {
                    "uri": "notebook_uri",
                },
                "change": {
                    "cells": {
                        "textContent": [
                            {
                                "document": {
                                    "uri": "cell_3_uri",
                                },
                                "changes": [{"text": "sys.path"}],
                            }
                        ]
                    }
                },
            },
        )
        wait_for_condition(lambda: mock_notify.call_count >= 2)
        expected_call_args = [
            call(
                "textDocument/publishDiagnostics",
                params={"uri": "cell_1_uri", "diagnostics": []},
            ),
            call(
                "textDocument/publishDiagnostics",
                params={
                    "uri": "cell_3_uri",
                    "diagnostics": [
                        {
                            "source": "pycodestyle",
                            "range": {
                                "start": {"line": 0, "character": 8},
                                "end": {"line": 0, "character": 8},
                            },
                            "message": "W292 no newline at end of file",
                            "code": "W292",
                            "severity": 2,
                        }
                    ],
                },
            ),
        ]
        mock_notify.assert_has_calls(expected_call_args)


def test_notebook__did_close(client_server_pair):   # pylint: disable=redefined-outer-name
    client, server = client_server_pair
    client._endpoint.request(
        "initialize",
        {
            "processId": 1234,
            "rootPath": os.path.dirname(__file__),
            "initializationOptions": {},
        },
    ).result(timeout=CALL_TIMEOUT)

    # Open notebook
    with patch.object(server._endpoint, "notify") as mock_notify:
        client._endpoint.notify(
            "notebookDocument/didOpen",
            {
                "notebookDocument": {
                    "uri": "notebook_uri",
                    "notebookType": "jupyter-notebook",
                    "cells": [
                        {
                            "kind": NotebookCellKind.Code,
                            "document": "cell_1_uri",
                        },
                        {
                            "kind": NotebookCellKind.Code,
                            "document": "cell_2_uri",
                        },
                    ],
                },
                "cellTextDocuments": [
                    {
                        "uri": "cell_1_uri",
                        "languageId": "python",
                        "text": "import sys",
                    },
                    {
                        "uri": "cell_2_uri",
                        "languageId": "python",
                        "text": "",
                    },
                ],
            },
        )
        wait_for_condition(lambda: mock_notify.call_count >= 2)
        assert len(server.workspace.documents) == 3
        for uri in ["cell_1_uri", "cell_2_uri", "notebook_uri"]:
            assert uri in server.workspace.documents

    # Close notebook
    with patch.object(server._endpoint, "notify") as mock_notify:
        client._endpoint.notify(
            "notebookDocument/didClose",
            {
                "notebookDocument": {
                    "uri": "notebook_uri",
                },
                "cellTextDocuments": [
                    {
                        "uri": "cell_1_uri",
                    },
                    {
                        "uri": "cell_2_uri",
                    },
                ],
            },
        )
        wait_for_condition(lambda: mock_notify.call_count >= 2)
        assert len(server.workspace.documents) == 0
