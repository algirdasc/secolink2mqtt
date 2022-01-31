from .packet import Packet

class ACC(Packet):
        
    def mqtt_other_payload(self) -> str:
        return None