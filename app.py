from bleak import BleakClient, BleakScanner
from rich import console, inspect, panel
import asyncio
import signal

from config.polar_profile import polar_profile


DEVICE_NAME_UUID = polar_profile["Generic Access Profile"]["characteristics"]["Device Name"]["uuid"]
MANUFACTURER_NAME_UUID = polar_profile["Device Information"]["characteristics"]["Manufacturer Name String"]["uuid"]
BATTERY_LEVEL_UUID = polar_profile["Battery Service"]["characteristics"]["Battery Level"]["uuid"]

HEARTRATE_MEASUREMENT_UUID = polar_profile["Heart Rate"]["characteristics"]["Heart Rate Measurement"]["uuid"]

stop = False


def signal_handler(signum, frame):
    global stop
    stop = True


signal.signal(signal.SIGINT, signal_handler)


async def main():
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

        hr_data, hr_changed = None, False

        async def heartrate_handler(sender, data):
            nonlocal hr_data, hr_changed

            hr_data = data
            hr_changed = True

        await polar_client.start_notify(HEARTRATE_MEASUREMENT_UUID, heartrate_handler)

        while True:
            if hr_changed == True:
                hr_changed = False

                hr = int.from_bytes(hr_data[1:2], byteorder="little", signed=False)

                rr_intervals = []
                if len(list(hr_data)) > 2:
                    i = 2
                    while i < len(list(hr_data)):
                        rr_interval_raw = int.from_bytes(hr_data[i:i+2], byteorder="little", signed=False)
                        rr_intervals.append(rr_interval_raw / 1024.0 * 1000.0)

                        i += 2

                if not rr_intervals:
                    c.log(f"HR Measurement: {hr} bpm")
                else:
                    c.log(f"HR Measurement: {hr} bpm, RR Interval(s): {', '.join(str(rr_interval) for rr_interval in rr_intervals)} received.")
            else:
                await asyncio.sleep(0.1)

            if stop == True:
                break

        await polar_client.stop_notify(HEARTRATE_MEASUREMENT_UUID)


asyncio.run(main())
