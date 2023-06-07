import yaml
import datetime
from typing import TypedDict

CONFIG_ERROR_MSG: str = "Configuration file incorrectly formatted"


class Filters(TypedDict):
    """
    Filters config option dictionary hint typing.
    """

    liquidation: float
    zscore: int


class Config:
    """
    Configuration object based on configuration file.
    """

    trade_book_wait: int
    filters: Filters
    zscore_timeframes: list
    zscore_lookback: int
    excluded_symbols: list

    def __init__(self, config_file: str) -> None:
        """
        Initialize the Config object.

        :param config_file: Configuration file path as string.
        """

        self.__read_configuration_file(config_file)
        self.__check_configuration()

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
                    self.discord_webhook = config.get(
                        "discord_webhook"
                    )
                    self.discord_webhook_3 = config.get(
                        "discord_webhook_3"
                    )
                    self.discord_webhook_config_1 = config.get(
                        "discord_webhook_config_1"
                    )
                    self.discord_webhook_config_2 = config.get(
                        "discord_webhook_config_2"
                    )
                    self.discord_webhook_config_3 = config.get(
                        "discord_webhook_config_3"
                    )
                    self.discord_webhook_config_4 = config.get(
                        "discord_webhook_config_4"
                    )
                    self.discord_webhook_config_5 = config.get(
                        "discord_webhook_config_5"
                    )
                    self.discord_webhook_enabled = config.get(
                        "discord_webhook_enabled"
                    )
                    self.discord_webhook_3_enabled = config.get(
                        "discord_webhook_3_enabled"
                    )
                    self.discord_webhook_config_1_enabled = config.get(
                        "discord_webhook_config_1_enabled"
                    )
                    self.discord_webhook_config_2_enabled = config.get(
                        "discord_webhook_config_2_enabled"
                    )
                    self.discord_webhook_config_3_enabled = config.get(
                        "discord_webhook_config_3_enabled"
                    )
                    self.discord_webhook_config_4_enabled = config.get(
                        "discord_webhook_config_4_enabled"
                    )
                    self.discord_webhook_config_5_enabled = config.get(
                        "discord_webhook_config_5_enabled"
                    )
                    self.trade_book_wait = config.get(
                        "trade_book_wait"
                    )
                    self.filters = config.get(
                        "filters"
                    )
                    self.zscore_lookback = config.get(
                        "zscore_lookback"
                    )
                    self.zscore_timeframes = config.get(
                        "zscore_timeframes"
                    )
                    self.excluded_symbols = config.get(
                        "excluded_symbols"
                    )
                    self.leverage = config.get(
                        "leverage"
                    )
                except (AttributeError, yaml.YAMLError) as e:
                    raise AttributeError(CONFIG_ERROR_MSG + f": {e}")
        except EnvironmentError:
            raise FileNotFoundError("Configuration file not found.")

    def __check_configuration(self) -> None:
        """
        Check configuration object attributes values.

        :return: None
        """
        current_datetime = datetime.datetime.utcnow()
        try:
            if self.discord_webhook_enabled and self.discord_webhook is None:
                raise ValueError("Please provide a discord webhook URL.")
            if not self.filters.get("liquidation"):
                raise ValueError("Please provide a liquidations filter value.")
            if not self.filters.get("zscore"):
                raise ValueError("Please provide a Z-Score filter value.")
            if self.zscore_lookback is None:
                raise ValueError("Please provide Z-Score lookback value.")
            if self.zscore_timeframes is None:
                raise ValueError("Please provide Z-Score timeframes.")
        except ValueError as e:
            raise ValueError(CONFIG_ERROR_MSG + f": {e}")
