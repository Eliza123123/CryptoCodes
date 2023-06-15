import asyncio
import locale
import statistics

from datetime import datetime, timedelta
from tabulate import tabulate
from config import Config

from Exchange.Binance import Websocket as Binance_websocket
from Exchange.Binance import fetch_kline

from lib import acme, discord, trade_time
from lib.output_table import OutputTable
from lib.strategy_profit import StrategyProfit
from lib.trade_books import TradeBooks
from lib.trade_counts import TradeCounts

acme.init()
acme.combine_pnz()
conf = Config("config.yaml")
locale.setlocale(locale.LC_MONETARY, 'en_US.UTF-8')

cache = {}  # Keep track of when each symbol was last calculated
last_liq_times = {}  # Dictionary to store the last liquidation times for each symbol
zscore_tables = {}  # Store the Z-Score timeframes

output_confirmation = []  # Output formatting for tables

ws = Binance_websocket()
trade_counts = TradeCounts()

profit = StrategyProfit(dummy_strategy_count=5, real_strategy_count=1)

dummy_trade_books = TradeBooks(5)
dummy_strategy_order_list = ['acme_risk_reward_exit',
                             'acme_exit',
                             'tp_sl_exit',
                             'tp_sl_top_of_minute_exit',
                             'tp_sl_top_of_minute_exhaustion_exit']

real_trade_books = TradeBooks(1)
real_strategy_order_list = ['real_strategy_exit']


######################################################################################################################
# Entry logic from this point on
async def strategy_entries(msg: dict) -> None:

    dummy_entry_strategy_functions = {
        # Each strategy function is associated with its index and trade count
        'entry_strategy_1': (dummy_entry_strategy_1, 0, trade_counts[0]),
        'entry_strategy_2': (dummy_entry_strategy_2, 1, trade_counts[1]),
        'entry_strategy_3': (dummy_entry_strategy_3, 2, trade_counts[2]),
        'entry_strategy_4': (dummy_entry_strategy_4, 3, trade_counts[3]),
        'entry_strategy_5': (dummy_entry_strategy_5, 4, trade_counts[4]),
    }

    symbol = msg["s"]
    quantity = float(msg["q"])
    price = float(msg["p"])

    # Use the first entry strategy function and its corresponding trade book index and count
    entry_function, trade_book_index, trade_count = dummy_entry_strategy_functions['entry_strategy_1']
    result, output_table, zs_table, table, side = await entry_function(symbol, quantity, price, msg,
                                                                       trade_book_index=0)


async def dummy_entry_strategy_1(symbol, quantity, price, msg, trade_book_index):

    liq_value = round(float(quantity * price), 2)
    if liq_value > conf.filters["liquidation"]:
        candle_open, candle_close, scaled_open, entry_price = await get_scaled_price(symbol)
        side = "Buyer Liquidated" if msg["S"] == "SELL" else "Seller Liquidated"
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        output_table = OutputTable(symbol, side, quantity, price, liq_value, timestamp, entry_price)
        output_table.print_table()

        pnz = await get_pnz(output_table, scaled_open, entry_price)
        if pnz:
            zscore_vol = await volume_filter(symbol, conf.zscore_lookback, conf.zscore_timeframes)

            # if volume criteria is met, return True
            if any(z_score > conf.filters["zscore"] for z_score in zscore_vol.values()):
                side = "🟥 🟥 🟥 SELL 🟥 🟥 🟥" if msg["S"] == "BUY" else "🟩 🟩 🟩 BUY 🟩 🟩 🟩"
                output_confirmation.append(f"{side} conditions are met")

            # Prepare zs_table and table
                zs_table = tabulate([['Z-Score'] + [zs for zs in zscore_vol.values()]],
                                    headers=['Timeframe'] + [zs for zs in zscore_vol.keys()],
                                    tablefmt="simple",
                                    floatfmt=".2f")
                table = tabulate(output_table.table, tablefmt="plain")

                trade_data = {
                    "order": len(dummy_trade_books.books[trade_book_index].get(symbol, [])) + 1,
                    "symbol": symbol,
                    "side": "SELL" if msg["S"] == "BUY" else "BUY",
                    "entry": float(price),
                    "ts": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    "close": 0,
                    "perc": 0
                }
                print(trade_data)

                now = datetime.utcnow()
                last_liq_time = last_liq_times.get(symbol, now - timedelta(minutes=2))

                if now - last_liq_time < timedelta(minutes=1):
                    print(f"Skipped liquidation for {symbol}, less than a minute since last one.")
                else:
                    last_liq_times[symbol] = now
                    trade_book = dummy_trade_books.get_book(trade_book_index)
                    if symbol not in trade_book and trade_counts[trade_book_index] < conf.trade_cap:
                        dummy_trade_books.update_book(trade_book_index, symbol, trade_data)
                        trade_counts.counts[trade_book_index] += 1
                    ##################################################
                    if dummy_trade_books.symbol_in_books(symbol):
                        ws.subscribe([(symbol.lower(), "1m")])
                    ##################################################
                    if conf.discord_webhook_enabled:
                        discord.send_to_channel(zs_table, table, side)

                for confirmation in output_confirmation:
                    print(confirmation)

                output_table.clear()
                output_confirmation.clear()
                return True, output_table, zs_table, table, side

    # If no criteria are met, return False
    return False, None, None, None, None


