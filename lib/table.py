import locale
from datetime import datetime
from tabulate import tabulate


class EntryTable:
    def __init__(self, symbol, side, quantity, price, liq_value, entry_price):
        self.table = [
            ["Symbol", symbol],
            ["Side", "Buyer Liquidated" if side == "SELL" else "Seller Liquidated"],
            ["Quantity", quantity],
            ["Price", price],
            ["Liquidation Value", locale.currency(liq_value, grouping=True)],
            ["Timestamp", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')],
            ["Scaled Price", entry_price]
        ]

    def __str__(self):
        return tabulate(self.table, tablefmt="plain")

    def clear(self):
        self.table = []

    def append(self, key, value):
        self.table.append([key, value])


class ZScoreTable:
    def __init__(self, zscores):
        self.rows = [['Z-Score'] + [zs for zs in zscores.values()]]
        self.headers = ['Timeframe'] + [zs for zs in zscores.keys()]

    def __str__(self):
        return tabulate(self.rows, headers=self.headers, tablefmt="simple", floatfmt=".2f")
