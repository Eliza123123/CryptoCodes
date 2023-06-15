class TradeCounts:
    def __init__(self):
        self.counts = [0, 0, 0, 0, 0, 0]

    def __getitem__(self, index):
        return self.counts[index]

    def decrement(self, index):
        if self.counts[index] > 0:
            self.counts[index] -= 1
