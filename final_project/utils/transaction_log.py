import json
import os
from collections import defaultdict
from typing import Dict, List


class TxCoverageTracker:
    """
    Round-scoped transaction logger for each node
    `record(round_id, tx_id, tx_ts)` for every seen transaction
    `flush(round_id)` when a round ends
    `dump(node_id)` to write to disk
    """

    def __init__(self, node_name: str) -> None:
        self.node_name = node_name
        # round_id → { tx_hash → ts }
        self._seen: Dict[int, Dict[str, float]] = defaultdict(dict)
        self._history: List[dict] = []

    def record(self, round_id: int, tx_id: str, tx_ts: float) -> None:
        self._seen[round_id][tx_id] = tx_ts

    def flush(self, round_id: int) -> None:
        tx_map = self._seen.pop(round_id, {})
        ordered = sorted(tx_map.items(), key=lambda kv: kv[1])
        transactions = {
            tx_hash: {"order": i + 1, "timestamp": ts}
            for i, (tx_hash, ts) in enumerate(ordered)
        }
        entry = {
            "round": round_id,
            "transaction_count": len(transactions),
            "node_name": self.node_name,
            "transactions": transactions,
        }
        self._history.append(entry)

    def dump(self) -> str:
        dir_path = os.path.join("data", self.node_name)
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, "transactions_log.json")
        with open(file_path, "w") as fh:
            json.dump(self._history, fh, indent=2)
        return os.path.abspath(file_path)
