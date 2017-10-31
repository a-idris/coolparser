import collections
from collections import namedtuple
import re


class LexError(Exception):
    pass


def initialise_patterns():
    # orderedDict, so considers in order of insertion. add token_patterns in order of precedence.
    token_patterns = collections.OrderedDict()

    # case insensitive keywords
    case_insensitive_keywords = ["class", "else", "fi", "if", "inherits", "in", "isvoid", "let",
                                 "loop", "pool", "then", "while", "case", "esac",  "new", "of", "not"]
    for kw in case_insensitive_keywords:
        regex = re.compile(kw, re.IGNORECASE)
        token_patterns[kw] = regex

    # case sensitive keywords. first letter must be lower case, rest insensitive
    case_sensitive_keywords = ["false", "true"]
    for kw in case_sensitive_keywords:
        # craft correct pattern from kw e.g. f(a|A)(l|L)(s|S)(e|E)
        adjusted_kw = kw[0] + ''.join(["({0}|{1})".format(letter, letter.upper()) for letter in kw[1:]])
        regex = re.compile(adjusted_kw)  # encoding as string-escape makes it evaluated as raw string
        token_patterns[kw] = regex

    # add recognizers for symbols
    symbols = [";", ",", ":", "{", "}", "(", ")", "<-", "@", ".", "=>", "+", "-", "~", "*", "/", "<=", "<", "="]
    # can group by precedence e.g. addop, mulop, etc. also, consider 'full' string matching,
    # since = will match for <= and =>.
    # maybe just solve w/ ordering? or do "^{0}$".format(pattern)
    for symbol in symbols:
        regex = re.compile(re.escape(symbol))
        token_patterns[symbol] = regex

    # integers
    regex = re.compile(r"[0-9]+")
    token_patterns["integer"] = regex

    # special notation: self and SELF_TYPE
    regex = re.compile(r"self")
    token_patterns["self"] = regex

    regex = re.compile(r"SELF_TYPE")
    token_patterns["self_type"] = regex

    # type identifier
    regex = re.compile(r"[A-Z][A-Za-z0-9_]*")
    token_patterns["type_id"] = regex

    # object identifier
    regex = re.compile(r"[a-z][A-Za-z0-9_]*")
    token_patterns["object_id"] = regex

    # strings
    regex = re.compile(r'"(.*?)"', re.VERBOSE)
    token_patterns["string"] = regex

    # whitespace
    regex = re.compile(r"\s")
    token_patterns["whitespace"] = regex

    return token_patterns


# initialise patterns
patterns = initialise_patterns()
# use namedtuple to represent tokens
Token = namedtuple('Token', 'name val')


# remove
def lex(lexer):
    while True:
        token = next_token(lexer)
        print("<{0}, {1}>".format(token.name, token.val), end=' ')
        if token.name == "eof":
            break
        """
        # use shlex lexeme splitter, it will split alphanumeric (with _), and individual punctuation symbols.
        # need to slightly modify so that it matches multichar cool symbols as tokens (e.g. => as => not =,>)
        lexeme = lexer.get_token()

        while lexeme.count('"') == 1:
            # if there is an unmatched quote, append shlex tokens until the lexeme has a matched quote
            lexeme += lexer.get_token()

        # print("<{0}>".format(lexeme), end=', ')
        if lexeme == lexer.eof:
            break
        token = match_pattern(lexeme, lexer)
        print("<{0}, {1}>".format(token.name, token.val), end=' ')
        """


def next_token(lexer):
    # candidate string, switch w/ lexeme types. pass lexeme type?
    # list, precompiled regexes. get string token from shlex then pass it thru, returnign lex error if necessary else
    # returning an encoding of a token types
    lexeme = lexer.get_token()
    # if there is an unmatched quote, append shlex tokens until the lexeme has a matched quote
    while lexeme.count('"') == 1:
        lexeme += lexer.get_token()
    if lexeme == lexer.eof:
        return Token("eof", "")
    return match_pattern(lexeme, lexer)


def match_pattern(lexeme, lexer):
    """
    in order of importance
    find longest match from al the different regexes, tie break based on the index of the regex in the ordereddict
    """
    matches = []
    for token_name, regex in patterns.items():
        result = regex.match(lexeme)
        if result:
            matched_str = result.group()
            matches.append((token_name, matched_str))  # append str and match object tuple

    # if no matches, it's not a valid lexeme. raise error
    if len(matches) == 0:
        raise LexError

    # find max based on length of matched string. if multiple of same value, max returns the first one so there is
    # automatic tie-breaking based on the insertion order in the OrderedDict
    result_tuple = max(matches, key=lambda item: len(item[1]))
    token_name = result_tuple[0]
    matched_str = result_tuple[1]
    if len(matched_str) != len(lexeme):
        rest = lexeme[len(matched_str):]
        lexer.push_token(rest)
    return Token(token_name, matched_str)
    # return Token(name=token_name, val=matched_str)
