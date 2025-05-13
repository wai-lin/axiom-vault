from typing import Dict, List, Any, Optional
import json
from ipv8.messaging.payload import Payload
from ipv8.messaging.serialization import Serializer

# Message types
MSG_TRANSACTION = 1
MSG_BLOCK = 2
MSG_CHAIN_REQUEST = 3
MSG_CHAIN_RESPONSE = 4
MSG_MEMPOOL_REQUEST = 5
MSG_MEMPOOL_RESPONSE = 6
MSG_COMMIT = 7
MSG_REVEAL = 8


# gotta change these to dataclass

class TransactionPayload(Payload):
    """Payload for transaction messages"""

    format_list = ["varlenH"]

    def __init__(self, transaction: Dict):
        self.transaction = transaction

    def to_pack_list(self) -> List:
        return [("varlenH", json.dumps(self.transaction).encode())]

    @classmethod
    def from_unpack_list(cls, transaction_json: bytes) -> "TransactionPayload":
        return TransactionPayload(json.loads(transaction_json.decode()))


class BlockPayload(Payload):
    """Payload for block messages"""

    format_list = ["varlenH"]

    def __init__(self, block: Dict):
        self.block = block

    def to_pack_list(self) -> List:
        return [("varlenH", json.dumps(self.block).encode())]

    @classmethod
    def from_unpack_list(cls, block_json: bytes) -> "BlockPayload":
        return BlockPayload(json.loads(block_json.decode()))


class ChainRequestPayload(Payload):
    """Payload for blockchain request messages"""

    format_list = ["I"]

    def __init__(self, latest_block_index: int):
        self.latest_block_index = latest_block_index

    def to_pack_list(self) -> List:
        return [("I", self.latest_block_index)]

    @classmethod
    def from_unpack_list(cls, latest_block_index: int) -> "ChainRequestPayload":
        return ChainRequestPayload(latest_block_index)


class ChainResponsePayload(Payload):
    """Payload for blockchain response messages"""

    format_list = ["varlenH"]

    def __init__(self, blocks: List[Dict]):
        self.blocks = blocks

    def to_pack_list(self) -> List:
        return [("varlenH", json.dumps(self.blocks).encode())]

    @classmethod
    def from_unpack_list(cls, blocks_json: bytes) -> "ChainResponsePayload":
        return ChainResponsePayload(json.loads(blocks_json.decode()))


class MempoolRequestPayload(Payload):
    """Payload for mempool request messages with bloom filter"""

    format_list = ["varlenH"]

    def __init__(self, bloom_filter: bytes):
        self.bloom_filter = bloom_filter

    def to_pack_list(self) -> List:
        return [("varlenH", self.bloom_filter)]

    @classmethod
    def from_unpack_list(cls, bloom_filter: bytes) -> "MempoolRequestPayload":
        return MempoolRequestPayload(bloom_filter)


class MempoolResponsePayload(Payload):
    """Payload for mempool response messages"""

    format_list = ["varlenH"]

    def __init__(self, transactions: List[Dict]):
        self.transactions = transactions

    def to_pack_list(self) -> List:
        return [("varlenH", json.dumps(self.transactions).encode())]

    @classmethod
    def from_unpack_list(cls, transactions_json: bytes) -> "MempoolResponsePayload":
        return MempoolResponsePayload(json.loads(transactions_json.decode()))


class CommitPayload(Payload):
    """Payload for commit phase of commit-reveal scheme"""

    format_list = ["varlenH", "varlenH"]

    def __init__(self, peer_id: str, commit_hash: str):
        self.peer_id = peer_id
        self.commit_hash = commit_hash

    def to_pack_list(self) -> List:
        return [
            ("varlenH", self.peer_id.encode()),
            ("varlenH", self.commit_hash.encode()),
        ]

    @classmethod
    def from_unpack_list(cls, peer_id: bytes, commit_hash: bytes) -> "CommitPayload":
        return CommitPayload(peer_id.decode(), commit_hash.decode())


class RevealPayload(Payload):
    """Payload for reveal phase of commit-reveal scheme"""

    format_list = ["varlenH", "varlenH", "varlenH"]

    def __init__(self, peer_id: str, random_value: str, nonce: str):
        self.peer_id = peer_id
        self.random_value = random_value
        self.nonce = nonce

    def to_pack_list(self) -> List:
        return [
            ("varlenH", self.peer_id.encode()),
            ("varlenH", self.random_value.encode()),
            ("varlenH", self.nonce.encode()),
        ]

    @classmethod
    def from_unpack_list(
        cls, peer_id: bytes, random_value: bytes, nonce: bytes
    ) -> "RevealPayload":
        return RevealPayload(peer_id.decode(), random_value.decode(), nonce.decode())
