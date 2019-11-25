import json
import mock
import requests_mock
import pytest

from hubitat_maker_api_client.client import HubitatAPIClient
from hubitat_maker_api_client.constants import HSM_STATE_ARMED_AWAY
from hubitat_maker_api_client.constants import HSM_STATE_DISARMED
from hubitat_maker_api_client.easy_client_with_listener import HubitatEasyClientWithListener
from hubitat_maker_api_client.event_socket import HubitatEvent


FAKE_APP_ID = 'fake_app_id'
FAKE_ACCESS_TOKEN = 'fake_access_token'
FAKE_HUB_ID = 'fake_hub_id'

FAKE_URL_PREFIX = 'https://cloud.hubitat.com/api/{}/apps/{}'.format(
    FAKE_HUB_ID,
    FAKE_APP_ID,
)

FAKE_URL_DEVICES_ALL = '{}/devices/all?access_token={}'.format(
    FAKE_URL_PREFIX,
    FAKE_ACCESS_TOKEN,
)

FAKE_URL_MODES = '{}/modes?access_token={}'.format(
    FAKE_URL_PREFIX,
    FAKE_ACCESS_TOKEN,
)

FAKE_URL_HSM = '{}/hsm?access_token={}'.format(
    FAKE_URL_PREFIX,
    FAKE_ACCESS_TOKEN,
)

FAKE_SWITCH_ON = {
    'id': '1',
    'label': 'Kitchen Ceiling',
    'capabilities': ['Switch'],
    'attributes': {
        'switch': 'on',
    },
}

FAKE_SWITCH_OFF = {
    'id': '2',
    'label': 'Porch Light',
    'capabilities': ['Switch'],
    'attributes': {
        'switch': 'off',
    },
}

FAKE_LUX_1 = {
    'id': '3',
    'label': 'Office',
    'capabilities': ['IlluminanceMeasurement'],
    'attributes': {
        'illuminance': '30',
    },
}

FAKE_LUX_2 = {
    'id': '4',
    'label': 'Porch',
    'capabilities': ['IlluminanceMeasurement'],
    'attributes': {
        'illuminance': '70',
    },
}

FAKE_DEVICES_ALL = [
    FAKE_SWITCH_ON,
    FAKE_SWITCH_OFF,
    FAKE_LUX_1,
    FAKE_LUX_2,
]

FAKE_ACTIVE_MODE = 'Day'
FAKE_INACTIVE_MODE = 'Night'
FAKE_MODES = [
    {'active': True, 'id': 1, 'name': FAKE_ACTIVE_MODE},
    {'active': False, 'id': 2, 'name': FAKE_INACTIVE_MODE},
]

FAKE_HSM = {
    'hsm': HSM_STATE_DISARMED,
}


def make_event(device, attr_key, attr_value):
    return HubitatEvent({
        'deviceId': device['id'],
        'displayName': device['label'],
        'name': attr_key,
        'value': attr_value,
    })


@pytest.fixture
def mock_client():
    return HubitatEasyClientWithListener(
        HubitatAPIClient(
            app_id=FAKE_APP_ID,
            access_token=FAKE_ACCESS_TOKEN,
            hub_id=FAKE_HUB_ID,
        )
    )


@pytest.fixture(autouse=True)
def mock_requests():
    with requests_mock.mock() as req_mock:
        req_mock.get(FAKE_URL_DEVICES_ALL, text=json.dumps(FAKE_DEVICES_ALL))
        req_mock.get(FAKE_URL_MODES, text=json.dumps(FAKE_MODES))
        req_mock.get(FAKE_URL_HSM, text=json.dumps(FAKE_HSM))
        yield req_mock


@pytest.fixture
def mock_time():
    with mock.patch('hubitat_maker_api_client.event_socket.time.time') as mock_func:
        yield mock_func


def test_update_from_hubitat_event(mock_client):
    assert mock_client.get_on_switches() == {FAKE_SWITCH_ON['label']}

    mock_client.update_from_hubitat_event(make_event(FAKE_SWITCH_ON, 'switch', 'off'))
    mock_client.update_from_hubitat_event(make_event(FAKE_SWITCH_OFF, 'switch', 'on'))

    assert mock_client.get_on_switches() == {FAKE_SWITCH_OFF['label']}


def test_update_from_hubitat_event_mode(mock_client):
    assert mock_client.get_mode() == FAKE_ACTIVE_MODE

    mock_client.update_from_hubitat_event(
        HubitatEvent({
            'deviceId': 'home',
            'displayName': 'Home',
            'name': 'mode',
            'value': FAKE_INACTIVE_MODE,
        })
    )

    assert mock_client.get_mode() == FAKE_INACTIVE_MODE


def test_update_from_hubitat_event_hsm(mock_client):
    assert mock_client.get_hsm() == HSM_STATE_DISARMED

    mock_client.update_from_hubitat_event(
        HubitatEvent({
            'deviceId': None,
            'displayName': None,
            'name': 'hsmStatus',
            'value': HSM_STATE_ARMED_AWAY,
        })
    )

    assert mock_client.get_hsm() == HSM_STATE_ARMED_AWAY


def test_update_from_hubitat_event_lux(mock_client):
    lux_1 = int(FAKE_LUX_1['attributes']['illuminance'])
    lux_2 = lux_1 + 1
    assert mock_client.get_lux_readings()[FAKE_LUX_1['label']] == lux_1

    mock_client.update_from_hubitat_event(make_event(FAKE_LUX_1, 'illuminance', str(lux_2)))

    assert mock_client.get_lux_readings()[FAKE_LUX_1['label']] == lux_2


def test_get_last_device_activity(mock_client, mock_time):
    fake_timestamp = 1575573796
    mock_time.return_value = fake_timestamp

    assert mock_client.get_last_device_activity(FAKE_SWITCH_OFF['label'], 'switch', 'off') is None
    assert mock_client.get_last_device_activity(FAKE_SWITCH_OFF['label'], 'switch', 'on') is None

    mock_client.update_from_hubitat_event(make_event(FAKE_SWITCH_OFF, 'switch', 'on'))

    assert mock_client.get_last_device_activity(FAKE_SWITCH_OFF['label'], 'switch', 'off') is None
    assert mock_client.get_last_device_activity(FAKE_SWITCH_OFF['label'], 'switch', 'on') == fake_timestamp
