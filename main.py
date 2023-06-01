import asyncio

from liquidation_acme import binance_liquidations, process_messages


async def main():
    """
    Executes the main program flow
    """
    tasks = [
        binance_liquidations(),
        process_messages()
    ]

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    print("starting")
    asyncio.run(main())
