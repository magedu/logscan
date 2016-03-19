import threading
from os import path


class Schedule:
    def __init__(self):
        self.watchers = {}
        self.threads = {}

    def add_watcher(self, watcher):
        if watcher.filename not in self.watchers.keys():
            t = threading.Thread(target=watcher.start, name='Watcher-{0}'.format(watcher.filename))
            t.daemon = True
            t.start()
            self.threads[watcher.filename]= t
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

