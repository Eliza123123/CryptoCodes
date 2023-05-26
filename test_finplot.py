from trading_tool_functions import *
import finplot as fplt
import yfinance

no_candles = 20
df = yfinance.download('AAPL')
fplt.candlestick_ochl(df[['Open', 'Close', 'High', 'Low']])
for prime in prime_sequence(1000):
    fplt.add_line((0, prime), (no_candles, prime), color='blue')
fplt.show()
