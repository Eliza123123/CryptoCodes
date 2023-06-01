import asyncio
import pprint
from Lib import discord
from liquidation_acme import binance_liquidations,\
    process_messages, price_tracker, trade_performances, trade_book


async def price_tracking_task() -> None:
    """
    This function runs the price tracker every 10 seconds.
    """
    while True:
        prices_side = await price_tracker(trade_book)
        trade_performance = await trade_performances(trade_book, prices_side)
        print()
        pprint.pprint(trade_performance)
        print()
        discord.send_dictionary_to_channel(trade_performance)

        await asyncio.sleep(10)  # wait for 10 seconds


async def main():
    """
    Executes the main program flow
    """
    tasks = [
        binance_liquidations(),
        process_messages(),
        asyncio.create_task(price_tracking_task())

    ]

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    print("starting")
    asyncio.run(main())
