from asyncio import run

from ipv8_service import IPv8
from ipv8.util import run_forever


async def start():
    ipv8 = IPv8()

    await ipv8.start()

    await run_forever()


run(start())
