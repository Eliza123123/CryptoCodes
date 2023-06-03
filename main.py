import asyncio

from Lib.discord import delayed_send_trade_book
from liquidation_acme import ws, process_message, process_trade_book, trade_book


async def main():
    await asyncio.gather(ws.stream(),
                         ws.on_liquidation(process_message),
                         ws.on_kline(process_trade_book),
                         delayed_send_trade_book(trade_book))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
