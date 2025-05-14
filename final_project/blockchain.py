import json
import time
import hashlib
import random
from typing import List, Dict, Any, Optional, Tuple

from ipv8.messaging.payload_dataclass import dataclass
from final_project.community.setup import MyCommunity
from messages.betpayload import BetPayload
from messages.commitreveal import CommitReveal
from db.mempool import Mempool


@dataclass(msg_id=4)
class Block:
    """
    Block in the lottery blockchain
    
    Attributes:
        index: Block number in the chain
        timestamp: Time when the block was created
        transactions: List of bet transactions included in this block
        previous_hash: Hash of the previous block
        winning_number: The 2-digit winning lottery number (0-99)
        commit_reveals: Bytes containing commit reveals for the lottery
        validator: ID of the node that validated this block
    """
    index: int
    timestamp: float
    transactions: List[BetPayload]
    previous_hash: str
    winning_number: int = None
    commit_reveals: bytes = b''
    validator: str = None

    def __post_init__(self):
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """
        Calculate the hash of the block based on its contents
        
        Returns:
            str: SHA-256 hash of the block
        """
        # Convert transactions to a serializable format
        tx_data = []
        for tx in self.transactions:
            if hasattr(tx, '_generate_txid'):
                tx_data.append(tx._generate_txid())
            else:
                # Fallback if transaction doesn't have _generate_txid method
                tx_data.append(str(tx))

        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": tx_data,
            "previous_hash": self.previous_hash,
            "winning_number": self.winning_number,
            "commit_reveals": self.commit_reveals.hex() if self.commit_reveals else '',
            "validator": self.validator
        }, sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self) -> Dict:
        """
        Convert block to dictionary for serialization
        
        Returns:
            Dict: Block data as dictionary
        """
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [tx._generate_txid() for tx in self.transactions if hasattr(tx, '_generate_txid')],
            "previous_hash": self.previous_hash,
            "winning_number": self.winning_number,
            "commit_reveals": self.commit_reveals.hex() if self.commit_reveals else '',
            "validator": self.validator,
            "hash": self.hash
        }


