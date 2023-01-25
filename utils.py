from config import polar_profile


def parse_heartrate_measurement_data(data):
    hr = int.from_bytes(data[1:2], byteorder="little", signed=False)
    rr_intervals = []

    if len(list(data)) > 2:
        offset = 2
        while offset < len(list(data)):
            rr_interval_raw = int.from_bytes(data[offset : offset + 2], byteorder="little", signed=False)
            rr_intervals.append(rr_interval_raw / 1024.0 * 1000.0)

            offset += 2

    return hr, rr_intervals


def parse_ecg_data(data, prev_timestamp=None):
    timestamp = int.from_bytes(data[1:9], byteorder="little", signed=False)
    timestamp += polar_profile.timestamp_offset

    if prev_timestamp is None:
        return timestamp

    samples = data[10:]

    offset = 0
    ecg_list = [[], []]
    while offset < len(samples):
        ecg = int.from_bytes(samples[offset : offset + 3], byteorder="little", signed=True)
        offset += 3

        ecg_list[0].extend([ecg])

    diff_timestamp = timestamp - prev_timestamp
    each_timestamp = diff_timestamp / len(ecg_list[0])

    now_timestamp = timestamp
    for _ in ecg_list[0]:
        now_timestamp += each_timestamp
        ecg_list[1].extend([now_timestamp])

    return timestamp, ecg_list


def websocket_boardcast(clients, message):
    for client in clients:
        client.sendMessage(message)
