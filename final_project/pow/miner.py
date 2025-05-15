from messages.block import Block
import time
import hashlib

TARGET_BLOCK_TIME = 20  # seconds


class Miner:

    def mine_block(self, block):
        print("Mining Block")

        nonce, difficulty = self._calculate_nonce(block)

        # Mutate block
        block.nonce = nonce
        block.difficulty = difficulty  # Assign the updated difficulty

        hash_string = block._calculate_hash_string(nonce)
        block_hash = hashlib.sha256(hash_string.encode()).hexdigest()

        block.hash = block_hash
        print("Block Has Been Mined")
        return block

    def _calculate_nonce(self, block):
        nonce = 0
        start_time = time.time()

        while True:
            block_data = block._calculate_hash_string(nonce)
            block_hash = hashlib.sha256(block_data.encode()).hexdigest()
            print("Trying Nonce :", nonce)
            print("Hash :", block_hash)
            if block_hash.startswith('0' * block.difficulty):

                elapsed = time.time() - start_time
                difficulty = self._adjust_difficulty(elapsed, block.difficulty)
                return nonce, difficulty
            nonce += 1

    def _adjust_difficulty(self, elapsed_time, difficulty):

        # Soft Capping For Now ( Cuz I don't want to deal with Float Shit, or Large Integer)
        return 1

        if elapsed_time < TARGET_BLOCK_TIME:
            return difficulty + 1
        elif elapsed_time > TARGET_BLOCK_TIME * 2 and difficulty > 1:
            return difficulty - 1
        return difficulty
