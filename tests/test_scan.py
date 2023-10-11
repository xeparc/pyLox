from collections import Counter

import context
from src.scan import (
    PREFIXES,
    SYMBOLS,
    KEYWORDS,
    TokenKind,
    Token,
    match_comment,
    match_symbol,
    match_string,
    match_exponent,
    match_number,
    match_identifier,
    MatchResult
)
from src.loxerr import (
    ScanError,
    ScanErrorMessages
)


def test_prefixes():
    first_char_counts = Counter(s[0] for s in SYMBOLS.keys())
    first_char_counts.update(Counter(k[0] for k in KEYWORDS.keys()))
    prefixes = set()
    for k, c in first_char_counts.items():
        if c > 1:
            prefixes.add(k)
    assert set(PREFIXES) == prefixes


def test_match_exponent():
    assert match_exponent("E4+") == \
        MatchResult(True, Token(TokenKind.EXPONENT,"E4", 0, 2, 4), 2, None)
    assert match_exponent("1.2E4+", 3) == \
        MatchResult(True, Token(TokenKind.EXPONENT,"E4", 3, 5, 4), 2, None)
    assert match_exponent("E+4") == \
        MatchResult(True, Token(TokenKind.EXPONENT, "E+4", 0, 3, 4), 3, None)
    assert match_exponent("e-4") == \
        MatchResult(True, Token(TokenKind.EXPONENT, "e-4", 0, 3, -4), 3, None)
    assert match_exponent("e-145") == \
        MatchResult(True, Token(TokenKind.EXPONENT, "e-145", 0, 5, -145), 5, None)
    assert match_exponent("E-14.5") == \
        MatchResult(True, Token(TokenKind.EXPONENT, "E-14", 0, 4, -14), 4, None)
    assert match_exponent("eeac") == \
        MatchResult(False, None, 0, ScanError(None, "eeac", 1, ScanErrorMessages[31]))
    assert match_exponent("x=5") == \
        MatchResult(False, None, 0, ScanError(None, "x=5", 0, ScanErrorMessages[30]))
    assert match_exponent("21  x = 5") == \
        MatchResult(False, None, 0, ScanError(None, "21  x = 5", 0, ScanErrorMessages[30]))


def test_match_number():
    assert match_number("12") == \
        MatchResult(True, Token(TokenKind.NUMBER, "12", 0, 2, 12), 2, None)
    assert match_number("12  x = 5") == \
        MatchResult(True, Token(TokenKind.NUMBER, "12", 0, 2, 12), 2, None)
    assert match_number("001") == \
        MatchResult(True, Token(TokenKind.NUMBER, "001", 0, 3, 1), 3, None)
    assert match_number("12.0014+") == \
        MatchResult(True, Token(TokenKind.NUMBER, "12.0014", 0, 7, 12.0014), 7, None)
    assert match_number(".015()") == \
        MatchResult(True, Token(TokenKind.NUMBER, ".015", 0, 4, 0.015), 4, None)
    assert match_number("000.01-") == \
        MatchResult(True, Token(TokenKind.NUMBER, "000.01", 0, 6, 0.01), 6, None)
    assert match_number("1.2E6+") == \
        MatchResult(True, Token(TokenKind.NUMBER, "1.2E6", 0, 5, 1.2e6), 5, None)
    assert match_number("1.7E2+") == \
        MatchResult(True, Token(TokenKind.NUMBER, "1.7E2", 0, 5, 1.7e2), 5, None)
    assert match_number("11.e-2") == \
        MatchResult(True, Token(TokenKind.NUMBER, "11.e-2", 0, 6, 11e-2), 6, None)
    assert match_number("11.24e-5e+") == \
        MatchResult(True, Token(TokenKind.NUMBER, "11.24e-5", 0, 8, 11.24e-5), 8, None)
    assert match_number(".12.45") == \
        MatchResult(True, Token(TokenKind.NUMBER, ".12", 0, 3, 0.12), 3, None)
    assert match_number("x = 5", 4) == \
        MatchResult(True, Token(TokenKind.NUMBER, "5", 4, 5, 5), 1, None)


def test_match_identifier():
    assert match_identifier("x=56") == \
        MatchResult(True, Token(TokenKind.IDENTIFIER, "x", 0, 1), 1)
    assert match_identifier("_foo+0.5") == \
        MatchResult(True, Token(TokenKind.IDENTIFIER, "_foo", 0, 4), 4)
    assert match_identifier("_56ij_ = ") == \
        MatchResult(True, Token(TokenKind.IDENTIFIER, "_56ij_", 0, 6), 6)
    assert match_identifier("for i in range(0, 6)") == \
        MatchResult(True, Token(TokenKind.FOR, "for", 0, 3), 3)
    assert match_identifier("for i in ", 6) == \
        MatchResult(True, Token(TokenKind.IDENTIFIER, "in", 6, 8), 2, None)
    
    for kw, tk in KEYWORDS.items():
        assert match_identifier(f"{kw} _ =") == \
            MatchResult(True, Token(getattr(TokenKind, tk), kw, 0, len(kw)), len(kw))

def test_match_string():
    assert match_string("\"hello world\" +") == \
        MatchResult(True, Token(TokenKind.STRING, "\"hello world\"", 0, 13, "hello world"), 13, None)
    assert match_string("\"\"") == \
        MatchResult(True, Token(TokenKind.STRING, "\"\"", 0, 2, ""), 2, None)
    assert match_string("\"\t\nfoo \\\"bar\t\"").success

def test_match_comment():
    assert match_comment("//some long comment\n") == \
        MatchResult(True, None, 20)
    assert match_comment("// ") == MatchResult(True, None, 3)

def test_match_symbl():
    assert match_symbol("+ 5") == \
        MatchResult(True, Token(TokenKind.PLUS, "+", 0, 1), 1)
    assert match_symbol("+5") == \
        MatchResult(True, Token(TokenKind.PLUS, "+", 0, 1), 1)
    assert match_symbol("++5") == \
        MatchResult(True, Token(TokenKind.INC, "++", 0, 2), 2)
    assert match_symbol(" ++5", 1) == \
        MatchResult(True, Token(TokenKind.INC, "++", 1, 3), 2,)
    assert match_symbol("+*5") == \
        MatchResult(True, Token(TokenKind.PLUS, "+", 0, 1), 1)
    assert match_symbol("@4g") == \
        MatchResult(False, None, 0, ScanErrorMessages[10])
    
    for sy, tk in SYMBOLS.items():
        assert match_symbol(f"{sy} jibberish") == \
            MatchResult(True, Token(getattr(TokenKind, tk), sy, 0, len(sy)), len(sy))