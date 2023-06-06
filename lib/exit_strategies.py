from datetime import datetime, timedelta

from lib import discord, trade_time, acme

total_profit = 0


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
        return

    # Calculate upper and lower zones
    upper_zone_index = min(entry_zone_index + zone_traversals_up, len(acme.target_lg_list) - 1)
    lower_zone_index = max(entry_zone_index - zone_traversals_down, 0)

    upper_zone = acme.target_lg_list[upper_zone_index]
    lower_zone = acme.target_lg_list[lower_zone_index]

    print("Upper Zone:", upper_zone)
    print("Lower Zone:", lower_zone)

    if (trade["close"] >= upper_zone[1]) or (trade["close"] <= lower_zone[0]):
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
