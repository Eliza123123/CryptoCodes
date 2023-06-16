import asyncio
import json

from requests import get
from websocket import WebSocket, WebSocketException


class Websocket:
    """
    Exchange websocket implementation for Binance.
    """

    websocket: WebSocket
    queue: asyncio.Queue
    queue_subscribe: asyncio.Queue

    def __init__(self) -> None:
        self.wss = "wss://fstream.binance.com/ws"
        self.queue_liquidation = asyncio.Queue()
        self.queue_kline = asyncio.Queue()
        self.queue_subscribe = asyncio.Queue()
        self.stream_subscriptions = {}

    def __del__(self):
        self.websocket.close()

    def subscribe(self, symbols: list) -> None:
        """
        Subscribe to the kline streams for the given symbols and timeframes

        :param symbols: [("btcusdt", "1m"),...]
        :type symbols: List of tuples containing the symbol and timeframe as strings
        :return:
        :rtype:
        """

        subs = []
        for symbol, timeframe in symbols:
            fmt = f"{symbol}@kline_{timeframe}"
            subs.append(fmt)
            self.stream_subscriptions[symbol] = fmt

        self.queue_subscribe.put_nowait({
            "method": "SUBSCRIBE",
            "params": subs,
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
            "id": 2
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

        loop = asyncio.get_event_loop()
        while True:
            try:
                message = await loop.run_in_executor(None, self.websocket.recv)
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
            except WebSocketException as e:
                print(f"Connection closed unexpectedly: {e}. Retrying connection...")
                await asyncio.sleep(1)
                self.websocket = WebSocket()
                self.websocket.connect(self.wss)
                self.subscribe_liquidation()
                self.subscribe_klines()
                continue

    async def _stream_subscription(self):
        while True:
            message = await self.queue_subscribe.get()
            self.websocket.send(json.dumps(message))

    async def on_liquidation(self, fn):
        while True:
            while not self.queue_liquidation.empty():
                message = await self.queue_liquidation.get()
                await fn(message)
            await asyncio.sleep(0.01)  # Small delay to prevent 100% CPU usage

    async def on_kline(self, fn):
        while True:
            while not self.queue_kline.empty():
                message = await self.queue_kline.get()
                await fn(message)
            await asyncio.sleep(0.01)  # Small delay to prevent 100% CPU usage

    async def stream(self):
        self.websocket = WebSocket()
        self.websocket.connect(self.wss)
        print("Connected to websocket")
        await asyncio.gather(self._websocket_stream(), self._stream_subscription())


async def fetch_kline(parameters: dict) -> dict:
    """
    Fetch data from a specified URL, using provided parameters and headers. This function sends an
    asynchronous HTTP GET request to the URL, using the parameters and headers to customize the request.
    Upon receiving the response, it converts the JSON response content into a Python dictionary and returns it.

    This function is an essential building block for any program that interacts with web APIs. By packaging
    the request sending and response processing into a single function, it simplifies the process of fetching
    data from a web API.

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
