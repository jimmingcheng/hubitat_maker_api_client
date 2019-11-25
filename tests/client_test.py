import json
import requests_mock
import pytest

from hubitat_maker_api_client.client import HubitatAPIClient


FAKE_APP_ID = 'fake_app_id'
FAKE_ACCESS_TOKEN = 'fake_access_token'
FAKE_HUB_ID = 'fake_hub_id'
FAKE_LOCAL_HOST = 'http://192.168.111.111'


@pytest.fixture
def mock_cloud_client():
    return HubitatAPIClient(
        app_id=FAKE_APP_ID,
        access_token=FAKE_ACCESS_TOKEN,
        hub_id=FAKE_HUB_ID,
    )


@pytest.fixture
def mock_local_client():
    return HubitatAPIClient(
        host=FAKE_LOCAL_HOST,
        app_id=FAKE_APP_ID,
        access_token=FAKE_ACCESS_TOKEN,
    )


def test_cloud_api_get(mock_cloud_client):
    with requests_mock.mock() as req_mock:
        fake_payload = {'fake': 'payload'}
        req_mock.get(
            'https://cloud.hubitat.com/api/{}/apps/{}/some_endpoint?access_token={}'.format(
                FAKE_HUB_ID,
                FAKE_APP_ID,
                FAKE_ACCESS_TOKEN,
            ),
            text=json.dumps(fake_payload),
        )

        resp = mock_cloud_client.api_get('/some_endpoint')

        assert resp == fake_payload


def test_local_api_get(mock_local_client):
    with requests_mock.mock() as req_mock:
        fake_payload = {'fake': 'payload'}
        req_mock.get(
            '{}/apps/api/{}/some_endpoint?access_token={}'.format(
                FAKE_LOCAL_HOST,
                FAKE_APP_ID,
                FAKE_ACCESS_TOKEN,
            ),
            text=json.dumps(fake_payload),
        )

        resp = mock_local_client.api_get('/some_endpoint')

        assert resp == fake_payload
