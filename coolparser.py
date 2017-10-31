import sys
import shlex
import cool_lexer
from cool_lexer import next_token
from cool_lexer import Token


token = Token('', '')


def parse(filename):
    # open file
    with open(filename) as f:
        input_file = f.read()
        lexer = shlex.shlex(input_file)
        lexer.whitespace_split = True
        lexer.quotes = ''  # disable shlex quote behaviour

        global token
        token = next_token(lexer)

        if program(lexer):
            print("No errors found")
        else:
            print("Errors found")


def program(lexer):
    global token
    if _class(lexer):
        if token.name == ";":
            token = next_token(lexer)
            if program_rest(lexer):
                return True
    return False


def program_rest(lexer):
    global token
    if token.name == "class":
        return program(lexer)
    elif token.name == "eof":
        return True
    return False


def _class(lexer):
    global token
    if token.name == "class":
        token = next_token(lexer)
        if token.name == "type_id":
            token = next_token(lexer)
            # if begins w/ inherits. else if begins w/ {
            if class_type(lexer):
                if token.name == "{":
                    token = next_token(lexer)
                    if feature_list(lexer):
                        if token.name == "}":
                            token = next_token(lexer)
                            return True
    return False


def class_type(lexer):
    global token
    print(token)
    if token.name == "inherits":
        token = next_token(lexer)
        if token.name == "type_id":
            token = next_token(lexer)
            return True
    elif token.name == "{":
        return True
    return False


def feature_list(lexer):
    global token
    if token.name == "object_id":
        if feature(lexer):
            if token.name == ";":
                token = next_token(lexer)
                return feature_list(lexer)
    elif token.name == "}":
        return True
    return False


def feature(lexer):
    global token
    if token.name == "object_id":
        token = next_token(lexer)
        return feature_rest(lexer)
    return False


def feature_rest(lexer):
    global token
    if token.name == "(":
        token = next_token(lexer)
        if opt_feature_args(lexer):
            if token.name == ")":
                token = next_token(lexer)
                if token.name == ":":
                    token = next_token(lexer)
                    if token.name == "type_id":
                        token = next_token(lexer)
                        if token.name == "{":
                            token = next_token(lexer)
                            if expr(lexer):
                                if token.name == "}":
                                    token = next_token(lexer)
                                    return True
    elif token.name == ":":
        token = next_token(lexer)
        if token.name == "type_id":
            token = next_token(lexer)
            return opt_expr_assignment(lexer)
    return False


def opt_feature_args(lexer):
    global token
    if token.name == "object_id":
        return feature_args(lexer)
    elif token.name == ")":
        return True
    return False


def feature_args(lexer):
    global token
    if formal(lexer):
        return more_feature_args(lexer)
    return False


def more_feature_args(lexer):
    global token
    if token.name == ",":
        token = next_token(lexer)
        if formal(lexer):
            return more_feature_args(lexer)
    elif token.name == ")":
        return True
    return False


def opt_expr_assignment(lexer):
    global token
    if token.name == "<-":
        return expr_assignment(lexer)
    elif token.name == ";" or token.name == "," or token.name == "in":
        return True
    return False


def expr_assignment(lexer):
    global token
    if token.name == "<-":
        token = next_token(lexer)
        return expr(lexer)
    return False


def formal(lexer):
    global token
    if token.name == "object_id":
        token = next_token(lexer)
        if token.name == ":":
            token = next_token(lexer)
            if token.name == "type_id":
                token = next_token(lexer)
                return True
    return False


def expr(lexer):
    global token
    if token.name == "object_id":
        if _id(lexer):
            return object_id_op(lexer)
    elif token.name in ["integer", "string", "true", "false", "(", "~", "isvoid", "not"]:
        return assignment_expr(lexer)
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
    return False


def _id(lexer):
    global token
    if token.name == "object_id":
        token = next_token(lexer)
        return True
    return False


# lineno, column, tokens expected


def object_id_op(lexer):
    global token
    if token.name == "(":
        token = next_token(lexer)
        if opt_expr_args(lexer):
            if token.name == ")":
                token = next_token(lexer)
                return True
    elif token.name == "<-":
        token = next_token(lexer)
        return expr(lexer)
    elif token.name in ['}', ';', 'in', ')', 'then', 'else', 'fi', 'loop', 'pool', 'of', ',']:
        return True
    return False


def assignment_expr(lexer):
    global token
    if token.name == "not":
        token = next_token(lexer)
        return boolean_complement_expr(lexer)
    elif token.name in ['integer', 'string', 'true', 'false', '(', '~', 'isvoid']:
        return boolean_complement_expr(lexer)
    return False


def boolean_complement_expr(lexer):
    global token
    if comparison_expr(lexer):
        return comparison_op(lexer)


