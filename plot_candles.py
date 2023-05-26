from trading_tool_functions import *
import finplot as fplt
import pandas as pd

# Global variables
no_candles = 50
scale_max = 100

candlestick_data = pseudo_candles(no_candles, max_price=scale_max)

ohlc_data = [(i+1, d[0], d[1], d[2], d[3])
             for i, d in enumerate(candlestick_data)]

df = pd.DataFrame(ohlc_data, columns=['Index',
                                      'Open',
                                      'Close',
                                      'High',
                                      'Low']
                  )

# for element in dir(finplot):
#     print(element)

print(df)

# Plot the candlestick chart
fplt.candlestick_ochl(df[['Index', 'Open', 'Close', 'High', 'Low']])

for prime in prime_sequence(scale_max):
    fplt.add_line((0, prime), (no_candles, prime), color='blue')

for prime in prime_indexed_prime_sequence(scale_max):
    fplt.add_line((0, prime), (no_candles, prime), color='red')
fplt.show()
