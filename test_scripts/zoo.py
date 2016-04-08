import threading

from kazoo.client import KazooClient
from kazoo.recipe.watchers import ChildrenWatch, DataWatch


class Zoo:
    def __init__(self, hosts):
        self.__event = threading.Event()
        self.zk = KazooClient(hosts=hosts, read_only=True)
        self.zk.start()
        ChildrenWatch(self.zk, '/test/test', self.watch_children)

    def watch_children(self, children):
        print("Children are %s" % children)

    def join(self):
        self.__event.wait()

    def stop(self):
        self.zk.stop()
        self.__event.set()


if __name__ == '__main__':
    zoo = Zoo('127.0.0.1:2181')
    try:
        zoo.join()
    except KeyboardInterrupt:
        zoo.stop()