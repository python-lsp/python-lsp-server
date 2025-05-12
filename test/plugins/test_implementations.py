# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

from pathlib import Path

import pytest

import test
from pylsp import uris
from pylsp.config.config import Config
from pylsp.plugins.rope_implementation import pylsp_implementations
from pylsp.workspace import Workspace


# We use a real file because the part of Rope that this feature uses
# (`rope.findit.find_implementations`) *always* loads files from the
# filesystem, in contrast to e.g. `code_assist` which takes a `source` argument
# that can be more easily faked.
# An alternative to using real files would be `unittest.mock.patch`, but that
# ends up being more trouble than it's worth...
@pytest.fixture
def examples_dir_path() -> Path:
    # In Python 3.12+, this should be obtained using `importlib.resources`,
    # but as we need to support older versions, we do it the hacky way:
    return Path(test.__file__).parent / "data/implementations_examples"


@pytest.fixture
def doc_uri(examples_dir_path: Path) -> str:
    return uris.from_fs_path(str(examples_dir_path / "example.py"))


# Similarly to the above, we need our workspace to point to the actual location
# on the filesystem containing the example modules, so we override the fixture:
@pytest.fixture
def workspace(examples_dir_path: Path, endpoint) -> None:
    ws = Workspace(uris.from_fs_path(str(examples_dir_path)), endpoint)
    ws._config = Config(ws.root_uri, {}, 0, {})
    yield ws
    ws.close()


def test_implementations(config, workspace, doc_uri) -> None:
    # Over 'fly' in WingedAnimal.fly
    cursor_pos = {"line": 15, "character": 8}

    # The implementation of 'Bird.fly'
    def_range = {
        "start": {"line": 22, "character": 8},
        "end": {"line": 22, "character": 11},
    }

    doc = workspace.get_document(doc_uri)
    assert [{"uri": doc_uri, "range": def_range}] == pylsp_implementations(
        config, workspace, doc, cursor_pos
    )


def test_implementations_skipping_one_class(config, workspace, doc_uri) -> None:
    # Over 'Animal.breathe'
    cursor_pos = {"line": 5, "character": 8}

    # The implementation of 'breathe', skipping intermediate classes
    def_range = {
        "start": {"line": 19, "character": 8},
        "end": {"line": 19, "character": 15},
    }

    doc = workspace.get_document(doc_uri)
    assert [{"uri": doc_uri, "range": def_range}] == pylsp_implementations(
        config, workspace, doc, cursor_pos
    )


@pytest.mark.xfail(
    reason="not implemented upstream (Rope)", strict=True, raises=AssertionError
)
def test_property_implementations(config, workspace, doc_uri) -> None:
    # Over 'Animal.size'
    cursor_pos = {"line": 10, "character": 9}

    # The property implementation 'Bird.size'
    def_range = {
        "start": {"line": 26, "character": 8},
        "end": {"line": 26, "character": 12},
    }

    doc = workspace.get_document(doc_uri)
    assert [{"uri": doc_uri, "range": def_range}] == pylsp_implementations(
        config, workspace, doc, cursor_pos
    )


def test_implementations_not_a_method(config, workspace, doc_uri) -> None:
    # Over 'print(...)' call
    cursor_pos = {"line": 29, "character": 0}

    doc = workspace.get_document(doc_uri)

    # Rope produces an error because we're not over a method, which we then
    # turn into an empty result list:
    assert [] == pylsp_implementations(config, workspace, doc, cursor_pos)
