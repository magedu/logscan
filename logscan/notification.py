import sqlite3
import threading
import logging
from queue import Queue, Full, Empty
from .rule import Contact


class MailSender:
    def __init__(self, config):
        self.config = config

    def send(self, message):
        pass


class SMSSender:
    def __init__(self, config):
        self.config = config

    def send(self, message):
        pass


class Message:
    def __init__(self, contact, name, count, receive_time):
        if not isinstance(contact, Contact):
            contact = Contact.loads(contact)
        self.contact = contact
        self.name = name
        self.count = count
        self.receive_time = receive_time


CREATE_TABLE_DDL = r'''
CREATE TABLE IF NOT EXISTS notifications (
  id             INTEGER      PRIMARY KEY AUTOINCREMENT,
  name           STRING (128) NOT NULL,
  count          BIGINT       NOT NULL,
  contact        TEXT         NOT NULL,
  receive_time   DATETIME     NOT NULL,
  is_send        BOOLEAN      NOT NULL DEFAULT FALSE
)'''


class Notifier:
    def __init__(self, config):
        self.config = config
        self.__senders = [MailSender(config), SMSSender(config)]
        self.__event = threading.Event()
        self.__queue = Queue(100)
        self.__semaphore = threading.BoundedSemaphore(int(config['notification']['threads']))
        self.db = sqlite3.connect(config['notification']['persistence'])
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()
        try:
            self.cursor.execute(CREATE_TABLE_DDL)
            self.db.commit()
        except Exception as e:
            logging.error('init notification error, {0}'.format(e))

    def notify(self, message):
        sql = r'INSERT INTO notifications (name, count, contact, receive_time) VALUES (?, ?, ?, ?)'
        try:
            ret = self.cursor.execute(sql, (message.name, message.count,
                                            message.contact.dumps(), message.receive_time))
            self.db.commit()
            self.__queue.put_nowait(ret.lastrowid)
        except Full:
            logging.warning('notification queue full')
        except Exception as e:
            self.db.rollback()
            logging.error('persistence message failed, {0}'.format(e))

    def __sender_wrap(self, sender, message):
        with self.__semaphore:
            sender.send(message)

    def __send(self):
        while not self.__event.is_set():
            try:
                row_id = self.__queue.get(timeout=100)
                self.cursor.execute(r'SELECT name, count, contact, receive_time, is_sender '
                                    r'FROM notifications WHERE rowid=?',
                                    (row_id, ))
                row = self.cursor.fetchone()
                if row['is_sender']:
                    continue
                del row['is_sender']
                message = Message(**row)
                for sender in self.__senders:
                    t = threading.Thread(target=self.__sender_wrap, args=(sender, message),
                                         name='sender-{0}'.format(sender.__name__))
                    t.daemon = True
                    t.start()
                self.cursor.execute(r'UPDATE notifications SET is_send=? WHERE rowid=?', (True, row_id))
                self.db.commit()
            except Empty:
                pass

    def __compensate(self):
        self.cursor.execute(r'SELECT rowid FROM notifications WHERE is_send=?', (False, ))
        for row in self.cursor.fetchall():
            try:
                self.__queue.put_nowait(row['rowid'])
            except Full:
                logging.warning('notification queue full')

    def __compensation(self):
        while self.__event.is_set():
            self.__event.wait(60)
            self.__compensate()

    def start(self):
        self.__compensate()
        s = threading.Thread(target=self.__send, name='notifier-send')
        s.daemon = True
        s.start()
        c = threading.Thread(target=self.__compensation, name='notifier-compensation')
        c.daemon = True
        c.start()

    def stop(self):
        self.__event.set()
        self.cursor.close()
        self.db.commit()
        self.db.close()

