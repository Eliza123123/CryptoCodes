class StrategyProfit:
    def __init__(self):
        self.dummy_strategy_1_profit = 0
        self.dummy_strategy_2_profit = 0
        self.dummy_strategy_3_profit = 0
        self.dummy_strategy_4_profit = 0
        self.dummy_strategy_5_profit = 0
        self.real_strategy_profit = 0

    def worst_dummy_profit(self):
        strategy_profits = {
            'strategy_1': self.dummy_strategy_1_profit,
            'strategy_2': self.dummy_strategy_2_profit,
            'strategy_3': self.dummy_strategy_3_profit,
            'strategy_4': self.dummy_strategy_4_profit,
            'strategy_5': self.dummy_strategy_5_profit
        }
        worst_strategy = min(strategy_profits, key=strategy_profits.get)
        return worst_strategy

    def best_dummy_profit(self):
        strategy_profits = {
            'strategy_1': self.dummy_strategy_1_profit,
            'strategy_2': self.dummy_strategy_2_profit,
            'strategy_3': self.dummy_strategy_3_profit,
            'strategy_4': self.dummy_strategy_4_profit,
            'strategy_5': self.dummy_strategy_5_profit
        }
        best_strategy = max(strategy_profits, key=strategy_profits.get)
        return best_strategy
