import statistics
from trading_tool_functions import constant_frame

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
gaps = []

pnz = {
    1: [],
    2: [],
    3: [],
    4: [],
    5: [],
    6: [],
    7: [],
}

for i in range(1, len(frame_values)):
    gap = frame_values[i] - frame_values[i - 1]
    gaps.append(gap)

average = statistics.mean(gaps)
deviation = statistics.stdev(gaps)

for i in range(1, len(frame_values)):
    gap = frame_values[i] - frame_values[i - 1]
    for j in range(7, 0, -1):
        if gap > average + (j * deviation):
            pnz[j].append((frame_values[i - 1], frame_values[i]))
            for k in range(j - 1, 0, -1):
                pnz[k] = [value for value in pnz[k] if value not in pnz[j]]

# for j in range(1, 8):
#     print(f"pnz{j}:", pnz[j])
