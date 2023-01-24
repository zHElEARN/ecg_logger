import json

time_offset = 946684800000000000

polar_profile = None


with open("polar_profile.json", "r") as file:
    polar_profile = json.load(file)


DEVICE_NAME_UUID = polar_profile["Generic Access Profile"]["characteristics"]["Device Name"]["uuid"]
MANUFACTURER_NAME_UUID = polar_profile["Device Information"]["characteristics"]["Manufacturer Name String"]["uuid"]
BATTERY_LEVEL_UUID = polar_profile["Battery Service"]["characteristics"]["Battery Level"]["uuid"]
HEARTRATE_MEASUREMENT_UUID = polar_profile["Heart Rate"]["characteristics"]["Heart Rate Measurement"]["uuid"]
PMD_CONTROL_UUID = "FB005C81-02E7-F387-1CAD-8ACD2D8DF0C8"
PMD_DATA_UUID = "FB005C82-02E7-F387-1CAD-8ACD2D8DF0C8"