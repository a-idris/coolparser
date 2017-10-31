import sys
import shlex
import re
import collections
from collections import namedtuple


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
        if lexeme == "eof":
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
    if lexeme == "eof":
        return Token("eof", "")
    return match_pattern(lexeme, lexer)


Token = namedtuple('Token', 'name val')


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
    return Token(token_name, matched_str)
    # return Token(name=token_name, val=matched_str)


word = ''


def program(lexer):
    global word
    word = next_word(lexer)

    if _class(lexer):
        if word == ";":
            word = next_word(lexer)
            if word == "eof":
                return True
            elif program(lexer):
                return True
    else:
        return False


def _class(lexer):
    global word

    if word == "class":
        word = next_word(lexer)

        if word == "type_id":
            word = next_word(lexer)

            #if begins w/ inherits. else if begins w/ {
            if class_type(lexer):

                if word == "{":
                    word = next_word(lexer)

                    if feature_list(lexer):

                        if word == "}":
                            word = next_word(lexer)

                            if word == ";":
                                word = next_word(lexer)
                                return True
    return False


def class_type(lexer):
    global word

    if word == "inherits":
        word = next_word(lexer)

        if word == "type_id" or word == "self_type":
            word = next_word(lexer)
            return True
    return False


def feature_list(lexer):
    global word

    if feature(lexer):
        if word == ";":
            word = next_word(lexer)

            if feature_list(lexer):
                return True
            elif word == "eof":
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
        if word == "eof":
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
    *** FIRST: class
    *** FOLLOW: eof | FOLLOW(PROGRAM_REST)
    PROGRAM -> CLASS ; PROGRAM_REST                 $$ FIRST_PLUS = class
    
    *** FIRST: class | eps
    *** FOLLOW: FOLLOW(PROGRAM) = eof 
    PROGRAM_REST -> PROGRAM                         $$ FIRST_PLUS = class
                |   eps                             $$ FIRST_PLUS = eof 
    
    *** FIRST: class
    *** FOLLOW: ;
    CLASS -> class type_id CLASS_TYPE { FEATURE_LIST }        $$ FIRST_PLUS = class
    
    *** FIRST: inherits | eps
    *** FOLLOW: {
    CLASS_TYPE -> inherits type_id                  $$ FIRST_PLUS = inherits
            | eps                                   $$ FIRST_PLUS = { 
    
    *** FIRST: object_id | eps
    *** FOLLOW: }
    FEATURE_LIST -> FEATURE ; FEATURE_LIST                  $$ FIRST_PLUS = object_id
                | eps                                       $$ FIRST_PLUS = } 
    
    *** FIRST: object_id
    *** FOLLOW: ; 
    FEATURE -> object_id FEATURE_REST               $$ FIRST_PLUS = object_id
    
    *** FIRST: ( | :
    *** FOLLOW: ;
    FEATURE_REST -> ( OPT_FEATURE_ARGS ) : type { EXPR }    $$ FIRST_PLUS = (
                |   : type OPT_EXPR_ASSIGNMENT              $$ FIRST_PLUS = :
    
    *** FIRST: object_id | eps
    *** FOLLOW: )
    OPT_FEATURE_ARGS -> FEATURE_ARGS                $$ FIRST_PLUS = object_id
                    | eps                           $$ FIRST_PLUS = ) 
    
    *** FIRST: object_id
    *** FOLLOW: )
    FEATURE_ARGS -> FORMAL MORE_FEATURE_ARGS                  $$ FIRST_PLUS = object_id
    
    *** FIRST: , | eps
    *** FOLLOW: )
    MORE_FEATURE_ARGS -> , FORMAL MORE_FEATURE_ARGS         $$ FIRST_PLUS = ,
                     | eps                                  $$ FIRST_PLUS = )
    
    *** FIRST: <- | eps
    *** FOLLOW: ; | , | in
    OPT_EXPR_ASSIGNMENT -> EXPR_ASSIGNMENT          $$ FIRST_PLUS = <-
                        | eps                       $$ FIRST_PLUS = ; | , | in 
    
    *** FIRST: <-
    *** FOLLOW: ; | , | in
    EXPR_ASSIGNMENT -> <- EXPR                      $$ FIRST_PLUS = <-
    
    *** FIRST: object_id
    *** FOLLOW: , | )
    FORMAL -> object_id : type_id                   $$ FIRST_PLUS = object_id
        
    *** FIRST: object_id | integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid | not
    *** FOLLOW: } | ; | in | ) | then | else | fi | loop | pool | of | , | . | @ | * | / | + | - | <= | < | =
    EXPR -> ID OBJECT_ID_OP                                     $$ FIRST_PLUS = object_id
        |   ASSIGNMENT_EXPR                                     $$ FIRST_PLUS = integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid | not

    *** FIRST: object_id 
    *** FOLLOW: ( | <- | } | ; | in | ) | then | else | fi | loop | pool | of | , | . | @ | * | / | + | - | <= | < | =  
    ID -> object_id                                     $$ FIRST_PLUS = object_id

    *** FIRST: ( | <- | eps
    *** FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    OBJECT_ID_OP -> ( OPT_EXPR_ARGS )                           $$ FIRST_PLUS = (
                |   <- ASSIGNMENT_EXPR                          $$ FIRST_PLUS = <-
                |   eps                                         $$ FIRST_PLUS = . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
            
    *** FIRST: integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid | not 
    *** FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    ASSIGNMENT_EXPR -> not BOOLEAN_COMPLEMENT_EXPR              $$ FIRST_PLUS = not
                    | BOOLEAN_COMPLEMENT_EXPR                   $$ FIRST_PLUS = integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid 

    *** FIRST: integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid 
    *** FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    BOOLEAN_COMPLEMENT_EXPR -> COMPARISON_EXPR COMPARISON_OP    $$ FIRST_PLUS = integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid 
    
    *** FIRST: <= | < | = | eps
    *** FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    COMPARISON_OP -> <= COMPARISON_EXPR COMPARISON_OP           $$ FIRST_PLUS = <=
                  |  < COMPARISON_EXPR COMPARISON_OP            $$ FIRST_PLUS = < 
                  |  = COMPARISON_EXPR COMPARISON_OP            $$ FIRST_PLUS = =
                  |  eps                                        $$ FIRST_PLUS = . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
                    
    *** FIRST: integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid 
    *** FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    COMPARISON_EXPR -> ADD_EXPR ADD_OP              $$ FIRST_PLUS = integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid 
    
    *** FIRST: + | - | eps
    *** FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    ADD_OP -> + ADD_EXPR ADD_OP                     $$ FIRST_PLUS = +
             |  - ADD_EXPR ADD_OP                   $$ FIRST_PLUS = - 
             |  eps                                 $$ FIRST_PLUS = . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
                
    *** FIRST: integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid 
    *** FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    ADD_EXPR -> MULT_EXPR MULT_OP                   $$ FIRST_PLUS = integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid 
    
    *** FIRST: * | / | eps
    *** FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    MULT_OP -> * MULT_EXPR MULT_OP                      $$ FIRST_PLUS = *
             | / MULT_EXPR MULT_OP                      $$ FIRST_PLUS = / 
             | eps                                      $$ FIRST_PLUS = . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 

    *** FIRST: integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid 
    *** FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    MULT_EXPR -> isvoid CHECKVOID_EXPR                  $$ FIRST_PLUS = isvoid
                | CHECKVOID_EXPR                        $$ FIRST_PLUS = integer | string | true | false | (  | if | while | { | let | case | new | ~
    
    *** FIRST: integer | string | true | false | (  | if | while | { | let | case | new | ~
    *** FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    CHECKVOID_EXPR -> ~ INTEGER_COMPLEMENT_EXPR               $$ FIRST_PLUS = ~
                    | INTEGER_COMPLEMENT_EXPR                 $$ FIRST_PLUS =  integer | string | true | false | (  | if | while | { | let | case | new
    
    *** FIRST:  integer | string | true | false | (  | if | while | { | let | case | new
    *** FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    INTEGER_COMPLEMENT_EXPR -> DISPATCH_TYPE_EXPR DISPATCH_TYPE_OP       $$ FIRST_PLUS =  integer | string | true | false | (  | if | while | { | let | case | new
    
    *** FIRST: @ | eps
    *** FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    DISPATCH_TYPE_OP -> @ type_id                       $$ FIRST_PLUS = @
                      | eps                             $$ FIRST_PLUS = . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
                    
    *** FIRST: integer | string | true | false | (  | if | while | { | let | case | new     
    *** FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    DISPATCH_TYPE_EXPR -> DISPATCH_EXPR DISPATCH_OP     $$ FIRST_PLUS = integer | string | true | false | (  | if | while | { | let | case | new
    
    *** FIRST: eps | .
    *** FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    DISPATCH_OP -> . object_id ( OPT_EXPR_ARGS )            $$ FIRST_PLUS = .
                | eps                                   $$ FIRST_PLUS = . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    
    *** FIRST: integer | string | true | false | (  | if | while | { | let | case | new
    *** FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    DISPATCH_EXPR -> CONSTANT                               $$ FIRST_PLUS = integer | string | true | false
                    | ( EXPR )                              $$ FIRST_PLUS = (
                    | if EXPR then EXPR else EXPR fi        $$ FIRST_PLUS = if
                    | while EXPR loop EXPR pool             $$ FIRST_PLUS = while
                    | { EXPR_LIST }                         $$ FIRST_PLUS = {
                    | let LET_ARGS in EXPR                  $$ FIRST_PLUS = let
                    | case EXPR of CASE_ARGS esac           $$ FIRST_PLUS = case
                    | new type_id                           $$ FIRST_PLUS = new
    
    *** FIRST: integer | string | true | false
    *** FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    CONSTANT -> integer                                 $$ FIRST_PLUS = integer
            | string                                    $$ FIRST_PLUS = string
            | true                                      $$ FIRST_PLUS = true
            | false                                     $$ FIRST_PLUS = false
    
    *** FIRST: object_id | integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid | not | eps
    *** FOLLOW: )
    OPT_EXPR_ARGS -> EXPR_ARGS                             $$ FIRST_PLUS = object_id | integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid | not
            | eps                                       $$ FIRST_PLUS = )
    
    *** FIRST: object_id | integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid | not
    *** FOLLOW: )
    EXPR_ARGS -> EXPR MORE_EXPR_ARGS                      $$ FIRST_PLUS = object_id | integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid | not
    
    *** FIRST: , | eps
    *** FOLLOW: )
    MORE_EXPR_ARGS -> , EXPR MORE_EXPR_ARGS             $$ FIRST_PLUS = ,
                | eps                                   $$ FIRST_PLUS = )
    
    *** FIRST: object_id | integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid | not
    *** FOLLOW: } | FOLLOW(MORE_EXPRS)  
    EXPR_LIST -> EXPR ; MORE_EXPRs                      $$ FIRST_PLUS = object_id | integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid | not
    
    *** FIRST: object_id | integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid | not | eps
    *** FOLLOW: FOLLOW(EXPR_LIST) = }
    MORE_EXPRS -> EXPR_LIST                             $$ FIRST_PLUS = object_id | integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid | not
                | eps                                   $$ FIRST_PLUS = }
    
    *** FIRST: object_id
    *** FOLLOW: in
    LET_ARGS ->  LET_ARG MORE_LET_ARGS                       $$ FIRST_PLUS = object_id
    
    *** FIRST: , | eps
    *** FOLLOW: in
    MORE_LET_ARGS -> , LET_ARG MORE_LET_ARGS                    $$ FIRST_PLUS = ,
                | eps                                           $$ FIRST_PLUS = in
    
    *** FIRST: object_id            
    *** FOLLOW: , | in
    LET_ARG -> object_id : type_id OPT_EXPR_ASSIGNMENT   $$ FIRST_PLUS = object_id    
    
    *** FIRST: object_id
    *** FOLLOW: esac | FOLLOW(MORE_CASE_ARGS)
    CASE_ARGS -> CASE_ARG MORE_CASE_ARGS            $$ FIRST_PLUS = object_id
    
    *** FIRST: object_id | eps
    *** FOLLOW: FOLLOW(CASE_ARGS) = esac
    MORE_CASE_ARGS -> CASE_ARGS                 $$ FIRST_PLUS = object_id
                    | eps                       $$ FIRST_PLUS = esac
    
    *** FIRST: object_id 
    *** FOLLOW: object_id | esac | FOLLOW(MORE_CASE_ARGS)
    CASE_ARG -> object_id : type_id => EXPR ;        $$ FIRST_PLUS = object_id

"""
