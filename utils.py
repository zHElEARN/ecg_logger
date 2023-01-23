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
