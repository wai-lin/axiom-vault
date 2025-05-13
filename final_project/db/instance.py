from pickledb import PickleDB
from dataclasses import asdict


from messages import BetPayload
from typing import List


class Database:
    def __init__(self):  # Added db_path, default value provided
        self.db = PickleDB('./db/mempool.json')

    def add_transaction(self, txid: str, value: BetPayload):

        if self.get_transaction(txid):
            print(f"Transaction with TXID {txid} already in mempool.")
            return False

        self.db.set(txid, asdict(value))
        print(f"Transaction {txid} added to mempool.")
        return True

    def get_transaction(self, txid: str) -> BetPayload | None:
        return self.db.get(txid)

    def remove_transaction(self, txid: str) -> bool:
        if txid in self.get_transaction(txid):
            self.db.remove(txid)
            print(f"Transaction {txid} removed from mempool.")
            return True
        print(f"Transaction {txid} not found in mempool.")
        return False

    def get_pending_transactions(self, sort_by_fee=True) -> List[BetPayload]:

        key_list = self.db.all()
        transactions_list = [self.db.get(id) for id in key_list]
        if sort_by_fee:
            transactions_list.sort(key=lambda tx: tx.timestamp, reverse=True)
        return transactions_list