async def dummy_entry_strategy_2():
    pass


async def dummy_entry_strategy_3():
    pass


async def dummy_entry_strategy_4():
    pass


async def dummy_entry_strategy_5():
    pass
# End of entry logic
######################################################################################################################


######################################################################################################################
# Start of exit logic
async def strategy_exits(msg) -> None:

    dummy_exit_strategy_functions = {

        # Dummy strategy 1
        'acme_risk_reward_exit':
            lambda trade_exit, book, symbol_exit:
            acme_risk_reward_exit(trade, book, symbol,
                                  strategy_profit_index=0),

        # Dummy strategy 2
        'acme_exit':
            lambda trade_exit, book, symbol_exit:
            acme_exit(trade, book, symbol,
                      zone_traversals_up=2, zone_traversals_down=1,
                      strategy_profit_index=1),

        # Dummy strategy 3
        'tp_sl_exit':
            lambda trade_exit, book, symbol_exit:
            tp_sl_exit(trade, book, symbol,
                       tp=0.1, sl=-0.1,
                       strategy_profit_index=2),

        # Dummy strategy 4
        'tp_sl_top_of_minute_exit':
            lambda trade_exit, book, symbol_exit:
            tp_sl_top_of_minute_exit(trade, book, symbol,
                                     tp=0.7, sl=-0.5,
                                     strategy_profit_index=3),

        # Dummy strategy 5
        'tp_sl_top_of_minute_exhaustion_exit':
            lambda trade_exit, book, symbol_exit:
            tp_sl_top_of_minute_exhaustion_exit(trade, book, symbol,
                                                tp=0.7, sl=-0.4,
                                                exhaustion=60, strategy_profit_index=4),
    }

    real_exit_strategy_functions = {

        # Real strategy 1
        'real_trade_exit':
            lambda trade_exit, book, symbol_exit:
            real_trade_exit()
    }

    # Code to handle exiting of a variable numbers of dummy strategies
    for i in range(len(dummy_trade_books)):
        trade_book = dummy_trade_books[i]
        exit_strategy_name = dummy_strategy_order_list[i]

        symbol = msg['s']

        scale_factor = acme.get_scale(float(msg['c']))

        # Iterate over each trade in trade book for the symbol
        for trade in trade_book.get(symbol, []):
            # Set the market price here
            trade["close"] = float(msg['c']) / scale_factor

            if trade["side"] == "BUY":
                trade["perc"] = ((trade["close"] - trade["entry"]) / trade["entry"]) * 100
            else:
                trade["perc"] = ((trade["entry"] - trade["close"]) / trade["entry"]) * 100

            # Call the appropriate exit function
            exit_strategy_function = dummy_exit_strategy_functions.get(exit_strategy_name)
            if exit_strategy_function is not None:
                await exit_strategy_function(trade, trade_book, symbol)

        # unsubscribe from websocket if symbol has no other trades
        if not is_symbol_in_any_trade_books(symbol):
            ws.unsubscribe([symbol])

    # Code to handle exiting of a variable numbers of real strategies
    for i in range(len(real_trade_books)):
        trade_book = real_trade_books[i]
        exit_strategy_name = real_strategy_order_list[i]

        symbol = msg['s']

        scale_factor = acme.get_scale(float(msg['c']))

        # Iterate over each trade in trade book for the symbol
        for trade in trade_book.get(symbol, []):
            # Set the market price here
            trade["close"] = float(msg['c']) / scale_factor

            if trade["side"] == "BUY":
                trade["perc"] = ((trade["close"] - trade["entry"]) / trade["entry"]) * 100
            else:
                trade["perc"] = ((trade["entry"] - trade["close"]) / trade["entry"]) * 100

            # Call the appropriate exit function
            exit_strategy_function = real_exit_strategy_functions.get(exit_strategy_name)
            if exit_strategy_function is not None:
                await exit_strategy_function(trade, trade_book, symbol)

        # unsubscribe from websocket if symbol has no other trades
        if not is_symbol_in_any_trade_books(symbol):
            ws.unsubscribe([symbol])


