import sys
import shlex
import cool_lexer
from cool_lexer import next_token
from cool_lexer import peek_token
from cool_lexer import Token


# init global vars
token = Token('', '', 0, 0, '')
classes = []  # keeps track of the summaries for each parsed class so far
class_methods = []  # keeps track of methods while parsing a class
errors = []  # keeps track of errors

FIRST_PLUS = {}
FOLLOW = {}
FIRST = {}

"""
def next_token(lexer):
    global token
    try:
        token = cool_lexer.next_token(lexer)
    except cool_lexer.LexError:
        errors.append("Lexical error. Unrecognized token = {0}".format(token))
        next_token(lexer)  # keep trying until a valid token is found
"""


def parse(filename):
    with open(filename) as f:
        lexer = shlex.shlex(f)
        # split only on newlines
        lexer.whitespace = '\r\n'
        lexer.whitespace_split = True

        # disable shlex quote behaviour
        lexer.quotes = ''

        global token
        token = next_token(lexer)

        # program(lexer)
        # if len(errors) == 0:
        #
        if program(lexer):
            print("No errors found")
            for class_summary in classes:
                print(class_summary)
        else:
            print("Errors found")
            for error in errors:
                print(error)


def error_msg(incorrect_token, *expected_tokens):
    error = "Unexpected token '{0}' on line {1}, column {2}. Expected one of: \n".format(incorrect_token.val,
                                                                                         incorrect_token.line_no,
                                                                                         incorrect_token.column_index)
    for expected_token in expected_tokens:
        error += expected_token + ", "
    error = error[:-2] + "\n"  # remove last comma
    error += incorrect_token.line
    error += "\n"
    for index, char in enumerate(incorrect_token.line):
        if index == incorrect_token.column_index:
            error += "^"
            break
        elif char == "\t":
            error += "\t"
        else:
            error += " "
    return error


"""
def recover1(lexer, first, follow):
    global token
    while token.name not in first and token.name not in follow and token.name != "eof":
        token = next_token(lexer)
    if token.name in first:
        # continue trying to parse the nt
        return True
    elif token.name in follow:
        # return from this nt and go to parent
        return False
    elif token.name == "eof":
        # ret false? haven't recovered?
        # in case eof is in the follow set, it will be discovered in the previous elif.
        return False


#def match(lexer, follow, *terminals, first_plus=None):
def match1(lexer, first, follow, *terminals):
    global token
    for terminal in terminals:
        if token.name == terminal:
            token = next_token(lexer)
            return
    # no terminal matched.
    error = error_msg(token, terminals)
    errors.append(error)
    # recover
    return recover(lexer, first, follow)
    # need nt state.
    if first_plus is not None:
        return recover(lexer, first_plus, follow)
    else:
        return recover(lexer, terminals, follow)
"""


def recover(lexer, follow, first=None):
    global token
    while token.name not in first and token.name not in follow and token.name != "eof":
        token = next_token(lexer)
    if token.name in first:
        # continue trying to parse the nt
        return True
    elif token.name in follow:
        # return from this nt and go to parent
        return False
    elif token.name == "eof":
        # ret false? haven't recovered?
        # in case eof is in the follow set, it will be discovered in the previous elif.
        return False


def match(lexer, follow, *terminals):
    global token
    for terminal in terminals:
        if token.name == terminal:
            return True
    # no terminal matched.
    error = error_msg(token, terminals)
    errors.append(error)
    # recover
    return recover(lexer, follow, first=terminals)


def recover_first(lexer, first, follow):
    error = error_msg(token, first)
    errors.append(error)
    return recover(lexer, follow, first=first)


def is_in_follow(nonterminal):
    return token.name in FOLLOW[nonterminal]


# use return value of false from a nonterminal to indicate that eof has been reached (prematurely).
# thus, if match

FIRST['program'] = ['class']
FOLLOW['program'] = ['eof']


def program(lexer):
    """
    *** FIRST: class
    *** FOLLOW: eof
    PROGRAM -> CLASS ; PROGRAM_REST                 $$ FIRST_PLUS = class
    """
    global token
    # for single first plus rules also need to do: if token.name == class. FOR ERR HANDLING
    if _class(lexer):
        if not match(lexer, FOLLOW['program'], ";"):
            return is_in_follow('program')
        else:
            #successful match
            token = next_token(lexer)
            if program_rest(lexer):
                return True
    return False


FIRST['program_rest'] = ['class', 'eof']
FOLLOW['program_rest'] = ['eof']


