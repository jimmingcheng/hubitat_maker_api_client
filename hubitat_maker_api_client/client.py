from cachetools.func import ttl_cache
from collections import defaultdict
from typing import Any
from typing import NewType

from hubitat_maker_api_client.api_client import HubitatAPIClient
from hubitat_maker_api_client.errors import DeviceNotFoundError
from hubitat_maker_api_client.errors import MultipleDevicesFoundError


Capability = NewType('Capability', str)
DeviceAlias = NewType('DeviceAlias', str)


class HubitatClient():
    def __init__(
        self,
        api_client: HubitatAPIClient,
        alias_key: str = 'label'
    ):
        self.api_client = api_client
        self.alias_key = alias_key

    @ttl_cache(ttl=86400)
    def _get_capability_to_alias_to_device_ids(self) -> dict[Capability, dict[DeviceAlias, list[int]]]:
        devices = self.api_client.get_devices()
        capability_to_alias_to_device_ids: dict[Capability, dict[DeviceAlias, list[int]]] = defaultdict(lambda: defaultdict(list))
        for device in devices:
            for capability in device['capabilities']:
                alias = device[self.alias_key]
                device_id = int(device['id'])
                capability_to_alias_to_device_ids[capability][alias].append(device_id)
        return capability_to_alias_to_device_ids

    @ttl_cache(ttl=86400)
    def _get_capability_to_room_to_aliases(self) -> dict[Capability, dict[str | None, set[DeviceAlias]]]:
        capability_to_room_to_aliases: dict[Capability, dict[str | None, set[DeviceAlias]]] = defaultdict(lambda: defaultdict(set))
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

    def _get_capability_to_alias_to_attributes(self) -> dict[Capability, dict[DeviceAlias, dict[str, Any]]]:
        return self._get_capability_to_alias_to_attributes_from_api()

    @ttl_cache(ttl=2)
    def _get_capability_to_alias_to_attributes_from_api(self) -> dict[Capability, dict[DeviceAlias, dict[str, Any]]]:
        devices = self.api_client.get_devices()
        capability_to_alias_to_attributes: dict[Capability, dict[DeviceAlias, dict]] = defaultdict(lambda: defaultdict(dict))
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

    def get_devices_by_capability(self, capability: Capability) -> set[DeviceAlias]:
        alias_to_device_ids = self._get_capability_to_alias_to_device_ids().get(capability, {})
        aliases = list(alias_to_device_ids.keys())
        return self._get_alias_set(aliases)

    def get_devices_by_capability_and_room(self, capability: Capability, room: str | None) -> set[DeviceAlias]:
        return self._get_capability_to_room_to_aliases()[capability][room]

    def get_devices_by_capability_and_attribute(self, capability: Capability, attr_key: str, attr_value: str) -> set[DeviceAlias]:
        aliases = []
        for alias, attributes in self._get_capability_to_alias_to_attributes()[capability].items():
            if attributes[attr_key] == attr_value:
                aliases.append(alias)
        return self._get_alias_set(aliases)

    def get_capabilities_for_device_id(self, device_id: int) -> set[Capability]:
        return {
            capability for capability in self.api_client.get_device(device_id)['capabilities']
            if type(capability) == Capability
        }

    def send_device_command_by_capability_and_alias(self, capability: Capability, alias: DeviceAlias, command: str, *secondary_values) -> dict:
        matched_device_ids = self._get_capability_to_alias_to_device_ids().get(capability, {}).get(alias, [])
        if not matched_device_ids:
            raise DeviceNotFoundError('Unable to find {} {}'.format(capability, alias))
        elif len(matched_device_ids) > 1:
            raise MultipleDevicesFoundError('Multiple devices found for {} {}'.format(capability, alias))
        else:
            return self.api_client.send_device_command(matched_device_ids[0], command, *secondary_values)

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
        return self.get_devices_by_capability(Capability('ContactSensor'))

    def get_door_controls(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability(Capability('DoorControl'))

    def get_locks(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability(Capability('Lock'))

    def get_motion_sensors(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability(Capability('MotionSensor'))

    def get_switches(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability(Capability('Switch'))

    def get_users(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability(Capability('PresenceSensor'))

    # Device accessors with attribute filters
    def get_open_doors(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability_and_attribute(Capability('ContactSensor'), 'contact', 'open')

    def get_unlocked_doors(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability_and_attribute(Capability('Lock'), 'lock', 'unlocked')

    def get_active_motion(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability_and_attribute(Capability('MotionSensor'), 'motion', 'active')

    def get_on_switches(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability_and_attribute(Capability('Switch'), 'switch', 'on')

    def get_present_users(self) -> set[DeviceAlias]:
        return self.get_devices_by_capability_and_attribute(Capability('PresenceSensor'), 'presence', 'present')

    # Device commands
    def open_door(self, alias: DeviceAlias) -> dict:
        return self.send_device_command_by_capability_and_alias(Capability('DoorControl'), alias, 'open')

    def close_door(self, alias: DeviceAlias) -> dict:
        return self.send_device_command_by_capability_and_alias(Capability('DoorControl'), alias, 'close')

    def lock_door(self, alias: DeviceAlias) -> dict:
        return self.send_device_command_by_capability_and_alias(Capability('Lock'), alias, 'lock')

    def unlock_door(self, alias: DeviceAlias) -> dict:
        return self.send_device_command_by_capability_and_alias(Capability('Lock'), alias, 'unlock')

    def turn_on_switch(self, alias: DeviceAlias) -> dict:
        return self.send_device_command_by_capability_and_alias(Capability('Switch'), alias, 'on')

    def turn_off_switch(self, alias: DeviceAlias) -> dict:
        return self.send_device_command_by_capability_and_alias(Capability('Switch'), alias, 'off')

    def arrived(self, alias: DeviceAlias) -> dict:
        return self.send_device_command_by_capability_and_alias(Capability('PresenceSensor'), alias, 'arrived')

    def departed(self, alias: DeviceAlias) -> dict:
        return self.send_device_command_by_capability_and_alias(Capability('PresenceSensor'), alias, 'departed')

    def set_lux(self, alias: DeviceAlias, lux: int) -> dict:
        return self.send_device_command_by_capability_and_alias(Capability('IlluminanceMeasurement'), alias, 'setLux', lux)

    # Echo speaks
    def echo_set_volume_and_speak(self, alias: DeviceAlias, volume: int, message: str) -> dict:
        return self.send_device_command_by_capability_and_alias(Capability('SpeechSynthesis'), alias, 'setVolumeAndSpeak', volume, message)

    def echo_voice_cmd_as_text(self, alias: DeviceAlias, message: str) -> dict:
        return self.send_device_command_by_capability_and_alias(Capability('SpeechSynthesis'), alias, 'voiceCmdAsText', message)

    def echo_parallel_speak(self, alias: DeviceAlias, message: str) -> dict:
        return self.send_device_command_by_capability_and_alias(Capability('SpeechSynthesis'), alias, 'parallelSpeak', message)

    def echo_set_volume_speak_and_restore(self, alias: DeviceAlias, volume: int, message: str, restore_volume: int) -> dict:
        return self.send_device_command_by_capability_and_alias(Capability('SpeechSynthesis'), alias, 'setVolumeSpeakAndRestore', volume, message, restore_volume)

    def echo_play_announcement(self, alias: DeviceAlias, message: str) -> dict:
        return self.send_device_command_by_capability_and_alias(Capability('SpeechSynthesis'), alias, 'playAnnouncement', message)

    def echo_play_announcement_all(self, alias: DeviceAlias, message: str) -> dict:
        return self.send_device_command_by_capability_and_alias(Capability('SpeechSynthesis'), alias, 'playAnnouncementAll', message)

    def echo_room_announce(self, room: str, message: str) -> dict:
        for echo in self.get_devices_by_capability_and_room(Capability('SpeechSynthesis'), room):
            self.echo_play_announcement(echo, message)
        return {}

    def echo_room_speak(self, room: str, message: str) -> dict:
        for echo in self.get_devices_by_capability_and_room(Capability('SpeechSynthesis'), room):
            self.echo_parallel_speak(echo, message)
        return {}
