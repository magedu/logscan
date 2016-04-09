import threading
from queue import Empty
from .match import Matcher
from .check import Checker
from .rule import Rule


class Monitor:
    def __init__(self, queue, counter, notifier):
        self.matcher_list = []
        self.checker_list = []
        self.rules = []
        self.queue = queue
        self.counter = counter
        self.notifier = notifier
        self.__event = threading.Event()
        self.__thread = None

    def __add_matcher(self, rule):
        matcher = Matcher(rule.name, rule.expression, rule.order)
        self.matcher_list.append(matcher)
        self.matcher_list = sorted(self.matcher_list, key=lambda x: x.order)

    def __add_checker(self, rule):
        checker = Checker(rule.name, rule.interval, rule.threshold, rule.contacts, self.counter, self.notifier)
        self.checker_list.append(checker)
        checker.start()

    def add(self, filename, name, src):
        rule = Rule.loads(filename, name, src)
        self.__add_matcher(rule)
        self.__add_checker(rule)

    def __remove_matcher(self, name):
        self.matcher_list.remove(Matcher(name, '', 0))
        #self.matcher_list = sorted(self.matcher_list, key=lambda x: x.order)

    def __remove_checker(self, name):
        checker = None
        for c in self.checker_list:
            if c.name == name:
                c.stop()
                checker = c
                break
        self.checker_list.remove(checker)

    def remove(self, name):
        self.__remove_matcher(name)
        self.__remove_checker(name)

    def __do_match(self):
        while not self.__event.is_set():
            try:
                line = self.queue.get(timeout=100)
                for matcher in self.matcher_list:
                    if matcher.match(line):
                        self.counter.inc(matcher.name)
                        break
            except Empty:
                pass

    def start(self):
        self.__thread = threading.Thread(target=self.__do_match)
        self.__thread.daemon = True
        self.__thread.start()

    def stop(self):
        self.__event.set()
        if self.__thread is not None:
            self.__thread.join()
