import locale
from datetime import datetime
from tabulate import tabulate
from websockets import exceptions
from acme_calculations import pnz_bigs, pnz_smalls
from trading_tool_functions import json, get_scale, \
    through_pnz_small, colour_print, price_within, fetch_data, \
    MAGENTA, GREEN, CYAN, YELLOW, BLUE, BLACK, RED, \
    UNDERLINE, BOLD, REVERSE

import websockets
import colorama
import queue
import asyncio
import statistics

websocket_uri = "wss://fstream.binance.com/ws/!forceOrder@arr"
url = 'https://fapi.binance.com/fapi/v1/klines'

colorama.init()
locale.setlocale(locale.LC_MONETARY, '')
messages = queue.Queue()

last_calculated = {}  # dictionary to keep track of when each symbol was last calculated
zscore_tables = {}

vol_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h']
vol_candle_lookback = 27

output_table = []
output_confirmation = []


async def binance_liquidations(uri: str) -> None:
    """
    This is an asynchronous coroutine that establishes a connection with the Binance
    cryptocurrency exchange's liquidation data websocket server and continuously monitors
    the stream of data.

    If the connection to the server is lost, the function automatically attempts to
    reconnect after a brief delay.

    Each message received from the server is a JSON string representing a liquidation
    event. The function loads the JSON string into a Python dictionary and puts it into
    a global queue for further processing.

    :param uri: The Uniform Resource Identifier (URI) of the websocket server.
    :return None: The function runs indefinitely, receiving messages and putting them in the
        global queue.
    """
    while True:  # Add a loop for automatic reconnection
        try:
            async with websockets.connect(uri, ping_interval=20, ping_timeout=10) as websocket:
                while True:
                    msg = await websocket.recv()
                    if msg is None:
                        break  # Connection closed cleanly
                    else:
                        messages.put(json.loads(msg)["o"])
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Connection closed unexpectedly: {e}. Retrying connection...")
        except Exception as e:
            print(f"Unexpected error occurred: {e}. Retrying connection...")
        finally:
            await asyncio.sleep(1)  # Wait before reconnecting


