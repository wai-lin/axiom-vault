import time
import json
import hashlib
import random
from typing import Dict, List, Any, Optional, Tuple
from ipv8.community import Community
from ipv8.lazy_community import lazy_wrapper
from ipv8.messaging.bloom_filter import BloomFilter
from ipv8.messaging.payload import Payload
from ipv8.peer import Peer
from ipv8.types import Address
from ipv8.util import succeed

from blockchain import LotteryBlockchain, Block
from db import DatabaseManager

# Message types
MSG_TRANSACTION = 1
MSG_BLOCK = 2
MSG_CHAIN_REQUEST = 3
MSG_CHAIN_RESPONSE = 4
MSG_MEMPOOL_REQUEST = 5
MSG_MEMPOOL_RESPONSE = 6
MSG_COMMIT = 7
MSG_REVEAL = 8

class TransactionPayload(Payload):
    format_list = ['varlenH']
    
    def __init__(self, transaction: Dict):
        self.transaction = transaction
    
    def to_pack_list(self) -> List:
        return [('varlenH', json.dumps(self.transaction).encode())]
    
    @classmethod
    def from_unpack_list(cls, transaction_json: bytes) -> 'TransactionPayload':
        return TransactionPayload(json.loads(transaction_json.decode()))

class BlockPayload(Payload):
    format_list = ['varlenH']
    
    def __init__(self, block: Dict):
        self.block = block
    
    def to_pack_list(self) -> List:
        return [('varlenH', json.dumps(self.block).encode())]
    
    @classmethod
    def from_unpack_list(cls, block_json: bytes) -> 'BlockPayload':
        return BlockPayload(json.loads(block_json.decode()))

class ChainRequestPayload(Payload):
    format_list = ['I']
    
    def __init__(self, latest_block_index: int):
        self.latest_block_index = latest_block_index
    
    def to_pack_list(self) -> List:
        return [('I', self.latest_block_index)]
    
    @classmethod
    def from_unpack_list(cls, latest_block_index: int) -> 'ChainRequestPayload':
        return ChainRequestPayload(latest_block_index)

class ChainResponsePayload(Payload):
    format_list = ['varlenH']
    
    def __init__(self, blocks: List[Dict]):
        self.blocks = blocks
    
    def to_pack_list(self) -> List:
        return [('varlenH', json.dumps(self.blocks).encode())]
    
    @classmethod
    def from_unpack_list(cls, blocks_json: bytes) -> 'ChainResponsePayload':
        return ChainResponsePayload(json.loads(blocks_json.decode()))

class MempoolRequestPayload(Payload):
    format_list = ['varlenH']
    
    def __init__(self, bloom_filter: bytes):
        self.bloom_filter = bloom_filter
    
    def to_pack_list(self) -> List:
        return [('varlenH', self.bloom_filter)]
    
    @classmethod
    def from_unpack_list(cls, bloom_filter: bytes) -> 'MempoolRequestPayload':
        return MempoolRequestPayload(bloom_filter)

class MempoolResponsePayload(Payload):
    format_list = ['varlenH']
    
    def __init__(self, transactions: List[Dict]):
        self.transactions = transactions
    
    def to_pack_list(self) -> List:
        return [('varlenH', json.dumps(self.transactions).encode())]
    
    @classmethod
    def from_unpack_list(cls, transactions_json: bytes) -> 'MempoolResponsePayload':
        return MempoolResponsePayload(json.loads(transactions_json.decode()))

class CommitPayload(Payload):
    format_list = ['varlenH', 'varlenH']
    
    def __init__(self, peer_id: str, commit_hash: str):
        self.peer_id = peer_id
        self.commit_hash = commit_hash
    
    def to_pack_list(self) -> List:
        return [
            ('varlenH', self.peer_id.encode()),
            ('varlenH', self.commit_hash.encode())
        ]
    
    @classmethod
    def from_unpack_list(cls, peer_id: bytes, commit_hash: bytes) -> 'CommitPayload':
        return CommitPayload(peer_id.decode(), commit_hash.decode())

class RevealPayload(Payload):
    format_list = ['varlenH', 'varlenH', 'varlenH']
    
    def __init__(self, peer_id: str, random_value: str, nonce: str):
        self.peer_id = peer_id
        self.random_value = random_value
        self.nonce = nonce
    
    def to_pack_list(self) -> List:
        return [
            ('varlenH', self.peer_id.encode()),
            ('varlenH', self.random_value.encode()),
            ('varlenH', self.nonce.encode())
        ]
    
    @classmethod
    def from_unpack_list(cls, peer_id: bytes, random_value: bytes, nonce: bytes) -> 'RevealPayload':
        return RevealPayload(peer_id.decode(), random_value.decode(), nonce.decode())

