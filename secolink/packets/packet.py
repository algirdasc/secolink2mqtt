class Packet(object):
    
    data: str = ''    

    def __init__(self, data: str):
        self.data = data

    def mqtt_suffix(self) -> str:
        return None

    def mqtt_state_payload(self) -> str:
        return None

    def mqtt_attributes_payload(self) -> dict:
        return {}
    
    def mqtt_other_payload(self) -> str:
        return None