import threading
from os import path
from .count import Counter


class Schedule:
    def __init__(self, counter_path):
        self.watchers = {}
        self.threads = {}
        self.counter = Counter(counter_path)

    def add_watcher(self, watcher):
        if watcher.filename not in self.watchers.keys():
            watcher.counter = self.counter
            t = threading.Thread(target=watcher.start, name='Watcher-{0}'.format(watcher.filename))
            t.daemon = True
            t.start()
            self.threads[watcher.filename] = t
            self.watchers[watcher.filename] = watcher

    def remove_watcher(self, filename):
        key = path.abspath(filename)
        if key in self.watchers.keys():
            self.watchers[key].stop()
            self.watchers.pop(key)
            self.threads.pop(key)

    def join(self):
        while self.watchers.values():
            for t in list(self.threads.values()):
                t.join()

    def stop(self):
        for w in self.watchers.values():
            w.stop()
        self.counter.stop()
