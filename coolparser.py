import sys
import shlex
from cool_lexer import next_token
from cool_lexer import peek_token
from cool_lexer import Token


token = Token('', '')
classes = []
class_methods = []
errors = []

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
            for c in classes:
                print(c)
        else:
            print("Errors found")


def fail(name, lexer):
    print("Parse error in {0} on line {1}".format(name, lexer.lineno))


# lineno, column, tokens expected


def program(lexer):
    global token
    # for single first plus rules also need to do: if token.name == class. FOR ERR HANDLING
    if _class(lexer):
        if token.name == ";":
            token = next_token(lexer)
            if program_rest(lexer):
                return True
            else:
                fail("program", lexer)
    raise Exception


def program_rest(lexer):
    global token
    if token.name == "class":
        return program(lexer)
    elif token.name == "eof":
        return True
    else:
        fail("program_rest", lexer)
    raise Exception


def _class(lexer):
    global token
    if token.name == "class":
        token = next_token(lexer)
        if token.name == "type_id":
            class_name = token.val
            class_methods.clear()
            token = next_token(lexer)
            if class_type(lexer):
                if token.name == "{":
                    token = next_token(lexer)
                    if feature_list(lexer):
                        if token.name == "}":
                            token = next_token(lexer)
                            class_summary = class_name + ": "
                            for method in class_methods:
                                class_summary += method + ", "
                            # slice last comma off and add to classes
                            classes.append(class_summary[:-2])
                            return True
                        else:
                            fail("class", lexer)
    raise Exception


def class_type(lexer):
    global token
    if token.name == "inherits":
        token = next_token(lexer)
        if token.name == "type_id":
            token = next_token(lexer)
            return True
    elif token.name == "{":
        return True
    raise Exception


def feature_list(lexer):
    global token
    if token.name == "object_id":
        if feature(lexer):
            if token.name == ";":
                token = next_token(lexer)
                return feature_list(lexer)
    elif token.name == "}":
        return True
    raise Exception


def feature(lexer):
    global token
    if token.name == "object_id":
        feature_id = token.val
        token = next_token(lexer)
        is_valid_feature_rest, feature_type = feature_rest(lexer)
        class_methods.append(feature_id)
        return is_valid_feature_rest
    raise Exception


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
                                    return True, "method"
    elif token.name == ":":
        token = next_token(lexer)
        if token.name == "type_id":
            token = next_token(lexer)
            return opt_expr_assignment(lexer), ""
    raise Exception


def opt_feature_args(lexer):
    global token
    if token.name == "object_id":
        return feature_args(lexer)
    elif token.name == ")":
        return True
    raise Exception


def feature_args(lexer):
    global token
    if formal(lexer):
        return more_feature_args(lexer)
    raise Exception


def more_feature_args(lexer):
    global token
    if token.name == ",":
        token = next_token(lexer)
        if formal(lexer):
            return more_feature_args(lexer)
    elif token.name == ")":
        return True
    raise Exception


def opt_expr_assignment(lexer):
    global token
    if token.name == "<-":
        return expr_assignment(lexer)
    elif token.name == ";" or token.name == "," or token.name == "in":
        return True
    raise Exception


def expr_assignment(lexer):
    global token
    if token.name == "<-":
        token = next_token(lexer)
        return expr(lexer)
    raise Exception


def formal(lexer):
    global token
    if token.name == "object_id":
        token = next_token(lexer)
        if token.name == ":":
            token = next_token(lexer)
            if token.name == "type_id":
                token = next_token(lexer)
                return True
    raise Exception


def expr(lexer):
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
    elif token.name in ["integer", "string", "true", "false", "(", "if", "while", "{", "let", "case", "new", "~", "isvoid", "not"]:
        return boolean_complement_expr(lexer)

    raise Exception


def boolean_complement_expr(lexer):
    global token
    if token.name == "not":
        token = next_token(lexer)
        return boolean_complement_expr(lexer)
    elif token.name in ['integer', 'string', 'true', 'false', '(', 'object_id', 'if', 'while', '{', 'let', 'case', 'new', '~', 'isvoid']:
        return comparison_expr(lexer)
    raise Exception


def comparison_expr(lexer):
    global token
    if add_expr(lexer):
        return comparison_op(lexer)


def comparison_op(lexer):
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


def add_expr(lexer):
    global token
    if mult_expr(lexer):
        return add_op(lexer)


