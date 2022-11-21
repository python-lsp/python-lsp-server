# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

import os
from io import StringIO
from unittest.mock import MagicMock
import pytest
from pylsp_jsonrpc.endpoint import Endpoint

from pylsp import uris
from pylsp.config.config import Config
from pylsp.python_lsp import PythonLSPServer
from pylsp.workspace import Workspace, Document


DOC_URI = uris.from_fs_path(__file__)
DOC = """import sys

def main():
    print sys.stdin.read()
"""


@pytest.fixture
def pylsp(tmpdir):
    """ Return an initialized python LS """
    ls = PythonLSPServer(StringIO, StringIO)

    ls.m_initialize(
        processId=1,
        rootUri=uris.from_fs_path(str(tmpdir)),
        initializationOptions={}
    )

    return ls


@pytest.fixture
def pylsp_w_workspace_folders(tmpdir):
    """ Return an initialized python LS """
    ls = PythonLSPServer(StringIO, StringIO)

    folder1 = tmpdir.mkdir('folder1')
    folder2 = tmpdir.mkdir('folder2')

    ls.m_initialize(
        processId=1,
        rootUri=uris.from_fs_path(str(folder1)),
        initializationOptions={},
        workspaceFolders=[
            {
                'uri': uris.from_fs_path(str(folder1)),
                'name': 'folder1'
            },
            {
                'uri': uris.from_fs_path(str(folder2)),
                'name': 'folder2'
            }
        ]
    )

    workspace_folders = [folder1, folder2]
    return (ls, workspace_folders)


@pytest.fixture()
def consumer():
    return MagicMock()


@pytest.fixture()
def endpoint(consumer):  # pylint: disable=redefined-outer-name
    return Endpoint({}, consumer, id_generator=lambda: "id")


@pytest.fixture
def workspace(tmpdir, endpoint):  # pylint: disable=redefined-outer-name
    """Return a workspace."""
    ws = Workspace(uris.from_fs_path(str(tmpdir)), endpoint)
    ws._config = Config(ws.root_uri, {}, 0, {})
    yield ws
    ws.close()


@pytest.fixture
def workspace_other_root_path(tmpdir, endpoint):  # pylint: disable=redefined-outer-name
    """Return a workspace with a root_path other than tmpdir."""
    ws_path = str(tmpdir.mkdir('test123').mkdir('test456'))
    ws = Workspace(uris.from_fs_path(ws_path), endpoint)
    ws._config = Config(ws.root_uri, {}, 0, {})
    return ws


@pytest.fixture
def config(workspace):  # pylint: disable=redefined-outer-name
    """Return a config object."""
    cfg = Config(workspace.root_uri, {}, 0, {})
    cfg._plugin_settings = {'plugins': {'pylint': {'enabled': False, 'args': [], 'executable': None}}}
    return cfg


@pytest.fixture
def doc(workspace):  # pylint: disable=redefined-outer-name
    return Document(DOC_URI, workspace, DOC)


@pytest.fixture
def temp_workspace_factory(workspace):  # pylint: disable=redefined-outer-name
    '''
    Returns a function that creates a temporary workspace from the files dict.
    The dict is in the format {"file_name": "file_contents"}
    '''
    def fn(files):
        def create_file(name, content):
            fn = os.path.join(workspace.root_path, name)
            with open(fn, 'w', encoding='utf-8') as f:
                f.write(content)
            workspace.put_document(uris.from_fs_path(fn), content)

        for name, content in files.items():
            create_file(name, content)
        return workspace

    return fn
