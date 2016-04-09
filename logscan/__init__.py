import logging
import threading
from base64 import urlsafe_b64decode
from functools import partial
from os import path
from kazoo.client import KazooClient, NoNodeError
from kazoo.recipe.watchers import ChildrenWatch, DataWatch
from .schedule import Schedule


class Scan:
    def __init__(self, config):
        self.config = config
        self.app_id = config['main']['app_id']
        self.schedule = Schedule(config)
        self.zk = KazooClient(hosts=config['zookeeper']['connect'], read_only=True)
        self.root = path.join(config['zookeeper']['root'], self.app_id)
        self.files = set()
        self.rules = {}
        self.file_watchers_ctl = {}
        self.rule_watchers_ctl = {}
        self.__event = threading.Event()

    def watch_files(self, files):
        for f in set(files).difference(self.files):
            logging.error('added {0}'.format(urlsafe_b64decode(f).decode()))
            self.schedule.add_watcher(f)
            self.file_watchers_ctl[f] = threading.Event()
            fn = partial(self.watch_rules, filename=f, event=self.file_watchers_ctl[f])
            ChildrenWatch(self.zk, path.join(self.root, f), fn)
        for f in self.files.difference(set(files)):
            logging.error('removed {0}'.format(urlsafe_b64decode(f).decode()))
            self.schedule.remove_watcher(f)
            event = self.file_watchers_ctl.pop(f)
            event.set()
        self.files = set(files)
        return not self.__event.is_set()

    def watch_rules(self, rules, filename, event):
        if event.is_set():
            return False
        if filename not in self.rules:
            self.rules[filename] = set()
        for rule in set(rules).difference(self.rules[filename]):
            node = path.join(self.root, filename, rule)
            self.schedule.add_monitor(filename, rule, self.zk.get(node))
            self.rule_watchers_ctl[rule] = threading.Event()
            fn = partial(self.watch_rule, filename=filename, name=rule, event=self.rule_watchers_ctl[rule])
            try:
                DataWatch(self.zk, node, fn)
            except NoNodeError:
                pass
        for rule in self.rules[filename].difference(set(rules)):
            self.schedule.remove_monitor(filename, rule)
            self.rule_watchers_ctl.pop(rule).set()
        self.rules[filename] = set(rules)
        return not event.is_set()

    def watch_rule(self, data, stat, zk_event, filename, name, event):
        self.schedule.remove_monitor(filename, name)
        self.schedule.add_monitor(filename, name, data)
        return not event.is_set()

    def start(self):
        self.zk.start()
        ChildrenWatch(self.zk, self.root, self.watch_files)
        self.schedule.start()

    def join(self):
        self.__event.wait()

    def stop(self):
        for e in self.rule_watchers_ctl.values():
            e.set()
        for e in self.file_watchers_ctl.values():
            e.set()
        self.zk.stop()
        self.schedule.stop()
        self.__event.set()
