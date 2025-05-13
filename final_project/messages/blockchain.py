from ipv8.messaging.payload_dataclass import dataclass


from messages.block import Block
from db.mempool import Mempool
from db.database import Database

import hashlib
import json


@dataclass(msg_id=4)
class BlockChain:
    chain: list[Block]
    mempool: Mempool
    db: Database
