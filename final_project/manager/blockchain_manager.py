from messages.blockchain import BlockChain
from messages.block import Block


from db.mempool import Mempool
from db.database import Database

import time
import random


from typing import Optional, Dict


class BlockChainManager:

    def __init__(self, chain: BlockChain):
        self.block_chain = chain
        self.mempool = Mempool()
        self.db = Database()

        # Implement PoW
        # self.miner = Miner()

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

        self.block_chain.chain.append(genesis_block)
        if self.db:
            self.db.save_block(genesis_block._to_dict())

    def create_block(self) -> Optional[Block]:
        print(f"block creation every 10 sec from mempool {id(self.mempool)}")
        print(
            f"current mempool size: {len(self.mempool.get_all_transactions())} and id: {id(self.mempool)}"
        )
        if not self.mempool:

            transactions = []
        else:
            transactions = self.mempool.get_all_transactions()
            self.mempool.clear_mempool()

        new_block = Block(
            index=len(self.block_chain.chain),
            timestamp=time.time(),
            transactions=transactions,
            previous_hash=self.block_chain._get_latest_block().hash,
            winning_number=random.randint(1, 100),
            hash=None,
        )._calculate_block_hash()

        self.block_chain.chain.append(new_block)
        print(f"chain height: {len(self.block_chain.chain)}")
        if self.db:
            self.db.save_block(new_block._to_dict())

        return new_block

    def validate_chain(self):
        for i in range(1, self.block_chain._get_latest_block):
            current = self.block_chain.chain[i]
            previous = self.block_chain.chain[i - 1]

            # Check hash integrity
            if current.previous_hash != previous.hash:
                return False

            # Check block hash
            if current.hash != current.calculate_hash():
                return False

        return True

    def get_winning_number(self):
        round_blocks = self.block_chain._get_blocks_for_round()

        winning_block = random.choice(round_blocks)

        winning_number = winning_block.winning_number

        return winning_number
