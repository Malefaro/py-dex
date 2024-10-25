import asyncio

from web3 import AsyncWeb3, WebSocketProvider

from uniswap.client import Uniswap


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


if __name__ == "__main__":
    import os

    asyncio.run(main())
