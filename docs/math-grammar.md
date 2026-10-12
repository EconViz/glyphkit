# Supported math grammar

`parse_math()` is a bounded TeX-like adapter, not a TeX implementation. It keeps semantic source
ranges and never executes TeX, macros, packages, or external programs.

| Form | Example |
|---|---|
| Identifiers, numbers, operators | `U(x_1, x_2) = 2` |
| Groups and scripts | `x_{i+1}^2` |
| Fractions | `\\frac{a}{b}` |
| Roots | `\\sqrt{x}`, `\\sqrt[n]{x}` |
| Large operators and limits | `\\sum_{i}^{n}`, `\\prod`, `\\int`, `\\lim` |
| Delimiters | `\\left( x \\right)` |
| Accents | `\\hat{x}`, `\\bar{x}`, `\\vec{x}`, `\\overline{x}`, `\\underline{x}` |
| Greek names | `\\alpha`, `\\Gamma`, and the documented common names |
| Matrices | `\\begin{matrix}a & b \\\\ c & d\\end{matrix}` |

Unknown commands, malformed groups, and unsupported environments raise `MathSyntaxError`.
Defaults limit input to 100,000 code points, nesting to 256 levels, and matrix content to 10,000
cells; callers may set lower limits. Structured layout requires an explicitly selected font with
an OpenType `MATH` table.
