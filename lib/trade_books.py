class TradeBooks:
    def __init__(self, num_books):
        self.books = [{} for _ in range(num_books)]

    def __getitem__(self, index):
        return self.books[index]

    def __iter__(self):
        return iter(self.books)

    def __len__(self):
        return len(self.books)

    def get_book(self, index):
        return self.books[index]

    def update_book(self, index, symbol, trade_data):
        trade_book = self.books[index]
        if symbol not in trade_book:
            trade_book[symbol] = [trade_data]
        else:
            if trade_data not in trade_book[symbol]:
                trade_book[symbol].append(trade_data)

    def remove_trade(self, index, symbol, trade_data):
        trade_book = self.books[index]
        if symbol in trade_book and trade_data in trade_book[symbol]:
            trade_book[symbol].remove(trade_data)

    def symbol_in_books(self, symbol):
        return any(symbol in trade_book for trade_book in self.books)
