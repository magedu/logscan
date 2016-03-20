import threading


def send_mail(user, message):
    pass


class Checker:
    def __init__(self, name, expr, path, interval, threshold, users, counter):
        self.name = name
        self.expr = expr
        self.path = path
        self.interval = interval
        self.threshold = threshold
        self.users = users
        self.counter = counter
        self.__event = threading.Event()

    def check(self):
        while not self.__event.is_set():
            self.__event.wait(self.interval * 60)
            count = self.counter.get(name=self.name)
            self.counter.clean(self.name)
            if count >= self.threshold[0]:
                if count < self.threshold[1] or self.threshold[1] < 0:
                    self.notify('{0} matched {1} times in {2}min'.format(self.name, count, self.interval))

    def notify(self, message):
        for user in self.users:
            t = threading.Thread(target=send_mail, args=(user, message), name='mail_sender-{0}'.format(user))
            t.start()

    def stop(self):
        self.__event.set()
