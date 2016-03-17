import os
import logging
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logging.basicConfig(level=logging.INFO)


class Watcher(FileSystemEventHandler):
    def __init__(self, filename, matcher):
        super(Watcher, self).__init__()
        self.filename = filename
        self.matcher = matcher
        self.fd = None
        self.offset = 0
        if os.path.isfile(self.filename):
            self.fd = open(self.filename)
            self.offset = os.path.getsize(self.filename)

    def __close(self):
        if self.fd is not None and not self.fd.closed:
            self.fd.close()
            self.fd = None

    def __open(self):
        self.fd = open(self.filename)
        self.offset = 0

    def __read(self):
        size = os.path.getsize(self.filename)
        if size < self.offset:
            self.offset = 0
        self.fd.seek(self.offset, 0)
        for line in self.fd:
            line.rstrip('\n')
            match = getattr(self.matcher, 'match', lambda x: False)
            if match(line):
                logging.info("match {0}".format(line))
            logging.info(line)
        self.offset = self.fd.tell()

    @property
    def dirname(self):
        return os.path.dirname(os.path.abspath(self.filename))

    def on_deleted(self, event):
        if event.src_path == self.filename:
            logging.info("{0} deleted, close it".format(self.filename))
            self.__close()

    def on_moved(self, event):
        if event.src_path == self.filename:
            logging.info("{0} move out, close it".format(self.filename))
            self.__close()
        if event.dest_path == self.filename and not event.is_directory:
            logging.info("{0} move in, open it".format(self.filename))
            self.__close()
            self.__open()
            self.__read()

    def on_created(self, event):
        if event.src_path == self.filename and not event.is_directory:
            logging.info("{0} created, open it".format(self.filename))
            self.__close()
            self.__open()
            self.__read()

    def on_modified(self, event):
        if event.src_path == self.filename:
            logging.info("{0} modified".format(event.src_path))
            self.__read()


if __name__ == '__main__':
    import sys
    observer = Observer()
    watcher = Watcher(sys.argv[1], None)
    w2 = Watcher(sys.argv[2], None)
    observer.schedule(watcher, watcher.dirname, recursive=False)
    observer.schedule(w2, w2.dirname, recursive=False)
    observer.start()
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
