from tabulate import tabulate


class TradeBooks:
    def __init__(self, *strategies):
        self.books = {}
        self.stats = {}
        for i in strategies:
            self.books[i] = {}
            self.stats[i] = {
                "profit": 0.0,
                "min": 0.0,
                "max": 0.0,
            }

    def __getitem__(self, index):
        return self.books[index]

    def __setitem__(self, index, data):
        self.books[index] = data

    def __iter__(self):
        return iter(self.books)

    def __len__(self):
        return len(self.books)

    def as_dict(self):
        return self.books.items()

    def update(self, index, symbol, data):
        self.books[index][symbol] = data

    def remove(self, index, symbol):
        if symbol in self.books[index]:
            del self.books[index][symbol]

    def symbol_in_book(self, index, symbol) -> bool:
        return True if symbol in self.books[index] else False

    def symbol_in_books(self, symbol):
        for i in self.books:
            if symbol in self.books[i]:
                return True
        return False

    def total_trades(self) -> int:
        total: int = 0
        for i in self.books:
            total += len(self.books[i])
        return total

    def update_stats(self, index: str, perc: float):
        self.stats[index]["profit"] += perc
        self.stats[index]["min"] = min(self.stats[index]["min"], perc)
        self.stats[index]["max"] = min(self.stats[index]["max"], perc)

    def display_table(self, strategy: str, symbol: str, side: str, perc: float) -> str:
        return tabulate([
            ["Strategy", strategy],
            ["Symbol", symbol],
            ["Side", side],
            ["Profit", "{0:.2f}%".format(perc)],
            ["Min", "{0:.2f}%".format(self.stats[strategy]["min"])],
            ["Max", "{0:.2f}%".format(self.stats[strategy]["max"])],
            ["Total", "{0:.2f}%".format(self.stats[strategy]["profit"])],
        ], tablefmt="plain")
