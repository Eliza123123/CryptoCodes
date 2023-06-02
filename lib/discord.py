import json
import requests

from config import Config
from tabulate import tabulate

conf = Config("config.yaml")


def send_dictionary_to_channel(dictionary):
    # Convert the dictionary to a JSON-formatted string
    message = json.dumps(dictionary, indent=4)
    result = requests.post(conf.discord_webhook_2, json={
        "content": f"```\n{message}\n```",  # Surrounding the message with backticks for code block formatting in Discord
        "username": "ACME"
    })

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)


def send_simple_message_to_channel(message):
    result = requests.post(conf.discord_webhook_2, json={
        "content": message,
        "username": "ACME"
    })

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)


def send_to_channel(zs_table, table, confirmation):
    content = ("\n" + "-" * 65 + "\n").join([zs_table, table])

    result = requests.post(conf.discord_webhook, json={
        "content": f"**New Entry**\n```{content}\n\n{confirmation}```",
        "username": "ACME"
    })

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)


# def send_trade_book(dictionary):
#     # Create a table header
#     table_header = ["Symbol", "Average Entry Price"]
#     # Create a list to hold the table data
#     table_data = []
#
#     # Iterate over the dictionary
#     for symbol, prices in dictionary.items():
#         # Calculate the average price
#         avg_price = sum(prices) / len(prices)
#         # Add a row to the table data
#         table_data.append([symbol, avg_price])
#
#     # Create a table
#     table = tabulate(table_data, headers=table_header, tablefmt="plain", floatfmt=".2f")
#
#     result = requests.post(conf.discord_webhook, json={
#         "content": f"**Trade Book**\n```\n{table}\n```",  # Added title "Trade Book"
#         "username": "ACME"
#     })
#
#     try:
#         result.raise_for_status()
#     except requests.exceptions.HTTPError as err:
#         print(err)
