import json
import os


class Database:
    def __init__(self, filename='database.json'):
        self.filename = filename
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                return json.load(f)
        return {}

    def save_data(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)

    def update(self, sender, receiver):

        # Convert UDPv4Address objects to strings in the format "ip:port"
        sender_str = f"{sender[1]}" if hasattr(
            sender, "__getitem__") else str(sender)
        receiver_str = f"{receiver[1]}" if hasattr(
            receiver, "__getitem__") else str(receiver)

        if sender_str not in self.data:
            self.data[sender_str] = [receiver_str]
        else:
            if receiver_str not in self.data[sender_str]:
                self.data[sender_str].append(receiver_str)
        self.save_data()

    def get(self, sender):
        # Convert UDPv4Address object to string
        sender_str = f"{sender[0]}:{sender[1]}" if hasattr(
            sender, "__getitem__") else str(sender)
        return self.data.get(sender_str, [])
