from asyncio import run

from network.setup import start_network

import sys


run(start_network(sys.argv[1]))
