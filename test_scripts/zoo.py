from kazoo.client import KazooClient

if __name__ == '__main__':
    zk = KazooClient(hosts='127.0.0.1:2181')
    zk.start()
