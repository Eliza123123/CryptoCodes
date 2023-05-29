import asyncio
import websockets
import json
from datetime import datetime

websocket_uri = "wss://fstream.binance.com/ws/!forceOrder@arr"


async def print_liquidations(uri):
    async with websockets.connect(uri) as websocket:
        try:
            while True:
                msg = await websocket.recv()
                msg = json.loads(msg)["o"]
                symbol = msg["s"]
                side = "Buyer Liquidated" if msg["S"] == "SELL" else "Seller Liquidated"
                quantity = float(msg["q"])
                price = float(msg["p"])
                m1 = "Symbol: " + symbol
                m2 = "Side: " + side
                m3 = "Quantity: " + msg["q"]
                m4 = "Price: " + msg["p"]
                m5 = "USD Value: $" + str(round(quantity * price, 2))
                m5float = float(round(quantity * price, 2))
                m6 = "Timestamp: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                m7 = "-----------------"
                blocktext = '\n'.join([m1, m2, m3, m4, m5, m6, m7])
                if m5float > 1:
                    print(blocktext)
        except Exception as e:
            print(e)


print('starting')
asyncio.run(print_liquidations(websocket_uri))
