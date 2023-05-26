from trading_tool_functions import *
from datetime import datetime
from babylonicus_deductions import pnz
import colorama
import asyncio
import websockets
import json
from keys import api_key

websocket_uri = "wss://fstream.binance.com/ws/!forceOrder@arr"

url = 'https://fapi.binance.com/fapi/v1/klines'


headers = {
    'X-MBX-APIKEY': api_key
}

symbols = ['FOOTBALLUSDT',
           'OPUSDT',
           'UNFIUSDT',
           'ATAUSDT',
           'BTCUSDT',
           'ETHUSDT',
           'BNBUSDT',
           ]

filename = 'market-kline.json'

updates = [0]
# updates = [0, 15, 30, 45]

colorama.init()


async def binance_liquidations(uri):
    async with websockets.connect(uri) as websocket:
        try:
            while True:
                msg = await websocket.recv()
                msg = json.loads(msg)["o"]
                symbol = msg["s"]  # 'ATAUSDT' (for testing)
                side = "Buyer Liquidated" if msg["S"] == "SELL" else "Seller Liquidated"
                quantity = float(msg["q"])
                price = float(msg["p"])
                m1 = "Symbol: " + symbol
                m2 = "Side: " + side
                m3 = "Quantity: " + msg["q"]
                m4 = "Price: " + msg["p"]
                m5 = "USD Value: $" + str(round(quantity * price, 2))
                m5float = float(round(quantity * price, 2))
                m6 = "-----------------"
                blocktext = '\n'.join([m1, m2, m3, m4, m5, m6])
                if m5float > 1 and (symbol in symbols):
                    colour_print("TARGET MARKET LIQUIDATION", RED, REVERSE)
                    colour_print(blocktext, RED, REVERSE)
        except Exception as e:
            print(e)


async def process_symbols():
    while True:
        if datetime.now().second in updates:
            for symbol in symbols:
                parameters = {
                    'symbol': symbol,
                    'interval': '1m',
                    'limit': 1,
                }
                print('*' * 27)
                store_data(url=url, parameters=parameters, headers=headers, filename=filename)
                with open(filename, 'r') as file:
                    data = json.load(file)
                    price = float(data[0][4])
                    scaled_price = price / get_scale(price)
                    print(f"Symbol: {symbol}")
                    print(f"Scaled Price: {scaled_price}")
                    found_match = False  # Flag variable
                    for key in range(1, 8):
                        for tup in pnz[key]:
                            if price_within([tup], scaled_price):
                                found_match = True
                                if key == 6:
                                    colour_print(f"ACME{key}: {tup}", MAGENTA, REVERSE)
                                if key == 5:
                                    colour_print(f"ACME{key}: {tup}", GREEN, REVERSE)
                                if key == 4:
                                    colour_print(f"ACME{key}: {tup}", CYAN, REVERSE)
                                if key == 3:
                                    colour_print(f"ACME{key}: {tup}", YELLOW, REVERSE)
                                break
                        if found_match:
                            break
            print('*' * 27)
            print()
        await asyncio.sleep(1)


async def main():
    symbol_processing_task = asyncio.create_task(process_symbols())
    liquidations_task = asyncio.create_task(binance_liquidations(websocket_uri))
    await asyncio.gather(symbol_processing_task, liquidations_task)


print('Starting...')
asyncio.run(main())
