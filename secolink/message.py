import re
import random
import socket
import logging
from binascii import hexlify, unhexlify
from datetime import datetime
from Crypto.Cipher import AES
from secolink.exceptions import EmptyMessageException, MalformedMessageException

logger = logging.getLogger('message')


class Message(object):

    vector = '00000000000000000000000000000000'
    chars = []
    regex_common = r'^(\w{4})(0[0-9A-F]{3})\"(\*?KDN-01)\"(\d{4})(L[0-9A-F]{1,6})(#\w{3,16})\[([\w|:_\s]*)\]?_?([\d:,-]*)?$'
    #regex_enc = r'^[\x00-\xff]+\|([\w:|\s]*)\]_([\d:,-]*)?$'
    regex_enc = r'(.*)\]_([\d:,-]*)?$'

    def __init__(self, request: socket, key='') -> None:
        self.request = request
        self.encryption_key = key     

        self.raw = self.request.recv(4096)
        if not self.raw:
            raise EmptyMessageException()
        
        self.chars.extend(range(1, 91))
        self.chars.extend(range(94, 124))

        self.parse_message()         
        
    def reply(self, content: str = '') -> None:
        message = ''.join([
            '"{0}"'.format(self.id),
            str(self.seq).zfill(4),
            self.acc_prefix,
            self.acc_number,
            '['   
        ])

        now = datetime.now()
        
        payload = ''.join([
            content.upper(),
            ']',
            '_',
            now.strftime('%H:%M:%S,%m-%d-%Y')
        ])

        logger.debug('{0} <- Payload: {1}'.format(self.request.getpeername()[0], message + payload))

        if self.is_encrypted():
            payload = self.encrypt(payload)

        packet = message + payload
        packet_size = '0{:03x}'.format(len(packet)).upper()
        packet_crc = self.calc_crc(packet)

        p = '\x0a{0}{1}{2}\x0d'.format(packet_crc, packet_size, packet).encode('latin-1')
        logger.debug('{0} <- {1}'.format(self.request.getpeername()[0], p))

        self.request.sendall(p)        

    def encrypt(self, content: str) -> str:
        vector = unhexlify(self.vector)
        cipher = AES.new(self.encryption_key, AES.MODE_CBC, vector)
        bs = AES.block_size
        content = '|{0}'.format(content)
        content = content + (bs - len(content) % bs) * chr(random.choice(self.chars))
        return hexlify(cipher.encrypt(content)).decode('latin-1').upper()

    def decrypt(self) -> str:
        vector = unhexlify(self.vector)
        cipher = AES.new(self.encryption_key, AES.MODE_CBC, vector)
        decrypted = cipher.decrypt(unhexlify(self.data))
        return decrypted.decode('latin-1')

    def valid_crc(self) -> bool:
        return self.calc_crc(self.message[8:]) == self.crc

    def is_encrypted(self) -> bool:
        return self.id == '*KDN-01'

    def parse_message(self) -> None:     
        logger.debug('{0} -> {1}'.format(self.request.getpeername()[0], self.raw))

        self.message = self.raw.decode('latin-1').strip()
        
        match = re.search(self.regex_common, self.message)
        if not match:
            raise MalformedMessageException('Failed to match common regex')

        self.crc = match.group(1)
        if not self.valid_crc():
            raise MalformedMessageException('CRC does not match')

        self.len = int(match.group(2), 16)
        if self.len != len(self.message[8:]):
            raise MalformedMessageException('Message length is invalid')

        self.id = match.group(3)

        self.seq = int(match.group(4))
        if self.seq < 1 or self.seq > 9999:
            raise MalformedMessageException('Sequence is invalid - {0}'.format(self.seq))

        self.acc_prefix = match.group(5)
        self.acc_number = match.group(6)

        self.data = match.group(7)
        self.timestamp = match.group(8)

        if self.is_encrypted():
            decrypted = self.decrypt()
            logger.debug('decrypted: {0}'.format(decrypted))
            
            match = re.search(self.regex_enc, decrypted)
        
            if not match:
                raise MalformedMessageException('Failed to match encryption regex')

            self.data = match.group(1)
            self.timestamp = match.group(2)

        self.parse_data()

        if self.data:
            logger.info('{0}: {1}'.format(self.request.getpeername()[0], self.data))

    @staticmethod
    def calc_crc(message: str) -> str:
        crc = 0
        for letter in str.encode(message):
            temp = letter
            for _ in range(0, 8):
                temp ^= crc & 1
                crc >>= 1
                if (temp & 1) != 0:
                    crc ^= 0xA001
                temp >>= 1
        return ('%x' % crc).upper().zfill(4)

    def parse_data(self) -> None:
        parsed = []
        data = self.data.split('|')

        for d in data:
            matches = re.match(r'[A-Z]+:\w*', d)
            if matches:
                parsed.append(d)

        self.data = parsed
