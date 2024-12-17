import asyncio
import logging

import traceback
from hexbytes import HexBytes
import websockets
from dataclasses import dataclass
from typing import AsyncIterator
from eth_typing import HexStr

from web3 import AsyncWeb3
from web3.contract import AsyncContract
from aiochannel import Channel


logger = logging.getLogger("DexClient")

logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(name)s %(message)s",
    level=logging.INFO,
)


class Client:
    @dataclass
    class Subscription:
        channel: Channel
        address: HexStr

    def __init__(self, w3: AsyncWeb3) -> None:
        self.w3 = w3
        self._subscriptions: dict[HexStr, Client.Subscription] = dict()

    async def _process_logs(self):
        while True:
            try:
                async for payload in self.w3.socket.process_subscriptions():
                    subscription_id = payload["subscription"]
                    channel = self._subscriptions.get(subscription_id).channel
                    if channel is None:
                        continue
                    await channel.put(payload["result"])
            except websockets.ConnectionClosed:
                logger.warn("connection closed reconnecting")
            except Exception:
                logger.error(
                    "something went wrong reconnecting:%s", traceback.format_exc()
                )
            finally:
                # reconnecting:
                await self.w3.provider.disconnect()
                await self.w3.provider.connect()
                # resubscribe
                old_subs = self._subscriptions.copy()
                self._subscriptions.clear()
                while len(old_subs) > 0:
                    (_, sub) = old_subs.popitem()
                    subscription_id = await self._subscribe_eth(sub.address)
                    self._subscriptions[subscription_id] = sub

    async def start(self):
        if not await self.w3.provider.is_connected():
            await self.w3.provider.connect()
        self._process_logs_task = asyncio.create_task(self._process_logs())

    async def stop(self):
        self._process_logs_task.cancel()
        await self.w3.provider.disconnect()

    async def subscribe_contract(
        self,
        address,
        abi,
    ) -> AsyncIterator:
        """returns async iterator with already parsed events"""
        contract: AsyncContract = self.w3.eth.contract(address=address, abi=abi)
        subscription_id = await self._subscribe_eth(address)
        channel = Channel()
        sub = Client.Subscription(channel, address)
        self._subscriptions[subscription_id] = sub
        return _parser(channel, contract)

    async def _subscribe_eth(self, address) -> HexStr:
        """subscribe and return subscription_id"""
        filter_params = {
            "address": address,
        }
        subscription_id = await self.w3.eth.subscribe("logs", filter_params)
        return subscription_id


async def _parser(
    channel: Channel,
    contract: AsyncContract,
) -> AsyncIterator:
    async for log in channel:
        event_signature: HexBytes = log["topics"][0]
        event = contract.get_event_by_topic(event_signature.to_0x_hex())
        parsed = event.process_log(log)
        yield parsed
