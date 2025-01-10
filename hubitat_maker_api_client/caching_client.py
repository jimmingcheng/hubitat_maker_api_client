from datetime import datetime

from hubitat_maker_api_client.api_client import HubitatAPIClient
from hubitat_maker_api_client.capabilities import CapabilityAttrKey
from hubitat_maker_api_client.capabilities import CapabilityName
from hubitat_maker_api_client.capabilities import ContactSensorCapability
from hubitat_maker_api_client.capabilities import EnergyMeterCapability
from hubitat_maker_api_client.capabilities import IlluminanceMeasurementCapability
from hubitat_maker_api_client.capabilities import LockCapability
from hubitat_maker_api_client.capabilities import MotionSensorCapability
from hubitat_maker_api_client.capabilities import PowerMeterCapability
from hubitat_maker_api_client.capabilities import PresenceSensorCapability
from hubitat_maker_api_client.capabilities import SwitchCapability
from hubitat_maker_api_client.client import DeviceAlias
from hubitat_maker_api_client.client import HubitatClient
from hubitat_maker_api_client.client import RoomName
from hubitat_maker_api_client.device_cache import DeviceCache
from hubitat_maker_api_client.event_socket import HubitatEvent


ATTR_KEY_TO_CAPABILITY = {
    'battery': MotionSensorCapability.name,
    'contact': ContactSensorCapability.name,
    'energy': EnergyMeterCapability.name,
    'illuminance': IlluminanceMeasurementCapability.name,
    'lock': LockCapability.name,
    'motion': MotionSensorCapability.name,
    'power': PowerMeterCapability.name,
    'presence': PresenceSensorCapability.name,
    'switch': SwitchCapability.name,
}


SUPPORTED_ACCESSOR_ATTRS = [
    (ContactSensorCapability.name, 'contact', 'open'),
    (LockCapability.name, 'lock', 'unlocked'),
    (MotionSensorCapability.name, 'motion', 'active'),
    (SwitchCapability.name, 'switch', 'on'),
    (PresenceSensorCapability.name, 'presence', 'present'),
]


UNSUPPORTED_ATTR_KEYS = ['dataType', 'values']
ATTR_KEYS_WITH_NUMERIC_VALS = [
    'battery',
    'illuminance',
    'ultravioletIndex',
    'temperature',
    'humidity',
    'energy',
    'power',
]


def date_to_timestamp(date_str: str) -> int:
    return int(datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z').timestamp())


class HubitatCachingClient(HubitatClient):
    def __init__(
        self,
        api_client: HubitatAPIClient,
        device_cache: DeviceCache,
        alias_key: str = 'label',
        event_key: str = 'device_label',
        cache_writes_enabled: bool = True,
    ):
        super(HubitatCachingClient, self).__init__(api_client, alias_key)
        self.device_cache = device_cache
        self.event_key = event_key
        self.cache_writes_enabled = cache_writes_enabled

        if self.cache_writes_enabled:
            self.device_cache.clear()
            self.load_cache()

    def load_cache(self) -> None:
        self.device_cache.set_last_device_attr_value(None, DeviceAlias('Home'), 'mode', self._get_mode_from_api())
        self.device_cache.set_last_device_attr_value(None, DeviceAlias('Home'), 'hsmStatus', self._get_hsm_from_api())

        devices = self.api_client.get_devices()
        for device in devices:
            alias = device[self.alias_key]

            self.device_cache.set_capabilities_for_device_id(device['id'], set(device['capabilities']))

            for capability in device['capabilities']:
                self.device_cache.add_device_for_capability(capability, alias)
                self.device_cache.add_device_for_capability_and_room(capability, device['room'], alias)

                for k, v in device['attributes'].items():
                    if k not in UNSUPPORTED_ATTR_KEYS:
                        self.device_cache.add_device_for_capability_and_attribute(capability, k, v, alias)
                        self.device_cache.set_last_device_attr_value(capability, alias, k, v)
                        if device['date']:
                            timestamp = date_to_timestamp(device['date'])
                            if k in ATTR_KEYS_WITH_NUMERIC_VALS:
                                self.device_cache.set_last_device_attr_timestamp(capability, alias, k, None, timestamp)
                            else:
                                self.device_cache.set_last_device_attr_timestamp(capability, alias, k, v, timestamp)

    def get_devices_by_capability(self, capability: CapabilityName) -> set[DeviceAlias]:
        return self.device_cache.get_devices_by_capability(capability)

    def get_devices_by_capability_and_room(self, capability: CapabilityName, room: RoomName | None) -> set[DeviceAlias]:
        return self.device_cache.get_devices_by_capability_and_room(capability, room)

    def get_devices_by_capability_and_attribute(self, capability: CapabilityName, attr_key: CapabilityAttrKey, attr_value: str) -> set[DeviceAlias]:
        return self.device_cache.get_devices_by_capability_and_attribute(capability, attr_key, attr_value)

    def get_capabilities_for_device_id(self, device_id: int) -> set[CapabilityName]:
        return self.device_cache.get_capabilities_for_device_id(device_id)

    # Device accessors

    def get_mode(self) -> str | None:
        return self.device_cache.get_last_device_attr_value(None, DeviceAlias('Home'), 'mode')

    def get_hsm(self) -> str | None:
        return self.device_cache.get_last_device_attr_value(None, DeviceAlias('Home'), 'hsmStatus')

    def get_last_device_value(self, alias: DeviceAlias, attr_key: CapabilityAttrKey, capability: CapabilityName | None = None) -> str | None:
        if not capability:
            capability = ATTR_KEY_TO_CAPABILITY.get(attr_key)
        return self.device_cache.get_last_device_attr_value(capability, alias, attr_key)

    def get_last_device_timestamp(self, alias: DeviceAlias, attr_key: CapabilityAttrKey, attr_value: str, capability: CapabilityName | None = None) -> int | None:
        if not capability:
            capability = ATTR_KEY_TO_CAPABILITY.get(attr_key)
        return self.device_cache.get_last_device_attr_timestamp(capability, alias, attr_key, attr_value)

    def update_from_hubitat_event(self, event: HubitatEvent) -> None:
        if not self.cache_writes_enabled:
            return

        alias = getattr(event, self.event_key)

        capabilities = self.get_capabilities_for_device_id(event.device_id) or {None}  # type: ignore

        for capability in capabilities:
            for cap, k, v in SUPPORTED_ACCESSOR_ATTRS:
                if cap == capability and k == event.attr_key:
                    if v == event.attr_value:
                        self.device_cache.add_device_for_capability_and_attribute(capability, k, v, alias)
                    else:
                        self.device_cache.remove_device_for_capability_and_attribute(capability, k, v, alias)

            self.device_cache.set_last_device_attr_value(capability, alias, event.attr_key, event.attr_value)
            if event.attr_key in ATTR_KEYS_WITH_NUMERIC_VALS:
                self.device_cache.set_last_device_attr_timestamp(capability, alias, event.attr_key, None, event.timestamp)
            else:
                self.device_cache.set_last_device_attr_timestamp(capability, alias, event.attr_key, event.attr_value, event.timestamp)
