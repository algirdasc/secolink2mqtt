import select
import logging
import socketserver

from secolink import packets
from secolink.server import Server
from secolink.message import Message
from secolink.exceptions import EmptyMessageException, MalformedMessageException

logger = logging.getLogger('handler')
mqtt_logger = logging.getLogger('mqtt')


class Handler(socketserver.BaseRequestHandler):

    id: int
    server: Server
    mqtt_attributes: dict = {}

    def setup(self) -> None:
        logger.debug('Got request {0}'.format(self.request))
        self.server.clients.add(self.request)

    def handle(self) -> None:
        logger.info('{0}: connected'.format(self.client_address[0]))
        while True:
            ready = select.select([self.request], [], [], 600)
            if not ready[0]:
                logger.info('{0}: idle time out'.format(self.client_address[0]))
                break

            try:
                m = Message(self.request, self.server.encryption_key)

                if not self.validate_account(m):
                    break

                if len(m.data) > 0:
                    logger.info('{0}: handling message'.format(self.client_address[0]))
                    self.handle_message_data(m)

                m.reply(self.get_next_command(m))
            except EmptyMessageException:
                break
            except MalformedMessageException as e:
                logger.error('{0}: {1}'.format(self.client_address[0], str(e)))
            except Exception as e:
                logger.error('{0}: {1}'.format(self.client_address[0], str(e)))                
                break

        logger.info('{0}: disconnected'.format(self.client_address[0]))

    def finish(self) -> None:
        logger.debug('Finishing request {0}'.format(self.request))
        self.server.clients.remove(self.request)

    def validate_account(self, message: Message) -> bool:
        if self.server.acc_number and self.server.acc_number != message.acc_number:
            logger.error('{0}: account number mismatch'.format(self.client_address[0]))
            return False

        if self.server.acc_prefix and self.server.acc_prefix != message.acc_prefix:
            logger.error('{0}: account prefix mismatch'.format(self.client_address[0]))
            return False

        return True

    def get_next_command(self, message: Message) -> str:
        if message.data or len(self.server.command_queue) == 0:
            return ''

        return 'CMD:{0}'.format(self.server.command_queue.pop(0))

    def handle_message_data(self, message: Message) -> None:
        for mdata in message.data:
            packet, data = mdata.split(':')
            module = getattr(packets, packet, None)

            if module is None:
                logger.error('{0} packet is not implemented'.format(packet)) 
                continue

            try:
                pckt = module(str(data))
            except Exception as e:
                logger.error(e)
                continue

            self.server.publish_state(pckt.mqtt_state_payload())
            self.server.publish_attributes(pckt.mqtt_attributes_payload())
            self.server.publish_mqtt(pckt.mqtt_other_payload(), suffix=pckt.mqtt_suffix())
