import time


class HubitatEvent:
    def __init__(self, json_dict):
        self.device_id: int = json_dict['deviceId']
        self.device_label: str = json_dict['displayName']
        self.attr_key: str = json_dict['name']
        self.attr_value: str = json_dict['value']
        self.source: str = json_dict['source']
        self.timestamp: int = int(time.time())
        self.raw_event: dict = json_dict
