from ipv8.messaging.payload_dataclass import dataclass


@dataclass(msg_id=2)
class TransactionsRequest:
    last_seen_timestamp: float


@dataclass(msg_id=3)
class TransactionsResponse:
    transactions: str
    has_more: bool
