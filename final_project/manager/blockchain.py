from messages.block import Block


from db.mempool import Mempool
from db.database import Database

import time
import random


from typing import Optional, Dict

BLOCKS_PER_ROUND = 12


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
        self.round = 1
        self.mempool = Mempool()
        self.db = Database()

        # Implement PoW
        # self.miner = Miner()

    def _get_latest_block(self) -> Block:
        return self.chain[-1]

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

    def _get_blocks_for_round(self) -> list[Block]:
        start_index = (self.round - 1) * BLOCKS_PER_ROUND
        end_index = start_index + BLOCKS_PER_ROUND
        return self.chain[start_index:end_index]

    def create_genesis_block(self) -> None:
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            transactions=[],
            previous_hash="0",
            winning_number=random.randint(1, 100),
            hash=None,
        )

        genesis_block._calculate_block_hash()

        self.chain.append(genesis_block)
        if self.db:
            self.db.save_block(genesis_block._to_dict())

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
        )._calculate_block_hash()

        self.chain.append(new_block)
        if self.db:
            self.db.save_block(new_block._to_dict())

        return new_block

    def validate_chain(self):
        for i in range(1, self._get_latest_block):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Check hash integrity
            if current.previous_hash != previous.hash:
                return False

            # Check block hash
            if current.hash != current.calculate_hash():
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