def program_rest(lexer):
    """
    *** FIRST: class | eps
    *** FOLLOW: eof
    PROGRAM_REST -> PROGRAM                         $$ FIRST_PLUS = class
                |   eps                             $$ FIRST_PLUS = eof
    """
    global token
    if token.name == "class":
        return program(lexer)
    elif token.name == "eof":
        return True
    else:
        if not recover_first(lexer, FIRST["program_rest"], FOLLOW["program_rest"]):
            return is_in_follow('program_rest')
        else:
            return program_rest(lexer)


FIRST['class'] = ['class']
FOLLOW['class'] = [';']


def _class(lexer):
    """
    *** FIRST: class
    *** FOLLOW: ;
    CLASS -> class type_id CLASS_TYPE { FEATURE_LIST }        $$ FIRST_PLUS = class
    """
    global token
    if not match(lexer, FOLLOW['class'], "class"):
        # if FOLLOW reached, parent can continue
        return is_in_follow('class')
    else:
        # successful match
        token = next_token(lexer)
        if not match(lexer, FOLLOW['class', "type_id"]):
            return is_in_follow('class')
        else:
            class_name = token.val
            class_methods.clear()

            token = next_token(lexer)

            if class_type(lexer):
                if not match(lexer, FOLLOW['class'], "{"):
                    return is_in_follow('class')
                else:
                    token = next_token(lexer)
                    if feature_list(lexer):
                        if not match(lexer, FOLLOW['class'], "}"):
                            return is_in_follow('class')
                        else:
                            token = next_token(lexer)

                            # generate class summary
                            class_summary = class_name + ": "
                            for method in class_methods:
                                class_summary += method + ", "
                            # slice last comma off and add to classes
                            classes.append(class_summary[:-2])
                            return True
    return False


FIRST['class_type'] = ['inherits', '{']
FOLLOW['class_type'] = ['{']


def class_type(lexer):
    """
    *** FIRST: inherits | eps
    *** FOLLOW: {
    CLASS_TYPE -> inherits type_id                  $$ FIRST_PLUS = inherits
            | eps                                   $$ FIRST_PLUS = {
    """
    global token
    if token.name == "inherits":
        token = next_token(lexer)
        if not match(lexer, FOLLOW['class_type'], "type_id"):
            return is_in_follow('class_type')
        else:
            token = next_token(lexer)
            return True
    elif token.name == "{":
        return True
    else:
        if not recover_first(lexer, FIRST['class_type'], FOLLOW['class_type']):
            return is_in_follow('class_type')
        else:
            return class_type(lexer)


FIRST['feature_list'] = ['object_id', '}']
FOLLOW['feature_list'] = ['}']


def feature_list(lexer):
    """
    * FIRST: object_id | eps
    * FOLLOW: }
    FEATURE_LIST -> FEATURE ; FEATURE_LIST                  $$ FIRST_PLUS = object_id
                | eps                                       $$ FIRST_PLUS = }
    """
    global token
    if token.name == "object_id":
        if feature(lexer):
            if token.name == ";":
                token = next_token(lexer)
                return feature_list(lexer)
    elif token.name == "}":
        return True
    else:
        if not recover_first(lexer, FIRST['feature_list'], FOLLOW['feature_list']):
            return is_in_follow('feature_list')
        else:
            return feature_list(lexer)


FIRST['feature'] = ['object_id']
FOLLOW['feature'] = [';']


def feature(lexer):
    """
    * FIRST: object_id
    * FOLLOW: ;
    FEATURE -> object_id FEATURE_REST               $$ FIRST_PLUS = object_id
    """
    global token
    if not match(lexer, FOLLOW['feature'], "object_id"):
        return is_in_follow('feature')
    else:
        feature_id = token.val
        token = next_token(lexer)
        is_valid_feature_rest, feature_type = feature_rest(lexer)
        if feature_type == "method":
            class_methods.append(feature_id)
        return is_valid_feature_rest


FIRST['feature_rest'] = ['(', ':']
FOLLOW['feature_rest'] = [';']


