from typing import Dict, List, Optional
from db.mempool import Mempool
from messages.betpayload import BetPayload


class Database:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not Database._initialized:
            self.blockchain_db = {}
            self.mempool = Mempool()  # Get the singleton Mempool instance
            Database._initialized = True

    def save_block(self, block: Dict) -> None:
        block_key = f"block_{block['index']}"
        self.blockchain_db[block_key] = block

    def get_block(self, index: int) -> Optional[Dict]:
        block_key = f"block_{index}"
        return self.blockchain_db.get(block_key)

    def get_latest_block_index(self) -> int:
        latest_index = -1
        for key in self.blockchain_db:
            if key.startswith("block_"):
                try:
                    index = int(key.split("_")[1])
                    latest_index = max(latest_index, index)
                except (ValueError, IndexError):
                    pass
        return latest_index if latest_index >= 0 else 0

    def get_all_blocks(self) -> List[Dict]:
        blocks = [block for key, block in self.blockchain_db.items()
                  if key.startswith("block_")]
        blocks.sort(key=lambda x: x['index'])
        return blocks

    def save_transaction(self, transaction: Dict) -> None:
        tx_id = transaction.get(
            "id", str(transaction["timestamp"]) + transaction["sender"])
        bet_payload = BetPayload(**transaction)
        self.mempool.add_transaction(tx_id, bet_payload)
