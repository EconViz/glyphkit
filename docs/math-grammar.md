# Supported math grammar

`parse_math()` is a bounded TeX-like adapter, not a TeX implementation. It keeps semantic source
ranges and never executes TeX, macros, packages, or external programs.

| Form | Example |
|---|---|
| Identifiers, numbers | `U(x_1, x_2) = 2` |
| Groups and scripts | `x_{i+1}^2` |
| Fractions | `\\frac{a}{b}` |
| Roots | `\\sqrt{x}`, `\\sqrt[n]{x}` |
| Large operators with limits | `\\sum_{i}^{n}`, `\\prod`, `\\bigcup`, `\\lim`, `\\max`, `\\min`, `\\sup`, `\\inf` |
| Integrals (scripts at the side) | `\\int_0^1`, `\\iint`, `\\iiint`, `\\oint` |
| Functions, set upright | `\\sin`, `\\cos`, `\\tan`, `\\ln`, `\\log`, `\\exp`, `\\det`, `\\Pr`, and similar |
| Upright text | `\\mathrm{TR}`, `\\text{if }x`, `\\operatorname{rank}` |
| Binary operators | `+`, `-`, `\\times`, `\\cdot`, `\\pm`, `\\cup`, `\\cap`, `\\setminus` |
| Relations | `=`, `<`, `>`, `\\le`, `\\ge`, `\\ne`, `\\approx`, `\\equiv`, `\\in`, `\\subset`, `\\to`, `\\Rightarrow` |
| Other symbols | `\\infty`, `\\partial`, `\\nabla`, `\\forall`, `\\exists`, `\\ell`, `\\ldots`, `\\cdots` |
| Spaces | `\\,` (3 mu), `\\:` (4), `\\;` (5), `\\!` (-3), `\\quad`, `\\qquad` |
| Delimiters | `\\left( x \\right)` |
| Accents | `\\hat{x}`, `\\bar{x}`, `\\vec{x}`, `\\overline{x}`, `\\underline{x}` |
| Greek letters | the whole alphabet, `\\alpha` to `\\omega` and `\\Gamma` to `\\Omega`, with `\\varepsilon`, `\\vartheta`, `\\varphi`, `\\varrho`, `\\varsigma` |
| Matrices | `\\begin{matrix}a & b \\\\ c & d\\end{matrix}` |

## How a formula is set

Layout follows TeX's rules (Appendix G) with the constants of the font's `MATH` table:

- **Styles.** An expression starts in display style (`MathStyle.level`). A fraction's numerator and
  denominator are set at full size in display style and at script size in text style; scripts use
  `ScriptPercentScaleDown` and `ScriptScriptPercentScaleDown` of the whole expression's size.
- **Fractions** keep the font's shift-up and shift-down and the minimum gaps to the rule.
- **Scripts** keep the minimum gaps between a subscript and a superscript and above the baseline.
- **Limits.** In display style a large operator is enlarged (`DisplayOperatorMinHeight`), centred on
  the math axis, and its limits clear it by the font's minimum gaps; in text style they are scripts.
- **Spacing.** Atoms are classified (ordinary, large operator, binary, relation, opening, closing,
  punctuation, inner) and spaced by TeX's table, in thin, medium and thick spaces of 3, 4 and 5
  mu (1/18 em) outside script styles. A binary operator with no left operand, such as the minus in
  `(-x)`, is ordinary. A hyphen-minus that is a binary operator is drawn as U+2212 when the font
  has it.
- **Stretching.** Radical signs and delimiters are the plain glyph enlarged to the height of their
  content, not the font's size variants or glyph assemblies, so large ones have heavier strokes.

Roles on `Symbol` carry the class: `ordinary`, `identifier`, `binary`, `relation`, `open`, `close`,
`punct`, `large-operator`, `integral`, `function` and `upright`. The earlier role `operator` is
still read, as a relation or a binary operator by its character.

Unknown commands, malformed groups, and unsupported environments raise `MathSyntaxError`.
Defaults limit input to 100,000 code points, nesting to 256 levels, and matrix content to 10,000
cells; callers may set lower limits. Structured layout requires an explicitly selected font with
an OpenType `MATH` table.