def feature_rest(lexer):
    """
    * FIRST: ( | :
    * FOLLOW: ;
    FEATURE_REST -> ( OPT_FEATURE_ARGS ) : type_id { EXPR }    $$ FIRST_PLUS = (
                |   : type_id OPT_EXPR_ASSIGNMENT              $$ FIRST_PLUS = :
    """
    global token
    if token.name == "(":
        token = next_token(lexer)
        if opt_feature_args(lexer):
            if not match(lexer, FOLLOW['feature_rest'], ")"):
                return is_in_follow('feature_rest')
            else:
                token = next_token(lexer)
                if not match(lexer, FOLLOW['feature_rest'], ":"):
                    return is_in_follow('feature_rest')
                else:
                    token = next_token(lexer)
                    if not match(lexer, FOLLOW['feature_rest'], "type_id"):
                        return is_in_follow('feature_rest')
                    else:
                        token = next_token(lexer)
                        if not match(lexer, FOLLOW['feature_rest'], "{"):
                            return is_in_follow('feature_rest')
                        else:
                            token = next_token(lexer)
                            if expr(lexer):
                                if not match(lexer, FOLLOW['feature_rest'], "}"):
                                    return is_in_follow('feature_rest')
                                else:
                                    token = next_token(lexer)
                                    return True, "method"
    elif token.name == ":":
        token = next_token(lexer)
        if not match(lexer, FOLLOW['feature_rest'], "type_id"):
            return is_in_follow('feature_rest')
        else:
            token = next_token(lexer)
            return opt_expr_assignment(lexer), "attribute"
    else:
        if not recover_first(lexer, FIRST['feature_rest'], FOLLOW['rest']):
            return is_in_follow('feature_rest'), ""
        else:
            return feature_rest(lexer)


FIRST['opt_feature_args'] = ['object_id', ')']
FOLLOW['opt_feature_args'] = [')']


def opt_feature_args(lexer):
    """
    * FIRST: object_id | eps
    * FOLLOW: )
    OPT_FEATURE_ARGS -> FEATURE_ARGS                $$ FIRST_PLUS = object_id
                    | eps                           $$ FIRST_PLUS = )
    """
    global token
    if token.name == "object_id":
        return feature_args(lexer)
    elif token.name == ")":
        return True
    else:
        if not recover_first(lexer, FIRST['opt_feature_args'], FOLLOW['opt_feature_args']):
            return is_in_follow('opt_feature_args')
        else:
            return opt_feature_args(lexer)


FIRST['feature_args'] = ['object_id']
FOLLOW['feature_args'] = [')']


def feature_args(lexer):
    """
    * FIRST: object_id
    * FOLLOW: )
    FEATURE_ARGS -> FORMAL MORE_FEATURE_ARGS                  $$ FIRST_PLUS = object_id
    """
    global token
    if formal(lexer):
        return more_feature_args(lexer)
    return False


FIRST['more_feature_args'] = [',', ')']
FOLLOW['more_feature_args'] = [')']


def more_feature_args(lexer):
    """
    * FIRST: , | eps
    * FOLLOW: )
    MORE_FEATURE_ARGS -> , FORMAL MORE_FEATURE_ARGS         $$ FIRST_PLUS = ,
                     | eps                                  $$ FIRST_PLUS = )
    """
    global token
    if token.name == ",":
        token = next_token(lexer)
        if formal(lexer):
            return more_feature_args(lexer)
    elif token.name == ")":
        return True
    else:
        if not match(lexer, FIRST['more_feature_args'], FOLLOW['more_feature_args']):
            return is_in_follow('more_feature_args')
        else:
            return more_feature_args(lexer)
    return False


FIRST['opt_expr_assignment'] = ['<-', ';', ',', 'in']
FOLLOW['opt_expr_assignment'] = [';', ',', 'in']


def opt_expr_assignment(lexer):
    """
    * FIRST: <- | eps
    * FOLLOW: ; | , | in
    OPT_EXPR_ASSIGNMENT -> EXPR_ASSIGNMENT          $$ FIRST_PLUS = <-
                        | eps                       $$ FIRST_PLUS = ; | , | in
    """
    global token
    if token.name == "<-":
        return expr_assignment(lexer)
    elif token.name == ";" or token.name == "," or token.name == "in":
        return True
    else:
        if not match(lexer, FIRST['opt_expr_assignment'], FOLLOW['opt_expr_assignment']):
            return is_in_follow('opt_expr_assignment')
        else:
            return opt_expr_assignment(lexer)


FIRST['expr_assignment'] = ['<-']
FOLLOW['expr_assignment'] = [';', ',', 'in']


def expr_assignment(lexer):
    """
    * FIRST: <-
    * FOLLOW: ; | , | in
    EXPR_ASSIGNMENT -> <- EXPR                      $$ FIRST_PLUS = <-
    """
    global token
    if not match(lexer, FOLLOW['expr_assignment'], "<-"):
        return is_in_follow('expr_assignment')
    else:
        token = next_token(lexer)
        return expr(lexer)


FIRST['formal'] = ['object_id']
FOLLOW['formal'] = [',', ')']


