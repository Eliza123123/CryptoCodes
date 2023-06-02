import requests

from config import Config

conf = Config("config.yaml")


def send_dictionary_to_channel(dictionary):
    # Build a formatted message from the dictionary
    lines = []
    net_profit = 0  # Initialize net profit
    for symbol, entries in dictionary.items():
        lines.append(symbol)
        for entry, data in entries.items():
            entry_num = entry.split('_')[1]  # Extract entry number from 'entry_X'
            side = data['side']  # Simplify side
            entry_price = round(data['entry_price'], 2)  # Round to 2 decimal places
            market_price = round(data['market_price'], 2)  # Round to 2 decimal places
            gain = round(data['percentage_gain'], 2)  # Round gain to 2 decimal places
            net_profit += gain  # Add gain to net profit
            # Add emoji based on gain
            emoji = '🟩' if gain > 0 else '🟥' if gain < 0 else '🟧'
            line = f"    Entry {entry_num}: {side} at {entry_price}, current price {market_price}, gain {gain}% {emoji}"
            lines.append(line)

    # Determine net profit emoji
    net_profit_emoji = '🟩🟩🟩' if net_profit > 0 else '🟥🟥🟥' if net_profit < 0 else '🟧🟧🟧'
    # Add a separating line and net profit line
    lines.append("------------------------------------------------------------------------------------")  # Markdown for horizontal line
    lines.append(f"Net Profit: {round(net_profit, 2)}% {net_profit_emoji}")

    # Combine all lines into a single string, with line breaks between lines
    message = "\n".join(lines)

    # Send the message
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