async def acme_risk_reward_exit(trade_exit: dict, book_exit: dict, symbol_exit: str,
                                strategy_profit_index: int):

    entry_price = trade_exit['entry']
    trade_type = trade_exit['side']  # 'buy' or 'sell'
    entry_zone_index = None
    min_distance = float('inf')

    # Calculate the entry_zone_index
    for i, tup in enumerate(acme.target_lg_list):
        mid_point = (tup[0] + tup[1]) / 2
        distance = abs(mid_point - entry_price)
        if distance < min_distance:
            min_distance = distance
            entry_zone_index = i

    if entry_zone_index is not None:
        if trade_type == 'BUY':
            upper_zone_index = min(entry_zone_index + 1, len(acme.target_lg_list) - 1)
            lower_zone_index = max(entry_zone_index - 1, 0)

            upper_zone = acme.target_lg_list[upper_zone_index]
            lower_zone = acme.target_lg_list[lower_zone_index]

            room_up = abs(upper_zone[1] - entry_price)
            room_down = abs(entry_price - lower_zone[0])

            risk_reward = room_up / room_down
            # print("Initial Risk Reward: ", risk_reward)

            while risk_reward < 1:
                upper_zone_index += 1
                # prevent index out of range error
                if upper_zone_index >= len(acme.target_lg_list):
                    # print("Reached end of zone list, can't move zone up further.")
                    break
                upper_zone = acme.target_lg_list[upper_zone_index]
                room_up = abs(upper_zone[1] - entry_price)
                risk_reward = room_up / room_down
            #     print("Adjusted Risk Reward: ", risk_reward)
            #
            # print("Final Take Profit: ", upper_zone[1])
            # print("Final Stop Loss: ", lower_zone[0])
            # print("Final Risk Reward: ", risk_reward)

            if (trade_exit["close"] >= upper_zone[1]) or (trade_exit["close"] <= lower_zone[0]):
                profit.dummy_strategy_profits[strategy_profit_index] += trade_exit["perc"]
                book_exit[symbol_exit].remove(trade_exit)
                discord.send_exit_message('Strategy 1: acme_risk_reward_exit', symbol_exit, trade_exit['perc'],
                                          profit.dummy_strategy_profits[strategy_profit_index])
                # After the exit trade is confirmed, reduce the trade count by 1.
                if len(trade_counts.counts) > 0:
                    trade_counts.counts[0] -= 1  # Decrement the count for the first strategy
                    # Ensure the count doesn't go below 0
                    if trade_counts.counts[0] < 0:
                        trade_counts.counts[0] = 0

        elif trade_type == 'SELL':
            upper_zone_index = min(entry_zone_index + 1, len(acme.target_lg_list) - 1)
            lower_zone_index = max(entry_zone_index - 1, 0)

            upper_zone = acme.target_lg_list[upper_zone_index]
            lower_zone = acme.target_lg_list[lower_zone_index]

            room_up = abs(upper_zone[1] - entry_price)
            room_down = abs(entry_price - lower_zone[0])

            risk_reward = room_down / room_up
            # print("Initial Risk Reward: ", risk_reward)

            while risk_reward < 1:
                lower_zone_index -= 1
                # prevent index out of range error
                if lower_zone_index < 0:
                    # print("Reached start of zone list, can't move zone down further.")
                    break
                lower_zone = acme.target_lg_list[lower_zone_index]
                room_down = abs(entry_price - lower_zone[0])
                risk_reward = room_down / room_up
            #     print("Adjusted Risk Reward: ", risk_reward)
            #
            # print("Final Stop Loss: ", upper_zone[1])
            # print("Final Take Profit: ", lower_zone[0])
            # print("Final Risk Reward: ", risk_reward)

            if (trade_exit["close"] >= upper_zone[1]) or (trade_exit["close"] <= lower_zone[0]):
                profit.dummy_strategy_profits[strategy_profit_index] += trade_exit["perc"]
                book_exit[symbol_exit].remove(trade_exit)
                discord.send_exit_message('Strategy 1: acme_risk_reward_exit', symbol_exit, trade_exit['perc'],
                                          profit.dummy_strategy_profits[strategy_profit_index])
                # After the exit trade is confirmed, reduce the trade count by 1.
                if len(trade_counts.counts) > 0:
                    trade_counts.counts[0] -= 1  # Decrement the count for the first strategy
                    # Ensure the count doesn't go below 0
                    if trade_counts.counts[0] < 0:
                        trade_counts.counts[0] = 0