def formal(lexer):
    """
    * FIRST: object_id
    * FOLLOW: , | )
    FORMAL -> object_id : type_id                   $$ FIRST_PLUS = object_id
    """
    global token
    if not match(lexer, FOLLOW['formal'], "object_id"):
        return is_in_follow('formal')
    else:
        token = next_token(lexer)
        if not match(lexer, FOLLOW['formal'], ":"):
            return is_in_follow('formal')
        else:
            token = next_token(lexer)
            if not match(lexer, FOLLOW['formal'], "type_id"):
                return is_in_follow('formal')
            else:
                token = next_token(lexer)
                return True


FIRST['expr'] = ['']
FOLLOW['expr'] = ['']


def expr(lexer):
    """
    * FIRST: object_id | integer | string | true | false | ( | if | while | { | let | case | new | ~ | isvoid | not
    * FOLLOW: } | ; | in | ) | then | else | fi | loop | pool | of | ,
    EXPR -> ID <- EXPR                     $$ FIRST_PLUS = object_id
        |   BOOLEAN_COMPLEMENT_EXPR        $$ FIRST_PLUS = integer | string | true | false | ( | object_id | if |
                                                           while | { | let | case | new | ~ | isvoid | not
    """
    global token
    if token.name == "object_id":
        # there is FIRST+ conflict for token object_id.
        # peek_token preserves the token so that the next call to next_token will return the same token
        peek = peek_token(lexer)
        if peek.name == '<-':
            if _id(lexer):
                if token.name == "<-":
                    token = next_token(lexer)
                    return expr(lexer)
        else:
            return boolean_complement_expr(lexer)
    elif token.name in ["integer", "string", "true", "false", "(", "if", "while", "{", "let", "case", "new", "~",
                        "isvoid", "not"]:
        return boolean_complement_expr(lexer)

    raise Exception


FIRST['boolean_complement_expr'] = ['']
FOLLOW['boolean_complement_expr'] = ['']


def boolean_complement_expr(lexer):
    """
    * FIRST: integer | string | true | false | ( | object_id | if | while | { | let | case | new | ~ | isvoid | not
    * FOLLOW: } | ; | in | ) | then | else | fi | loop | pool | of | ,
    BOOLEAN_COMPLEMENT_EXPR -> not BOOLEAN_COMPLEMENT_EXPR 		$$ FIRST_PLUS = not
                            | COMPARISON_EXPR                   $$ FIRST_PLUS = integer | string | true | false | ( |
                                                                   | object_id | if | while | { | let | case | new | ~ | isvoid
    """
    global token
    if token.name == "not":
        token = next_token(lexer)
        return boolean_complement_expr(lexer)
    elif token.name in ['integer', 'string', 'true', 'false', '(', 'object_id', 'if', 'while', '{', 'let', 'case',
                        'new', '~', 'isvoid']:
        return comparison_expr(lexer)
    raise Exception


FIRST['comparison_expr'] = ['']
FOLLOW['comparison_expr'] = ['']


def comparison_expr(lexer):
    """
    * FIRST: integer | string | true | false | ( | object_id | if | while | { | let | case | new | ~ | isvoid
    * FOLLOW: } | ; | in | ) | then | else | fi | loop | pool | of | ,
    COMPARISON_EXPR -> ADD_EXPR COMPARISON_OP    $$ FIRST_PLUS = integer | string | true | false | ( | object_id
                                                    | if | while | { | let | case | new | ~ | isvoid
    :param lexer:
    :return:
    """
    global token
    if add_expr(lexer):
        return comparison_op(lexer)


FIRST['comparison_op'] = ['']
FOLLOW['comparison_op'] = ['']


def comparison_op(lexer):
    """
    * FIRST: <= | < | = | eps
    * FOLLOW: } | ; | in | ) | then | else | fi | loop | pool | of | ,
    COMPARISON_OP -> <= ADD_EXPR COMPARISON_OP           		$$ FIRST_PLUS = <=
                  |  < ADD_EXPR COMPARISON_OP            		$$ FIRST_PLUS = <
                  |  = ADD_EXPR COMPARISON_OP            		$$ FIRST_PLUS = =
                  |  eps                                        $$ FIRST_PLUS = } | ; | in | ) | then | else | fi |
                                                                                | loop | pool | of | ,
    """
    global token
    if token.name == "<=":
        token = next_token(lexer)
        if add_expr(lexer):
            return comparison_op(lexer)
    elif token.name == "<":
        token = next_token(lexer)
        if add_expr(lexer):
            return comparison_op(lexer)
    elif token.name == "=":
        token = next_token(lexer)
        if add_expr(lexer):
            return comparison_op(lexer)
    elif token.name in ['}', ';', 'in', ')', 'then', 'else', 'fi', 'loop', 'pool', 'of', ',']:
        return True
    raise Exception


