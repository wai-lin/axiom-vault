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
    winning_number: int
    hash: str

    def _calculate_block_hash(self):
        try:
            block_data = {
                "index": self.index,
                "timestamp": self.timestamp,
                "transactions": [asdict(payload) for payload in self.transactions],
                "previous_hash": self.previous_hash,
                "winning_number": self.winning_number,
            }
            block_string = json.dumps(block_data, sort_keys=True).encode()
            hash_string = hashlib.sha256(block_string).hexdigest()
            self.hash = hash_string
        except TypeError as e:
            print(
                f"TypeError encountered while calculating hash for block {self.index}: {e}")
            print(f"Block data: {block_data}")
        except Exception as e:
            print(
                f"An unexpected error occurred while calculating hash for block {self.index}: {e}")
            print(f"Block data: {block_data}")

        return self

    def _to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "winning_number": self.winning_number,
            "hash": self.hash,
        }
