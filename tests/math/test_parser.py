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


def test_symbol_commands_get_their_tex_class() -> None:
    from glyphkit.math import Sequence, Symbol

    def roles(source: str) -> list[tuple[str, str]]:
        node = parse_math(source)
        children = node.children if isinstance(node, Sequence) else (node,)
        return [(c.value, c.role) for c in children if isinstance(c, Symbol)]

    assert roles(r"a \le b") == [("a", "ordinary"), ("\u2264", "relation"), ("b", "ordinary")]
    assert roles(r"a \cdot b")[1] == ("\u22c5", "binary")
    assert roles("a+b=c,d")[1::2] == [("+", "binary"), ("=", "relation"), (",", "punct")]
    assert roles("(a)") == [("(", "open"), ("a", "ordinary"), (")", "close")]
    assert roles(r"\infty \partial") == [("\u221e", "ordinary"), ("\u2202", "ordinary")]
    assert roles(r"\sin")[0] == ("sin", "function")
    assert roles(r"\mathrm{max} \text{if }x")[0] == ("max", "upright")
    assert roles(r"\mathrm{max} \text{if }x")[1] == ("if ", "upright")
    assert roles(r"\zeta \Psi \varepsilon") == [
        ("\u03b6", "identifier"),
        ("\u03a8", "identifier"),
        ("\u03f5", "identifier"),
    ]


def test_spaces_and_integrals() -> None:
    from glyphkit.math import Script, Sequence, Space

    node = parse_math(r"a\,b\;c\!d\quad e")
    assert isinstance(node, Sequence)
    assert [c.mu for c in node.children if isinstance(c, Space)] == [3.0, 5.0, -3.0, 18.0]
    integral = parse_math(r"\int_0^1")
    assert isinstance(integral, Script)
    assert integral.base.role == "integral"


def test_unknown_commands_are_still_named_in_the_error() -> None:
    with pytest.raises(MathSyntaxError, match=r"unsupported command \\nonsense"):
        parse_math(r"\nonsense")
