# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

from collections.abc import Iterable
from importlib.resources import as_file, files
from pathlib import Path

import pytest
from rope.base.exceptions import BadIdentifierError

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
def examples_dir_path() -> Iterable[Path]:
    with as_file(files("test.data.implementations_examples")) as path:
        yield path


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
    cursor_pos = {"line": 14, "character": 8}

    # The implementation of 'Bird.fly'
    def_range = {
        "start": {"line": 21, "character": 8},
        "end": {"line": 21, "character": 11},
    }

    doc = workspace.get_document(doc_uri)
    assert [{"uri": doc_uri, "range": def_range}] == pylsp_implementations(
        config, workspace, doc, cursor_pos
    )


def test_implementations_skipping_one_class(config, workspace, doc_uri) -> None:
    # Over 'Animal.breathe'
    cursor_pos = {"line": 4, "character": 8}

    # The implementation of 'breathe', skipping intermediate classes
    def_range = {
        "start": {"line": 18, "character": 8},
        "end": {"line": 18, "character": 15},
    }

    doc = workspace.get_document(doc_uri)
    assert [{"uri": doc_uri, "range": def_range}] == pylsp_implementations(
        config, workspace, doc, cursor_pos
    )


@pytest.mark.xfail(
    reason="not implemented upstream (Rope)", strict=True, raises=BadIdentifierError
)
def test_property_implementations(config, workspace, doc_uri) -> None:
    # Over 'Animal.size'
    cursor_pos = {"line": 9, "character": 9}

    # The property implementation 'Bird.size'
    def_range = {
        "start": {"line": 25, "character": 8},
        "end": {"line": 25, "character": 12},
    }

    doc = workspace.get_document(doc_uri)
    assert [{"uri": doc_uri, "range": def_range}] == pylsp_implementations(
        config, workspace, doc, cursor_pos
    )


def test_implementations_not_a_method(config, workspace, doc_uri) -> None:
    # Over 'print(...)' call => Rope error because not a method.
    cursor_pos = {"line": 28, "character": 0}

    doc = workspace.get_document(doc_uri)

    # This exception is turned into an empty result set automatically in upper
    # layers, so we just check that it is raised to document this behavior:
    with pytest.raises(BadIdentifierError):
        pylsp_implementations(config, workspace, doc, cursor_pos)
