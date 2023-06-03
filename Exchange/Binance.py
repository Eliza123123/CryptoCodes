import asyncio
import json

import websockets
from requests import get
from websockets import exceptions, connect


class Websocket:
    """
    Exchange websocket implementation for Binance.
    """

    id: int
    websocket: websockets.connect
    queue: asyncio.Queue
    queue_subscribe: asyncio.Queue

    def __init__(self) -> None:
        self.wss = "wss://fstream.binance.com/ws"
        self.queue_liquidation = asyncio.Queue()
        self.queue_kline = asyncio.Queue()
        self.queue_subscribe = asyncio.Queue()
        self.stream_subscriptions = {}

    def subscribe(self, symbols: list) -> None:
        """
        Subscribe to the kline streams for the given symbols and timeframes

        :param symbols: [("btcusdt", "1m"),...]
        :type symbols: List of tuples containing the symbol and timeframe as strings
        :return:
        :rtype:
        """
        for symbol, timeframe in symbols:
            self.stream_subscriptions[symbol] = f"{symbol}@kline_{timeframe}"

        self.queue_subscribe.put_nowait({
            "method": "SUBSCRIBE",
            "params": [*self.stream_subscriptions.values()],
            "id": 2
        })

    def subscribe_liquidation(self):
        self.queue_subscribe.put_nowait({
            "method": "SUBSCRIBE",
            "params": ["!forceOrder@arr"],
            "id": 1
        })

    def subscribe_klines(self):
        self.queue_subscribe.put_nowait({
            "method": "SUBSCRIBE",
            "params": [*self.stream_subscriptions.values()],
            "id": 1
        })

    def unsubscribe(self, symbols: list) -> None:
        """
        Unsubscribe to the kline streams for the given symbols

        :param symbols: ["btcusdt","ltcusdt",...]
        :type symbols: List of strings containing the symbols
        :return:
        :rtype:
        """

        unsubs = []
        for i in symbols:
            unsubs.append(self.stream_subscriptions[i])
            del self.stream_subscriptions[i]

        self.queue_subscribe.put_nowait({
            "method": "UNSUBSCRIBE",
            "params": unsubs,
            "id": 3
        })

    async def _websocket_stream(self):
        """
        _websocket_stream subscribes to the liquidation stream as default and processes liquidation and klines messages.
        It pushes matching messages into their respective queues.

        :return:
        :rtype:
        """

        self.subscribe_liquidation()

        while True:
            try:
                message = await self.websocket.recv()
                if message is None:
                    break
                m = json.loads(message)
                if "e" in m:
                    if m['e'] == "forceOrder":
                        await self.queue_liquidation.put(m['o'])
                    elif m['e'] == "kline":
                        await self.queue_kline.put(m['k'])
                else:
                    if m["result"] is None and m['id'] == 1:
                        print("Liquidations stream subscribed")
                    elif m["result"] is None and m['id'] == 2:
                        print("Kline stream subscribed")
                    elif m["result"] is None and m['id'] == 3:
                        print("Kline stream unsubscribed")
            except (exceptions.ConnectionClosed, exceptions.ConnectionClosedError) as e:
                print(f"Connection closed unexpectedly: {e}. Retrying connection...")
                await asyncio.sleep(1)
                self.websocket = await connect(self.wss, ping_interval=10, ping_timeout=25)
                self.subscribe_liquidation()
                self.subscribe_klines()
                continue

    async def _stream_subscription(self):
        while True:
            message = await self.queue_subscribe.get()
            await self.websocket.send(json.dumps(message))

    async def on_liquidation(self, fn):
        while True:
            message = await self.queue_liquidation.get()
            await fn(message)

    async def on_kline(self, fn):
        while True:
            message = await self.queue_kline.get()
            await fn(message)

    async def stream(self):
        self.websocket = await connect(self.wss, ping_interval=10, ping_timeout=25)
        await asyncio.gather(self._websocket_stream(), self._stream_subscription())


async def fetch_kline(parameters: dict) -> dict:
    """
    Fetch data from a specified URL, using provided parameters and headers. This function sends an
    asynchronous HTTP GET request to the URL, using the parameters and headers to customize the request.
    Upon receiving the response, it converts the JSON response content into a Python dictionary and returns it.

    This function is an essential building block for any program that interacts with web APIs. By packaging
    the request sending and response processing into a single function, it simplifies the process of fetching
    data from a web API.

    :param url: A string that represents the URL to which the HTTP GET request will be sent. This should be
    the endpoint of the web API that you want to interact with.

    :param parameters: A dictionary of key-value pairs that will be sent as query parameters in the HTTP GET
    request. These can be used to customize the request based on the API's specifications. For example,
    parameters could be used to specify the data that you want to receive from the API.

    :return: A dictionary that represents the JSON content of the HTTP GET request's response. This dictionary
    can then be used in your program to interact with the data that the API returned.

    Note: The function is asynchronous and should be awaited when called. This means that it will not block
    the rest of your program while it waits for the HTTP GET request to be sent and the response to be received.

    Example usage:

    ```
    data = await fetch_data(
        'https://api.example.com/data',
        {'param1': 'value1', 'param2': 'value2'},
        {'Authorization': 'Bearer example_token'}
    )
    ```
    """
    response = get('https://fapi.binance.com/fapi/v1/klines', params=parameters)
    return response.json()
