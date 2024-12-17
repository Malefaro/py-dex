from typing import AsyncIterator
from web3 import AsyncWeb3
from client import Client
from .abi import UNISWAP_V2_PAIR_ABI


class UniswapV2(Client):
    def __init__(self, w3: AsyncWeb3) -> None:
        super().__init__(w3)

    async def subscribe_pool(self, address) -> AsyncIterator:
        """returns async iterator with parsed events"""
        return await self.subscribe_contract(address, UNISWAP_V2_PAIR_ABI)
