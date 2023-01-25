from bleak import BleakClient, BleakScanner
from rich import console, inspect, panel
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import threading
import asyncio
import signal
import numpy
import json

from config import polar_profile
import utils


stop = False
hr_data, hr_changed = None, False
ecg_data, ecg_changed, ecg_first, ecg_prev_timestamp = None, False, True, None

websocket_server = None
websocket_clients = []
class weboskcet_handler(WebSocket):
    def handleConnected(self):
        websocket_clients.append(self)


def websocket_main():
    global websocket_server, stop
    websocket_server = SimpleWebSocketServer("", 3500, weboskcet_handler)
    while stop == False:
        websocket_server.serveonce()

websocket_thread = threading.Thread(target=websocket_main)

def signal_handler(signum, frame):
    global stop
    stop = True


async def heartrate_handler(sender, data):
    global hr_data, hr_changed

    hr_data = data
    hr_changed = True


async def ecg_handler(sender, data):
    global ecg_data, ecg_changed

    ecg_data = data
    ecg_changed = True


async def main():
    global stop
    global websocket_clients
    global hr_data, hr_changed
    global ecg_data, ecg_changed, ecg_first, ecg_prev_timestamp

    c = console.Console()

    devices = await BleakScanner.discover()
    polar_device = next((device for device in devices if "Polar H10" in device.name), None)
    if polar_device is None:
        c.print("No devices found")
        stop = True
        exit()

    c.print(
        panel.Panel(
            f"Name: {polar_device.name}\nAddress: {polar_device.address}\nRSSI: {polar_device.rssi}", title="Bluetooth LE Information", border_style="cyan"
        )
    )

    async with BleakClient(polar_device) as polar_client:
        device_name = "".join(map(chr, await polar_client.read_gatt_char(polar_profile.DEVICE_NAME_UUID)))
        manufacturer_name = "".join(map(chr, await polar_client.read_gatt_char(polar_profile.MANUFACTURER_NAME_UUID)))
        battery_level = int((await polar_client.read_gatt_char(polar_profile.BATTERY_LEVEL_UUID))[0])

        c.print(
            panel.Panel(
                f"Device Name: {device_name}\nManufacturer Name: {manufacturer_name}\nBattery Level: {battery_level}%",
                title="Device Information",
                border_style="cyan",
            )
        )

        await polar_client.start_notify(polar_profile.HEARTRATE_MEASUREMENT_UUID, heartrate_handler)

        await polar_client.write_gatt_char(polar_profile.PMD_CONTROL_UUID, polar_profile.START_ECG_STREAM_BYTES)
        await polar_client.start_notify(polar_profile.PMD_DATA_UUID, ecg_handler)

        ecg_data_list = []

        while True:
            if hr_changed == True:
                hr_changed = False

                hr, rr_intervals = utils.parse_heartrate_measurement_data(hr_data)

                if not rr_intervals:
                    c.log(f"HR Measurement: {hr} bpm")
                    utils.websocket_boardcast(websocket_clients, json.dumps({"heartrate": hr}))
                else:
                    c.log(f"HR Measurement: {hr} bpm, RR Interval(s): {', '.join(str(rr_interval) for rr_interval in rr_intervals)} received.")
                    utils.websocket_boardcast(websocket_clients, json.dumps({"heartrate": hr, "rr_intervals": rr_intervals}))

            if ecg_changed == True:
                ecg_changed = False

                if ecg_first == True:
                    ecg_prev_timestamp = utils.parse_ecg_data(ecg_data)
                    c.log(f"Received the first ECG signal samples, the last timestamp: {ecg_prev_timestamp}")

                    ecg_first = False
                else:
                    ecg_prev_timestamp, ecg_parsed_data = utils.parse_ecg_data(ecg_data, ecg_prev_timestamp)
                    ecg_data_list.extend(ecg_parsed_data)
                    c.log(f"Received ECG signal samples, the last timestamp: {ecg_prev_timestamp}")

            await asyncio.sleep(0.01)

            if stop == True:
                break

        await polar_client.stop_notify(polar_profile.HEARTRATE_MEASUREMENT_UUID)
        numpy.save("ecg_data", ecg_data_list)


if __name__ == "__main__":
    websocket_thread.start()

    signal.signal(signal.SIGINT, signal_handler)
    asyncio.run(main())
