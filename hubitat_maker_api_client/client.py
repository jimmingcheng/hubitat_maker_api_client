from cachetools.func import ttl_cache
from collections import defaultdict
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

from hubitat_maker_api_client.api_client import HubitatAPIClient
from hubitat_maker_api_client.errors import DeviceNotFoundError
from hubitat_maker_api_client.errors import MultipleDevicesFoundError


class HubitatClient():
    def __init__(
        self,
        api_client: HubitatAPIClient,
        alias_key: str = 'label'
    ):
        self.api_client = api_client
        self.alias_key = alias_key

    @ttl_cache(ttl=86400)
    def _get_capability_to_alias_to_device_ids(self) -> Dict[str, Dict[str, List[int]]]:
        devices = self.api_client.get_devices()
        capability_to_alias_to_device_ids: Dict[str, Dict[str, List[int]]] = defaultdict(lambda: defaultdict(list))
        for device in devices:
            for capability in device['capabilities']:
                alias = device[self.alias_key]
                device_id = int(device['id'])
                capability_to_alias_to_device_ids[capability][alias].append(device_id)
        return capability_to_alias_to_device_ids

    @ttl_cache(ttl=86400)
    def _get_mode_name_to_id(self) -> Dict[str, int]:
        return {
            mode['name']: mode['id']
            for mode in self.api_client.get_modes()
        }

    def _get_capability_to_alias_to_attributes(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        return self._get_capability_to_alias_to_attributes_from_api()

    @ttl_cache(ttl=2)
    def _get_capability_to_alias_to_attributes_from_api(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        devices = self.api_client.get_devices()
        capability_to_alias_to_attributes: Dict[str, Dict[str, dict]] = defaultdict(lambda: defaultdict(dict))
        for device in devices:
            for capability in device['capabilities']:
                alias = device[self.alias_key]
                capability_to_alias_to_attributes[capability][alias] = device['attributes']
        return capability_to_alias_to_attributes

    def _get_alias_set(self, alias_list: List[str]) -> Set[str]:
        aliases = set()
        duplicate_aliases = set()
        for alias in alias_list:
            if alias in aliases:
                duplicate_aliases.add(alias)
            aliases.add(alias)
        if duplicate_aliases:
            raise MultipleDevicesFoundError(
                'Multiple devices found for ' + self.alias_key + ' ' + ','.join(map(str, duplicate_aliases))
            )
        return aliases

    def get_devices_by_capability(self, capability: str) -> Set[str]:
        alias_to_device_ids = self._get_capability_to_alias_to_device_ids().get(capability, {})
        aliases = list(alias_to_device_ids.keys())
        return self._get_alias_set(aliases)

    def get_devices_by_capability_and_attribute(self, capability: str, attr_key: str, attr_value: str) -> Set[str]:
        aliases = []
        for alias, attributes in self._get_capability_to_alias_to_attributes()[capability].items():
            if attributes[attr_key] == attr_value:
                aliases.append(alias)
        return self._get_alias_set(aliases)

    def get_capabilities_for_device_id(self, device_id: int) -> Set[str]:
        return {
            capability for capability in self.api_client.get_device(device_id)['capabilities']
            if type(capability) == str
        }

    def send_device_command_by_capability_and_alias(self, capability: str, alias: str, command: str) -> dict:
        matched_device_ids = self._get_capability_to_alias_to_device_ids().get(capability, {}).get(alias, [])
        if not matched_device_ids:
            raise DeviceNotFoundError('Unable to find {} {}'.format(capability, alias))
        elif len(matched_device_ids) > 1:
            raise MultipleDevicesFoundError('Multiple devices found for {} {}'.format(capability, alias))
        else:
            return self.api_client.send_device_command(matched_device_ids[0], command)

    # Mode
    def get_mode(self) -> Optional[str]:
        return self._get_mode_from_api()

    def _get_mode_from_api(self) -> Optional[str]:
        for mode in self.api_client.get_modes():
            if mode['active']:
                return mode['name']
        return None

    def set_mode(self, mode_name: str) -> None:
        mode_id = self._get_mode_name_to_id()[mode_name]
        self.api_client.set_mode(mode_id)

    # HSM (Hubitat Security Monitor)
    def get_hsm(self) -> str:
        return self._get_hsm_from_api()

    def _get_hsm_from_api(self) -> str:
        return self.api_client.get_hsm()['hsm']

    def set_hsm(self, hsm_state: str) -> None:
        self.api_client.set_hsm(hsm_state)

    def send_hsm_command(self, command: str) -> None:
        self.api_client.send_hsm_command(command)

    # Device accessors
    def get_contact_sensors(self) -> Set[str]:
        return self.get_devices_by_capability('ContactSensor')

    def get_door_controls(self) -> Set[str]:
        return self.get_devices_by_capability('DoorControl')

    def get_locks(self) -> Set[str]:
        return self.get_devices_by_capability('Lock')

    def get_motion_sensors(self) -> Set[str]:
        return self.get_devices_by_capability('MotionSensor')

    def get_switches(self) -> Set[str]:
        return self.get_devices_by_capability('Switch')

    def get_users(self) -> Set[str]:
        return self.get_devices_by_capability('PresenceSensor')

    # Device accessors with attribute filters
    def get_open_doors(self) -> Set[str]:
        return self.get_devices_by_capability_and_attribute('ContactSensor', 'contact', 'open')

    def get_unlocked_doors(self) -> Set[str]:
        return self.get_devices_by_capability_and_attribute('Lock', 'lock', 'unlocked')

    def get_active_motion(self) -> Set[str]:
        return self.get_devices_by_capability_and_attribute('MotionSensor', 'motion', 'active')

    def get_on_switches(self) -> Set[str]:
        return self.get_devices_by_capability_and_attribute('Switch', 'switch', 'on')

    def get_present_users(self) -> Set[str]:
        return self.get_devices_by_capability_and_attribute('PresenceSensor', 'presence', 'present')

    # Device commands
    def open_door(self, alias: str) -> dict:
        return self.send_device_command_by_capability_and_alias('DoorControl', alias, 'open')

    def close_door(self, alias: str) -> dict:
        return self.send_device_command_by_capability_and_alias('DoorControl', alias, 'close')

    def lock_door(self, alias: str) -> dict:
        return self.send_device_command_by_capability_and_alias('Lock', alias, 'lock')

    def unlock_door(self, alias: str) -> dict:
        return self.send_device_command_by_capability_and_alias('Lock', alias, 'unlock')

    def turn_on_switch(self, alias: str) -> dict:
        return self.send_device_command_by_capability_and_alias('Switch', alias, 'on')

    def turn_off_switch(self, alias: str) -> dict:
        return self.send_device_command_by_capability_and_alias('Switch', alias, 'off')
