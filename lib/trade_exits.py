from lib import acme


def on_acme(close: float, zone_traversals_up: int, zone_traversals_down: int) -> bool:
    entry_zone_index = None

    # Iterate over the combined zones list
    for i, tup in enumerate(acme.target_lg_list):
        if tup[0] <= close <= tup[1]:
            entry_zone_index = i
            break

    if entry_zone_index is None:
        # Entry price is not within any tuple in the list.
        # Calculate the mid-points of each tuple.
        mid_points = [(tup[0] + tup[1]) / 2 for tup in acme.target_lg_list]

        # Find the index of the tuple with the closest mid-point to the entry price.
        entry_zone_index = min(range(len(mid_points)), key=lambda j: abs(mid_points[j] - close))

    # Calculate upper and lower zones
    upper_zone_index = min(entry_zone_index + zone_traversals_up, len(acme.target_lg_list) - 1)
    lower_zone_index = max(entry_zone_index - zone_traversals_down, 0)

    upper_zone = acme.target_lg_list[upper_zone_index]
    lower_zone = acme.target_lg_list[lower_zone_index]

    return close >= upper_zone[1] or close <= lower_zone[0]


def on_tp_sl(pct: float, tp: float, sl: float):
    return pct <= sl or pct >= tp


def on_tp_sl_top_of_minute(pct: float, trade_time, tp: float, sl: float):
    return pct <= sl or (pct >= tp and trade_time.is_top_of_minute())


def on_tp_sl_top_of_minute_exhaustion(pct: float, tp: float, sl: float):
    pass
