import random
import time

from ipv8.messaging.payload_dataclass import dataclass
from ipv8.community import Community
from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8.peerdiscovery.network import PeerObserver
from ipv8.types import Peer
from ipv8_service import IPv8
from ipv8.lazy_community import lazy_wrapper

from db.instance import Database
from messages import BetPayload


class MyCommunity(Community, PeerObserver):
    community_id = b'harbourspaceuniverse'

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.tx_db = Database()

    async def generate_transaction(self) -> None:
        print("Generating transaction...")

        bettor_id = self.crypto.key_to_bin(self.my_peer.public_key).hex()
        bet_number = random.randint(1, 100)
        bet_amount = random.randint(1, 100)
        timestamp = time.time()
        signature = self.crypto.create_signature(
            self.my_peer.key, str(timestamp).encode())

        payload = BetPayload(
            bettor_id=bettor_id,
            bet_number=bet_number,
            bet_amount=bet_amount,
            timestamp=timestamp,
            signature=signature.hex(),
        )

        self.send_transaction(payload)

    def send_transaction(self, tx_message: BetPayload):
        print("Sending transaction. TxID:", tx_message._generate_txid())
        for peer in self.get_peers():
            self.ez_send(peer, tx_message)

    def on_peer_added(self, peer: Peer) -> None:
        print("I am:", self.my_peer, "I found:", peer)

    def on_peer_removed(self, peer: Peer) -> None:
        pass

    @lazy_wrapper(BetPayload)
    def on_transaction_message(self, peer: Peer, payload: BetPayload):
        bettor_id = self.crypto.key_from_public_bin(
            bytes.fromhex(payload.bettor_id))

        timestamp = str(payload.timestamp).encode()

        signature = bytes.fromhex(payload.signature)

        if self.crypto.is_valid_signature(bettor_id, timestamp, signature):
            self.tx_db.add_transaction(payload._generate_txid(), payload)
            print("Got a new valid transaction")
        else:
            print("Got bad transaction")

    def started(self) -> None:
        self.network.add_peer_observer(self)

        self.add_message_handler(
            BetPayload, self.on_transaction_message)

        self.register_task('generate_transaction',
                           self.generate_transaction, interval=2.0, delay=0)