FIRST['add_expr'] = ['']
FOLLOW['add_expr'] = ['']


def add_expr(lexer):
    """

    * FIRST: integer | string | true | false | ( | object_id | if | while | { | let | case | new | ~ | isvoid
    * FOLLOW: <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    ADD_EXPR -> MULT_EXPR ADD_OP              $$ FIRST_PLUS = integer | string | true | false | ( | object_id | if
                                                            | while | { | let | case | new | ~ | isvoid
    """
    global token
    if mult_expr(lexer):
        return add_op(lexer)


FIRST['add_op'] = ['']
FOLLOW['add_op'] = ['']


def add_op(lexer):
    """
    * FIRST: + | - | eps
    * FOLLOW: <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    ADD_OP -> + MULT_EXPR ADD_OP                     $$ FIRST_PLUS = +
             |  - MULT_EXPR ADD_OP                   $$ FIRST_PLUS = -
             |  eps                                  $$ FIRST_PLUS = <= | < | = | } | ; | in | ) | then | else | fi
                                                                    | loop | pool | of | ,
    """
    global token
    if token.name == "+":
        token = next_token(lexer)
        if mult_expr(lexer):
            return add_op(lexer)
    elif token.name == "-":
        token = next_token(lexer)
        if mult_expr(lexer):
            return add_op(lexer)
    elif token.name in ['<=', '<', '=', '}', ';', 'in', ')', 'then', 'else', 'fi', 'loop', 'pool', 'of', ',']:
        return True
    raise Exception


FIRST['mult_expr'] = ['']
FOLLOW['mult_expr'] = ['']


def mult_expr(lexer):
    """
    * FIRST: integer | string | true | false | ( | object_id | if | while | { | let | case | new | ~ | isvoid
    * FOLLOW: + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    MULT_EXPR -> CHECKVOID_EXPR MULT_OP                   $$ FIRST_PLUS = integer | string | true | false | ( |
                                                            | object_id | if | while | { | let | case | new | ~ | isvoid
    """
    global token
    if checkvoid_expr(lexer):
        return mult_op(lexer)


FIRST['mult_op'] = ['']
FOLLOW['mult_op'] = ['']


def mult_op(lexer):
    """
    * FIRST: * | / | eps
    * FOLLOW: + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , | FOLLOW(ELEMENT)
    MULT_OP -> * CHECKVOID_EXPR MULT_OP                      $$ FIRST_PLUS = *
             | / CHECKVOID_EXPR MULT_OP                      $$ FIRST_PLUS = /
             | eps                                      	 $$ FIRST_PLUS = + | - | <= | < | = | } | ; | in | ) | then |
                                                                            | else | fi | loop | pool | of | ,
    """
    global token
    if token.name == "*":
        token = next_token(lexer)
        if checkvoid_expr(lexer):
            return mult_op(lexer)
    elif token.name == "/":
        token = next_token(lexer)
        if checkvoid_expr(lexer):
            return mult_op(lexer)
    elif token.name in ['+', '-', '<=', '<', '=', '}', ';', 'in', ')', 'then', 'else', 'fi', 'loop', 'pool', 'of', ',']:
        return True
    raise Exception


FIRST['checkvoid_expr'] = ['']
FOLLOW['checkvoid_expr'] = ['']


def checkvoid_expr(lexer):
    """
    * FIRST: integer | string | true | false | ( | object_id | if | while | { | let | case | new | ~ | isvoid
    * FOLLOW: * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    CHECKVOID_EXPR -> isvoid CHECKVOID_EXPR                  $$ FIRST_PLUS = isvoid
                   | INTEGER_COMPLEMENT_EXPR                 $$ FIRST_PLUS = integer | string | true | false | ( |
                                                                    | object_id | if | while | { | let | case | new | ~
    """
    global token
    if token.name == "isvoid":
        token = next_token(lexer)
        return checkvoid_expr(lexer)
    elif token.name in ['integer', 'string', 'true', 'false', '(', 'object_id', 'if', 'while', '{', 'let', 'case',
                        'new', '~']:
        return integer_complement_expr(lexer)
    raise Exception


FIRST['integer_complement_expr'] = ['']
FOLLOW['integer_complement_expr'] = ['']


def integer_complement_expr(lexer):
    """
   * FIRST: integer | string | true | false | ( | object_id | if | while | { | let | case | new | ~
    * FOLLOW: * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    INTEGER_COMPLEMENT_EXPR -> ~ INTEGER_COMPLEMENT_EXPR          $$ FIRST_PLUS = ~
                            | DISPATCH_EXPR                       $$ FIRST_PLUS =  integer | string | true | false | ( |
                                                                    | object_id | if | while | { | let | case | new
    """
    global token
    if token.name == "~":
        token = next_token(lexer)
        return integer_complement_expr(lexer)
    elif token.name in ['integer', 'string', 'true', 'false', '(', 'object_id', 'if', 'while', '{', 'let', 'case',
                        'new']:
        return dispatch_expr(lexer)
    raise Exception


