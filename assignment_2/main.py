from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8.util import run_forever
from ipv8_service import IPv8

from asyncio import run

from community import BlockchainCommunity


async def start_communities(num_communities: int) -> None:
    for i in range(num_communities):
        builder = ConfigBuilder().clear_keys().clear_overlays()
        builder.add_key("my peer", "medium", f"ec_{i}.pem")
        # We provide the 'started' function to the 'on_start'.
        # We will call the overlay's 'started' function without any
        # arguments once IPv8 is initialized.
        builder.add_overlay("BlockchainCommunity", "my peer",
                            [WalkerDefinition(Strategy.RandomWalk,
                                              3, {'timeout': 3.0})],
                            default_bootstrap_defs, {"idx": i}, [('started',)])
        await IPv8(builder.finalize(),
                   extra_communities={'BlockchainCommunity': BlockchainCommunity}).start()

    await run_forever()

run(start_communities(8))