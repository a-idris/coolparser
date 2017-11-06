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

    for symbol in symbols:
        regex = re.compile(re.escape(symbol))
        token_patterns[symbol] = regex

    # integers
    regex = re.compile(r"[0-9]+")
    token_patterns["integer"] = regex

    # type identifier
    regex = re.compile(r"[A-Z][A-Za-z0-9_]*")
    token_patterns["type_id"] = regex

    # object identifier
    regex = re.compile(r"[a-z][A-Za-z0-9_]*")
    token_patterns["object_id"] = regex

    # special notation: self and SELF_TYPE
    regex = re.compile(r"self")
    token_patterns["self"] = regex

    regex = re.compile(r"SELF_TYPE")
    token_patterns["self_type"] = regex

    # strings
    regex = re.compile(r'"(.*?)"', re.VERBOSE)
    token_patterns["string"] = regex

    # whitespace
    regex = re.compile(r"[ \t]+")
    token_patterns["whitespace"] = regex

    return token_patterns


# initialise patterns
patterns = initialise_patterns()
# use namedtuple to represent tokens
Token = namedtuple('Token', 'name val line_no column_index line')

line_no = 0
column_index = 0
current_line = ''


def next_token(lexer):
    # list, precompiled regexes. get string token from shlex then pass it thru, returnign lex error if necessary else
    # returning an encoding of a token types
    global line_no
    global column_index
    global current_line

    if line_no == 0:
        line_no = lexer.lineno

    while True:
        lexeme = lexer.get_token()
        if lexer.lineno - 1 != line_no:
            line_no = lexer.lineno - 1  # line_no = lexer.lineno - 1
            column_index = 0
            current_line = lexeme
        if lexeme == lexer.eof:
            return Token("eof", "eof", line_no, column_index, current_line)
        token_name, matched_str = match_pattern(lexeme, lexer)
        column_index += len(matched_str)

        if token_name != "whitespace":
            return Token(token_name, matched_str, line_no, column_index - len(matched_str), current_line)


def peek_token(lexer):
    nt = next_token(lexer)
    # push it back on the stack so the next call to next_token returns the same result
    lexer.push_token(nt.val)
    return nt


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
    return token_name, matched_str
