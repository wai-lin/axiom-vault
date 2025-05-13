# 2-Digit Lottery Blockchain System

## Overview
This project implements a blockchain-based lottery system with 10 peers participating in daily draws. The system uses PyIPv8 for networking with a pull-based gossip protocol and proof of stake consensus.

## Features
- 10 peers participating in a daily lottery by buying tokens (1-99)
- Results drawn once per day (simulated as 30-second intervals)
- Blockchain records entries, selects winners, and distributes rewards
- Controlled block creation as a daily timer
- Commit-reveal protocol for fair randomness generation
- LevelDB for mempool storage

## Installation

### Prerequisites
- Python 3.8 or higher
- libsodium (required by PyIPv8 for cryptographic operations)

### Installing Dependencies
1. Install system dependencies:
   - **libsodium**:
     - macOS: `brew install libsodium`
     - Linux: `sudo apt-get install libsodium-dev`

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running the System
Use the provided script:
```
./run.sh
```

Or run manually:
```
python main.py --peers 10 --visualize
```

### Troubleshooting
If you encounter an error related to libsodium:
```
OSError: Could not locate nacl lib, searched for libsodium
```
Make sure to install the libsodium system package as mentioned above.

## System Architecture

### Network Setup
- 10 nodes/peers using PyIPv8 for P2P communication
- Pull-based gossip protocol with Bloom filters
- RandomWalk strategy for peer discovery

### Block Creation
- Daily blocks (every 30 seconds in the simulation)
- Each block includes:
  - Winning lottery number
  - Commit-reveal values from peers
  - Lottery bets since the last block
  - Results of the lottery

### Mempool Design
- Storage: LevelDB (key=tx_hash, value=tx_data)
- Sync: Pull-based gossip with Bloom filters
- Cleaning: Clear confirmed transactions after block creation

## Components

### Blockchain
- Proof of Stake consensus
- Block structure for lottery data
- Genesis block configuration

### Networking
- PyIPv8 integration
- Gossip protocol implementation
- Peer discovery and management

### Lottery Logic
- Bet placement and validation
- Winner selection using commit-reveal scheme
- Reward distribution

## Installation

```bash
pip install -r requirements.txt
```

## Running the System

```bash
python main.py
```

This will start a network of 10 peers, each participating in the lottery system. The system will automatically:

1. Place random bets for testing purposes
2. Create blocks every 30 seconds (simulating daily draws)
3. Determine winning numbers and distribute rewards

## Lottery Process

1. Users place bets by selecting a number (1-99) and an amount (1-99 tokens)
2. Bets are stored in the mempool
3. Every 30 seconds (simulating a day):
   - Peers contribute random values through a commit-reveal scheme
   - A winning number is determined based on these values
   - Rewards are distributed to winners
   - A new block is created and added to the blockchain