async def acme_exit(trade_exit: dict, book_exit: dict, symbol_exit: str,
                    zone_traversals_up: int, zone_traversals_down: int,
                    strategy_profit_index: int):

    entry_price = trade_exit['entry']
    entry_zone_index = None

    # Iterate over the combined zones list
    for i, tup in enumerate(acme.target_lg_list):
        if tup[0] <= entry_price <= tup[1]:
            entry_zone_index = i
            break

    if entry_zone_index is None:
        # Entry price is not within any tuple in the list.
        # Calculate the mid-points of each tuple.
        mid_points = [(tup[0] + tup[1]) / 2 for tup in acme.target_lg_list]

        # Find the index of the tuple with the closest mid-point to the entry price.
        entry_zone_index = min(range(len(mid_points)), key=lambda j: abs(mid_points[j] - entry_price))

    # Calculate upper and lower zones
    upper_zone_index = min(entry_zone_index + zone_traversals_up, len(acme.target_lg_list) - 1)
    lower_zone_index = max(entry_zone_index - zone_traversals_down, 0)

    upper_zone = acme.target_lg_list[upper_zone_index]
    lower_zone = acme.target_lg_list[lower_zone_index]

    if (trade_exit["close"] >= upper_zone[1]) or (trade_exit["close"] <= lower_zone[0]):
        profit.dummy_strategy_profits[strategy_profit_index] += trade_exit["perc"]
        book_exit[symbol_exit].remove(trade_exit)
        discord.send_exit_message("Strategy 2: acme_exit", symbol_exit, trade_exit['perc'],
                                  profit.dummy_strategy_profits[strategy_profit_index])
        # After the exit trade is confirmed, reduce the trade count by 1.
        if len(trade_counts.counts) > 0:
            trade_counts.counts[1] -= 1
            # Ensure the count doesn't go below 0
            if trade_counts.counts[1] < 0:
                trade_counts.counts[1] = 0


