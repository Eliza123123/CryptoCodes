import locale
from tabulate import tabulate


class OutputTable:
    def __init__(self, symbol, side, quantity, price, liq_value, timestamp, entry_price):
        self.table = [
            ["Symbol", symbol],
            ["Side", side],
            ["Quantity", quantity],
            ["Price", price],
            ["Liquidation Value", locale.currency(liq_value, grouping=True)],
            ["Timestamp", timestamp],
            ["Scaled Price", entry_price]
        ]

    def print_table(self):
        table_string = tabulate(self.table, tablefmt="plain")
        print(table_string)

    def clear(self):
        self.table = []

    def append(self, row):
        self.table.append(row)
