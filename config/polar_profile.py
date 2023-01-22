import json

polar_profile = None

with open("polar_profile.json", "r") as file:
    polar_profile = json.load(file)