def comparison_op(lexer):
    global token
    if token.name == "<=":
        token = next_token(lexer)
        if comparison_expr(lexer):
            return comparison_op(lexer)
    elif token.name == "<":
        token = next_token(lexer)
        if comparison_expr(lexer):
            return comparison_op(lexer)
    elif token.name == "=":
        token = next_token(lexer)
        if comparison_expr(lexer):
            return comparison_op(lexer)
    elif token.name in ['}', ';', 'in', ')', 'then', 'else', 'fi', 'loop', 'pool', 'of', ',']:
        return True
    return False


def comparison_expr(lexer):
    global token
    if add_expr(lexer):
        return add_op(lexer)


def add_op(lexer):
    global token
    if token.name == "+":
        token = next_token(lexer)
        if add_expr(lexer):
            return add_op(lexer)
    elif token.name == "-":
        token = next_token(lexer)
        if add_expr(lexer):
            return add_op(lexer)
    elif token.name in ['<=', '<', '=', '}', ';', 'in', ')', 'then', 'else', 'fi', 'loop', 'pool', 'of', ',']:
        return True
    return False


def add_expr(lexer):
    global token
    if mult_expr(lexer):
        return mult_op(lexer)


def mult_op(lexer):
    global token
    if token.name == "*":
        token = next_token(lexer)
        if mult_expr(lexer):
            return mult_op(lexer)
    elif token.name == "/":
        token = next_token(lexer)
        if mult_expr(lexer):
            return mult_op(lexer)
    elif token.name in ['+', '-', '<=', '<', '=', '}', ';', 'in', ')', 'then', 'else', 'fi', 'loop', 'pool', 'of', ',']:
        return True
    return False


def mult_expr(lexer):
    global token
    if token.name == "isvoid":
        token = next_token(lexer)
        return checkvoid_expr(lexer)
    elif token.name in ['integer', 'string', 'true', 'false', '(', '~']:
        return checkvoid_expr(lexer)
    return False


def checkvoid_expr(lexer):
    global token
    if token.name == "~":
        token = next_token(lexer)
        return integer_complement_expr(lexer)
    elif token.name in ['integer', 'string', 'true', 'false', '(']:
        return integer_complement_expr(lexer)
    return False


def integer_complement_expr(lexer):
    global token
    if dispatch_type_expr(lexer):
        return dispatch_type_op(lexer)
    return False


def dispatch_type_op(lexer):
    global token
    if token.name == "@":
        token = next_token(lexer)
        if token.name == "type_id":
            token = next_token(lexer)
            return True
    elif token.name in ['*', '/', '+', '-', '<=', '<', '=', '}', ';', 'in', ')', 'then', 'else', 'fi', 'loop', 'pool', 'of', ',']:
        return True
    return False


def dispatch_type_expr(lexer):
    global token
    if dispatch_expr(lexer):
        return dispatch_op(lexer)
    return False


def dispatch_op(lexer):
    global token
    if token.name == ".":
        token = next_token(lexer)
        if token.name == "object_id":
            token = next_token(lexer)
            if token.name == "(":
                token = next_token(lexer)
                if opt_expr_args(lexer):
                    if token.name == ")":
                        token = next_token(lexer)
                        return True
    elif token.name in ['@', '*', '/', '+', '-', '<=', '<', '=', '}', ';', 'in', ')', 'then', 'else', 'fi', 'loop', 'pool', 'of', ',']:
        return True
    return False


def dispatch_expr(lexer):
    global token
    if token.name in ['integer', 'string', 'true', 'false']:
        return constant(lexer)
    elif token.name == "(":
        token = next_token(lexer)
        if expr(lexer):
            if token.name == ")":
                token = next_token(lexer)
                return True
    return False


def constant(lexer):
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
    return False


def opt_expr_args(lexer):
    global token
    if token.name in ['object_id', 'integer', 'string', 'true', 'false', '(', '~', 'isvoid', 'not', 'if', 'while', '{', 'let', 'case', 'new']:
        return expr_args(lexer)
    elif token.name == ")":
        return True
    return False


def expr_args(lexer):
    global token
    if expr(lexer):
        return more_expr_args(lexer)
    return False


def more_expr_args(lexer):
    global token
    if token.name == ",":
        token = next_token(lexer)
        if expr(lexer):
            return more_expr_args(lexer)
    elif token.name == ")":
        return True
    return False


def expr_list(lexer):
    global token
    if expr(lexer):
        if token.name ==";":
            token = next_token(lexer)
            return more_exprs(lexer)
    return False


def more_exprs(lexer):
    global token
    if token.name in ['object_id', 'integer', 'string', 'true', 'false', '(', '~', 'isvoid', 'not', 'if', 'while', '{', 'let', 'case', 'new']:
        return expr_list(lexer)
    elif token.name == "}":
        return True
    return False


