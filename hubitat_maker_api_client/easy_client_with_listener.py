from collections import defaultdict
from hubitat_maker_api_client.easy_client import HubitatEasyClient


ATTR_KEY_TO_CAPABILITY = {
    'contact': 'ContactSensor',
    'lock': 'Lock',
    'motion': 'MotionSensor',
    'switch': 'Switch',
    'presence': 'PresenceSensor',
    'illuminance': 'IlluminanceMeasurement',
}


class HubitatEasyClientWithListener(HubitatEasyClient):
    def __init__(
        self,
        api_client,
        alias_key='label',
        event_key='device_label',
    ):
        super(HubitatEasyClientWithListener, self).__init__(api_client, alias_key)
        self.event_key = event_key
        self.cached_capability_to_alias_to_attr_timestamps = defaultdict(
            lambda: defaultdict(lambda: defaultdict(dict))
        )
        self.cached_capability_to_alias_to_attributes = None
        self.cached_mode = None
        self.cached_hsm = None

    def _get_capability_to_alias_to_attributes(self):
        if self.cached_capability_to_alias_to_attributes is None:
            self.cached_capability_to_alias_to_attributes = self._get_capability_to_alias_to_attributes_from_api()
        return self.cached_capability_to_alias_to_attributes

    def _get_capability_to_alias_to_attr_timestamps(self):
        return self.cached_capability_to_alias_to_attr_timestamps

    def get_mode(self):
        if self.cached_mode is None:
            self.cached_mode = self._get_mode_from_api()
        return self.cached_mode

    def get_hsm(self):
        if self.cached_hsm is None:
            self.cached_hsm = self._get_hsm_from_api()
        return self.cached_hsm

    def update_from_hubitat_event(self, event):
        alias = getattr(event, self.event_key)
        k = event.attr_key
        v = event.attr_value
        if k == 'mode':
            self.cached_mode = v
        elif k == 'hsmStatus':
            self.cached_hsm = v
        else:
            capability = ATTR_KEY_TO_CAPABILITY.get(k)
            if capability:
                self._get_capability_to_alias_to_attributes()[capability][alias][k] = v
                self._get_capability_to_alias_to_attr_timestamps()[capability][alias][k][v] = event.timestamp

    def get_last_device_activity(self, alias, attr_key, attr_value):
        capability = ATTR_KEY_TO_CAPABILITY.get(attr_key)
        return self.cached_capability_to_alias_to_attr_timestamps[capability][alias][attr_key].get(attr_value)
