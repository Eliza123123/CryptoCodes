import requests
from trading_tool_functions import store_data
from datetime import datetime


url = 'https://fapi.binance.com/fapi/v1/klines'
api_key = 'd4g8tK4spj6opzAlAwJCqS81449pRDqtNEQZE24lB2xYfWvT089GuZS6LfmEGG7U'
secret_key = 'bJLJVdKvAERrtBEJ19SVCdR18kXzuVeyt4fD27lGnkJPbVigrKq8sVCNmlfHLbPB'

headers = {
    'X-MBX-APIKEY': api_key
}

filename = 'btc-kline.json'

parameters = {
    'symbol': 'BTCUSDT',
    'interval': '1m',
    'limit': 1,
}

updates = 0

while True:
    if datetime.now().second == updates:
        response = requests.get(url, headers=headers, params=parameters, verify=False)
        print(response.json())
        store_data(url=url, parameters=parameters, headers=headers, filename=filename)
