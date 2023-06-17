import asyncio

from lib.discord import delayed_send_trade_book
from liquidation_acme import ws, books, strategy_entries, strategy_exits


async def main():
    await asyncio.gather(ws.stream(),
                         ws.on_liquidation(strategy_entries),
                         ws.on_kline(strategy_exits),
                         delayed_send_trade_book(books))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