class LotteryNetworkCommunity(Community):
    community_id = b'\x01LotteryNetwork'
    
    def __init__(self, my_peer, endpoint, network, db_path="./lottery_db", max_peers=10):
        super().__init__(my_peer, endpoint, network, max_peers=max_peers)
        
        # Initialize database
        self.db_manager = DatabaseManager(db_path)
        
        # Initialize blockchain
        self.blockchain = LotteryBlockchain(self.db_manager)
        
        # Initialize commit-reveal scheme
        self.commits = {}
        self.reveals = {}
        self.my_random_value = None
        self.my_nonce = None
        self.my_commit_hash = None
        
        # Register message handlers
        self.add_message_handler(MSG_TRANSACTION, self.on_transaction)
        self.add_message_handler(MSG_BLOCK, self.on_block)
        self.add_message_handler(MSG_CHAIN_REQUEST, self.on_chain_request)
        self.add_message_handler(MSG_CHAIN_RESPONSE, self.on_chain_response)
        self.add_message_handler(MSG_MEMPOOL_REQUEST, self.on_mempool_request)
        self.add_message_handler(MSG_MEMPOOL_RESPONSE, self.on_mempool_response)
        self.add_message_handler(MSG_COMMIT, self.on_commit)
        self.add_message_handler(MSG_REVEAL, self.on_reveal)
        
        # Register as validator with random stake (1-100)
        self.stake = random.randint(1, 100)
        self.blockchain.register_validator(str(self.my_peer.mid), self.stake)
        
        # Schedule tasks
        self.register_task("sync_blockchain", self.sync_blockchain, interval=10.0)
        self.register_task("sync_mempool", self.sync_mempool, interval=5.0)
        self.register_task("lottery_cycle", self.lottery_cycle, interval=30.0)  # 30 seconds = 1 day in simulation
        
        # For testing: place random bets
        self.register_task("place_random_bet", self.place_random_bet, interval=random.uniform(3.0, 10.0))
    
    def started(self) -> None:
        """Called when the community is started."""
        super().started()
        print(f"Lottery peer {self.my_peer.mid.hex()[:8]} started with stake {self.stake}")
    
    def place_random_bet(self) -> None:
        """Place a random bet for testing purposes"""
        bet_number = random.randint(1, 99)
        amount = random.randint(1, 99)
        
        transaction = {
            "id": hashlib.sha256(f"{time.time()}-{self.my_peer.mid.hex()}".encode()).hexdigest(),
            "sender": self.my_peer.mid.hex(),
            "bet_number": bet_number,
            "amount": amount,
            "timestamp": time.time(),
            "signature": "dummy_signature"  # In a real system, this would be a cryptographic signature
        }
        
        # Add to local blockchain and broadcast
        if self.blockchain.add_transaction(transaction):
            print(f"Placed bet: number {bet_number}, amount {amount}")
            self.broadcast_transaction(transaction)
    
    def broadcast_transaction(self, transaction: Dict) -> None:
        """Broadcast a transaction to all peers"""
        payload = TransactionPayload(transaction)
        self.ez_send(self.get_peers(), MSG_TRANSACTION, payload)
    
    @lazy_wrapper(TransactionPayload)
    def on_transaction(self, peer: Peer, payload: TransactionPayload) -> None:
        """Handle received transaction"""
        transaction = payload.transaction
        if self.blockchain.add_transaction(transaction):
            print(f"Received valid transaction from {transaction['sender'][:8]}")
    
    def broadcast_block(self, block: Block) -> None:
        """Broadcast a block to all peers"""
        payload = BlockPayload(block.to_dict())
        self.ez_send(self.get_peers(), MSG_BLOCK, payload)
    
    @lazy_wrapper(BlockPayload)
    def on_block(self, peer: Peer, payload: BlockPayload) -> None:
        """Handle received block"""
        block_dict = payload.block
        block = Block.from_dict(block_dict)
        
        # Check if block index is next in our chain
        if block.index == len(self.blockchain.chain):
            # Validate and add block
            if block.previous_hash == self.blockchain.get_latest_block().hash:
                self.blockchain.chain.append(block)
                print(f"Added new block #{block.index} from peer {peer.mid.hex()[:8]}")
                
                # Process lottery results
                results = self.blockchain.calculate_lottery_results(block)
                if results["winners"]:
                    print(f"Lottery results: winning number {results['winning_number']}, {len(results['winners'])} winners")
                else:
                    print(f"Lottery results: winning number {results['winning_number']}, no winners")
                
                # Clear mempool of transactions included in this block
                tx_ids = [tx.get("id") for tx in block.transactions]
                self.db_manager.clear_mempool_transactions(tx_ids)
                
                # Reset commit-reveal for next round
                self.commits = {}
                self.reveals = {}
                self.my_random_value = None
                self.my_nonce = None
                self.my_commit_hash = None
        elif block.index > len(self.blockchain.chain):
            # We're behind, request the chain
            self.request_chain(peer)
    
    def request_chain(self, peer: Optional[Peer] = None) -> None:
        """Request blockchain from peers"""
        latest_block_index = len(self.blockchain.chain) - 1
        payload = ChainRequestPayload(latest_block_index)
        
        if peer:
            self.ez_send([peer], MSG_CHAIN_REQUEST, payload)
        else:
            self.ez_send(self.get_peers(), MSG_CHAIN_REQUEST, payload)
    
    @lazy_wrapper(ChainRequestPayload)
    def on_chain_request(self, peer: Peer, payload: ChainRequestPayload) -> None:
        """Handle chain request"""
        latest_block_index = payload.latest_block_index
        
        # Send blocks newer than the requested index
        blocks_to_send = [block.to_dict() for block in self.blockchain.chain[latest_block_index+1:]]
        if blocks_to_send:
            response_payload = ChainResponsePayload(blocks_to_send)
            self.ez_send([peer], MSG_CHAIN_RESPONSE, response_payload)
    
    @lazy_wrapper(ChainResponsePayload)
    def on_chain_response(self, peer: Peer, payload: ChainResponsePayload) -> None:
        """Handle chain response"""
        received_blocks = payload.blocks
        
        if not received_blocks:
            return
        
        # Convert to Block objects
        blocks = [Block.from_dict(block_dict) for block_dict in received_blocks]
        
        # Check if the first block connects to our chain
        if blocks[0].index == len(self.blockchain.chain) and blocks[0].previous_hash == self.blockchain.get_latest_block().hash:
            # Add all blocks
            for block in blocks:
                self.blockchain.chain.append(block)
                print(f"Added block #{block.index} from chain sync")
                
                # Process lottery results
                results = self.blockchain.calculate_lottery_results(block)
                if results["winners"]:
                    print(f"Lottery results: winning number {results['winning_number']}, {len(results['winners'])} winners")
                else:
                    print(f"Lottery results: winning number {results['winning_number']}, no winners")
    
    def sync_blockchain(self) -> None:
        """Sync blockchain with peers"""
        if self.get_peers():
            self.request_chain()
    
    def sync_mempool(self) -> None:
        """Sync mempool with peers using bloom filters"""
        if not self.get_peers():
            return
        
        # Create bloom filter of our transactions
        bloom = self.db_manager.create_tx_bloom_filter()
        bloom_bytes = bloom.to_bytes()
        
        # Request transactions from peers
        payload = MempoolRequestPayload(bloom_bytes)
        self.ez_send(self.get_peers(), MSG_MEMPOOL_REQUEST, payload)
    
    @lazy_wrapper(MempoolRequestPayload)
    def on_mempool_request(self, peer: Peer, payload: MempoolRequestPayload) -> None:
        """Handle mempool request with bloom filter"""
        peer_bloom = BloomFilter.from_bytes(payload.bloom_filter)
        
        # Get all mempool transactions
        all_txs = self.db_manager.get_all_mempool_transactions()
        
        # Filter out transactions the peer likely already has
        txs_to_send = []
        for tx in all_txs:
            tx_id = tx.get("id", str(tx["timestamp"]) + tx["sender"])
            if tx_id.encode() not in peer_bloom:
                txs_to_send.append(tx)
        
        if txs_to_send:
            response_payload = MempoolResponsePayload(txs_to_send)
            self.ez_send([peer], MSG_MEMPOOL_RESPONSE, response_payload)
    
    @lazy_wrapper(MempoolResponsePayload)
    def on_mempool_response(self, peer: Peer, payload: MempoolResponsePayload) -> None:
        """Handle mempool response"""
        transactions = payload.transactions
        
        added_count = 0
        for tx in transactions:
            if self.blockchain.add_transaction(tx):
                added_count += 1
        
        if added_count > 0:
            print(f"Added {added_count} transactions from peer {peer.mid.hex()[:8]}")
    
    def start_commit_phase(self) -> None:
        """Start the commit phase of the commit-reveal scheme"""
        # Generate random value and nonce
        self.my_random_value = str(random.randint(1, 1000))
        self.my_nonce = hashlib.sha256(str(time.time()).encode()).hexdigest()
        
        # Create commit hash
        commit_data = f"{self.my_random_value}-{self.my_nonce}"
        self.my_commit_hash = hashlib.sha256(commit_data.encode()).hexdigest()
        
        # Broadcast commit
        payload = CommitPayload(self.my_peer.mid.hex(), self.my_commit_hash)
        self.ez_send(self.get_peers(), MSG_COMMIT, payload)
        
        # Add own commit
        self.commits[self.my_peer.mid.hex()] = self.my_commit_hash
        
        print(f"Sent commit: {self.my_commit_hash[:8]}")
    
    @lazy_wrapper(CommitPayload)
    def on_commit(self, peer: Peer, payload: CommitPayload) -> None:
        """Handle commit message"""
        peer_id = payload.peer_id
        commit_hash = payload.commit_hash
        
        # Store commit
        self.commits[peer_id] = commit_hash
        print(f"Received commit from {peer_id[:8]}: {commit_hash[:8]}")
    
    def start_reveal_phase(self) -> None:
        """Start the reveal phase of the commit-reveal scheme"""
        if not self.my_random_value or not self.my_nonce:
            print("Cannot reveal: no random value or nonce")
            return
        
        # Broadcast reveal
        payload = RevealPayload(self.my_peer.mid.hex(), self.my_random_value, self.my_nonce)
        self.ez_send(self.get_peers(), MSG_REVEAL, payload)
        
        # Add own reveal
        self.reveals[self.my_peer.mid.hex()] = {
            "value": self.my_random_value,
            "nonce": self.my_nonce
        }
        
        print(f"Sent reveal: value={self.my_random_value}, nonce={self.my_nonce[:8]}")
    
    @lazy_wrapper(RevealPayload)
    def on_reveal(self, peer: Peer, payload: RevealPayload) -> None:
        """Handle reveal message"""
        peer_id = payload.peer_id
        random_value = payload.random_value
        nonce = payload.nonce
        
        # Verify against commit
        if peer_id in self.commits:
            commit_hash = self.commits[peer_id]
            verify_data = f"{random_value}-{nonce}"
            verify_hash = hashlib.sha256(verify_data.encode()).hexdigest()
            
            if verify_hash == commit_hash:
                # Store valid reveal
                self.reveals[peer_id] = {
                    "value": random_value,
                    "nonce": nonce
                }
                print(f"Received valid reveal from {peer_id[:8]}: value={random_value}")
            else:
                print(f"Invalid reveal from {peer_id[:8]}: hash mismatch")
        else:
            print(f"Received reveal from {peer_id[:8]} without prior commit")
    
    def calculate_winning_number(self) -> int:
        """Calculate winning number from revealed values"""
        if not self.reveals:
            # Fallback to random number if no reveals
            return random.randint(1, 99)
        
        # Combine all revealed values
        combined_value = 0
        for peer_id, reveal_data in self.reveals.items():
            try:
                value = int(reveal_data["value"])
                combined_value += value
            except (ValueError, KeyError):
                pass
        
        # Map to range 1-99
        winning_number = (combined_value % 99) + 1
        return winning_number
    
    def lottery_cycle(self) -> None:
        """Run one lottery cycle (commit -> reveal -> block creation)"""
        # Start commit phase
        self.start_commit_phase()
        
        # Wait for commits (5 seconds)
        yield self.pause(5.0)
        
        # Start reveal phase
        self.start_reveal_phase()
        
        # Wait for reveals (5 seconds)
        yield self.pause(5.0)
        
        # Calculate winning number
        winning_number = self.calculate_winning_number()
        print(f"Calculated winning number: {winning_number}")
        
        # Check if we are the validator for this round
        selected_validator = self.blockchain.select_validator()
        if selected_validator == self.my_peer.mid.hex():
            print(f"I am the validator for this round!")
            
            # Create new block
            new_block = self.blockchain.create_block(
                validator=self.my_peer.mid.hex(),
                winning_number=winning_number,
                commit_reveals=self.reveals
            )
            
            # Broadcast block
            self.broadcast_block(new_block)
            
            # Calculate and display results
            results = self.blockchain.calculate_lottery_results(new_block)
            if results["winners"]:
                print(f"Lottery results: winning number {results['winning_number']}, {len(results['winners'])} winners")
                for winner in results["winners"]:
                    print(f"  Winner: {winner['sender'][:8]}, bet: {winner['amount']}, reward: {winner['reward']:.2f}")
            else:
                print(f"Lottery results: winning number {results['winning_number']}, no winners")
        
        # Reset for next round
        self.commits = {}
        self.reveals = {}
        self.my_random_value = None
        self.my_nonce = None
        self.my_commit_hash = None