# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

import pytest

from pylsp import uris
from pylsp.plugins import signature
from pylsp.workspace import Document

DOC_URI = uris.from_fs_path(__file__)
DOC = """import sys

def main(param1, param2):
    \"\"\" Main docstring

    Args:
        param1 (str): Docs for param1
    \"\"\"
    raise Exception()

main(
"""

MULTI_LINE_DOC = """import sys

def main(param1=None,
            param2=None,
            param3=None,
            param4=None,
            param5=None,
            param6=None,
            param7=None,
            param8=None):
    \"\"\" Main docstring

    Args:
        param1 (str): Docs for param1
    \"\"\"
    raise Exception()

main(
"""


def test_no_signature(workspace) -> None:
    # Over blank line
    sig_position = {"line": 9, "character": 0}
    doc = Document(DOC_URI, workspace, DOC)

    sigs = signature.pylsp_signature_help(doc._config, doc, sig_position)["signatures"]
    assert not sigs


def test_signature(workspace) -> None:
    # Over '( ' in main(
    sig_position = {"line": 10, "character": 5}
    doc = Document(DOC_URI, workspace, DOC)

    sig_info = signature.pylsp_signature_help(doc._config, doc, sig_position)

    sigs = sig_info["signatures"]
    assert len(sigs) == 1
    assert sigs[0]["label"] == "main(param1, param2)"
    assert sigs[0]["parameters"][0]["label"] == "param1"
    assert sigs[0]["parameters"][0]["documentation"] == {
        "kind": "markdown",
        "value": "Docs for param1",
    }

    assert sig_info["activeParameter"] == 0


def test_multi_line_signature(workspace) -> None:
    # Over '( ' in main(
    sig_position = {"line": 17, "character": 5}
    doc = Document(DOC_URI, workspace, MULTI_LINE_DOC)

    sig_info = signature.pylsp_signature_help(doc._config, doc, sig_position)

    sigs = sig_info["signatures"]
    assert len(sigs) == 1
    assert sigs[0]["label"] == (
        "main(param1=None, param2=None, param3=None, param4=None, "
        "param5=None, param6=None, param7=None, param8=None)"
    )
    assert sigs[0]["parameters"][0]["label"] == "param1"
    assert sigs[0]["parameters"][0]["documentation"] == {
        "kind": "markdown",
        "value": "Docs for param1",
    }

    assert sig_info["activeParameter"] == 0


@pytest.mark.parametrize(
    "regex,doc",
    [
        (signature.SPHINX, "    :param test: parameter docstring"),
        (signature.EPYDOC, "    @param test: parameter docstring"),
        (signature.GOOGLE, "    test (str): parameter docstring"),
    ],
)
def test_docstring_params(regex, doc) -> None:
    m = regex.match(doc)
    assert m.group("param") == "test"
    assert m.group("doc") == "parameter docstring"


def test_signature_without_docstring(
    workspace_with_signature_docstring_disabled,
) -> None:
    # Over '( ' in main(
    sig_position = {"line": 10, "character": 5}
    doc = Document(DOC_URI, workspace_with_signature_docstring_disabled, DOC)

    sig_info = signature.pylsp_signature_help(doc._config, doc, sig_position)

    sigs = sig_info["signatures"]
    assert len(sigs) == 1
    assert sigs[0]["documentation"] == {"kind": "markdown", "value": ""}


CALLABLE_CLASS_DOC = """class MyCallable:
    \"\"\"Docstring for MyCallable\"\"\"
    def __call__(self, a, b=1):
        \"\"\"Call docstring\"\"\"
        pass

c = MyCallable()
c(
"""


def test_callable_instance_signature(workspace) -> None:
    # Over '( ' in c(
    sig_position = {"line": 8, "character": 2}
    doc = Document(DOC_URI, workspace, CALLABLE_CLASS_DOC)

    sig_info = signature.pylsp_signature_help(doc._config, doc, sig_position)

    sigs = sig_info["signatures"]
    assert len(sigs) == 1
    # Parameter labels must be substrings of the signature label per LSP 3.17
    assert sigs[0]["label"] == "MyCallable(a, b=1)"
    param_labels = [p["label"] for p in sigs[0]["parameters"]]
    assert param_labels == ["a", "b"]
    assert all(label in sigs[0]["label"] for label in param_labels)


def test_signature_fallback_when_label_missing_params(workspace, monkeypatch) -> None:
    # Test fallback when s.to_string() does not contain all parameter names
    sig_position = {"line": 10, "character": 5}
    doc = Document(DOC_URI, workspace, DOC)

    orig_jedi_script = doc.jedi_script

    class MockScript:
        def get_signatures(self, **kwargs):
            signatures = orig_jedi_script().get_signatures(**kwargs)
            if not signatures:
                return signatures
            s = signatures[0]
            # Mock to_string to return a label missing the parameters (like ufunc())
            monkeypatch.setattr(s, "to_string", lambda: "mock_func()")
            return [s]

    monkeypatch.setattr(doc, "jedi_script", lambda: MockScript())

    sig_info = signature.pylsp_signature_help(doc._config, doc, sig_position)
    sigs = sig_info["signatures"]
    assert len(sigs) == 1
    # Fallback should ensure parameter labels are substrings of signature label
    assert sigs[0]["label"] == "main(param1, param2)"
    param_labels = [p["label"] for p in sigs[0]["parameters"]]
    assert param_labels == ["param1", "param2"]
    assert all(label in sigs[0]["label"] for label in param_labels)
