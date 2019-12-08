from collections import defaultdict


class DeviceCache:
    # Cache mutators
    def clear(self):
        raise NotImplementedError

    def add_device_for_capability(self, capability, alias):
        raise NotImplementedError

    def remove_device_for_capability(self, capability, alias):
        raise NotImplementedError

    def add_device_for_capability_and_attribute(self, capability, attr_key, attr_value, alias):
        raise NotImplementedError

    def remove_device_for_capability_and_attribute(self, capability, attr_key, attr_value, alias):
        raise NotImplementedError

    def set_last_device_attr_value(self, capability, alias, attr_key, attr_value):
        raise NotImplementedError

    def set_last_device_attr_timestamp(self, capability, alias, attr_key, attr_value, timestamp):
        raise NotImplementedError

    # Cache accessors

    def get_devices_by_capability(self, capability):
        raise NotImplementedError

    def get_devices_by_capability_and_attribute(self, capability, attr_key, attr_value):
        raise NotImplementedError

    def get_last_device_attr_value(self, capability, alias, attr_key):
        raise NotImplementedError

    def get_last_device_attr_timestamp(self, capability, alias, attr_key, attr_value):
        raise NotImplementedError


class InMemoryDeviceCache(DeviceCache):
    def clear(self):
        self.cached_cap_to_aliases = defaultdict(set)
        self.cached_cap_to_attr_to_aliases = defaultdict(set)
        self.cached_cap_to_alias_to_attr_to_timestamp = dict()
        self.cached_cap_to_alias_to_attr = dict()

    def add_device_for_capability(self, capability, alias):
        self.cached_cap_to_aliases[capability].add(alias)

    def remove_device_for_capability(self, capability, alias):
        self.cached_cap_to_aliases[capability].remove(alias)

    def add_device_for_capability_and_attribute(self, capability, attr_key, attr_value, alias):
        k = (capability, attr_key, attr_value)
        self.cached_cap_to_attr_to_aliases[k].add(alias)

    def remove_device_for_capability_and_attribute(self, capability, attr_key, attr_value, alias):
        k = (capability, attr_key, attr_value)
        self.cached_cap_to_attr_to_aliases[k].remove(alias)

    def set_last_device_attr_value(self, capability, alias, attr_key, attr_value):
        k = (capability, alias, attr_key)
        self.cached_cap_to_alias_to_attr[k] = attr_value

    def set_last_device_attr_timestamp(self, capability, alias, attr_key, attr_value, timestamp):
        k = (capability, alias, attr_key, attr_value)
        self.cached_cap_to_alias_to_attr_to_timestamp[k] = timestamp

    # Cache accessors

    def get_devices_by_capability(self, capability):
        return self.cached_cap_to_aliases[capability]

    def get_devices_by_capability_and_attribute(self, capability, attr_key, attr_value):
        k = (capability, attr_key, attr_value)
        return self.cached_cap_to_attr_to_aliases.get(k)

    def get_last_device_attr_value(self, capability, alias, attr_key):
        k = (capability, alias, attr_key)
        return self.cached_cap_to_alias_to_attr.get(k)

    def get_last_device_attr_timestamp(self, capability, alias, attr_key, attr_value):
        k = (capability, alias, attr_key, attr_value)
        return self.cached_cap_to_alias_to_attr_to_timestamp.get(k)
