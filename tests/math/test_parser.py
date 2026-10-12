import pytest

from glyphkit import MathSyntaxError
from glyphkit.math import Accent, Fraction, Matrix, Root, Script, Sequence, parse_math


def test_parses_economic_formula_into_semantic_nodes() -> None:
    expression = parse_math(r"U(x_1,x_2)=\frac{x_1^\alpha}{x_2}")
    assert isinstance(expression, Sequence)
    assert any(isinstance(node, Fraction) for node in expression.children)
    assert any(isinstance(node, Script) for node in expression.children)


def test_parses_root_accent_and_matrix() -> None:
    assert isinstance(parse_math(r"\sqrt[n]{x}"), Root)
    assert isinstance(parse_math(r"\hat{x}"), Accent)
    assert isinstance(parse_math(r"\begin{matrix}a&b\\c&d\end{matrix}"), Matrix)


@pytest.mark.parametrize("source", [r"\unknown{x}", r"\frac{x}", "{x"])
def test_rejects_unsupported_or_malformed_input(source: str) -> None:
    with pytest.raises(MathSyntaxError):
        parse_math(source)


def test_enforces_configurable_input_bound() -> None:
    with pytest.raises(MathSyntaxError, match="length"):
        parse_math("abcdef", max_length=5)
