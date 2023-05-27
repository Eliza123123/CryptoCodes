import random
import json
import requests
import colorama
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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


def average(lst):
    if len(lst) == 0:
        return 0  # Return 0 for an empty list to avoid division by zero error
    else:
        return sum(lst) / len(lst)


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


def adjacent_dists(self_added_constants: list) -> list:
    """
    Calculates the distance between adjacent elements in the provided list.
        Example:

        >self_added_constants = [1, 4, 7, 2]
            >distances = distance_compare(self_added_constants)
                >print(distances)
                    >Output: [3, 3, 5]

    :param self_added_constants: The list of values.
    :return list: A list of distances between adjacent elements.
    """
    distances = []

    for i in range(len(self_added_constants) - 1):
        distance = abs(self_added_constants[i] - self_added_constants[i + 1])
        distances.append(distance)

    return distances


# Test code
# selected_constants = constant_frame(2.71828, 3.14159)
# print(selected_constants[1] - selected_constants[0])
# print(adjacent_dists(selected_constants))


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


def prime_sequence(n: int) -> list:
    """
    Generates a sequence of prime numbers up to the given number `n`.

    :param n: The upper limit for generating prime numbers.
    :return: A list of prime numbers up to `n`.
    """
    primes = []

    for num in range(2, n + 1):
        is_prime = True

        for i in range(2, int(num ** 0.5) + 1):
            if num % i == 0:
                is_prime = False
                break

        if is_prime:
            primes.append(num)

    return primes


# Test code
# print(prime_sequence(100))


def prime_indexed_prime_sequence(n: int) -> list:
    """
    Generates a sequence of prime numbers up to the given number `n`,
    where each prime number represents the index of another prime number.

    :param n: The upper limit for generating prime numbers.
    :return: A list of prime numbers where each prime represents an index.
    """
    primes = prime_sequence(n)
    indexed_primes = []

    for prime in primes:
        if prime <= len(primes):
            indexed_primes.append(primes[prime - 1])

    return indexed_primes


# Test code
# print(prime_indexed_prime_sequence(100))


def price_within(bounds_list: list, price: float) -> bool:
    for bounds in bounds_list:
        if bounds[0] <= price <= bounds[1]:
            return True
    return False


def pseudo_candles(n: int, max_price: int = 100) -> list:
    """
    Generates a list of pseudo candlestick data.

    Each element in the list represents a candlestick and consists
    of four values:
    - open_val: The opening price of the candlestick.
    - close_val: The closing price of the candlestick.
    - high_val: The highest price reached during the candlestick's duration.
    - low_val: The lowest price reached during the candlestick's duration.

    :param n: The number of candlesticks to generate.
    :param max_price: The maximum price value to use for generating the
        candlestick data. Defaults to 100.
    :return: A list of pseudo candlestick data.
    """
    candlestick_data = []
    close_val = 0

    for candle_count in range(0, n):
        if candle_count == 0:
            close_val = round(random.uniform(1, max_price), 2)

        else:
            open_val = close_val
            close_val = round(random.uniform(1, max_price), 2)
            high_val = \
                round(random.uniform(max(open_val, close_val), max_price), 2)
            low_val = \
                round(random.uniform(1, min(open_val, close_val)), 2)
            candle = (open_val, close_val, high_val, low_val)
            candlestick_data.append(candle)

    return candlestick_data


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
            print("Data stored successfully.")
    except Exception as e:
        print(f"Error occurred: {str(e)}")


def through_pnz_small(bounds_list: list, candle_open: float, candle_close: float) -> bool:
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
