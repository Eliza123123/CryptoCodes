import json
import requests
import colorama
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)

# Some ANSI escape sequences for colours and effects
BLACK = '\u001b[30m'
RED = '\u001b[31m'
GREEN = '\u001b[32m'
YELLOW = '\u001b[33m'
BLUE = '\u001b[34m'
MAGENTA = '\u001b[35m'
CYAN = '\u001b[36m'
WHITE = '\u001b[37m'
RESET = '\u001b[0m'
BOLD = '\u001b[1m'
UNDERLINE = '\u001b[4m'
REVERSE = '\u001b[7m'


def colour_print(text: str, *effects: str) -> None:
    """
    Print `text` using the ANSI sequences to change colour, etc.

    :param text: The text to print.
    :param effects: The effect we want. One of the constants
        defined at the start of this module
    """
    effect_string = "".join(effects)
    output_string = "{0}{1}{2}".format(effect_string, text, RESET)
    colorama.init()
    print(output_string)
    colorama.deinit()


def constant_frame(*consts: float) -> list:
    """
    Generates a sorted list of values by repeatedly adding each constant
    to itself until reaching or exceeding 100.

    :param consts: Variable number of constants (floats) to be used in
    generating the values.
    :return: A sorted list of values obtained by adding the constants until
     reaching or exceeding 100.
    """
    values_list = []

    for const in consts:
        const_sequence = [const]
        const_added = const
        while const_added < 100:
            const_added += const
            if const_added < 100:
                const_sequence.append(round(const_added, 5))
            else:
                break
        values_list.extend(const_sequence)

    return sorted(values_list)


# Test code
# print(constant_frame(2.71828, 3.14159))


async def fetch_data(url: str, parameters: dict, headers: dict) -> dict:
    """
    Fetch data from the url with given parameters and headers.
    Return the JSON response as a dictionary.

    :param url: The URL to send the request to.
    :param parameters: The parameters for the request.
    :param headers: The headers for the request.
    :return: The JSON response from the request.
    """
    response = requests.get(url, params=parameters, headers=headers)
    return response.json()


def get_scale(price: float) -> float:
    """
    Determines the scale for a given price.

    :param price: The price value/
    :return: The scale value.
    """
    scales = [0.000000000001, 0.00000000001, 0.0000000001,
              0.000000001, 0.00000001, 0.0000001, 0.000001,
              0.00001, 0.0001, 0.001, 0.01, 0.1, 1, 10, 100, 1000,
              10000, 100000, 1000000, 10000000, 1000000000]
    for scale in scales:
        if scale <= price < (scale * 100):
            return scale
    return 1

# Test code
# print(get_scale(0.0000000000047465))
# print(get_scale(3.2))
# print(get_scale(27000))


def price_within(bounds_list: list, price: float) -> bool:
    """
    Check if the given price falls within any of the bounds in the bounds_list.

    :param bounds_list: A list of bounds, where each bound is
        a tuple containing two values: lower bound and upper bound.
    :param price: The price to check.
    :return:bool: True if the price falls within any of the bounds, False otherwise.
    """
    for bounds in bounds_list:
        if bounds[0] <= price <= bounds[1]:
            return True
    return False


def store_data(url: str, parameters: dict, headers: dict, filename: str) -> None:
    """
    Store data from an API response to a file.

    :param url: The URL of the API endpoint.
    :param parameters: The parameters to include in the API request.
    :param headers: The headers to include in the API request.
    :param filename: The name of the file to store the data.
    :return: This function does not return any value.
    :raises:  Exception: If an error occurs during the data retrieval or storage process.
    """
    try:
        response = requests.get(url, params=parameters, headers=headers, verify=False)
        data = json.loads(response.text)

        with open(filename, "w") as stored_data:
            json.dump(data, stored_data, indent=4)
    except Exception as e:
        print(f"Error occurred: {str(e)}")


def through_pnz_small(bounds_list: list, candle_open: float, candle_close: float) -> bool:
    """
    Check if the candle has crossed through any of the bounds in the bounds_list.

    :param bounds_list: A list of bounds, where each bound is a tuple
        containing two values: lower bound and upper bound.
    :param candle_open: The opening price of the candle.
    :param candle_close: The closing price of the candle.
    :return bool: True if the candle has crossed through any of the bounds, False otherwise.
    """
    for bounds in bounds_list:
        # Tests for cross under (the open is above bounds[1] and bounds [0]),
        # (the close is below bounds[1] and bounds [0]
        if (candle_open > bounds[1]) and (candle_close < bounds[0]):
            return True
        # Tests for cross over (the open is below bounds[0] and bounds [1]),
        # (the close is above bounds[0] and bounds [1]
        elif (candle_open < bounds[0]) and (candle_close > bounds[1]):
            return True
    return False
