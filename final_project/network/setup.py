from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8_service import IPv8
from ipv8.util import run_forever


# make sure this module exists in your project
from community.setup import MyCommunity

import random


async def start_network(key: int):

    builder = ConfigBuilder().clear_keys().clear_overlays()
    builder.add_key("my peer", "medium", f"ec_{key}.pem")

    builder.add_overlay(
        "MyCommunity",
        "my peer",
        [
            WalkerDefinition(Strategy.RandomWalk, 10, {"timeout": 3.0})
        ],  # 10 optimal to converge
        default_bootstrap_defs,
        {"node_id": f"node_{key}"},
        [("started",)],
    )

    await IPv8(builder.finalize(),
               extra_communities={'MyCommunity': MyCommunity}).start()

    await run_forever()
