from bleak import BleakClient, BleakScanner
from rich import console, inspect, panel
import asyncio
import signal
import numpy

from config.polar_profile import *
import utils

stop = False


def signal_handler(signum, frame):
    global stop
    stop = True


signal.signal(signal.SIGINT, signal_handler)


hr_data, hr_changed = None, False


async def heartrate_handler(sender, data):
    global hr_data, hr_changed

    hr_data = data
    hr_changed = True


async def main():
    global hr_data, hr_changed

    c = console.Console()

    devices = await BleakScanner.discover()
    polar_device = next((device for device in devices if "Polar H10" in device.name), None)
    if polar_device is None:
        c.print("No devices found")
        exit()

    c.print(
        panel.Panel(
            f"Name: {polar_device.name}\nAddress: {polar_device.address}\nRSSI: {polar_device.rssi}", title="Bluetooth LE Information", border_style="cyan"
        )
    )

    async with BleakClient(polar_device) as polar_client:
        device_name = "".join(map(chr, await polar_client.read_gatt_char(DEVICE_NAME_UUID)))
        manufacturer_name = "".join(map(chr, await polar_client.read_gatt_char(MANUFACTURER_NAME_UUID)))
        battery_level = int((await polar_client.read_gatt_char(BATTERY_LEVEL_UUID))[0])

        c.print(
            panel.Panel(
                f"Device Name: {device_name}\nManufacturer Name: {manufacturer_name}\nBattery Level: {battery_level}%",
                title="Device Information",
                border_style="cyan",
            )
        )

        await polar_client.start_notify(HEARTRATE_MEASUREMENT_UUID, heartrate_handler)

        ecg_data_list = []
        ecg_first = True
        prev_timestamp = None

        async def handler(sender, data):
            nonlocal ecg_data_list, ecg_first, prev_timestamp

            if ecg_first:
                prev_timestamp = utils.parse_ecg_data(data)
                ecg_first = False
                print("first")
            else:
                prev_timestamp, ecg_data = utils.parse_ecg_data(data, prev_timestamp)
                ecg_data_list.extend(ecg_data)
                print("done")

        ECG_WRITE = bytearray([0x02, 0x00, 0x00, 0x01, 0x82, 0x00, 0x01, 0x01, 0x0E, 0x00])
        await polar_client.write_gatt_char(PMD_CONTROL_UUID, ECG_WRITE)
        await polar_client.start_notify(PMD_DATA_UUID, handler)

        while True:
            if hr_changed == True:
                hr_changed = False

                hr, rr_intervals = utils.parse_heartrate_measurement_data(hr_data)

                if not rr_intervals:
                    c.log(f"HR Measurement: {hr} bpm")
                else:
                    c.log(f"HR Measurement: {hr} bpm, RR Interval(s): {', '.join(str(rr_interval) for rr_interval in rr_intervals)} received.")
            else:
                await asyncio.sleep(0.1)

            if stop == True:
                break

        await polar_client.stop_notify(HEARTRATE_MEASUREMENT_UUID)
        numpy.save("ecg_data", ecg_data_list)


asyncio.run(main())
