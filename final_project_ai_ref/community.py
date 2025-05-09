import json
import random
import time
from datetime import datetime
from hashlib import sha256

from ipv8.community import Community
from ipv8.lazy_community import lazy_wrapper
from ipv8.types import Peer
from ipv8.peerdiscovery.network import PeerObserver
from ipv8.peerdiscovery.discovery import RandomWalk

from messages import BetTicketMessage
from db import Database
from visualizer import LotteryVisualizer

# Constants for the lottery system
BLOCK_INTERVAL = 30  # 30 seconds to simulate a day
MAX_LOTTERY_NUMBER = 99  # 2-digit lottery (1-99)
MIN_BET_AMOUNT = 1
MAX_BET_AMOUNT = 99


class Block:
    def __init__(self, index, timestamp, bets, previous_hash, winning_number=None, commit_reveals=None):
        self.index = index
        self.timestamp = timestamp
        self.bets = bets  # List of bet transactions
        self.previous_hash = previous_hash
        self.winning_number = winning_number  # Winning lottery number (1-99)
        self.commit_reveals = commit_reveals or []  # Commit-reveal values from peers
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "bets": self.bets,
            "previous_hash": self.previous_hash,
            "winning_number": self.winning_number,
            "commit_reveals": self.commit_reveals
        }, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()


class Mempool:
    def __init__(self):
        self.transactions = {}  # key=tx_hash, value=tx_data
        self.db = None  # Will be set by the community

    def set_database(self, db):
        self.db = db

    def add_transaction(self, transaction):
        tx_hash = sha256(json.dumps(transaction, sort_keys=True).encode()).hexdigest()
        self.transactions[tx_hash] = transaction

        # Save to database if available
        if self.db:
            self.db.add_transaction(tx_hash, transaction)

        return tx_hash

    def get_transactions(self):
        return list(self.transactions.values())

    def clear_transactions(self, tx_hashes):
        for tx_hash in tx_hashes:
            if tx_hash in self.transactions:
                del self.transactions[tx_hash]


