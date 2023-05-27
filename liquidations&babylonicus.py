import asyncio
from datetime import datetime
import websockets
from trading_tool_functions import *
from babylonicus_deductions import pnz
import colorama
from keys import api_key

websocket_uri = "wss://fstream.binance.com/ws/!forceOrder@arr"
url = 'https://fapi.binance.com/fapi/v1/klines'

headers = {
    'X-MBX-APIKEY': api_key
}

symbols = []

filename = 'market-kline.json'


colorama.init()


async def binance_liquidations(uri):
    async with websockets.connect(uri) as websocket:
        try:
            while True:
                msg = await websocket.recv()
                msg = json.loads(msg)["o"]
                symbol = msg["s"]  # (for testing)
                side = "Buyer Liquidated" if msg["S"] == "SELL" else "Seller Liquidated"
                quantity = float(msg["q"])
                price = float(msg["p"])
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get current timestamp
                m1 = '*' * 40
                m2 = "Symbol: " + symbol
                m3 = "Side: " + side
                m4 = "Quantity: " + msg["q"]
                m5 = "Price: " + msg["p"]
                m6 = "USD Value: $" + str(round(quantity * price, 2))
                m7 = "Timestamp: " + timestamp  # Add timestamp to the message
                m5float = float(round(quantity * price, 2))
                blocktext = '\n'.join([m1, m2, m3, m4, m5, m6, m7])
                if m5float > 1:
                    print(blocktext)
                    await process_symbols(symbol)  # Pass the symbol to process_symbols function
        except Exception as e:
            print(e)


async def process_symbols(symbol):
    parameters = {
        'symbol': symbol,
        'interval': '1m',
        'limit': 1,
    }
    store_data(url=url, parameters=parameters, headers=headers, filename=filename)
    with open(filename, 'r') as file:
        data = json.load(file)
        if data:  # Check if data is not empty
            price = float(data[0][4])
            scaled_price = price / get_scale(price)
            print(f"Scaled Price: {scaled_price}")
            found_match = False  # Flag variable
            for key in range(1, 8):
                for tup in pnz[key]:
                    if price_within([tup], scaled_price):
                        found_match = True
                        if key == 6:
                            colour_print(f"ACME{key}: {tup}", MAGENTA, REVERSE)
                        elif key == 5:
                            colour_print(f"ACME{key}: {tup}", GREEN, REVERSE)
                        elif key == 4:
                            colour_print(f"ACME{key}: {tup}", CYAN, REVERSE)
                        elif key == 3:
                            colour_print(f"ACME{key}: {tup}", YELLOW, REVERSE)
                        break
                if found_match:
                    break
        else:
            print("No data available in the file.")
    print('*' * 40)
    print()


async def main():
    tasks = []
    for symbol in symbols:
        symbol_processing_task = asyncio.create_task(process_symbols(symbol))
        tasks.append(symbol_processing_task)
    liquidations_task = asyncio.create_task(binance_liquidations(websocket_uri))
    await asyncio.gather(*tasks, liquidations_task)


if __name__ == '__main__':
    asyncio.run(main())
