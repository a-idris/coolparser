import sys
import shlex
import re
import collections


# first, follow, firstplus
# recursive descent class - if valid, store. recursive descent method - if valid, store.
# if valid, print stored
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


def parse(filename):
    # open file
    with open(filename) as f:
        input_file = f.read()
        lexer = shlex.shlex(input_file)
        lexer.whitespace_split = True
        lexer.quotes = ''  # disable shlex quote behaviour
        if program(lexer):
            print("No errors found")
        else:
            print("Errors found")
        # set global pointer, manipulating w/ getToken
        # stream tokens to parse method
    # for more accurate error reporting can loop over readline, maintain line num. char within shlex gives index


# remove
def lex(lexer):
    while True:
        # use shlex lexeme splitter, it will split alphanumeric (with _), and individual punctuation symbols.
        # need to slightly modify so that it matches multichar cool symbols as tokens (e.g. => as => not =,>)
        lexeme = lexer.get_token()

        while lexeme.count('"') == 1:
            # if there is an unmatched quote, append shlex tokens until the lexeme has a matched quote
            lexeme += lexer.get_token()

        # print("<{0}>".format(lexeme), end=', ')
        if lexeme == lexer.eof:
            break
        match_pattern(lexeme, lexer)


def next_word(lexer):
    # candidate string, switch w/ lexeme types. pass lexeme type?
    # list, precompiled regexes. get string token from shlex then pass it thru, returnign lex error if necessary else
    # returning an encoding of a token types
    lexeme = lexer.get_token()
    # if there is an unmatched quote, append shlex tokens until the lexeme has a matched quote
    while lexeme.count('"') == 1:
        lexeme += lexer.get_token()
    if lexeme == lexer.eof:
        return None
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
    print("<{0}, {1}>".format(token_name, matched_str), end=' ')
    return token_name


word = ''


def program(lexer):
    global word
    word = next_word(lexer)

    if _class(lexer):
        if program(lexer):
            return True
        elif word == lexer.eof:
            return True
    else:
        return False


def _class(lexer):
    global word

    if word == "class":
        word = next_word(lexer)

        if word == "type_id":
            word = next_word(lexer)

            if class_inheritance(lexer):

                if word == "{":
                    word = next_word(lexer)

                    if feature_list(lexer):

                        if word == "}":
                            word = next_word(lexer)

                            if word == ";":
                                word = next_word(lexer)
                                return True
    return False


def class_inheritance(lexer):
    global word

    if word == "inherits":
        word = next_word(lexer)

        if word == "type_id" or word == "self_type":
            word = next_word(lexer)
            return True


def feature_list(lexer):
    global word

    if feature(lexer):
        if word == ";":
            word = next_word(lexer)

            if feature_list(lexer):
                return True
            elif word == lexer.eof:
                return True
    return False


def feature(lexer):
    global word
    if word == "object_id":
        word = next_word(lexer)

        if word == "(":
            word = next_word(lexer)

            if formal_list(lexer):
                if word == ")":
                    word = next_word(lexer)

                    if word == "type_id":
                        word = next_word(lexer)

                        if word == "{":
                            word = next_word(lexer)

                            if expr(lexer):
                                if word == "}":
                                    return True
        elif word == ":":
            word = next_word(lexer)

            if word == "type_id":
                word = next_word(lexer)

                if feature_assignment(lexer):
                    return True
    return False


def feature_assignment(lexer):
    global word
    if word == "<-":
        word = next_word(lexer)
        if expr(lexer):
            return True
    return False


def formal_list(lexer):
    global word
    if formal(lexer):
        if word == lexer.eof:
            return True
        elif formal_list(lexer):
            return True
    return False


def formal(lexer):
    global word

    if word == "object_id":
        word = next_word(lexer)

        if word == ":":
            word = next_word(lexer)

            if word == "type_id":
                word = next_word(lexer)
                return True
    return False


def expr(lexer):
    global word
    return True


if __name__ == "__main__":
    parse(sys.argv[1])

