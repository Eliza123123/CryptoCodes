import json
from statistics import mean, stdev

from requests import get

# Initiate Data Structures.
gaps = []
pnz_lg = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: []}
pnz_sm = {1: []}

target_lg_list = []


def init() -> None:
    # Define constants for calculation.
    frame_values = constant_frame(1.32, 0.787, 1.1, 1.1494, 1.2346, 1.8786,
                                  1.9453, 2.3571, 2.6149, 2.8017, 3.5327,
                                  3.7396, 4.1245, 4.2817, 4.7494, 0.54325,
                                  0.57596, 0.57722, 0.59017, 0.59635, 0.60793,
                                  0.62432, 0.63092, 0.63212, 0.64341, 0.66016,
                                  0.66132, 0.66171, 0.66274, 0.67823, 0.69315,
                                  0.73908, 0.76422, 0.82248, 0.83463, 0.83565,
                                  0.85074, 0.87059, 0.91596, 0.91894, 0.95532,
                                  0.97027, 0.98943, 1.00743, 1.01494, 1.13199,
                                  1.1547, 1.16803, 1.17628, 1.18657, 1.18745,
                                  1.20207, 1.2337, 1.25992, 1.28243, 1.29129,
                                  1.30358, 1.30568, 1.30638, 1.32472, 1.41421,
                                  1.44225, 1.45136, 1.45607, 1.46708, 1.50659,
                                  1.5396, 1.58496, 1.60667, 1.61803, 1.66169,
                                  1.70521, 1.73205, 1.78723, 1.90216, 2.09455,
                                  2.10974, 2.23606, 2.29317, 2.29559, 2.39996,
                                  2.50291, 2.58498, 2.62206, 2.66514, 2.68545,
                                  2.71828, 2.74724, 2.80777, 3.14159, 3.35989,
                                  4.53236, 4.6692, 23.14609
                                  )

    # Find the average gap between the lines created by constants being
    # iterated, then find the standard deviation of these gaps.
    for i in range(1, len(frame_values)):
        gap = frame_values[i] - frame_values[i - 1]
        gaps.append(gap)

    average = mean(gaps)
    deviation = stdev(gaps)

    # Populate pnz_lg dictionary with the relevant data
    for i in range(1, len(frame_values)):
        gap = frame_values[i] - frame_values[i - 1]
        for j in sorted(pnz_lg.keys(), reverse=True):
            if gap > average + (j * deviation):
                pnz_lg[j].append((frame_values[i - 1], frame_values[i]))
                for k in range(j - 1, 0, -1):
                    pnz_lg[k] = \
                        [value for value in pnz_lg[k] if value not in pnz_lg[j]]

    # Populate pnz_sm dictionary with the relevant data
    for i in range(1, len(frame_values)):
        gap = frame_values[i] - frame_values[i - 1]
        if gap < average - (1 * deviation):
            pnz_sm[1].append((frame_values[i - 1], frame_values[i]))


def combine_pnz():
    for key in range(3, 7):  # inclusive of 3 and 6
        target_lg_list.extend(pnz_lg[key])
    target_lg_list.sort(key=lambda tup: tup[0])  # sort by the first element of each tuple


