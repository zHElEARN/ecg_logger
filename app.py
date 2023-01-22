from bleak import BleakClient, BleakScanner
from rich import console, inspect, panel
import asyncio
import json

from config.polar_profile import polar_profile


DEVICE_NAME_UUID = polar_profile["Generic Access Profile"]["characteristics"]["Device Name"]["uuid"]
MANUFACTURER_NAME_UUID = polar_profile["Device Information"]["characteristics"]["Manufacturer Name String"]["uuid"]
BATTERY_LEVEL_UUID = polar_profile["Battery Service"]["characteristics"]["Battery Level"]["uuid"]

HEARTRATE_MEASUREMENT_UUID = polar_profile["Heart Rate"]["characteristics"]["Heart Rate Measurement"]["uuid"]


def heartrate_handler(sender, data):
    pass

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

        await polar_client.start_notify(HEARTRATE_MEASUREMENT_UUID, heartrate_handler)


if __name__ == "__main__":
    asyncio.run(main())
