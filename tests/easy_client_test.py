import json
import requests_mock
import pytest

from hubitat_maker_api_client.client import HubitatAPIClient
from hubitat_maker_api_client.constants import HSM_STATE_DISARMED
from hubitat_maker_api_client.easy_client import HubitatEasyClient
from hubitat_maker_api_client.easy_client_with_listener import HubitatEasyClientWithListener


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


@pytest.fixture(params=[HubitatEasyClient, HubitatEasyClientWithListener])
def mock_client(request):
    return request.param(
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


def test_get_switches(mock_client):
    assert mock_client.get_switches() == {FAKE_SWITCH_ON['label'], FAKE_SWITCH_OFF['label']}


def test_get_on_switches(mock_client):
    assert mock_client.get_on_switches() == {FAKE_SWITCH_ON['label']}


def test_get_lux_readings(mock_client):
    assert mock_client.get_lux_readings() == {
        FAKE_LUX_1['label']: int(FAKE_LUX_1['attributes']['illuminance']),
        FAKE_LUX_2['label']: int(FAKE_LUX_2['attributes']['illuminance']),
    }


def test_get_mode(mock_client):
    assert mock_client.get_mode() == FAKE_ACTIVE_MODE


def test_get_hsm(mock_client):
    assert mock_client.get_hsm() == HSM_STATE_DISARMED


def test_turn_on_switch(mock_client, mock_requests):
    api_request_url = '{}/devices/{}/on?access_token={}'.format(
        FAKE_URL_PREFIX,
        FAKE_SWITCH_OFF['id'],
        FAKE_ACCESS_TOKEN,
    )
    req_adapter = mock_requests.get(
        api_request_url,
        text='{"fake": "json"}',
    )

    mock_client.turn_on_switch(FAKE_SWITCH_OFF['label'])

    assert len(req_adapter.request_history) == 1
    assert req_adapter.request_history[0].url == api_request_url
