from datetime import datetime
from hubitat_maker_api_client.client import HubitatClient


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


class HubitatCachingClient(HubitatClient):
    def __init__(
        self,
        api_client,
        device_cache,
        alias_key='label',
        event_key='device_label',
        cache_writes_enabled=True,
    ):
        super(HubitatCachingClient, self).__init__(api_client, alias_key)
        self.device_cache = device_cache
        self.event_key = event_key
        self.cache_writes_enabled = cache_writes_enabled

        if self.cache_writes_enabled:
            self.device_cache.clear()
            self.load_cache()

    def load_cache(self):
        self.device_cache.set_last_device_attr_value(None, 'Home', 'mode', self._get_mode_from_api())
        self.device_cache.set_last_device_attr_value(None, 'Home', 'hsmStatus', self._get_hsm_from_api())

        devices = self.api_client.get_devices()
        for device in devices:
            timestamp = date_to_timestamp(device['date'])
            alias = device[self.alias_key]
            for capability in device['capabilities']:
                self.device_cache.add_device_for_capability(capability, alias)

                for k, v in device['attributes'].items():
                    if k not in UNSUPPORTED_ATTR_KEYS:
                        self.device_cache.add_device_for_capability_and_attribute(capability, k, v, alias)
                        self.device_cache.set_last_device_attr_value(capability, alias, k, v)
                        self.device_cache.set_last_device_attr_timestamp(capability, alias, k, v, timestamp)

    def get_devices_by_capability(self, capability):
        return self.device_cache.get_devices_by_capability(capability)

    def get_devices_by_capability_and_attribute(self, capability, attr_key, attr_value):
        return self.device_cache.get_devices_by_capability_and_attribute(capability, attr_key, attr_value)

    # Device accessors

    def get_mode(self):
        return self.device_cache.get_last_device_attr_value(None, 'Home', 'mode')

    def get_hsm(self):
        return self.device_cache.get_last_device_attr_value(None, 'Home', 'hsmStatus')

    def get_last_device_value(self, alias, attr_key, capability=None):
        if not capability:
            capability = ATTR_KEY_TO_CAPABILITY.get(attr_key)
        return self.device_cache.get_last_device_attr_value(capability, alias, attr_key)

    def get_last_device_timestamp(self, alias, attr_key, attr_value, capability=None):
        if not capability:
            capability = ATTR_KEY_TO_CAPABILITY.get(attr_key)
        return self.device_cache.get_last_device_attr_timestamp(capability, alias, attr_key, attr_value)

    def update_from_hubitat_event(self, event):
        if not self.cache_writes_enabled:
            return

        capability = ATTR_KEY_TO_CAPABILITY.get(event.attr_key)
        alias = getattr(event, self.event_key)
        if capability:
            for cap, k, v in SUPPORTED_ACCESSOR_ATTRS:
                if cap == capability and k == event.attr_key:
                    if v == event.attr_value:
                        self.device_cache.add_device_for_capability_and_attribute(capability, k, v, alias)
                    else:
                        self.device_cache.remove_device_for_capability_and_attribute(capability, k, v, alias)

        self.device_cache.set_last_device_attr_value(capability, alias, event.attr_key, event.attr_value)
        self.device_cache.set_last_device_attr_timestamp(capability, alias, event.attr_key, event.attr_value, event.timestamp)
