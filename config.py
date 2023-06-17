import datetime
from typing import TypedDict

import yaml

CONFIG_ERROR_MSG: str = "Configuration file incorrectly formatted"


class Filters(TypedDict):
    """
    Filters config option dictionary hint typing.
    """
    liquidation: float
    zscore: int
    webhook: str


class Config:
    """
    Configuration object based on configuration file.
    """

    trade_book_wait: int
    entry_strategy_1: Filters
    entry_strategy_2: Filters
    zscore_timeframes: list
    zscore_period: int
    excluded_symbols: list

    def __init__(self, config_file: str) -> None:
        """
        Initialize the Config object.

        :param config_file: Configuration file path as string.
        """

        self.__read_configuration_file(config_file)
        self.__check_configuration()

    def __getitem__(self, item):
        return getattr(self, item)

    def __read_configuration_file(self, config_file: str) -> None:
        """
        Read passed config file assign class attributes.

        :param config_file: Configuration file path as string.
        :return: None
        """
        try:
            with open(config_file, "r") as stream:
                try:
                    config = yaml.load(stream, Loader=yaml.SafeLoader)
                    self.discord_entry_webhook = config.get("discord_entry_webhook")
                    self.discord_entry_webhook_enabled = config.get("discord_entry_webhook_enabled")

                    self.discord_exit_webhook = config.get("discord_exit_webhook")
                    self.discord_exit_webhook_enabled = config.get("discord_exit_webhook_enabled")

                    self.trade_cap = config.get("trade_cap")
                    self.trade_book_wait = config.get("trade_book_wait")

                    self.entry_strategy_1 = config.get("entry_strategy_1")
                    self.entry_strategy_2 = config.get("entry_strategy_2")

                    self.zscore_period = config.get("zscore_period")
                    self.zscore_timeframes = config.get("zscore_timeframes")
                    self.excluded_symbols = config.get("excluded_symbols")
                    self.excluded_quote = config.get("excluded_quote")
                    self.leverage = config.get("leverage")

                except (AttributeError, yaml.YAMLError) as e:
                    raise AttributeError(CONFIG_ERROR_MSG + f": {e}")
        except EnvironmentError:
            raise FileNotFoundError("Configuration file not found.")

    def __check_configuration(self) -> None:
        """
        Check configuration object attributes values.

        :return: None
        """
        try:
            if self.discord_entry_webhook_enabled and self.discord_entry_webhook is None:
                raise ValueError("Please provide a discord entry webhook URL.")
            if self.discord_exit_webhook_enabled and self.discord_exit_webhook is None:
                raise ValueError("Please provide a discord exit webhook URL.")
            if self.zscore_period is None:
                raise ValueError("Please provide Z-Score period value.")
            if self.zscore_timeframes is None:
                raise ValueError("Please provide Z-Score timeframes.")
        except ValueError as e:
            raise ValueError(CONFIG_ERROR_MSG + f": {e}")
