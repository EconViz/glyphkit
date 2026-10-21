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
    Space,
    Symbol,
)

GREEK = {
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "delta": "δ",
    "epsilon": "ε",
    "varepsilon": "ϵ",
    "zeta": "ζ",
    "eta": "η",
    "theta": "θ",
    "vartheta": "ϑ",
    "iota": "ι",
    "kappa": "κ",
    "lambda": "λ",
    "mu": "μ",
    "nu": "ν",
    "xi": "ξ",
    "pi": "π",
    "rho": "ρ",
    "varrho": "ϱ",
    "sigma": "σ",
    "varsigma": "ς",
    "tau": "τ",
    "upsilon": "υ",
    "phi": "φ",
    "varphi": "ϕ",
    "chi": "χ",
    "psi": "ψ",
    "omega": "ω",
    "Gamma": "Γ",
    "Delta": "Δ",
    "Theta": "Θ",
    "Lambda": "Λ",
    "Xi": "Ξ",
    "Pi": "Π",
    "Sigma": "Σ",
    "Upsilon": "Υ",
    "Phi": "Φ",
    "Psi": "Ψ",
    "Omega": "Ω",
}
# Large operators with limits above and below in display style.
OPERATORS = {
    "sum": "∑",
    "prod": "∏",
    "coprod": "∐",
    "bigcup": "⋃",
    "bigcap": "⋂",
    "bigoplus": "⨁",
    "bigotimes": "⨂",
    "lim": "lim",
    "max": "max",
    "min": "min",
    "sup": "sup",
    "inf": "inf",
    "limsup": "lim sup",
    "liminf": "lim inf",
}
# Integrals take their scripts at the side, even in display style.
INTEGRALS = {"int": "∫", "iint": "∬", "iiint": "∭", "oint": "∮"}
# Function names are set upright with a thin space after them.
FUNCTIONS = [
    "sin",
    "cos",
    "tan",
    "cot",
    "sec",
    "csc",
    "arcsin",
    "arccos",
    "arctan",
    "sinh",
    "cosh",
    "tanh",
    "coth",
    "ln",
    "log",
    "lg",
    "exp",
    "det",
    "gcd",
    "dim",
    "ker",
    "arg",
    "deg",
    "hom",
    "Pr",
]
BINARY = {
    "pm": "±",
    "mp": "∓",
    "times": "×",
    "div": "÷",
    "cdot": "⋅",
    "ast": "∗",
    "circ": "∘",
    "bullet": "∙",
    "cup": "∪",
    "cap": "∩",
    "setminus": "∖",
    "oplus": "⊕",
    "ominus": "⊖",
    "otimes": "⊗",
    "wedge": "∧",
    "vee": "∨",
}
RELATIONS = {
    "le": "≤",
    "leq": "≤",
    "ge": "≥",
    "geq": "≥",
    "ne": "≠",
    "neq": "≠",
    "approx": "≈",
    "equiv": "≡",
    "sim": "∼",
    "simeq": "≃",
    "cong": "≅",
    "propto": "∝",
    "ll": "≪",
    "gg": "≫",
    "in": "∈",
    "notin": "∉",
    "ni": "∋",
    "subset": "⊂",
    "supset": "⊃",
    "subseteq": "⊆",
    "supseteq": "⊇",
    "to": "→",
    "rightarrow": "→",
    "leftarrow": "←",
    "leftrightarrow": "↔",
    "Rightarrow": "⇒",
    "Leftarrow": "⇐",
    "Leftrightarrow": "⇔",
    "implies": "⟹",
    "iff": "⟺",
    "mapsto": "↦",
    "perp": "⊥",
    "parallel": "∥",
    "mid": "∣",
}
ORDINARY = {
    "infty": "∞",
    "partial": "∂",
    "nabla": "∇",
    "forall": "∀",
    "exists": "∃",
    "emptyset": "∅",
    "varnothing": "∅",
    "ell": "ℓ",
    "hbar": "ℏ",
    "Re": "ℜ",
    "Im": "ℑ",
    "aleph": "ℵ",
    "neg": "¬",
    "angle": "∠",
    "prime": "′",
    "ldots": "…",
    "cdots": "⋯",
    "vdots": "⋮",
    "ddots": "⋱",
    "dots": "…",
    "%": "%",
    "&": "&",
    "#": "#",
    "$": "$",
    "_": "_",
    "{": "{",
    "}": "}",
}
SPACES = {",": 3.0, ":": 4.0, ";": 5.0, "!": -3.0, " ": 6.0, "quad": 18.0, "qquad": 36.0}
UPRIGHT = {"mathrm", "text", "textrm", "operatorname", "mbox"}
ACCENTS = {"overline", "underline", "hat", "bar", "vec"}
RELATION_CHARACTERS = "=<>≤≥≠≈≡∼∈→←"
BINARY_CHARACTERS = "+−-×÷"
OPENING = "([⟨"
CLOSING = ")]⟩"
PUNCTUATION = ",;"


def _character_role(character: str) -> str:
    if character in RELATION_CHARACTERS:
        return "relation"
    if character in BINARY_CHARACTERS:
        return "binary"
    if character in OPENING:
        return "open"
    if character in CLOSING:
        return "close"
    if character in PUNCTUATION:
        return "punct"
    return "ordinary"


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

    def raw_group(self) -> str:
        """The text inside ``{...}`` after a command such as ``\\mathrm``, braces balanced."""
        self.skip_space()
        if self.position >= len(self.source) or self.source[self.position] != "{":
            raise self.error("missing command argument")
        depth = 0
        start = self.position + 1
        while self.position < len(self.source):
            character = self.source[self.position]
            self.position += 1
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return self.source[start : self.position - 1]
        raise self.error("unclosed group")

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
            return Symbol(character, SourceRange(start, self.position), _character_role(character))
        command = self.command()
        if command in SPACES:
            return Space(SPACES[command], SourceRange(start, self.position))
        if command in UPRIGHT:
            return Symbol(self.raw_group(), SourceRange(start, self.position), "upright")
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
        if command in INTEGRALS:
            return Symbol(INTEGRALS[command], SourceRange(start, self.position), "integral")
        if command in FUNCTIONS:
            return Symbol(command, SourceRange(start, self.position), "function")
        for table, role in ((BINARY, "binary"), (RELATIONS, "relation"), (ORDINARY, "ordinary")):
            if command in table:
                return Symbol(table[command], SourceRange(start, self.position), role)
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
