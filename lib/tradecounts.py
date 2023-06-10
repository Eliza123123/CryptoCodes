class TradeCounts:
    def __init__(self):
        self.counts = [0, 0, 0, 0, 0, 0]

    def decrement(self, index):
        if self.counts[index] > 0:
            self.counts[index] -= 1
