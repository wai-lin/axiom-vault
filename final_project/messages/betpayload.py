from ipv8.messaging.payload_dataclass import dataclass


import hashlib
import json


@dataclass(msg_id=1)
class BetPayload:
    bettor_id: str
    bet_number: int
    bet_amount: int
    timestamp: float
    signature: str

    def _generate_txid(self):
        payload_data = {
            "bettor_id": self.bettor_id,
            "bet_number": self.bet_number,
            "bet_amount": self.bet_amount,
            "timestamp": self.timestamp,
        }
        payload_bytes = json.dumps(
            payload_data, sort_keys=True).encode('utf-8')
        return hashlib.sha256(payload_bytes).hexdigest()


@dataclass(msg_id=2)
class GetTransactionsRequest:
    last_seen_timestamp: float


@dataclass(msg_id=3)
class TransactionsResponse:
    transactions: str
