import asyncio
import locale
import statistics
from datetime import datetime, timedelta

from Exchange.Binance import Websocket as Binance_websocket
from Exchange.Binance import fetch_kline
from config import Config
from lib import acme, discord, trade_exits
from lib.table import EntryTable, ZScoreTable
from lib.trade_books import TradeBooks

acme.init()
acme.combine_pnz()

conf = Config("config.yaml")

locale.setlocale(locale.LC_MONETARY, 'en_US.UTF-8')

liq_cache = {}  # Dictionary to store the last liquidation times for each symbol
zs_cache = {}  # Cache for the Z-Score timestamp and timeframes

output_confirmation = []  # Output formatting for tables

ws = Binance_websocket()

# init books for each strategy
books = TradeBooks("entry_strategy_1", "entry_strategy_2")


async def strategy_exits(msg) -> None:
    symbol = msg['s']

    for strategy, d in books.as_dict():
        trade = d.get(symbol, None)
        if trade is None:
            continue

        scale_factor = acme.get_scale(float(msg['c']))

        trade['close'] = float(msg['c']) / scale_factor
        if trade["side"] == "BUY":
            trade["perc"] = ((trade["close"] - trade["entry"]) / trade["entry"]) * 100
        else:
            trade["perc"] = ((trade["entry"] - trade["close"]) / trade["entry"]) * 100

        # Add all strategies here
        if strategy == "entry_strategy_1":
            if trade_exits.on_acme(trade['close'], zone_traversals_up=2, zone_traversals_down=1):
                books.update_stats(strategy, trade["perc"])

                table = books.display_table(strategy, trade["side"], trade["perc"])
                print(table)

                if conf.discord_exit_webhook_enabled:
                    discord.send_exit(table)

                books.remove(strategy, symbol)
                break

        elif strategy == "entry_strategy_2":
            if trade_exits.on_tp_sl(trade["perc"], tp=0.1, sl=0.1):
                books.update_stats(strategy, trade["perc"])

                table = books.display_table(strategy, trade["side"], trade["perc"])
                print(table)

                if conf.discord_exit_webhook_enabled:
                    discord.send_exit(table)

                books.remove(strategy, symbol)
                break
        else:
            continue
        break

    if not books.symbol_in_books(symbol):
        ws.unsubscribe([symbol.lower()])


async def strategy_entries(msg: dict) -> None:
    side = msg["S"]
    symbol = msg["s"]
    quantity = float(msg["q"])
    price = float(msg["p"])
    liq_value = round(float(quantity * price), 2)
    now = datetime.utcnow()

    for fn in [entry_strategy_1, entry_strategy_2]:
        # process liquidation if value > than threshold and liquidation > than one minute
        if liq_value > conf[fn.__qualname__]["liquidation"] and (now - liq_cache.get(symbol, now - timedelta(minutes=2)) > timedelta(minutes=1)):
            candle_open, candle_close, scaled_open, entry_price = await get_scaled_price(symbol)

            liq_cache[symbol] = now

            output_table = EntryTable(symbol, side, quantity, price, liq_value, entry_price)

            if await get_pnz(output_table, scaled_open, entry_price):
                zscores = await volume_filter(symbol, conf.zscore_period, conf.zscore_timeframes)
                # process strategies
                if fn(symbol, side, quantity, price, zscores):
                    # add new trade into book
                    books.update(fn.__qualname__, symbol, {
                        "symbol": symbol,
                        "side": "SELL" if side == "BUY" else "BUY",
                        "entry": entry_price,
                        "ts": now.strftime('%Y-%m-%d %H:%M:%S'),
                        "close": 0.,
                        "perc": 0.
                    })

                    ws.subscribe([(symbol.lower(), "1m")])

                    zs_table = ZScoreTable(zscores)

                    if conf.discord_entry_webhook_enabled:
                        discord.send_entry(zs_table, output_table, side)

                    print(f"{zs_table}\n\n{output_table}\n\n{'SELL' if side == 'BUY' else 'BUY'}\n")
                    print(f"DEBUG: {books[fn.__qualname__][symbol]}\n")

                else:
                    print(f"{fn.__qualname__}: {symbol} not processed")

            output_table.clear()


def entry_strategy_1(symbol: str, side: str, quantity: float, price: float, zscore) -> bool:
    return any(z_score > conf["entry_strategy_1"]["zscore"] for z_score in zscore.values()) and not books.symbol_in_book("entry_strategy_1",
                                                                                                                         symbol) and not len(
        books["entry_strategy_1"]) >= conf.trade_cap


def entry_strategy_2(symbol, side, quantity, price, zscore) -> bool:
    return any(z_score > conf["entry_strategy_2"]["zscore"] for z_score in zscore.values()) and not books.symbol_in_book("entry_strategy_2",
                                                                                                                         symbol) and not len(
        books["entry_strategy_2"]) >= conf.trade_cap


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

    if symbol in zs_cache:
        # If it was calculated less than 5 minutes ago, print the stored Z-score table and return
        if (datetime.now() - zs_cache[symbol]['dt']).seconds < 5 * 60:
            return zs_cache[symbol]['zs']  # return the previously stored Z-scores as a dict
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
    zs_cache[symbol] = {
        'zs': zscores,
        'dt': datetime.now()
    }
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


async def get_pnz(output_table: EntryTable, scaled_open: float, entry_price: float) -> bool:
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
        if tup not in seen_tups and acme.through_pnz_small([tup], scaled_open, entry_price):
            seen_tups.add(tup)
            flag_pnz_sm = True
            output_table.append(f"ACME Small {emoji_map.get(1, '')}", tup)
    for key in range(3, 7):
        for tup in acme.pnz_lg[key]:
            if acme.price_within([tup], entry_price):
                output_table.append(f"ACME Big {key} {emoji_map.get(key, '')} ", tup)
                return True
    return flag_pnz_sm
