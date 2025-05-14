from ipv8.messaging.payload_dataclass import dataclass


from messages.block import Block
from db.mempool import Mempool
from db.database import Database
from typing import Dict

import hashlib
import json


BLOCKS_PER_ROUND = 12


@dataclass(msg_id=4)
class BlockChain:
    chain: list[Block]
    round: int

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

    def _get_blocks_for_round(self) -> list[Block]:
        start_index = (self.round - 1) * BLOCKS_PER_ROUND
        end_index = start_index + BLOCKS_PER_ROUND
        return self.chain[start_index:end_index]