def add_op(lexer):
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


def mult_expr(lexer):
    global token
    if checkvoid_expr(lexer):
        return mult_op(lexer)


def mult_op(lexer):
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


def checkvoid_expr(lexer):
    global token
    if token.name == "isvoid":
        token = next_token(lexer)
        return checkvoid_expr(lexer)
    elif token.name in ['integer', 'string', 'true', 'false', '(', 'object_id', 'if', 'while', '{', 'let', 'case', 'new', '~']:
        return integer_complement_expr(lexer)
    raise Exception


def integer_complement_expr(lexer):
    global token
    if token.name == "~":
        token = next_token(lexer)
        return integer_complement_expr(lexer)
    elif token.name in ['integer', 'string', 'true', 'false', '(', 'object_id', 'if', 'while', '{', 'let', 'case', 'new']:
        return dispatch_expr(lexer)
    raise Exception


def dispatch_expr(lexer):
    global token
    if element(lexer):
        return dispatch_op(lexer)
    raise Exception


def dispatch_op(lexer):
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
    elif token.name in ['*', '/', '+', '-', '<=', '<', '=', '}', ';', 'in', ')', 'then', 'else', 'fi', 'loop', 'pool', 'of', ',']:
        return True
    raise Exception


def dispatch_type(lexer):
    global token
    if token.name == "@":
        token = next_token(lexer)
        if token.name == "type_id":
            token = next_token(lexer)
            return True
    elif token.name == '.':
        return True
    raise Exception


def element(lexer):
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
    raise Exception


def _id(lexer):
    global token
    if token.name == "object_id":
        token = next_token(lexer)
        return True
    raise Exception


def id_op(lexer):
    global token
    if token.name == "(":
        token = next_token(lexer)
        if opt_expr_args(lexer):
            if token.name == ")":
                token = next_token(lexer)
                return True
    elif token.name in ['.', '@', '*', '/', '+', '-', '<=', '<', '=', '}', ';', 'in', ')', 'then', 'else', 'fi', 'loop','pool', 'of', ',']:
        return True
    raise Exception


def opt_expr_args(lexer):
    global token
    if token.name in ['object_id', 'integer', 'string', 'true', 'false', '(', '~', 'isvoid', 'not', 'if', 'while', '{', 'let', 'case', 'new']:
        return expr_args(lexer)
    elif token.name == ")":
        return True
    raise Exception


def expr_args(lexer):
    global token
    if expr(lexer):
        return more_expr_args(lexer)
    raise Exception


def more_expr_args(lexer):
    global token
    if token.name == ",":
        token = next_token(lexer)
        if expr(lexer):
            return more_expr_args(lexer)
        else:
            fail("more_expr_args", lexer)
    elif token.name == ")":
        return True
    else:
        fail("more_expr_args", lexer)
        return False
    raise Exception


def expr_list(lexer):
    global token
    if expr(lexer):
        if token.name ==";":
            token = next_token(lexer)
            return more_exprs(lexer)
    raise Exception


def more_exprs(lexer):
    global token
    if token.name in ['object_id', 'integer', 'string', 'true', 'false', '(', '~', 'isvoid', 'not', 'if', 'while', '{', 'let', 'case', 'new']:
        return expr_list(lexer)
    elif token.name == "}":
        return True
    raise Exception


def let_args(lexer):
    global token
    if let_arg(lexer):
        return more_let_args(lexer)
    raise Exception


def more_let_args(lexer):
    global token
    if token.name == ",":
        token = next_token(lexer)
        if let_arg(lexer):
            return more_let_args(lexer)
    elif token.name == "in":
        return True
    raise Exception


def let_arg(lexer):
    global token
    if token.name == "object_id":
        token = next_token(lexer)
        if token.name == ":":
            token = next_token(lexer)
            if token.name == "type_id":
                token = next_token(lexer)
                return opt_expr_assignment(lexer)
    raise Exception


def case_args(lexer):
    global token
    if case_arg(lexer):
        return more_case_args(lexer)
    raise Exception


def more_case_args(lexer):
    global token
    if token.name == "object_id":
        return case_args(lexer)
    elif token.name == "esac":
        return True
    raise Exception


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
    else:
        error = "Unexpected token {0} on line {1}, column {2}. Expected one of: object_id".format(token.val, )


if __name__ == "__main__":
    parse(sys.argv[1])
