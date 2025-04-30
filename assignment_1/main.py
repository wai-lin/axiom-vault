from asyncio import run
from dataclasses import dataclass

from ipv8.community import Community, CommunitySettings
from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8.lazy_community import lazy_wrapper
from ipv8.messaging.payload_dataclass import DataClassPayload
from ipv8.types import Peer
from ipv8.util import run_forever
from ipv8_service import IPv8

from ipv8.keyvault.crypto import ECCrypto


@dataclass
class MyMessage(DataClassPayload[1]):
    pub_key: str
    signature: str
    nonce: int


class MyCommunity(Community):

    community_id = b'harbourchainuniverse'

    def __init__(self, settings: CommunitySettings) -> None:

        super().__init__(settings)
        self.add_message_handler(MyMessage, self.on_message)
        self.lamport_clock = 0

        self.key_gen = ECCrypto()
        self.key_storage = set()

        self.my_priv_key = self.key_gen.generate_key(security_level='very-low')
        self.my_pub_key_bin = self.key_gen.key_to_bin(self.my_priv_key.pub())
        self.my_signature = self.key_gen.create_signature(
            ec=self.my_priv_key, data=self.my_pub_key_bin)

    def started(self) -> None:
        async def start_communication() -> None:
            if not self.lamport_clock:
                for p in self.get_peers():
                    if p.public_key not in self.key_storage:
                        self.ez_send(p, MyMessage(
                            pub_key=self.my_pub_key_bin.hex(), signature=self.my_signature.hex(), nonce=self.lamport_clock))
                        self.key_storage.add(p.public_key)
                self.cancel_pending_task("start_communication")
            else:
                self.cancel_pending_task("start_communication")

        self.register_task("start_communication",
                           start_communication, interval=5.0, delay=1)

    @lazy_wrapper(MyMessage)
    def on_message(self, peer: Peer, payload: MyMessage) -> None:
        self.lamport_clock = max(self.lamport_clock, payload.nonce) + 1
        print(f"{self.my_peer} received from {peer}: pub_key={payload.pub_key}, signature={payload.signature}, current clock={self.lamport_clock}")

        pass


async def start_communities(num_instances: int = 3) -> None:
    """Starts multiple instances of the MyCommunity."""
    for i in range(num_instances):
        builder = ConfigBuilder().clear_keys().clear_overlays()
        builder.add_key(f"peer_{i}", "medium", f"ec{i}.pem")
        builder.add_overlay("MyCommunity", f"peer_{i}",
                            [WalkerDefinition(Strategy.RandomWalk, 10, {
                                              'timeout': 3.0})],
                            default_bootstrap_defs, {}, [('started',)])
        await IPv8(builder.finalize(),
                   extra_communities={'MyCommunity': MyCommunity}).start()
    await run_forever()


if __name__ == "__main__":
    num_instances_to_run = 3
    run(start_communities(num_instances_to_run))
