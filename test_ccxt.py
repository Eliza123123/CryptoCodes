import ccxt

exchange = ccxt.binance()
print(dir(exchange))

markets = exchange.load_markets()

btc_usdt_market = markets['BTC/USDT']

print(btc_usdt_market)
