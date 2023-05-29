from liquidation_acme import binance_liquidations, websocket_uri, process_messages
import asyncio


async def main():
    """
    Executes the main program flow
    """
    tasks = [
        process_messages(liquidation_size_filter=1),
        binance_liquidations(websocket_uri)
    ]

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    print("starting")
    asyncio.run(main())