async def tp_sl_exit(trade_exit: dict, book_exit: dict, symbol_exit: str,
                     tp: float, sl: float,
                     strategy_profit_index: int):

    if (trade_exit["perc"] <= sl) or (trade_exit["perc"] >= tp):
        profit.dummy_strategy_profits[strategy_profit_index] += trade_exit["perc"]
        book_exit[symbol_exit].remove(trade_exit)
        discord.send_exit_message("Strategy 3: tp_sl_exit", symbol_exit, trade_exit['perc'],
                                  profit.dummy_strategy_profits[strategy_profit_index])
        # After the exit trade is confirmed, reduce the trade count by 1.
        if len(trade_counts.counts) > 0:
            trade_counts.counts[2] -= 1
            # Ensure the count doesn't go below 0
            if trade_counts.counts[2] < 0:
                trade_counts.counts[2] = 0


async def tp_sl_top_of_minute_exit(trade_exit: dict, book_exit: dict, symbol_exit: str,
                                   tp: float, sl: float,
                                   strategy_profit_index: int):

    if (trade_exit["perc"] <= sl) or (trade_exit["perc"] >= tp and trade_time.is_top_of_minute()):
        profit.dummy_strategy_profits[strategy_profit_index] += trade_exit["perc"]
        book_exit[symbol_exit].remove(trade_exit)
        discord.send_exit_message("Strategy 4: tp_sl_top_of_minute_exit", symbol_exit, trade_exit['perc'],
                                  profit.dummy_strategy_profits[strategy_profit_index])
        # After the exit trade is confirmed, reduce the trade count by 1.
        if len(trade_counts.counts) > 0:
            trade_counts.counts[3] -= 1
            # Ensure the count doesn't go below 0
            if trade_counts.counts[3] < 0:
                trade_counts.counts[3] = 0


async def tp_sl_top_of_minute_exhaustion_exit(trade_exit: dict, book_exit: dict, symbol_exit: str,
                                              tp: float, sl: float,
                                              exhaustion: int, strategy_profit_index: int):

    time_of_trade = datetime.strptime(trade_exit["ts"], '%Y-%m-%d %H:%M:%S')
    trade_is_old = datetime.utcnow() - time_of_trade > timedelta(minutes=exhaustion)

    if (trade_exit["perc"] <= sl) or (trade_exit["perc"] >= tp and trade_time.is_top_of_minute()) or trade_is_old:
        profit.dummy_strategy_profits[strategy_profit_index] += trade_exit["perc"]
        book_exit[symbol_exit].remove(trade_exit)
        discord.send_exit_message("Strategy 5: tp_sl_top_of_minute_exhaustion_exit", symbol_exit, trade_exit['perc'],
                                  profit.dummy_strategy_profits[strategy_profit_index])
        # After the exit trade is confirmed, reduce the trade count by 1.
        if len(trade_counts.counts) > 0:
            trade_counts.counts[4] -= 1
            # Ensure the count doesn't go below 0
            if trade_counts.counts[4] < 0:
                trade_counts.counts[4] = 0


async def real_trade_exit():

    # worst_strategy = profit.worst_dummy_profit()
    pass

    # End of exit code
######################################################################################################################


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


async def get_pnz(output_table: OutputTable, scaled_open: float, entry_price: float) -> bool:
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
            output_table.append([f"ACME Small {emoji_map.get(1, '')}", tup])
    for key in range(3, 7):
        for tup in acme.pnz_lg[key]:
            if acme.price_within([tup], entry_price):
                output_table.append([f"ACME Big {key} {emoji_map.get(key, '')} ", tup])
                return True
    return flag_pnz_sm


def is_symbol_in_any_trade_books(symbol):
    # Iterate over all trade books
    for trade_book in [dummy_trade_books, real_trade_books]:  # list all your trade books here
        # If symbol is in this trade book, return True immediately
        if symbol in trade_book:
            return True
    # If symbol is not in any trade books, return False
    return False
