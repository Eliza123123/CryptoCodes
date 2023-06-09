import asyncio
import locale
import statistics
from datetime import datetime, timedelta

from tabulate import tabulate

from Exchange.Binance import Websocket as Binance_websocket
from Exchange.Binance import fetch_kline
from config import Config
from lib import acme, discord, trade_time

acme.init()
acme.combine_pnz()
conf = Config("config.yaml")
locale.setlocale(locale.LC_MONETARY, 'en_US.UTF-8')
ws = Binance_websocket()

cache = {}  # Keep track of when each symbol was last calculated
last_liq_times = {}  # Dictionary to store the last liquidation times for each symbol
zscore_tables = {}  # Store the Z-Score timeframes

output_confirmation = []  # Output formatting for tables
output_table = []  # Output formatting for tables

trade_counts = [0 for _ in range(6)]
trade_books = [{} for _ in range(6)]

strategy_order_list = ['acme_risk_reward_exit',
                       'acme_exit', 'tp_sl_exit',
                       'tp_sl_top_of_minute_exit',
                       'tp_sl_top_of_minute_exhaustion_exit',
                       'real_strategy_exit']

dummy_strategy_1_profit = 0
dummy_strategy_2_profit = 0
dummy_strategy_3_profit = 0
dummy_strategy_4_profit = 0
dummy_strategy_5_profit = 0
real_strategy_profit = 0

######################################################################################################################
# Entry logic from this point on
# TODO: allow code to process different entry criteria in a similar fashion to how exits have been performed


