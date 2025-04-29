import os
from asyncio import run
from dataclasses import dataclass

from ipv8.community import Community, CommunitySettings
from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8.lazy_community import lazy_wrapper
from ipv8.messaging.payload_dataclass import DataClassPayload
from ipv8.types import Peer
from ipv8.util import run_forever
from ipv8_service import IPv8


@dataclass
class MyMessage(DataClassPayload[1]):
    pub_keys: str
    signature: str
    nonce: int


class MyCommunity(Community):
    community_id = b'harbourchainuniverse'

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.add_message_handler(MyMessage, self.on_message)
        self.lamport_clock = 0
        # Unique identifier
        self.pub_keys = f"Node-{self.my_peer.public_key.key_to_bin().hex()[:8]}"
        self.signature = "InitialSignature"

    def started(self) -> None:
        async def start_communication() -> None:
            if not self.lamport_clock:
                for p in self.get_peers():
                    self.ez_send(p, MyMessage(
                        pub_keys=self.pub_keys, signature=self.signature, nonce=self.lamport_clock))
            else:
                self.cancel_pending_task("start_communication")

        self.register_task("start_communication",
                           start_communication, interval=5.0, delay=0)

    @lazy_wrapper(MyMessage)
    def on_message(self, peer: Peer, payload: MyMessage) -> None:
        self.lamport_clock = max(self.lamport_clock, payload.nonce) + 1
        print(f"{self.my_peer} received from {peer}: pub_keys={payload.pub_keys}, signature={payload.signature}, current clock={self.lamport_clock}")

        self.ez_send(peer, MyMessage(
            pub_keys=self.pub_keys, signature=self.signature, nonce=self.lamport_clock))


async def start_communities(num_instances: int = 2) -> None:
    """Starts multiple instances of the MyCommunity."""
    for i in range(num_instances):
        builder = ConfigBuilder().clear_keys().clear_overlays()
        builder.add_key(f"peer_{i}", "medium", f"ec{i}.pem")
        builder.add_overlay("MyCommunity", f"peer_{i}",
                            [WalkerDefinition(Strategy.RandomWalk,
                                              10, {'timeout': 3.0})],
                            default_bootstrap_defs, {}, [('started',)])
        await IPv8(builder.finalize(),
                   extra_communities={'MyCommunity': MyCommunity}).start()
    await run_forever()


if __name__ == "__main__":
    num_instances_to_run = 2
    run(start_communities(num_instances_to_run))
