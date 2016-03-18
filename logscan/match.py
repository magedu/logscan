import re

fn_map = {
    '&': lambda x, y:  x and y,
    '|': lambda x, y: x or y,
    '!': lambda x: not x
}


class Token:
    LEFT_BRACKETS = 1
    RIGHT_BRACKETS = 2
    SYMBOL = 3
    EXPRESSION = 4

    SYMBOLS = '&|!'

    def __init__(self, value, type):
        self.value = value
        self.type = type


class ASTree:
    def __init__(self, value):
        self.root = value
        self.left = None
        self.right = None


class Matcher:
    def __init__(self, origin):
        self.origin = origin
        self.ast = Matcher.make_ast(self.tokenize())

    def tokenize(self):
        tokens = []
        is_expr = False
        expr = []
        for c in self.origin:
            if c == '#':
                if not is_expr:
                    is_expr = True
                else:
                    is_expr = False
                    tokens.append(Token(''.join(expr), Token.EXPRESSION))
                    expr = []
            elif is_expr:
                expr.append(c)
            elif c in Token.SYMBOLS:
                tokens.append(Token(c, Token.SYMBOL))
            elif c == '(':
                tokens.append(Token(c, Token.LEFT_BRACKETS))
            elif c == ')':
                tokens.append(Token(c, Token.RIGHT_BRACKETS))
        return tokens

    @staticmethod
    def make_sub_tree(stack, t):
        current = t
        while stack and stack[-1].root.type != Token.LEFT_BRACKETS:
            node = stack.pop()
            if node.root.type != Token.SYMBOL:
                raise Exception("parse error")
            node.right = current
            if node.root.value == '&' or node.root.value == '|':
                left = stack.pop()
                if left.root.type != Token.SYMBOL and left.root.type != Token.EXPRESSION:
                    raise Exception("parse error")
                node.left = left
            current = node
        stack.append(current)

    @staticmethod
    def make_ast(tokens):
        stack = []
        for token in tokens:
            t = ASTree(token)
            if t.root.type == Token.SYMBOL or t.root.type == Token.LEFT_BRACKETS:
                stack.append(t)
            elif t.root.type == Token.EXPRESSION:
                Matcher.make_sub_tree(stack, t)
            else:
                t = stack.pop()
                tmp = stack.pop()
                if tmp.root.type != Token.LEFT_BRACKETS:
                    raise Exception("parse error")
                Matcher.make_sub_tree(stack, t)
        return stack.pop()

    @staticmethod
    def eval(ast, line):

        if ast.root.type == Token.EXPRESSION:
            return re.match(ast.root.value, line) is not None
        if ast.root.value == '!':
            if ast.right is None:
                raise Exception('syntax error')
            return fn_map['!'](Matcher.eval(ast.right, line))
        if ast.left is None:
            raise Exception('syntax error')
        if ast.right is None:
            raise Exception('syntax error')
        return fn_map[ast.root.value](Matcher.eval(ast.left, line), Matcher.eval(ast.right, line))

    def match(self, line):
        return Matcher.eval(self.ast, line)


if __name__ == '__main__':
    m = Matcher('#test# & #abc# | (!#sdf# & #123#)')
    print(m.match("test acd dds 234"))
