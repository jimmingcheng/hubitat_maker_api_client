import inspect
import sys
from typing import NewType


CapabilityName = NewType('CapabilityName', str)
CapabilityAttrKey = NewType('CapabilityAttrKey', str)


def supported_capabilities() -> list[type['Capability']]:
    current_module = sys.modules[__name__]
    subclasses = [
        cls for name, cls in inspect.getmembers(current_module, inspect.isclass)
        if issubclass(cls, Capability) and cls is not Capability
    ]
    return subclasses


class Capability:
    name: CapabilityName
    attr_keys: list[CapabilityAttrKey]


class BatteryCapability:
    name = CapabilityName('Battery')
    attr_keys = [CapabilityAttrKey('battery')]


class ContactSensorCapability:
    name = CapabilityName('ContactSensor')
    attr_keys = [CapabilityAttrKey('contact')]


class DoorControlCapability:
    name = CapabilityName('DoorControl')
    attr_keys = [CapabilityAttrKey('door')]


class EnergyMeterCapability:
    name = CapabilityName('EnergyMeter')
    attr_keys = [CapabilityAttrKey('energy')]


class IlluminanceMeasurementCapability:
    name = CapabilityName('IlluminanceMeasurement')
    attr_keys = [CapabilityAttrKey('illuminance')]


class LockCapability:
    name = CapabilityName('Lock')
    attr_keys = [CapabilityAttrKey('lock')]


class MotionSensorCapability:
    name = CapabilityName('MotionSensor')
    attr_keys = [CapabilityAttrKey('motion')]


class PowerMeterCapability:
    name = CapabilityName('PowerMeter')
    attr_keys = [CapabilityAttrKey('power')]


class PresenceSensorCapability:
    name = CapabilityName('PresenceSensor')
    attr_keys = [CapabilityAttrKey('presence')]


class SpeechSynthesisCapability:
    name = CapabilityName('SpeechSynthesis')
    attr_keys = [CapabilityAttrKey('speech')]


class SwitchCapability:
    name = CapabilityName('Switch')
    attr_keys = [CapabilityAttrKey('switch')]


class SwitchLevelCapability:
    name = CapabilityName('SwitchLevel')
    attr_keys = [CapabilityAttrKey('level')]
