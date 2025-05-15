import json
import os


class PeerDiscoveryTracker:
    def __init__(self, id):
        self.path = f"data/{id}/peer_discovery.json"
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.data = {}
        self._save()

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)

    def update(self, sender: str, receiver: str):
        self.data.setdefault(sender, [])
        if receiver not in self.data[sender]:
            self.data[sender].append(receiver)
            self._save()

    def get_edges(self):
        return [(s, r) for s, rs in self.data.items() for r in rs]
