from asyncio import run

from network.setup import start_network

PEER_COUNT = 3


run(start_network(PEER_COUNT))
