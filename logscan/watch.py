import logging
from os import path
from datetime import datetime
from queue import Queue, Full
from watchdog.events import FileSystemEventHandler
from .monitor import Monitor


class WatcherHandler(FileSystemEventHandler):
    def __init__(self, filename, counter, notifier, offset_db, queue_len=1000):
        self.filename = path.abspath(filename)
        self.queue = Queue(queue_len)
        self.counter = counter
        self.monitor = Monitor(self.queue, counter, notifier)
        self.offset_db = offset_db
        self.fd = None
        self.offset = 0
        self.timer = datetime.now()
        if path.isfile(self.filename):
            self.fd = open(self.filename)
            offset = self.offset_db.get(self.filename)
            file_size = path.getsize(self.filename)
            if offset < 0:
                self.offset = file_size
            else:
                if offset <= file_size:
                    self.offset = offset
                else:
                    self.offset = 0

    def start(self):
        self.monitor.start()

    def stop(self):
        if self.fd is not None and not self.fd.closed:
            self.fd.close()
        self.monitor.stop()
        self.offset_db.put(self.filename, self.offset)
        self.offset_db.sync()

    def on_deleted(self, event):
        if path.abspath(event.src_path) == self.filename:
            self.fd.close()

    def on_moved(self, event):
        if path.abspath(event.src_path) == self.filename:
            self.fd.close()
        if path.abspath(event.dest_path) == self.filename and path.isfile(self.filename):
            self.fd = open(self.filename)
            self.offset = path.getsize(self.filename)

    def on_modified(self, event):
        now = datetime.now()
        if path.abspath(event.src_path) == self.filename:
            self.fd.seek(self.offset, 0)
            for line in self.fd:
                line = line.rstrip('\n')
                try:
                    self.queue.put_nowait(line)
                except Full:
                    logging.warning('queue overflow')
            self.offset = self.fd.tell()
        if (now - self.timer).seconds > 30:
            self.offset_db.put(self.filename, self.offset)
            self.timer = now

    def on_created(self, event):
        if path.abspath(event.src_path) == self.filename and path.isfile(self.filename):
            self.fd = open(self.filename)
            self.offset = path.getsize(self.filename)