class LotteryBlockchain:
    def __init__(self, mempool: Optional[Mempool] = None):
        """
        Initialize the lottery blockchain
        
        Args:
            mempool: Optional mempool for transactions
        """
        self.chain = []
        self.mempool = mempool if mempool else Mempool()
        self.validators = {}  # peer_id -> CommitReveal data
        self.balances = {}  # peer_id -> balance
        # Create the genesis block
        self.create_genesis_block()

    def create_genesis_block(self) -> None:
        """
        Create the first block in the chain with no transactions
        """
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            transactions=[],
            previous_hash="0" * 64,  # 64 zeros for genesis block
            winning_number=None,  # No winning number for genesis
            commit_reveals=b'',  # Empty commit reveals for genesis
            validator=None  # No validator for genesis
        )
        self.chain.append(genesis_block)
        print(f"Genesis block created with hash: {genesis_block.hash}")

    def get_latest_block(self) -> Block:
        """
        Return the most recent block in the chain
        
        Returns:
            Block: The latest block in the chain
        """
        return self.chain[-1]

    def is_chain_valid(self) -> bool:
        """
        Validate the entire blockchain
        
        Returns:
            bool: True if the chain is valid, False otherwise
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Verify current block hash
            if current_block.hash != current_block.calculate_hash():
                print(f"Invalid hash in block {i}")
                return False

            # Verify chain linkage
            if current_block.previous_hash != previous_block.hash:
                print(f"Chain broken at block {i}")
                return False

        return True

    def add_bet_transaction(self, bet: BetPayload) -> bool:
        """
        Add a new bet transaction to the mempool
        
        Args:
            bet: The bet transaction to add
            
        Returns:
            bool: True if the transaction was added, False otherwise
        """
        # Verify the transaction is valid
        if not self._validate_bet(bet):
            return False

        # Add to mempool
        txid = bet._generate_txid()
        self.mempool.add_transaction(txid, bet)
        return True

    def _validate_bet(self, bet: BetPayload) -> bool:
        """
        Validate a bet transaction
        
        Args:
            bet: The bet transaction to validate
            
        Returns:
            bool: True if the transaction is valid, False otherwise
        """
        # Check if bet number is valid (0-99)
        if not 0 <= bet.bet_number <= 99:
            print(f"Invalid bet number: {bet.bet_number}")
            return False

        # Check if bet amount is positive
        if bet.bet_amount <= 0:
            print(f"Invalid bet amount: {bet.bet_amount}")
            return False

        # In a real implementation, we would verify the signature here
        # For simplicity, we'll assume all signatures are valid

        return True

    def register_commit_reveal(self, peer_id: str, random_value: int) -> CommitReveal:
        """
        Register a commit-reveal for a validator
        
        Args:
            peer_id: The ID of the validator peer
            random_value: The random value to commit (0-99)
            
        Returns:
            CommitReveal: The commit-reveal object to be shared with other validators
        """
        # Create a new CommitReveal object
        commit_reveal = CommitReveal(validator_id=peer_id)

        # Generate commit hash and salt
        commit_reveal.generate_commit(random_value)

        # Store validator's commit-reveal object
        self.validators[peer_id] = commit_reveal

        # Return commit-reveal object (only with commit_hash, not reveal_value)
        return CommitReveal(
            validator_id=peer_id,
            commit_hash=commit_reveal.commit_hash
        )

    def verify_reveal(self, peer_id: str, revealed_value: int, salt: str) -> bool:
        """
        Verify a revealed value against a previously committed hash
        
        Args:
            peer_id: The ID of the validator peer
            revealed_value: The revealed random value
            salt: The salt used in the commit
            
        Returns:
            bool: True if the reveal is valid, False otherwise
        """
        if peer_id not in self.validators:
            return False

        # Get the validator's commit-reveal object
        commit_reveal = self.validators[peer_id]

        # Verify the reveal
        return commit_reveal.verify_reveal(revealed_value, salt)

    def create_new_block(self, validator_id: str) -> Block:
        """
        Create a new block with transactions from the mempool
        
        Args:
            validator_id: The ID of the validator creating the block
            
        Returns:
            Block: The newly created block
        """
        # Get the latest block
        latest_block = self.get_latest_block()

        # Get transactions from mempool
        transactions = self.mempool.get_all_transaction()
        # Limit to 10 transactions per block
        transactions = transactions[:10] if len(transactions) > 10 else transactions

        # Generate winning number using commit-reveals
        winning_number, commit_reveals = self._generate_winning_number(validator_id)

        # Create new block
        new_block = Block(
            index=latest_block.index + 1,
            timestamp=time.time(),
            transactions=transactions,
            previous_hash=latest_block.hash,
            winning_number=winning_number,
            commit_reveals=commit_reveals,
            validator=validator_id
        )

        # Process winning bets
        self._process_winning_bets(new_block)

        # Clear processed transactions from mempool
        for tx in transactions:
            txid = tx._generate_txid()
            self.mempool.remove_transaction(txid)

        # Add block to chain
        self.chain.append(new_block)

        return new_block

    def collect_commit_reveals(self, validator_ids: List[str]) -> List[CommitReveal]:
        """
        Collect commit-reveals from multiple validators
        
        Args:
            validator_ids: List of validator IDs to collect from
            
        Returns:
            List[CommitReveal]: List of commit-reveal objects
        """
        commit_reveals = []
        for validator_id in validator_ids:
            if validator_id in self.validators:
                commit_reveals.append(self.validators[validator_id])
        return commit_reveals

    def _generate_winning_number(self, validator_id: str) -> Tuple[int, bytes]:
        """
        Generate a winning lottery number using commit-reveals
        
        Args:
            validator_id: The ID of the validator creating the block
            
        Returns:
            Tuple[int, bytes]: (winning_number, commit_reveals_data)
        """
        # In a real implementation, we would collect commit-reveals from multiple validators
        # For this implementation, we'll use all available validators' reveals if possible

        # Get all validators with reveals
        valid_validators = [v_id for v_id in self.validators.keys()
                            if self.validators[v_id].reveal_value is not None]

        if not valid_validators:
            # Fallback to a simple random number if no commit-reveal data
            return random.randint(0, 99), b''

        # Collect all commit-reveals
        commit_reveals = self.collect_commit_reveals(valid_validators)

        # Combine all reveal values to generate the winning number
        # XOR all reveal values together for a simple combination
        winning_number = 0
        for cr in commit_reveals:
            if cr.reveal_value is not None:
                winning_number ^= cr.reveal_value

        # Ensure the winning number is in range 0-99
        winning_number = winning_number % 100

        # Serialize all commit-reveals data
        commit_reveals_data = json.dumps([cr.to_dict() for cr in commit_reveals]).encode()

        # Return the winning number and commit-reveals data
        return winning_number, commit_reveals_data

    def _process_winning_bets(self, block: Block) -> None:
        """
        Process winning bets and update balances
        
        Args:
            block: The block containing transactions to process
        """
        if block.winning_number is None:
            return

        for tx in block.transactions:
            # Check if this bet is a winner
            if tx.bet_number == block.winning_number:
                # Calculate winnings (10x the bet amount)
                winnings = tx.bet_amount * 10

                # Update bettor's balance
                if tx.bettor_id not in self.balances:
                    self.balances[tx.bettor_id] = 0

                self.balances[tx.bettor_id] += winnings
                print(f"Winner! {tx.bettor_id} won {winnings} tokens with bet {tx.bet_number}")

    def get_balance(self, peer_id: str) -> int:
        """
        Get the balance for a peer
        
        Args:
            peer_id: The ID of the peer
            
        Returns:
            int: The peer's balance
        """
        return self.balances.get(peer_id, 0)
