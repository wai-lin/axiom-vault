from dataclasses import asdict
from typing import Dict, List, Optional

from messages.betpayload import BetPayload


class Mempool:
    _instance: Optional["Mempool"] = None

    def __new__(cls) -> "Mempool":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._mempool = {}
        return cls._instance

    @classmethod
    def get_instance(cls) -> "Mempool":
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def add_transaction(self, txid: str, payload: BetPayload) -> bool:
        if txid in self._mempool:
            print(f"Transaction with TXID {txid} already in mempool.")
            return False
        self._mempool[txid] = asdict(payload)
        print(f"Transaction {txid} added to mempool.")
        return True

    def get_transaction(self, txid: str) -> Optional[BetPayload]:
        tx_data = self._mempool.get(txid)
        if tx_data:
            return BetPayload(**tx_data)
        return None

    def remove_transaction(self, txid: str) -> bool:
        if txid in self._mempool:
            del self._mempool[txid]
            print(f"Transaction {txid} removed from mempool.")
            return True
        print(f"Transaction {txid} not found in mempool.")
        return False

    def get_all_transactions(self) -> List[BetPayload]:
        return [BetPayload(**data) for data in self._mempool.values()]

    def get_latest_transactions(self, last_seen_timestamp: float) -> list[BetPayload]:
        latest_txs = []
        for tx in self.get_all_transactions():
            if tx.timestamp > last_seen_timestamp:
                latest_txs.append(tx)
        return latest_txs

    def clear_mempool(self):
        self._mempool.clear()
