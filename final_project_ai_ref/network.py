from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8_service import IPv8
from ipv8.util import run_forever

from community import LotteryBlockchainCommunity


async def start_peer_network(num_of_peers: int) -> None:
    for i in range(num_of_peers):
        builder = ConfigBuilder().clear_keys().clear_overlays()
        builder.add_key("my peer", "medium", f"pem/ec_{i}.pem")
        # We provide the 'started' function to the 'on_start'.
        # We will call the overlay's 'started' function without any
        # arguments once IPv8 is initialized.
        builder.add_overlay("LotteryBlockchainCommunity", "my peer",
                            [WalkerDefinition(Strategy.RandomWalk,
                                              3, {'timeout': 3.0})],
                            default_bootstrap_defs, {"idx": i}, [('started',)])

        await IPv8(builder.finalize(),
                   extra_communities={'LotteryBlockchainCommunity': LotteryBlockchainCommunity}).start()

    await run_forever()
