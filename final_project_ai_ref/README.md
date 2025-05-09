# 2-Digit Lottery Blockchain System

This project implements a 2-digit lottery system using blockchain technology. The system allows 10 users to participate in a daily lottery by buying tokens with numbers from 1 to 99.

## Features

- 10 peers participating in a lottery network
- Daily lottery draws (simulated as 30-second intervals)
- Blockchain-based recording of entries, winner selection, and reward distribution
- Commit-reveal scheme for fair randomness generation
- Persistent storage of blockchain data and transactions

## System Architecture

### Network Setup
- 10 nodes/peers using IPv8 for P2P communication
- RandomWalk strategy for peer discovery

### Block Creation
- Daily blocks (every 30 seconds in the simulation)
- Each block includes:
  - Winning lottery number
  - Commit-reveal values from peers
  - Lottery bets since the last block
  - Results of the lottery

### Mempool Design
- Storage of pending transactions
- Clearing of confirmed transactions after block creation

## Running the System

### Prerequisites

1. Make sure you have Python installed
2. Install required dependencies

### Setup

1. Create a directory for PEM files:
   ```
   mkdir -p pem
   ```

2. Generate PEM files for each peer (this happens automatically when running the system for the first time)

### Running the Lottery Network

```
python main.py
```

This will start a network of 10 peers, each participating in the lottery system. The system will automatically:

1. Place random bets for testing purposes
2. Create blocks every 30 seconds (simulating daily draws)
3. Determine winning numbers and distribute rewards

## Implementation Details

- `community.py`: Contains the LotteryBlockchainCommunity class that implements the lottery logic
- `network.py`: Sets up the peer network
- `messages.py`: Defines message types for peer communication
- `db.py`: Implements persistent storage for blockchain data
- `main.py`: Entry point to start the lottery network

## Lottery Process

1. Users place bets by selecting a number (1-99) and an amount (1-99 tokens)
2. Bets are stored in the mempool
3. Every 30 seconds (simulating a day):
   - Peers contribute random values through a commit-reveal scheme
   - A winning number is determined based on these values
   - Rewards are distributed to winners
   - A new block is created and added to the blockchain