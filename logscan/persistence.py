import shelve
import threading


class OffsetPersistence:
    def __init__(self, config):
        self.config = config
        self.__db = shelve.open(config['main']['offset_db'])
        self.__lock = threading.Lock()

    def put(self, filename, offset):
        with self.__lock:
            self.__db[filename] = offset

    def get(self, filename):
        with self.__lock:
            return self.__db.get(filename, -1)

    def sync(self):
        with self.__lock:
            self.__db.sync()

    def close(self):
        self.__db.close()