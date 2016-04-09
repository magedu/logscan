import logging
from os import path
from base64 import urlsafe_b64decode
from watchdog.observers import Observer
from .watch import WatcherHandler
from .count import Counter
from .notification import Notifier
from .persistence import OffsetPersistence


class Schedule:
    def __init__(self, config):
        self.observer = Observer()
        self.handlers = {}
        self.watchers = {}
        self.counter = Counter()
        self.notifier = Notifier(config)
        self.offset_db = OffsetPersistence(config)

    def __make_key(self, filename):
        return path.abspath(urlsafe_b64decode(filename))

    def add_watcher(self, filename):
        handler = WatcherHandler(urlsafe_b64decode(filename), counter=self.counter,
                                 notifier=self.notifier, offset_db=self.offset_db)
        if handler.filename not in self.handlers.keys():
            self.handlers[handler.filename] = handler
            self.watchers[handler.filename] = self.observer.schedule(handler,
                                                                     path.dirname(handler.filename),
                                                                     recursive=False)
            handler.start()

    def remove_watcher(self, filename):
        key = self.__make_key(filename)
        if key in self.watchers.keys():
            self.observer.unschedule(self.watchers.get(key))
            self.watchers.pop(key)
            self.handlers.pop(key).stop()

    def add_monitor(self, filename, name, src):
        key = self.__make_key(filename)
        handler = self.handlers.get(key)
        if handler is None:
            logging.warning('watcher {0} not found, auto add it'.format(filename))
            self.add_watcher(filename)
            handler = self.handlers.get(key)
        handler.monitor.add(filename, name, src)

    def remove_monitor(self, filename, name):
        key = self.__make_key(filename)
        handler = self.handlers.get(key)
        if handler is None:
            logging.warning('watcher {0} not found'.format(filename))
            return
        handler.monitor.remove(name)

    def start(self):
        self.observer.start()
        self.notifier.start()

    def join(self):
        self.observer.join()

    def stop(self):
        self.observer.stop()
        for handler in self.handlers.values():
            handler.stop()
        self.notifier.stop()
        self.offset_db.close()
