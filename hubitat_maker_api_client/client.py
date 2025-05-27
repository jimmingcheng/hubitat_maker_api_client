from cachetools.func import ttl_cache
from collections import defaultdict
from typing import Any
from typing import NewType

from hubitat_maker_api_client.api_client import HubitatAPIClient
from hubitat_maker_api_client.capabilities import CapabilityAttrKey
from hubitat_maker_api_client.capabilities import CapabilityName
from hubitat_maker_api_client.capabilities import ContactSensorCapability
from hubitat_maker_api_client.capabilities import DoorControlCapability
from hubitat_maker_api_client.capabilities import IlluminanceMeasurementCapability
from hubitat_maker_api_client.capabilities import LockCapability
from hubitat_maker_api_client.capabilities import MotionSensorCapability
from hubitat_maker_api_client.capabilities import PresenceSensorCapability
from hubitat_maker_api_client.capabilities import SpeechSynthesisCapability
from hubitat_maker_api_client.capabilities import SwitchCapability
from hubitat_maker_api_client.capabilities import supported_capabilities
from hubitat_maker_api_client.errors import DeviceNotFoundError
from hubitat_maker_api_client.errors import MultipleDevicesFoundError


DeviceAlias = NewType('DeviceAlias', str)
RoomName = NewType('RoomName', str)


