from ipv8.messaging.payload_dataclass import dataclass


from messages.betpayload import BetPayload

import hashlib
import json


@dataclass(msg_id=4)
class Block:
    index: int
    timestamp: float
    transactions: list[BetPayload]
    previous_hash: str
    winning_number: int
    commit_reveals: bytes
    validator: str

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
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self):
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