"""
    Naive Grammar:
    PROGRAM -> CLASS ; PROGRAM                                                           ||
            | CLASS ;
    
    CLASS -> class type_id CLASS_TYPE { FEATURE_LIST } ;
    
    CLASS_TYPE -> inherits type_id 
            | eps
    
    FEATURE_LIST -> FEATURE ; FEATURE_LIST 
                | eps
    
    FEATURE -> object_id ( ARGS_LIST ) : type { EXPR }
             | object_id : type OPT_EXPR_ASSIGNMENT 
    
    ARGSLIST -> ARGSLIST' 
            | eps    
    ARGSLIST' -> FORMAL ARGSLIST''
    ARGSLIST'' -> , FORMAL ARGSLIST'' 
                | eps
    
    OPT_EXPR_ASSIGNMENT -> EXPR_ASSIGNMENT 
                        | eps
    EXPR_ASSIGNMENT -> <- EXPR
    
    FORMAL -> object_id : type
        
    EXPR -> object_id ( EXPR_ARGS ) 
            | if EXPR then EXPR else EXPR fi 
            | while EXPR loop EXPR pool 
            | { EXPR_LIST } 
            | let LET_ARGS in EXPR 
            | case EXPR of CASE_ARGS esac 
            | new type_id 
            | object_id  <- ASSIGNMENT_EXPR 
            | ASSIGNMENT_EXPR
            
    ASSIGNMENT_EXPR -> not BOOLEAN_COMPLEMENT_EXPR 
                    | BOOLEAN_COMPLEMENT_EXPR

    BOOLEAN_COMPLEMENT_EXPR -> COMPARISON_EXPR BOOLEAN_COMPLEMENT_EXPR'
    BOOLEAN_COMPLEMENT_EXPR' -> <= COMPARISON_EXPR BOOLEAN_COMPLEMENT_EXPR' 
                              | < COMPARISON_EXPR BOOLEAN_COMPLEMENT_EXPR' 
                              | = COMPARISON_EXPR BOOLEAN_COMPLEMENT_EXPR' 
                              | eps
                    
    COMPARISON_EXPR -> ADDOP_EXPR COMPARISON_EXPR'
    COMPARISON_EXPR' -> + ADDOP_EXPR COMPARISON_EXPR'  
                     |  - ADDOP_EXPR COMPARISON_EXPR'
                     |  eps 
                
    ADDOP_EXPR -> MULTOP_EXPR ADDOP_EXPR'
    ADDOP_EXPR' -> * MULTOP_EXPR ADDOP_EXPR'  
                 |  / MULTOP_EXPR ADDOP_EXPR'
                 |  eps                 

    MULTOP_EXPR -> isvoid CHECKVOID_EXPR 
                | CHECKVOID_EXPR
    
    CHECKVOID_EXPR -> ~ INTEGER_COMPLEMENT_EXPR 
                    | INTEGER_COMPLEMENT_EXPR
    
    INTEGER_COMPLEMENT_EXPR -> DISPATCH_TYPE_EXPR @ type_id 
                            | DISPATCH_TYPE_EXPR
    
    DISPATCH_TYPE_EXPR  -> DISPATCH_EXPR . object_id ( EXPR_ARGS ) 
                        | DISPATCH_EXPR 
    
    DISPATCH_EXPR -> CONSTANT 
                    | ID 
                    | ( EXPR )
    CONSTANT -> integer 
            | string 
            | true 
            | false
            
    ID -> object_id
      
    EXPR_ARGS -> EXPR_ARGS' 
            | eps
            
    EXPR_ARGS' -> EXPR EXPR_ARGS''
    
    EXPR_ARGS'' -> , EXPR EXPR_ARGS'' 
                | eps
    
    EXPR_LIST -> EXPR ; EXPR_LIST 
                | EXPR ;
    
    LET_ARGS ->  LET_ARG LET_ARGS'
    
    LET_ARGS' -> , LET_ARG LET_ARGS' 
                | eps
                
    LET_ARG -> object_id : type_id OPT_EXPR_ASSIGNMENT
    
    CASE_ARGS -> CASE_ARG CASE_ARGS 
                | CASE_ARG 
                
    CASE_ARG -> object_id : type_id => EXPR ; 
    
    
    ===========
    A+B:
    G -> A
    G -> B
    
    A*:
    G -> A G
    G -> (empty)
    
    AB:
    G -> AB
    
    A+: == AA*
    G -> A G2
    G2 -> A G
    G2 -> (empty)
    
    PROGRAM -> CLASS ; PROGRAM | CLASS ;
    
    program -> class; program'
    program' -> class; program' | eps 
    
    ATTRIBUTE | METHOD
    ATTRIBUTE -> Id ':' Type ';'
    METHOD ->  Id '(' ARGSLIST ')' ':' Type {' METHOD_BODY '}'
    ARGSLIST -> ARG ARGSLIST | eps
    ARG -> Id ':' Type
    METHOD_BODY -> STATEMENT METHOD_BODY | eps

"""
