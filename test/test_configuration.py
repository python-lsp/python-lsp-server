# Copyright 2021- Python Language Server Contributors.

import os
from unittest.mock import patch

from test.fixtures import CALL_TIMEOUT_IN_SECONDS
from test.test_notebook_document import wait_for_condition

import pytest

from pylsp import IS_WIN


INITIALIZATION_OPTIONS = {
    "pylsp": {
        "plugins": {
            "flake8": {"enabled": True},
            "pycodestyle": {"enabled": False},
            "pyflakes": {"enabled": False},
        },
    }
}


@pytest.mark.skipif(IS_WIN, reason="Flaky on Windows")
def test_set_flake8_using_init_opts(client_server_pair):
    client, server = client_server_pair
    client._endpoint.request(
        "initialize",
        {
            "processId": 1234,
            "rootPath": os.path.dirname(__file__),
            "initializationOptions": INITIALIZATION_OPTIONS,
        },
    ).result(timeout=CALL_TIMEOUT_IN_SECONDS)
    for key, value in INITIALIZATION_OPTIONS["pylsp"]["plugins"].items():
        assert server.workspace._config.settings().get("plugins").get(key).get(
            "enabled"
        ) == value.get("enabled")


@pytest.mark.skipif(IS_WIN, reason="Flaky on Windows")
def test_set_flake8_using_workspace_did_change_configuration(client_server_pair):
    client, server = client_server_pair
    client._endpoint.request(
        "initialize",
        {
            "processId": 1234,
            "rootPath": os.path.dirname(__file__),
        },
    ).result(timeout=CALL_TIMEOUT_IN_SECONDS)
    assert (
        server.workspace._config.settings().get("plugins").get("flake8").get("enabled")
        is False
    )

    with patch.object(server, "_hook") as mock_hook:
        client._endpoint.notify(
            "workspace/didChangeConfiguration",
            {"settings": INITIALIZATION_OPTIONS},
        )
        wait_for_condition(lambda: mock_hook.call_count >= 1)

        for key, value in INITIALIZATION_OPTIONS["pylsp"]["plugins"].items():
            assert server.workspace._config.settings().get("plugins").get(key).get(
                "enabled"
            ) == value.get("enabled")
