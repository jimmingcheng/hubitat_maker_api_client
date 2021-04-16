from collections import defaultdict
from typing import Optional
from typing import Set


class DeviceCache:
    # Cache mutators
    def clear(self) -> None:
        raise NotImplementedError

    def add_device_for_capability(self, capability: str, alias: str) -> None:
        raise NotImplementedError

    def remove_device_for_capability(self, capability: str, alias: str) -> None:
        raise NotImplementedError

    def add_device_for_capability_and_attribute(self, capability: str, attr_key: str, attr_value: str, alias: str) -> None:
        raise NotImplementedError

    def remove_device_for_capability_and_attribute(self, capability: str, attr_key: str, attr_value: str, alias: str) -> None:
        raise NotImplementedError

    def set_last_device_attr_value(self, capability: Optional[str], alias: str, attr_key: str, attr_value: Optional[str]) -> None:
        raise NotImplementedError

    def set_capabilities_for_device_id(self, device_id: int, capabilities: Set[str]) -> None:
        raise NotImplementedError

    def set_last_device_attr_timestamp(self, capability: Optional[str], alias: str, attr_key: str, attr_value: Optional[str], timestamp: int) -> None:
        raise NotImplementedError

    # Cache accessors

    def get_devices_by_capability(self, capability: str) -> Set[str]:
        raise NotImplementedError

    def get_devices_by_capability_and_attribute(self, capability: str, attr_key: str, attr_value: str) -> Set[str]:
        raise NotImplementedError

    def get_capabilities_for_device_id(self, device_id: int) -> Set[str]:
        raise NotImplementedError

    def get_last_device_attr_value(self, capability: Optional[str], alias: str, attr_key: str) -> str:
        raise NotImplementedError

    def get_last_device_attr_timestamp(self, capability: Optional[str], alias: str, attr_key: str, attr_value: Optional[str]) -> int:
        raise NotImplementedError


class InMemoryDeviceCache(DeviceCache):
    def clear(self):
        self.cached_cap_to_aliases = defaultdict(set)
        self.cached_cap_to_attr_to_aliases = defaultdict(set)
        self.cached_cap_to_alias_to_attr_to_timestamp = dict()
        self.cached_cap_to_alias_to_attr = dict()
        self.cached_device_id_to_capabilities = dict()

    def add_device_for_capability(self, capability: str, alias: str) -> None:
        self.cached_cap_to_aliases[capability].add(alias)

    def remove_device_for_capability(self, capability: str, alias: str) -> None:
        self.cached_cap_to_aliases[capability].remove(alias)

    def add_device_for_capability_and_attribute(self, capability: str, attr_key: str, attr_value: str, alias: str) -> None:
        k = (capability, attr_key, attr_value)
        self.cached_cap_to_attr_to_aliases[k].add(alias)

    def remove_device_for_capability_and_attribute(self, capability: str, attr_key: str, attr_value: str, alias: str) -> None:
        k = (capability, attr_key, attr_value)
        self.cached_cap_to_attr_to_aliases[k].remove(alias)

    def set_capabilities_for_device_id(self, device_id: int, capabilities: Set[str]) -> None:
        self.cached_device_id_to_capabilities[device_id] = capabilities

    def set_last_device_attr_value(self, capability: Optional[str], alias: str, attr_key: str, attr_value: Optional[str]) -> None:
        k = (capability, alias, attr_key)
        self.cached_cap_to_alias_to_attr[k] = attr_value

    def set_last_device_attr_timestamp(self, capability: Optional[str], alias: str, attr_key: str, attr_value: Optional[str], timestamp: int) -> None:
        k = (capability, alias, attr_key, attr_value)
        self.cached_cap_to_alias_to_attr_to_timestamp[k] = timestamp

    # Cache accessors

    def get_devices_by_capability(self, capability: str) -> Set[str]:
        return self.cached_cap_to_aliases[capability]

    def get_devices_by_capability_and_attribute(self, capability: str, attr_key: str, attr_value: str) -> Set[str]:
        k = (capability, attr_key, attr_value)
        return self.cached_cap_to_attr_to_aliases.get(k)

    def get_capabilities_for_device_id(self, device_id: int) -> Set[str]:
        return self.cached_device_id_to_capabilities.get(device_id, set())

    def get_last_device_attr_value(self, capability: Optional[str], alias: str, attr_key: str) -> str:
        k = (capability, alias, attr_key)
        return self.cached_cap_to_alias_to_attr.get(k)

    def get_last_device_attr_timestamp(self, capability: Optional[str], alias: str, attr_key: Optional[str], attr_value: Optional[str]) -> int:
        k = (capability, alias, attr_key, attr_value)
        return self.cached_cap_to_alias_to_attr_to_timestamp.get(k)
