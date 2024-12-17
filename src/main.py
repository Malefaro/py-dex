import asyncio

from web3 import AsyncWeb3, WebSocketProvider
from client.client import Client

from uniswap.client import Uniswap
from uniswap_v2.abi import UNISWAP_V2_PAIR_ABI
from uniswap_v2.uniswap_v2 import UniswapV2


async def main():
    # infura url in format:
    # wss://mainnet.infura.io/ws/v3/<api_token>
    infura_url = os.getenv("INFURA_WS_URL")
    # WETH_USDT pool with 0.05% fee
    pool_addr = "0x11b815efB8f581194ae79006d24E0d814B7697F6"

    w3: AsyncWeb3 = AsyncWeb3(WebSocketProvider(infura_url))
    uniswap_client = Uniswap(w3)
    await uniswap_client.start()  # connects websocket and run background tasks

    try:
        # specify events that you will parse
        # events_to_subscribe can be omitted in which case all events related to address will be sent
        events_to_subscribe = [uniswap_client.swap_event_signature()]

        chan = await uniswap_client.subscribe(pool_addr, events_to_subscribe)
        pool_contract = uniswap_client.pool_contract(pool_addr)
        print("waiting for logs...")
        async for log in chan:
            # contains event name signature
            event_name_sig = log["topics"][0]
            # find this signature in subscribed event to determine how to parse it
            idx = events_to_subscribe.index(event_name_sig)
            match idx:
                # first element of `events_to_subscribe` list which is `Swap` event
                case 0:
                    # parsing event log
                    # to parse other type of events change `Swap` to other event name
                    # pool_contract.events.<event_name>().process_log(result)
                    parsed = pool_contract.events.Swap().process_log(log)
                    print("parsed:", parsed)
                    # call some contract function
                    # in this case we call `slot0()` function which contains pool info
                    # https://docs.uniswap.org/contracts/v3/reference/core/interfaces/pool/IUniswapV3PoolState#slot0
                    slot0 = await pool_contract.functions.slot0().call()
                    print("slot0:", slot0)

                case _:
                    print("unknown event")

    finally:
        await uniswap_client.stop()


async def main_uniswap():
    infura_url = os.getenv("INFURA_WS_URL")
    # ETH_USDT pool
    pool_addr = "0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852"

    w3: AsyncWeb3 = AsyncWeb3(WebSocketProvider(infura_url))
    client = UniswapV2(w3)
    try:
        await client.start()
        # returns async iterator with parsed events
        chan = await client.subscribe_pool(pool_addr)
        async for msg in chan:
            # already parsed event like
            # AttributeDict({'args': AttributeDict({'sender': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D', 'to': '0xCfe7579A82c94b016be218b8C54b3F8fB6658692', 'amount0In': 1000000000000000, 'amount1In': 0, 'amount0Out': 0, 'amount1Out': 3959242}), 'event': 'Swap', 'logIndex': 309, 'transactionIndex': 150, 'transactionHash': HexBytes('0x3f1ae2bd95c2c836a176a97c6da8fc53118eaa3b22080721bebe92570a1c476d'), 'address': '0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852', 'blockHash': HexBytes('0xfca32c164a043303322ae19d049b0061be2b43040b2acbdf14e0a64b0236d61d'), 'blockNumber': 21423928})
            print(msg)
    finally:
        await client.stop()


async def main_generic():
    infura_url = os.getenv("INFURA_WS_URL")
    # ETH_USDT pool
    pool_addr = "0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852"

    w3: AsyncWeb3 = AsyncWeb3(WebSocketProvider(infura_url))
    client = Client(w3)
    try:
        await client.start()
        # just specify addr and contract abi and subscribe to all events of cotract
        chan = await client.subscribe_contract(pool_addr, UNISWAP_V2_PAIR_ABI)
        async for msg in chan:
            print(msg)
    finally:
        await client.stop()


if __name__ == "__main__":
    import os

    asyncio.run(main_generic())
