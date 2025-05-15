from messages.block import Block
from pow.miner import Miner

from db.mempool import Mempool
from db.database import Database


import time
import random
import math
import hashlib

from typing import Optional, Dict
from dataclasses import asdict


BLOCKS_PER_ROUND = 12
DEFAULT_DIFFICULTY = 1


class BlockChain():

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BlockChain, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self.chain = []
        self.mempool = Mempool()
        self.db = Database()
        self.miner = Miner()

    def _get_latest_block(self) -> Block:
        return self.chain[-1]

    def _get_length(self) -> int:
        return len(self.chain)

    def _validate_transaction(self, transaction: Dict) -> bool:
        required_fields = ["sender", "bet_number",
                           "amount", "timestamp", "signature"]
        if not all(field in transaction for field in required_fields):
            return False

        if not (1 <= transaction["bet_number"] <= 99):
            return False

        if not (1 <= transaction["amount"] <= 99):
            return False

        return True

    def _get_round_number(self) -> int:
        return int(math.ceil(len(self.chain) / BLOCKS_PER_ROUND))

    def _get_blocks_for_round(self) -> list[Block]:
        round = self._get_round_number()
        start_index = (round - 1) * BLOCKS_PER_ROUND
        end_index = start_index + BLOCKS_PER_ROUND
        return self.chain[start_index:end_index]

    def _add_block(self, block: Block):
        self.chain.append(block)
        if self.db:
            self.db.save_block(block._to_dict())
<<<<<<< HEAD
=======
        return True
>>>>>>> e5fed4b (Update: Block Syncing)

    def create_genesis_block(self) -> Block:
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            transactions=[],
            previous_hash="0",
            winning_number=random.randint(1, 100),
            hash='genesis_hash',
            nonce=None,
            difficulty=DEFAULT_DIFFICULTY,
        )

        self.miner.mine_block(genesis_block)

        self.chain.append(genesis_block)
        if self.db:
            self.db.save_block(genesis_block._to_dict())

        return genesis_block

    def create_block(
        self
    ) -> Optional[Block]:
        if not self.mempool:

            transactions = []
        else:
            transactions = self.mempool.get_all_transactions()
            self.mempool.clear_mempool()

        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            transactions=transactions,
            previous_hash=self._get_latest_block().hash,
            winning_number=random.randint(1, 100),
            hash=None,
            nonce=None,
<<<<<<< HEAD
            difficulty=1.0,
        )._calculate_block_hash()
=======
            difficulty=self._get_latest_block().difficulty,
        )

        self.miner.mine_block(new_block)
>>>>>>> e5fed4b (Update: Block Syncing)

        self.chain.append(new_block)
        if self.db:
            self.db.save_block(new_block._to_dict())

        return new_block

    def validate_block(self, block: Block) -> bool:
        calculated_hash = hashlib.sha256(
            block._calculate_hash_string(block.nonce).encode()
        ).hexdigest()

        if calculated_hash != block.hash:
            print(
                f"Block hash invalid. Calculated: {calculated_hash}, Received: {block.hash}"
            )
            return False

        return True

    def get_winning_result(self):

        round_blocks = self._get_blocks_for_round()
        winning_block = random.choice(round_blocks)

        winning_number = winning_block.winning_number

        winner_list = {}

        total_amount = 0

        # print("Winning Number: ", winning_number)
        # print("Length of Block: ", len(self.chain))
        # print("Round Block: ", len(round_blocks))
        for block in round_blocks:
            # print("Transaction Length: ", len(block.transactions))
            for bet in block.transactions:
                if winning_number == bet.bet_number:
                    winner_list[bet.bettor_id] = winner_list.get(
                        bet.bettor_id, 0) + bet.bet_amount
                    total_amount = total_amount + bet.bet_amount

        print("Winner List:", winner_list)

        return winning_number, total_amount, winner_list
