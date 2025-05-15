from ipv8.messaging.payload_dataclass import dataclass


@dataclass(msg_id=6)
class LotteryResult:
    round: int
    winning_number: int
    total_amount: int
