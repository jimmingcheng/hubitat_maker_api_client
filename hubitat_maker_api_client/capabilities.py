import inspect
import sys
from typing import NewType


CapabilityName = NewType('CapabilityName', str)
CapabilityAttrKey = NewType('CapabilityAttrKey', str)


def supported_capabilities() -> list[type['Capability']]:
    current_module = sys.modules['hubitat_maker_api_client.capabilities']
    subclasses = [
        cls for name, cls in inspect.getmembers(current_module, inspect.isclass)
        if issubclass(cls, Capability) and cls is not Capability
    ]
    return subclasses


class Capability:
    name: CapabilityName
    attr_keys: list[CapabilityAttrKey]


class BatteryCapability(Capability):
    name = CapabilityName('Battery')
    attr_keys = [CapabilityAttrKey('battery')]


class ContactSensorCapability(Capability):
    name = CapabilityName('ContactSensor')
    attr_keys = [CapabilityAttrKey('contact')]


class DoorControlCapability(Capability):
    name = CapabilityName('DoorControl')
    attr_keys = [CapabilityAttrKey('door')]


class EnergyMeterCapability(Capability):
    name = CapabilityName('EnergyMeter')
    attr_keys = [CapabilityAttrKey('energy')]


class IlluminanceMeasurementCapability(Capability):
    name = CapabilityName('IlluminanceMeasurement')
    attr_keys = [CapabilityAttrKey('illuminance')]


class LockCapability(Capability):
    name = CapabilityName('Lock')
    attr_keys = [CapabilityAttrKey('lock')]


class MotionSensorCapability(Capability):
    name = CapabilityName('MotionSensor')
    attr_keys = [CapabilityAttrKey('motion')]


class PowerMeterCapability(Capability):
    name = CapabilityName('PowerMeter')
    attr_keys = [CapabilityAttrKey('power')]


class PresenceSensorCapability(Capability):
    name = CapabilityName('PresenceSensor')
    attr_keys = [CapabilityAttrKey('presence')]


class SpeechSynthesisCapability(Capability):
    name = CapabilityName('SpeechSynthesis')
    attr_keys = [CapabilityAttrKey('speech')]


class SwitchCapability(Capability):
    name = CapabilityName('Switch')
    attr_keys = [CapabilityAttrKey('switch')]


class SwitchLevelCapability(Capability):
    name = CapabilityName('SwitchLevel')
    attr_keys = [CapabilityAttrKey('level')]
