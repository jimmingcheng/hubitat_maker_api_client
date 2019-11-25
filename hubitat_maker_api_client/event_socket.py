import time


class HubitatEvent:
    def __init__(self, json_dict):
        self.device_id = json_dict['deviceId']
        self.device_label = json_dict['displayName']
        self.attr_key = json_dict['name']
        self.attr_value = json_dict['value']
        self.timestamp = int(time.time())
