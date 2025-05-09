from asyncio import run

from network import start_peer_network

# Number of peers in the lottery network
NUM_PEERS = 10

# Start the lottery blockchain network with 10 peers
run(start_peer_network(NUM_PEERS))
