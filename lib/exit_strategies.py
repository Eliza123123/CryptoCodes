from datetime import datetime, timedelta

from lib import discord, trade_time, acme

total_profit = 0


async def acme_risk_reward_exit(trade: dict, book: dict, symbol: str) -> None:
    global total_profit
    entry_price = trade['entry']
    trade_type = trade['side']  # 'buy' or 'sell'
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

            if (trade["close"] >= upper_zone[1]) or (trade["close"] <= lower_zone[0]):
                total_profit += trade["perc"]
                book[symbol].remove(trade)
                discord.send_exit_message(symbol, trade['perc'], total_profit)

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

            if (trade["close"] >= upper_zone[1]) or (trade["close"] <= lower_zone[0]):
                total_profit += trade["perc"]
                book[symbol].remove(trade)
                discord.send_exit_message(symbol, trade['perc'], total_profit)


async def acme_exit(trade: dict, book: dict, symbol: str,
                    zone_traversals_up: int, zone_traversals_down: int) -> None:
    global total_profit
    entry_price = trade['entry']
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

    if (trade["close"] >= upper_zone[1]) or (trade["close"] <= lower_zone[0]):
        total_profit += trade["perc"]
        book[symbol].remove(trade)
        discord.send_exit_message(symbol, trade['perc'], total_profit)


async def tp_sl_exit(trade: dict, book: dict, symbol: str, tp: float, sl: float):
    global total_profit

    if (trade["perc"] <= sl) or (trade["perc"] >= tp):
        total_profit += trade["perc"]
        book[symbol].remove(trade)
        discord.send_exit_message(symbol, trade['perc'], total_profit)


async def tp_sl_top_of_minute_exit(trade: dict, book: dict, symbol: str, tp: float, sl: float):
    global total_profit

    if (trade["perc"] <= sl) or (trade["perc"] >= tp and trade_time.is_top_of_minute()):
        total_profit += trade["perc"]
        book[symbol].remove(trade)
        discord.send_exit_message(symbol, trade['perc'], total_profit)


async def tp_sl_top_of_minute_exhaustion_exit(
        trade: dict, book: dict, symbol: str, tp: float, sl: float, exhaustion: int):
    global total_profit

    time_of_trade = datetime.strptime(trade["ts"], '%Y-%m-%d %H:%M:%S')
    trade_is_old = datetime.utcnow() - time_of_trade > timedelta(minutes=exhaustion)

    if (trade["perc"] <= sl) or (trade["perc"] >= tp and trade_time.is_top_of_minute()) or trade_is_old:
        total_profit += trade["perc"]
        book[symbol].remove(trade)
        discord.send_exit_message(symbol, trade['perc'], total_profit)
