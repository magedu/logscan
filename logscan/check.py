import threading
import logging
from queue import Queue, Full


class Message:
    def __init__(self, user, name, path, count, type=None):
        self.user = user
        self.name = name
        self.path = path
        self.count = count
        if type is None:
            type = ['mail', ]
        self.type = type


class Notification:
    def __init__(self):
        self.message = None
        self.__event = threading.Event()
        self.__cond = threading.Condition()
        self.__mail_queue = Queue(100)

    def _send_mail(self):
        while not self.__event.is_set():
            message = self.__mail_queue.get()
            #TODO send email

    def send_mail(self):
        threading.Thread(target=self._send_mail, name='send-mail-real').start()
        while not self.__event.is_set():
            with self.__cond:
                self.__cond.wait()
                if 'mail' in self.message.type:
                    try:
                        self.__mail_queue.put(self.message, timeout=1)
                    except Full:
                        logging.error('mail queue is full')

    def send_sms(self):
        while not self.__event.is_set():
            with self.__cond:
                self.__cond.wait()
                #TODO send sms

    def notify(self, message):
        with self.__cond:
            self.message = message
            self.__cond.notify_all()

    def start(self):
        mail = threading.Thread(target=self.send_mail, name='send-mail')
        mail.start()
        sms = threading.Thread(target=self.send_sms, name='send-sms')
        sms.start()

    def stop(self):
        self.__event.set()


class Checker:
    def __init__(self, name, expr, path, interval, threshold, users, counter, notification):
        self.name = name
        self.expr = expr
        self.path = path
        self.interval = interval
        self.threshold = threshold
        self.users = users
        self.counter = counter
        self.__event = threading.Event()
        self.notification = notification

    def start(self):

        while not self.__event.is_set():
            self.__event.wait(self.interval * 60)
            count = self.counter.get(name=self.name)
            self.counter.clean(self.name)
            if count >= self.threshold[0]:
                if count < self.threshold[1] or self.threshold[1] < 0:
                    self.notify('{0} matched {1} times in {2}min'.format(self.name, count, self.interval))

    def notify(self, count):
        for user in self.users:
            message = Message(user, self.name, self.path, count)
            self.notification.notify(message)

    def stop(self):
        self.__event.set()
