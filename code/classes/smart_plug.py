
import asyncio
import signal
import time

# Async MQTT
from gmqtt.mqtt.constants import MQTTv311
from gmqtt import Client as MQTTClient

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# Class SmartPlug
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

class SmartPlug(object):

    def __init__(self, settings=None, sensor_id=None, event_buffer=None):
        print("SmartPlug init()",sensor_id)

        self.broker_host = 'localhost'
        self.broker_port = 1887

        self.sensor_id = sensor_id

        self.STOP = asyncio.Event()

        self.client = MQTTClient(self.sensor_id)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.on_subscribe = self.on_subscribe


    async def begin(self):

        #client.set_auth_credentials(token, None)
        await self.client.connect(self.broker_host, self.broker_port, version=MQTTv311)

    async def finish(self):

        #await self.STOP.wait()
        await self.client.disconnect()

    def on_connect(self, client, flags, rc, properties):
        print('Connected')

        self.client.publish('TEST/TIME', "{:.3f} {} {}".format(time.time(),self.sensor_id,'connected mqtt'), qos=1)

        self.client.subscribe('TEST/#', qos=0)

    def on_message(self, client, topic, payload, qos, properties):
        self.handle_input(payload)

    def on_disconnect(self, client, packet, exc=None):
        print('Disconnected')

    def on_subscribe(self, client, mid, qos):
        print('SUBSCRIBED')

    def ask_exit(self, *args):
        self.STOP.set()

    def handle_input(self, input):
        print("got input",input)
