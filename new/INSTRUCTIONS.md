# 2-Digit Lottery Blockchain System - Instructions

## Overview

This project implements a blockchain-based lottery system with 10 peers participating in daily draws. The system uses PyIPv8 for networking with a pull-based gossip protocol and proof of stake consensus.

## Features

- 10 peers participating in a daily lottery by buying tokens (1-99)
- Results drawn once per day (simulated as 30-second intervals)
- Blockchain records entries, selects winners, and distributes rewards
- Controlled block creation as a daily timer
- Commit-reveal protocol for fair randomness generation
- LevelDB for mempool storage
- Pull-based gossip protocol with Bloom filters for efficient message passing

## System Components

1. **Blockchain** (`blockchain.py`): Implements the lottery blockchain with proof of stake consensus
2. **Database** (`db.py`): Handles persistent storage using LevelDB
3. **Community** (`community.py`): Implements the PyIPv8 community for peer-to-peer communication
4. **Messages** (`messages.py`): Defines message types and payloads for network communication
5. **Visualizer** (`visualizer.py`): Provides a web interface to visualize the blockchain and lottery results
6. **Main** (`main.py`): Entry point to start the lottery blockchain network

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Running the System

### Option 1: Using the run script

```bash
# Make the script executable
chmod +x run.sh

# Run the script
./run.sh
```

### Option 2: Manual execution

```bash
# Start with 10 peers and visualization
python main.py --peers 10 --visualize

# Start a single peer with visualization
python main.py --single 0 --visualize
```

## Visualization

When running with the `--visualize` flag, a web interface will be available at:

```
http://localhost:8080
```

This interface shows:
- The current blockchain state
- Pending bets in the mempool
- Lottery results
- Validator information

## Lottery Process

1. Users place bets by selecting a number (1-99) and an amount (1-99 tokens)
2. Bets are stored in the mempool
3. Every 30 seconds (simulating a day):
   - Peers contribute random values through a commit-reveal scheme
   - A winning number is determined based on these values
   - Rewards are distributed to winners
   - A new block is created and added to the blockchain

## Implementation Details

### Commit-Reveal Scheme

To ensure fair randomness generation:
1. Each peer commits a hash of a random value and a nonce
2. After all commits are collected, peers reveal their random values and nonces
3. The winning number is calculated from the combined revealed values

### Proof of Stake Consensus

- Each peer has a stake (1-100 tokens)
- The probability of being selected as a validator is proportional to the stake
- The selected validator creates the next block and broadcasts it to the network

### Mempool Synchronization

- Bloom filters are used to efficiently synchronize mempool transactions
- Each peer maintains a bloom filter of its transactions
- When syncing, only missing transactions are transferred

## Troubleshooting

- If the system fails to start, ensure all dependencies are installed
- If peers cannot connect, check your network configuration
- If the visualization doesn't load, ensure port 8080 is available