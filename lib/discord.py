from asyncio import sleep
from datetime import datetime

import requests
from tabulate import tabulate

from config import Config

conf = Config("config.yaml")


def send_text(message: str) -> None:
    result = requests.post(conf.discord_webhook_3, json={
        "content": message,
        "username": "ACME"
    })

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)


def send_exit_message(symbol: str, perc: float, total_profit: float) -> None:
    message = (
        f"```Trade for {symbol} closed with {round(perc, 2)}% gain.\n"
        f"Total profit is now {round(total_profit, 2)}%.\n"
        f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Leverage: {conf.leverage}x```"
    )

    result = requests.post(conf.discord_webhook_3, json={
        "content": message,
        "username": "ACME"
    })

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)


def send_to_channel(zs_table, table, confirmation) -> None:
    content = ("\n" + "-" * 65 + "\n").join([zs_table, table])

    result = requests.post(conf.discord_webhook, json={
        "content": f"**New Entry**\n```{content}\n\n{confirmation}```",
        "username": "ACME"
    })

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)


def send_trade_book(book: dict, discord_webhook) -> None:
    # Initialize a variable for net open percentage
    net_open_perc = 0

    # Iterate over each symbol and its trades in the book
    for symbol, trades in book.items():
        for trade in trades:
            net_open_perc += trade['perc']

    net_open_perc_emoji = '🟩🟩🟩' if net_open_perc > 0 else '🟥🟥🟥' if net_open_perc < 0 else '🟧🟧🟧'

    lines = [
        tabulate([[i for i in j.values()] for symbol, trades in book.items() for j in trades],
                 headers=["Symbol", "Side", "Entry Price", "Entry Timestamp", "Market Price", "Percent Gain"],
                 tablefmt="simple", floatfmt=".2f"),
        "-" * 65,
        f"Open Profit: {round(net_open_perc, 2)}% {net_open_perc_emoji}"
    ]

    message = "\n".join(lines)

    print(message)

    result = requests.post(discord_webhook, json={
        "content": f"\n```\n{message}\n```",
        "username": "ACME"
    })

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)


async def delayed_send_trade_book(books: list, discord_webhook) -> None:
    while conf.discord_webhook_config_1_enabled:
        for book in books:
            if len(book) > 0:
                send_trade_book(book, discord_webhook)

            await sleep(conf.trade_book_wait)
