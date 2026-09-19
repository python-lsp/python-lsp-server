# Copyright 2021- Python Language Server Contributors.

from pathlib import PureWindowsPath
from types import SimpleNamespace

import pytest

from pylsp import uris
from pylsp.plugins.definition import pylsp_definitions
from pylsp.plugins.references import pylsp_references
from pylsp.workspace import Document


@pytest.mark.parametrize("operation", ["definition", "references"])
@pytest.mark.parametrize(
    "document_uri,target_path,expected_uri",
    [
        (
            "file:///c:/project/main.py",
            r"\\server\share\target.py",
            "file://server/share/target.py",
        ),
        (
            "file://server/share/main.py",
            r"\\other\share\target.py",
            "file://other/share/target.py",
        ),
        (
            "file://server/share/main.py",
            r"C:\project\target.py",
            "file:///c:/project/target.py",
        ),
        (
            "file://server/share/main.py",
            r"\\server\share\target.py",
            "file://server/share/target.py",
        ),
    ],
)
def test_location_uri(
    config, workspace, monkeypatch, operation, document_uri, target_path, expected_uri
) -> None:
    monkeypatch.setattr(uris, "IS_WIN", True)
    name = SimpleNamespace(
        module_path=PureWindowsPath(target_path),
        line=1,
        column=0,
        name="target",
        is_definition=lambda: True,
        in_builtin_module=lambda: False,
    )
    script = SimpleNamespace(
        goto=lambda **kwargs: [name], get_references=lambda **kwargs: [name]
    )
    document = Document(document_uri, workspace, "target()")
    monkeypatch.setattr(document, "jedi_script", lambda **kwargs: script)
    position = {"line": 0, "character": 0}

    if operation == "definition":
        locations = pylsp_definitions(config, document, position)
    else:
        locations = pylsp_references(document, position, exclude_declaration=False)

    assert len(locations) == 1
    assert locations[0]["uri"] == expected_uri
