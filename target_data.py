import json

json_data_source = 'stored-data.json'
stablecoins = ('USDT', 'USDC', 'BUSD', 'TUSD', 'GUSD', 'USDD', 'DAI', 'USDP')

with open(json_data_source, encoding='utf-8') as data:
    load_json = json.load(data)

target_data = {}
for item in load_json['data']:
    if item['symbol'] not in stablecoins:
        symbol = item['symbol']
        price = item['quote']['USD']['price']
        market_cap = item['quote']['USD']['market_cap']
        target_data[symbol] = [price, market_cap]
