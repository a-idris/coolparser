import shlex
import sys

#first, follow, firstplus
#recursive descent class - if valid, store. recursive descent method - if valid, store.
#if valid, print stored


def parse(filename):
    
    #open file
    with open(filename) as f:
        inputfile = f.read()
        lexer = shlex.shlex(inputfile)
        # set global pointer, manipulating w/ getToken
        #stream tokens to parse method

    #for more accurate error reporting can loop over readline, maintaine line num. char within shlex gives index

    start()

def getToken():
    #regexps
    #candidate string, switch w/ lexeme types. pass lexeme type?

    #list, precompiled regexes. get string token from shlex then pass it thru, returnign lex error if necessary else returning an ecncoding of a token type

def start():
    """
    Name -> [A-Z][A-Za-z0-9] 
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
    METHOD ->  Id '(' ARGSLIST ')' 
    ARGSLIST -> ARG ARGSLIST | eps
    ARG -> Id ':' Type

    """

if __name__ == "__main__":
    import sys
    parse(sys.argv[1])
