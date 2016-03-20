import re
import threading
import logging
from queue import Queue, Full

class Token:
    LEFT_BRACKETS = 'LEFT_BRACKETS'
    RIGHT_BRACKETS = 'RIGHT_BRACKETS'
    SYMBOL = 'SYMBOL'
    EXPRESSION = 'EXPRESSION'
    SYMBOLS = '&|!'

    def __init__(self, value, type):
        self.value = value
        self.type = type

    def __str__(self):
        return '{0}<{1}>'.format(self.value, self.type)

    def __repr__(self):
        return self.__str__()


class ASTree:
    def __init__(self, token):
        self.root = token
        self.left = None
        self.right = None

    def visit(self):
        ret = []
        q = Queue()
        q.put(self)
        while not q.empty():
            t = q.get()
            ret.append(t.root)
            if t.left:
                q.put(t.left)
            if t.right:
                q.put(t.right)
        return ret


def tokenize(origin):
    tokens = []
    is_expr = False
    expr = []
    for c in origin:
        if c == '#':
            if not is_expr:
                is_expr = True
            else:
                is_expr = False
                token = Token(''.join(expr), Token.EXPRESSION)
                tokens.append(token)
                expr = []
        elif is_expr:
            expr.append(c)
        elif c in Token.SYMBOLS:
            token = Token(c, Token.SYMBOL)
            tokens.append(token)
        elif c == '(':
            token = Token(c, Token.LEFT_BRACKETS)
            tokens.append(token)
        elif c == ')':
            token = Token(c, Token.RIGHT_BRACKETS)
            tokens.append(token)

    return tokens


def make_sub_ast(stack, t):
    current = t
    while stack and stack[-1].root.type != Token.LEFT_BRACKETS:
        node = stack.pop()
        if node.root.type != Token.SYMBOL:
            raise Exception('parse error, excepted {0} but {1}'.format(Token.SYMBOL, node.root))
        node.right = current
        if node.root.value == '&' or node.root.value == '|':
            left = stack.pop()
            if left.root.type != Token.SYMBOL and left.root.type != Token.EXPRESSION:
                raise Exception('parse error, excepted {0} or {1} but {2}'.format(Token.SYMBOL,
                                                                                  Token.EXPRESSION, left.root))
            node.left = left
        current = node
    stack.append(current)


def make_ast(tokens):
    stack = []
    for t in tokens:
        tree = ASTree(t)
        if tree.root.type == Token.SYMBOL or tree.root.type == Token.LEFT_BRACKETS:
            stack.append(tree)
        elif tree.root.type == Token.EXPRESSION:
            make_sub_ast(stack, tree)
        else:
            sub_tree = stack.pop()
            if sub_tree.root.type != Token.SYMBOL and sub_tree.root.type != Token.EXPRESSION:
                raise Exception('parse error, excepted {0} or {1} but {2}'.format(Token.SYMBOL,
                                                                                  Token.EXPRESSION, sub_tree))
            tmp = stack.pop()
            if tmp.root.type != Token.LEFT_BRACKETS:
                raise Exception('paser error, excepted {0} but {1}'.format(Token.LEFT_BRACKETS, tmp))
            make_sub_ast(stack, sub_tree)
    return stack.pop()


def cacl(ast, line):
    if ast.root.type != Token.EXPRESSION:
        if ast.root.value == '!':
            return not cacl(ast.right, line)
        if ast.root.value == '&':
            return cacl(ast.left, line) and cacl(ast.right, line)
        if ast.root.value == '|':
            return cacl(ast.left, line) or cacl(ast.right, line)
    else:
        return re.search(ast.root.value, line) is not None


class Matcher:
    def __init__(self, name, origin):
        self.name = name
        self.origin = origin
        self.ast = make_ast(tokenize(origin))

    def match(self, line):
        return cacl(self.ast, line)


class Mathcers:
    def __init__(self, queue, counter):
        self.checkers = {}
        self.macthers = {}
        self.events = {}
        self.queue = queue
        self.queues = {}
        self.counter = counter
        self.line = None
        self.__cond = threading.Condition()
        self.__event = threading.Event()

    def _match(self, checker, event):
        while not event.is_set():
            line = self.queues[checker.name]
            if self.macthers[checker.name].match(line):
                self.counter.inc(checker.name)

    def match(self, checker, event):
        queue = Queue()
        self.queues[checker.name] = queue
        threading.Thread(target=self._match, args=(checker, event)).start()
        while not event.is_set():
            with self.__cond:
                self.__cond.wait()
                try:
                    queue.put_nowait(self.line)
                except Full:
                    logging.error("metch queue full")

    def add_checker(self, checker):
        matcher = Matcher(checker.name, checker.expr)
        self.checkers[checker.name] = checker
        self.macthers[checker.name] = matcher
        checker.start()
        event = threading.Event()
        self.events[checker.name] = event
        threading.Thread(target=self.match, args=(checker, )).start()

    def remove_checker(self, name):
        if name in self.events.keys():
            self.events[name].set()
            self.checkers[name].stop()
            self.events.pop(name)
            self.checkers.pop(name)

    def start(self):
        while not self.__event.is_set():
            self.line = self.queue.get()
            self.__cond.notify_all()

    def stop(self):
        self.__event.set()
        for e in self.events.values():
            e.set()
        for c in self.checkers.values():
            c.stop()



if __name__ == '__main__':
    e = '#test# & #abc# |(!#asd# | #456#)'
    s = 'test cdf asd 568'

    m = Matcher(e)
    print(m.match(s))

