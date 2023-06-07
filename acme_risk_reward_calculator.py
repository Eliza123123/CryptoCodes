from lib import acme

acme.init()
acme.combine_pnz()

price = 27150
entry_price = price / acme.get_scale(price)
trade_type = 'SELL'


entry_zone_index = None
min_distance = float('inf')

# Calculate the entry_zone_index
for i, tup in enumerate(acme.target_lg_list):
    mid_point = (tup[0] + tup[1]) / 2
    distance = abs(mid_point - entry_price)
    if distance < min_distance:
        min_distance = distance
        entry_zone_index = i

if entry_zone_index is not None:
    # outcome 1
    if trade_type == 'BUY':
        upper_zone_index = min(entry_zone_index + 1, len(acme.target_lg_list) - 1)
        lower_zone_index = max(entry_zone_index - 1, 0)

        upper_zone = acme.target_lg_list[upper_zone_index]
        lower_zone = acme.target_lg_list[lower_zone_index]

        room_up = abs(upper_zone[1] - entry_price)
        room_down = abs(entry_price - lower_zone[0])

        risk_reward = room_up / room_down
        print("Initial Risk Reward: ", risk_reward)

        while risk_reward < 1:
            upper_zone_index += 1
            # prevent index out of range error
            if upper_zone_index >= len(acme.target_lg_list):
                print("Reached end of zone list, can't move zone up further.")
                break
            upper_zone = acme.target_lg_list[upper_zone_index]
            room_up = abs(upper_zone[1] - entry_price)
            risk_reward = room_up / room_down
            print("Adjusted Risk Reward: ", risk_reward)

        print("Final Take Profit: ", upper_zone[1])
        print("Final Stop Loss: ", lower_zone[0])
        print("Final Risk Reward: ", risk_reward)
    # outcome 2
    elif trade_type == 'SELL':
        upper_zone_index = min(entry_zone_index + 1, len(acme.target_lg_list) - 1)
        lower_zone_index = max(entry_zone_index - 1, 0)

        upper_zone = acme.target_lg_list[upper_zone_index]
        lower_zone = acme.target_lg_list[lower_zone_index]

        room_up = abs(upper_zone[1] - entry_price)
        room_down = abs(entry_price - lower_zone[0])

        risk_reward = room_down / room_up
        print("Initial Risk Reward: ", risk_reward)

        while risk_reward < 1:
            lower_zone_index -= 1
            # prevent index out of range error
            if lower_zone_index < 0:
                print("Reached start of zone list, can't move zone down further.")
                break
            lower_zone = acme.target_lg_list[lower_zone_index]
            room_down = abs(entry_price - lower_zone[0])
            risk_reward = room_down / room_up
            print("Adjusted Risk Reward: ", risk_reward)

        print("Final Stop Loss: ", upper_zone[1])
        print("Final Take Profit: ", lower_zone[0])
        print("Final Risk Reward: ", risk_reward)
