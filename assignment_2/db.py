import json
import os


class Database:
    def __init__(self, filename='database.json'):
        self.filename = filename
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.filename) and os.path.getsize(self.filename) > 0:
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {self.filename}: {e}")
                print("Initializing database with empty data.")
                return {}
        else:
            print(
                f"Database file {self.filename} does not exist or is empty. Initializing with empty data.")
            return {}

    def save_data(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)

    def update(self, sender, receiver):
        if sender not in self.data:
            self.data[sender] = [receiver]
        elif receiver not in self.data[sender]:
            self.data[sender].append(receiver)
        self.save_data()

    def get_edges(self):
        """
        generate edge list
        "8092": [8090, 8091],
        """
        edges = []
        for sender, receivers in self.data.items():
            for receiver in receivers:
                edges.append((str(sender), str(receiver)))
        return edges