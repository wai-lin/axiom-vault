from asyncio import run
import sys

from network.setup import start_network

if __name__ == '__main__':
    run(start_network(sys.argv[1]))
