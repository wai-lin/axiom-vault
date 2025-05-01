import random

from ipv8.messaging.payload_dataclass import dataclass
from ipv8.community import Community
from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8.peerdiscovery.network import PeerObserver
from ipv8.types import Peer
from ipv8_service import IPv8
from ipv8.lazy_community import lazy_wrapper

from assignment_1.db import Database


@dataclass(msg_id=1)
class TransactionMessage:
    public_key: str
    signature: str
    nonce: int


class MyCommunity(Community, PeerObserver):
    community_id = b'harbourspaceuniverse'

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.tx_db = Database()

    async def generate_transaction(self) -> None:
        print("Generating transaction...")

        nonce = random.randint(1, 1_000_000)
        signature = self.crypto.create_signature(
            self.my_peer.key, nonce.to_bytes(8))

        self.send_transaction(TransactionMessage(
            nonce=nonce,
            signature=signature.hex(),
            public_key=self.crypto.key_to_bin(self.my_peer.public_key).hex()
        ))

    def send_transaction(self, tx_message: TransactionMessage):
        print("Sending transaction. Nonce:", tx_message.nonce)
        for peer in self.get_peers():
            self.ez_send(peer, tx_message)

    def on_peer_added(self, peer: Peer) -> None:
        print("I am:", self.my_peer, "I found:", peer)

    def on_peer_removed(self, peer: Peer) -> None:
        pass

    @lazy_wrapper(TransactionMessage)
    def on_transaction_message(self, peer: Peer, payload: TransactionMessage):
        nonce = int(payload.nonce).to_bytes(8)
        pub_key = self.crypto.key_from_public_bin(
            bytes.fromhex(payload.public_key))
        signature = bytes.fromhex(payload.signature)

        if self.crypto.is_valid_signature(pub_key, nonce, signature):
            self.tx_db.put(nonce, payload)
            print("Got a new valid transaction")
        else:
            print("Got bad transaction")
        print("Current transactions in the database:", self.tx_db)

    def started(self) -> None:
        self.network.add_peer_observer(self)

        self.add_message_handler(
            TransactionMessage, self.on_transaction_message)

        self.register_task('generate_transaction',
                           self.generate_transaction, interval=5.0, delay=0)


async def run_community():
    builder = ConfigBuilder().clear_keys().clear_overlays()
    builder.add_key("my peer", "medium", f"ec_{i}.pem")
    # We provide the 'started' function to the 'on_start'.
    # We will call the overlay's 'started' function without any
    # arguments once IPv8 is initialized.
    builder.add_overlay("MyCommunity", "my peer",
                        [WalkerDefinition(Strategy.RandomWalk,
                                          10, {'timeout': 3.0})],
                        default_bootstrap_defs, {}, [('started',)])
    await IPv8(builder.finalize(),
               extra_communities={'MyCommunity': MyCommunity}).start()
