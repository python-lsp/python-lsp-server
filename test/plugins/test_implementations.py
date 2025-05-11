# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

import os

import pytest

from pylsp import uris
from pylsp.plugins.rope_implementation import pylsp_implementations
from pylsp.workspace import Document

DOC_URI = uris.from_fs_path(__file__)
DOC = """
from abc import ABC, abstractmethod

class Animal(ABC):
    @abstractmethod
    def breathe(self):
        ...

    @property
    @abstractmethod
    def size(self) -> str:
        ...

class WingedAnimal(Animal):
    @abstractmethod
    def fly(self, destination):
        ...

class Bird(WingedAnimal):
    def breathe(self):
        print("*inhales like a bird*")

    def fly(self, destination):
        print("*flies like a bird*")

    @property
    def size(self) -> str:
        return "bird-sized"

print("not a method at all")
"""


def test_implementations(config, workspace) -> None:
    # Over 'fly' in WingedAnimal.fly
    cursor_pos = {"line": 15, "character": 9}

    # The implementation of 'Bird.fly'
    def_range = {
        "start": {"line": 22, "character": 0},
        "end": {"line": 22, "character": 999},
    }

    workspace.put_document(DOC_URI, DOC)
    doc = workspace.get_document(DOC_URI)
    assert [{"uri": DOC_URI, "range": def_range}] == pylsp_implementations(
        config, workspace, doc, cursor_pos
    )


def test_implementations_skipping_one_class(config, workspace) -> None:
    # Over 'Animal.breathe'
    cursor_pos = {"line": 15, "character": 9}

    # The implementation of 'breathe', skipping intermediate classes
    def_range = {
        "start": {"line": 19, "character": 0},
        "end": {"line": 19, "character": 999},
    }

    doc = Document(DOC_URI, workspace, DOC)
    assert [{"uri": DOC_URI, "range": def_range}] == pylsp_implementations(
        config, workspace, doc, cursor_pos
    )


@pytest.mark.xfail(reason="not implemented upstream (Rope)", strict=True)
def test_property_implementations(config, workspace) -> None:
    # Over 'Animal.size'
    cursor_pos = {"line": 10, "character": 9}

    # The property implementation 'Bird.size'
    def_range = {
        "start": {"line": 26, "character": 0},
        "end": {"line": 26, "character": 999},
    }

    doc = Document(DOC_URI, workspace, DOC)
    assert [{"uri": DOC_URI, "range": def_range}] == pylsp_implementations(
        config, workspace, doc, cursor_pos
    )


def test_no_implementations_if_not_a_method(config, workspace) -> None:
    # Over 'print(...)' call
    cursor_pos = {"line": 26, "character": 0}

    doc = Document(DOC_URI, workspace, DOC)
    assert [] == pylsp_implementations(config, workspace, doc, cursor_pos)


def test_document_path_implementations(
    config, workspace, workspace_other_root_path, tmpdir
) -> None:
    # Create a dummy module out of the workspace's root_path and try to get
    # a implementation on it in another file placed next to it.
    module_content = """
class A:
    def f():
"""

    p = tmpdir.join("mymodule.py")
    p.write(module_content)

    # Content of doc to test implementation
    doc_content = """
from mymodule import A
class B(A):
    def f():
"""
    doc_path = str(tmpdir) + os.path.sep + "myfile.py"
    doc_uri = uris.from_fs_path(doc_path)
    doc = Document(doc_uri, workspace_other_root_path, doc_content)

    # The range where f is defined in mymodule.py
    def_range = {
        "start": {"line": 2, "character": 0},
        "end": {"line": 2, "character": 999},
    }

    # The position where foo is called in myfile.py
    cursor_pos = {"line": 3, "character": 9}

    # The uri for mymodule.py
    module_path = str(p)
    module_uri = uris.from_fs_path(module_path)

    assert [{"uri": module_uri, "range": def_range}] == pylsp_implementations(
        config, workspace, doc, cursor_pos
    )
