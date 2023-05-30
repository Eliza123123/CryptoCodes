import statistics

from tabulate import tabulate

from trading_tool_functions import json, get_scale, \
    through_pnz_small, colour_print, REVERSE, price_within, MAGENTA, \
    GREEN, CYAN, YELLOW, BLUE, BLACK, fetch_data, UNDERLINE, RED, BOLD
from acme_calculations import pnz_bigs, pnz_smalls
from keys import api_key
from datetime import datetime

import websockets
from websockets import exceptions
import colorama
import queue
import asyncio

websocket_uri = "wss://fstream.binance.com/ws/!forceOrder@arr"
url = 'https://fapi.binance.com/fapi/v1/klines'
headers = {'X-MBX-APIKEY': api_key}

colorama.init()
messages = queue.Queue()


async def binance_liquidations(uri: str) -> None:
    """
    This function establishes a WebSocket connection to Binance and continuously processes
    liquidation messages. These messages are passed to the process_symbols function for further processing.

    The function leverages the ping mechanism inherent to WebSockets to keep the connection alive.
    The ping_interval parameter is set to 20 seconds, meaning that a ping frame is sent to the server
    every 20 seconds. If no pong response is received from the server within the ping_timeout
    period (set to 10 seconds), the client presumes the connection is dead and will throw
    a websockets.exceptions.ConnectionClosedError.

    In the event of an unexpected disconnection, the function will attempt to reconnect
    after a 1-second delay.

    :param uri: The URI to connect to the Binance WebSocket.
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
            await asyncio.sleep(1)  # Wait before reconnecting
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            break


async def process_messages(liquidation_size_filter: int) -> None:
    """
     Continuously processes messages from a global queue.

     The function runs in an infinite loop, during which it checks if the global message queue is not empty.
     If the queue contains messages, it fetches a message, processes it, and sends it for further processing
     if certain conditions are met.

     Each message is a dictionary containing details about a liquidation event. The function extracts the
     symbol, quantity, and price from the message, and then constructs a block of text containing these
     details along with additional information like the side of the trade (buyer/seller liquidated), the
     USD value of the trade, and a timestamp.

     If the USD value of the trade is greater than a predefined threshold (liquidation_size_filter), the
     function sends the symbol and the block of text to the process_symbols function for further processing.

     If the queue is empty, the function waits for 0.01 seconds before checking the queue again. This
     pause is necessary to prevent the CPU from constantly polling the queue when it's empty, which can
     lead to high CPU usage (a condition known as 'CPU spin').

     This is a coroutine function and must be used with await or inside another coroutine function.

     :param liquidation_size_filter: Any liquidation values under this level will not be passed to process_symbols
    """
    while True:
        if not messages.empty():
            msg = messages.get()
            symbol = msg["s"]
            quantity = float(msg["q"])
            price = float(msg["p"])
            liq_value = round(quantity * price, 2)

            m1 = '-' * 50
            m2 = "Symbol: " + symbol
            m3 = "Side: " + "Buyer Liquidated" \
                if msg["S"] == "SELL" else "Seller Liquidated"
            m4 = "Quantity: " + msg["q"]
            m5 = "Price: " + msg["p"]
            m6 = "Liquidation Value: $" + str(round(quantity * price, 2))
            m7 = "Timestamp: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            blocktext = '\n'.join([m1, m2, m3, m4, m5, m6, m7])

            if float(round(quantity * price, 2)) > liquidation_size_filter:
                # Pass the symbol to process_symbols function
                await process_symbols(symbol, blocktext, liq_value)
        else:
            await asyncio.sleep(0.01)  # prevent CPU spin when the queue is empty


last_calculated = {}  # dictionary to keep track of when each symbol was last calculated
zscore_tables = {}


async def volume_filter(symbol: str, n: int, *timeframes: str) -> dict:
    print('*' * 50)
    colour_print(f"{symbol} multi-timeframe volume analysis", UNDERLINE, return_message=False)

    last_time = last_calculated.get(symbol)
    if last_time is not None:
        # If it was calculated less than 5 minutes ago, print the stored Z-score table and return
        if (datetime.now() - last_time).seconds < 5 * 60:
            print(zscore_tables[symbol])
            return zscore_tables[symbol]  # return the previously stored Z-scores

    # Create a list of tasks to run concurrently
    tasks = []
    for timeframe in timeframes:
        parameters = {
            'symbol': symbol,
            'interval': timeframe,
            'limit': n,
        }
        tasks.append(fetch_data(url=url, parameters=parameters, headers=headers))

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

    # Print and store the Z-scores in a table
    table = tabulate([[tf, zs] for tf, zs in zscores.items()],
                     headers=["Timeframe", "Z-score"], tablefmt="pipe", floatfmt=".2f")
    print(table)
    zscore_tables[symbol] = zscores  # store the Z-scores

    # Update the time of the last calculation for this symbol
    last_calculated[symbol] = datetime.now()

    return zscores  # return the Z-scores


async def process_symbols(symbol: str, liquidation_message: str, liq_value: float) -> list:
    """
    Processes the given symbol and performs various calculations and checks related to liquidations.

    This function performs a series of operations on the symbol data related to liquidations:
    1. Fetches the latest candle data for the symbol from Binance with a 1-minute interval.
    2. If the fetched data is not empty, the open and close prices of the candle are extracted,
       and then scaled by dividing by the respective scale values.
    3. The liquidation message is printed and the scaled close price is displayed.
    4. The function then checks whether the scaled open and close prices pass through
       predefined ACME small price levels, and prints a message if so.
    5. The function checks whether the scaled close price is within predefined ACME big price
       levels. If so, it prints a message indicating the relevant level and breaks out of the loop.
    6. If the fetched data is empty, the function prints a message indicating that no data is available.
    7. Finally, it prints a separator line to delimit the output for each symbol.

    This is a coroutine function and should be used with await or inside another coroutine function.

    :param liq_value:
    :param symbol: The trading symbol to be processed.

    :param liquidation_message: The message associated with a liquidation event for the symbol.
    """
    parameters = {
        'symbol': symbol,
        'interval': '1m',
        'limit': 1,
    }
    data = await fetch_data(url=url, parameters=parameters, headers=headers)
    this_message = []  # initialize list for storing messages

    if data:  # Check if data is not empty
        candle_open = float(data[0][1])
        candle_close = float(data[0][4])
        scale_factor = get_scale(min(candle_open, candle_close))
        scaled_open = candle_open / scale_factor
        scaled_close = candle_close / scale_factor

        color_map = {6: (MAGENTA, REVERSE), 5: (GREEN, REVERSE),
                     4: (CYAN, REVERSE), 3: (YELLOW, REVERSE),
                     2: (BLUE, REVERSE), 1: (BLACK, REVERSE)}

        this_message.append(liquidation_message)
        this_message.append(f"Scaled Price: {scaled_close}")

        flag_pnz_small = False
        seen_tups = set()
        for tup in pnz_smalls[1]:
            if tup not in seen_tups and through_pnz_small([tup],
                                                          scaled_open,
                                                          scaled_close):
                seen_tups.add(tup)
                flag_pnz_small = True
                this_message.append(colour_print(f"ACME Small: {tup}",
                                                 REVERSE,
                                                 return_message=True))
        flag_pnz_big = False

        for key in range(3, 6):
            for tup in pnz_bigs[key]:
                if price_within([tup], scaled_close):
                    flag_pnz_big = True
                    this_message.append(colour_print(f"ACME Big {key}: {tup}",
                                                     *color_map[key],
                                                     return_message=True))
                    break
            if flag_pnz_big:
                break

        if not flag_pnz_big and not flag_pnz_small:
            this_message.append("Not in ACME big zone or across ACME small zone")

        if flag_pnz_small or flag_pnz_big:
            volume_scores = await volume_filter(symbol, 27,
                                                '1m', '3m',
                                                '5m', '15m',
                                                '30m', '1h',
                                                '2h', '4h')

            if 'Buyer Liquidated' in liquidation_message:
                if liq_value > 4427:
                    if any(z_score > 2 for z_score in volume_scores.values()):
                        this_message.append(colour_print("\nBuy conditions are met.",
                                                         GREEN, BOLD, UNDERLINE,
                                                         return_message=True))

            if 'Seller Liquidated' in liquidation_message:
                if liq_value > 4427:
                    if any(z_score > 2 for z_score in volume_scores.values()):
                        this_message.append(colour_print("\nSell conditions are met.",
                                                         RED, BOLD, UNDERLINE,
                                                         return_message=True))

    else:
        this_message.append("No data available in the response.")

    this_message.append('*' * 50)
    this_message.append('\n')

    # printing all the messages at the end
    for message in this_message:
        print(message)
    return this_message
