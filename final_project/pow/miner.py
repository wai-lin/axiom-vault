import hashlib
import time


class Miner:
    TARGET_BLOCK_TIME = 20  # Seconds
    INITIAL_DIFFICULTY = 4

    def __init__(self):
        self.difficulty = self.INITIAL_DIFFICULTY

    def proof_of_work(self, block):
        nonce = 0
        start_time = time.time()
        block_data = self._block_string(block, nonce)

        while True:
            block_hash = hashlib.sha256(block_data.encode()).hexdigest()
            if block_hash.startswith('0' * self.difficulty):
                elapsed = time.time() - start_time
                return block_hash, nonce, elapsed
            nonce += 1
            block_data = self._block_string(block, nonce)

    def adjust_difficulty(self, elapsed_time):
        if elapsed_time < self.TARGET_BLOCK_TIME:
            self.difficulty += 1
        elif elapsed_time > self.TARGET_BLOCK_TIME:
            self.difficulty = max(1, self.difficulty - 1)

    def _block_string(self, block, nonce):
        data = f"{block.index}{block.timestamp}{block.transactions}{block.previous_hash}{block.winning_number}{nonce}"
        return data