async def process_messages(liquidation_size_filter: int) -> None:
    """
    This function is an asynchronous coroutine that continuously monitors and processes messages
    from a global queue. The messages represent cryptocurrency liquidation events.

    Each message in the queue is a dictionary containing details about a single liquidation event.
    The function pulls messages from the queue, extracts the relevant details (such as symbol,
    quantity, and price), and formats this data into a human-readable text block.

    If the calculated USD value of the liquidation event (quantity * price) exceeds the
    'liquidation_size_filter', the function forwards the symbol and the formatted message to
    the 'process_symbols' function for further processing.

    When the queue is empty, the function waits for a short period (0.01 seconds) before checking
    the queue again to avoid excessive CPU usage.

    :param liquidation_size_filter: This value acts as a filter threshold. Liquidation events
        with a calculated USD value below this threshold are ignored.
    :return None: The function runs indefinitely, processing messages and passing them to
        'process_symbols' as needed.
    """
    while True:
        if not messages.empty():
            msg = messages.get()
            symbol = msg["s"]
            quantity = float(msg["q"])
            price = float(msg["p"])
            liq_value = round(float(quantity * price), 2)

            if liq_value > liquidation_size_filter:
                candle_open, candle_close, scaled_open, scaled_close = await get_scaled_price(symbol)

                output_table.append(["Symbol", symbol])
                output_table.append(["Side", "Buyer Liquidated" if msg["S"] == "SELL" else "Seller Liquidated"])
                output_table.append(["Quantity", msg["q"]])
                output_table.append(["Price", msg["p"]])
                output_table.append(["Liquidation Value", locale.currency(liq_value, grouping=True)])
                output_table.append(["Timestamp", datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                output_table.append(["Scaled Price", scaled_close])

                pnz = await get_pnz(scaled_open, scaled_close)

                if pnz:
                    zscore_vol = await volume_filter(symbol, vol_candle_lookback, vol_timeframes)

                    print('-' * 65)
                    # 1. Print volume analysis
                    print(tabulate([['Z-Score'] + [zs for zs in zscore_vol.values()]],
                                   headers=['Timeframe'] + [zs for zs in zscore_vol.keys()],
                                   tablefmt="simple",
                                   floatfmt=".2f"))
                    print('-' * 65)
                    # 2. Print symbol info
                    print(tabulate(output_table, tablefmt="plain"))
                    print('-' * 65)

                    if any(z_score > 2 for z_score in zscore_vol.values()) and liq_value > 4427:
                        side = "Sell" if msg["S"] == "SELL" else "Buy"
                        color = GREEN if msg["S"] == "SELL" else RED
                        output_confirmation.append("\n")
                        output_confirmation.append(colour_print(f"{side} conditions are met", color, BOLD, UNDERLINE, return_message=True))
                        output_confirmation.append("\n")
                else:
                    output_confirmation.append("Liquidation: ACME not detected.")

                # 3. Print confirmation messages
                for confirmation in output_confirmation:
                    print(confirmation)

                # Reset tables
                output_table.clear()
                output_confirmation.clear()
        else:
            await asyncio.sleep(0.01)  # prevent CPU spin when the queue is empty


async def volume_filter(symbol: str, n: int, timeframes: list) -> dict:
    """
    This function calculates the Z-scores of trading volumes for multiple timeframes of a given symbol
    and displays them in a tabulated format.

    It first checks if the Z-scores for the symbol were calculated within the last 5 minutes. If they were,
    it prints the stored Z-scores and returns them. If not, it sends requests to fetch the latest trading data
    for each timeframe and calculates the Z-scores.

    The Z-scores are calculated as follows:
    Z-score = (current_volume - mean_volume) / standard_deviation_volume

    Once calculated, the Z-scores are printed in a tabulated format and stored for later use.

    This function leverages asyncio.gather() to send multiple requests concurrently, improving the speed
    and efficiency of the function.

    :param symbol: The trading symbol to fetch data for.
    :param n: The number of latest data points to fetch for each timeframe.
    :param timeframes: Variable length argument, each specifying a timeframe to fetch data for.
    :return: A dictionary where each key is a timeframe and its corresponding value is the Z-score
             for that timeframe.
    """

    last_time = last_calculated.get(symbol)
    if last_time is not None:
        # If it was calculated less than 5 minutes ago, print the stored Z-score table and return
        if (datetime.now() - last_time).seconds < 5 * 60:
            return zscore_tables[symbol]  # return the previously stored Z-scores as a dict

    # Create a list of tasks to run concurrently
    tasks = []
    for timeframe in timeframes:
        parameters = {
            'symbol': symbol,
            'interval': timeframe,
            'limit': n,
        }
        tasks.append(fetch_data(url, parameters))

    # Gather tasks and run them concurrently
    responses = await asyncio.gather(*tasks)

    # Prepare a dictionary to store Z-scores for each timeframe
    zscores = {}

    for response, timeframe in zip(responses, timeframes):
        volumes = [float(bar[5]) for bar in response]
        mean_volume = statistics.mean(volumes)
        std_volume = statistics.stdev(volumes)
        current_volume = volumes[-2]  # last complete candle
        z_score = (current_volume - mean_volume) / std_volume

        # Store the Z-score for this timeframe in the dictionary
        zscores[timeframe] = z_score

    zscore_tables[symbol] = zscores  # store the Z-scores

    # Update the time of the last calculation for this symbol
    last_calculated[symbol] = datetime.now()

    return zscores  # return the Z-scores


async def get_scaled_price(symbol: str) -> list:
    parameters = {
        'symbol': symbol,
        'interval': '1m',
        'limit': 1,
    }
    data = await fetch_data(url, parameters)

    if not data:
        return []

    candle_open = float(data[0][1])
    candle_close = float(data[0][4])
    scale_factor = get_scale(min(candle_open, candle_close))
    return [candle_open, candle_close, candle_open / scale_factor, candle_close / scale_factor]


async def get_pnz(scaled_open: float, scaled_close: float) -> bool:
    color_map = {
        6: (MAGENTA, REVERSE), 5: (GREEN, REVERSE),
        4: (CYAN, REVERSE), 3: (YELLOW, REVERSE),
        2: (BLUE, REVERSE), 1: (BLACK, REVERSE)
    }

    flag_pnz_sm = False
    seen_tups = set()

    for tup in pnz_smalls[1]:
        if tup not in seen_tups and through_pnz_small([tup], scaled_open, scaled_close):
            seen_tups.add(tup)
            flag_pnz_sm = True
            output_table.append([colour_print(f"ACME Small", REVERSE, return_message=True), tup])

    for key in range(3, 6):
        for tup in pnz_bigs[key]:
            if price_within([tup], scaled_close):
                output_table.append([colour_print(f"ACME Big {key}", *color_map[key], return_message=True), tup])
                return True

    return flag_pnz_sm

# async def process_symbols(symbol: str, liq_value: float) -> None:
#     """
#     Processes the given symbol and performs various calculations and checks related to liquidations.
#
#     This function performs a series of operations on the symbol data related to liquidations:
#     1. Fetches the latest candle data for the symbol from Binance with a 1-minute interval.
#     2. If the fetched data is not empty, the open and close prices of the candle are extracted,
#        and then scaled by dividing by the respective scale values.
#     3. The liquidation message is printed and the scaled close price is displayed.
#     4. The function then checks whether the scaled open and close prices pass through
#        predefined ACME small price levels, and prints a message if so.
#     5. The function checks whether the scaled close price is within predefined ACME big price
#        levels. If so, it prints a message indicating the relevant level and breaks out of the loop.
#     6. If the fetched data is empty, the function prints a message indicating that no data is available.
#     7. Depending on the liquidation value, the function checks if the buy or sell conditions are met,
#        and if so, it appends an appropriate message to the list.
#     8. Finally, it prints a separator line to delimit the output for each symbol and returns the list of messages.
#
#     This is a coroutine function and should be used with await or inside another coroutine function.
#
#     :param symbol: The trading symbol to be processed.
#     :param liquidation_message: The message associated with a liquidation event for the symbol.
#     :param liq_value: The value associated with a liquidation event for the symbol.
#
#     :return: A list of messages to be printed.
#     """
#     parameters = {
#         'symbol': symbol,
#         'interval': '1m',
#         'limit': 1,
#     }
#     data = await fetch_data(url, parameters)
#     this_message = []  # initialize list for storing messages
#
#     if data:  # Check if data is not empty
#         candle_open = float(data[0][1])
#         candle_close = float(data[0][4])
#         scale_factor = get_scale(min(candle_open, candle_close))
#         scaled_open = candle_open / scale_factor
#         scaled_close = candle_close / scale_factor
#
#         color_map = {6: (MAGENTA, REVERSE), 5: (GREEN, REVERSE),
#                      4: (CYAN, REVERSE), 3: (YELLOW, REVERSE),
#                      2: (BLUE, REVERSE), 1: (BLACK, REVERSE)}
#
#         output_table.append(["Scaled Price", scaled_close])
#
#         flag_pnz_small = False
#         seen_tups = set()
#         for tup in pnz_smalls[1]:
#             if tup not in seen_tups and through_pnz_small([tup], scaled_open, scaled_close):
#                 seen_tups.add(tup)
#                 flag_pnz_small = True
#                 this_message.append(colour_print(f"ACME Small: {tup}",
#                                                  REVERSE,
#                                                  return_message=True))
#         flag_pnz_big = False
#
#         for key in range(3, 6):
#             for tup in pnz_bigs[key]:
#                 if price_within([tup], scaled_close):
#                     flag_pnz_big = True
#                     this_message.append(colour_print(f"ACME Big {key}: {tup}",
#                                                      *color_map[key],
#                                                      return_message=True))
#                     break
#             if flag_pnz_big:
#                 break
#
#         if flag_pnz_small or flag_pnz_big:
#             print("a")
#             # zscore_vol = await volume_filter(symbol, vol_candle_lookback, vol_timeframes)
#             #
#             # # Print volume analysis
#             # print(tabulate([['Z-Score'] + [zs for zs in zscore_vol.values()]],
#             #                headers=['Timeframe'] + [zs for zs in zscore_vol.keys()],
#             #                tablefmt="simple",
#             #                floatfmt=".2f"))
#             #
#             # if any(z_score > 2 for z_score in zscore_vol.values()):
#             #     if liq_value > 4427:
#             #         side = "Buy" if 'Buyer' in liquidation_message else "Sell"
#             #         color = GREEN if 'Buyer' in liquidation_message else RED
#             #         this_message.append(colour_print(f"{side} conditions are met", color, BOLD, UNDERLINE, return_message=True))
#
#         else:
#             this_message.append("Not in ACME big zone or across ACME small zone")
#     else:
#         this_message.append("No data available in the response.")
#
#     # this_message.append('*' * 50)
#     this_message.append('\n')
#
#     # printing all the messages at the end
#     for message in this_message:
#         print(message)
