from asyncio import sleep

import requests
from tabulate import tabulate

from config import Config

conf = Config("config.yaml")


def send_entry(zs_table, table, side) -> None:
    result = requests.post(conf.discord_entry_webhook, json={
        "content": f"**New Entry**\n```{zs_table}\n\n{table}\n\n{'🟥 🟥 🟥 SELL 🟥 🟥 🟥' if side == 'BUY' else '🟩 🟩 🟩 BUY 🟩 🟩 🟩'}```",
        "username": "ACME"
    })

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)


def send_exit(table) -> None:
    result = requests.post(conf.discord_exit_webhook, json={
        "content": f"**Exit**\n```{table}\n```",
        "username": "ACME"
    })

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)


def send_trade_book(books) -> None:
    # Iterate over each strategy, symbol and its trades in the book
    for strategy, trades in books.as_dict():
        if len(trades) == 0:
            continue

        net_open_perc = 0
        for symbol, trade in trades.items():
            net_open_perc += trade['perc']

        message = "\n".join([
            tabulate([[i for i in trade.values()] for symbol, trade in trades.items()],
                     headers=["Symbol", "Side", "Entry Price", "Entry Timestamp", "Market Price", "Percent Gain"],
                     tablefmt="simple", floatfmt=".2f"),
            "-" * 87,
            f"Open Profit: {round(net_open_perc, 2)}% {'🟩' if net_open_perc > 0 else '🟥' if net_open_perc < 0 else '🟧'}"
        ])

        result = requests.post(conf[strategy]["webhook"], json={
            "content": f"\n```\n{message}\n```",
            "username": "ACME"
        })

        try:
            result.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)


async def delayed_send_trade_book(book) -> None:
    while True:
        send_trade_book(book)
        await sleep(conf.trade_book_wait)
