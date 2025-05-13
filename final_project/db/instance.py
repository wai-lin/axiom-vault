from dataclasses import asdict
from typing import List

from messages.betpayload import BetPayload


class Mempool:
    def __init__(self):
        self.db = {}

    def add_transaction(self, txid: str, value: BetPayload):
        if txid in self.db:
            print(f"Transaction with TXID {txid} already in mempool.")
            return False
        self.db[txid] = asdict(value)
        print(f"Transaction {txid} added to mempool.")
        return True

    def get_transaction(self, txid: str) -> BetPayload | None:
        tx_data = self.db.get(txid)
        if tx_data:
            return BetPayload(**tx_data)
        return None

    def remove_transaction(self, txid: str) -> bool:
        if txid in self.db:
            del self.db[txid]
            print(f"Transaction {txid} removed from mempool.")
            return True
        print(f"Transaction {txid} not found in mempool.")
        return False

    def get_pending_transactions(self, sort_by_fee=True) -> List[BetPayload]:
        transactions_data = list(self.db.values())
        transactions_list = [BetPayload(**data) for data in transactions_data]
        if sort_by_fee:
            transactions_list.sort(key=lambda tx: tx.timestamp, reverse=True)
        return transactions_list
