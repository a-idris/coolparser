import sys
import shlex
import re
import collections


# first, follow, firstplus
# recursive descent class - if valid, store. recursive descent method - if valid, store.
# if valid, print stored
class LexError(Exception):
    pass


def parse(filename):

    # initialise patterns
    patterns = initialise_patterns()
    # open file
    with open(filename) as f:
        input_file = f.read()
        lexer = shlex.shlex(input_file)
        lexer.whitespace_split = True
        while True:
            # use shlex lexeme splitter, it will split alphanumeric (with _), and individual punctuation symbols.
            # need to slightly modifty so that it matches multichar cool symbols as tokens (e.g. => as => not =,>)
            lexeme = lexer.get_token()
            # print("<{0}>".format(lexeme), end=', ')
            if lexeme == lexer.eof:
                break
            match_pattern(lexeme, patterns, lexer)

        # set global pointer, manipulating w/ getToken
        # stream tokens to parse method

    # for more accurate error reporting can loop over readline, maintaine line num. char within shlex gives index


def match_full_str(pattern):
    return pattern
    # return "^({0})$".format(pattern)


def initialise_patterns():
    # orderedDict, so considers in order of insertion. add token_patterns in order of precedence.
    token_patterns = collections.OrderedDict()

    # case insensitive keywords
    case_insensitive_keywords = ["class", "else", "fi", "if", "in", "inherits", "isvoid", "let",
                                 "loop", "pool", "then", "while", "case", "esac",  "new", "of", "not"]
    for kw in case_insensitive_keywords:
        regex = re.compile(match_full_str(kw), re.IGNORECASE)
        token_patterns[kw] = regex

    # case sensitive keywords. first letter must be lower case, rest insensitive
    case_sensitive_keywords = ["false", "true"]
    for kw in case_sensitive_keywords:
        # craft correct pattern from kw e.g. f(a|A)(l|L)(s|S)(e|E)
        adjusted_kw = kw[0] + ''.join(["({0}|{1})".format(letter, letter.upper()) for letter in kw[1:]])
        regex = re.compile(match_full_str(adjusted_kw))  # encoding as string-escape makes it evaluated as raw string
        token_patterns[kw] = regex

    # add recognizers for symbols
    symbols = [";", ",", ":", "{", "}", "(", ")",
               "<-", "@", ".", "=>", "+", "-", "~", "*", "/", "<=", "<", "="]
    # can group by precedence e.g. addop, mulop, etc. also, consider 'full' string matching,
    # since = will match for <= and =>.
    # maybe just solve w/ ordering? or do "^{0}$".format(pattern)
    for symbol in symbols:
        regex = re.compile(match_full_str(re.escape(symbol)))
        token_patterns[symbol] = regex

    # integers
    regex = re.compile(match_full_str(r"[0-9]+"))
    token_patterns["integer"] = regex

    # special notation: self and SELF_TYPE
    regex = re.compile(match_full_str(r"self"))
    token_patterns["self"] = regex

    regex = re.compile(match_full_str(r"SELF_TYPE"))
    token_patterns["self_type"] = regex

    # type identifier
    regex = re.compile(match_full_str(r"[A-Z][A-Za-z0-9_]*"))
    token_patterns["type_id"] = regex

    # object identifier
    regex = re.compile(match_full_str(r"[a-z][A-Za-z0-9_]*"))
    token_patterns["object_id"] = regex

    # strings
    regex = re.compile(match_full_str(r'"(.*?)"'), re.VERBOSE)
    token_patterns["string"] = regex

    # whitespace
    regex = re.compile(match_full_str(r"\s"))
    token_patterns["whitespace"] = regex

    return token_patterns


def match_pattern(lexeme, patterns, lexer):
    """
    in order of importance
    """

    for token_name, regex in patterns.items():
        result = regex.match(lexeme)
        if result:
            matched_str = result.group()
            if len(matched_str) != len(lexeme):
                rest = lexeme[len(matched_str):]
                lexer.push_token(rest)
            print("<{0}>".format(token_name), end=' ')
            return token_name

    # if no matches, it's not a valid lexeme. raise error
    raise LexError


if __name__ == "__main__":
    parse(sys.argv[1])

"""
def is_match(token_name):
    pass

def getToken():
    #regexs
    #candidate string, switch w/ lexeme types. pass lexeme type?
    #list, precompiled regexes. get string token from shlex then pass it thru, returnign lex error if necessary else returning an ecncoding of a token types
    pass

def start():
    ""
    lexical types:
    integers, type identifiers, object identifiers, special notation, strings, keywords, white space.
    integers = [0-9]+
    type identifiers = [A-Z][A-Za-z0-9_] | SELF_TYPE
    object identifiers = [a-z][A-Za-z0-9_] | self 
    special identifiers = self | SELF_TYPE  ->CANT USE SPECIAL IDS IN SOME CONSTRUCTS E,G, CASE OR LET
    Name -> [A-Z][A-Za-z0-9] 

    keywords: class, else, false, fi, if, in, inherits, isvoid, let, loop, pool, then, while, case, esac, new, of, not, true
        "class", "else", "false", "fi", "if", "in", "inherits", "isvoid", "let", "loop", "pool", "then", "while", "case", "esac",  "new", "of", "not", "true"

    ----

    Grammar:
    PROGRAM ->  CLASS *

    PROGRAM -> PROGRAM'
    PROGRAM' -> CLASS PROGRAM' | eps

    CLASS -> 'class' Name ('inherits' Type)? '{' FEATURE_LIST '}' ';'
    CLASS_TYPE -> eps | 'inherits' Type
    FEATURE_LIST -> FEATURE_SINGLE FEATURE_LIST_PRIME
    FEATURE_LIST_PRIME -> 
    FEATURE-> ATTRIBUTE | METHOD
    ATTRIBUTE -> Id ':' Type ';'
    METHOD ->  Id '(' ARGSLIST ')' ':' Type {' METHOD_BODY '}'
    ARGSLIST -> ARG ARGSLIST | eps
    ARG -> Id ':' Type
    METHOD_BODY -> STATEMENT METHOD_BODY | eps


    ""
    pass
"""