class HubitatClient():
    def __init__(
        self,
        api_client: HubitatAPIClient,
        alias_key: str = 'label'
    ):
        self.api_client = api_client
        self.alias_key = alias_key

    @ttl_cache(ttl=86400)
    def _get_capability_to_alias_to_device_ids(self) -> dict[CapabilityName, dict[DeviceAlias, list[int]]]:
        devices = self.api_client.get_devices()
        capability_to_alias_to_device_ids: dict[CapabilityName, dict[DeviceAlias, list[int]]] = defaultdict(lambda: defaultdict(list))
        for device in devices:
            for capability in device['capabilities']:
                alias = device[self.alias_key]
                device_id = int(device['id'])
                capability_to_alias_to_device_ids[capability][alias].append(device_id)
        return capability_to_alias_to_device_ids

    @ttl_cache(ttl=86400)
    def _get_capability_to_room_to_aliases(self) -> dict[CapabilityName, dict[RoomName | None, set[DeviceAlias]]]:
        capability_to_room_to_aliases: dict[CapabilityName, dict[RoomName | None, set[DeviceAlias]]] = defaultdict(lambda: defaultdict(set))
        for device in self.api_client.get_devices():
            for capability in device['capabilities']:
                alias = device[self.alias_key]
                room = device['room']
                capability_to_room_to_aliases[capability][room].add(alias)
        return capability_to_room_to_aliases

    @ttl_cache(ttl=86400)
    def _get_mode_name_to_id(self) -> dict[str, int]:
        return {
            mode['name']: mode['id']
            for mode in self.api_client.get_modes()
        }

    def _get_capability_to_alias_to_attributes(self) -> dict[CapabilityName, dict[DeviceAlias, dict[str, Any]]]:
        return self._get_capability_to_alias_to_attributes_from_api()

    @ttl_cache(ttl=2)
    def _get_capability_to_alias_to_attributes_from_api(self) -> dict[CapabilityName, dict[DeviceAlias, dict[str, Any]]]:
        devices = self.api_client.get_devices()
        capability_to_alias_to_attributes: dict[CapabilityName, dict[DeviceAlias, dict]] = defaultdict(lambda: defaultdict(dict))
        for device in devices:
            for capability in device['capabilities']:
                alias = device[self.alias_key]
                capability_to_alias_to_attributes[capability][alias] = device['attributes']
        return capability_to_alias_to_attributes

    def _get_alias_set(self, alias_list: list[DeviceAlias]) -> set[DeviceAlias]:
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

    def get_devices_by_capability(self, capability: CapabilityName) -> set[DeviceAlias]:
        alias_to_device_ids = self._get_capability_to_alias_to_device_ids().get(capability, {})
        aliases = list(alias_to_device_ids.keys())
        return self._get_alias_set(aliases)

    def get_devices_by_capability_and_room(self, capability: CapabilityName, room: RoomName | None) -> set[DeviceAlias]:
        return self._get_capability_to_room_to_aliases()[capability][room]

    def get_devices_by_capability_and_attribute(self, capability: CapabilityName, attr_key: CapabilityAttrKey, attr_value: str) -> set[DeviceAlias]:
        aliases = []
        for alias, attributes in self._get_capability_to_alias_to_attributes()[capability].items():
            if attributes[attr_key] == attr_value:
                aliases.append(alias)
        return self._get_alias_set(aliases)

    def get_capabilities_for_device_id(self, device_id: int) -> set[CapabilityName]:
        return {
            capability for capability in self.api_client.get_device(device_id)['capabilities']
            if type(capability) == CapabilityName
        }

    def _send_device_command_by_capability_and_alias(self, capability: CapabilityName, alias: DeviceAlias, command: str, *secondary_values) -> dict:
        matched_device_ids = self._get_capability_to_alias_to_device_ids().get(capability, {}).get(alias, [])
        if not matched_device_ids:
            raise DeviceNotFoundError('Unable to find {} {}'.format(capability, alias))
        elif len(matched_device_ids) > 1:
            raise MultipleDevicesFoundError('Multiple devices found for {} {}'.format(capability, alias))
        else:
            return self.api_client.send_device_command(matched_device_ids[0], command, *secondary_values)

    # Capabilities
    def get_capabilities(self, supported_only: bool = True) -> set[CapabilityName]:
        all_capabilities = set(self._get_capability_to_alias_to_device_ids().keys())
        if supported_only:
            return all_capabilities & {c.name for c in supported_capabilities()}
        else:
            return all_capabilities

    # Rooms
    def get_rooms(self) -> set[RoomName]:
        return {
            room
            for room_to_aliases in self._get_capability_to_room_to_aliases().values()
            for room in room_to_aliases.keys()
            if room
        }

    # Mode
    def get_mode(self) -> str | None:
        return self._get_mode_from_api()

    def _get_mode_from_api(self) -> str | None:
        for mode in self.api_client.get_modes():
            if mode['active']:
                return mode['name']
        return None

    def set_mode(self, mode_name: str) -> None:
        mode_id = self._get_mode_name_to_id()[mode_name]
        self.api_client.set_mode(mode_id)

    # HSM (Hubitat Security Monitor)
    def get_hsm(self) -> str | None:
        return self._get_hsm_from_api()

    def _get_hsm_from_api(self) -> str:
        return self.api_client.get_hsm()['hsm']

    def set_hsm(self, hsm_state: str) -> None:
        self.api_client.set_hsm(hsm_state)

    def send_hsm_command(self, command: str) -> None:
        self.api_client.send_hsm_command(command)

    # Device accessors
    def get_contact_sensors(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability(ContactSensorCapability.name)

    def get_door_controls(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability(DoorControlCapability.name)

    def get_locks(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability(LockCapability.name)

    def get_motion_sensors(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability(MotionSensorCapability.name)

    def get_switches(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability(SwitchCapability.name)

    def get_users(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability(PresenceSensorCapability.name)

    # Device accessors with attribute filters
    def get_open_doors(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability_and_attribute(ContactSensorCapability.name, CapabilityAttrKey('contact'), 'open')

    def get_unlocked_doors(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability_and_attribute(LockCapability.name, CapabilityAttrKey('lock'), 'unlocked')

    def get_active_motion(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability_and_attribute(MotionSensorCapability.name, CapabilityAttrKey('motion'), 'active')

    def get_on_switches(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability_and_attribute(SwitchCapability.name, CapabilityAttrKey('switch'), 'on')

    def get_present_users(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability_and_attribute(PresenceSensorCapability.name, CapabilityAttrKey('presence'), 'present')

    # Device commands
    def open_door(self, alias: DeviceAlias) -> dict:
        return self._send_device_command_by_capability_and_alias(DoorControlCapability.name, alias, 'open')

    def close_door(self, alias: DeviceAlias) -> dict:
        return self._send_device_command_by_capability_and_alias(DoorControlCapability.name, alias, 'close')

    def lock_door(self, alias: DeviceAlias) -> dict:
        return self._send_device_command_by_capability_and_alias(LockCapability.name, alias, 'lock')

    def unlock_door(self, alias: DeviceAlias) -> dict:
        return self._send_device_command_by_capability_and_alias(LockCapability.name, alias, 'unlock')

    def turn_on_switch(self, alias: DeviceAlias) -> dict:
        return self._send_device_command_by_capability_and_alias(SwitchCapability.name, alias, 'on')

    def turn_off_switch(self, alias: DeviceAlias) -> dict:
        return self._send_device_command_by_capability_and_alias(SwitchCapability.name, alias, 'off')

    def arrived(self, alias: DeviceAlias) -> dict:
        return self._send_device_command_by_capability_and_alias(PresenceSensorCapability.name, alias, 'arrived')

    def departed(self, alias: DeviceAlias) -> dict:
        return self._send_device_command_by_capability_and_alias(PresenceSensorCapability.name, alias, 'departed')

    def set_lux(self, alias: DeviceAlias, lux: int) -> dict:
        return self._send_device_command_by_capability_and_alias(IlluminanceMeasurementCapability.name, alias, 'setLux', lux)

    # Echo speaks
    def echo_set_volume_and_speak(self, alias: DeviceAlias, volume: int, message: str) -> dict:
        return self._send_device_command_by_capability_and_alias(SpeechSynthesisCapability.name, alias, 'setVolumeAndSpeak', volume, message)

    def echo_voice_cmd_as_text(self, alias: DeviceAlias, message: str) -> dict:
        return self._send_device_command_by_capability_and_alias(SpeechSynthesisCapability.name, alias, 'voiceCmdAsText', message)

    def echo_parallel_speak(self, alias: DeviceAlias, message: str) -> dict:
        return self._send_device_command_by_capability_and_alias(SpeechSynthesisCapability.name, alias, 'parallelSpeak', message)

    def echo_set_volume_speak_and_restore(self, alias: DeviceAlias, volume: int, message: str, restore_volume: int) -> dict:
        return self._send_device_command_by_capability_and_alias(SpeechSynthesisCapability.name, alias, 'setVolumeSpeakAndRestore', volume, message, restore_volume)

    def echo_play_announcement(self, alias: DeviceAlias, message: str) -> dict:
        return self._send_device_command_by_capability_and_alias(SpeechSynthesisCapability.name, alias, 'playAnnouncement', message)

    def echo_play_announcement_all(self, alias: DeviceAlias, message: str) -> dict:
        return self._send_device_command_by_capability_and_alias(SpeechSynthesisCapability.name, alias, 'playAnnouncementAll', message)

    # Intercom
    def get_intercom_rooms(self) -> set[RoomName]:
        return set([
            k for k in
            self._get_capability_to_room_to_aliases()[SpeechSynthesisCapability.name].keys()
            if k
        ])

    def intercom_speak(self, room: RoomName, message: str, chime_before_message: bool = False) -> None:
        message = message.replace(',', '...')  # Echo speaks can't handle commas well
        for echo in self.get_devices_by_capability_and_room(SpeechSynthesisCapability.name, room):
            if chime_before_message:
                self.echo_play_announcement(echo, message)
            else:
                self.echo_parallel_speak(echo, message)
