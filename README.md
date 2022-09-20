# hubitat_maker_api_client

This library facilitates access to Hubitat's [Maker API](https://docs.hubitat.com/index.php?title=Maker_API). A key innovation is the **HubitatCachingClient**, which is capable of maintaining a cache of all your devices in a data store of your choice. This can allow you to query device state more efficiently than using the Maker API directly. HubitatCachingClient can be attached to a process that listens to Hubitat's `/eventsocket` to update the cached device states in real time.

## Quick Start

Install

```
pip install hubitat-maker-api-client
```

This sample code demonstrates how to configure a HubitatCachingClient using your `HOST`, `APP_ID`, `ACCESS_TOKEN` and `HUB_ID` along with your custom implementation of **DeviceCache**.

```
from hubitat_maker_api_client import DeviceCache, HubitatAPIClient, HubitatCachingClient


class YourDeviceCache(DeviceCache):
   # Override methods for reading and writing
   # device state to your own datastore


_api_client = HubitatAPIClient(
    host=<HOST>,
    app_id=<APP_ID>,
    access_token=<ACCESS_TOKEN>,
    hub_id=<HUB_ID>,
)

client = HubitatCachingClient(
    api_client=_api_client,
    device_cache=YourDeviceCache(),
)


for switch in client.get_on_switches():
    client.turn_off_switch(switch)
    print(f'Turned off {switch}')
```

This sample code demonstrates how to update device state on your HubitatCachingClient by listening to Hubitat's `/eventsocket`.

```
import asyncio
import websockets
hubitat_maker_api_client import HubitatEvent

async def listen(uri: str) -> None:
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            event = HubitatEvent(json.loads(message))
            client.update_from_hubitat_event(event)

asyncio.get_event_loop().run_until_complete(listen('ws://<HOST_IP>/eventsocket'))
```
