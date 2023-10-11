import itertools
from enum import Enum
from typing import Optional

from src.loxerr import ScanError, ScanErrorMessages

SYMBOLS = {
    "(":   "LPAREN",
    ")":   "RPAREN",
    "{":   "LCURLY",
    "}":   "RCURLY",
    "[":   "LANGLE",
    "]":   "RANGLE",
    ":":   "DOTS",
    ".":   "DOT",
    ",":   "COMMA",
    ";":   "COLON",
    "+":   "PLUS",
    "++":  "INC",
    "+=":  "PLUSEQ",
    "-":   "MINUS",
    "--":  "DEC",
    "-=":  "MINEQ",
    "*":   "MUL",
    "/":   "DIV",
    "//":  "COMMENT",
    "=":   "EQ",
    "==":  "DEQ",
    "<":   "LT",
    "<=":  "LTEQ",
    ">":   "GT",
    ">=":  "GTEQ",
    "!=":  "NEQ",
    "!":   "BANG"
}

KEYWORDS = {
    "and": "AND",
    "or":  "OR",
    "not": "NOT",
    "xor": "XOR",
    "if":  "IF",
    "else": "ELSE",
    "while": "WHILE",
    "for": "FOR",
    "def": "DEF",
    "var": "VAR",
    "nil": "NIL",
    "true": "TRUE",
    "false": "FALSE"
}

PREFIXES = ("+", "-", "=", "<", ">", "!", "n", "/", "f")

ESCAPE_SEQUENCES = {
    'a': '\a',
    'b': '\b',
    'f': '\f',
    'n': '\n',
    'r': '\r',
    't': '\t',
    'v': '\v',
    '\\': '\\',
    '\'': '\'',
    '\"': '\"',
}



TokenKind = Enum("TokenKind",
                list(SYMBOLS.values()) + list(KEYWORDS.values()) + \
                ["NUMBER", "STRING", "IDENTIFIER", "EXPONENT"])


class Token:

    Kind = TokenKind

    def __init__(self, kind, lexeme, start, end, literal=None):
        self.kind = kind
        self.lexeme = lexeme
        self.start = start
        self.end = end
        self.literal = literal

    def __str__(self):
        if self.literal is not None:
            return f"{self.kind.name}({self.literal})"
        else:
            return f"{self.kind.name}({self.lexeme})"

    def __repr__(self):
        if self.literal is None:
            return f"Token({self.kind.name}, \"{self.lexeme}\", " \
                   f"{self.start}, {self.end})"
        else:
            return f"Token({self.kind.name}, \"{self.lexeme}\", " \
                   f"{self.start}, {self.end}, {self.literal})"

    def __eq__(self, other):
        return self.kind == other.kind and \
               self.literal == other.literal and \
               self.lexeme == other.lexeme


class MatchResult:

    def __init__(self,
                 success: bool, token: Optional[Token], span: int,
                 error: Optional[ScanError] = None):
        self.success = success
        self.token = token
        self.span = span
        self.error = error

    def __repr__(self):
        return f"MatchResult({self.success}, {self.span}, {self.token})"
    
    def __eq__(self, other):
        return  self.success == other.success and \
                self.span == other.span and \
                self.token == other.token and \
                self.error == other.error



