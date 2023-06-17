from tabulate import tabulate


class TradeBooks:
    def __init__(self, *strategies):
        self.books = {}
        for i in strategies:
            self.books[i] = {}

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
        self.books[index]["stats"]["profit"] += perc
        self.books[index]["stats"]["min"] = min(self.books[index]["stats"]["min"], perc)
        self.books[index]["stats"]["max"] = min(self.books[index]["stats"]["max"], perc)

    def display_table(self, strategy: str, side: str, perc: float) -> str:
        return tabulate([
            ["Strategy", strategy],
            ["Side", side],
            ["Profit", perc],
            ["Min", self.books[strategy]["stats"]["min"]],
            ["Max", self.books[strategy]["stats"]["max"]],
            ["Total", self.books[strategy]["stats"]["profit"]],
        ], tablefmt="plain")
