import json
import time
import hashlib
import random
from typing import List, Dict, Any, Optional
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15


class Block:
    def __init__(
        self,
        index: int,
        timestamp: float,
        transactions: List[Dict],
        previous_hash: str,
        winning_number: int = None,
        commit_reveals: Dict = None,
        validator: str = None,
    ):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.winning_number = winning_number
        self.commit_reveals = commit_reveals or {}
        self.validator = validator
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        block_string = json.dumps(
            {
                "index": self.index,
                "timestamp": self.timestamp,
                "transactions": self.transactions,
                "previous_hash": self.previous_hash,
                "winning_number": self.winning_number,
                "commit_reveals": self.commit_reveals,
                "validator": self.validator,
            },
            sort_keys=True,
        ).encode()
        return SHA256.new(block_string).hexdigest()

    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "winning_number": self.winning_number,
            "commit_reveals": self.commit_reveals,
            "validator": self.validator,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, block_dict: Dict) -> "Block":
        block = cls(
            index=block_dict["index"],
            timestamp=block_dict["timestamp"],
            transactions=block_dict["transactions"],
            previous_hash=block_dict["previous_hash"],
            winning_number=block_dict.get("winning_number"),
            commit_reveals=block_dict.get("commit_reveals", {}),
            validator=block_dict.get("validator"),
        )
        block.hash = block_dict["hash"]
        return block


# TODO: to byte


class LotteryBlockchain:
    def __init__(self, db_manager=None):
        self.chain = []
        self.mempool = []
        self.validators = {}  # peer_id -> stake amount
        self.db_manager = db_manager
        self.create_genesis_block()

    def create_genesis_block(self) -> None:
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            transactions=[],
            previous_hash="0",
            winning_number=None,
            commit_reveals={},
            validator=None,
        )
        self.chain.append(genesis_block)
        if self.db_manager:
            self.db_manager.save_block(genesis_block.to_dict())

    def get_latest_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, transaction: Dict) -> bool:
        # Validate transaction
        if not self._validate_transaction(transaction):
            return False

        # Add to mempool
        self.mempool.append(transaction)
        if self.db_manager:
            self.db_manager.save_transaction(transaction)
        return True

    def _validate_transaction(self, transaction: Dict) -> bool:
        # Basic validation
        required_fields = ["sender", "bet_number", "amount", "timestamp", "signature"]
        if not all(field in transaction for field in required_fields):
            return False

        # Validate bet number (1-99)
        if not (1 <= transaction["bet_number"] <= 99):
            return False

        # Validate amount (1-99 tokens)
        if not (1 <= transaction["amount"] <= 99):
            return False

        # Validate signature (in a real system)
        # This is simplified for the demo
        return True

    def create_block(
        self, validator: str, winning_number: int, commit_reveals: Dict
    ) -> Optional[Block]:
        if not self.mempool:
            # No transactions, but we still create a daily block
            transactions = []
        else:  # pop
            transactions = self.mempool.copy()
            self.mempool = []

        # Create new block
        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            transactions=transactions,
            previous_hash=self.get_latest_block().hash,
            winning_number=winning_number,
            commit_reveals=commit_reveals,
            validator=validator,
        )

        # Add to chain
        self.chain.append(new_block)
        if self.db_manager:  # save bytes
            self.db_manager.save_block(new_block.to_dict())
            self.db_manager.clear_mempool_transactions(
                [tx.get("id") for tx in transactions]
            )

        return new_block

    def validate_chain(self, chain: List[Block]) -> bool:
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i - 1]

            # Check hash integrity
            if current.previous_hash != previous.hash:
                return False

            # Check block hash
            if current.hash != current.calculate_hash():
                return False

        return True

    def resolve_conflicts(self, peer_chains: List[List[Dict]]) -> bool:
        max_length = len(self.chain)
        new_chain = None

        for peer_chain_dicts in peer_chains:
            # Convert dict to Block objects
            peer_chain = [
                Block.from_dict(block_dict) for block_dict in peer_chain_dicts
            ]

            # Check if chain is valid and longer
            if len(peer_chain) > max_length and self.validate_chain(peer_chain):
                max_length = len(peer_chain)
                new_chain = peer_chain

        if new_chain:
            self.chain = new_chain
            if self.db_manager:
                for block in new_chain:
                    self.db_manager.save_block(block.to_dict())
            return True

        return False

    def register_validator(self, peer_id: str, stake: int) -> bool:
        if stake <= 0:
            return False

        self.validators[peer_id] = stake
        return True

    def select_validator(self) -> str:
        if not self.validators:
            return None

        # Simple PoS: probability proportional to stake
        total_stake = sum(self.validators.values())
        selection_point = random.random() * total_stake

        current_sum = 0
        for validator_id, stake in self.validators.items():
            current_sum += stake
            if current_sum >= selection_point:
                return validator_id

        # Fallback to random selection
        return random.choice(list(self.validators.keys()))

    def calculate_lottery_results(self, block: Block) -> Dict[str, Any]:
        if (
            not block.winning_number
            or block.winning_number < 1
            or block.winning_number > 99
        ):
            return {"winners": [], "total_pot": 0, "winning_number": None}

        winning_number = block.winning_number
        winners = []
        total_pot = 0

        # Calculate total pot and find winners
        for tx in block.transactions:
            total_pot += tx["amount"]
            if tx["bet_number"] == winning_number:
                winners.append(tx)

        # Calculate rewards
        results = {
            "winning_number": winning_number,
            "total_pot": total_pot,
            "winners": winners,
        }

        if winners:
            # Distribute pot among winners proportionally to their bet amount
            total_winning_amount = sum(winner["amount"] for winner in winners)
            for winner in winners:
                winner["reward"] = (winner["amount"] / total_winning_amount) * total_pot

        return results

    def to_dict(self) -> Dict:
        return {
            "chain": [block.to_dict() for block in self.chain],
            "mempool": self.mempool,
            "validators": self.validators,
        }

    def load_from_dict(self, blockchain_dict: Dict) -> None:
        self.chain = [
            Block.from_dict(block_dict) for block_dict in blockchain_dict["chain"]
        ]
        self.mempool = blockchain_dict["mempool"]
        self.validators = blockchain_dict["validators"]
