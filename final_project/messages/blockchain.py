from ipv8.messaging.payload_dataclass import dataclass


from messages.block import Block
from db.mempool import Mempool
from db.database import Database
from typing import Dict

import hashlib
import json


@dataclass(msg_id=4)
class BlockChain:
    chain: list[Block]

    def _get_latest_block(self) -> Block:
        return self.chain[-1]

    def _validate_transaction(self, transaction: Dict) -> bool:
        required_fields = ["sender", "bet_number",
                           "amount", "timestamp", "signature"]
        if not all(field in transaction for field in required_fields):
            return False

        if not (1 <= transaction["bet_number"] <= 99):
            return False

        if not (1 <= transaction["amount"] <= 99):
            return False

        return True