class LoxScanner:

    def __init__(self, content: str):
        self.content = content
        self.size = len(self.content)
        self.start = 0
        self.current = 0
        self.tokens = []
        self.errors = []

    def advance(self) -> str:
        if self.current < len(self.content):
            char = self.content[self.current]
            self.current += 1
            return char
        else:
            char = ''
        return char

    def consume(self) -> None:
        while self.current < len(self.content):
            nextchar = self.advance()
            match nextchar:
                case ' ' | '\t' | '\n' | '\r':
                    self.current -= 1
                    return
                case _:
                    continue

    def peek(self, n=0) -> str:
        idx = self.current + n
        if idx < len(self.content):
            char = self.content[idx]
        else:
            char = ''
        return char

    def scan_symbol(self, char0: str) -> Token:
        char1 = self.advance()
        if (char0 + char1) in SYMBOLS:
            lexeme = char0 + char1
            kind = getattr(TokenKind, SYMBOLS[lexeme])
        elif char0 in SYMBOLS:
            lexeme = char0
            kind = getattr(TokenKind, SYMBOLS[lexeme])
        else:
            kind = None
        return None if kind is None else Token(kind, lexeme, None)

    def scan_identifier(self, char0: str):
        chars = [char0]
        # Read characters until next whitespace
        while self.current < len(self.content):
            c = self.advance()
            if c.isalnum():
                chars.append(c)
            else:
                self.current -= 1
                break
        lexeme = ''.join(chars)
        kind = getattr(TokenKind, KEYWORDS.get(lexeme, ""), TokenKind.IDENTIFIER)
        return Token(kind, lexeme, None)

    def scan_number(self, char0: str):
        chars = [char0]
        has_dot = (char0 == '.')
        has_exp = False
        error = False
        while self.current < len(self.content):
            c = self.advance()
            if c.isnumeric():
                chars.append(c)
            elif c == '.' and not has_dot:
                chars.append(c)
                has_dot = True
            elif c == '.' and has_dot:
                self.makeerr("Expected digit")
                self.consume()
                error = True
                break
            elif c == 'E' or c == 'e' and not has_exp:
                chars.append(c)
                has_exp = True
                c = self.advance()
                if c == '-' or c == '+' or c.isnumeric():
                    chars.append(c)
                else:
                    self.makeerr("Expected proper exponent")
                    self.consume()
                    error = True
                    break
            elif c == 'E' or c == 'e' and has_exp:
                self.makeerr("Expected digit")
                self.consume()
                error = True
            else:
                self.current -= 1
                break
        if error:
            return None
        number = ''.join(chars)
        if has_dot or has_exp:
            literal = float(number)
        else:
            literal = int(number)
        return Token(TokenKind.NUMBER, number, literal)

    def scan_string(self, char0):
        assert char0 == '\"'
        chars = []
        lexeme = [char0]
        end = False
        while self.current < len(self.content):
            c = self.advance()
            lexeme.append(c)
            if c == '\\':
                next_c = self.advance()
                lexeme.append(next_c)
                # TODO
                # Add support for \nnn \xhh \uhhhh \Uhhhhhhhh
                if next_c in Scanner.EscapeChars:
                    chars.append(Scanner.EscapeChars[next_c])
                else:
                    self.makeerr("Unknown escape character.")
                    self.advance()
            elif c == '\"':
                end = True
                break
            else:
                chars.append(c)
        if not end:
            self.makeerr("String not terminated.")
            return None
        literal = ''.join(chars)
        lexeme = ''.join(lexeme)
        return Token(TokenKind.STRING, lexeme, literal)

    def scan_comment(self):
        c = self.content[self.current]
        while self.current < len(self.content) and c != '\n':
            c = self.advance()

    def nexttok(self):
        while self.current < self.size:
            char = self.peek()
            tok = None
            # Whitespace
            if char.isspace():
                self.current += 1
                continue
            # Keyword or Identifier
            elif char.isalpha() or char == '_':
                m = match_identifier(self.content, self.current)
                if m.success:
                    self.current += m.span
                    tok = m.token
                else:
                    raise RuntimeError('Unreachable case')
            # Number
            elif char.isnumeric():
                m = match_number(self.content, self.current)
                if m.success:
                    self.current += m.span
                    tok = m.token
                else:
                    raise RuntimeError('Unreachable case')
            # Number or '.'
            elif char == '.':
                m = match_number(self.content, self.current)
                if m.success:
                    self.current += m.span
                    tok = m.token
                else:
                    m = match_symbol(self.content, self.current)
                    if m.success:
                        self.current += m.span
                        tok = m.token
                    else:
                        raise RuntimeError('Unreachable case')
            # Comment or /
            elif char == '/':
                m = match_comment(self.content, self.current)
                if m.success:
                    self.current += m.span
                    continue
                else:
                    m = match_symbol(self.content, self.current)
                    if m.success:
                        self.current += m.span
                        tok = m.token
                    else:
                        raise RuntimeError('Unreachable case')
            # String
            elif char == '"':
                m = match_string(self.content, self.current)
                if m.success:
                    tok = m.token
                else:
                    self.errors.extend(m.error)
                self.current += m.span
            # Symbol
            else:
                m = match_symbol(self.content, self.current)
                if m.success:
                    tok = m.token
                    self.current += m.span
                else:
                    self.errors.append(m.error)
                    self.current += 1
            yield tok

    def scan(self):
        g = self.nexttok()
        for tok in filter(lambda t: t is not None, g):
            self.tokens.append(tok)

    def makeerr(self, msg):
        err = ScanError('', self.content, self.current, msg)
        self.errors.append(err)


def tokenize(line):
    scanner = LoxScanner(line)
    scanner.scan()
    return scanner.tokens


def match_symbol(content: str, start=0) -> MatchResult:
    """Matches symbol in `content` at `start` and retuns `MatchResult`."""
    # If the character at `start` position is prefix of more than 1 symbols
    # try to match 2-character symbols first
    if len(content) - start > 1 and content[start] in PREFIXES:
        lex01 = content[start:start+2]
        kind = getattr(TokenKind, SYMBOLS.get(lex01, ""), None)
        if kind is not None:
            tok = Token(kind, lex01, start, start+2, None)
            return MatchResult(True, tok, span=2)
    # Match single character against SYMBOLS
    lex0 = content[start:start+1]
    kind = getattr(TokenKind, SYMBOLS.get(lex0, ""), None)
    if kind is not None:
        tok = Token(kind, lex0, start, start+1, None)
        return MatchResult(True, tok, span=1)
    else:
        return MatchResult(False, None, span=0, error=ScanErrorMessages[10])


