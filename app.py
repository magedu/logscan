import sys
import configparser
from logscan import Scan

if __name__ == '__main__':
    config = configparser.ConfigParser()
    with open(sys.argv[1] if len(sys.argv) == 2 else './config.ini') as f:
        config.read_file(f)
    scan = Scan(config)
    scan.start()
    try:
        scan.join()
    except KeyboardInterrupt:
        scan.stop()
