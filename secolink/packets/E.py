import logging
from datetime import datetime
from .packet import Packet

logger = logging.getLogger('packetE')


class E(Packet):

    zone: str = ''
    area: str = ''
    periodic_report: str = None
    trouble: bool = False
    program_mode: bool = False

    def mqtt_state_payload(self) -> str:
        if len(self.data) != 9:
            raise Exception('Invalid packet data')

        qualifier = self.data[0]
        type = int(self.data[1:4])
        area = self.data[4:6]
        zone = self.data[6:9]

        if qualifier not in ['E', 'R']:
            raise Exception('Invalid event type {0}'.format(type))

        self.area = area
        self.zone = zone

        if 100 <= type < 200: # ALARMS
            return 'triggered'
        elif 400 <= type < 410: # ARM / DISARM
            if qualifier == 'R':
                return 'armed_away'
            elif qualifier == 'E':
                return 'disarmed'
        elif type in [441, 442]: # ARM STAY
            if qualifier == 'R':
                return 'armed_home'
            elif qualifier == 'E':
                return 'disarmed'
        elif type in [601, 602, 608]: # PERIODIC REPORT (WITH/OUT REPORT)
            self.periodic_report = datetime.utcnow()
            self.trouble = type == 608
            return None
        elif type in [627, 628]: # PROGRAM MODE
            self.program_mode = type == 627
            return None

        logger.warning('Not implemented event - qualifier={0}, type={1}, area={2}, zone={3}'.format(qualifier, type, area, zone))

    def mqtt_attributes_payload(self) -> dict:
        return {
            'changed_by': self.zone,
            'last_periodic_report': str(self.periodic_report),
            'has_trouble': self.trouble,
            'program_mode': self.program_mode
        }