async def process_message(msg: dict) -> None:
    global trade_counts
    symbol = msg["s"]
    quantity = float(msg["q"])
    price = float(msg["p"])
    liq_value = round(float(quantity * price), 2)

    # if symbol in conf.excluded_symbols:
    #     print(f"Liquidation {symbol} in excluded list.")
    #
    # if symbol[-4:] in conf.excluded_quote:
    #     print(f"{symbol} not processed. No processing on BUSD symbols.")

    # If liquidation is above threshold
    if liq_value > conf.filters["liquidation"]:
        # print(f"Processing liquidation for {symbol}...")

        candle_open, candle_close, scaled_open, entry_price = await get_scaled_price(symbol)

        output_table.append(["Symbol", symbol])
        output_table.append(["Side", "Buyer Liquidated" if msg["S"] == "SELL" else "Seller Liquidated"])
        output_table.append(["Quantity", msg["q"]])
        output_table.append(["Price", msg["p"]])
        output_table.append(["Liquidation Value", locale.currency(liq_value, grouping=True)])
        output_table.append(["Timestamp", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')])
        output_table.append(["Scaled Price", entry_price])

        # If in acme zone
        pnz = await get_pnz(scaled_open, entry_price)
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

                trade_data = {
                    "order": sum(len(book.get(symbol, [])) for book in trade_books) + 1,
                    "symbol": symbol,
                    "side": "SELL" if msg["S"] == "BUY" else "BUY",
                    "entry": float(entry_price),
                    "ts": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    "close": 0,
                    "perc": 0
                }
                now = datetime.utcnow()
                last_liq_time = last_liq_times.get(symbol, now - timedelta(minutes=2))

                if now - last_liq_time < timedelta(minutes=1):
                    print(f"Skipped liquidation for {symbol}, less than a minute since last one.")
                else:
                    last_liq_times[symbol] = now

                    for i in range(len(trade_books)):
                        trade_book = trade_books[i]
                        trade_count = trade_counts[i]
                        if symbol not in trade_book and trade_count < conf.trade_cap:
                            trade_book[symbol] = [trade_data]
                            trade_counts[i] += 1
                        else:
                            if trade_data not in trade_book[symbol] and trade_count < conf.trade_cap:
                                trade_book[symbol].append(trade_data)
                                trade_counts[i] += 1

                    if any(symbol in trade_book for trade_book in trade_books):
                        ws.subscribe([(symbol.lower(), "1m")])

                    if conf.discord_webhook_enabled:
                        discord.send_to_channel(zs_table, table, side)

        # else:
        #     output_confirmation.append(f"{symbol} Liquidation: ACME not detected.")
        # 3. Print confirmation messages
        for confirmation in output_confirmation:
            print(confirmation)
        # Reset tables
        output_table.clear()
        output_confirmation.clear()

        # End of entry logic
######################################################################################################################

######################################################################################################################
        # Start of exit logic


async def process_trade_book(msg) -> None:
    global trade_books

    best_performing_strat = get_best_strategy()
    worst_performing_strat = get_worst_strategy()

    if trade_time.fifteen_second_intervals():
        print('worst: ', worst_performing_strat, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
        print('best: ', best_performing_strat, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))

    exit_strategy_functions = {
        'acme_risk_reward_exit':
            lambda trade_exit, book, symbol_exit:
            acme_risk_reward_exit(trade, book, symbol),
        'acme_exit':
            lambda trade_exit, book, symbol_exit:
            acme_exit(trade, book, symbol, zone_traversals_up=2, zone_traversals_down=1),
        'tp_sl_exit':
            lambda trade_exit, book, symbol_exit:
            tp_sl_exit(trade, book, symbol, tp=0.1, sl=-0.1),
        'tp_sl_top_of_minute_exit':
            lambda trade_exit, book, symbol_exit:
            tp_sl_top_of_minute_exit(trade, book, symbol, tp=0.7, sl=-0.5),
        'tp_sl_top_of_minute_exhaustion_exit':
            lambda trade_exit, book, symbol_exit:
            tp_sl_top_of_minute_exhaustion_exit(trade, book, symbol, tp=0.7, sl=-0.5, exhaustion=60),
        'real_trade_exit':
            lambda trade_exit, book, symbol_exit:
            real_trade_exit()
    }

    for i in range(len(trade_books)):
        trade_book = trade_books[i]
        exit_strategy_name = strategy_order_list[i]

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
            exit_strategy_function = exit_strategy_functions.get(exit_strategy_name)
            if exit_strategy_function is not None:
                await exit_strategy_function(trade, trade_book, symbol)

        # unsubscribe from websocket if symbol has no other trades
        if symbol not in trade_book:
            ws.unsubscribe([symbol])


async def acme_risk_reward_exit(trade_exit: dict, book_exit: dict, symbol_exit: str) -> None:
    global dummy_strategy_1_profit

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
                dummy_strategy_1_profit += trade_exit["perc"]
                book_exit[symbol_exit].remove(trade_exit)
                discord.send_exit_message('Strategy 1: acme_risk_reward_exit', symbol_exit, trade_exit['perc'],
                                          dummy_strategy_1_profit)
                # After the exit trade is confirmed, reduce the trade count by 1.
                if len(trade_counts) > 0:
                    trade_counts[0] -= 1  # Decrement the count for the first strategy
                    # Ensure the count doesn't go below 0
                    if trade_counts[0] < 0:
                        trade_counts[0] = 0

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
                dummy_strategy_1_profit += trade_exit["perc"]
                book_exit[symbol_exit].remove(trade_exit)
                discord.send_exit_message('Strategy 1: acme_risk_reward_exit', symbol_exit, trade_exit['perc'],
                                          dummy_strategy_1_profit)
                # After the exit trade is confirmed, reduce the trade count by 1.
                if len(trade_counts) > 0:
                    trade_counts[0] -= 1  # Decrement the count for the first strategy
                    # Ensure the count doesn't go below 0
                    if trade_counts[0] < 0:
                        trade_counts[0] = 0


async def acme_exit(trade_exit: dict, book_exit: dict, symbol_exit: str,
                    zone_traversals_up: int, zone_traversals_down: int) -> None:
    global dummy_strategy_2_profit

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
        dummy_strategy_2_profit += trade_exit["perc"]
        book_exit[symbol_exit].remove(trade_exit)
        discord.send_exit_message("Strategy 2: acme_exit", symbol_exit, trade_exit['perc'],
                                  dummy_strategy_2_profit)
        # After the exit trade is confirmed, reduce the trade count by 1.
        if len(trade_counts) > 0:
            trade_counts[1] -= 1
            # Ensure the count doesn't go below 0
            if trade_counts[1] < 0:
                trade_counts[1] = 0


async def tp_sl_exit(trade_exit: dict, book_exit: dict, symbol_exit: str, tp: float, sl: float):
    global dummy_strategy_3_profit

    if (trade_exit["perc"] <= sl) or (trade_exit["perc"] >= tp):
        dummy_strategy_3_profit += trade_exit["perc"]
        book_exit[symbol_exit].remove(trade_exit)
        discord.send_exit_message("Strategy 3: tp_sl_exit", symbol_exit, trade_exit['perc'],
                                  dummy_strategy_3_profit)
        # After the exit trade is confirmed, reduce the trade count by 1.
        if len(trade_counts) > 0:
            trade_counts[2] -= 1
            # Ensure the count doesn't go below 0
            if trade_counts[2] < 0:
                trade_counts[2] = 0


async def tp_sl_top_of_minute_exit(trade_exit: dict, book_exit: dict, symbol_exit: str, tp: float, sl: float):
    global dummy_strategy_4_profit

    if (trade_exit["perc"] <= sl) or (trade_exit["perc"] >= tp and trade_time.is_top_of_minute()):
        dummy_strategy_4_profit += trade_exit["perc"]
        book_exit[symbol_exit].remove(trade_exit)
        discord.send_exit_message("Strategy 4: tp_sl_top_of_minute_exit", symbol_exit, trade_exit['perc'],
                                  dummy_strategy_4_profit)
        # After the exit trade is confirmed, reduce the trade count by 1.
        if len(trade_counts) > 0:
            trade_counts[3] -= 1
            # Ensure the count doesn't go below 0
            if trade_counts[3] < 0:
                trade_counts[3] = 0


async def tp_sl_top_of_minute_exhaustion_exit(
        trade_exit: dict, book_exit: dict, symbol_exit: str, tp: float, sl: float, exhaustion: int):
    global dummy_strategy_5_profit

    time_of_trade = datetime.strptime(trade_exit["ts"], '%Y-%m-%d %H:%M:%S')
    trade_is_old = datetime.utcnow() - time_of_trade > timedelta(minutes=exhaustion)

    if (trade_exit["perc"] <= sl) or (trade_exit["perc"] >= tp and trade_time.is_top_of_minute()) or trade_is_old:
        dummy_strategy_5_profit += trade_exit["perc"]
        book_exit[symbol_exit].remove(trade_exit)
        discord.send_exit_message("Strategy 5: tp_sl_top_of_minute_exhaustion_exit", symbol_exit, trade_exit['perc'],
                                  dummy_strategy_5_profit)
        # After the exit trade is confirmed, reduce the trade count by 1.
        if len(trade_counts) > 0:
            trade_counts[4] -= 1
            # Ensure the count doesn't go below 0
            if trade_counts[4] < 0:
                trade_counts[4] = 0


async def real_trade_exit():
    pass

    # End of exit code
######################################################################################################################


def get_worst_strategy():
    global dummy_strategy_1_profit
    global dummy_strategy_2_profit
    global dummy_strategy_3_profit
    global dummy_strategy_4_profit
    global dummy_strategy_5_profit

    min_profit = min(dummy_strategy_1_profit,
                     dummy_strategy_2_profit,
                     dummy_strategy_3_profit,
                     dummy_strategy_4_profit,
                     dummy_strategy_5_profit)

    if min_profit == dummy_strategy_1_profit:
        return 'strategy_1', dummy_strategy_1_profit
    elif min_profit == dummy_strategy_2_profit:
        return 'strategy_2', dummy_strategy_2_profit
    elif min_profit == dummy_strategy_3_profit:
        return 'strategy_3', dummy_strategy_3_profit
    elif min_profit == dummy_strategy_4_profit:
        return 'strategy_4', dummy_strategy_4_profit
    elif min_profit == dummy_strategy_5_profit:
        return 'strategy_5', dummy_strategy_5_profit
    else:
        return 'Not enough trade performance to calculate yet.'


def get_best_strategy():
    global dummy_strategy_1_profit
    global dummy_strategy_2_profit
    global dummy_strategy_3_profit
    global dummy_strategy_4_profit
    global dummy_strategy_5_profit

    max_profit = max(dummy_strategy_1_profit,
                     dummy_strategy_2_profit,
                     dummy_strategy_3_profit,
                     dummy_strategy_4_profit,
                     dummy_strategy_5_profit)

    if max_profit == dummy_strategy_1_profit:
        return 'strategy_1', dummy_strategy_1_profit
    elif max_profit == dummy_strategy_2_profit:
        return 'strategy_2', dummy_strategy_2_profit
    elif max_profit == dummy_strategy_3_profit:
        return 'strategy_3', dummy_strategy_3_profit
    elif max_profit == dummy_strategy_4_profit:
        return 'strategy_4', dummy_strategy_4_profit
    elif max_profit == dummy_strategy_5_profit:
        return 'strategy_5', dummy_strategy_5_profit
    else:
        return 'Not enough trade performance to calculate yet.'


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


async def get_pnz(scaled_open: float, entry_price: float) -> bool:
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
