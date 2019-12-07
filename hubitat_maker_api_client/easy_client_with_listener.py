from collections import defaultdict
from datetime import datetime
from hubitat_maker_api_client.easy_client import HubitatEasyClient


ATTR_KEY_TO_CAPABILITY = {
    'contact': 'ContactSensor',
    'lock': 'Lock',
    'motion': 'MotionSensor',
    'switch': 'Switch',
    'presence': 'PresenceSensor',
    'illuminance': 'IlluminanceMeasurement',
}


SUPPORTED_ACCESSOR_ATTRS = [
    ('ContactSensor', 'contact', 'open'),
    ('Lock', 'lock', 'unlocked'),
    ('MotionSensor', 'motion', 'active'),
    ('Switch', 'switch', 'on'),
    ('PresenceSensor', 'presence', 'present'),
]


UNSUPPORTED_ATTR_KEYS = ['dataType', 'values']


def date_to_timestamp(date_str):
    return int(datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z').timestamp())


class HubitatEasyClientWithListener(HubitatEasyClient):
    def __init__(
        self,
        api_client,
        alias_key='label',
        event_key='device_label',
        read_only=False,
    ):
        super(HubitatEasyClientWithListener, self).__init__(api_client, alias_key)
        self.event_key = event_key
        self.read_only = read_only

        if not self.read_only:
            self.init_cache()
            self.load_cache()

    def init_cache(self):
        self.cached_cap_to_aliases = defaultdict(set)
        self.cached_cap_to_attr_to_aliases = defaultdict(set)
        self.cached_cap_to_alias_to_attr_to_timestamp = dict()
        self.cached_cap_to_alias_to_attr = dict()

    def load_cache(self):
        self.set_last_device_attr_value(None, 'Home', 'mode', self._get_mode_from_api())
        self.set_last_device_attr_value(None, 'Home', 'hsmStatus', self._get_hsm_from_api())

        devices = self.api_client.get_devices()
        for device in devices:
            timestamp = date_to_timestamp(device['date'])
            alias = device[self.alias_key]
            for capability in device['capabilities']:
                self.add_device_alias_for_capability(capability, alias)

                for k, v in device['attributes'].items():
                    if k not in UNSUPPORTED_ATTR_KEYS:
                        self.add_device_alias_for_capability_and_attribute(capability, k, v, alias)
                        self.set_last_device_attr_value(capability, alias, k, v)
                        self.set_last_device_attr_timestamp(capability, alias, k, v, timestamp)

    # Cache mutators

    def add_device_alias_for_capability(self, capability, alias):
        self.cached_cap_to_aliases[capability].add(alias)

    def remove_device_alias_for_capability(self, capability, alias):
        self.cached_cap_to_aliases[capability].remove(alias)

    def add_device_alias_for_capability_and_attribute(self, capability, attr_key, attr_value, alias):
        k = (capability, attr_key, attr_value)
        self.cached_cap_to_attr_to_aliases[k].add(alias)

    def remove_device_alias_for_capability_and_attribute(self, capability, attr_key, attr_value, alias):
        k = (capability, attr_key, attr_value)
        self.cached_cap_to_attr_to_aliases[k].remove(alias)

    def set_last_device_attr_value(self, capability, alias, attr_key, attr_value):
        k = (capability, alias, attr_key)
        self.cached_cap_to_alias_to_attr[k] = attr_value

    def set_last_device_attr_timestamp(self, capability, alias, attr_key, attr_value, timestamp):
        k = (capability, alias, attr_key, attr_value)
        self.cached_cap_to_alias_to_attr_to_timestamp[k] = timestamp

    # Cache accessors

    def get_device_aliases_by_capability(self, capability):
        return self.cached_cap_to_aliases[capability]

    def get_device_aliases_by_capability_and_attribute(self, capability, attr_key, attr_value):
        k = (capability, attr_key, attr_value)
        return self.cached_cap_to_attr_to_aliases.get(k)

    def get_last_device_attr_value(self, capability, alias, attr_key):
        k = (capability, alias, attr_key)
        return self.cached_cap_to_alias_to_attr.get(k)

    def get_last_device_attr_timestamp(self, capability, alias, attr_key, attr_value):
        k = (capability, alias, attr_key, attr_value)
        return self.cached_cap_to_alias_to_attr_to_timestamp.get(k)

    # Device accessors

    def get_mode(self):
        return self.get_last_device_attr_value(None, 'Home', 'mode')

    def get_hsm(self):
        return self.get_last_device_attr_value(None, 'Home', 'hsmStatus')

    def get_last_device_value(self, alias, attr_key):
        capability = ATTR_KEY_TO_CAPABILITY.get(attr_key)
        return self.get_last_device_attr_value(capability, alias, attr_key)

    def get_last_device_timestamp(self, alias, attr_key, attr_value):
        capability = ATTR_KEY_TO_CAPABILITY.get(attr_key)
        return self.get_last_device_attr_timestamp(capability, alias, attr_key, attr_value)

    def update_from_hubitat_event(self, event):
        if self.read_only:
            return

        capability = ATTR_KEY_TO_CAPABILITY.get(event.attr_key)
        alias = getattr(event, self.event_key)
        if event.attr_key == 'mode':
            self.cached_mode = event.attr_value
        elif event.attr_key == 'hsmStatus':
            self.cached_hsm = event.attr_value
        elif capability:
            for cap, k, v in SUPPORTED_ACCESSOR_ATTRS:
                if cap == capability and k == event.attr_key:
                    if v == event.attr_value:
                        self.add_device_alias_for_capability_and_attribute(capability, k, v, alias)
                    else:
                        self.remove_device_alias_for_capability_and_attribute(capability, k, v, alias)

        self.set_last_device_attr_value(capability, alias, event.attr_key, event.attr_value)
        self.set_last_device_attr_timestamp(capability, alias, event.attr_key, event.attr_value, event.timestamp)
