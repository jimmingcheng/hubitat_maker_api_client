import requests

from hubitat_maker_api_client.constants import HSM_STATE_TO_ACTION


CLOUD_API_HOST = 'https://cloud.hubitat.com'


class HubitatAPIClient():
    def __init__(
        self,
        app_id,
        access_token,
        host=CLOUD_API_HOST,
        hub_id=None,
    ):
        self.host = host
        self.app_id = app_id
        self.access_token = access_token
        self.hub_id = hub_id

        if host == CLOUD_API_HOST and not hub_id:
            raise ValueError('hub_id required for Cloud API')

    def api_get(self, endpoint):
        path = self._path_prefix() + endpoint
        resp = requests.get(
            f'{self.host}{path}?access_token={self.access_token}'
        )
        resp.raise_for_status()

        return resp.json()

    def _path_prefix(self):
        if self.host == CLOUD_API_HOST:
            return f'/api/{self.hub_id}/apps/{self.app_id}'
        else:
            return f'/apps/api/{self.app_id}'

    def api_get_device_endpoint(self, device_id, endpoint):
        return self.api_get(f'/devices/{device_id}{endpoint}')

    def get_modes(self):
        return self.api_get('/modes')

    def set_mode(self, mode_id):
        self.api_get(f'/modes/{mode_id}')

    def get_hsm(self):
        return self.api_get('/hsm')

    def set_hsm(self, hsm_state):
        self.send_hsm_command(HSM_STATE_TO_ACTION[hsm_state])

    def send_hsm_command(self, command):
        self.api_get(f'/hsm/{command}')

    def get_devices(self, brief=False):
        if brief:
            return self.api_get('/devices')
        else:
            return self.api_get('/devices/all')

    def get_device(self, device_id):
        return self.api_get_device_endpoint(device_id, '')

    def get_device_events(self, device_id):
        return self.api_get_device_endpoint(device_id, '/events')

    def get_device_commands(self, device_id):
        return self.api_get_device_endpoint(device_id, '/commands')

    def get_device_capabilities(self, device_id):
        return self.api_get_device_endpoint(device_id, '/capabilities')

    def send_device_command(self, device_id, command, secondary_value=None):
        if secondary_value:
            return self.api_get_device_endpoint(device_id, f'/{command}/{secondary_value}')
        else:
            return self.api_get_device_endpoint(device_id, f'/{command}')
