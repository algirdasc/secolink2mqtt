import configparser
import socket
import logging
import json
import socketserver
from typing import Tuple
import paho.mqtt.client as mqtt

logger = logging.getLogger('server')
mqtt_logger = logging.getLogger('mqtt')


class Server(socketserver.ThreadingTCPServer):

    mqttc: mqtt.Client
    config: configparser.ConfigParser
    encryption_key: str
    acc_prefix: str
    acc_number: str
    mqtt_topic: str
    command_queue: list = []
    clients: set
    mqtt_attributes: dict = {
        'changed_by': None,
        'last_periodic_report': None,
        'has_trouble': False,
        'program_mode': False
    }

    def mqtt_on_connect(self, client: mqtt.Client, userdata, msg, rc: int) -> None:
        if rc == mqtt.MQTT_ERR_SUCCESS:
            client.publish('{0}/availability'.format(self.mqtt_topic), payload='online', retain=True)
            client.subscribe('{0}/set'.format(self.mqtt_topic))
            self.publish_attributes()
        else:
            mqtt_logger.error('Connection error: {}'.format(mqtt.error_string(rc)))

    def mqtt_on_disconnect(self, client: mqtt.Client, userdata, rc: int) -> None:
        if rc != mqtt.MQTT_ERR_SUCCESS:
            mqtt_logger.error('Disconnected with code {}, reconnecting'.format(rc))
            try:
                client.reconnect()
            except Exception as e:
                mqtt_logger.exception(e)

    def mqtt_on_message(self, client: mqtt.Client, userdata, msg) -> None:
        command = msg.payload.decode('utf-8')
        if not command:
            return
        self.command_queue.append(msg.payload.decode('utf-8'))
        for c in self.clients:
            c.sendall(b'PING')
            
    def publish_attributes(self, attributes: dict = None) -> None:
        if attributes is not None:
            self.mqtt_attributes = {**self.mqtt_attributes, **attributes}
        self.mqttc.publish('{0}/attributes'.format(self.mqtt_topic), payload=json.dumps(self.mqtt_attributes), retain=True)

    def publish_state(self, state: str = None) -> None:
        if state is not None:
            self.mqttc.publish('{0}/state'.format(self.mqtt_topic), payload=state, retain=True)

    def publish_mqtt(self, payload: str, suffix: str, retain: bool = False) -> None:
        if payload is not None and suffix is not None:
            self.mqttc.publish('{0}/{1}'.format(self.mqtt_topic, suffix), payload=payload, retain=retain)

    def verify_request(self, request: bytes, client_address: Tuple[str, int]) -> bool:        
        request_verified = len(self.clients) <= 10                
        if request_verified is False:
            logger.error('Max connection limit reached')
        return request_verified

    def service_actions(self) -> None:
        rc = self.mqttc.loop()
        if rc != mqtt.MQTT_ERR_SUCCESS:
            self.mqtt_on_disconnect(self.mqttc, {}, rc)

        return super().service_actions()

    def server_bind(self) -> None:
        self.clients = set()
        self.encryption_key = self.config.get('secolink', 'encryption_key', fallback=None)
        self.acc_number = self.config.get('secolink', 'acc_number', fallback=None)
        self.acc_prefix = self.config.get('secolink', 'acc_prefix', fallback=None)

        self.mqtt_topic = 'secolink/{0}'.format(self.acc_number.strip('#'))

        self.mqttc = mqtt.Client(client_id='secolink', clean_session=True)
        self.mqttc.enable_logger(logger=mqtt_logger)
        self.mqttc.reconnect_delay_set(min_delay=1, max_delay=120)
        self.mqttc.will_set('{0}/availability'.format(self.mqtt_topic), payload='offline', retain=True)
        self.mqttc.on_connect = self.mqtt_on_connect
        self.mqttc.on_disconnect = self.mqtt_on_disconnect
        self.mqttc.on_message = self.mqtt_on_message

        username = self.config.get('mqtt', 'username', fallback=None)
        if username is not None:
            self.mqttc.username_pw_set(username, password=self.config.get('mqtt', 'password', fallback=None))

        mqtt_host = self.config.get('mqtt', 'host')
        mqtt_port = self.config.getint('mqtt', 'port', fallback=1883)

        logger.info('Starting up MQTT client ({0}:{1})'.format(mqtt_host, mqtt_port))         
        self.RequestHandlerClass.mqttc = self.mqttc
        self.mqttc.connect(
            host=mqtt_host,
            port=mqtt_port,
            keepalive=int(self.config.getint('mqtt', 'keepalive', fallback=60))
        )

        logger.info('Starting up socket ({0}:{1})'.format(self.server_address[0], self.server_address[1]))

        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setblocking(0)
        self.socket.bind(self.server_address)
