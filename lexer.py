"""
PA 2: The USILang Lexer.

tokenize() turns raw USILang source text into a flat, ordered list of
Token objects for PA 3's recursive-descent parser. It uses a single
compiled master regex with named groups and a position index -- not a
hand-rolled character-by-character state machine.
"""

import re
from dataclasses import dataclass
from typing import List


@dataclass
class Token:
    type: str
    lexeme: str
    line: int


class LexError(Exception):
    pass


# Reserved words: lexemes that match the IDENT pattern but must be
# relabeled after the fact. We never give `let` its own regex
# alternative ahead of IDENT -- that would be maximal-munch-fragile
# (see Part A). Instead IDENT matches wide, then we downgrade here.
KEYWORDS = {
    "let": "LET",
}


# One ordered list of (group name, sub-pattern). Order only matters
# where two alternatives could match at the same position; here every
# real token has a disjoint first character, so the only ordering that
# matters is keeping MISMATCH last as the catch-all trap state.
_TOKEN_SPEC = [
    ("NUMBER",   r"[0-9]+"),                    # USILang NUMBER = unsigned integer
    ("IDENT",    r"[A-Za-z_][A-Za-z0-9_]*"),    # matched wide, then keyword-checked
    ("PLUS",     r"\+"),
    ("MINUS",    r"-"),
    ("STAR",     r"\*"),
    ("SLASH",    r"/"),
    ("LPAREN",   r"\("),
    ("RPAREN",   r"\)"),
    ("ASSIGN",   r"="),
    ("SEMI",     r";"),
    ("COMMENT",  r"#[^\n]*"),                   # '#' to end of line, newline not consumed
    ("NEWLINE",  r"\n"),                        # consumed, never emitted; bumps line count
    ("SKIP",     r"[ \t\r]+"),                  # consumed, never emitted
    ("MISMATCH", r"."),                         # any other single char -> LexError
]

_MASTER_RE = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in _TOKEN_SPEC)
)


def tokenize(source: str) -> List[Token]:
    """
    Convert `source` into a list of Token objects, ending in an EOF
    token with an empty lexeme. Recognize NUMBER, IDENT, LET, PLUS,
    MINUS, STAR, SLASH, LPAREN, RPAREN, ASSIGN, SEMI. Discard
    whitespace and '#'-prefixed comments without emitting tokens for
    them. Track 1-indexed line numbers. Raise LexError (with the
    offending character and line) on unrecognized input.
    """
    tokens: List[Token] = []
    line = 1
    pos = 0
    end = len(source)

    while pos < end:
        m = _MASTER_RE.match(source, pos)
        # m can never be None: the MISMATCH group matches any single
        # character that nothing else claimed, and NEWLINE covers '\n'.
        kind = m.lastgroup
        lexeme = m.group()
        pos = m.end()

        if kind == "NEWLINE":
            line += 1
        elif kind == "SKIP" or kind == "COMMENT":
            continue
        elif kind == "MISMATCH":
            raise LexError(
                f"Unexpected character {lexeme!r} at line {line}"
            )
        elif kind == "IDENT" and lexeme in KEYWORDS:
            tokens.append(Token(KEYWORDS[lexeme], lexeme, line))
        else:
            tokens.append(Token(kind, lexeme, line))

    tokens.append(Token("EOF", "", line))
    return tokens


if __name__ == "__main__":
    import sys

    src = sys.stdin.read() if len(sys.argv) < 2 else sys.argv[1]
    for tok in tokenize(src):
        print(tok)
