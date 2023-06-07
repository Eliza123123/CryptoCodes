import asyncio

from lib.discord import delayed_send_trade_book
from liquidation_acme import ws, process_message, process_trade_book, trade_books, conf

discord_webhooks = [
    conf.discord_webhook_config_1,
    conf.discord_webhook_config_2,
    conf.discord_webhook_config_3,
    conf.discord_webhook_config_4,
    conf.discord_webhook_config_5,
]


async def main():
    tasks = [
        ws.stream(),
        ws.on_liquidation(process_message),
        ws.on_kline(process_trade_book)
    ]

    # Adding tasks for each trade_book with corresponding webhook
    for book, discord_webhook in zip(trade_books, discord_webhooks):
        tasks.append(delayed_send_trade_book(book, discord_webhook))

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
