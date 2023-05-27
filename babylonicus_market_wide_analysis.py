import time
from trading_tool_functions import *
from babylonicus_deductions import pnz_bigs

json_data_source = 'stored-data.json'
stablecoins = ('USDT', 'USDC', 'BUSD', 'TUSD', 'GUSD', 'USDD', 'DAI', 'USDP')


def read_target_data():
    with open(json_data_source, encoding='utf-8') as data:
        load_json = json.load(data)

    target_data = {}
    for item in load_json['data']:
        if item['symbol'] not in stablecoins:
            symbol = item['symbol']
            price = item['quote']['USD']['price']
            market_cap = item['quote']['USD']['market_cap']
            target_data[symbol] = [price, market_cap]

    return target_data


def process_data():
    # Read target_data
    target_data = read_target_data()
    market_scores = []
    total_sum_closest_acme_3_6 = 0.0

    for symbol, data in target_data.items():
        price = data[0]
        market_cap = data[1]
        scaled_price = price / get_scale(price)
        target_data[symbol] = [scaled_price, market_cap]

        sum_closest_acme_3_6 = 0.0

        for i in range(7, 0, -1):
            differences = [abs(scaled_price - element) for element in pnz_bigs[i]]
            closest = min(differences)
            if 3 <= i <= 6:
                sum_closest_acme_3_6 += closest

        total_sum_closest_acme_3_6 += sum_closest_acme_3_6

    print(total_sum_closest_acme_3_6)


while True:
    process_data()
    # Wait for 5 minutes
    time.sleep(300)