FIRST['dispatch_expr'] = ['']
FOLLOW['dispatch_expr'] = ['']


def dispatch_expr(lexer):
    """
    * FIRST: integer | string | true | false | ( | object_id | if | while | { | let | case | new
    * FOLLOW: * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    DISPATCH_EXPR -> ELEMENT DISPATCH_OP               $$ FIRST_PLUS = integer | string | true | false | ( | object_id |
                                                                        | if | while | { | let | case | new
    """
    global token
    if element(lexer):
        return dispatch_op(lexer)
    raise Exception


FIRST['dispatch_op'] = ['']
FOLLOW['dispatch_op'] = ['']


def dispatch_op(lexer):
    """
    * FIRST: @ | . | eps
    * FOLLOW: * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    DISPATCH_OP -> DISPATCH_TYPE . object_id ( OPT_EXPR_ARGS ) DISPATCH_OP    $$ FIRST_PLUS = @ | .
                | eps                                                         $$ FIRST_PLUS = * | / | + | - | <= | < | = | }
                                                                        | ; | in | ) | then | else | fi | loop | pool | of | ,
    """
    global token
    if token.name == "@" or token.name == ".":
        if dispatch_type(lexer):
            if token.name == ".":
                token = next_token(lexer)
                if token.name == "object_id":
                    token = next_token(lexer)
                    if token.name == "(":
                        token = next_token(lexer)
                        if opt_expr_args(lexer):
                            if token.name == ")":
                                token = next_token(lexer)
                                return dispatch_op(lexer)
    elif token.name in ['*', '/', '+', '-', '<=', '<', '=', '}', ';', 'in', ')', 'then', 'else', 'fi', 'loop',
                        'pool', 'of', ',']:
        return True
    raise Exception


FIRST['dispatch_type'] = ['']
FOLLOW['dispatch_type'] = ['']


def dispatch_type(lexer):
    """
    * FIRST: @ | eps
    * FOLLOW: .
    DISPATCH_TYPE -> @ type_id                $$ FIRST_PLUS = @
                    | eps                     $$ FIRST_PLUS = .
    """
    global token
    if token.name == "@":
        token = next_token(lexer)
        if token.name == "type_id":
            token = next_token(lexer)
            return True
    elif token.name == '.':
        return True
    raise Exception


FIRST['element'] = ['']
FOLLOW['element'] = ['']


def element(lexer):
    """
    * FIRST: integer | string | true | false | ( | object_id | if | while | { | let | case | new
    * FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    ELEMENT -> CONSTANT                                             $$ FIRST_PLUS = integer | string | true | false
            | ( EXPR )                                              $$ FIRST_PLUS = (
            |  ID ID_OP                                             $$ FIRST_PLUS = object_id
            |   if EXPR then EXPR else EXPR fi                      $$ FIRST_PLUS = if
            |   while EXPR loop EXPR pool                           $$ FIRST_PLUS = while
            |   { EXPR_LIST }                                       $$ FIRST_PLUS = {
            |   let LET_ARGS in EXPR                                $$ FIRST_PLUS = let
            |   case EXPR of CASE_ARGS esac                         $$ FIRST_PLUS = case
            |   new type_id                                         $$ FIRST_PLUS = new
    """
    global token
    if token.name in ['integer', 'string', 'true', 'false']:
        return constant(lexer)
    elif token.name == "(":
        token = next_token(lexer)
        if expr(lexer):
            if token.name == ")":
                token = next_token(lexer)
                return True
    elif token.name == 'object_id':
        if _id(lexer):
            return id_op(lexer)
    elif token.name == "if":
        token = next_token(lexer)
        if expr(lexer):
            if token.name == "then":
                token = next_token(lexer)
                if expr(lexer):
                    if token.name == "else":
                        token = next_token(lexer)
                        if expr(lexer):
                            if token.name == "fi":
                                token = next_token(lexer)
                                return True
    elif token.name == "while":
        token = next_token(lexer)
        if expr(lexer):
            if token.name == "loop":
                token = next_token(lexer)
                if expr(lexer):
                    if token.name == "pool":
                        token = next_token(lexer)
                        return True
    elif token.name == "{":
        token = next_token(lexer)
        if expr_list(lexer):
            if token.name == "}":
                token = next_token(lexer)
                return True
    elif token.name == "let":
        token = next_token(lexer)
        if let_args(lexer):
            if token.name == "in":
                token = next_token(lexer)
                return expr(lexer)
    elif token.name == "case":
        token = next_token(lexer)
        if expr(lexer):
            if token.name == "of":
                token = next_token(lexer)
                if case_args(lexer):
                    if token.name == "esac":
                        token = next_token(lexer)
                        return True
    elif token.name == "new":
        token = next_token(lexer)
        if token.name == "type_id":
            token = next_token(lexer)
            return True
    raise Exception


