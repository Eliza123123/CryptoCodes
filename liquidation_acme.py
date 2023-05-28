from trading_tool_functions import json, get_scale, \
    through_pnz_small, colour_print, REVERSE, price_within, MAGENTA, \
    GREEN, CYAN, YELLOW, fetch_data
from acme_calculations import pnz_bigs, pnz_smalls
from keys import api_key
from datetime import datetime

import websockets
from websockets import exceptions
import colorama
import queue
import asyncio

colorama.init()

websocket_uri = "wss://fstream.binance.com/ws/!forceOrder@arr"
url = 'https://fapi.binance.com/fapi/v1/klines'

headers = {
    'X-MBX-APIKEY': api_key
}

symbols = []
liquidation_size_filter = 1

messages = queue.Queue()


async def binance_liquidations(uri: str) -> None:
    """
    Connects to the Binance WebSocket and processes liquidation messages.
    Passes the symbol to the process_symbols function.

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


async def process_messages():
    while True:
        if not messages.empty():
            msg = messages.get()
            symbol = msg["s"]
            quantity = float(msg["q"])
            price = float(msg["p"])

            m1 = '*' * 40
            m2 = "Symbol: " + symbol
            m3 = "Side: " + "Buyer Liquidated" \
                if msg["S"] == "SELL" else "Seller Liquidated"
            m4 = "Quantity: " + msg["q"]
            m5 = "Price: " + msg["p"]
            m6 = "USD Value: $" + str(round(quantity * price, 2))
            m7 = "Timestamp: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            blocktext = '\n'.join([m1, m2, m3, m4, m5, m6, m7])

            if float(round(quantity * price, 2)) > liquidation_size_filter:
                # Pass the symbol to process_symbols function
                await process_symbols(symbol, blocktext)
        else:
            await asyncio.sleep(0.01)  # prevent CPU spin when the queue is empty


async def process_symbols(symbol: str, liquidation_message: str) -> None:
    """
    Processes symbols and performs relevant operations.

    :param symbol: The symbol to process.
    :param liquidation_message: The liquidation message associated with the symbol.
    """
    parameters = {
        'symbol': symbol,
        'interval': '1m',
        'limit': 1,
    }
    data = await fetch_data(url=url, parameters=parameters, headers=headers)

    if data:  # Check if data is not empty
        candle_open = float(data[0][1])
        candle_close = float(data[0][4])
        scaled_open = candle_open / get_scale(candle_open)
        scaled_close = candle_close / get_scale(candle_close)

        print(liquidation_message)
        print(f"Scaled Price: {scaled_close}")

        for tup in pnz_smalls[1]:
            if through_pnz_small([tup], scaled_open, scaled_close):
                colour_print(f"ACME Small: {tup}", REVERSE)

        flag_pnz_big = False  # Flag variable
        for key in range(1, 8):
            for tup in pnz_bigs[key]:
                if price_within([tup], scaled_close):
                    flag_pnz_big = True
                    if key == 6:
                        colour_print(f"ACME Big {key}: {tup}", MAGENTA, REVERSE)
                    elif key == 5:
                        colour_print(f"ACME Big {key}: {tup}", GREEN, REVERSE)
                    elif key == 4:
                        colour_print(f"ACME Big {key}: {tup}", CYAN, REVERSE)
                    elif key == 3:
                        colour_print(f"ACME Big {key}: {tup}", YELLOW, REVERSE)
                    break
            if flag_pnz_big:
                break
    else:
        print("No data available in the response.")

    print('*' * 40)
    print()
