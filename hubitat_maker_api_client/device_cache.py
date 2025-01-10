from abc import ABC
from abc import abstractmethod
from collections import defaultdict

from hubitat_maker_api_client.client import Capability
from hubitat_maker_api_client.client import DeviceAlias


class DeviceCache(ABC):
    # Cache mutators

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def add_device_for_capability(self, capability: Capability, alias: DeviceAlias) -> None:
        pass

    @abstractmethod
    def remove_device_for_capability(self, capability: Capability, alias: DeviceAlias) -> None:
        pass

    @abstractmethod
    def add_device_for_capability_and_room(self, capability: Capability, room: str | None, alias: DeviceAlias) -> None:
        pass

    @abstractmethod
    def remove_device_for_capability_and_room(self, capability: Capability, room: str | None, alias: DeviceAlias) -> None:
        pass

    @abstractmethod
    def add_device_for_capability_and_attribute(self, capability: Capability, attr_key: str, attr_value: str, alias: DeviceAlias) -> None:
        pass

    @abstractmethod
    def remove_device_for_capability_and_attribute(self, capability: Capability, attr_key: str, attr_value: str, alias: DeviceAlias) -> None:
        pass

    @abstractmethod
    def set_last_device_attr_value(self, capability: Capability | None, alias: DeviceAlias, attr_key: str, attr_value: str | None) -> None:
        pass

    @abstractmethod
    def set_capabilities_for_device_id(self, device_id: int, capabilities: set[Capability]) -> None:
        pass

    @abstractmethod
    def set_last_device_attr_timestamp(self, capability: Capability | None, alias: DeviceAlias, attr_key: str, attr_value: str | None, timestamp: int) -> None:
        pass

    # Cache accessors

    @abstractmethod
    def get_devices_by_capability(self, capability: Capability) -> set[DeviceAlias]:
        pass

    @abstractmethod
    def get_devices_by_capability_and_room(self, capability: Capability, room: str | None) -> set[DeviceAlias]:
        pass

    @abstractmethod
    def get_devices_by_capability_and_attribute(self, capability: Capability, attr_key: str, attr_value: str) -> set[DeviceAlias]:
        pass

    @abstractmethod
    def get_capabilities_for_device_id(self, device_id: int) -> set[Capability]:
        pass

    @abstractmethod
    def get_last_device_attr_value(self, capability: Capability | None, alias: DeviceAlias, attr_key: str) -> str | None:
        pass

    @abstractmethod
    def get_last_device_attr_timestamp(self, capability: Capability | None, alias: DeviceAlias, attr_key: str, attr_value: str | None) -> int | None:
        pass


class InMemoryDeviceCache(DeviceCache):
    def clear(self):
        self.cached_cap_to_aliases = defaultdict(set)
        self.cached_cap_to_room_to_aliases = defaultdict(lambda: defaultdict(set))
        self.cached_cap_to_attr_to_aliases = defaultdict(set)
        self.cached_cap_to_alias_to_attr_to_timestamp = dict()
        self.cached_cap_to_alias_to_attr = dict()
        self.cached_device_id_to_capabilities = dict()

    def add_device_for_capability(self, capability: Capability, alias: DeviceAlias) -> None:
        self.cached_cap_to_aliases[capability].add(alias)

    def remove_device_for_capability(self, capability: Capability, alias: DeviceAlias) -> None:
        self.cached_cap_to_aliases[capability].remove(alias)

    def add_device_for_capability_and_room(self, capability: Capability, room: str | None, alias: DeviceAlias) -> None:
        self.cached_cap_to_room_to_aliases[capability][room].add(alias)

    def remove_device_for_capability_and_room(self, capability: Capability, room: str | None, alias: DeviceAlias) -> None:
        self.cached_cap_to_room_to_aliases[capability][room].remove(alias)

    def add_device_for_capability_and_attribute(self, capability: Capability, attr_key: str, attr_value: str, alias: DeviceAlias) -> None:
        k = (capability, attr_key, attr_value)
        self.cached_cap_to_attr_to_aliases[k].add(alias)

    def remove_device_for_capability_and_attribute(self, capability: Capability, attr_key: str, attr_value: str, alias: DeviceAlias) -> None:
        k = (capability, attr_key, attr_value)
        self.cached_cap_to_attr_to_aliases[k].remove(alias)

    def set_capabilities_for_device_id(self, device_id: int, capabilities: set[Capability]) -> None:
        self.cached_device_id_to_capabilities[device_id] = capabilities

    def set_last_device_attr_value(self, capability: Capability | None, alias: DeviceAlias, attr_key: str, attr_value: str | None) -> None:
        k = (capability, alias, attr_key)
        self.cached_cap_to_alias_to_attr[k] = attr_value

    def set_last_device_attr_timestamp(self, capability: Capability | None, alias: DeviceAlias, attr_key: str, attr_value: str | None, timestamp: int) -> None:
        k = (capability, alias, attr_key, attr_value)
        self.cached_cap_to_alias_to_attr_to_timestamp[k] = timestamp

    # Cache accessors

    def get_devices_by_capability(self, capability: Capability) -> set[DeviceAlias]:
        return self.cached_cap_to_aliases[capability]

    def get_devices_by_capability_and_room(self, capability: Capability, room: str | None) -> set[DeviceAlias]:
        return self.cached_cap_to_room_to_aliases[capability]

    def get_devices_by_capability_and_attribute(self, capability: Capability, attr_key: str, attr_value: str) -> set[DeviceAlias]:
        k = (capability, attr_key, attr_value)
        return self.cached_cap_to_attr_to_aliases.get(k)

    def get_capabilities_for_device_id(self, device_id: int) -> set[Capability]:
        return self.cached_device_id_to_capabilities.get(device_id, set())

    def get_last_device_attr_value(self, capability: Capability | None, alias: DeviceAlias, attr_key: str) -> str | None:
        k = (capability, alias, attr_key)
        return self.cached_cap_to_alias_to_attr.get(k)

    def get_last_device_attr_timestamp(self, capability: Capability | None, alias: DeviceAlias, attr_key: str | None, attr_value: str | None) -> int | None:
        k = (capability, alias, attr_key, attr_value)
        return self.cached_cap_to_alias_to_attr_to_timestamp.get(k)
