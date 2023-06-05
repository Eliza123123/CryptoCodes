from lib import discord, trade_time

total_profit = 0


async def tp_sl_top_of_minute_exit(trade, book, symbol, tp, sl):
    global total_profit

    if (trade["perc"] <= sl) or (trade["perc"] >= tp and trade_time.is_top_of_minute()):
        total_profit += trade["perc"]
        book[symbol].remove(trade)
        discord.send_exit_message(symbol, trade['perc'], total_profit)
