from ipv8.messaging.payload_dataclass import dataclass

from messages.betpayload import BetPayload



@dataclass(msg_id=4)
class Block:
    index: int
    timestamp: float
    transactions: list[BetPayload]
    previous_hash: str
    winning_number: int
    commit_reveals: bytes
    validator: str
    hash: str


    def _to_dict(self):
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
