import asyncio
import locale
import statistics
from datetime import datetime, timedelta

from tabulate import tabulate

from Exchange.Binance import Websocket as Binance_websocket
from Exchange.Binance import fetch_kline
from config import Config
from lib import acme, discord, exit_strategies

acme.init()
conf = Config("config.yaml")
locale.setlocale(locale.LC_MONETARY, 'en_US.UTF-8')
ws = Binance_websocket()

cache = {}  # Keep track of when each symbol was last calculated
last_liq_times = {}  # Dictionary to store the last liquidation times for each symbol
trade_book = {}  # Keep track of open trades
zscore_tables = {}  # Store the Z-Score timeframes

output_confirmation = []  # Output formatting for tables
output_table = []  # Output formatting for tables

trade_count = 0  # Count of total trades


async def process_trade_book(msg) -> None:
    global trade_count

    symbol = msg['s']

    scale_factor = acme.get_scale(float(msg['c']))

    # Iterate over each trade in trade book for the symbol
    for trade in trade_book.get(symbol, []):
        trade["close"] = float(msg['c']) / scale_factor

        if trade["side"] == "BUY":
            trade["perc"] = ((trade["close"] - trade["entry"]) / trade["entry"]) * 100
        else:
            trade["perc"] = ((trade["entry"] - trade["close"]) / trade["entry"]) * 100

        # Exit function goes here
        await exit_strategies.tp_sl_top_of_minute_exhaustion_exit(
            trade=trade, book=trade_book, symbol=symbol, tp=0.7, sl=-0.5, exhaustion=60)

        trade_count -= 1

    # unsubscribe from websocket if symbol has no other trades
    if symbol not in trade_book:
        ws.unsubscribe([symbol])


