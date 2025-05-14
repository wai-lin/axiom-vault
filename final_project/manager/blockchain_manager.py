from final_project.utils import calculate_block_hash
from messages.blockchain import BlockChain
from messages.block import Block


from db.mempool import Mempool
from db.database import Database

import time


class BlockChainManager():

    def __init__(self, chain: BlockChain):
        self.chain = chain
        self.mempool = Mempool()
        self.db = Database()

    def create_genesis_block(self) -> None:
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            transactions=[],
            previous_hash="0",
            winning_number=None,
            commit_reveals=None,
            validator=None,
            hash=None,
        )
        calculate_block_hash(genesis_block)

        self.chain.chain.append(genesis_block)
        if self.db:
            self.db.save_block(genesis_block.to_dict())