def constant_frame(*consts: float) -> list:
    """
    Generates a sorted list of values based on the input constants.
    For each constant, it continues to incrementally add the constant to itself until
    the summed value reaches or exceeds 100. All such generated values are less than 100.

    This function is primarily useful for creating a sequence of values for each provided
    constant, up to a certain limit (100 in this case). This could be useful for creating
    frames or scales based on given constants.

    :param consts: Variable number of constants (floats). These are the base values used
    to generate sequences of values. Each constant generates its own sequence, and all
    sequences are combined into a single sorted list.

    :return: A sorted list of values, each value being the result of successively adding
    a constant to itself up to a limit of 100. Each constant produces its own sequence of
    values, and all these sequences are merged and sorted to produce the returned list.

    Note: The function rounds each summed value to 5 decimal places.

    Example usage:

    ```
    print(constant_frame(10.5, 15.75))
    ```

    This will output a list of numbers, where each number is a multiple of either 10.5 or 15.75,
    all numbers are less than 100, and the list is in ascending order.
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


def get_scale(price: float) -> float:
    """
    Computes a scale factor for a given price.

    This function determines an appropriate scale for a price value
    based on predefined scale thresholds. The scale is the smallest
    value in the predefined list such that the price is greater than
    or equal to the scale but less than one hundred times the scale.
    The function is designed to adjust the scale of a price value so
    that comparisons and calculations can be made in a consistent way,
    regardless of the original magnitude of the price.

    The function uses a predefined list of scale values, which range
    from 1e-12 to 1e9. If no suitable scale is found in the list (i.e.,
    the price is larger than one hundred times the largest scale), a
    scale of 1 is returned by default.

    :param price: The price value for which to determine a scale.
    This should be a non-negative float, although this is not enforced
    by the function.

    :return: The determined scale factor as a float.

    Example usage:

    ```
    price = 150000
    scale = get_scale(price)
    print(scale)  # Outputs: 1000
    ```
    """
    scales = [0.000000000001, 0.00000000001, 0.0000000001,
              0.000000001, 0.00000001, 0.0000001, 0.000001,
              0.00001, 0.0001, 0.001, 0.01, 0.1, 1, 10, 100, 1000,
              10000, 100000, 1000000, 10000000, 1000000000]
    for scale in scales:
        if scale <= price < (scale * 100):
            return scale
    return 1


def price_within(bounds_list: list, price: float) -> bool:
    """
    Determines whether a given price is within any of the specified bounds.

    This function iterates over a list of bounds (each represented as a tuple of
    two values: a lower limit and an upper limit). For each bound in the list,
    the function checks whether the given price falls within the range specified
    by the bound, inclusive of the limit values.

    If the price is found to be within any of the bounds, the function immediately
    returns True and stops further iteration. If the end of the list is reached
    without finding a matching bound, the function returns False, indicating that
    the price is outside all the specified bounds.

    The function is useful for checking whether a price falls within any of
    multiple potentially overlapping or disjoint price ranges.

    :param bounds_list: A list of bounds. Each bound should be a tuple of two
    float values, representing a lower limit and an upper limit respectively.

    :param price: The price to be checked. This should be a float value.

    :return: A boolean value indicating whether the price falls within any of the
    bounds. True if the price is within any of the bounds, False otherwise.

    Example usage:

    ```
    bounds = [(0, 10), (20, 30), (40, 50)]
    price = 25
    result = price_within(bounds, price)
    print(result)  # Outputs: True
    ```
    """
    for bounds in bounds_list:
        if bounds[0] <= price <= bounds[1]:
            return True
    return False


def store_data(url: str, parameters: dict, headers: dict, filename: str) -> None:
    """
    Fetches data from a specified URL with given parameters and headers,
    and stores the returned data in a local file in JSON format.

    This function sends a GET request to the specified URL, passing the
    provided parameters and headers as part of the request. It expects the
    response to be in JSON format and attempts to parse it accordingly.
    If the request is successful and the response can be parsed as JSON,
    the resulting data structure is written to a local file with the specified
    filename. The data is stored in a human-readable format with indentation
    for ease of viewing.

    This function provides a convenient way to store data retrieved from an API
    for offline analysis or to cache the result of a time-consuming data retrieval
    operation for later use.

    :param url: A string representing the URL of the API endpoint from which to
    fetch the data.

    :param parameters: A dictionary containing the parameters to be included in
    the GET request. Each key-value pair in the dictionary corresponds to one parameter.

    :param headers: A dictionary containing the headers to be included in the GET request.
    Each key-value pair in the dictionary corresponds to one header.

    :param filename: A string representing the name of the file in which to store the
    retrieved data. If the file does not already exist, it will be created. If it does
    exist, it will be overwritten.

    :return: This function does not return any value. Its sole purpose is to
    retrieve data and store it in a file.

    :raises Exception: If any error occurs during the data retrieval or storage
    process, this function will raise an exception. Typical reasons for exceptions
    include network errors, invalid responses from the server, and I/O errors when
    attempting to write to the file.
    """
    try:
        response = get(url, params=parameters, headers=headers, verify=False)
        data = json.loads(response.text)

        with open(filename, "w") as stored_data:
            json.dump(data, stored_data, indent=4)
    except Exception as e:
        print(f"Error occurred: {str(e)}")


def through_pnz_small(bounds_list: list, candle_open: float, candle_close: float) -> bool:
    """
    Checks if the price during the timeframe of a single candlestick has crossed through any
    of the price bounds in the provided list.

    This function is used in the context of candlestick chart analysis, where each candlestick
    represents price movement over a specific timeframe. The "open" price is the price at the
    start of the timeframe, and the "close" price is the price at the end.

    For each pair of bounds in the list, the function checks if the price has moved from above
    the upper bound to below the lower bound (cross under), or from below the lower bound to
    above the upper bound (cross over) during the timeframe.

    This function can be useful for identifying candles that have crossed certain significant
    price levels or zones during their formation.

    :param bounds_list: A list of tuples, each of which represents a pair of price bounds.
    Each tuple should contain two float values: the first being the lower bound and the second
    being the upper bound.

    :param candle_open: A float representing the opening price of the candlestick.

    :param candle_close: A float representing the closing price of the candlestick.

    :return: Returns a boolean value. The function returns True if the price has crossed through
    any of the provided bounds during the candlestick's timeframe. Otherwise, it returns False.

    :raises ValueError: If the bounds_list does not contain tuples of two elements, a ValueError
    will be raised.
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