def let_args(lexer):
    global token
    if let_arg(lexer):
        return more_let_args(lexer)
    return False


def more_let_args(lexer):
    global token
    if token.name == ",":
        token = next_token(lexer)
        if let_arg(lexer):
            return more_let_args(lexer)
    elif token.name == "in":
        return True
    return False


def let_arg(lexer):
    global token
    if token.name == "object_id":
        token = next_token(lexer)
        if token.name == ":":
            token = next_token(lexer)
            if token.name == "type_id":
                token = next_token(lexer)
                return opt_expr_assignment(lexer)
    return False


def case_args(lexer):
    global token
    if case_arg(lexer):
        return more_case_args(lexer)
    return False


def more_case_args(lexer):
    global token
    if token.name == "object_id":
        return case_args(lexer)
    elif token.name == "esac":
        return True
    return False


def case_arg(lexer):
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
    return False


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
        
    *** FIRST: object_id | integer | string | true | false | ( | ~ | isvoid | not | if | while | { | let | case | new
    *** FOLLOW: } | ; | in | ) | then | else | fi | loop | pool | of | , 
    EXPR -> ID OBJECT_ID_OP                                     $$ FIRST_PLUS = object_id
        |   ASSIGNMENT_EXPR                                     $$ FIRST_PLUS = integer | string | true | false | ( | ~ | isvoid | not
        |   if EXPR then EXPR else EXPR fi                      $$ FIRST_PLUS = if
        |   while EXPR loop EXPR pool                           $$ FIRST_PLUS = while
        |   { EXPR_LIST }                                       $$ FIRST_PLUS = {
        |   let LET_ARGS in EXPR                                $$ FIRST_PLUS = let
        |   case EXPR of CASE_ARGS esac                         $$ FIRST_PLUS = case
        |   new type_id                                         $$ FIRST_PLUS = new

    *** FIRST: object_id 
    *** FOLLOW: ( | <- | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    ID -> object_id                                     $$ FIRST_PLUS = object_id

    *** FIRST: ( | <- | eps
    *** FOLLOW: } | ; | in | ) | then | else | fi | loop | pool | of | ,  
    OBJECT_ID_OP -> ( OPT_EXPR_ARGS )                           $$ FIRST_PLUS = (
                |   <- ASSIGNMENT_EXPR                          $$ FIRST_PLUS = <-
                |   eps                                         $$ FIRST_PLUS = } | ; | in | ) | then | else | fi | loop | pool | of | , 
            
    *** FIRST: integer | string | true | false | ( | ~ | isvoid | not 
    *** FOLLOW: } | ; | in | ) | then | else | fi | loop | pool | of | , 
    ASSIGNMENT_EXPR -> not BOOLEAN_COMPLEMENT_EXPR              $$ FIRST_PLUS = not
                    | BOOLEAN_COMPLEMENT_EXPR                   $$ FIRST_PLUS = integer | string | true | false | ( | ~ | isvoid 

    *** FIRST: integer | string | true | false | ( | ~ | isvoid 
    *** FOLLOW: } | ; | in | ) | then | else | fi | loop | pool | of | , 
    BOOLEAN_COMPLEMENT_EXPR -> COMPARISON_EXPR COMPARISON_OP    $$ FIRST_PLUS = integer | string | true | false | ( | ~ | isvoid 
    
    *** FIRST: <= | < | = | eps
    *** FOLLOW: } | ; | in | ) | then | else | fi | loop | pool | of | , 
    COMPARISON_OP -> <= COMPARISON_EXPR COMPARISON_OP           $$ FIRST_PLUS = <=
                  |  < COMPARISON_EXPR COMPARISON_OP            $$ FIRST_PLUS = < 
                  |  = COMPARISON_EXPR COMPARISON_OP            $$ FIRST_PLUS = =
                  |  eps                                        $$ FIRST_PLUS = } | ; | in | ) | then | else | fi | loop | pool | of | , 
                    
    *** FIRST: integer | string | true | false | ( | ~ | isvoid 
    *** FOLLOW: <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    COMPARISON_EXPR -> ADD_EXPR ADD_OP              $$ FIRST_PLUS = integer | string | true | false | ( | ~ | isvoid 
    
    *** FIRST: + | - | eps
    *** FOLLOW: <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    ADD_OP -> + ADD_EXPR ADD_OP                     $$ FIRST_PLUS = +
             |  - ADD_EXPR ADD_OP                   $$ FIRST_PLUS = - 
             |  eps                                 $$ FIRST_PLUS = <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
                
    *** FIRST: integer | string | true | false | ( | ~ | isvoid 
    *** FOLLOW: + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    ADD_EXPR -> MULT_EXPR MULT_OP                   $$ FIRST_PLUS = integer | string | true | false | ( | ~ | isvoid 
    
    *** FIRST: * | / | eps
    *** FOLLOW: + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    MULT_OP -> * MULT_EXPR MULT_OP                      $$ FIRST_PLUS = *
             | / MULT_EXPR MULT_OP                      $$ FIRST_PLUS = / 
             | eps                                      $$ FIRST_PLUS = + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 

    *** FIRST: integer | string | true | false | ( | ~ | isvoid 
    *** FOLLOW: * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    MULT_EXPR -> isvoid CHECKVOID_EXPR                  $$ FIRST_PLUS = isvoid
                | CHECKVOID_EXPR                        $$ FIRST_PLUS = integer | string | true | false | ( | ~
    
    *** FIRST: integer | string | true | false | ( | ~
    *** FOLLOW: * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    CHECKVOID_EXPR -> ~ INTEGER_COMPLEMENT_EXPR               $$ FIRST_PLUS = ~
                    | INTEGER_COMPLEMENT_EXPR                 $$ FIRST_PLUS =  integer | string | true | false | (  
    
    *** FIRST:  integer | string | true | false | (  
    *** FOLLOW: * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    INTEGER_COMPLEMENT_EXPR -> DISPATCH_TYPE_EXPR DISPATCH_TYPE_OP       $$ FIRST_PLUS =  integer | string | true | false | (  
    
    *** FIRST: @ | eps
    *** FOLLOW: * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    DISPATCH_TYPE_OP -> @ type_id                       $$ FIRST_PLUS = @
                      | eps                             $$ FIRST_PLUS = * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
                    
    *** FIRST: integer | string | true | false | (  
    *** FOLLOW: @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    DISPATCH_TYPE_EXPR -> DISPATCH_EXPR DISPATCH_OP     $$ FIRST_PLUS = integer | string | true | false | (  
    
    *** FIRST: . | eps
    *** FOLLOW: @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    DISPATCH_OP -> . object_id ( OPT_EXPR_ARGS )            $$ FIRST_PLUS = .
                | eps                                   $$ FIRST_PLUS = @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    
    *** FIRST: integer | string | true | false | ( 
    *** FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | , 
    DISPATCH_EXPR -> CONSTANT                               $$ FIRST_PLUS = integer | string | true | false
                    | ( EXPR )                              $$ FIRST_PLUS = (
    
    *** FIRST: integer | string | true | false
    *** FOLLOW: . | @ | * | / | + | - | <= | < | = | } | ; | in | ) | then | else | fi | loop | pool | of | ,
    CONSTANT -> integer                                 $$ FIRST_PLUS = integer
            | string                                    $$ FIRST_PLUS = string
            | true                                      $$ FIRST_PLUS = true
            | false                                     $$ FIRST_PLUS = false
    
    *** FIRST: object_id | integer | string | true | false | ( | ~ | isvoid | not | if | while | { | let | case | new | eps
    *** FOLLOW: )
    OPT_EXPR_ARGS -> EXPR_ARGS                             $$ FIRST_PLUS = object_id | integer | string | true | false | ( | ~ | isvoid | not | if | while | { | let | case | new
            | eps                                          $$ FIRST_PLUS = )
    
    *** FIRST: object_id | integer | string | true | false | ( | ~ | isvoid | not | if | while | { | let | case | new
    *** FOLLOW: )
    EXPR_ARGS -> EXPR MORE_EXPR_ARGS                      $$ FIRST_PLUS = object_id | integer | string | true | false | ( | ~ | isvoid | not | if | while | { | let | case | new
    
    *** FIRST: , | eps
    *** FOLLOW: )
    MORE_EXPR_ARGS -> , EXPR MORE_EXPR_ARGS             $$ FIRST_PLUS = ,
                | eps                                   $$ FIRST_PLUS = )
    
    *** FIRST: object_id | integer | string | true | false | ( | ~ | isvoid | not | if | while | { | let | case | new
    *** FOLLOW: } | FOLLOW(MORE_EXPRS)  
    EXPR_LIST -> EXPR ; MORE_EXPRs                      $$ FIRST_PLUS = object_id | integer | string | true | false | ( | ~ | isvoid | not | if | while | { | let | case | new
    
    *** FIRST: object_id | integer | string | true | false | (  | if | while | { | let | case | new | ~ | isvoid | not | eps
    *** FOLLOW: FOLLOW(EXPR_LIST) = }
    MORE_EXPRS -> EXPR_LIST                             $$ FIRST_PLUS = object_id | integer | string | true | false | ( | ~ | isvoid | not | if | while | { | let | case | new
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
