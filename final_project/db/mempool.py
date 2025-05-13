from dataclasses import asdict
from typing import List, Optional

from messages.betpayload import BetPayload


class Mempool:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Mempool, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not Mempool._initialized:
            self.mempool = {}
            Mempool._initialized = True

    def add_transaction(self, txid: str, value: BetPayload):
        if txid in self.mempool:
            print(f"Transaction with TXID {txid} already in mempool.")
            return False
        self.mempool[txid] = asdict(value)
        print(f"Transaction {txid} added to mempool.")
        return True

    def get_transaction(self, txid: str) -> Optional[BetPayload]:
        tx_data = self.mempool.get(txid)
        if tx_data:
            return BetPayload(**tx_data)
        return None

    def remove_transaction(self, txid: str) -> bool:
        if txid in self.mempool:
            del self.mempool[txid]
            print(f"Transaction {txid} removed from mempool.")
            return True
        print(f"Transaction {txid} not found in mempool.")
        return False

    def get_all_transaction(self) -> List[BetPayload]:
        transactions_data = list(self.mempool.values())
        transactions_list = [BetPayload(**data) for data in transactions_data]
        return transactions_list