class LotteryBlockchainCommunity(Community, PeerObserver):
    community_id = b'axiom_lottery_community'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._connected_peers = set()
        self.db = Database()

        # Initialize blockchain
        blockchain_data = self.db.get_blockchain()
        if not blockchain_data:
            # Create genesis block if blockchain is empty
            genesis_block = self.create_genesis_block()
            self.blockchain = [genesis_block]
            self.db.save_block(genesis_block)
        else:
            # Load blockchain from database
            self.blockchain = []
            for block_data in blockchain_data:
                block = Block(
                    index=block_data["index"],
                    timestamp=block_data["timestamp"],
                    bets=block_data["bets"],
                    previous_hash=block_data["previous_hash"],
                    winning_number=block_data["winning_number"],
                    commit_reveals=block_data["commit_reveals"]
                )
                block.hash = block_data["hash"]
                self.blockchain.append(block)

        self.mempool = Mempool()
        # Set database for mempool
        self.mempool.set_database(self.db)
        # Load mempool transactions from database
        for tx_hash, tx_data in self.db.get_mempool_transactions().items():
            self.mempool.transactions[tx_hash] = tx_data

        self.peer_id = str(self.my_peer.address.port)  # Use port as peer ID
        self.commit_values = {}  # Store commit values for randomness
        self.reveal_values = {}  # Store reveal values for randomness
        self.winners = self.db.get_winners()  # Load winners from database

        # Initialize visualizer
        self.visualizer = LotteryVisualizer()

        # Update peer information in database
        self.db.update_peer(self.peer_id, {"active": True, "joined_at": time.time()})

    def create_genesis_block(self):
        return Block(0, time.time(), [], "0", None, [])

    def get_latest_block(self):
        return self.blockchain[-1]

    def add_block(self, block):
        block.previous_hash = self.get_latest_block().hash
        block.hash = block.calculate_hash()
        self.blockchain.append(block)

        # Save block to database
        self.db.save_block(block)

        print(f"Block #{block.index} added to the blockchain")
        return block

    def place_bet(self, bet_number, bet_amount):
        if not (1 <= bet_number <= MAX_LOTTERY_NUMBER):
            print(f"Invalid bet number. Must be between 1 and {MAX_LOTTERY_NUMBER}")
            return False

        if not (MIN_BET_AMOUNT <= bet_amount <= MAX_BET_AMOUNT):
            print(f"Invalid bet amount. Must be between {MIN_BET_AMOUNT} and {MAX_BET_AMOUNT}")
            return False

        bet = {
            "bettor_id": self.peer_id,
            "bet_number": bet_number,
            "bet_amount": bet_amount,
            "timestamp": datetime.now().isoformat()
        }

        # Add to mempool
        tx_hash = self.mempool.add_transaction(bet)
        print(f"Bet placed: {bet_number} for {bet_amount} tokens. Transaction: {tx_hash[:8]}...")

        # Broadcast bet to network
        self.broadcast_bet(bet)
        return True

    def broadcast_bet(self, bet):
        bet_message = BetTicketMessage(
            bettor_id=bet["bettor_id"],
            bet_number=bet["bet_number"],
            bet_amount=bet["bet_amount"],
            timestamp=bet["timestamp"]
        )
        for peer in self.get_peers():
            self.ez_send(peer, bet_message)

    @lazy_wrapper(BetTicketMessage)
    def on_bet_message(self, peer, payload):
        print(f"Received bet from {payload.bettor_id}: {payload.bet_number} for {payload.bet_amount}")
        bet = {
            "bettor_id": payload.bettor_id,
            "bet_number": payload.bet_number,
            "bet_amount": payload.bet_amount,
            "timestamp": payload.timestamp
        }
        self.mempool.add_transaction(bet)

    def generate_commit_value(self):
        """Generate a random value and its hash for commit-reveal scheme"""
        random_value = random.randint(1, 10000)
        commit_hash = sha256(str(random_value).encode()).hexdigest()
        self.commit_values[self.peer_id] = {
            "value": random_value,
            "hash": commit_hash
        }
        return commit_hash

    def reveal_value(self):
        """Reveal the previously committed random value"""
        if self.peer_id in self.commit_values:
            self.reveal_values[self.peer_id] = self.commit_values[self.peer_id]["value"]
            return self.reveal_values[self.peer_id]
        return None

    def determine_winning_number(self, commit_reveals):
        """Determine winning number based on revealed values"""
        if not commit_reveals:
            return random.randint(1, MAX_LOTTERY_NUMBER)

        # Combine all revealed values and hash them
        combined = sum(commit_reveals)
        # Map the hash to a number between 1 and MAX_LOTTERY_NUMBER
        winning_number = (combined % MAX_LOTTERY_NUMBER) + 1
        return winning_number

    def distribute_rewards(self, block):
        """Distribute rewards to winners"""
        if not block.winning_number:
            return

        winners = []
        total_bet_amount = 0

        # Calculate total bet amount and find winners
        for bet in block.bets:
            total_bet_amount += bet["bet_amount"]
            if bet["bet_number"] == block.winning_number:
                winners.append(bet)

        # If no winners, carry over to next draw
        if not winners:
            print(f"No winners for block #{block.index}. Prize pool: {total_bet_amount}")
            winners_data = {
                "winners": [],
                "prize_pool": total_bet_amount,
                "carried_over": True
            }
            self.winners[block.index] = winners_data
            # Save winners to database
            self.db.save_winners(block.index, winners_data)
            return

        # Calculate prize per winner
        prize_per_winner = total_bet_amount / len(winners)
        print(f"Block #{block.index} - {len(winners)} winners! Prize per winner: {prize_per_winner}")

        # Record winners
        winners_data = {
            "winners": winners,
            "prize_pool": total_bet_amount,
            "prize_per_winner": prize_per_winner,
            "carried_over": False
        }
        self.winners[block.index] = winners_data
        # Save winners to database
        self.db.save_winners(block.index, winners_data)

    async def create_lottery_block(self):
        """Create a new block with lottery results"""
        latest_block = self.get_latest_block()
        bets = self.mempool.get_transactions()

        # Collect commit-reveal values from peers
        commit_reveals = list(self.reveal_values.values())

        # Determine winning number
        winning_number = self.determine_winning_number(commit_reveals)

        # Create new block
        new_block = Block(
            index=latest_block.index + 1,
            timestamp=time.time(),
            bets=bets,
            previous_hash=latest_block.hash,
            winning_number=winning_number,
            commit_reveals=commit_reveals
        )

        # Add block to blockchain
        self.add_block(new_block)

        # Distribute rewards
        self.distribute_rewards(new_block)

        # Clear mempool
        tx_hashes = [sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest() for tx in bets]
        self.mempool.clear_transactions(tx_hashes)
        # Also clear from database
        self.db.clear_transactions(tx_hashes)

        # Reset commit-reveal values for next round
        self.commit_values = {}
        self.reveal_values = {}

        print(f"Lottery results for block #{new_block.index}: Winning number is {winning_number}")

        # Visualize lottery results (only for the first peer to avoid duplicate visualizations)
        if self.peer_id == str(self.get_peers()[0].address.port) if self.get_peers() else "8090":
            self.visualizer.plot_lottery_results(self.blockchain, self.winners)

            # Get all bets from all blocks for bet distribution visualization
            all_bets = []
            for block in self.blockchain[1:]:  # Skip genesis block
                all_bets.extend(block.bets)
            if all_bets:
                self.visualizer.plot_bet_distribution(all_bets)

        return new_block

    def on_peer_added(self, peer: Peer) -> None:
        print(f"Peer added: {peer}")
        self._connected_peers.add(peer)

    def on_peer_removed(self, peer: Peer) -> None:
        if peer in self._connected_peers:
            self._connected_peers.remove(peer)

    def started(self):
        """Initialize the community when it's started"""
        self.network.add_peer_observer(self)

        # Register message handlers
        self.add_message_handler(BetTicketMessage, self.on_bet_message)

        # Register tasks
        self.register_task(
            "commit_phase",
            self.commit_phase,
            interval=BLOCK_INTERVAL,
            delay=5.0
        )

        self.register_task(
            "reveal_phase",
            self.reveal_phase,
            interval=BLOCK_INTERVAL,
            delay=BLOCK_INTERVAL / 2
        )

        self.register_task(
            "create_lottery_block_task",
            self.create_lottery_block,
            interval=BLOCK_INTERVAL,
            delay=BLOCK_INTERVAL - 5.0
        )

        # For testing: place a random bet
        self.register_task(
            "place_random_bet",
            self.place_random_bet,
            interval=BLOCK_INTERVAL / 2,
            delay=2.0
        )

        print(f"Lottery blockchain community started. Peer ID: {self.peer_id}")

    async def commit_phase(self):
        """Generate and broadcast commit values"""
        commit_hash = self.generate_commit_value()
        print(f"Generated commit hash: {commit_hash[:8]}...")
        # In a real implementation, we would broadcast this commit hash

    async def reveal_phase(self):
        """Reveal committed values"""
        revealed_value = self.reveal_value()
        if revealed_value:
            print(f"Revealed value: {revealed_value}")
            # In a real implementation, we would broadcast this revealed value

    async def place_random_bet(self):
        """Place a random bet for testing"""
        bet_number = random.randint(1, MAX_LOTTERY_NUMBER)
        bet_amount = random.randint(MIN_BET_AMOUNT, MAX_BET_AMOUNT)
        self.place_bet(bet_number, bet_amount)
