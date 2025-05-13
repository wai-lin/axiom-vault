from ipv8.messaging.payload_dataclass import dataclass


@dataclass(msg_id=1)
class BetTicketMessage:
    bettor_id: str
    bet_number: int
    bet_amount: float
    timestamp: str
