# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

import os

from pylsp import uris
from pylsp.plugins.hover import pylsp_hover
from pylsp.workspace import Document

DOC_URI = uris.from_fs_path(__file__)
DOC = """
from random import randint
from typing import overload

class A:
    \"\"\"Docstring for class A\"\"\"

    b = 42
    \"\"\"Docstring for the class property A.b\"\"\"

    def foo(self):
        \"\"\"Docstring for A.foo\"\"\"
        pass

if randint(0, 1) == 0:
    int_or_string_value = 10
else:
    int_or_string_value = "10"

@overload
def overload_function(s: int) -> int:
    ...

@overload
def overload_function(s: str) -> str:
    ...

def overload_function(s):
    \"\"\"Docstring of overload function\"\"\"
    pass

int_value = 10
string_value = "foo"
instance_of_a = A()
copy_of_class_a = A
copy_of_property_b = A.b
int_or_string_value
overload_function

"""

NUMPY_DOC = """

import numpy as np
np.sin

"""


def _hover_result_in_doc(workspace, position):
    doc = Document(DOC_URI, workspace, DOC)
    return pylsp_hover(
        doc._config, doc, {"line": position[0], "character": position[1]}
    )["contents"]["value"]


def test_hover_over_nothing(workspace):
    # Over blank line
    assert "" == _hover_result_in_doc(workspace, (3, 0))


def test_hover_on_keyword(workspace):
    # Over "class" in "class A:"
    res = _hover_result_in_doc(workspace, (4, 1))
    assert "Class definitions" in res


def test_hover_on_variables(workspace):
    # Over "int_value" in "int_value = 10"
    res = _hover_result_in_doc(workspace, (31, 2))
    assert "int" in res  # type

    # Over "string_value" in "string_value = "foo""
    res = _hover_result_in_doc(workspace, (32, 2))
    assert "string" in res  # type


def test_hover_on_class(workspace):
    # Over "A" in "class A:"
    res = _hover_result_in_doc(workspace, (4, 7))
    assert "A()" in res  # signature
    assert "Docstring for class A" in res  # docstring

    # Over "A" in "instance_of_a = A()"
    res = _hover_result_in_doc(workspace, (33, 17))
    assert "A()" in res  # signature
    assert "Docstring for class A" in res  # docstring

    # Over "copy_of_class_a" in "copy_of_class_a = A" - needs infer
    res = _hover_result_in_doc(workspace, (34, 4))
    assert "A()" in res  # signature
    assert "Docstring for class A" in res  # docstring


def test_hover_on_property(workspace):
    # Over "b" in "b = 42"
    res = _hover_result_in_doc(workspace, (7, 5))
    assert "int" in res  # type
    assert "Docstring for the class property A.b" in res  # docstring

    # Over "b" in "A.b"
    res = _hover_result_in_doc(workspace, (35, 24))
    assert "int" in res  # type
    assert "Docstring for the class property A.b" in res  # docstring


def test_hover_on_method(workspace):
    # Over "foo" in "def foo(self):"
    res = _hover_result_in_doc(workspace, (10, 10))
    assert "foo(self)" in res  # signature
    assert "Docstring for A.foo" in res  # docstring


def test_hover_multiple_definitions(workspace):
    # Over "int_or_string_value"
    res = _hover_result_in_doc(workspace, (36, 5))
    assert "```python\nUnion[int, str]\n```" == res.strip()  # only type

    # Over "overload_function"
    res = _hover_result_in_doc(workspace, (37, 5))
    assert (
        "overload_function(s: int) -> int\noverload_function(s: str) -> str" in res
    )  # signature
    assert "Docstring of overload function" in res  # docstring


def test_numpy_hover(workspace):
    # Over the blank line
    no_hov_position = {"line": 1, "character": 0}
    # Over 'numpy' in import numpy as np
    numpy_hov_position_1 = {"line": 2, "character": 8}
    # Over 'np' in import numpy as np
    numpy_hov_position_2 = {"line": 2, "character": 17}
    # Over 'np' in np.sin
    numpy_hov_position_3 = {"line": 3, "character": 1}
    # Over 'sin' in np.sin
    numpy_sin_hov_position = {"line": 3, "character": 4}

    doc = Document(DOC_URI, workspace, NUMPY_DOC)

    contents = ""
    assert (
        contents in pylsp_hover(doc._config, doc, no_hov_position)["contents"]["value"]
    )

    contents = "NumPy\n=====\n\nProvides\n"
    assert (
        contents
        in pylsp_hover(doc._config, doc, numpy_hov_position_1)["contents"]["value"]
    )

    contents = "NumPy\n=====\n\nProvides\n"
    assert (
        contents
        in pylsp_hover(doc._config, doc, numpy_hov_position_2)["contents"]["value"]
    )

    contents = "NumPy\n=====\n\nProvides\n"
    assert (
        contents
        in pylsp_hover(doc._config, doc, numpy_hov_position_3)["contents"]["value"]
    )

    # https://github.com/davidhalter/jedi/issues/1746
    import numpy as np

    if np.lib.NumpyVersion(np.__version__) < "1.20.0":
        contents = "Trigonometric sine, element-wise.\n\n"
        assert (
            contents
            in pylsp_hover(doc._config, doc, numpy_sin_hov_position)["contents"][
                "value"
            ]
        )


def test_document_path_hover(workspace_other_root_path, tmpdir):
    # Create a dummy module out of the workspace's root_path and try to get
    # a definition on it in another file placed next to it.
    module_content = '''
def foo():
    """A docstring for foo."""
    pass
'''

    p = tmpdir.join("mymodule.py")
    p.write(module_content)

    # Content of doc to test definition
    doc_content = """from mymodule import foo
foo"""
    doc_path = str(tmpdir) + os.path.sep + "myfile.py"
    doc_uri = uris.from_fs_path(doc_path)
    doc = Document(doc_uri, workspace_other_root_path, doc_content)

    cursor_pos = {"line": 1, "character": 3}
    contents = pylsp_hover(doc._config, doc, cursor_pos)["contents"]

    assert "A docstring for foo." in contents["value"]
