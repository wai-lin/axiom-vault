from ipv8.messaging.payload_dataclass import dataclass

from messages.betpayload import BetPayload


import json
import hashlib
from dataclasses import asdict


@dataclass(msg_id=4)
class Block:
    index: int
    timestamp: float
    transactions: list[BetPayload]
    previous_hash: str
    hash: str
    winning_number: int
    nonce: int
    difficulty: int  # Default is 1

    def _to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "winning_number": self.winning_number,
            "hash": self.hash,
            "difficulty": self.difficulty,
            "nonce": self.nonce
        }

    def _calculate_hash_string(self, nonce) -> str:
        block_data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [asdict(item) for item in self.transactions],
            "previous_hash": self.previous_hash,
            "winning_number": self.winning_number,
            "difficulty": self.difficulty,
            "nonce": nonce,
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return block_string
