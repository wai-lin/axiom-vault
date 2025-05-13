from typing import Dict, List, Optional
from dataclasses import asdict
from mempool import Mempool


Python


class Mempool:
    _instance = None

    def __new__(cls, singleton=True):
        if singleton:
            if cls._instance is None:
                cls._instance = super(Mempool, cls).__new__(cls)
                cls._instance.mempool = {}
            return cls._instance
        else:
            instance = super(Mempool, cls).__new__(cls)
            instance.mempool = {}
            return instance

    def __init__(self, singleton=True):
        if not singleton or not hasattr(self, 'mempool'):
            self.mempool = {}

    # Assuming BetPayload is defined elsewhere
    def add_transaction(self, txid: str, value):
        if txid in self.mempool:
            print(f"Transaction with TXID {txid} already in mempool.")
            return False
        self.mempool[txid] = value
        print(f"Transaction {txid} added to mempool.")
        return True

    def get_transaction(self, txid: str):
        return self.mempool.get(txid)

    def remove_transaction(self, txid: str) -> bool:
        if txid in self.mempool:
            del self.mempool[txid]
            print(f"Transaction {txid} removed from mempool.")
            return True
        print(f"Transaction {txid} not found in mempool.")
        return False

    def get_all_transaction(self) -> List:
        return list(self.mempool.values())


class Database:
    _instance = None

    def __new__(cls, singleton=False):
        if singleton:
            if cls._instance is None:
                cls._instance = super(Database, cls).__new__(cls)
                cls._instance.blockchain_db = {}
            return cls._instance
        else:
            instance = super(Database, cls).__new__(cls)
            instance.blockchain_db = {}
            return instance

    def __init__(self, singleton=False):
        if not singleton or not hasattr(self, 'blockchain_db'):
            self.blockchain_db = {}
            self.mempool = Mempool(singleton=singleton)

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
