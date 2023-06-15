class StrategyProfit:
    def __init__(self, dummy_strategy_count, real_strategy_count):
        self.dummy_strategy_profits = [0 for _ in range(dummy_strategy_count)]
        self.real_strategy_profits = [0 for _ in range(real_strategy_count)]

    def worst_dummy_profit(self):
        worst_profit = min(self.dummy_strategy_profits)
        return worst_profit

    def best_dummy_profit(self):
        best_profit = max(self.dummy_strategy_profits)
        return best_profit
