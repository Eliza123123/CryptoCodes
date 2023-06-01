import asyncio

from liquidation_acme import binance_liquidations, process_messages, price_tracker, trade_book


async def price_tracking_task() -> None:
    """
    This function runs the price tracker every second.
    """
    while True:
        open_market_prices = await price_tracker(trade_book)
        print(open_market_prices)
        await asyncio.sleep(10)  # wait for 1 second


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