async def process_message(msg: dict) -> None:
    global trade_count
    symbol = msg["s"]
    quantity = float(msg["q"])
    price = float(msg["p"])
    liq_value = round(float(quantity * price), 2)

    if symbol in conf.excluded_symbols:
        print(f"Liquidation {symbol} in excluded list.")

    # If liquidation is above threshold
    elif liq_value > conf.filters["liquidation"]:

        candle_open, candle_close, scaled_open, scaled_close = await get_scaled_price(symbol)

        output_table.append(["Symbol", symbol])
        output_table.append(["Side", "Buyer Liquidated" if msg["S"] == "SELL" else "Seller Liquidated"])
        output_table.append(["Quantity", msg["q"]])
        output_table.append(["Price", msg["p"]])
        output_table.append(["Liquidation Value", locale.currency(liq_value, grouping=True)])
        output_table.append(["Timestamp", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')])
        output_table.append(["Scaled Price", scaled_close])

        # If in acme zone
        pnz = await get_pnz(scaled_open, scaled_close)
        if pnz:
            zscore_vol = await volume_filter(symbol, conf.zscore_lookback, conf.zscore_timeframes)
            print('-' * 65)
            # 1. Print volume analysis
            zs_table = tabulate([['Z-Score'] + [zs for zs in zscore_vol.values()]],
                                headers=['Timeframe'] + [zs for zs in zscore_vol.keys()],
                                tablefmt="simple",
                                floatfmt=".2f")
            print(zs_table)
            print('-' * 65)
            # 2. Print symbol info
            table = tabulate(output_table, tablefmt="plain")
            print(table)
            print('-' * 65)

            # If volume criteria hit
            if any(z_score > conf.filters["zscore"] for z_score in zscore_vol.values()):
                side = "🟥 🟥 🟥 SELL 🟥 🟥 🟥" if msg["S"] == "BUY" else "🟩 🟩 🟩 BUY 🟩 🟩 🟩"
                output_confirmation.append(f"{side} conditions are met")

                # Check if total trades is 10 or more
                if trade_count >= 10:
                    print("Max trades reached, not adding new trade.")
                    return

                # If no trade exists for the symbol, open trade and subscribe to kline stream for updates
                trade_data = {
                    "order": len(trade_book.get(symbol, [])) + 1,
                    "symbol": symbol,
                    "side": "SELL" if msg["S"] == "BUY" else "BUY",
                    "entry": float(scaled_close),
                    "ts": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    "close": 0,
                    "perc": 0
                }

                # Check if it's been more than a minute since the last liquidation for this symbol
                now = datetime.utcnow()
                # Default to more than a minute ago
                last_liq_time = last_liq_times.get(symbol, now - timedelta(minutes=2))

                if now - last_liq_time < timedelta(minutes=1):
                    print(f"Skipped liquidation for {symbol}, less than a minute since last one.")
                else:
                    last_liq_times[symbol] = now

                    if symbol not in trade_book:
                        trade_book[symbol] = [trade_data]
                        ws.subscribe([(symbol.lower(), "1m")])
                    else:
                        trade_book[symbol].append(trade_data)
                    trade_count += 1

                    if conf.discord_webhook_enabled:
                        discord.send_to_channel(zs_table, table, side)
        else:
            output_confirmation.append(f"{symbol} Liquidation: ACME not detected.")
        # 3. Print confirmation messages
        for confirmation in output_confirmation:
            print(confirmation)
        # Reset tables
        output_table.clear()
        output_confirmation.clear()


async def volume_filter(symbol: str, n: int, timeframes: list) -> dict:
    """
    This function calculates the Z-scores of trading volumes for multiple timeframes of a given symbol
    and displays them in a tabulated format.
    It first checks if the Z-scores for the symbol were calculated within the last 5 minutes. If they were,
    it prints the stored Z-scores and returns them. If not, it sends requests to fetch the latest trading data
    for each timeframe and calculates the Z-scores.
    The Z-scores are calculated as follows:
    Z-score = (current_volume - mean_volume) / standard_deviation_volume
    Once calculated, the Z-scores are printed in a tabulated format and stored for later use.
    This function leverages asyncio.gather() to send multiple requests concurrently, improving the speed
    and efficiency of the function.
    :param symbol: The trading symbol to fetch data for.
    :param n: The number of latest data points to fetch for each timeframe.
    :param timeframes: Variable length argument, each specifying a timeframe to fetch data for.
    :return: A dictionary where each key is a timeframe and its corresponding value is the Z-score
             for that timeframe.
    """
    last_time = cache.get(symbol)
    if last_time is not None:
        # If it was calculated less than 5 minutes ago, print the stored Z-score table and return
        if (datetime.now() - last_time).seconds < 5 * 60:
            return zscore_tables[symbol]  # return the previously stored Z-scores as a dict
    # Create a list of tasks to run concurrently
    tasks = []
    for timeframe in timeframes:
        parameters = {
            'symbol': symbol,
            'interval': timeframe,
            'limit': n,
        }
        tasks.append(fetch_kline(parameters))
    # Gather tasks and run them concurrently
    responses = await asyncio.gather(*tasks)
    # Prepare a dictionary to store Z-scores for each timeframe
    zscores = {}
    for response, timeframe in zip(responses, timeframes):
        volumes = [float(bar[5]) for bar in response]
        mean_volume = statistics.mean(volumes)
        std_volume = statistics.stdev(volumes)
        current_volume = volumes[-2]  # last complete candle
        z_score = (current_volume - mean_volume) / std_volume
        # Store the Z-score for this timeframe in the dictionary
        zscores[timeframe] = z_score
    zscore_tables[symbol] = zscores  # store the Z-scores
    # Update the time of the last calculation for this symbol
    cache[symbol] = datetime.now()
    return zscores  # return the Z-scores


async def get_scaled_price(symbol: str) -> list:
    parameters = {
        'symbol': symbol,
        'interval': '1m',
        'limit': 1,
    }
    data = await fetch_kline(parameters)
    if not data:
        return []
    candle_open = float(data[0][1])
    candle_close = float(data[0][4])
    scale_factor = acme.get_scale(min(candle_open, candle_close))
    return [candle_open, candle_close, candle_open / scale_factor, candle_close / scale_factor]


async def get_pnz(scaled_open: float, scaled_close: float) -> bool:
    emoji_map = {
        1: "⬜",
        3: "🟨",
        4: "🟦",
        5: "🟩",
        6: "🟪",
    }
    flag_pnz_sm = False
    seen_tups = set()
    for tup in acme.pnz_sm[1]:
        if tup not in seen_tups and acme.through_pnz_small([tup], scaled_open, scaled_close):
            seen_tups.add(tup)
            flag_pnz_sm = True
            output_table.append([f"ACME Small {emoji_map.get(1, '')}", tup])
    for key in range(3, 6):
        for tup in acme.pnz_lg[key]:
            if acme.price_within([tup], scaled_close):
                output_table.append([f"ACME Big {key} {emoji_map.get(key, '')} ", tup])
                return True
    return flag_pnz_sm
