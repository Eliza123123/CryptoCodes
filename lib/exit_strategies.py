from datetime import datetime, timedelta

from lib import discord, trade_time

total_profit = 0


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