FIRST['constant'] = ['']
FOLLOW['constant'] = ['']


def constant(lexer):
    """
    * FIRST: integer | string | true | false
    * FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    CONSTANT -> integer                                 $$ FIRST_PLUS = integer
            | string                                    $$ FIRST_PLUS = string
            | true                                      $$ FIRST_PLUS = true
            | false                                     $$ FIRST_PLUS = false
    """
    global token
    if token.name == "integer":
        token = next_token(lexer)
        return True
    elif token.name == "string":
        token = next_token(lexer)
        return True
    elif token.name == "true":
        token = next_token(lexer)
        return True
    elif token.name == "false":
        token = next_token(lexer)
        return True
    raise Exception


FIRST['_id'] = ['']
FOLLOW['_id'] = ['']


def _id(lexer):
    """
    * FIRST: object_id
    * FOLLOW: ( | <- | . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    ID -> object_id                                     $$ FIRST_PLUS = object_id
    """
    global token
    if token.name == "object_id":
        token = next_token(lexer)
        return True
    raise Exception


FIRST['id_op'] = ['']
FOLLOW['id_op'] = ['']


def id_op(lexer):
    """
    * FIRST: ( | eps
    * FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    ID_OP -> ( OPT_EXPR_ARGS )                       $$ FIRST_PLUS = (
           | eps                                     $$ FIRST_PLUS = . | @ | * | / | + | - | <= | < | = | } | ; |
                                                                   | in | ) | then | else | fi | loop | pool | of | ,
    """
    global token
    if token.name == "(":
        token = next_token(lexer)
        if opt_expr_args(lexer):
            if token.name == ")":
                token = next_token(lexer)
                return True
    elif token.name in ['.', '@', '*', '/', '+', '-', '<=', '<', '=', '}', ';', 'in', ')', 'then', 'else', 'fi',
                        'loop','pool', 'of', ',']:
        return True
    raise Exception


FIRST['opt_expr_args'] = ['']
FOLLOW['opt_expr_args'] = ['']


def opt_expr_args(lexer):
    """
    * FIRST: object_id | integer | string | true | false | ( | ~ | isvoid | not | if | while | { | let | case | new | eps
    * FOLLOW: )
    OPT_EXPR_ARGS -> EXPR_ARGS                    $$ FIRST_PLUS = object_id | integer | string | true | false | ( | ~ |
                                                                | isvoid | not | if | while | { | let | case | new
                    | eps                         $$ FIRST_PLUS = )
    """
    global token
    if token.name in ['object_id', 'integer', 'string', 'true', 'false', '(', '~', 'isvoid', 'not', 'if', 'while',
                      '{', 'let', 'case', 'new']:
        return expr_args(lexer)
    elif token.name == ")":
        return True
    raise Exception


FIRST['expr_args'] = ['']
FOLLOW['expr_args'] = ['']


def expr_args(lexer):
    """
    * FIRST: object_id | integer | string | true | false | ( | ~ | isvoid | not | if | while | { | let | case | new
    * FOLLOW: )
    EXPR_ARGS -> EXPR MORE_EXPR_ARGS              $$ FIRST_PLUS = object_id | integer | string | true | false | ( | ~ |
                                                              | isvoid | not | if | while | { | let | case | new
    """
    global token
    if expr(lexer):
        return more_expr_args(lexer)
    raise Exception


FIRST['more_expr_args'] = ['']
FOLLOW['more_expr_args'] = ['']


def more_expr_args(lexer):
    """
    * FIRST: , | eps
    * FOLLOW: )
    MORE_EXPR_ARGS -> , EXPR MORE_EXPR_ARGS             $$ FIRST_PLUS = ,
                | eps                                   $$ FIRST_PLUS = )
    """
    global token
    if token.name == ",":
        token = next_token(lexer)
        if expr(lexer):
            return more_expr_args(lexer)
        else:
            error_msg("more_expr_args", lexer)
    elif token.name == ")":
        return True
    else:
        error_msg("more_expr_args", lexer)
        return False
    raise Exception


