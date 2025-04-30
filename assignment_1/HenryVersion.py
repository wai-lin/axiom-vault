from asyncio import run
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from ipv8.community import Community, CommunitySettings
from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8.lazy_community import lazy_wrapper
from ipv8.messaging.payload_dataclass import DataClassPayload
from ipv8.types import Peer
from ipv8.util import run_forever
from ipv8_service import IPv8

import random


# proof-of-work payload 
@dataclass
class TransactionMessage(DataClassPayload[2]):
    nonce: int
    signature: bytes
    public_key: bytes


class MyCommunity(Community):
    community_id = b'harbourspaceuniverse'

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.add_message_handler(TransactionMessage, self.on_transaction)
        # { nonce: TransactionMessage } in memory
        self.transaction_pool: dict[int, TransactionMessage] = {}

    def started(self) -> None:
        self.register_task('create_transaction', self.send_transaction, interval=5.0, delay=1.0)

    async def send_transaction(self):
        if not self.get_peers():
            print('waiting for peers...')
            return

        # generate ECDSA keypair
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()
        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # rand nonce
        nonce = random.randint(100_000, 999_999)
        msg = str(nonce).encode()
        # sign the nonce
        signature = private_key.sign(msg, ec.ECDSA(hashes.SHA256()))
        # create the transaction
        tx = TransactionMessage(nonce=nonce, signature=signature, public_key=pub_bytes)

        for peer in self.get_peers():
            self.ez_send(peer, tx)
            print(f'msg sent: {tx} to peer: {peer}')


    @lazy_wrapper(TransactionMessage)
    def on_transaction(self, peer: Peer, payload: TransactionMessage) -> None:
        print(f'Received transaction from {peer}')
        print(f'>Nonce: {payload.nonce}')
        try:
            nonce_bytes = int(payload.nonce).to_bytes(8, byteorder="big")
            pub_key = self.crypto.key_from_public_bin(payload.public_key)
            signature = payload.signature
            if self.crypto.is_valid_signature(pub_key, nonce_bytes, signature):
                print("valid transaction")
                if payload.nonce not in self.transaction_pool:
                    self.transaction_pool[payload.nonce] = payload
                    print(f"transaction added to pool (nonce={payload.nonce})")
                else:
                    print(f"duplicate transaction (nonce={payload.nonce}) ignored")
            else:
                print("invalid transaction signature")
        except Exception as e:
            print(f"error during verification: {e}")

async def start_community() -> None:
    builder = ConfigBuilder().clear_keys().clear_overlays()
    builder.add_key("my peer", "medium", "ec1.pem")
    builder.add_overlay(
        "MyCommunity", "my peer",
        [WalkerDefinition(Strategy.RandomWalk, 10, {'timeout': 3.0})],
        default_bootstrap_defs, {}, [('started',)]
    )
    await IPv8(builder.finalize(), extra_communities={'MyCommunity': MyCommunity}).start()
    await run_forever()


if __name__ == '__main__':
    run(start_community())
