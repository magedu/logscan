import threading
import datetime
from .notification import Message


class Checker:
    def __init__(self, name, interval, threshold, contacts, counter, notifier):
        self.name = name
        self.interval = interval
        self.threshold = threshold
        self.contacts = contacts
        self.counter = counter
        self.notifier = notifier
        self.__event = threading.Event()

    def __do_check(self):
        while not self.__event.is_set():
            self.__event.wait(self.interval * 60)
            count = self.counter.get(name=self.name)
            self.counter.clean(self.name)
            if count >= self.threshold[0]:
                if count < self.threshold[1] or self.threshold[1] < 0:
                    self.notify(count)

    def start(self):
        threading.Thread(self.__do_check, name='checker-{0}'.format(self.name)).start()

    def notify(self, count):
        for contact in self.contacts:
            message = Message(contact, self.name, count, datetime.datetime.now())
            self.notifier.notify(message)

    def stop(self):
        self.__event.set()