def match_comment(content: str, start=0) -> MatchResult:
    """Matches comment in `content` at `start` and retuns `MatchResult`."""
    if len(content) - start > 2:
        mark = content[start:start+2]
        if mark == "//":
            i = start + 2
            while i < len(content) and content[i] != '\n':
                i += 1
            # Consume '\n'
            if i < len(content) and content[i] == '\n':
                i += 1
            return MatchResult(True, None, span=i-start)
    return MatchResult(False, None, 0)


def match_string(content: str, start=0) -> MatchResult:
    chars = []
    end = False
    if content[start] != '"':
        return MatchResult(False, None, span=0, error=ScanErrorMessages[11])
    i = start + 1
    errors = []

    while i < len(content):
        c = content[i]
        # Check if we have escape sequence
        # TODO
        # Add support for \nnn \xhh \uhhhh \Uhhhhhhhh
        if c == '\\':
            if i + 1 >= len(content):
                errors.append(ScanError(None, content, i, ScanErrorMessages[12]))
                break
            c2 = content[i + 1]
            seq = ESCAPE_SEQUENCES.get(c2, None)
            if seq:
                chars.append(seq)
            else:
                errors.append(ScanError(None, content, i, ScanErrorMessages[13]))
            i += 2
        # End of string
        elif c == '\"':
            i += 1
            end = True
            break
        # Any character
        else:
            chars.append(c)
            i += 1
    if not end:
        errors.append(ScanError(None, content, i, ScanErrorMessages[14]))

    literal = ''.join(chars) if not errors else ''
    lexeme = ''.join(['"'] + chars + (['"'] if end else []))
    return MatchResult(
        success=(len(errors) == 0),
        token=Token(TokenKind.STRING, lexeme, start, i, literal),
        span=i - start,
        error=errors if len(errors) else None
    )


def match_identifier(content: str, start=0):
    chars = []
    # Read characters until next whitespace or symbol
    i = start
    while i < len(content):
        c = content[i]
        if c.isalnum() or c == '_':
            chars.append(c)
            i += 1
        else:
            break
    lexeme = ''.join(chars)
    if not lexeme:
        err = ScanError(None, content, start, ScanErrorMessages[15])
        return MatchResult(False, None, 0, err)
    kind = getattr(TokenKind, KEYWORDS.get(lexeme, ""), TokenKind.IDENTIFIER)
    return MatchResult(True, Token(kind, lexeme, start, i), span=i-start)


def match_number(content: str, start=0):

    if not (content[start].isnumeric() or content[start] == '.'):
        err = ScanError(None, content, start, ScanErrorMessages[16])
        return MatchResult(False, None, 0, err)
    chars = []
    has_dot = False
    has_digit = False
    i = start
    while i < len(content):
        c = content[i]
        if c.isnumeric():
            chars.append(c)
            has_digit = True
        elif c == '.' and not has_dot:
            chars.append(c)
            has_dot = True
        # We've consumed extra char
        else:
            break
        i += 1
    # Check if we have valid number
    if not has_digit:
        err = ScanError(None, content, i, ScanErrorMessages[17])
        return MatchResult(False, None, 0, err)
    lexeme = ''.join(chars)
    literal = float(lexeme) if has_dot else int(lexeme)
    # Check for optional exponent
    if i < len(content):
        exp = match_exponent(content, i)
        if exp.success:
            lexeme += exp.token.lexeme
            literal = float(lexeme)
            i += exp.span
    tok = Token(TokenKind.NUMBER, lexeme, start, i, literal)
    return MatchResult(True, tok, i - start)


def match_exponent(content: str, start=0) -> MatchResult:
    """Matches an exponent token in the form '[Ee][+-]?\\d+'."""
    if start >= len(content):
        err = ScanError(None, content, start, ScanErrorMessages[40])
        return MatchResult(False, None, 0, err)
    # Read 'E' or 'e'
    if content[start].lower() != 'e':
        err = ScanError(None, content, start, ScanErrorMessages[30])
        return MatchResult(False, None, 0, err)
    i = start + 1
    # Read optional sign
    sign = 1
    if content[i] == '-':
        sign = -1
        i += 1
    elif content[i] == '+':
        i += 1
    # Read exponent value
    value = list(itertools.takewhile(lambda c: c.isnumeric(),
                                     itertools.islice(content, i, len(content))))
    i += len(value)
    if not value:
        err = ScanError(None, content, i, ScanErrorMessages[31])
        return MatchResult(False, None, 0, err)
    # Construct and return token & MatchResult
    literal = sign * int(''.join(value))
    tok = Token(TokenKind.EXPONENT, content[start:i], start, i, literal)
    return MatchResult(True, tok, i - start)
