import asyncio
import pprint
from Lib import discord
from liquidation_acme import binance_liquidations,\
    process_messages, price_tracker, market_exits, trade_book, total_profit


async def price_tracking_task() -> None:
    """
    This function runs the price tracker every 10 seconds.
    """
    while True:
        prices_side = await price_tracker(trade_book)
        trade_performance = await market_exits(trade_book, prices_side)
        # print()
        # pprint.pprint(trade_performance)
        # print()
        discord.send_dictionary_to_channel(trade_performance, total_profit)

        await asyncio.sleep(3)  # wait for 3 seconds


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
