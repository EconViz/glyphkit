"""Bounded parser for GlyphKit documented mathematical syntax."""

# ruff: noqa: RUF001 -- mathematical symbols are intentional Unicode tokens.

from __future__ import annotations

from glyphkit.diagnostics import SourceRange
from glyphkit.errors import MathSyntaxError
from glyphkit.math.nodes import (
    Accent,
    Delimited,
    Fraction,
    Limits,
    MathNode,
    Matrix,
    Root,
    Script,
    Sequence,
    Symbol,
)

GREEK = {
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "delta": "δ",
    "epsilon": "ε",
    "theta": "θ",
    "lambda": "λ",
    "mu": "μ",
    "pi": "π",
    "rho": "ρ",
    "sigma": "σ",
    "phi": "φ",
    "omega": "ω",
    "Gamma": "Γ",
    "Delta": "Δ",
    "Theta": "Θ",
    "Lambda": "Λ",
    "Pi": "Π",
    "Sigma": "Σ",
    "Phi": "Φ",
    "Omega": "Ω",
}
OPERATORS = {"sum": "∑", "prod": "∏", "int": "∫", "lim": "lim"}
ACCENTS = {"overline", "underline", "hat", "bar", "vec"}


class _Parser:
    def __init__(self, source: str, *, max_depth: int, max_matrix_cells: int) -> None:
        self.source = source
        self.position = 0
        self.max_depth = max_depth
        self.max_matrix_cells = max_matrix_cells

    def error(self, message: str) -> MathSyntaxError:
        return MathSyntaxError(f"{message} at source offset {self.position}")

    def skip_space(self) -> None:
        while self.position < len(self.source) and self.source[self.position].isspace():
            self.position += 1

    def sequence(self, *, depth: int, stop: str | None = None) -> MathNode:
        if depth > self.max_depth:
            raise self.error("maximum math nesting depth exceeded")
        start = self.position
        children: list[MathNode] = []
        while self.position < len(self.source):
            self.skip_space()
            if stop is not None and self.source.startswith(stop, self.position):
                break
            if self.position >= len(self.source) or self.source[self.position] == "}":
                break
            node = self.atom(depth=depth)
            subscript = None
            superscript = None
            while self.position < len(self.source) and self.source[self.position] in "_^":
                marker = self.source[self.position]
                self.position += 1
                value = self.argument(depth=depth + 1)
                if marker == "_":
                    if subscript is not None:
                        raise self.error("duplicate subscript")
                    subscript = value
                else:
                    if superscript is not None:
                        raise self.error("duplicate superscript")
                    superscript = value
            if subscript is not None or superscript is not None:
                source_range = SourceRange(node.source_range.start, self.position)
                if isinstance(node, Symbol) and node.role == "large-operator":
                    node = Limits(node, source_range, subscript, superscript)
                else:
                    node = Script(node, source_range, subscript, superscript)
            children.append(node)
        end = self.position
        if len(children) == 1:
            return children[0]
        return Sequence(tuple(children), SourceRange(start, end))

    def argument(self, *, depth: int) -> MathNode:
        self.skip_space()
        if self.position >= len(self.source):
            raise self.error("missing command argument")
        if self.source[self.position] == "{":
            start = self.position
            self.position += 1
            value = self.sequence(depth=depth)
            if self.position >= len(self.source) or self.source[self.position] != "}":
                raise self.error("unclosed group")
            self.position += 1
            if isinstance(value, Sequence):
                return Sequence(value.children, SourceRange(start, self.position))
            return value
        return self.atom(depth=depth)

    def command(self) -> str:
        self.position += 1
        start = self.position
        while self.position < len(self.source) and self.source[self.position].isalpha():
            self.position += 1
        if start == self.position and self.position < len(self.source):
            self.position += 1
        return self.source[start : self.position]

    def atom(self, *, depth: int) -> MathNode:
        self.skip_space()
        start = self.position
        character = self.source[self.position]
        if character == "{":
            return self.argument(depth=depth + 1)
        if character != "\\":
            self.position += 1
            role = "operator" if character in "+−-=<>×÷" else "ordinary"
            return Symbol(character, SourceRange(start, self.position), role)
        command = self.command()
        if command == "frac":
            numerator = self.argument(depth=depth + 1)
            denominator = self.argument(depth=depth + 1)
            return Fraction(numerator, denominator, SourceRange(start, self.position))
        if command == "sqrt":
            index = None
            if self.position < len(self.source) and self.source[self.position] == "[":
                self.position += 1
                index = self.sequence(depth=depth + 1, stop="]")
                if self.position >= len(self.source) or self.source[self.position] != "]":
                    raise self.error("unclosed root index")
                self.position += 1
            radicand = self.argument(depth=depth + 1)
            return Root(radicand, SourceRange(start, self.position), index)
        if command in ACCENTS:
            body = self.argument(depth=depth + 1)
            return Accent(command, body, SourceRange(start, self.position))
        if command in GREEK:
            return Symbol(GREEK[command], SourceRange(start, self.position), "identifier")
        if command in OPERATORS:
            return Symbol(OPERATORS[command], SourceRange(start, self.position), "large-operator")
        if command == "left":
            if self.position >= len(self.source):
                raise self.error("missing left delimiter")
            left = self.source[self.position]
            self.position += 1
            body = self.sequence(depth=depth + 1, stop="\\right")
            if not self.source.startswith("\\right", self.position):
                raise self.error("missing right delimiter")
            self.position += len("\\right")
            if self.position >= len(self.source):
                raise self.error("missing right delimiter character")
            right = self.source[self.position]
            self.position += 1
            return Delimited(left, body, right, SourceRange(start, self.position))
        if command == "begin" and self.source.startswith("{matrix}", self.position):
            self.position += len("{matrix}")
            end_marker = "\\end{matrix}"
            end = self.source.find(end_marker, self.position)
            if end < 0:
                raise self.error("unclosed matrix")
            content = self.source[self.position : end]
            rows: list[tuple[MathNode, ...]] = []
            cell_count = 0
            for raw_row in content.split("\\\\"):
                row: list[MathNode] = []
                for raw_cell in raw_row.split("&"):
                    cell_count += 1
                    if cell_count > self.max_matrix_cells:
                        raise self.error("maximum matrix cell count exceeded")
                    row.append(
                        parse_math(
                            raw_cell,
                            max_depth=self.max_depth,
                            max_matrix_cells=self.max_matrix_cells,
                        )
                    )
                rows.append(tuple(row))
            self.position = end + len(end_marker)
            return Matrix(tuple(rows), SourceRange(start, self.position))
        raise self.error(f"unsupported command \\{command}")


def parse_math(
    source: str,
    *,
    max_length: int = 100_000,
    max_depth: int = 256,
    max_matrix_cells: int = 10_000,
) -> MathNode:
    if len(source) > max_length:
        raise MathSyntaxError("maximum math input length exceeded")
    parser = _Parser(source, max_depth=max_depth, max_matrix_cells=max_matrix_cells)
    result = parser.sequence(depth=0)
    parser.skip_space()
    if parser.position != len(source):
        raise parser.error("unexpected closing token")
    return result
