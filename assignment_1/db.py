import random


class Database:
    def __init__(self):
        self.id = random.randint(1, 1000)
        self.data = {}

    def __str__(self):
        return f"{self.id} :: {str(self.data)}"

    def put(self, key, value):
        if not key in self.data:
            self.data[key] = value

    def get(self, key):
        return self.data.get(key, None)

    def delete(self, key):
        if key in self.data:
            del self.data[key]
