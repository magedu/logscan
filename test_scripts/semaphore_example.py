import time
import threading
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s [%(threadName)s] %(message)s')


def worker():
    time.sleep(1)
    logging.debug('i am worker')


def wrap(s):
    with s:
        worker()
    # s.acquire()
    # worker()
    # s.release()

if __name__ == '__main__':
    s = threading.BoundedSemaphore(1)
    for x in range(10):
        threading.Thread(target=wrap, args=(s, ), name='worker-{0}'.format(x)).start()

