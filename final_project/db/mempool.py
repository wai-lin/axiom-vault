from dataclasses import asdict
from typing import List, Optional

from messages.betpayload import BetPayload


# Make Sure That The Mempool is Singleton
# Please Switch this back to Multiton Pattern when running Multi Node in Single Computer

class Mempool:
    _instance = None

    def __new__(cls, singleton=False):
        if singleton:
            if cls._instance is None:
                cls._instance = super(Mempool, cls).__new__(cls)
                cls._instance.mempool = {}
            return cls._instance
        else:
            instance = super(Mempool, cls).__new__(cls)
            instance.mempool = {}
            return instance

    def __init__(self, singleton=False):
        # This init will only be called for the first instance in singleton mode
        # or for every instance in multi mode.
        if not singleton or not hasattr(self, 'mempool'):
            self.mempool = {}

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
