"""Helpers for assertions about what a module *does*, not what it explains.

Several guards in this suite are source-level: they assert that no page
recomputes a risk class, that no literal year survives in the sidebar, that no
CartoDB tile shorthand is still wired up. Those are claims about executable
code. A comment recording the defect that was fixed, or a docstring naming the
tile host that had to be abandoned, cannot reintroduce the defect — and a guard
that cannot tell the two apart punishes the explanation.
"""

from __future__ import annotations

import ast
import io
import tokenize


def executable_source(source: str) -> str:
    """Return `source` with comments and docstrings blanked out.

    Ordinary string literals are kept, so a value hardcoded into displayed
    markup is still caught.

    Args:
        source: Python source text.

    Returns:
        The same text with comment and docstring lines emptied, preserving line
        numbering so failure output still points at the right place.
    """
    without_comments = tokenize.untokenize(
        tok
        for tok in tokenize.generate_tokens(io.StringIO(source).readline)
        if tok.type != tokenize.COMMENT
    )

    tree = ast.parse(without_comments)
    docstrings = {
        node.body[0].value
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }

    lines = without_comments.splitlines()
    for node in docstrings:
        for lineno in range(node.lineno, node.end_lineno + 1):
            lines[lineno - 1] = ""
    return "\n".join(lines)
