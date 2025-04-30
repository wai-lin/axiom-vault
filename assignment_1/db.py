
class Database:
    def __init__(self):
        self.data = {}

    def put(self, key, value):
        if not key in self.data:
            self.data[key] = value

    def get(self, key):
        return self.data.get(key, None)

    def delete(self, key):
        if key in self.data:
            del self.data[key]