FIRST['expr_list'] = ['']
FOLLOW['expr_list'] = ['']


def expr_list(lexer):
    """
    * FIRST: object_id | integer | string | true | false | ( | ~ | isvoid | not | if | while | { | let | case | new
    * FOLLOW: }
    EXPR_LIST -> EXPR ; MORE_EXPRs              $$ FIRST_PLUS = object_id | integer | string | true | false | ( |
                                                                | ~ | isvoid | not | if | while | { | let | case | new
    """
    global token
    if expr(lexer):
        if token.name ==";":
            token = next_token(lexer)
            return more_exprs(lexer)
    raise Exception


FIRST['more_exprs'] = ['']
FOLLOW['more_exprs'] = ['']


def more_exprs(lexer):
    """
    * FIRST: object_id | integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid | not | eps
    * FOLLOW: }
    MORE_EXPRS -> EXPR_LIST                   $$ FIRST_PLUS = object_id | integer | string | true | false | (
                                                             | ~ | isvoid | not | if | while | { | let | case | new
                | eps                         $$ FIRST_PLUS = }
    """
    global token
    if token.name in ['object_id', 'integer', 'string', 'true', 'false', '(', '~', 'isvoid', 'not', 'if', 'while',
                      '{', 'let', 'case', 'new']:
        return expr_list(lexer)
    elif token.name == "}":
        return True
    raise Exception


FIRST['let_args'] = ['']
FOLLOW['let_args'] = ['']


def let_args(lexer):
    """
    * FIRST: object_id
    * FOLLOW: in
    LET_ARGS ->  LET_ARG MORE_LET_ARGS                       $$ FIRST_PLUS = object_id
    """
    global token
    if let_arg(lexer):
        return more_let_args(lexer)
    raise Exception


FIRST['more_let_args'] = ['']
FOLLOW['more_let_args'] = ['']


def more_let_args(lexer):
    """
    * FIRST: , | eps
    * FOLLOW: in
    MORE_LET_ARGS -> , LET_ARG MORE_LET_ARGS                    $$ FIRST_PLUS = ,
                | eps                                           $$ FIRST_PLUS = in
    """
    global token
    if token.name == ",":
        token = next_token(lexer)
        if let_arg(lexer):
            return more_let_args(lexer)
    elif token.name == "in":
        return True
    raise Exception


FIRST['let_arg'] = ['']
FOLLOW['let_arg'] = ['']


def let_arg(lexer):
    """
    * FIRST: object_id
    * FOLLOW: , | in
    LET_ARG -> object_id : type_id OPT_EXPR_ASSIGNMENT   $$ FIRST_PLUS = object_id
    """
    global token
    if token.name == "object_id":
        token = next_token(lexer)
        if token.name == ":":
            token = next_token(lexer)
            if token.name == "type_id":
                token = next_token(lexer)
                return opt_expr_assignment(lexer)
    raise Exception


FIRST['case_args'] = ['']
FOLLOW['case_args'] = ['']


def case_args(lexer):
    """
    * FIRST: object_id
    * FOLLOW: esac
    CASE_ARGS -> CASE_ARG MORE_CASE_ARGS            $$ FIRST_PLUS = object_id
    """
    global token
    if case_arg(lexer):
        return more_case_args(lexer)
    raise Exception


FIRST['more_case_args'] = ['']
FOLLOW['more_case_args'] = ['']


def more_case_args(lexer):
    """
    * FIRST: object_id | eps
    * FOLLOW: esac
    MORE_CASE_ARGS -> CASE_ARGS                 $$ FIRST_PLUS = object_id
                    | eps                       $$ FIRST_PLUS = esac
    """
    global token
    if token.name == "object_id":
        return case_args(lexer)
    elif token.name == "esac":
        return True
    raise Exception


FIRST['case_arg'] = ['']
FOLLOW['case_arg'] = ['']


def case_arg(lexer):
    """
    * FIRST: object_id
    * FOLLOW: object_id | esac
    CASE_ARG -> object_id : type_id => EXPR ;        $$ FIRST_PLUS = object_id
    """
    global token
    if token.name == "object_id":
        token = next_token(lexer)
        if token.name == ":":
            token = next_token(lexer)
            if token.name == "type_id":
                token = next_token(lexer)
                if token.name == "=>":
                    token = next_token(lexer)
                    if expr(lexer):
                        if token.name == ";":
                            token = next_token(lexer)
                            return True
    else:
        error = "Unexpected token {0} on line {1}, column {2}. Expected one of: object_id".format(token.val, '', '')
        return False


if __name__ == "__main__":
    parse(sys.argv[1])
