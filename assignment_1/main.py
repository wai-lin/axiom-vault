from asyncio import run
from ipv8.util import run_forever

from community import run_community


async def start_communities() -> None:
    for i in [1]:
        await run_community(i)
    await run_forever()


run(start_communities())
